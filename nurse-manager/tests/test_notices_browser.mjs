// Hermes independence notes as a browser renders them (build step 0.8).
//
// test_notices.py checks the markup statically. This test is the authority on
// what a reader actually sees: it opens every page whose <title> names Hermes
// in Chromium, with the site's own stylesheets and scripts, and requires
// exactly one attribution note that a reader can see and read. The note's
// rendered text (innerText, which drops hidden descendants and honours
// implicit end tags) must name Nous Research and Nurse AI OS and carry the
// page language's non-endorsement clause. The page list and the clauses come
// from test_notices.py, so both tests agree.
//
// "Can see and read" is decided in two steps:
//   1. In the page: the note is visible to CSS (display, visibility,
//      opacity); once scrolled to, it overlaps the viewport; and it is what
//      the browser paints at the centre of that overlap, so a note moved
//      off-canvas, clipped away or covered by another element fails.
//   2. In pixels: the note is screenshotted as rendered and again with its
//      text forced transparent. Enough pixels must differ between the two by
//      at least 3:1 contrast, so text that is transparent, coloured like its
//      background (a colour, gradient or image), too faint or too small to
//      read fails. The browser decodes the screenshots itself, so no image
//      library is needed.
//
// Each page is checked at a phone and a desktop viewport, so a responsive
// rule cannot hide the note from phone readers only.
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
  "print(json.dumps({'pages': t.hermes_pages(), 'clauses': t.NON_ENDORSEMENT_CLAUSE}))",
].join('\n')], { cwd: repo, encoding: 'utf8' });
assert.equal(load.status, 0, load.stderr);
const { pages, clauses } = JSON.parse(load.stdout);
assert.ok(pages.length >= 14, `expected the known Hermes pages, found ${pages.length}`);

const MARKER = '[data-attribution="hermes-independence"]';
// Pixels of the note's text that must stand out 3:1 from what is behind them.
// A 14px sentence paints thousands; transparent or background-coloured text
// paints none, and 1px text a handful.
const MIN_LEGIBLE_PIXELS = 200;

/** Step 1, run in the page: notes that are visible, on screen and on top. */
const onScreenNotes = (marker) => [...document.querySelectorAll(marker)]
  .map((el, index) => ({ el, index }))
  .filter(({ el }) => {
    if (!el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
    el.scrollIntoView({ block: 'center', inline: 'center' });
    const box = el.getBoundingClientRect();
    const left = Math.max(box.left, 0);
    const right = Math.min(box.right, window.innerWidth);
    const top = Math.max(box.top, 0);
    const bottom = Math.min(box.bottom, window.innerHeight);
    if (right - left < 1 || bottom - top < 1) return false;
    const hit = document.elementFromPoint((left + right) / 2, (top + bottom) / 2);
    return hit !== null && el.contains(hit);
  })
  .map(({ el, index }) => ({ index, text: el.innerText.replace(/\s+/g, ' ').trim() }));

/** Count pixels where the rendered note differs from its text-less twin by >= 3:1. */
const legiblePixels = async ([withText, withoutText]) => {
  const decode = async (b64) => {
    const img = new Image();
    img.src = `data:image/png;base64,${b64}`;
    await img.decode();
    const canvas = new OffscreenCanvas(img.width, img.height);
    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0);
    return ctx.getImageData(0, 0, img.width, img.height).data;
  };
  const [a, b] = await Promise.all([decode(withText), decode(withoutText)]);
  const lin = (c) => { const v = c / 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; };
  const lum = (d, i) => 0.2126 * lin(d[i]) + 0.7152 * lin(d[i + 1]) + 0.0722 * lin(d[i + 2]);
  let count = 0;
  for (let i = 0; i < a.length && i < b.length; i += 4) {
    const x = lum(a, i);
    const y = lum(b, i);
    if ((Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05) >= 3) count += 1;
  }
  return count;
};

/** Step 2: keep the on-screen notes whose text is actually painted legibly. */
const readableNotes = async (page) => {
  const candidates = await page.evaluate(onScreenNotes, MARKER);
  const readable = [];
  for (const { index, text } of candidates) {
    const note = page.locator(MARKER).nth(index);
    await note.scrollIntoViewIfNeeded();
    const box = await note.boundingBox();
    if (!box || box.width < 1 || box.height < 1) continue;
    const clip = { x: box.x, y: box.y, width: box.width, height: box.height };
    const withText = (await page.screenshot({ clip, animations: 'disabled' })).toString('base64');
    const probe = await page.addStyleTag({ content:
      `${MARKER}, ${MARKER} * { color: transparent !important;
        -webkit-text-fill-color: transparent !important; text-shadow: none !important;
        text-decoration-color: transparent !important; caret-color: transparent !important; }` });
    const withoutText = (await page.screenshot({ clip, animations: 'disabled' })).toString('base64');
    await probe.evaluate((node) => node.remove());
    if (await page.evaluate(legiblePixels, [withText, withoutText]) >= MIN_LEGIBLE_PIXELS) {
      readable.push(text);
    }
  }
  return readable;
};

