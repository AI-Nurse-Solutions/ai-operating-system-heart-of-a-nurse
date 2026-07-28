import assert from 'node:assert/strict';
import { createReadStream, statSync } from 'node:fs';
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
  '.png': 'image/png',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2'
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

await new Promise((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const { port } = server.address();
const browser = await chromium.launch({ channel: 'chrome', headless: true });

try {
  for (const width of [320, 390]) {
    const page = await browser.newPage({ viewport: { width, height: 844 } });
    const errors = [];
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('response', (response) => {
      if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });

    const response = await page.goto(`http://127.0.0.1:${port}/`);
    assert.equal(response?.status(), 200, `homepage must return HTTP 200 at ${width}px`);
    await page.locator('.leader-walkthrough-grid').waitFor();

    const geometry = await page.evaluate(() => {
      const visibleRects = (selector) => [...document.querySelectorAll(selector)]
        .filter((element) => {
          const style = getComputedStyle(element);
          return style.display !== 'none' && style.visibility !== 'hidden';
        })
        .map((element) => element.getBoundingClientRect());
      const cardButtons = visibleRects('.leader-walkthrough-card .btn');
      const navLinks = visibleRects('.leader-educator-home .nav-links a');
      return {
        cardButtonHeights: cardButtons.map((rect) => rect.height),
        navLinkHeights: navLinks.map((rect) => rect.height),
        pageOverflow: document.documentElement.scrollWidth > window.innerWidth,
        targetsWithinViewport: [...cardButtons, ...navLinks].every(
          (rect) => rect.left >= -0.5 && rect.right <= window.innerWidth + 0.5
        )
      };
    });

    assert.equal(geometry.pageOverflow, false, `homepage must not overflow at ${width}px`);
    assert.equal(geometry.targetsWithinViewport, true, `targets must remain in bounds at ${width}px`);
    assert.ok(geometry.cardButtonHeights.length >= 3, 'all walkthrough actions must be measurable');
    assert.ok(geometry.navLinkHeights.length >= 3, 'visible mobile navigation links must be measurable');
    assert.ok(
      geometry.cardButtonHeights.every((height) => height >= 44),
      `walkthrough actions must be at least 44px high at ${width}px: ${geometry.cardButtonHeights}`
    );
    assert.ok(
      geometry.navLinkHeights.every((height) => height >= 44),
      `mobile navigation links must be at least 44px high at ${width}px: ${geometry.navLinkHeights}`
    );
    await assert.doesNotReject(() => page.getByText('When you paste elsewhere:').waitFor());
    assert.equal(errors.length, 0, `browser console/network errors at ${width}px: ${errors.join(' | ')}`);
    await page.close();
  }

  console.log('LEADER_HOME_BROWSER_OK viewports=320,390 touch_targets>=44 overflow=0');
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}
