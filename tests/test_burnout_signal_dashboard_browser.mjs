import assert from 'node:assert/strict';
import { createReadStream, existsSync, readFileSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const mime = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.ico': 'image/x-icon',
  '.jpg': 'image/jpeg',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp'
};

const server = createServer((request, response) => {
  try {
    const url = new URL(request.url || '/', 'http://127.0.0.1');
    let relative = decodeURIComponent(url.pathname).replace(/^\/+/, '');
    if (!relative || relative.endsWith('/')) relative += 'index.html';
    const path = resolve(root, relative);
    if (path !== root && !path.startsWith(`${root}${sep}`)) throw new Error('outside root');
    if (!statSync(path).isFile()) throw new Error('not a file');
    response.writeHead(200, { 'content-type': mime[extname(path)] || 'application/octet-stream' });
    createReadStream(path).pipe(response);
  } catch {
    response.writeHead(404, { 'content-type': 'text/plain; charset=utf-8' });
    response.end('Not found');
  }
});

/* CI provides the Chrome channel like the other browser tests; sandboxed
   containers only ship the Playwright-managed Chromium, so fall back. */
async function launchBrowser() {
  const attempts = [
    () => chromium.launch({ channel: 'chrome', headless: true }),
    () => chromium.launch({ headless: true }),
    ...(existsSync('/opt/pw-browsers/chromium')
      ? [() => chromium.launch({ headless: true, executablePath: '/opt/pw-browsers/chromium' })]
      : [])
  ];
  let lastError;
  for (const attempt of attempts) {
    try { return await attempt(); } catch (error) { lastError = error; }
  }
  throw lastError;
}

function collectPageErrors(page, errors) {
  page.on('console', (message) => {
    // Ignore blocked third-party font fetches in offline sandboxes.
    if (message.type() === 'error' && !/googleapis|gstatic|net::ERR/i.test(message.text())) {
      errors.push(message.text());
    }
  });
  page.on('pageerror', (error) => errors.push(error.message));
}

async function saveWeek(page, week) {
  await page.fill('#week-of', week.weekOf);
  await page.fill('#staff-count', String(week.staffCount));
  await page.fill('#shifts-worked', String(week.shiftsWorked));
  await page.fill('#late-departures', String(week.lateDepartures));
  await page.fill('#breaks-missed', String(week.breaksMissed));
  await page.fill('#staff-no-pto', String(week.staffNoRecentPto));
  await page.getByRole('button', { name: 'Save week' }).click();
}

