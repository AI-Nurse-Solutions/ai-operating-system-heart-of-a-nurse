import assert from 'node:assert/strict';
import { createReadStream, readFileSync, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { chromium } from 'playwright-core';

const root = resolve(fileURLToPath(new URL('..', import.meta.url)));
const mime = {
  '.css': 'text/css; charset=utf-8', '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
  '.svg': 'image/svg+xml', '.png': 'image/png', '.webp': 'image/webp'
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

const packageInspectionScript = `
import json,sys,zipfile
p=sys.argv[1]
with zipfile.ZipFile(p) as z:
 profile=json.loads(z.read('ally-soul-profile.json'))
 dashboard=z.read('manager-ally-collaboration-dashboard.html').decode('utf-8')
 print(json.dumps({'names':sorted(z.namelist()),'bad':z.testzip(),'profile':profile,'dashboard':dashboard}))
`;

async function completeSafety(page, name = 'Alex & Team') {
  await page.locator('#display-name').fill(name);
  for (const checkbox of await page.locator('input[name^="safety-"]').all()) await checkbox.check();
  await page.getByRole('button', { name: 'Continue →' }).click();
  await page.getByRole('heading', { name: 'Name the capability you bring' }).waitFor();
}

await new Promise((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const { port } = server.address();
const browser = await chromium.launch({ channel: 'chrome', headless: true });

try {
  for (const width of [320, 390, 768, 1024, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 950 } });
    const errors = [];
    const externalRequests = [];
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('request', (request) => {
      const url = new URL(request.url());
      if (url.hostname !== '127.0.0.1') externalRequests.push(request.url());
    });
    const response = await page.goto(`http://127.0.0.1:${port}/technical-ally-soul-quiz/`);
    assert.equal(response?.status(), 200, `quiz must return HTTP 200 at ${width}px`);
    await page.locator('#display-name').waitFor();
    assert.match(await page.locator('.boundary-panel').textContent(), /cannot detect every form of sensitive information/i);
    const geometry = await page.evaluate(() => {
      const visible = (selector) => [...document.querySelectorAll(selector)].filter((element) => getComputedStyle(element).display !== 'none').map((element) => element.getBoundingClientRect());
      const controls = visible('.quiz-section button, .ally-brand, .safety-check');
      return {
        overflow: document.documentElement.scrollWidth > innerWidth,
        safetyCount: document.querySelectorAll('input[name^="safety-"]').length,
        mainCount: document.querySelectorAll('main').length,
        h1Count: document.querySelectorAll('h1').length,
        withinViewport: controls.every((rect) => rect.left >= -0.5 && rect.right <= innerWidth + 0.5),
        controlHeights: controls.map((rect) => rect.height),
        controlWidths: controls.map((rect) => rect.width)
      };
    });
    assert.equal(geometry.overflow, false, `no horizontal overflow at ${width}px`);
    assert.equal(geometry.safetyCount, 5, `five safety commitments at ${width}px`);
    assert.equal(geometry.mainCount, 1);
    assert.equal(geometry.h1Count, 1);
    assert.equal(geometry.withinViewport, true, `controls remain in viewport at ${width}px`);
    assert.ok(geometry.controlHeights.every((height) => height >= 44), `controls >=44px high at ${width}px`);
    assert.ok(geometry.controlWidths.every((controlWidth) => controlWidth >= 44), `controls >=44px wide at ${width}px`);
    assert.deepEqual(externalRequests, [], `no external requests at ${width}px`);
    assert.deepEqual(errors, [], `no browser errors at ${width}px: ${errors.join(' | ')}`);
    await page.close();
  }

  const page = await browser.newPage({ viewport: { width: 390, height: 1000 } });
  const errors = [];
  const externalRequests = [];
  page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('request', (request) => { if (new URL(request.url()).hostname !== '127.0.0.1') externalRequests.push(request.url()); });
  await page.goto(`http://127.0.0.1:${port}/technical-ally-soul-quiz/`);
  await completeSafety(page);
  assert.equal(await page.locator('#quiz-app h2').evaluate((element) => document.activeElement === element), true, 'step heading receives focus');

  await page.locator('input[name="background"][value="software-engineering"]').check();
  await page.locator('input[name="background"][value="automation-integrations"]').check();
  await page.locator('input[name="background"][value="technical-business"]').check();
  await page.locator('input[name="experience"][value="founder"]').check();
  await page.locator('input[name="relationship"][value="invited-by-nurse"]').check();
  await page.getByRole('button', { name: 'Continue →' }).click();

  for (const value of ['workflow-mapping', 'prototype-building', 'business-validation']) await page.locator(`input[name="contribution"][value="${value}"]`).check();
  for (const value of ['meeting-action', 'workflow-spec']) await page.locator(`input[name="manager-needs"][value="${value}"]`).check();
  await page.getByRole('button', { name: 'Continue →' }).click();

  await page.locator('input[name="business-stage"][value="customer-discovery"]').check();
  await page.locator('input[name="business-model"][value="professional-service"]').check();
  await page.locator('#business-boundary').fill('No clinical automation, workforce scoring, or unsupported outcome claims.');
  for (const checkbox of await page.locator('input[name^="venture-"]').all()) await checkbox.check();
  await page.getByRole('button', { name: 'Continue →' }).click();

  await page.locator('input[name="first-outcome"][value="meeting-to-action"]').check();
  await page.locator('#outcome-detail').fill('Turn approved non-sensitive meeting notes into a review-ready action brief.');
  await page.locator('#ally-responsibility').fill('Build the draft-only prototype, tests, documentation, and rollback path.');
  await page.locator('#nurse-rights').fill('The nurse manager defines nursing meaning, accepts the result, and decides whether work continues.');
  await page.locator('#success-signal').fill('The manager accepts the brief with less rework and returns with a second bounded problem.');
  await page.locator('input[name="review-cadence"][value="weekly"]').check();
  for (const value of ['phi-sensitive-data', 'authority-expansion', 'nurse-disagreement', 'unexpected-permission']) await page.locator(`input[name="stop-condition"][value="${value}"]`).check();
  await page.getByRole('button', { name: 'Build my results and dashboard →' }).click();
  await page.getByRole('heading', { name: 'Download your results with the manager dashboard' }).waitFor();
  assert.match(await page.locator('.results').textContent(), /Nurse-Supporting Workflow Engineer/);
  assert.match(await page.locator('.results').textContent(), /Governed technical service, consulting, or implementation sprint/);
  assert.match(await page.locator('.results').textContent(), /EDENA: Not evaluated · A0\/no action · Draft only/);
  assert.equal(await page.getByRole('button', { name: '← Review answers' }).isVisible(), true, 'review answers control is visible');
  const secondaryColors = await page.locator('.quiz-section .btn-secondary').evaluateAll((buttons) => buttons.map((button) => ({ color: getComputedStyle(button).color, border: getComputedStyle(button).borderColor })));
  assert.ok(secondaryColors.every(({ color, border }) => color === 'rgb(14, 31, 51)' && border === 'rgb(14, 31, 51)'), 'secondary quiz controls use navy text and borders');
  const skipState = await page.locator('.skip-link').evaluate((link) => {
    const rect = link.getBoundingClientRect();
    return { focused: document.activeElement === link, bottom: rect.bottom, transform: getComputedStyle(link).transform };
  });
  assert.equal(skipState.focused, false, 'skip link is not focused after results render');
  assert.ok(skipState.bottom < 0, `skip link stays offscreen when unfocused: ${JSON.stringify(skipState)}`);
  assert.equal(await page.evaluate(() => localStorage.length), 0, 'quiz never uses localStorage');
  assert.equal(await page.evaluate(() => sessionStorage.length), 1, 'one tab-local draft exists');

  const packagePromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download results + dashboard ZIP' }).click();
  const packageDownload = await packagePromise;
  assert.equal(packageDownload.suggestedFilename(), 'Nurse-AI-OS-Technical-Ally-Manager-Collaboration-Dashboard.zip');
  const packagePath = await packageDownload.path();
  const header = readFileSync(packagePath).subarray(0, 4).toString('hex');
  assert.equal(header, '504b0304', 'download is a ZIP');
  const inspectedProcess = spawnSync('python3', ['-c', packageInspectionScript, packagePath], { encoding: 'utf8' });
  assert.equal(inspectedProcess.status, 0, inspectedProcess.stderr);
  const inspected = JSON.parse(inspectedProcess.stdout);
  assert.equal(inspected.bad, null);
  assert.equal(inspected.names.length, 7);
  assert.equal(inspected.profile.authority.nursing_authority_granted, false);
  assert.equal(inspected.profile.authority.managerial_authority_granted, false);
  assert.equal(inspected.profile.authority.institutional_authority_granted, false);
  assert.equal(inspected.profile.governance_posture.edena, 'not-evaluated');
  assert.equal(inspected.profile.governance_posture.autonomy, 'A0-no-action');
  assert.match(inspected.dashboard, /Alex &amp; Team/);
  assert.doesNotMatch(inspected.dashboard, /fetch\(|XMLHttpRequest|WebSocket/);

  const profilePromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download JSON profile' }).click();
  const profileDownload = await profilePromise;
  const profile = JSON.parse(readFileSync(await profileDownload.path(), 'utf8'));
  assert.equal(profile.profile_type, 'nurse-connected-technical-ally');
  assert.equal(profile.result.first_outcome, 'meeting-to-action');
  assert.equal(profile.venture.businessModel, 'professional-service');

  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Start a new ally profile' }).click();
  await page.locator('#display-name').waitFor();
  assert.equal(await page.evaluate(() => sessionStorage.length), 0, 'restart removes tab-local draft');
  assert.deepEqual(externalRequests, [], 'complete flow makes no external requests');
  assert.deepEqual(errors, [], `complete flow errors: ${errors.join(' | ')}`);
  await page.close();

  const restricted = await browser.newPage({ viewport: { width: 390, height: 1000 } });
  await restricted.goto(`http://127.0.0.1:${port}/technical-ally-soul-quiz/`);
  await restricted.locator('#display-name').fill('Patient Jane Doe');
  for (const checkbox of await restricted.locator('input[name^="safety-"]').all()) await checkbox.check();
  await restricted.getByRole('button', { name: 'Save in this tab' }).click();
  assert.match(await restricted.locator('#form-error').textContent(), /identifiers/i);
  assert.equal(await restricted.evaluate(() => sessionStorage.length), 0, 'restricted text is never persisted');
  await restricted.getByRole('button', { name: 'Continue →' }).click();
  assert.match(await restricted.locator('#form-error').textContent(), /generic display name/i);
  assert.equal(await restricted.locator('#display-name').count(), 1, 'restricted input stays at safety gate');
  await restricted.close();

  const malformed = await browser.newPage({ viewport: { width: 390, height: 1000 } });
  await malformed.goto(`http://127.0.0.1:${port}/technical-ally-soul-quiz/`);
  await malformed.evaluate(() => sessionStorage.setItem('naio.technical-ally-soul-quiz.v1', '{bad-json'));
  await malformed.reload();
  assert.equal(await malformed.evaluate(() => sessionStorage.length), 0, 'malformed state is removed');
  await malformed.close();

  console.log('TECHNICAL_ALLY_SOUL_QUIZ_BROWSER_OK viewports=320,390,768,1024,1280 flow=complete package=valid files=7 privacy=session-only');
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}

// Chrome's updater can retain inherited handles on macOS after Playwright and
// the local server have both closed. All assertions and cleanup are complete;
// terminate the standalone test process so the aggregate suite is not held for
// several minutes by a browser-owned background handle.
process.exit(0);
