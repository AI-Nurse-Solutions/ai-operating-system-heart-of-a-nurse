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
const baseUrl = `http://127.0.0.1:${port}/switchboard/`;
const browser = await chromium.launch({ channel: 'chrome', headless: true });
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
const errors = [];
page.on('console', (message) => { if (message.type() === 'error') errors.push(message.text()); });
page.on('pageerror', (error) => errors.push(error.message));

try {
  const response = await page.goto(baseUrl);
  assert.equal(response?.status(), 200, 'Switchboard route must return HTTP 200');
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await page.evaluate(() => localStorage.setItem('naio.switchboard.preview.v2', '{malformed'));
  await page.reload();
  assert.equal(await page.evaluate(() => localStorage.getItem('naio.switchboard.preview.v2')), null, 'malformed stored JSON must be removed');

  const legacyState = { schemaVersion: 1, stage: 3, safety: { noPhi: true, noClinical: true, noSecrets: true, guideOnly: true }, door: 'browser', environment: { device: 'mac', ownership: 'personal', admin: 'yes', browser: 'chrome', hermesStatus: 'not-installed' }, identityRole: 'staff', postSetupLane: 'staff_nurse', readiness: { time: false, folder: false, recovery: false, boundaries: false }, route: 'browser', flowIndex: 0, completedFlowIds: [], issueCode: '', updatedAt: '2026-07-17T00:00:00.000Z' };
  await page.evaluate((legacy) => {
    localStorage.setItem('naio.setup-helper.phase1.v1', JSON.stringify(legacy));
    localStorage.removeItem('naio.switchboard.legacy-dismissed.v1');
  }, legacyState);
  await page.reload();
  await page.locator('#legacy-banner:not([hidden])').waitFor();
  await page.getByRole('button', { name: 'Not now' }).click();
  assert.equal(await page.evaluate(() => localStorage.getItem('naio.switchboard.legacy-dismissed.v1')), '1');
  await page.reload();
  assert.equal(await page.locator('#legacy-banner').isHidden(), true, 'dismissed migration prompt must stay hidden after reload');

  await page.evaluate(() => localStorage.removeItem('naio.switchboard.legacy-dismissed.v1'));
  await page.reload();
  await page.getByRole('button', { name: 'Create starter dashboard' }).click();
  assert.equal(await page.locator('#dashboard-count').textContent(), '1');
  assert.equal(await page.evaluate(() => localStorage.getItem('naio.switchboard.legacy-dismissed.v1')), '1');
  await page.reload();
  assert.equal(await page.locator('#legacy-banner').isHidden(), true, 'completed migration prompt must stay hidden after reload');
  assert.equal(await page.locator('#dashboard-count').textContent(), '1');
  await page.evaluate(() => {
    localStorage.removeItem('naio.switchboard.preview.v2');
    localStorage.removeItem('naio.setup-helper.phase1.v1');
    localStorage.removeItem('naio.switchboard.legacy-dismissed.v1');
  });
  await page.reload();

  assert.equal(await page.locator('.rail-heading strong').textContent(), 'Synthetic examples');
  assert.equal(await page.locator('#dashboard-count').textContent(), '3');
  assert.equal(await page.locator('[data-demo-dashboard-id]').count(), 3, 'first run must expose three reviewable examples');
  assert.equal(await page.locator('[data-demo-dashboard-id][aria-pressed="true"]').count(), 1);
  assert.equal(await page.locator('#export-state').isDisabled(), true, 'synthetic examples must never be exported as personal state');
  assert.equal(await page.locator('#reset-state').textContent(), 'Clear saved local data');
  await assert.doesNotReject(() => page.getByText('Synthetic demo · not saved').waitFor());
  await assert.doesNotReject(() => page.getByText('What works in this preview').waitFor());
  assert.ok(await page.locator('.assessment-card').count() >= 4, 'role and capability boundaries must be immediately assessable');
  assert.equal(await page.locator('.assessment-card[open]').count(), 1, 'primary role scope must be expanded by default');
  assert.equal(await page.evaluate(() => localStorage.getItem('naio.switchboard.preview.v2')), null, 'reviewing examples must not create saved state');
  const demoButtons = page.locator('[data-demo-dashboard-id]');
  await demoButtons.nth(1).click();
  assert.match(await page.locator('.dashboard-head h3').textContent(), /Nurse Educator/);
  await demoButtons.nth(2).click();
  assert.match(await page.locator('.dashboard-head h3').textContent(), /Nurse Community Organizer-Developer/);
  assert.equal(await page.evaluate(() => localStorage.getItem('naio.switchboard.preview.v2')), null, 'switching synthetic examples must remain ephemeral');
  await page.setViewportSize({ width: 320, height: 720 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, '320px synthetic review mode must not overflow');
  const demoCtaBox = await page.getByRole('button', { name: 'Create my own →' }).boundingBox();
  const assessmentSummaryBox = await page.locator('.assessment-card summary').first().boundingBox();
  assert.ok(demoCtaBox.height >= 44, `synthetic demo CTA target height ${demoCtaBox.height}`);
  assert.ok(assessmentSummaryBox.height >= 44, `assessment disclosure target height ${assessmentSummaryBox.height}`);
  await page.getByRole('button', { name: 'Create my own →' }).click();
  await page.locator('#dashboard-dialog[open]').waitFor();
  await page.getByRole('button', { name: 'Cancel' }).click();
  assert.equal(await page.locator('[data-demo-dashboard-id]').count(), 3);
  await page.setViewportSize({ width: 1280, height: 720 });

  await page.evaluate(() => {
    window.scrollTo(0, 600);
    document.querySelector('footer').inert = true;
    document.querySelector('#dashboard-dialog').showModal = undefined;
  });
  await page.locator('#create-dashboard').focus();
  await page.click('#create-dashboard');
  assert.equal(await page.locator('#dashboard-dialog').getAttribute('data-fallback'), 'true');
  const fallbackMetrics = await page.locator('#dashboard-dialog').evaluate((dialog) => {
    const style = getComputedStyle(dialog);
    const rect = dialog.getBoundingClientRect();
    const siblings = [...document.body.children].filter((element) => element !== dialog);
    return { position: style.position, zIndex: style.zIndex, role: dialog.getAttribute('role'), ariaModal: dialog.getAttribute('aria-modal'), boxShadow: style.boxShadow, allSiblingsInert: siblings.every((element) => element.inert), top: rect.top, bottom: rect.bottom, viewportHeight: innerHeight };
  });
  assert.equal(fallbackMetrics.position, 'fixed');
  assert.equal(fallbackMetrics.role, 'dialog');
  assert.equal(fallbackMetrics.ariaModal, 'true');
  assert.ok(Number(fallbackMetrics.zIndex) >= 1000);
  assert.notEqual(fallbackMetrics.boxShadow, 'none', 'fallback must render a visual modal backdrop');
  assert.equal(fallbackMetrics.allSiblingsInert, true, 'every fallback background sibling must be inert');
  assert.ok(fallbackMetrics.top >= 0 && fallbackMetrics.bottom <= fallbackMetrics.viewportHeight, `fallback must be visible in viewport: ${JSON.stringify(fallbackMetrics)}`);
  await page.evaluate(() => document.querySelector('#export-state').focus());
  assert.equal(await page.evaluate(() => document.querySelector('#dashboard-dialog').contains(document.activeElement)), true, 'fallback background must be inert');
  await page.evaluate(() => {
    const focusable = [...document.querySelectorAll('#dashboard-dialog button:not([disabled]), #dashboard-dialog [href], #dashboard-dialog input:not([disabled]), #dashboard-dialog select:not([disabled]), #dashboard-dialog textarea:not([disabled]), #dashboard-dialog [tabindex]:not([tabindex="-1"])')];
    focusable.at(-1).focus();
  });
  await page.keyboard.press('Tab');
  const fallbackFocus = await page.evaluate(() => {
    const first = document.querySelector('#dashboard-dialog button:not([disabled]), #dashboard-dialog [href], #dashboard-dialog input:not([disabled]), #dashboard-dialog select:not([disabled]), #dashboard-dialog textarea:not([disabled]), #dashboard-dialog [tabindex]:not([tabindex="-1"])');
    return { wrapped: document.activeElement === first, contained: document.querySelector('#dashboard-dialog').contains(document.activeElement), tag: document.activeElement?.tagName, className: document.activeElement?.className };
  });
  assert.equal(fallbackFocus.wrapped, true, `fallback Tab must wrap to its first focusable control: ${JSON.stringify(fallbackFocus)}`);
  assert.equal(fallbackFocus.contained, true);
  await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'create-dashboard', 'fallback close must restore invoking focus');
  assert.equal(await page.evaluate(() => document.querySelector('main').inert), false, 'fallback close must restore background interactivity');
  assert.equal(await page.evaluate(() => document.querySelector('footer').inert), true, 'fallback close must preserve a sibling that was already inert');
  assert.equal(await page.locator('#dashboard-dialog').getAttribute('role'), null, 'fallback-only dialog role must be restored on close');
  assert.equal(await page.locator('#dashboard-dialog').getAttribute('aria-modal'), null, 'fallback-only modal semantics must be restored on close');
  await page.evaluate(() => { document.querySelector('footer').inert = false; });
  await page.reload();
  await page.evaluate(() => window.scrollTo(0, 0));

  await page.locator('#create-dashboard').focus();
  await page.click('#create-dashboard');
  await page.locator('#dashboard-context').waitFor();
  await page.waitForFunction(() => document.activeElement?.id === 'dashboard-context');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'dashboard-context', 'native dialog must focus its first form field');
  await page.evaluate(() => document.querySelector('#export-state').focus());
  assert.equal(await page.evaluate(() => document.querySelector('#dashboard-dialog').contains(document.activeElement)), true, 'native modal must contain focus');
  await page.keyboard.press('Escape');
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'create-dashboard', 'native Escape must restore invoking focus');

  await page.getByRole('button', { name: '+ Create dashboard' }).click();
  await page.getByRole('button', { name: 'Cancel' }).click();
  assert.equal(await page.locator('#dashboard-count').textContent(), '3', 'Cancel must return to the three synthetic examples');
  assert.equal(await page.evaluate(() => localStorage.getItem('naio.switchboard.preview.v2')), null);
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'create-dashboard', 'native Cancel must restore invoking focus');

  await page.getByRole('button', { name: '+ Create dashboard' }).click();
  await page.getByRole('button', { name: 'Close dashboard form' }).click();
  assert.equal(await page.locator('#dashboard-count').textContent(), '3', 'Close must not replace the synthetic review mode');

  await page.setViewportSize({ width: 320, height: 720 });
  await page.getByRole('button', { name: '+ Create dashboard' }).click();
  let closeBox = await page.getByRole('button', { name: 'Close dashboard form' }).boundingBox();
  assert.ok(closeBox.width >= 44 && closeBox.height >= 44, `dashboard close target ${closeBox.width}x${closeBox.height}`);
  await page.getByRole('button', { name: 'Close dashboard form' }).click();
  await page.evaluate(() => document.querySelector('#role-dialog').showModal());
  closeBox = await page.locator('#role-dialog .dialog-close').boundingBox();
  assert.ok(closeBox.width >= 44 && closeBox.height >= 44, `role close target ${closeBox.width}x${closeBox.height}`);
  await page.evaluate(() => document.querySelector('#role-dialog').close());
  await page.setViewportSize({ width: 390, height: 844 });

  await page.getByRole('button', { name: '+ Create dashboard' }).click();
  await page.locator('#dashboard-context').selectOption('community-a');
  const communityRoles = await page.locator('#dashboard-role option').allTextContents();
  assert(communityRoles.some((name) => name.includes('Nurse Community Organizer-Developer')), 'community organizer role must be available in community context');
  assert(!communityRoles.some((name) => name.includes('Medico-Legal')), 'medico-legal role must be excluded from community context');
  await page.getByRole('button', { name: 'Cancel' }).click();

  await page.getByRole('button', { name: '+ Create dashboard' }).click();
  await page.getByRole('button', { name: 'Create separate dashboard' }).click();
  assert.equal(await page.locator('#dashboard-count').textContent(), '1');
  assert.equal(await page.locator('[data-demo-dashboard-id]').count(), 0, 'saved dashboard must replace synthetic review mode without mixing states');
  assert.equal(await page.locator('#export-state').isEnabled(), true);
  await page.getByRole('button', { name: '+ Create dashboard' }).click();
  await page.locator('#dashboard-context').selectOption('facility-a');
  await page.locator('#dashboard-department').selectOption('critical-care');
  await page.locator('#dashboard-role').selectOption('staff-nurse');
  await page.locator('#dashboard-assignment').selectOption('organization-assigned-unverified');
  await page.locator('#dashboard-shift').selectOption('8-hours');
  await page.getByRole('button', { name: 'Create separate dashboard' }).click();
  assert.equal(await page.locator('#dashboard-count').textContent(), '2');
  await assert.doesNotReject(() => page.getByText('EDENA: Not evaluated').waitFor());
  await assert.doesNotReject(() => page.getByText('A0 · no action').waitFor());

  await page.locator('[data-dashboard-id]').first().click();
  assert.equal(await page.evaluate(() => document.activeElement?.id), 'dashboard-view', 'focus must move to selected dashboard content');
  const selectedDashboardId = await page.locator('[data-dashboard-id]').first().getAttribute('data-dashboard-id');
  const selectedButton = page.locator(`[data-dashboard-id="${selectedDashboardId}"]`);
  assert.equal(await selectedButton.getAttribute('aria-pressed'), 'true');
  assert.equal(await selectedButton.evaluate((element) => getComputedStyle(element).backgroundColor), 'rgb(16, 33, 63)', 'selected dashboard must have persistent navy styling');
  await page.reload();
  const reloadedSelectedButton = page.locator(`[data-dashboard-id="${selectedDashboardId}"]`);
  assert.equal(await reloadedSelectedButton.getAttribute('aria-pressed'), 'true', 'selected dashboard state must persist after reload');
  assert.equal(await reloadedSelectedButton.evaluate((element) => getComputedStyle(element).backgroundColor), 'rgb(16, 33, 63)');

  const emptyState = JSON.stringify({ schemaVersion: 2, activeDashboardId: null, dashboards: [], localRoles: [], updatedAt: '2026-07-17T00:00:00.000Z' });
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.locator('#import-state').setInputFiles({ name: 'switchboard.json', mimeType: 'application/json', buffer: Buffer.from(emptyState) });
  await page.getByText('Import cancelled. Current local configuration was kept.').waitFor();
  assert.equal(await page.locator('#dashboard-count').textContent(), '2');

  const importedSessionState = JSON.stringify({
    schemaVersion: 2,
    activeDashboardId: 'dashboard-imported-session',
    dashboards: [{
      id: 'dashboard-imported-session', contextKey: 'personal', departmentKey: 'personal-learning', primaryRoleId: 'staff-nurse', supportingRoleIds: [], capabilityIds: ['discover', 'future'], assignmentStatus: 'self-declared', shiftWindow: 'session', assignmentStartedAt: '2026-07-16T00:00:00.000Z', assignmentExpiresAt: null, createdAt: '2026-07-16T00:00:00.000Z', updatedAt: '2026-07-16T00:00:00.000Z'
    }],
    localRoles: [],
    updatedAt: '2026-07-16T00:00:00.000Z'
  });
  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#import-state').setInputFiles({ name: 'session.json', mimeType: 'application/json', buffer: Buffer.from(importedSessionState) });
  await page.waitForFunction(() => document.querySelector('#status-message')?.textContent?.includes('Switchboard JSON imported after strict validation.'));
  const sessionImportStatus = await page.locator('#status-message').textContent();
  assert.match(sessionImportStatus || '', /Switchboard JSON imported after strict validation/, `session import status: ${sessionImportStatus}`);
  assert.equal(await page.locator('#dashboard-count').textContent(), '1');
  assert.match(await page.locator('#dashboard-view').textContent(), /inactive or expired/i);
  assert.match(await page.locator('#dashboard-view').textContent(), /Not a current assignment/);

  page.once('dialog', (dialog) => dialog.accept());
  await page.locator('#import-state').setInputFiles({ name: 'switchboard.json', mimeType: 'application/json', buffer: Buffer.from(emptyState) });
  await page.waitForFunction(() => document.querySelector('#dashboard-count')?.textContent === '3');
  assert.equal(await page.locator('[data-demo-dashboard-id]').count(), 3, 'an imported empty state must return to synthetic review mode');
  assert.equal(await page.locator('#export-state').isDisabled(), true);

  await page.getByRole('button', { name: '+ Add local role or assignment' }).click();
  await page.locator('#local-role-name').fill('Jane Doe MRN 123');
  await page.locator('#local-role-no-identifiers').check();
  await page.getByRole('button', { name: 'Add local draft' }).click();
  await page.locator('#role-form-error:not([hidden])').waitFor();
  assert((await page.locator('#role-form-error').textContent())?.includes('not exhaustive PHI detection'));
  await page.getByRole('button', { name: 'Cancel' }).click();

  await page.getByRole('button', { name: '+ Add local role or assignment' }).click();
  await page.locator('#local-role-name').fill('Nurse Innovation Fellow');
  await page.locator('#local-role-no-identifiers').check();
  await page.getByRole('button', { name: 'Add local draft' }).click();
  assert.equal(await page.locator('#dashboard-count').textContent(), '0');
  assert.equal(await page.locator('[data-demo-dashboard-id]').count(), 0, 'persisted local-role-only state must exit synthetic mode');
  await assert.doesNotReject(() => page.getByRole('heading', { name: 'Your local draft is saved' }).waitFor());
  assert.equal(await page.locator('#export-state').isEnabled(), true, 'local-role-only state must remain exportable');
  assert.equal(await page.locator('#reset-state').textContent(), 'Clear local Switchboard');

  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth), true, '390px layout must not overflow horizontally');
  await page.evaluate(() => { Storage.prototype.removeItem = () => { throw new Error('blocked'); }; });
  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Clear local Switchboard' }).click();
  await page.getByText('Local storage could not be cleared.').waitFor();
  assert(!(await page.locator('#status-message').textContent())?.includes('Existing downloads'), 'reset must not announce success when removal fails');
  assert.deepEqual(errors, [], `browser console errors: ${errors.join(' | ')}`);

  const postSetupPage = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const postSetupErrors = [];
  const postSetupFailedResponses = [];
  const postSetupFailedRequests = [];
  const isOptionalFontUrl = (url) => url.startsWith('https://fonts.googleapis.com/') || url.startsWith('https://fonts.gstatic.com/');
  postSetupPage.on('console', (message) => {
    const location = message.location().url || '';
    if (message.type() === 'error' && !isOptionalFontUrl(location)) {
      postSetupErrors.push(`${message.text()} @ ${location || 'unknown'}`);
    }
  });
  postSetupPage.on('pageerror', (error) => postSetupErrors.push(error.message));
  postSetupPage.on('response', (response) => {
    if (response.status() >= 400 && !isOptionalFontUrl(response.url())) {
      postSetupFailedResponses.push(`${response.status()} ${response.url()}`);
    }
  });
  postSetupPage.on('requestfailed', (request) => {
    if (!isOptionalFontUrl(request.url())) {
      postSetupFailedRequests.push(`${request.url()} ${request.failure()?.errorText || 'failed'}`);
    }
  });
  for (const viewport of [{ width: 1280, height: 900 }, { width: 390, height: 844 }]) {
    await postSetupPage.setViewportSize(viewport);
    const postSetupResponse = await postSetupPage.goto(`http://127.0.0.1:${port}/post-setup/`);
    assert.equal(postSetupResponse?.status(), 200, `post-setup route must return HTTP 200 at ${viewport.width}px`);
    const leadCard = postSetupPage.locator('article').filter({ hasText: 'Nurse Leader Complete AI OS with LEAD SuperPowers' });
    assert.equal(await leadCard.count(), 1, 'exactly one Nurse Leader LEAD card must render');
    const leadLink = leadCard.locator('a[download]');
    assert.equal(await leadLink.getAttribute('href'), 'downloads/LEAD-Nurse-Leader-Manager-Mission-Control-Hermes-Build-Kit-v1.0.0.zip');
    assert.equal((await leadLink.textContent())?.trim(), 'Download LEAD Build Kit →');
    const journey = postSetupPage.getByRole('heading', { name: 'What happens after a self-install build-kit download?' });
    assert.equal(await journey.count(), 1, 'post-download journey must render once');
    const responsive = await postSetupPage.evaluate(() => {
      const heading = [...document.querySelectorAll('h3')].find((node) => node.textContent?.includes('Nurse Leader Complete'));
      const card = heading?.closest('article');
      const link = card?.querySelector('a[download]');
      const journeyHeading = [...document.querySelectorAll('h3')].find((node) => node.textContent?.includes('What happens after'));
      const viewportWidth = document.documentElement.clientWidth;
      const bounds = card?.getBoundingClientRect();
      return {
        pageOverflow: document.documentElement.scrollWidth > viewportWidth,
        cardOverflow: Boolean(card && card.scrollWidth > card.clientWidth),
        linkOverflow: Boolean(link && link.scrollWidth > link.clientWidth),
        cardWithinViewport: Boolean(bounds && bounds.left >= 0 && bounds.right <= viewportWidth),
        digestPresent: Boolean(card?.innerText.includes('78293c6eaef4fa277f4afecf14eeb87b90f3385ba71be3189faaca2466c90974')),
        journeySteps: journeyHeading?.parentElement?.querySelectorAll('li').length || 0,
      };
    });
    assert.equal(responsive.pageOverflow, false, `post-setup page must not overflow at ${viewport.width}px`);
    assert.equal(responsive.cardOverflow, false, `LEAD card must not overflow at ${viewport.width}px`);
    assert.equal(responsive.linkOverflow, false, `LEAD CTA must not overflow at ${viewport.width}px`);
    assert.equal(responsive.cardWithinViewport, true, `LEAD card must stay within ${viewport.width}px viewport`);
    assert.equal(responsive.digestPresent, true, 'visible LEAD digest must remain present');
    assert.equal(responsive.journeySteps, 6, 'post-download journey must retain six steps');
  }
  assert.deepEqual(postSetupErrors, [], `post-setup browser console errors: ${postSetupErrors.join(' | ')}; failed responses: ${postSetupFailedResponses.join(' | ')}; failed requests: ${postSetupFailedRequests.join(' | ')}`);
  assert.deepEqual(postSetupFailedResponses, [], `post-setup failed responses: ${postSetupFailedResponses.join(' | ')}`);
  assert.deepEqual(postSetupFailedRequests, [], `post-setup failed requests: ${postSetupFailedRequests.join(' | ')}`);
  await postSetupPage.close();
  console.log('POST_SETUP_LEAD_BROWSER_SMOKE_OK');
  console.log('SWITCHBOARD_BROWSER_SMOKE_OK');
} finally {
  await browser.close();
  await new Promise((resolveClose) => server.close(resolveClose));
}
