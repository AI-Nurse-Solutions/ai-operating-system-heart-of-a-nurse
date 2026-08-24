import assert from 'node:assert/strict';
import { createReadStream, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const isOptionalExternal = (url) => /^https:\/\/fonts\.(googleapis|gstatic)\.com\//.test(url || '');
const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const mime = {
  '.css': 'text/css; charset=utf-8',
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.jpg': 'image/jpeg',
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
    const page = await browser.newPage({ viewport: { width, height: 844 } });
    const errors = [];
    page.on('console', (message) => {
      if (message.type() === 'error' && !isOptionalExternal(message.location()?.url)) errors.push(message.text());
    });
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('response', (response) => {
      if (response.status() >= 400 && !isOptionalExternal(response.url())) errors.push(`${response.status()} ${response.url()}`);
    });

    const response = await page.goto(`http://127.0.0.1:${port}/personal-ai-datacenter/`);
    assert.equal(response?.status(), 200, `gallery must return HTTP 200 at ${width}px`);
    await page.locator('h1').waitFor();
    await page.locator('.build-card img').first().waitFor();
    await page.evaluate(async () => {
      const images = [...document.querySelectorAll('.build-card img')];
      for (const image of images) {
        image.loading = 'eager';
        image.scrollIntoView({ block: 'center' });
        if (!image.complete) {
          await new Promise((resolveImage, rejectImage) => {
            image.addEventListener('load', resolveImage, { once: true });
            image.addEventListener('error', rejectImage, { once: true });
          });
        }
        await image.decode();
      }
      window.scrollTo(0, 0);
    });

    const geometry = await page.evaluate(() => {
      const visibleRects = (selector) => [...document.querySelectorAll(selector)]
        .filter((element) => {
          const style = getComputedStyle(element);
          return style.display !== 'none' && style.visibility !== 'hidden';
        })
        .map((element) => element.getBoundingClientRect());
      const controls = visibleRects('.datacenter-hero .btn, .source-links a, .section .btn');
      return {
        overflow: document.documentElement.scrollWidth > window.innerWidth,
        h1Count: document.querySelectorAll('h1').length,
        mainCount: document.querySelectorAll('main').length,
        buildCount: document.querySelectorAll('.build-card').length,
        imageData: [...document.querySelectorAll('.build-card img')]
          .map((image) => ({ naturalWidth: image.naturalWidth, naturalHeight: image.naturalHeight })),
        controlHeights: controls.map((rect) => rect.height),
        controlWidths: controls.map((rect) => rect.width),
        quietButtonColors: [...document.querySelectorAll('.btn-quiet')]
          .map((button) => getComputedStyle(button).color),
        statusVisible: document.body.innerText.includes('Not a validated BOM, build guide, or purchase recommendation')
      };
    });

    assert.equal(geometry.overflow, false, `page must not overflow at ${width}px`);
    assert.equal(geometry.h1Count, 1, `one h1 required at ${width}px`);
    assert.equal(geometry.mainCount, 1, `one main landmark required at ${width}px`);
    assert.equal(geometry.buildCount, 5, `five build concepts required at ${width}px`);
    assert.equal(geometry.imageData.length, 8, `eight recovered drawings required at ${width}px`);
    assert.ok(geometry.imageData.every((image) => image.naturalWidth >= 1600 && image.naturalHeight >= 900), `drawings must decode at useful resolution at ${width}px`);
    assert.ok(geometry.controlHeights.every((height) => height >= 44), `controls must be at least 44px high at ${width}px`);
    assert.ok(geometry.controlWidths.every((controlWidth) => controlWidth >= 44), `controls must be at least 44px wide at ${width}px`);
    assert.ok(geometry.quietButtonColors.every((color) => color === 'rgb(14, 31, 51)'), `quiet CTA text needs navy contrast at ${width}px`);
    assert.equal(geometry.statusVisible, true, `draft-specification boundary must be visible at ${width}px`);
    assert.deepEqual(errors, [], `browser errors at ${width}px: ${errors.join('; ')}`);
    await page.close();
  }
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}

console.log('PERSONAL_AI_DATACENTER_BROWSER_OK viewports=320,390,768,1024,1280 builds=5 drawings=8 overflow=0 controls>=44');
