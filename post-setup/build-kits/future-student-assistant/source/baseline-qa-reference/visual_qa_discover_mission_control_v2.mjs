import { createRequire } from "node:module";
import { mkdir, rm, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { spawn } from "node:child_process";

const require = createRequire(import.meta.url);
const playwrightRoot = process.env.CODEX_PRIMARY_RUNTIME_NODE_MODULES;
const qaRoot = process.env.DISCOVER_QA_NODE_MODULES || "/tmp/discover-dashboard-qa/node_modules";
const { chromium: playwrightChromium } = require(`${playwrightRoot}/playwright`);
const sparticuzModule = await import(pathToFileURL(`${qaRoot}/@sparticuz/chromium/build/index.js`).href);

const out = resolve("qa/discover-mission-control-v2-visual-qa");
await rm(out, { recursive: true, force: true });
await mkdir(out, { recursive: true });

const server = spawn(process.env.CODEX_PRIMARY_RUNTIME_NODE, [resolve("deliverables/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0/server.mjs")], {
  cwd: resolve("."),
  stdio: ["ignore", "pipe", "pipe"]
});
let serverOutput = "";
server.stdout.on("data", (chunk) => { serverOutput += chunk.toString(); });
server.stderr.on("data", (chunk) => { serverOutput += chunk.toString(); });

const report = { generated_at: new Date().toISOString(), screenshots: [], checks: [], axe: [], console_errors: [] };
let browser;
try {
  await waitForHealth();
  sparticuzModule.default.setGraphicsMode = false;
  await rm("/tmp/chromium", { force: true });
  const executablePath = await sparticuzModule.inflate(`${qaRoot}/@sparticuz/chromium/bin/chromium.br`);
  browser = await playwrightChromium.launch({
    executablePath,
    args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--font-render-hinting=none"],
    headless: true
  });
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 }, colorScheme: "light", reducedMotion: "reduce", bypassCSP: true });
  const page = await context.newPage();
  page.on("console", (message) => { if (message.type() === "error") report.console_errors.push(message.text()); });
  page.on("pageerror", (error) => report.console_errors.push(error.stack || error.message));

  await page.goto("http://127.0.0.1:43127/", { waitUntil: "networkidle" });
  await page.waitForTimeout(250);
  record("first-run processing dialog opens", await page.locator("#onboardingDialog").getAttribute("open") !== null, null);
  await shot(page, "01-first-run-processing.png");
  await page.click("#closeOnboarding");
  record("first-run close cannot bypass the safety step", await page.locator('#onboardingDialog [data-onboarding-step="1"]').isVisible(), null);
  await shot(page, "02-first-run-safety.png");
  await completeOnboarding(page, { alreadyOnSafetyStep: true });
  record("walkthrough completion closes the dialog", await page.locator("#onboardingDialog").getAttribute("open") === null, null);
  await layout(page, "desktop-dashboard");
  await shot(page, "03-desktop-dashboard.png");

  await page.click('[data-view="soul"]');
  await page.click("#loadSampleDiscover");
  record("Discover Packet preview is explicitly synthetic", (await page.locator("#discoverPacketPreviewHeading").textContent() || "").includes("Synthetic"), await page.locator("#discoverPacketPreviewHeading").textContent());
  await layout(page, "desktop-discover-adapter");
  await shot(page, "04-desktop-discover-adapter.png");
  await page.click("#applyDiscoverPacket");
  record("Discover Packet applies without enabling authority", (await page.locator("#discoverPacketStatus").textContent() || "").includes("authority were unchanged"), await page.locator("#discoverPacketStatus").textContent());

  await page.click("#loadSampleSoul");
  await page.locator("#soulAdapterHeading").evaluate((element) => element.scrollIntoView({ block: "start" }));
  await layout(page, "desktop-soul-adapter");
  await shot(page, "05-desktop-soul-adapter.png");
  await page.click("#applySoulProfile");

  await page.click('[data-view="missions"]');
  await page.click("#loadSampleMission");
  await layout(page, "desktop-mission-loop");
  await shot(page, "06-desktop-mission-loop.png");
  record("all five visible mission stages exist", await page.locator("[data-mission-stage]").count() === 5, await page.locator("[data-mission-stage]").count());
  record("sample remains explicitly synthetic", (await page.locator("#missionStatus").textContent() || "").includes("Synthetic"), await page.locator("#missionStatus").textContent());

  await page.click('[data-view="capabilities"]');
  await layout(page, "desktop-capabilities");
  await shot(page, "07-desktop-capabilities.png");
  record("17 capability cards are visible", await page.locator(".capability-card").count() === 17, await page.locator(".capability-card").count());

  await page.click('[data-view="guide"]');
  await layout(page, "desktop-guide");
  await shot(page, "08-desktop-guide.png");
  await page.locator("#guide-help").scrollIntoViewIfNeeded();
  await shot(page, "09-desktop-guide-bottom.png");
  record("Guide contains 12 sections", await page.locator(".guide-content article").count() === 12, await page.locator(".guide-content article").count());

  await page.addScriptTag({ path: `${qaRoot}/axe-core/axe.min.js` });
  const axeResult = await page.evaluate(async () => window.axe.run(document, { rules: { "color-contrast": { enabled: true } } }));
  report.axe = axeResult.violations.map((item) => ({ id: item.id, impact: item.impact, help: item.help, nodes: item.nodes.length, targets: item.nodes.slice(0, 8).map((node) => node.target) }));
  const serious = report.axe.filter((item) => ["critical", "serious"].includes(item.impact));
  record("real-browser axe has no critical or serious violations", serious.length === 0, serious);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:43127/", { waitUntil: "networkidle" });
  await page.waitForTimeout(250);
  if (await page.locator("#onboardingDialog").getAttribute("open") !== null) await completeOnboarding(page);
  await layout(page, "mobile-dashboard");
  await shot(page, "10-mobile-dashboard.png");
  await page.click("#menuButton");
  record("mobile navigation exposes Missions and Guide", await page.locator('[data-view="missions"]').isVisible() && await page.locator('[data-view="guide"]').isVisible(), null);
  await shot(page, "11-mobile-navigation.png");
  await page.click('[data-view="missions"]');
  await layout(page, "mobile-missions");
  await shot(page, "12-mobile-missions.png");

  const keyboard = await keyboardSmoke(page);
  record("keyboard navigation reaches visible-focus controls", keyboard.ok, keyboard);
  record("browser console has no errors", report.console_errors.length === 0, report.console_errors);
} finally {
  if (browser) await browser.close();
  server.kill("SIGTERM");
}

