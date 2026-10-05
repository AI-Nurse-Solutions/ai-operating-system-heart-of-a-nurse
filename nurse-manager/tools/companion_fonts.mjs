// Developer companion typography: exclude UI fonts with separate commercial terms.
import { readFileSync, writeFileSync, readdirSync, unlinkSync, mkdirSync } from 'node:fs';
import { resolve, join, relative } from 'node:path';
import { createHash } from 'node:crypto';
const root = resolve(process.argv[2]);
const ui = join(root, 'node_modules/@nous-research/ui');
if (JSON.parse(readFileSync(join(ui, 'package.json'))).version !== '0.18.2') throw Error('Review changed UI dependency before patching fonts.');
const sha = data => createHash('sha256').update(data).digest('hex');
const changes = [];
function patch(path) {
  const original = readFileSync(path, 'utf8');
  const updated = original.replace(/@font-face\s*\{[^}]*\}/g, block =>
    /Collapse|RulesCompressed|RulesExpanded|Mondwest|Neuebit/.test(block) ? '' : block);
  if (updated !== original) {
    writeFileSync(path, updated);
    changes.push({ path: relative(root, path), before: sha(original), after: sha(updated), change: 'Remove UI font-face declarations; retain system fallback' });
  }
}
function scan(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const path = join(dir, entry.name);
    if (entry.isSymbolicLink()) throw Error('Unexpected UI asset symlink.');
    if (entry.isDirectory() && entry.name !== 'node_modules') scan(path);
    else if (entry.name.endsWith('.css')) patch(path);
    else if (entry.isFile() && /\.(woff2?|ttf|otf)$/i.test(entry.name)) {
      changes.push({ path: relative(root, path), before: sha(readFileSync(path)), change: 'Exclude third-party UI font from app and retained package source' });
      unlinkSync(path);
    }
  }
}
scan(ui);
patch(join(root, 'apps/desktop/src/styles.css'));
if (!changes.some(x => x.path === 'apps/desktop/src/styles.css') || !changes.some(x => x.path.endsWith('/fonts.css'))) throw Error('Expected pinned font declarations not found.');
mkdirSync(join(root, 'companion-audit'), { recursive: true });
writeFileSync(join(root, 'companion-audit/font-modifications.json'), JSON.stringify(changes, null, 2) + '\n');
console.log('Developer companion: commercial UI fonts excluded; system-font fallbacks; modification hashes recorded.');
