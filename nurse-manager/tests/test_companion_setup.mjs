// Exercise the actual resolver with simulated existing CLI/Python installs.
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { resolve, join } from 'node:path';
import path from 'node:path';
import vm from 'node:vm';
import { createRequire } from 'node:module';
const root = resolve(process.argv[2]);
const require = createRequire(join(root, 'apps/desktop/package.json'));
const ts = require('typescript');
const file = ts.createSourceFile('main.ts', readFileSync(join(root, 'apps/desktop/electron/main.ts'), 'utf8'), ts.ScriptTarget.Latest, true);
const fn = file.statements.find(node => ts.isFunctionDeclaration(node) && node.name?.text === 'resolveHermesBackend');
assert.ok(fn, 'test must exercise the actual upstream resolver');
async function exercise(ignore, cli) {
  const calls = [];
  const context = { path, process: { env: { HERMES_DESKTOP_IGNORE_EXISTING: ignore }, platform: 'darwin' },
    IS_PACKAGED: true, IS_WINDOWS: false, IS_WSL: false, SOURCE_REPO_ROOT: '/synthetic/no-source',
    ACTIVE_HERMES_ROOT: '/synthetic/empty-home', INSTALL_STAMP: null, bootstrapRepairRequested: false,
    isHermesSourceRoot: () => false,
    activeRuntimeState: async () => ({ shouldUseActiveRuntime: false }),
    rememberLog: () => {}, findOnPath: () => { calls.push('cli'); return cli ? '/synthetic/hermes' : null; },
    looksLikeDesktopAppBinary: () => false, unwrapWindowsVenvHermesCommand: async () => null,
    isCommandScript: () => false, shouldTrustHermesOverride: () => false, verifyHermesCli: async () => true,
    findSystemPython: async () => { calls.push('python'); return '/synthetic/python'; },
    canImportHermesCli: async () => { calls.push('import'); return true; },
  };
  const resolver = vm.runInNewContext('(' + fn.getText(file) + ')', context);
  return { backend: await resolver(['serve']), calls };
}
const ignored = await exercise('1', true);
assert.equal(ignored.backend.kind, 'bootstrap-needed', 'fresh trial must not activate an existing Python agent');
assert.deepEqual(ignored.calls, [], 'fresh trial must not probe existing CLI/Python');
const ordinaryCli = await exercise('0', true);
assert.equal(ordinaryCli.backend.kind, 'command');
const ordinaryPython = await exercise('0', false);
assert.equal(ordinaryPython.backend.kind, 'python');
assert.ok(ordinaryPython.calls.includes('import'));
console.log(JSON.stringify({ result: 'PASS', existingAgentsIgnoredInFreshTrial: true, ordinaryResolutionPreserved: true }));