const failed = report.checks.filter((item) => !item.passed);
report.summary = { passed: report.checks.length - failed.length, failed: failed.length };
await writeFile(resolve(out, "visual-qa-report.json"), `${JSON.stringify(report, null, 2)}\n`);
for (const item of report.checks) console.log(`${item.passed ? "PASS" : "FAIL"}  ${item.name}${item.passed ? "" : ` — ${JSON.stringify(item.detail)}`}`);
console.log(`SUMMARY passed=${report.summary.passed} failed=${report.summary.failed}`);
if (failed.length) process.exitCode = 1;

async function waitForHealth() {
  for (let attempt = 0; attempt < 50; attempt += 1) {
    if (server.exitCode !== null) throw new Error(`Server stopped before visual QA: ${serverOutput}`);
    try {
      const response = await fetch("http://127.0.0.1:43127/health");
      if (response.ok) return;
    } catch { /* retry */ }
    await new Promise((resolveWait) => setTimeout(resolveWait, 100));
  }
  throw new Error(`Server did not become healthy: ${serverOutput}`);
}

async function layout(page, label) {
  const result = await page.evaluate(() => {
    const viewportWidth = document.documentElement.clientWidth;
    const overflow = document.documentElement.scrollWidth - viewportWidth;
    const clipped = [];
    document.querySelectorAll("main :is(h1,h2,h3,p,button,label,select,input,textarea,article)").forEach((element) => {
      if (!(element instanceof HTMLElement)) return;
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      if (style.display === "none" || style.visibility === "hidden" || rect.width === 0 || rect.height === 0) return;
      if (rect.right > viewportWidth + 3 && style.position !== "fixed") clipped.push({ tag: element.tagName, id: element.id, class: element.className, right: Math.round(rect.right), viewportWidth });
    });
    return { viewportWidth, scrollWidth: document.documentElement.scrollWidth, overflow, clipped: clipped.slice(0, 20) };
  });
  record(`${label} has no page-level horizontal overflow`, result.overflow <= 2, result);
  record(`${label} has no clipped visible main controls`, result.clipped.length === 0, result.clipped);
}

async function shot(page, filename) {
  const path = resolve(out, filename);
  await page.screenshot({ path, fullPage: false, animations: "disabled" });
  report.screenshots.push({ filename, full_page: false });
}

async function completeOnboarding(page, { alreadyOnSafetyStep = false } = {}) {
  if (!alreadyOnSafetyStep) {
    const safetyVisible = await page.locator('#onboardingDialog [data-onboarding-step="1"]').isVisible().catch(() => false);
    if (!safetyVisible) await page.click("#onboardingNext");
  }
  await page.locator("#onboardingSafetyAck").check();
  await page.click("#onboardingNext");
  await page.click("#onboardingNext");
  await page.click("#onboardingFinish");
}

async function keyboardSmoke(page) {
  await page.keyboard.press("Home");
  await page.keyboard.press("Tab");
  const first = await page.evaluate(() => {
    const active = document.activeElement;
    return { tag: active?.tagName, class: active?.className, outline: active instanceof Element ? getComputedStyle(active).outlineStyle : "none" };
  });
  for (let index = 0; index < 8; index += 1) await page.keyboard.press("Tab");
  const later = await page.evaluate(() => {
    const active = document.activeElement;
    return { tag: active?.tagName, id: active?.id, class: active?.className, outline: active instanceof Element ? getComputedStyle(active).outlineStyle : "none" };
  });
  return { ok: ["A", "BUTTON"].includes(first.tag) && first.outline !== "none" && ["A", "BUTTON", "SELECT", "INPUT"].includes(later.tag), first, later };
}

function record(name, passed, detail) { report.checks.push({ name, passed: Boolean(passed), detail: passed ? null : detail }); }