await new Promise((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const { port } = server.address();
const url = `http://127.0.0.1:${port}/burnout-signal-dashboard.html`;
const browser = await launchBrowser();

try {
  for (const width of [320, 390, 768, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 1100 } });
    const errors = [];
    collectPageErrors(page, errors);
    const response = await page.goto(url);
    assert.equal(response?.status(), 200, `dashboard must return HTTP 200 at ${width}px`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    assert.equal(overflow, false, `no horizontal page overflow at ${width}px`);
    assert.equal(errors.length, 0, `errors at ${width}px: ${errors.join(' | ')}`);
    await page.close();
  }

  const page = await browser.newPage({ viewport: { width: 390, height: 1200 } });
  const errors = [];
  collectPageErrors(page, errors);
  page.on('dialog', (dialog) => dialog.accept());
  await page.goto(url);

  assert.match(await page.locator('#empty-note').textContent(), /No weeks recorded yet/);

  // A valid unit-aggregate week computes rates and persists across reload.
  await saveWeek(page, { weekOf: '2026-07-06', staffCount: 12, shiftsWorked: 60, lateDepartures: 9, breaksMissed: 15, staffNoRecentPto: 4 });
  assert.match(await page.locator('#entry-status').textContent(), /Saved week of 2026-07-06/);
  const rowText = await page.locator('#weeks-body tr').first().textContent();
  assert.match(rowText, /15%/, 'late-departure rate 9/60');
  assert.match(rowText, /25%/, 'break-skip rate 15/60');
  assert.match(rowText, /33%/, 'PTO non-use 4/12');
  await page.reload();
  assert.equal(await page.locator('#weeks-body tr').count(), 1, 'entries persist in localStorage');

  // Impossible aggregates are rejected: counts cannot exceed denominators.
  await saveWeek(page, { weekOf: '2026-07-13', staffCount: 10, shiftsWorked: 20, lateDepartures: 25, breaksMissed: 0, staffNoRecentPto: 0 });
  assert.match(await page.locator('#entry-status').textContent(), /cannot exceed their denominators/);
  assert.equal(await page.locator('#weeks-body tr').count(), 1, 'invalid week is not stored');

  // Below the minimum staff count, the week is stored but every rate is withheld.
  await saveWeek(page, { weekOf: '2026-07-13', staffCount: 4, shiftsWorked: 20, lateDepartures: 5, breaksMissed: 8, staffNoRecentPto: 2 });
  assert.match(await page.locator('#entry-status').textContent(), /excluded from trends/);
  assert.equal(await page.locator('#weeks-body tr').count(), 2);
  assert.match(await page.locator('#weeks-body tr').nth(1).textContent(), /withheld/);
  assert.match(await page.locator('#threshold-notice').textContent(), /Minimum aggregation threshold/);
  assert.match(await page.locator('#trends').textContent(), /not enough to describe/i);

  // Clear-all empties the workspace after an explicit confirm.
  await page.getByRole('button', { name: 'Clear all data' }).click();
  assert.equal(await page.locator('#weeks-body tr').count(), 0);
  assert.match(await page.locator('#entry-status').textContent(), /All data cleared/);

  // The synthetic example is clearly labeled and produces descriptive flags only.
  await page.getByRole('button', { name: 'Load synthetic example' }).click();
  assert.equal(await page.locator('#weeks-body tr').count(), 5);
  for (const cell of await page.locator('#weeks-body th[scope="row"]').all()) {
    assert.match(await cell.textContent(), /\(synthetic\)/, 'every example week is labeled synthetic');
  }
  assert.equal(await page.locator('#trends svg[role="img"]').count(), 3, 'one accessible chart per indicator');
  const flags = await page.locator('#trends .flag').all();
  assert.equal(flags.length, 3, 'one plain-language reading per indicator');
  for (const flag of flags) {
    const text = await flag.textContent();
    assert.match(text, /risen across the last 3 recorded weeks/, 'synthetic data rises for three consecutive weeks');
    assert.match(text, /not a conclusion about anyone/, 'flags describe patterns, never people or actions');
  }

  // The Mission Control export is born a draft with the leader-template sections.
  const summaryPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export Mission Control dashboard-summary draft' }).click();
  const summary = readFileSync(await (await summaryPromise).path(), 'utf8');
  for (const required of [
    'DRAFT — tool-generated scaffold.',
    'Generation alone never makes content final.',
    '## Measures included',
    '## What changed',
    '## Limitations',
    '## Suggested attention',
    'Contains synthetic example data.',
    'Laudio Insights / AONL',
    'underreporting'
  ]) {
    assert.ok(summary.includes(required), `summary draft must include: ${required}`);
  }
  assert.ok(
    summary.includes('suggestions to look, not conclusions and not recommended actions')
      && summary.includes('Interpretation and any next step belong to the reviewing human'),
    'summary keeps the observe-mode disclaimers'
  );

  // The JSON export carries only unit aggregates.
  const jsonPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Export data (JSON)' }).click();
  const exported = JSON.parse(readFileSync(await (await jsonPromise).path(), 'utf8'));
  assert.equal(exported.aggregateOnly, true);
  assert.equal(exported.weeks.length, 5);
  for (const week of exported.weeks) {
    assert.deepEqual(
      Object.keys(week).sort(),
      ['breaksMissed', 'lateDepartures', 'shiftsWorked', 'source', 'staffCount', 'staffNoRecentPto', 'weekOf'],
      'export rows contain only aggregate fields'
    );
  }

  assert.equal(errors.length, 0, `functional-flow errors: ${errors.join(' | ')}`);
  await page.close();

  console.log('BURNOUT_SIGNAL_DASHBOARD_BROWSER_OK viewports=320,390,768,1280 persistence=localStorage threshold=withheld flags=descriptive exports=draft+json');
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}
