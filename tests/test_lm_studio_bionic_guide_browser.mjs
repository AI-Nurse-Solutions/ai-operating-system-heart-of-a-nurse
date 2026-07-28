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
  for (const width of [320, 390, 768, 1024, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 900 } });
    const errors = [];
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('response', (response) => {
      if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`);
    });

    const response = await page.goto(`http://127.0.0.1:${port}/guides/nurse-ai-os-lm-studio-bionic/`);
    assert.equal(response?.status(), 200, `guide must return HTTP 200 at ${width}px`);
    await page.locator('.guide-path-grid').waitFor();

    const geometry = await page.evaluate(() => {
      const visibleRects = (selector) => [...document.querySelectorAll(selector)]
        .filter((element) => {
          const style = getComputedStyle(element);
          return style.display !== 'none' && style.visibility !== 'hidden';
        })
        .map((element) => element.getBoundingClientRect());
      const navLinks = visibleRects('.local-ai-guide .nav-links a');
      const heroButtons = visibleRects('.guide-hero .btn');
      const tableWrappers = [...document.querySelectorAll('.guide-table-wrap')];
      return {
        heroButtonHeights: heroButtons.map((rect) => rect.height),
        navLinkHeights: navLinks.map((rect) => rect.height),
        navLinkWidths: navLinks.map((rect) => rect.width),
        pageOverflow: document.documentElement.scrollWidth > window.innerWidth,
        targetsWithinViewport: [...navLinks, ...heroButtons].every(
          (rect) => rect.left >= -0.5 && rect.right <= window.innerWidth + 0.5
        ),
        tableWrappers: tableWrappers.map((element) => ({
          scrollable: element.scrollWidth > element.clientWidth,
          tabindex: element.getAttribute('tabindex')
        }))
      };
    });

    assert.equal(geometry.pageOverflow, false, `guide must not overflow at ${width}px`);
    assert.equal(geometry.targetsWithinViewport, true, `guide targets must remain in bounds at ${width}px`);
    assert.ok(geometry.navLinkHeights.length >= 4, 'all guide navigation links must be measurable');
    assert.ok(geometry.heroButtonHeights.length >= 2, 'both guide hero actions must be measurable');
    assert.equal(
      geometry.navLinkWidths.length,
      geometry.navLinkHeights.length,
      'every visible guide navigation link must have two-dimensional measurements'
    );
    assert.ok(
      geometry.navLinkHeights.every((height) => height >= 44),
      `guide navigation links must be at least 44px high at ${width}px: ${geometry.navLinkHeights}`
    );
    assert.ok(
      geometry.navLinkWidths.every((targetWidth) => targetWidth >= 44),
      `guide navigation links must be at least 44px wide at ${width}px: ${geometry.navLinkWidths}`
    );
    assert.ok(
      geometry.heroButtonHeights.every((height) => height >= 44),
      `guide hero actions must be at least 44px high at ${width}px: ${geometry.heroButtonHeights}`
    );
    assert.ok(geometry.tableWrappers.length >= 2, 'comparison tables must have overflow wrappers');
    assert.ok(
      geometry.tableWrappers.every(({ tabindex }) => tabindex === '0'),
      'scrollable table wrappers must be keyboard focusable'
    );
    if (width <= 390) {
      assert.ok(
        geometry.tableWrappers.every(({ scrollable }) => scrollable),
        `wide tables must scroll inside their wrappers at ${width}px`
      );
    }
    await assert.doesNotReject(() => page.getByRole('heading', { name: 'Pilot launch checklist' }).waitFor());
    assert.equal(errors.length, 0, `guide console/network errors at ${width}px: ${errors.join(' | ')}`);
    await page.close();
  }

  console.log('LM_STUDIO_BIONIC_GUIDE_BROWSER_OK viewports=320,390,768,1024,1280 touch_targets>=44 overflow=0');
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}