const VIEWPORTS = [
  { name: 'phone', width: 390, height: 844 },
  { name: 'desktop', width: 1280, height: 800 },
];

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
  const count = async (html) => {
    await page.setContent(html);
    return (await readableNotes(page)).length;
  };
  const texts = async (html) => {
    await page.setContent(html);
    return JSON.stringify(await readableNotes(page));
  };

  // Self-tests: the detector must reject what a reader cannot see or read.
  const words = 'Nurse AI OS is independent of Nous Research and not endorsed by it.';
  const note = `<p data-attribution="hermes-independence">${words}</p>`;
  const onDark = 'body { background: linear-gradient(160deg, #0e1f33, #1d3b5c); color: #e8eef4 }';
  await page.setViewportSize(VIEWPORTS[1]);
  check('a plain note is seen', await count(`<main>${note}</main>`) === 1);
  check('a light note on a dark gradient is seen', await count(`<style>${onDark}</style>${note}`) === 1);
  check('a note further down the page is seen', await count(`<div style="height:3000px"></div>${note}`) === 1);
  check('a stylesheet rule that hides the note is caught',
    await count(`<style>${MARKER} { display: none }</style>${note}`) === 0);
  check('an invisible (opacity 0) note is caught', await count(`<style>${MARKER} { opacity: 0 }</style>${note}`) === 0);
  check('a note moved off-canvas is caught',
    await count(`<style>${MARKER} { position: absolute; left: -10000px }</style>${note}`) === 0);
  check('a note covered by another element is caught', await count(`<main style="position:relative">${note}
    <div style="position:absolute; inset:0; background:#fff"></div></main>`) === 0);
  check('a note clipped away is caught', await count(`<style>${MARKER} { clip-path: inset(50%) }</style>${note}`) === 0);
  check('a note with transparent text is caught',
    await count(`<style>${MARKER} { color: transparent }</style>${note}`) === 0);
  check('a note coloured like its background is caught',
    await count(`<style>body { background: #fff } ${MARKER} { color: #fff }</style>${note}`) === 0);
  check('a note coloured like its gradient background is caught',
    await count(`<style>${onDark} ${MARKER} { color: #13283f }</style>${note}`) === 0);
  check('a faint (under 3:1) note is caught',
    await count(`<style>body { background: #fff } ${MARKER} { color: #d0d0d0 }</style>${note}`) === 0);
  check('a note in unreadably small text is caught',
    await count(`<style>${MARKER} { font-size: 1px }</style>${note}`) === 0);
  check('text after an omitted </p> is not part of the note',
    await texts(`<p data-attribution="hermes-independence">${words}<p>Nous Research</p>`) === JSON.stringify([words]));
  check('hidden text inside a note does not count',
    await texts(`<p data-attribution="hermes-independence">${words}<span hidden>extra</span></p>`)
      === JSON.stringify([words]));
  const phoneOnly = `<style>@media (max-width: 600px) { ${MARKER} { display: none } }</style>${note}`;
  await page.setViewportSize(VIEWPORTS[0]);
  check('a note hidden only at phone width is caught at phone width', await count(phoneOnly) === 0);
  await page.setViewportSize(VIEWPORTS[1]);
  check('the same note is seen at desktop width', await count(phoneOnly) === 1);

  // Every Hermes page, rendered with its own CSS and scripts, at each viewport.
  for (const viewport of VIEWPORTS) {
    await page.setViewportSize(viewport);
    for (const rel of pages) {
      await page.goto(pathToFileURL(join(repo, rel)).href, { waitUntil: 'load' });
      const notes = await readableNotes(page);
      const first = rel.split('/')[0];
      const lang = rel.includes('/') && first in clauses ? first : 'en';
      const ok = notes.length === 1 && notes[0].includes('Nous Research')
        && notes[0].includes('Nurse AI OS') && notes[0].includes(clauses[lang]);
      check(`${viewport.name} ${rel}: one readable note with the ${lang} non-endorsement clause`,
        ok, JSON.stringify(notes));
    }
  }
} finally {
  await browser.close();
}

console.log(failures ? `${failures} check(s) failed` : 'All attribution notes are visible and readable.');
process.exit(failures ? 1 : 0);
