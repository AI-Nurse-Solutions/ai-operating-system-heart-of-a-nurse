// Package actual build inputs and required notices; unknown terms fail closed.
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
  if (input.startsWith('\0') || input.startsWith('__vite-optional-peer-dep:')) { virtualInputs++; return; }
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
for (const name of ['electron', 'node-pty', 'get-windows', 'emojibase-data', '@vscode/codicons', 'vite']) {
  // Some packages intentionally do not export package.json.
  const path = require.resolve.paths(name).map(dir => join(dir, name, 'package.json')).find(existsSync);
  if (!path) throw Error('Missing required installed package: ' + name);
  const dir = realpathSync(dirname(path));
  if (!dir.startsWith(root + '/')) throw Error('Package resolves outside owned upstream source: ' + name);
  packages.set(dir, JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8')));
}
// Include native external dependencies that execute outside the JS bundles.
function nativeDependencies(dir, visited = new Set()) {
  if (visited.has(dir)) return;
  visited.add(dir);
  const pkg = JSON.parse(readFileSync(join(dir, 'package.json'), 'utf8'));
  const resolver = createRequire(join(dir, 'package.json'));
  for (const name of Object.keys(pkg.dependencies ?? {})) {
    const path = resolver.resolve.paths(name).map(base => join(base, name, 'package.json')).find(existsSync);
    if (!path) throw Error('Missing native dependency: ' + name);
    const dependency = realpathSync(dirname(path));
    if (!dependency.startsWith(root + '/')) throw Error('Native dependency resolves outside source.');
    packages.set(dependency, JSON.parse(readFileSync(path, 'utf8')));
    nativeDependencies(dependency, visited);
  }
}
for (const [dir, pkg] of [...packages]) {
  if (['node-pty', 'get-windows', 'emojibase-data'].includes(pkg.name)) nativeDependencies(dir);
}
mkdirSync(output);
const mitPermission = readFileSync(join(root, 'LICENSE'), 'utf8').split('Permission is hereby granted')[1];
if (!mitPermission) throw Error('Missing canonical MIT permission text.');
const allowedLicenses = new Set(['MIT', 'MIT (installed notice)', 'ISC', 'BSD-3-Clause', 'BSD-2-Clause', 'Apache-2.0', 'MPL-2.0', '(MPL-2.0 OR Apache-2.0)', 'Unlicense', 'BlueOak-1.0.0', '0BSD', 'CC-BY-4.0']);
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
  const noticeDir = join(output, 'notices', id);
  mkdirSync(noticeDir, { recursive: true });
  copyFileSync(join(dir, 'package.json'), join(noticeDir, 'package.json'));
  if (!notices.length) {
    if (license !== 'MIT') pending.push(`${pkg.name}@${pkg.version}: no installed license/notice file`);
    else {
      // Retain the authentic MIT grant in the exact installed manifest and
      // all distributed source notices. Do not invent a missing copyright.
      cpSync(dir, join(output, 'source', id), { recursive: true,
        filter: path => !relative(dir, path).split('/').includes('node_modules') });
      writeFileSync(join(noticeDir, 'MIT-permission.txt'), `This exact package declares MIT in its original package.json; no standalone copyright notice was supplied. Original files/notices are retained under source/. No holder or year has been invented.\n\n${"Permission is hereby granted" + mitPermission}`);
    }
  }
  if (!allowedLicenses.has(license)) pending.push(`${pkg.name}@${pkg.version}: unreviewed license ${license}`);
  if (!license) pending.push(`${pkg.name}@${pkg.version}: no identified license`);
  if (pkg.name === '@novnc/novnc') {
    cpSync(dir, join(output, 'source', 'novnc-' + pkg.version), { recursive: true, filter: path => !relative(dir, path).split('/').includes('node_modules') });
  }
  const locked = lock[id];
  if (!locked || locked.version !== pkg.version) throw Error('Installed package differs from pinned lockfile: ' + id);
  records.push({ name: pkg.name, version: pkg.version, installedPath: id, license, selectedLicense: pkg.name === 'dompurify' ? 'Apache-2.0' : license, integrity: locked.integrity ?? null, resolved: locked.resolved ?? null, notices, manifestSha256: digest(join(dir, 'package.json')) });
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
for (const asset of assets) {
  if (/Collapse|RulesCompressed|RulesExpanded|Mondwest|Neuebit/i.test(asset.path)) throw Error('Excluded commercial font still packaged: ' + asset.path);
  if (/\.(woff2?|ttf|otf)$/i.test(asset.path) && !/\/(KaTeX_|JetBrainsMono-|codicon-)/.test(asset.path)) throw Error('Review unknown packaged font: ' + asset.path);
  if (asset.path.endsWith('.css')) {
    const css = readFileSync(join(root, asset.path), 'utf8');
    if ((css.match(/@font-face\s*\{[^}]*\}/g) ?? []).some(block => /Collapse|RulesCompressed|RulesExpanded|Mondwest|Neuebit/.test(block))) throw Error('Commercial font face survives in emitted CSS');
  }
}
const electronDir = [...packages].find(([, p]) => p.name === 'electron')[0];
for (const file of ['LICENSE', 'LICENSES.chromium.html']) {
  const path = join(electronDir, 'dist', file);
  // Native macOS binaries place runtime notices at the distribution root.
  if (!existsSync(path)) throw Error('Missing actual Electron runtime notice: ' + file);
  copyFileSync(path, join(output, 'Electron-' + file));
}
const fontModifications = join(audit, 'font-modifications.json');
copyFileSync(fontModifications, join(output, 'font-modifications.json'));
copyFileSync(join(root, 'apps/desktop/src/styles.css'), join(output, 'modified-desktop-styles.css'));
writeFileSync(join(output, 'FONT-ATTRIBUTION.txt'), `Codicons 0.0.45: Copyright (c) Microsoft Corporation. https://github.com/microsoft/vscode-codicons . Font unmodified; CC-BY-4.0; full LICENSE and LICENSE-CODE under notices/node_modules/@vscode/codicons/.\nJetBrains Mono: Copyright 2020 The JetBrains Mono Project Authors (https://github.com/JetBrains/JetBrainsMono). Fonts unmodified; SIL OFL 1.1; full OFL under runtime-source/jetbrains-OFL.txt.\nKaTeX fonts: MIT; original package notice retained.\nThe commercial UI fonts are excluded. Their font-face declarations are removed; modified CSS uses the existing system fallback. Hashes of modifications are recorded.\nDOMPurify: distributed under its Apache-2.0 alternative, with original dual-license notice retained.\nnoVNC: MPL-2.0 preferred source is included in source/novnc-<version>.\n`);
if (pending.length) throw Error(JSON.stringify({ pending, unresolvedInputs }));
writeFileSync(join(output, 'inventory.json'), JSON.stringify({ upstreamCommit, dependencyNoticesComplete: true, packages: records, assets, scope: "Dependency/font notices only; runtime source and actual packaged loader/contents verified separately before upload", virtualInputs, unresolvedInputs, pending }, null, 2) + '\n');
console.log(JSON.stringify({ packages: records.length, pending, dependencyNoticesComplete: true }, null, 2));
