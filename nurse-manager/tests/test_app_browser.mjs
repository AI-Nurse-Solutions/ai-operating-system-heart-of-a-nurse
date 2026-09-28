// The local app as a manager meets it (ADR 0003).
//
// Launches `python -m nurse_manager.app` exactly as the packaged launcher
// does (minus opening a browser), then checks, in a real browser:
// - the launch token leaves the address bar
// - the page says the app is running on this computer and offers Quit
// - first-run onboarding works by keyboard and refuses identifiers with a
//   readable reason
// - a reload keeps the session, while a tab without the token is told it
//   is not connected
// - the sample path works
// - Quit really stops the process
//
// CHROME_PATH=/path/to/chrome overrides the system Chrome channel (local runs).
// NURSE_AI_OS_BIN=/path/to/nurse-ai-os runs it against a packaged build.
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright-core';

const src = fileURLToPath(new URL('../src', import.meta.url));
const env = { ...process.env, PYTHONPATH: src };
const work = mkdtempSync(join(tmpdir(), 'nm-app-'));

/** Launch the app; resolve with { child, url, exited }. */
const launch = (home) => new Promise((resolve, reject) => {
  const args = ['--no-browser', '--print-url', '--idle-timeout', '120', '--home', home];
  // NURSE_AI_OS_BIN runs the same journey against a packaged build.
  const child = process.env.NURSE_AI_OS_BIN
    ? spawn(process.env.NURSE_AI_OS_BIN, args, { env })
    : spawn('python3', ['-m', 'nurse_manager.app', ...args], { env });
  const exited = new Promise((done) => child.on('exit', (code) => done(code)));
  let out = '';
  child.stdout.on('data', (chunk) => {
    out += chunk;
    if (out.includes('\n')) resolve({ child, url: out.split('\n')[0].trim(), exited });
  });
  child.on('error', reject);
});

const apps = [];
let browser;
try {
  browser = await chromium.launch(process.env.CHROME_PATH
    ? { executablePath: process.env.CHROME_PATH, headless: true }
    : { channel: 'chrome', headless: true });

  // --- First run: start my own workspace ---------------------------------
  const own = await launch(join(work, 'own')); apps.push(own);
  assert.match(own.url, /^http:\/\/127\.0\.0\.1:\d+\/#token=[A-Za-z0-9_-]{20,}$/);
  const context = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await context.newPage();
  const errors = [];
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', (e) => errors.push(e.message));
  await page.goto(own.url);
  await page.waitForSelector('.view--onboarding');
  assert.equal(await page.title(), 'Welcome — Nurse AI OS');
  assert.ok(!page.url().includes('token'), 'the launch token leaves the address bar');
  assert.match(await page.getByRole('contentinfo').textContent(), /running on this computer.*2 minutes/s);
  assert.ok(await page.getByRole('button', { name: 'Quit Nurse AI OS' }).isVisible());
  assert.match(await page.getByRole('note').filter({ hasText: 'Before you start' }).textContent(),
    /Keep patient information, staff performance, and confidential employer material out/);

  // Keyboard onboarding, with an identifier refused first.
  await page.getByLabel('Workspace name').fill('Unit 4 planning');
  await page.getByLabel('Your name').fill('manager@example.org');
  await page.getByRole('button', { name: 'Create my workspace' }).focus();
  await page.keyboard.press('Enter');
  await page.waitForSelector('[role="alert"]');
  assert.match(await page.getByRole('alert').textContent(), /Not created.*does not keep identifying details.*EMAIL_ADDRESS/s);
  await page.getByLabel('Workspace name').fill('Unit planning');
  await page.getByLabel('Your name').fill('Test Manager');
  await page.getByLabel('Your name').press('Enter');
  await page.waitForFunction(() => document.activeElement?.tagName === 'H1'
    && document.activeElement.textContent === 'Mission Control', null, { timeout: 10000 });
  assert.equal(await page.locator('#workspace-name').textContent(), 'Unit planning');
  assert.equal(await page.getByRole('note').filter({ hasText: 'Sample workspace' }).count() === 0
    || !(await page.locator('#sample-banner').isVisible()), true, 'a real workspace is not labeled sample');
  assert.match(await page.getByRole('region', { name: "This week's priorities" }).textContent(), /No priorities set/);

  // A reload keeps the session; a fresh tab without the token is not connected.
  await page.reload();
  await page.waitForSelector('.view--mission');
  const stranger = await (await browser.newContext()).newPage();
  const base = own.url.split('#')[0];
  await stranger.goto(`${base}#/mission`);
  await stranger.waitForSelector('[role="alert"]');
  assert.match(await stranger.getByRole('alert').textContent(), /not connected to Nurse AI OS/);
  assert.equal(await stranger.locator('.view--mission').count(), 0, 'no records without the token');

  // Reflow at 320px on onboarding-free screens.
  await page.setViewportSize({ width: 320, height: 800 });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  assert.ok(overflow <= 0, `mission reflows at 320px (overflow ${overflow}px)`);
  await page.setViewportSize({ width: 1280, height: 900 });

  // Quit really stops the app.
  await page.getByRole('button', { name: 'Quit Nurse AI OS' }).click();
  await page.waitForFunction(() => document.activeElement?.textContent === 'Nurse AI OS has stopped');
  assert.equal(await page.getByRole('contentinfo').isVisible(), false);
  const code = await Promise.race([own.exited, new Promise((r) => setTimeout(() => r('still running'), 10000))]);
  assert.equal(code, 0, 'the process exits after Quit');
  assert.deepEqual(errors, [], 'no console errors on the connected page');

  // --- First run: explore the sample -------------------------------------
  const sample = await launch(join(work, 'sample')); apps.push(sample);
  const samplePage = await (await browser.newContext({ viewport: { width: 1280, height: 900 } })).newPage();
  await samplePage.goto(sample.url);
  await samplePage.waitForSelector('.view--onboarding');
  await samplePage.getByRole('button', { name: 'Explore the sample workspace' }).click();
  await samplePage.waitForSelector('.view--mission');
  assert.ok(await samplePage.locator('#sample-banner').isVisible(), 'the sample is labeled synthetic');
  assert.equal(await samplePage.getByRole('region', { name: "This week's priorities" }).getByRole('listitem').count(), 3);
  await samplePage.getByRole('button', { name: 'Quit Nurse AI OS' }).click();
  assert.equal(await Promise.race([sample.exited, new Promise((r) => setTimeout(() => r('still running'), 10000))]), 0);

  console.log('nurse-manager local app: token, onboarding, session, quit, sample pass');
} finally {
  await browser?.close();
  for (const app of apps) app.child.kill();
  rmSync(work, { recursive: true, force: true });
}
