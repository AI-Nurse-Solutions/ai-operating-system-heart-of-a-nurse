// Diagnostic inventory only: this does not authorize binary redistribution.
import { readFileSync, writeFileSync, readdirSync, existsSync, realpathSync, mkdirSync, copyFileSync, cpSync } from 'node:fs';
import { dirname, join, resolve, relative } from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
const root = realpathSync(resolve(process.argv[2]));
const upstreamCommit = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim();
if (upstreamCommit !== 'f97608f178d1ffeca59860195ab7da295f7c8e5f') throw Error('Unexpected upstream source revision.');
const audit = join(root, 'companion-audit');
const output = resolve(process.argv[3]);
if (existsSync(output)) throw Error('Use a fresh owned inventory directory.');
const require = createRequire(join(root, 'apps/desktop/package.json'));
const digest = p => createHash('sha256').update(readFileSync(p)).digest('hex');
const packages = new Map();
const lock = JSON.parse(readFileSync(join(root, 'package-lock.json'), 'utf8')).packages;
const unresolvedInputs = [];
let virtualInputs = 0;
function addFile(input) {
  if (input.startsWith('\0')) { virtualInputs++; return; }
  const path = input.split('?')[0];
  if (!existsSync(path)) { unresolvedInputs.push(input); return; }
  let dir = dirname(realpathSync(path));
  if (!dir.startsWith(root + '/')) { unresolvedInputs.push(input); return; }
  while (dir.startsWith(root + '/')) {
    const manifest = join(dir, 'package.json');
    if (existsSync(manifest)) {
      const pkg = JSON.parse(readFileSync(manifest, 'utf8'));
      // Nested package.json files can declare only the module format.
      if (pkg.name && pkg.version) {
        if (dir.includes('/node_modules/')) packages.set(dir, pkg);
        return;
      }
    }
    dir = dirname(dir);
  }
}
for (const name of ['renderer.json', 'electron-main.mjs.json', 'electron-preload.js.json', 'preview-guest-preload.js.json']) {
  for (const file of JSON.parse(readFileSync(join(audit, name), 'utf8')).files) addFile(file);
}
// Native/external packages are not present in bundler input metadata.
for (const name of ['electron', 'node-pty', 'get-windows', 'emojibase-data']) {
  // Some packages intentionally do not export package.json.
  const path = require.resolve.paths(name).map(dir => join(dir, name, 'package.json')).find(existsSync);
  if (!path) throw Error('Missing required installed package: ' + name);
  const dir = realpathSync(dirname(path));
  if (!dir.startsWith(root + '/')) throw Error('Package resolves outside owned upstream source: ' + name);
  packages.set(dir, JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8')));
}
mkdirSync(output);
const records = [];
const pending = [];
function collect(dir, paths = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    if (entry.isSymbolicLink()) continue;
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      if (!['node_modules', '.git'].includes(entry.name)) collect(path, paths);
    } else if (/^(licen[sc]es?|notices?|copying|attribution|third[_-]?party(?:notices?)?|ofl)([._-]|$)/i.test(entry.name)) {
      // Preserve full package-relative paths; identical basenames must not overwrite.
      paths.push(path);
    }
  }
  return paths;
}
for (const [dir, pkg] of [...packages].sort((a,b) => a[0].localeCompare(b[0]))) {
  if (realpathSync(dir) !== dir || !dir.startsWith(root + '/')) throw Error('Unsafe package inventory path.');
  const id = relative(root, dir);
  const notices = collect(dir).map(path => {
    const destination = join(output, 'notices', id, relative(dir, path));
    mkdirSync(dirname(destination), { recursive: true });
    copyFileSync(path, destination);
    return { path: relative(output, destination), sha256: digest(path) };
  });
  const license = pkg.license ?? (pkg.name === 'khroma' && existsSync(join(dir, 'license')) && readFileSync(join(dir, 'license'), 'utf8').startsWith('The MIT License (MIT)') ? 'MIT (installed notice)' : null);
  if (!notices.length) pending.push(`${pkg.name}@${pkg.version}: no installed license/notice file`);
  if (!license) pending.push(`${pkg.name}@${pkg.version}: no identified license`);
  if (pkg.name === '@novnc/novnc') {
    cpSync(dir, join(output, 'source', 'novnc-' + pkg.version), { recursive: true, filter: path => !relative(dir, path).split('/').includes('node_modules') });
  }
  const locked = lock[id];
  if (!locked || locked.version !== pkg.version) throw Error('Installed package differs from pinned lockfile: ' + id);
  records.push({ name: pkg.name, version: pkg.version, installedPath: id, license, integrity: locked.integrity ?? null, resolved: locked.resolved ?? null, notices, manifestSha256: digest(join(dir, 'package.json')) });
}
copyFileSync(join(root, 'LICENSE'), join(output, 'HERMES-LICENSE'));
copyFileSync(join(root, 'apps/desktop/src/plugins/hermes-bots/LICENSE'), join(output, 'HERMES-BOTS-LICENSE'));
const assets = [];
function inventoryAssets(dir) {
  if (!existsSync(dir)) return;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isSymbolicLink()) throw Error('Review asset symlink before inventory: ' + path);
    if (entry.isDirectory()) inventoryAssets(path);
    else assets.push({ path: relative(root, path), sha256: digest(path) });
  }
}
for (const dir of ['assets', 'public', 'dist/assets', 'dist/emojibase']) inventoryAssets(join(root, 'apps/desktop', dir));
if (unresolvedInputs.length) pending.push('Unresolved real bundler inputs: ' + unresolvedInputs.length);
pending.push('Electron FFmpeg: LGPL corresponding source/build controls and library replacement verification outstanding');
pending.push('Review custom licenses, attribution, assets, nested runtime notices and actual packaged contents before redistribution');
writeFileSync(join(output, 'inventory.json'), JSON.stringify({ upstreamCommit, redistributionReady: false, packages: records, assets, virtualInputs, unresolvedInputs, pending }, null, 2) + '\n');
console.log(JSON.stringify({ packages: records.length, pending, redistributionReady: false }, null, 2));
