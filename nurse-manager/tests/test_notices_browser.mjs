// Hermes independence notes as a browser renders them (build step 0.8).
//
// test_notices.py checks the markup statically. This test is the authority on
// what a reader actually sees: it opens every page whose <title> names Hermes
// in Chromium, with the site's own stylesheets and scripts, and requires
// exactly one attribution note that the browser computes as visible. The
// note's rendered text (innerText, which drops hidden descendants and honours
// implicit end tags) must name Nous Research and Nurse AI OS and carry the
// page language's non-endorsement clause. The page list, the documented
// exception and the clauses come from test_notices.py, so both tests agree.
//
// Network requests other than file:// are blocked so the run is offline.
// CHROME_PATH=/path/to/chrome overrides the system Chrome channel (local runs).
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { join } from 'node:path';
import { chromium } from 'playwright-core';

const repo = fileURLToPath(new URL('../..', import.meta.url));
const load = spawnSync('python3', ['-c', [
  'import json, sys',
  "sys.path.insert(0, 'nurse-manager/tests')",
  'import test_notices as t',
  "print(json.dumps({'pages': t.hermes_pages(), 'equivalent': t.EQUIVALENT_ATTRIBUTION,",
  "                  'clauses': t.NON_ENDORSEMENT_CLAUSE}))",
].join('\n')], { cwd: repo, encoding: 'utf8' });
assert.equal(load.status, 0, load.stderr);
const { pages, equivalent, clauses } = JSON.parse(load.stdout);
assert.ok(pages.length >= 14, `expected the known Hermes pages, found ${pages.length}`);

/** Visible attribution notes in the current document, as rendered text. */
const visibleNotes = () => [...document.querySelectorAll('[data-attribution="hermes-independence"]')]
  .filter((el) => {
    const box = el.getBoundingClientRect();
    return el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })
      && box.width > 0 && box.height > 0;
  })
  .map((el) => el.innerText.replace(/\s+/g, ' ').trim());

const browser = await chromium.launch(process.env.CHROME_PATH
  ? { executablePath: process.env.CHROME_PATH, headless: true }
  : { channel: 'chrome', headless: true });
let failures = 0;
const check = (name, ok, detail = '') => {
  console.log(`  ${ok ? '✓' : '✗'} ${name}${ok || !detail ? '' : ` — ${detail}`}`);
  if (!ok) failures += 1;
};

try {
  const context = await browser.newContext();
  await context.route(/^(?!file:)/, (route) => route.abort());
  const page = await context.newPage();

  // Self-tests: the detector must reject what a reader cannot see.
  const note = '<p data-attribution="hermes-independence">Nurse AI OS · Nous Research</p>';
  await page.setContent(`<main>${note}</main>`);
  check('a plain note is seen', (await page.evaluate(visibleNotes)).length === 1);
  await page.setContent(`<style>[data-attribution] { display: none }</style><main>${note}</main>`);
  check('a stylesheet rule that hides the note is caught', (await page.evaluate(visibleNotes)).length === 0);
  await page.setContent(`<style>[data-attribution] { opacity: 0 }</style><main>${note}</main>`);
  check('an invisible (opacity 0) note is caught', (await page.evaluate(visibleNotes)).length === 0);
  await page.setContent('<p data-attribution="hermes-independence">Nurse AI OS<p>Nous Research</p>');
  check('text after an omitted </p> is not part of the note',
    JSON.stringify(await page.evaluate(visibleNotes)) === '["Nurse AI OS"]');
  await page.setContent('<p data-attribution="hermes-independence">x<span hidden>Nous Research</span></p>');
  check('hidden text inside a note does not count',
    JSON.stringify(await page.evaluate(visibleNotes)) === '["x"]');

  // Every Hermes page, rendered with its own CSS and scripts.
  for (const rel of pages) {
    await page.goto(pathToFileURL(join(repo, rel)).href, { waitUntil: 'load' });
    if (rel in equivalent) {
      const text = await page.evaluate(() => document.body.innerText);
      check(`${rel}: equivalent attribution is visible`, text.includes(equivalent[rel]));
      continue;
    }
    const notes = await page.evaluate(visibleNotes);
    const first = rel.split('/')[0];
    const lang = rel.includes('/') && first in clauses ? first : 'en';
    const ok = notes.length === 1 && notes[0].includes('Nous Research')
      && notes[0].includes('Nurse AI OS') && notes[0].includes(clauses[lang]);
    check(`${rel}: one visible note with the ${lang} non-endorsement clause`, ok,
      JSON.stringify(notes));
  }
} finally {
  await browser.close();
}

console.log(failures ? `${failures} check(s) failed` : 'All attribution notes are visible.');
process.exit(failures ? 1 : 0);
