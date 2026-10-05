// Verify inventory bytes against the real packaged archive, not just dist/.
import assert from 'node:assert/strict';
import { readFileSync, writeFileSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createHash } from 'node:crypto';
import { createRequire } from 'node:module';
const root = resolve(process.argv[2]);
const app = resolve(process.argv[3]);
const notices = resolve(process.argv[4]);
const require = createRequire(join(root, 'apps/desktop/package.json'));
const asar = require('@electron/asar');
const archive = join(app, 'Contents/Resources/app.asar');
const inventory = JSON.parse(readFileSync(join(notices, 'inventory.json')));
assert.equal(inventory.dependencyNoticesComplete, true);
const files = asar.listPackage(archive).map(p => p.replace(/^\//, ''));
assert.ok(!files.some(p => /Collapse|RulesCompressed|RulesExpanded|Mondwest|Neuebit/i.test(p)));
assert.ok(!files.some(p => /(^|\/)gsap(\/|$)/i.test(p)), 'GSAP is not a packaged input');
const requiredFonts = new Set(['JetBrainsMono', 'KaTeX', 'codicon']);
for (const path of files.filter(p => /\.(woff2?|ttf|otf)$/i.test(p))) {
  const family = [...requiredFonts].find(name => path.includes(name));
  assert.ok(family, 'Review unknown packaged font: ' + path);
}
for (const asset of inventory.assets) {
  const path = asset.path.replace(/^apps\/desktop\//, '');
  if (path.startsWith('assets/')) {
    // electron-builder excludes its build-resource directory from app.asar.
    // ICO is an explicit extraResource; ICNS is the native bundle icon.
    if (path === 'assets/icon.png') continue; // build source, not a Mac payload
    assert.ok(['assets/icon.ico', 'assets/icon.icns'].includes(path), 'Review new build resource: ' + path);
    const bytes = readFileSync(join(app, 'Contents/Resources', path.slice('assets/'.length)));
    assert.equal(createHash('sha256').update(bytes).digest('hex'), asset.sha256, path);
    continue;
  }
  assert.ok(files.includes(path), 'Inventoried asset is absent from bundle: ' + path);
  const bytes = asar.extractFile(archive, path);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), asset.sha256, path);
}
for (const path of files.filter(p => p.endsWith('.css'))) {
  const css = asar.extractFile(archive, path).toString('utf8');
  assert.ok(!(css.match(/@font-face\s*\{[^}]*\}/g) ?? []).some(block => /Collapse|RulesCompressed|RulesExpanded|Mondwest|Neuebit/.test(block)), path);
}
const stamp = JSON.parse(readFileSync(join(app, 'Contents/Resources/install-stamp.json')));
assert.equal(stamp.commit, inventory.upstreamCommit);
assert.equal(stamp.dirty, true);
writeFileSync(process.argv[5], JSON.stringify({ result: 'PASS', packagedAssetsMatched: inventory.assets.length,
  excludedCommercialFonts: true, sourceStamp: stamp, actualPackageInspected: true }, null, 2) + '\n');
