import { chromium } from 'playwright-core';
import { pathToFileURL } from 'node:url';

const [inputPath, outputPath] = process.argv.slice(2);
if (!inputPath || !outputPath) {
  console.error('usage: render-media-pdf.mjs INPUT_HTML OUTPUT_PDF');
  process.exit(2);
}

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage'],
});
try {
  const page = await browser.newPage();
  await page.goto(pathToFileURL(inputPath).href, { waitUntil: 'load' });
  await page.emulateMedia({ media: 'print' });
  await page.evaluate(() => document.fonts.ready);
  await page.pdf({
    path: outputPath,
    format: 'Letter',
    preferCSSPageSize: true,
    printBackground: true,
    displayHeaderFooter: false,
  });
} finally {
  await browser.close();
}
