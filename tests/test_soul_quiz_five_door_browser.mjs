import assert from 'node:assert/strict';
import { createReadStream, readFileSync, statSync } from 'node:fs';
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

async function completeSafety(page, name = 'Jordan') {
  await page.locator('#person-name').fill(name);
  for (const checkbox of await page.locator('input[name^="safety-"]').all()) await checkbox.check();
  await page.getByRole('button', { name: 'Continue →' }).click();
  await page.getByRole('heading', { name: 'Choose your primary workspace' }).waitFor();
  await page.waitForFunction(() => document.activeElement?.tagName === 'H2');
}

async function selectWithKeyboard(page, selector) {
  const input = page.locator(selector);
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await input.focus();
    await page.keyboard.press('Space');
    if (await input.isChecked()) return;
    await page.waitForTimeout(25);
  }
  assert.fail(`${selector} must be keyboard-selectable`);
}

async function advanceWithKeyboard(page, buttonName, nextHeading) {
  for (let attempt = 0; attempt < 3; attempt += 1) {
    await page.getByRole('button', { name: buttonName }).press('Enter');
    try {
      await page.getByRole('heading', { name: nextHeading }).waitFor({ timeout: 1500 });
      return;
    } catch {
      // Chromium can occasionally lose a synthetic key event under full-suite load.
    }
  }
  assert.fail(`Enter on ${buttonName} must reach ${nextHeading}`);
}

await new Promise((resolveListen) => server.listen(0, '127.0.0.1', resolveListen));
const { port } = server.address();
const browser = await chromium.launch({ channel: 'chrome', headless: true });

