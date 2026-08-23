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

    const response = await page.goto(`http://127.0.0.1:${port}/local-sovereign-systems/`);
    assert.equal(response?.status(), 200, `guide must return HTTP 200 at ${width}px`);
    await page.locator('h1').waitFor();
    await page.locator('.equipment-figure img').waitFor();
    await page.evaluate(async () => Promise.all(
      [...document.querySelectorAll('.equipment-showcase img')].map((image) => image.decode())
    ));

    const geometry = await page.evaluate(() => {
      const visibleRects = (selector) => [...document.querySelectorAll(selector)]
        .filter((element) => {
          const style = getComputedStyle(element);
          return style.display !== 'none' && style.visibility !== 'hidden';
        })
        .map((element) => element.getBoundingClientRect());
      const primaryControls = visibleRects('.sovereign-hero .btn, .source-list a');
      return {
        pageOverflow: document.documentElement.scrollWidth > window.innerWidth,
        controlHeights: primaryControls.map((rect) => rect.height),
        controlWidths: primaryControls.map((rect) => rect.width),
        h1Count: document.querySelectorAll('h1').length,
        mainCount: document.querySelectorAll('main').length,
        sourceCount: document.querySelectorAll('.source-list a').length,
        loginLanguage: document.body.innerText.includes('ChatGPT sign-in'),
        quietButtonColors: [...document.querySelectorAll('.btn-quiet')]
          .map((button) => getComputedStyle(button).color),
        equipmentImages: [...document.querySelectorAll('.equipment-showcase img')]
          .map((image) => ({ naturalWidth: image.naturalWidth, naturalHeight: image.naturalHeight })),
        equipmentKickerColor: getComputedStyle(document.querySelector('.equipment-showcase .kicker')).color
      };
    });

    assert.equal(geometry.pageOverflow, false, `page must not overflow at ${width}px`);
    assert.equal(geometry.h1Count, 1, `one h1 required at ${width}px`);
    assert.equal(geometry.mainCount, 1, `one main landmark required at ${width}px`);
    assert.equal(geometry.sourceCount, 4, `four evidence links required at ${width}px`);
    assert.equal(geometry.loginLanguage, false, `public guide must not require ChatGPT login at ${width}px`);
    assert.ok(geometry.quietButtonColors.every((color) => color === 'rgb(14, 31, 51)'), `quiet CTAs need navy text contrast at ${width}px`);
    assert.equal(geometry.equipmentImages.length, 2, `two equipment drawings required at ${width}px`);
    assert.ok(geometry.equipmentImages.every((image) => image.naturalWidth > 800 && image.naturalHeight > 700), `equipment drawings must decode at useful resolution at ${width}px`);
    assert.equal(geometry.equipmentKickerColor, 'rgb(236, 200, 127)', `equipment kicker needs gold contrast at ${width}px`);
    assert.ok(geometry.controlHeights.every((height) => height >= 44), `new controls must be at least 44px high at ${width}px`);
    assert.ok(geometry.controlWidths.every((controlWidth) => controlWidth >= 44), `new controls must be at least 44px wide at ${width}px`);
    assert.deepEqual(errors, [], `browser errors at ${width}px: ${errors.join('; ')}`);
    await page.close();
  }
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}

console.log('LOCAL_SOVEREIGN_BROWSER_OK viewports=320,390,768,1024,1280 overflow=0 sources=4 controls>=44');
