import assert from 'node:assert/strict';
import { createReadStream, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const mime = { '.html': 'text/html; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8', '.svg': 'image/svg+xml' };

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
const baseUrl = `http://127.0.0.1:${port}/portal/`;

async function launch() {
  try {
    return await chromium.launch({ channel: 'chrome', headless: true });
  } catch {
    /* no branded Chrome — try the default chromium download */
  }
  try {
    return await chromium.launch({ headless: true });
  } catch {
    /* fall back to an explicitly provided chromium binary */
  }
  const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE || '/opt/pw-browsers/chromium';
  return chromium.launch({ headless: true, executablePath });
}

let browser;
let page;
try {
  browser = await launch();
  page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
} catch (error) {
  // Without this, a failed Chromium launch leaves the HTTP server holding
  // the event loop open and the test hangs instead of failing.
  if (browser) await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
  throw error;
}
const errors = [];
const isOptionalFontUrl = (url) => url.startsWith('https://fonts.googleapis.com/') || url.startsWith('https://fonts.gstatic.com/');
page.on('console', (message) => {
  const location = message.location().url || '';
  if (message.type() === 'error' && !isOptionalFontUrl(location)) errors.push(`${message.text()} @ ${location}`);
});
page.on('pageerror', (error) => errors.push(error.message));

try {
  const response = await page.goto(baseUrl);
  assert.equal(response?.status(), 200, 'portal route must return HTTP 200');
  await page.evaluate(() => localStorage.clear());
  await page.reload();

  // Governance boundary is visible before sign-in, on the static shell.
  await page.getByText('For Nurse AI OS setup, education, maintenance, and improvement support only.').waitFor();
  await page.getByRole('heading', { name: 'Preview the portal' }).waitFor();

  // ---- client journey ----
  await page.getByRole('button', { name: 'Enter as demo client →' }).click();
  await page.getByRole('heading', { name: 'Riverbend Nursing Education Cohort' }).waitFor();
  assert.match(await page.locator('.progress-meter + p').textContent(), /\d+%/);
  await page.getByText('Recommended next actions').waitFor();

  // Action plan: update a status with a comment.
  await page.getByRole('link', { name: 'Home' }).waitFor();
  await page.goto(`${baseUrl}#/actions`);
  await page.getByRole('heading', { name: 'Maintenance & improvement plan' }).waitFor();
  const firstForm = page.locator('[data-action-id="act-1"] form');
  await firstForm.locator('select[name="status"]').selectOption('started');
  await firstForm.locator('input[name="comment"]').fill('Scheduled for Friday huddle');
  await firstForm.getByRole('button', { name: 'Save update' }).click();
  await page.getByText('Action updated.').waitFor();

  // New question: PHI-shaped text is challenged, clean text goes through.
  await page.goto(`${baseUrl}#/messages/new`);
  await page.getByText('Before you type:').waitFor();
  await page.locator('input[name="subject"]').fill('Slide wording check');
  await page.locator('textarea[name="body"]').fill('Patient name: J. Smith needs this workflow');
  await page.getByRole('button', { name: 'Submit question →' }).click();
  await page.locator('.screen-warning').waitFor();
  assert.match(await page.locator('.screen-warning').textContent(), /patient-identifying language/);
  await page.locator('textarea[name="body"]').fill('Can you sanity-check our student-facing slide wording?');
  await page.getByRole('button', { name: 'Submit question →' }).click();
  await page.getByRole('heading', { name: 'Slide wording check' }).waitFor();

  // ---- admin journey ----
  await page.getByRole('button', { name: 'View as Robert (admin)' }).click();
  await page.getByRole('heading', { name: 'Client portfolio' }).waitFor();
  await page.getByRole('link', { name: 'Riverbend Nursing Education Cohort' }).click();
  await page.getByRole('heading', { name: 'Client record & approved AI context' }).waitFor();

  // Open the client's new question and draft with AI.
  await page.getByRole('link', { name: 'Slide wording check' }).click();
  await page.getByRole('button', { name: 'Draft with AI' }).click();
  await page.getByText('Draft ready — review and edit before sending.').waitFor();
  const drafted = await page.locator('textarea[name="body"]').inputValue();
  assert.ok(drafted.length > 80, 'draft should be substantial');
  assert.equal(await page.locator('input[name="aiAssisted"]').isChecked(), true);
  await page.getByRole('button', { name: 'Approve & send reply →' }).click();
  await page.getByText('Reply sent to the client.').waitFor();
  await page.getByText('AI-assisted · human approved').waitFor();

  // Client sees the answer with the AI-assisted label.
  await page.getByRole('button', { name: 'View as client' }).click();
  await page.goto(`${baseUrl}#/messages`);
  const answeredRow = page.locator('li', { hasText: 'Slide wording check' });
  await answeredRow.getByText('Answered').waitFor();

  // Mobile: no horizontal overflow.
  await page.setViewportSize({ width: 360, height: 780 });
  await page.goto(`${baseUrl}#/home`);
  await page.getByRole('heading', { name: 'Riverbend Nursing Education Cohort' }).waitFor();
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, '360px layout must not overflow');

  assert.deepEqual(errors, [], `browser console errors: ${errors.join(' | ')}`);
  console.log('PORTAL_BROWSER_SMOKE_OK');
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}