try {
  for (const width of [320, 390, 768, 1024, 1280]) {
    const page = await browser.newPage({ viewport: { width, height: 1000 } });
    const errors = [];
    page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
    page.on('pageerror', (error) => errors.push(error.message));
    page.on('response', (response) => { if (response.status() >= 400) errors.push(`${response.status()} ${response.url()}`); });
    const response = await page.goto(`http://127.0.0.1:${port}/soul-quiz.html`);
    assert.equal(response?.status(), 200, `SOUL Quiz must return HTTP 200 at ${width}px`);
    await completeSafety(page);

    const geometry = await page.evaluate(() => {
      const cards = [...document.querySelectorAll('.quick-lane-card')].map((element) => element.getBoundingClientRect());
      const controls = [...document.querySelectorAll('.quiz-actions button')].map((element) => element.getBoundingClientRect());
      return {
        cardCount: cards.length,
        pageOverflow: document.documentElement.scrollWidth > window.innerWidth,
        cardWidths: cards.map((rect) => rect.width),
        cardHeights: cards.map((rect) => rect.height),
        controlWidths: controls.map((rect) => rect.width),
        controlHeights: controls.map((rect) => rect.height),
        targetsWithinViewport: [...cards, ...controls].every((rect) => rect.left >= -0.5 && rect.right <= window.innerWidth + 0.5)
      };
    });
    assert.equal(geometry.cardCount, 5, `exactly five role doors at ${width}px`);
    assert.equal(geometry.pageOverflow, false, `no page overflow at ${width}px`);
    assert.equal(geometry.targetsWithinViewport, true, `targets remain in viewport at ${width}px`);
    assert.ok(geometry.cardWidths.every((value) => value >= 44), `lane cards >=44px wide at ${width}px`);
    assert.ok(geometry.cardHeights.every((value) => value >= 44), `lane cards >=44px high at ${width}px`);
    assert.ok(geometry.controlWidths.every((value) => value >= 44), `actions >=44px wide at ${width}px`);
    assert.ok(geometry.controlHeights.every((value) => value >= 44), `actions >=44px high at ${width}px`);
    assert.equal(errors.length, 0, `console/network errors at ${width}px: ${errors.join(' | ')}`);
    await page.close();
  }

  const keyboardPage = await browser.newPage({ viewport: { width: 390, height: 1000 } });
  await keyboardPage.goto(`http://127.0.0.1:${port}/soul-quiz.html`);
  await keyboardPage.locator('#person-name').focus();
  await keyboardPage.keyboard.type('Keyboard User');
  for (const checkbox of await keyboardPage.locator('input[name^="safety-"]').all()) {
    await selectWithKeyboard(keyboardPage, `input[name="${await checkbox.getAttribute('name')}"]`);
  }
  await advanceWithKeyboard(keyboardPage, 'Continue →', 'Choose your primary workspace');
  await selectWithKeyboard(keyboardPage, 'input[name="primary-lane"][value="staff-nurse"]');
  await advanceWithKeyboard(keyboardPage, 'Continue →', 'Choose your current mission');
  for (const selector of [
    'input[name="role-context"][value="staff-practice"]',
    'input[name="current-mission"][value="improve-daily-work"]',
    'input[name="project-state"][value="no-project"]'
  ]) {
    await selectWithKeyboard(keyboardPage, selector);
  }
  await advanceWithKeyboard(keyboardPage, 'Continue →', 'Add optional hats and choose a first artifact');
  await selectWithKeyboard(keyboardPage, 'input[name="first-artifact"][value="structured-question"]');
  await advanceWithKeyboard(keyboardPage, 'Build my focused workspace →', 'Your focused Mission Control is ready');
  await keyboardPage.waitForFunction(() => document.activeElement?.tagName === 'H2');
  await keyboardPage.close();

  const draftPage = await browser.newPage({ viewport: { width: 390, height: 1000 } });
  await draftPage.goto(`http://127.0.0.1:${port}/soul-quiz.html`);
  await completeSafety(draftPage, 'Saved Draft');
  await draftPage.locator('input[name="primary-lane"][value="staff-nurse"]').check();
  await draftPage.getByRole('button', { name: 'Continue →' }).click();
  await draftPage.getByRole('heading', { name: 'Choose your current mission' }).waitFor();
  await draftPage.reload();
  assert.equal(await draftPage.locator('#person-name').inputValue(), 'Saved Draft', 'partial quick-start reload preserves the saved name');
  assert.equal(await draftPage.locator('input[name^="safety-"]:checked').count(), 4, 'partial quick-start reload preserves safety confirmations');
  await draftPage.getByRole('button', { name: 'Continue →' }).click();
  await draftPage.getByRole('heading', { name: 'Choose your primary workspace' }).waitFor();
  assert.equal(await draftPage.locator('input[name="primary-lane"][value="staff-nurse"]').isChecked(), true, 'partial quick-start reload preserves the primary workspace');
  await draftPage.close();

  for (const projectCase of [
    { lane: 'staff-nurse', context: 'staff-practice', mission: 'improve-daily-work', project: 'idea', artifact: 'structured-question', label: /I have an idea/i },
    { lane: 'leader', context: 'nurse-manager', mission: 'prepare-decision', project: 'no-project', artifact: 'decision-brief', label: /No current initiative/i }
  ]) {
    const labelPage = await browser.newPage({ viewport: { width: 390, height: 1000 } });
    await labelPage.goto(`http://127.0.0.1:${port}/soul-quiz.html`);
    await completeSafety(labelPage, `Label ${projectCase.lane}`);
    await labelPage.locator(`input[name="primary-lane"][value="${projectCase.lane}"]`).check();
    await labelPage.getByRole('button', { name: 'Continue →' }).click();
    await labelPage.locator(`input[name="role-context"][value="${projectCase.context}"]`).check();
    await labelPage.locator(`input[name="current-mission"][value="${projectCase.mission}"]`).check();
    await labelPage.locator(`input[name="project-state"][value="${projectCase.project}"]`).check();
    await labelPage.getByRole('button', { name: 'Continue →' }).click();
    await labelPage.locator(`input[name="first-artifact"][value="${projectCase.artifact}"]`).check();
    await labelPage.getByRole('button', { name: 'Build my focused workspace →' }).click();
    assert.match(await labelPage.locator('.quick-summary').textContent(), projectCase.label, `${projectCase.lane} uses its own project label`);
    await labelPage.close();
  }

  for (const roleCase of [
    {
      lane: 'prelicensure-student', context: 'student-only', mission: 'understand-concept', artifact: 'learning-plan',
      boundary: /Faculty, preceptors, and institutional requirements remain controlling/i
    },
    {
      lane: 'leader', context: 'nurse-manager', mission: 'prepare-decision', artifact: 'decision-brief',
      boundary: /No hidden workforce scoring, autonomous staffing, discipline, or consequential institutional action/i
    },
    {
      lane: 'educator', context: 'clinical-preceptor', mission: 'create-learning-plan', artifact: 'learning-plan',
      boundary: /AI cannot independently determine competence, pass\/fail, progression, or official evaluation/i
    }
  ]) {
    const rolePage = await browser.newPage({ viewport: { width: 390, height: 1000 } });
    await rolePage.goto(`http://127.0.0.1:${port}/soul-quiz.html`);
    await completeSafety(rolePage, `Test ${roleCase.lane}`);
    await rolePage.locator(`input[name="primary-lane"][value="${roleCase.lane}"]`).check();
    await rolePage.getByRole('button', { name: 'Continue →' }).click();
    await rolePage.locator(`input[name="role-context"][value="${roleCase.context}"]`).check();
    await rolePage.locator(`input[name="current-mission"][value="${roleCase.mission}"]`).check();
    const projectRadio = rolePage.locator('input[type="radio"][name="project-state"][value="no-project"]');
    if (await projectRadio.count()) await projectRadio.check();
    await rolePage.getByRole('button', { name: 'Continue →' }).click();
    await rolePage.locator(`input[name="first-artifact"][value="${roleCase.artifact}"]`).check();
    await rolePage.getByRole('button', { name: 'Build my focused workspace →' }).click();
    const resultText = await rolePage.locator('.quick-results').textContent();
    assert.match(resultText, roleCase.boundary, `${roleCase.lane} must preserve its role boundary`);
    await rolePage.close();
  }

  const staffPage = await browser.newPage({ viewport: { width: 390, height: 1000 } });
  const staffErrors = [];
  staffPage.on('console', (message) => { if (message.type() === 'error') staffErrors.push(message.text()); });
  staffPage.on('pageerror', (error) => staffErrors.push(error.message));
  await staffPage.goto(`http://127.0.0.1:${port}/soul-quiz.html`);
  await completeSafety(staffPage, 'Alex');
  await staffPage.locator('input[name="primary-lane"][value="staff-nurse"]').check();
  await staffPage.getByRole('button', { name: 'Continue →' }).click();
  await staffPage.getByRole('heading', { name: 'Choose your current mission' }).waitFor();
  assert.equal(await staffPage.locator('.role-domain').count(), 0, 'full 14-domain taxonomy stays hidden in quick start');
  await staffPage.locator('input[name="role-context"][value="staff-practice"]').check();
  await staffPage.locator('input[name="current-mission"][value="improve-daily-work"]').check();
  await staffPage.locator('input[name="project-state"][value="no-project"]').check();
  await staffPage.getByRole('button', { name: 'Continue →' }).click();
  await staffPage.getByRole('heading', { name: 'Add optional hats and choose a first artifact' }).waitFor();
  await staffPage.locator('input[name="secondary-lane"][value="educator"]').check();
  await staffPage.locator('input[name="secondary-lane"][value="leader"]').check();
  await staffPage.locator('input[name="secondary-lane"][value="licensed-clinician"]').click();
  assert.equal(await staffPage.locator('input[name="secondary-lane"]:checked').count(), 2, 'quick start caps secondary hats at two');
  assert.match(await staffPage.locator('#quiz-status').textContent(), /two secondary hats/i);
  await staffPage.locator('input[name="first-artifact"][value="structured-question"]').check();
  await staffPage.getByRole('button', { name: 'Build my focused workspace →' }).click();
  await staffPage.getByRole('heading', { name: 'Your focused Mission Control is ready' }).waitFor();
  assert.match(await staffPage.locator('.quick-results').textContent(), /No current project/i);
  assert.doesNotMatch(await staffPage.locator('.quick-results').textContent(), /Quality improvement overlay active/i);
  assert.match(await staffPage.locator('.quick-results').textContent(), /No patient-specific advice, charting, or clinical delegation/i);

  const downloadPromise = staffPage.waitForEvent('download');
  await staffPage.getByRole('button', { name: 'Export OS Config' }).click();
  const download = await downloadPromise;
  const path = await download.path();
  const config = JSON.parse(readFileSync(path, 'utf8'));
  assert.equal(config.schema_version, '2.0.0');
  assert.equal(config.workspace_routing.primary_lane, 'staff-nurse');
  assert.equal(config.workspace_routing.project_state, 'no-project');
  assert.deepEqual(config.workspace_routing.active_overlays, []);
  assert.equal(config.authority.institutional_authority_granted, false);

  await staffPage.getByRole('button', { name: 'Deepen my SOUL' }).click();
  await staffPage.getByRole('heading', { name: 'Map your complete role constellation' }).waitFor();
  assert.ok(await staffPage.locator('.role-domain').count() >= 14, 'deep mode preserves the complete constellation');
  assert.equal(await staffPage.locator('input[name="role"]:checked').count(), 3, 'deep mode carries projected primary and secondary roles forward');
  assert.equal(staffErrors.length, 0, `staff quick-start errors: ${staffErrors.join(' | ')}`);
  await staffPage.close();

  const clinicianPage = await browser.newPage({ viewport: { width: 390, height: 1000 } });
  await clinicianPage.goto(`http://127.0.0.1:${port}/soul-quiz.html`);
  await completeSafety(clinicianPage, 'Morgan');
  await clinicianPage.locator('input[name="primary-lane"][value="licensed-clinician"]').check();
  await clinicianPage.getByRole('button', { name: 'Continue →' }).click();
  await clinicianPage.locator('input[name="role-context"][value="nurse-practitioner"]').check();
  await clinicianPage.locator('input[name="current-mission"][value="conduct-research"]').check();
  await clinicianPage.locator('input[name="project-state"][value="active-approved-research"]').check();
  await clinicianPage.getByRole('button', { name: 'Continue →' }).click();
  await clinicianPage.locator('input[name="first-artifact"][value="research-question"]').check();
  await clinicianPage.getByRole('button', { name: 'Build my focused workspace →' }).click();
  const clinicianText = await clinicianPage.locator('.quick-results').textContent();
  assert.match(clinicianText, /Research and evidence overlay active/i);
  assert.match(clinicianText, /Research status does not create IRB, privacy, security, data-use, or institutional approval/i);
  assert.match(clinicianText, /No independent diagnosis, prescribing, orders, patient communication/i);
  await clinicianPage.close();

  console.log('SOUL_QUIZ_FIVE_DOOR_BROWSER_OK viewports=320,390,768,1024,1280 keyboard=complete role-paths=5 doors=5 hats<=2 quick-export=valid deep-constellation=preserved');
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}
