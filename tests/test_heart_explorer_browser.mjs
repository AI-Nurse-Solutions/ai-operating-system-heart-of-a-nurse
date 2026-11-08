import assert from 'node:assert/strict';
import { createReadStream, existsSync, readFileSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const graph = JSON.parse(readFileSync(resolve(root, 'heart-explorer/heart-graph.json'), 'utf8'));
const mime = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
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

await new Promise((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const { port } = server.address();
const base = `http://127.0.0.1:${port}/heart-explorer/`;
const browser = await launchBrowser();

try {
  for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
    const page = await browser.newPage({ viewport });
    const errors = [];
    page.on('console', (message) => {
      const target = `${message.text()} ${message.location()?.url || ''}`;
      if (message.type() === 'error' && !/fonts\.googleapis\.com|fonts\.gstatic\.com/i.test(target)) errors.push(message.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));

    await page.goto(base, { waitUntil: 'networkidle' });
    const cards = page.locator('#hx-list button');
    assert.equal(await cards.count(), graph.nodes.length, 'every card is listed');
    assert.match(await page.locator('#hx-count').textContent(), new RegExp(`${graph.nodes.length} of ${graph.nodes.length} cards`));
    assert.match(await page.locator('#hx-boundary').textContent(), /Educational content only, not clinical guidance/);
    assert.equal(await page.locator('meta[name="robots"]').getAttribute('content'), 'noindex, nofollow');

    // Selecting a card shows it with its draft badge, levers, links and sources.
    await page.getByRole('button', { name: 'Aortic stenosis', exact: true }).click();
    const card = page.locator('#hx-card');
    await assert.doesNotReject(card.getByRole('heading', { name: 'Aortic stenosis', level: 2 }).waitFor());
    assert.match(await card.textContent(), /Draft, pending clinical review/);
    assert.match(await card.textContent(), /↑ Raises afterload/);
    assert.match(await card.textContent(), /Treat as preload-dependent/);
    assert.ok(await card.getByRole('link', { name: 'TAVR' }).count());
    assert.ok(await card.locator('a[href="https://doi.org/10.1161/CIR.0000000000000923"]').count(), 'guideline citation links to its DOI');
    assert.equal(new URL(page.url()).hash, '#aortic-stenosis');
    assert.equal(await page.locator('#hx-list button[aria-current="true"]').textContent(), 'Aortic stenosis');

    // Following a connection opens the linked card, and the reverse link shows up there.
    await card.getByRole('link', { name: 'TAVR' }).click();
    await card.getByRole('heading', { name: 'TAVR', level: 2 }).waitFor();
    assert.match(await card.textContent(), /Used to treat/);
    assert.ok(await card.getByRole('link', { name: 'Aortic stenosis' }).count());

    // Back returns to the previous card.
    await page.goBack();
    await card.getByRole('heading', { name: 'Aortic stenosis', level: 2 }).waitFor();

    // Search and lever filters narrow the list.
    await page.fill('#hx-search', 'lactate');
    assert.deepEqual(await cards.allTextContents(), ['Elevated lactate']);
    await page.fill('#hx-search', '');
    await page.selectOption('#hx-lever', 'afterload');
    const afterload = graph.nodes.filter((node) => (node.levers || []).some((lever) => lever.lever === 'afterload'));
    assert.equal(await cards.count(), afterload.length);
    assert.ok((await cards.allTextContents()).includes('VA-ECMO'));
    await page.fill('#hx-search', 'zzzz');
    assert.match(await page.locator('#hx-list').textContent(), /No cards match/);

    // Deep links open directly, and in-page anchors such as the skip link keep the card.
    await page.goto(`${base}#va-ecmo`, { waitUntil: 'networkidle' });
    await card.getByRole('heading', { name: 'VA-ECMO', level: 2 }).waitFor();
    assert.match(await card.textContent(), /↑ Raises afterload/);
    await page.evaluate(() => { location.hash = 'hx-card'; });
    await page.waitForTimeout(50);
    assert.equal(await card.getByRole('heading', { level: 2 }).textContent(), 'VA-ECMO');

    // Keyboard users can reach and open cards.
    await page.fill('#hx-search', '');
    await page.selectOption('#hx-lever', '');
    await page.locator('#hx-list button').first().focus();
    await page.keyboard.press('Enter');
    await card.getByRole('heading', { name: graph.nodes[0].label, level: 2 }).waitFor();

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `no horizontal scroll at ${viewport.width}px (overflow ${overflow}px)`);
    assert.deepEqual(errors, []);
    await page.close();
  }
  console.log('heart explorer browser tests passed');
} finally {
  await browser.close();
  server.close();
}
