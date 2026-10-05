// Extend upstream's existing opt-in ignore flag to its Python fallback too.
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve, join, relative } from 'node:path';
import { createHash } from 'node:crypto';
const root = resolve(process.argv[2]);
const path = join(root, 'apps/desktop/electron/main.ts');
const original = readFileSync(path, 'utf8');
const anchor = '  // 5. Last-ditch: pip-installed hermes_cli module via system Python.';
if (original.split(anchor).length !== 2) throw Error('Pinned backend resolver changed; review required.');
const [before, after] = original.split(anchor);
const from = '  const python = await findSystemPython()';
if (!after.startsWith('\n  //    Same rationale as #4') || !after.includes(from)) throw Error('Pinned Python fallback shape changed.');
const updated = before + anchor + after.replace(from,
  "  const python = process.env.HERMES_DESKTOP_IGNORE_EXISTING === '1' ? null : await findSystemPython()");
writeFileSync(path, updated);
const audit = join(root, 'companion-audit/font-modifications.json');
const modifications = JSON.parse(readFileSync(audit));
const sha = text => createHash('sha256').update(text).digest('hex');
modifications.push({ path: relative(root, path), before: sha(original), after: sha(updated),
  change: 'Make explicit HERMES_DESKTOP_IGNORE_EXISTING=1 skip existing Python as well as CLI; ordinary resolution preserved' });
writeFileSync(audit, JSON.stringify(modifications, null, 2) + '\n');
