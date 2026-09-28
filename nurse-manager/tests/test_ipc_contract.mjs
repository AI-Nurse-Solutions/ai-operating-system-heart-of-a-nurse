// IPC contract, checked the way the desktop host will consume it (build step 1.4).
//
// 1. The real CLI's envelopes are produced by tools/ipc_fixtures.py.
// 2. ajv (strict, draft 2020-12) validates each envelope and its data.
// 3. The TypeScript compiler (strict) typechecks every envelope as
//    Envelope<command> against the generated nurse-manager-ipc.d.ts,
//    and confirms that deliberate misuses do not compile.
// 4. The renderer's JavaScript (checkJs, strict) typechecks against the same
//    contract, so a contract change cannot silently break a screen.
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import Ajv2020 from 'ajv/dist/2020.js';
import ts from 'typescript';

const here = (p) => fileURLToPath(new URL(p, import.meta.url));
const ipc = here('../contracts/ipc/');
const schema = JSON.parse(readFileSync(join(ipc, 'nurse-manager-ipc.schema.json'), 'utf8'));
const commands = JSON.parse(readFileSync(join(ipc, 'commands.json'), 'utf8')).commands;

const work = mkdtempSync(join(tmpdir(), 'nm-ipc-'));
try {
  const fixturesDir = join(work, 'fixtures');
  const run = spawnSync('python3', [here('../tools/ipc_fixtures.py'), fixturesDir], { encoding: 'utf8' });
  assert.equal(run.status, 0, run.stderr);
  const fixtures = Object.fromEntries(
    readdirSync(fixturesDir).sort().map((f) => [f.replace(/\.json$/, ''), JSON.parse(readFileSync(join(fixturesDir, f), 'utf8'))]),
  );
  assert.ok(Object.keys(fixtures).length >= Object.keys(commands).length, 'every command has a fixture');

  // --- ajv ---------------------------------------------------------------
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  ajv.addSchema(schema);
  const validator = (name) => {
    const fn = ajv.getSchema(`${schema.$id}#/$defs/${name}`);
    assert.ok(fn, `schema defines ${name}`);
    return fn;
  };
  for (const [name, envelope] of Object.entries(fixtures)) {
    const outer = validator(envelope.ok ? 'OkEnvelope' : 'ErrorEnvelope');
    assert.equal(outer(envelope), true, `${name}: ${ajv.errorsText(outer.errors)}`);
    if (envelope.ok) {
      const inner = validator(commands[envelope.command]);
      assert.equal(inner(envelope.data), true, `${name}: ${ajv.errorsText(inner.errors)}`);
    }
  }
  const sent = structuredClone(fixtures.run);
  sent.data.outcome = 'sent';
  assert.equal(validator('Receipt')(sent.data), false, 'ajv must reject an outcome of "sent"');

  // --- tsc ---------------------------------------------------------------
  const tsDir = join(work, 'ts');
  mkdirSync(tsDir);
  copyFileSync(join(ipc, 'nurse-manager-ipc.d.ts'), join(tsDir, 'nurse-manager-ipc.d.ts'));
  const lines = ['import type { CommandData, Envelope, OkEnvelope } from "./nurse-manager-ipc";', ''];
  for (const [name, envelope] of Object.entries(fixtures)) {
    const id = `fx_${name.replace(/-/g, '_')}`;
    lines.push(`export const ${id}: Envelope<${JSON.stringify(envelope.command)}> = ${JSON.stringify(envelope)} as const;`);
  }
  lines.push(
    '',
    'export function priorities(e: Envelope<"mission">): readonly string[] {',
    '  if (!e.ok) return [e.error.message];',
    '  const m: CommandData["mission"] = e.data;',
    '  return m.priorities.items.map((p) => `${p.rank}. ${p.text}`);',
    '}',
    '// @ts-expect-error an error envelope carries no data',
    'export const misuse1: OkEnvelope<"board"> = { contract: "nurse-manager-ipc@1", command: "board", ok: false, error: { type: "X", message: "y" } };',
    '// @ts-expect-error the contract version is a literal',
    'export const misuse2: Envelope<"run"> = { contract: "nurse-manager-ipc@2", command: "run", ok: false, error: { type: "X", message: "y" } };',
    'export function misuse3(e: OkEnvelope<"board">) {',
    '  // @ts-expect-error records are read-only in the renderer',
    '  e.data.columns[0].cards[0].title = "edited in the view";',
    '}',
  );
  const file = join(tsDir, 'fixtures.ts');
  writeFileSync(file, lines.join('\n') + '\n');
  const program = ts.createProgram([file], {
    strict: true, noEmit: true, target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022, moduleResolution: ts.ModuleResolutionKind.Bundler,
    exactOptionalPropertyTypes: true, noUncheckedIndexedAccess: false,
  });
  const diagnostics = ts.getPreEmitDiagnostics(program)
    .map((d) => ts.flattenDiagnosticMessageText(d.messageText, '\n'));
  assert.deepEqual(diagnostics, [], diagnostics.join('\n'));

  // --- renderer consumes the contract --------------------------------------
  const renderer = ['views.mjs', 'app.mjs'].map((f) => here(`../renderer/${f}`));
  const rendererProgram = ts.createProgram(renderer, {
    allowJs: true, checkJs: true, noEmit: true, strict: true,
    target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.ES2022,
    moduleResolution: ts.ModuleResolutionKind.Bundler,
    lib: ['lib.es2022.d.ts', 'lib.dom.d.ts', 'lib.dom.iterable.d.ts'],
  });
  const rendererDiagnostics = ts.getPreEmitDiagnostics(rendererProgram).map((d) =>
    `${d.file?.fileName ?? ''}: ${ts.flattenDiagnosticMessageText(d.messageText, ' ')}`);
  assert.deepEqual(rendererDiagnostics, [], rendererDiagnostics.join('\n'));

  console.log(`nurse-manager IPC contract: ${Object.keys(fixtures).length} envelopes pass ajv and tsc; renderer typechecks`);
} finally {
  rmSync(work, { recursive: true, force: true });
}
