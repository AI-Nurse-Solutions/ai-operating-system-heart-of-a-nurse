// Reuse upstream build configuration; record actual inputs for notice collection.
import { createRequire } from 'node:module';
import { readFileSync, writeFileSync, mkdirSync, existsSync, unlinkSync } from 'node:fs';
import { resolve, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { spawnSync } from 'node:child_process';
const root = resolve(process.argv[2]);
const desktop = join(root, 'apps/desktop');
const output = join(root, 'companion-audit');
mkdirSync(output, { recursive: true });
const require = createRequire(join(desktop, 'package.json'));
const { build } = await import(pathToFileURL(require.resolve('vite')));
process.chdir(desktop);
await build({ plugins: [{ name: 'companion-license-inputs', generateBundle() {
  writeFileSync(join(output, 'renderer.json'), JSON.stringify({ files: [...this.getModuleIds()] }));
} }] });
const originalPath = join(desktop, 'scripts/bundle-electron-main.mjs');
const original = readFileSync(originalPath, 'utf8');
if ((original.match(/await build\(/g) || []).length !== 3) throw Error('Pinned upstream bundler shape changed; review required.');
const auditedPath = join(desktop, 'scripts/companion-audited-main.mjs');
if (existsSync(auditedPath)) throw Error('Refusing to overwrite an existing audit script.');
const instrumentation = `
async function auditedBuild(options) {
  const result = await build({ ...options, metafile: true });
  const fs = await import('node:fs');
  const path = await import('node:path');
  fs.writeFileSync(path.join(process.env.NAIO_COMPANION_AUDIT_DIR,
    path.basename(options.outfile) + '.json'), JSON.stringify({
      files: Object.keys(result.metafile.inputs).map(p => path.resolve(p))
    }));
  return result;
}
`;
try {
  writeFileSync(auditedPath, instrumentation + original.replace(/^#![^\n]*\n/, '').replaceAll('await build(', 'await auditedBuild('), { flag: 'wx' });
  const result = spawnSync(process.execPath, [auditedPath], {
    cwd: desktop, env: { ...process.env, NAIO_COMPANION_AUDIT_DIR: output }, stdio: 'inherit',
  });
  if (result.error || result.status !== 0) throw Error('Audited upstream main build failed.');
} finally {
  if (existsSync(auditedPath)) unlinkSync(auditedPath);
}
