import { createRequire } from "node:module";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";

const require = createRequire(import.meta.url);
const qaModules = process.env.DISCOVER_QA_NODE_MODULES || "/tmp/discover-dashboard-qa/node_modules";
const { JSDOM } = require(`${qaModules}/jsdom`);
const axe = require(`${qaModules}/axe-core`);

const root = resolve("deliverables/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0");
const html = await readFile(resolve(root, "index.html"), "utf8");
const script = await readFile(resolve(root, "assets/app.js"), "utf8");
const assertions = [];
const runtimeErrors = [];
const openedUrls = [];
const downloads = [];

const dom = new JSDOM(html, {
  url: "http://127.0.0.1:43127/",
  pretendToBeVisual: true,
  runScripts: "outside-only"
});

const { window } = dom;
window.confirm = () => true;
window.scrollTo = () => {};
window.open = (url) => { openedUrls.push(String(url)); return null; };
window.URL.createObjectURL = () => `blob:qa-${downloads.length + 1}`;
window.URL.revokeObjectURL = () => {};
window.document.execCommand = () => true;
Object.defineProperty(window.navigator, "clipboard", { value: { writeText: async () => {} }, configurable: true });
if (!window.File.prototype.text) {
  window.File.prototype.text = function textFile() {
    return new Promise((resolveText, rejectText) => {
      const reader = new window.FileReader();
      reader.addEventListener("load", () => resolveText(String(reader.result || "")));
      reader.addEventListener("error", () => rejectText(reader.error || new Error("Unable to read test file")));
      reader.readAsText(this);
    });
  };
}
if (window.HTMLDialogElement) {
  window.HTMLDialogElement.prototype.showModal = function showModal() { this.open = true; };
  window.HTMLDialogElement.prototype.close = function close() { this.open = false; };
}
window.HTMLAnchorElement.prototype.click = function click() {
  if (this.download) downloads.push({ name: this.download, href: this.href });
};
window.addEventListener("error", (event) => runtimeErrors.push(event.error?.stack || event.message));
window.addEventListener("unhandledrejection", (event) => runtimeErrors.push(String(event.reason)));

window.eval(script);
await tick(230);

test("dashboard initializes without runtime errors", runtimeErrors.length === 0, runtimeErrors);
test("processing message is displayed on first run", text("#onboardingDialog").includes("Your Nurse AI OS Mission Control is being prepared"), text("#onboardingDialog").slice(0, 220));
window.document.getElementById("onboardingNext").click();
window.document.getElementById("onboardingSafetyAck").checked = true;
window.document.getElementById("onboardingNext").click();
window.document.getElementById("onboardingNext").click();
window.document.getElementById("onboardingFinish").click();
await tick();
test("required first-run walkthrough completes only after safety acknowledgment", storedState().onboardingComplete === true && !window.document.getElementById("onboardingDialog").open, { onboardingComplete: storedState().onboardingComplete, open: window.document.getElementById("onboardingDialog").open });

test("24 workflows render", count(".workflow-card") === 24, count(".workflow-card"));
test("24 SuperPowers render", count(".power-card") === 24, count(".power-card"));
test("30 templates render", count(".template-item") === 30, count(".template-item"));
test("17 role recipes including a neutral shared identity are available", count(".role-option") === 17, count(".role-option"));
test("17 capability pathways render", count(".capability-card") === 17, count(".capability-card"));
test("Guide contains 12 numbered sections", count(".guide-content article") === 12, count(".guide-content article"));
test("permanent safety boundary is visible", text("body").includes("No automatic network calls or external actions") && text("body").includes("Do not enter PHI"), "missing safety copy");

clickView("soul");
window.document.getElementById("loadSampleDiscover").click();
test("synthetic Discover Packet is explicitly labeled", text("#discoverPacketPreviewHeading").includes("Synthetic"), text("#discoverPacketPreviewHeading"));
window.document.getElementById("applyDiscoverPacket").click();
await tick();
let persisted = storedState();
test("derived Discover Packet adapter applies without raw notes", persisted.discoverPacket?.schema === "NAIO-DISCOVER-PACKET-ADAPTER-1", persisted.discoverPacket?.schema);
test("synthetic Discover Packet remains labeled as demo", persisted.discoverPacket?.demo === true, persisted.discoverPacket?.demo);
test("Discover role goals add supporting dashboards without changing authority", persisted.selectedRoleIds.includes("nurse-manager") && persisted.selectedRoleIds.includes("quality-safety") && persisted.roleStates["nurse-manager"] === "supporting" && persisted.roleStates["quality-safety"] === "supporting", { selectedRoleIds: persisted.selectedRoleIds, roleStates: persisted.roleStates });
window.document.getElementById("loadSampleSoul").click();
test("synthetic Soul profile is explicitly labeled", text("#soulProfilePreviewHeading").includes("Synthetic"), text("#soulProfilePreviewHeading"));
window.document.getElementById("applySoulProfile").click();
await tick();
persisted = storedState();
test("derived Soul adapter applies without raw answers", persisted.soulProfile?.schema === "NAIO-SOUL-PROFILE-ADAPTER-1" && persisted.soul === null, persisted.soulProfile?.schema);
test("synthetic Soul profile remains labeled as demo", persisted.soulProfile?.demo === true, persisted.soulProfile?.demo);
test("Soul adaptation preserves exactly one primary role", Object.values(persisted.roleStates).filter((value) => value === "primary").length === 1 && persisted.roleStates["nurse-manager"] === "primary", persisted.roleStates);
test("raw quiz answers are absent from local storage", !/When an opportunity appears|Strongly me|Rarely me/.test(rawState()), "raw question or answer marker found");

clickView("roles");
for (const roleId of ["staff-nurse", "nurse-manager"]) window.document.getElementById(`role-${roleId}`).checked = true;
window.document.querySelector('[name="role-state-shared-identity"]').value = "supporting";
window.document.querySelector('[name="role-state-staff-nurse"]').value = "supporting";
window.document.querySelector('[name="role-state-nurse-manager"]').value = "primary";
window.document.getElementById("roleForm").dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true }));
await tick();
persisted = storedState();
test("multi-role constellation persists under one identity", persisted.selectedRoleIds.includes("staff-nurse") && persisted.selectedRoleIds.includes("nurse-manager"), persisted.selectedRoleIds);
test("manual constellation has exactly one primary role", Object.values(persisted.roleStates).filter((value) => value === "primary").length === 1 && persisted.roleStates["nurse-manager"] === "primary", persisted.roleStates);
test("role dashboards have distinct opaque partitions", new Set(Object.values(persisted.dashboards).map((item) => item.dashboardId)).size === persisted.selectedRoleIds.length, persisted.dashboards);

clickView("missions");
window.document.getElementById("newMission").click();
window.document.getElementById("missionTitle").value = "Improve a synthetic learning routine";
window.document.getElementById("missionSummary").value = "Create and evaluate a nonclinical learning routine using public information and a measurable usefulness check.";
window.document.getElementById("missionEdena").value = "green";
window.document.getElementById("missionEdena").dispatchEvent(new window.Event("change", { bubbles: true }));
window.document.getElementById("missionEdenaReason").value = "Synthetic nonclinical learning routine using public information; bounded and reversible.";
window.document.getElementById("stageAssessNotes").value = "Verified facts: the example uses public information only. Assumption: a brief routine is feasible.";
window.document.getElementById("stageAssessOutcome").value = "A bounded learning test is feasible; schedule and usefulness remain to be tested.";
window.document.getElementById("stageAssessComplete").checked = true;
submit("missionForm");
await tick();
test("session-only mission is not written to localStorage", storedState().missions.length === 0, storedState().missions);

window.document.getElementById("missionRetention").value = "local_non_sensitive";
submit("missionForm");
await tick();
persisted = storedState();
test("explicit local non-sensitive retention persists mission", persisted.missions.length === 1, persisted.missions.length);

window.document.getElementById("missionArtifactState").value = "evaluated_outcome";
submit("missionForm");
await tick();
test("artifact states cannot jump from Exploration to Evaluated Outcome", storedState().missions[0].artifactState === "exploration" && text("#missionStatus").includes("one gate at a time"), { artifactState: storedState().missions[0].artifactState, status: text("#missionStatus") });
window.document.getElementById("missionArtifactState").value = "exploration";

const stageFixtures = {
  define: ["Central opportunity: make a learning habit reliable without hidden burden.", "Test one bounded routine."],
  plan: ["Compare a live review, an asynchronous note and alternating formats. Use stop and rollback rules.", "Pilot one format twice; measure usefulness and preparation time."],
  implement: ["Prepared a draft checklist. No message, schedule or external action was created by this app.", "User may test the reviewed draft outside this app under their own authority."],
  evaluate: ["Compare observed usefulness and preparation time with the goal; record limits and next-cycle decision.", "Continue one iteration only if usefulness improves without added burden."]
};
for (const [stage, [notes, outcome]] of Object.entries(stageFixtures)) {
  const prefix = stage.charAt(0).toUpperCase() + stage.slice(1);
  window.document.getElementById(`stage${prefix}Notes`).value = notes;
  window.document.getElementById(`stage${prefix}Outcome`).value = outcome;
  window.document.getElementById(`stage${prefix}Complete`).checked = true;
}
window.document.getElementById("missionStatusState").value = "completed";
submit("missionForm");
await tick();
persisted = storedState();
test("five-stage mission can be completed only with Evaluate reviewed", persisted.missions[0].missionStatus === "completed" && persisted.missions[0].stages.evaluate.complete, persisted.missions[0]);

window.document.getElementById("missionEdena").value = "red";
window.document.getElementById("missionEdena").dispatchEvent(new window.Event("change", { bubbles: true }));
window.document.getElementById("missionEdenaReason").value = "High-consequence scenario used only to verify the advisory and review boundaries.";
window.document.getElementById("missionRiskAck").checked = true;
submit("missionForm");
await tick();
persisted = storedState();
test("EDENA changes reopen Plan through Evaluate and clear completed status", persisted.missions[0].missionStatus === "active" && !persisted.missions[0].stages.plan.complete && !persisted.missions[0].stages.implement.complete && !persisted.missions[0].stages.evaluate.complete, persisted.missions[0]);
window.document.getElementById("prepareMissionHandoff").click();
await tick();
let handoff = window.document.getElementById("missionHandoffOutput").value;
test("Personal Red permits sanitized reviewable exploration handoff", handoff.includes("edena_tier: red") && handoff.includes("external_action: prohibited") && handoff.includes("NO EXTERNAL ACTION TAKEN"), handoff.slice(0, 350));
window.document.getElementById("closeMissionHandoff").click();

window.document.getElementById("missionEdition").value = "institutional_preview";
window.document.getElementById("missionEdition").dispatchEvent(new window.Event("change", { bubbles: true }));
submit("missionForm");
await tick();
for (const artifact of ["simulation", "recommendation"]) {
  window.document.getElementById("missionArtifactState").value = artifact;
  submit("missionForm");
  await tick();
}
window.document.getElementById("stagePlanComplete").checked = true;
window.document.getElementById("missionArtifactState").value = "draft_artifact";
submit("missionForm");
await tick();
window.document.getElementById("missionArtifactState").value = "approved_plan";
window.document.getElementById("missionApprovalAttested").checked = true;
window.document.getElementById("missionApprovalRef").value = "SYNTHETIC-REVIEW-REF";
submit("missionForm");
await tick();
test("Institutional Red policy preview blocks Approved Plan transition", text("#missionStatus").includes("Institutional policy preview blocks"), text("#missionStatus"));

window.document.getElementById("missionEdition").value = "personal";
window.document.getElementById("missionEdition").dispatchEvent(new window.Event("change", { bubbles: true }));
window.document.getElementById("missionEdena").value = "green";
window.document.getElementById("missionEdena").dispatchEvent(new window.Event("change", { bubbles: true }));
window.document.getElementById("missionEdenaReason").value = "Returned to the bounded synthetic public-information learning routine for evidence review.";
window.document.getElementById("missionArtifactState").value = "recommendation";
submit("missionForm");
await tick();
for (const stage of ["Plan", "Implement", "Evaluate"]) window.document.getElementById(`stage${stage}Complete`).checked = true;
window.document.getElementById("missionStatusState").value = "completed";
submit("missionForm");
await tick();
persisted = storedState();
test("reviewed stages can be re-completed after governance reclassification", persisted.missions[0].edena === "green" && persisted.missions[0].missionStatus === "completed" && ["plan", "implement", "evaluate"].every((stage) => persisted.missions[0].stages[stage].complete), persisted.missions[0]);

clickView("capabilities");
const missionId = storedState().missions[0].id;
for (const [type, summary] of [
  ["mission", "Completed and evaluated one bounded learning mission."],
  ["artifact_review", "Reviewed a draft checklist against its success measure and safety boundary."],
  ["reflection", "Recorded what changed, what remained uncertain and the next safe challenge."],
  ["safety_drill", "Practiced a no-PHI stop rule and documented the rollback response."]
]) {
  window.document.getElementById("evidenceCapability").value = "structured-problem-solving";
  window.document.getElementById("evidenceMission").value = missionId;
  window.document.getElementById("evidenceType").value = type;
  window.document.getElementById("evidenceProvenance").value = type === "mission" ? "app_observed" : "user_attested";
  window.document.getElementById("evidenceEdena").value = "green";
  window.document.getElementById("evidenceSummary").value = summary;
  window.document.getElementById("evidenceAttestation").checked = true;
  submit("evidenceForm");
  await tick();
}
persisted = storedState();
test("evidence-based Basic level requires four distinct records", persisted.evidence.length === 4 && text("#view-capabilities").includes("Basic"), { evidence: persisted.evidence.length, capabilityText: text("#view-capabilities").slice(0, 400) });
test("capability page carries noncredential warning", text("#view-capabilities").includes("not licensure") && text("#view-capabilities").includes("not a credential"), text("#view-capabilities").slice(0, 500));

window.document.getElementById("evidenceCapability").value = "structured-problem-solving";
window.document.getElementById("evidenceMission").value = missionId;
window.document.getElementById("evidenceType").value = "reflection";
window.document.getElementById("evidenceSummary").value = "A repeated click must not manufacture progress.";
window.document.getElementById("evidenceAttestation").checked = true;
submit("evidenceForm");
await tick();
test("duplicate evidence does not manufacture badge progress", storedState().evidence.length === 4 && text("#evidenceStatus").includes("already recorded"), { evidence: storedState().evidence.length, status: text("#evidenceStatus") });

clickView("workflows");
window.document.querySelector(".workflow-card .primary-button").click();
window.document.getElementById("workflowContext").value = "PUBLIC_SAFE_LEARNER_CONTEXT_PLACEHOLDER";
window.document.getElementById("handoffEdena").value = "green";
window.document.getElementById("handoffEdenaReason").value = "Synthetic bounded workflow preview using public information.";
window.document.getElementById("handoffConsent").checked = true;
window.document.getElementById("buildHandoff").click();
test("obvious identifier marker blocks workflow handoff", window.document.getElementById("handoffOutput").value === "" && text("#handoffStatus").includes("medical record identifier"), text("#handoffStatus"));
window.document.getElementById("closeWorkflowDialog").click();

window.document.querySelector(".workflow-card .primary-button").click();
window.document.getElementById("workflowContext").value = "Synthetic public-information scenario.";
window.document.getElementById("handoffEdena").value = "green";
window.document.getElementById("handoffEdenaReason").value = "Synthetic bounded workflow preview using public information.";
window.document.getElementById("handoffConsent").checked = true;
window.document.getElementById("buildHandoff").click();
test("workflow handoff records EDENA advisory and reason", window.document.getElementById("handoffOutput").value.includes("EDENA Green") && window.document.getElementById("handoffOutput").value.includes("Synthetic bounded workflow preview"), window.document.getElementById("handoffOutput").value.slice(0, 400));
window.document.getElementById("hermesUrl").value = "ftp://example.test/path";
window.document.getElementById("openHermes").click();
test("non-HTTP Hermes address is rejected", openedUrls.length === 0, openedUrls);
window.document.getElementById("hermesUrl").value = "http://example.test/path";
window.document.getElementById("openHermes").click();
test("remote plaintext HTTP Hermes address is rejected", openedUrls.length === 0, openedUrls);
window.document.getElementById("hermesUrl").value = "http://127.0.0.1:8000/";
window.document.getElementById("openHermes").click();
test("trusted Hermes address opens separately without prompt", openedUrls.length === 1 && openedUrls[0] === "http://127.0.0.1:8000/" && !openedUrls[0].includes("prompt"), openedUrls);
window.document.getElementById("closeWorkflowDialog").click();

clickView("roles");
window.document.getElementById("exportProfile").click();
test("explicit backup download is clearly versioned", downloads.some((item) => item.name === "DISCOVER-Mission-Control-Backup-v2.json"), downloads);

const input = window.document.getElementById("importProfile");
const validFile = new window.File([JSON.stringify(backupFixture(storedState()))], "valid.json", { type: "application/json" });
Object.defineProperty(input, "files", { value: [validFile], configurable: true });
input.dispatchEvent(new window.Event("change", { bubbles: true }));
await tick(40);
test("closed-schema backup with Discover Packet and EDENA review metadata restores", text("#profileStatus").includes("Backup imported"), text("#profileStatus"));

const malicious = { ...backupFixture(storedState()), unexpected: "<img src=x onerror=alert(1)>" };
const badFile = new window.File([JSON.stringify(malicious)], "bad.json", { type: "application/json" });
Object.defineProperty(input, "files", { value: [badFile], configurable: true });
input.dispatchEvent(new window.Event("change", { bubbles: true }));
await tick(40);
test("closed-schema backup import rejects unexpected fields", text("#profileStatus").includes("rejected"), text("#profileStatus"));

window.eval(axe.source);
const axeResult = await window.axe.run(window.document, { rules: { "color-contrast": { enabled: false } } });
const serious = axeResult.violations.filter((item) => ["critical", "serious"].includes(item.impact));
test("axe finds no critical or serious DOM accessibility violations", serious.length === 0, serious.map((item) => ({ id: item.id, impact: item.impact, nodes: item.nodes.length })));
test("no asynchronous runtime errors occurred", runtimeErrors.length === 0, runtimeErrors);

const failed = assertions.filter((item) => !item.passed);
const report = {
  generated_at: new Date().toISOString(),
  app: "DISCOVER-NURSE-AI-OS-MISSION-CONTROL-2.0.0",
  passed: assertions.length - failed.length,
  failed: failed.length,
  assertions,
  axe: { violations: axeResult.violations.map((item) => ({ id: item.id, impact: item.impact, help: item.help, nodes: item.nodes.length })) },
  runtime_errors: runtimeErrors
};
await mkdir("qa", { recursive: true });
await writeFile("qa/discover-mission-control-v2-dom-qa.json", `${JSON.stringify(report, null, 2)}\n`);
for (const item of assertions) console.log(`${item.passed ? "PASS" : "FAIL"}  ${item.name}${item.passed ? "" : ` — ${JSON.stringify(item.detail)}`}`);
console.log(`SUMMARY passed=${report.passed} failed=${report.failed}`);
if (failed.length) process.exitCode = 1;

function backupFixture(internal) {
  return {
    schema: "DISCOVER-MISSION-CONTROL-PROFILE-2",
    app_version: "2.0.0",
    generated_at: new Date().toISOString(),
    instance_id: internal.instanceId,
    role_ids: internal.selectedRoleIds,
    active_role_id: internal.activeRoleId,
    active_mission_id: internal.activeMissionId,
    role_states: internal.roleStates,
    dashboards: Object.fromEntries(Object.entries(internal.dashboards).map(([key, value]) => [key, { dashboard_id: value.dashboardId, favorite_workflow_ids: value.favoriteWorkflowIds }])),
    soul: null,
    soul_profile: internal.soulProfile,
    discover_packet: internal.discoverPacket,
    missions: internal.missions,
    evidence: internal.evidence,
    guide_seen: false,
    onboarding_complete: false,
    edena_policy: "EDENA-MC-ADVISORY@1.0.0-draft",
    backup_edena: "yellow",
    backup_review_required: "Review this synthetic fixture before restoration.",
    privacy_note: "Test fixture"
  };
}

function test(name, passed, detail = null) { assertions.push({ name, passed: Boolean(passed), detail: passed ? null : detail }); }
function count(selector) { return window.document.querySelectorAll(selector).length; }
function text(selector) { return window.document.querySelector(selector)?.textContent || ""; }
function rawState() { return window.localStorage.getItem("discover.nurse-ai-os.mission-control.v2") || ""; }
function storedState() { return JSON.parse(rawState()); }
function clickView(view) { window.document.querySelector(`[data-view="${view}"]`).click(); }
function submit(id) { window.document.getElementById(id).dispatchEvent(new window.Event("submit", { bubbles: true, cancelable: true })); }
function tick(ms = 0) { return new Promise((resolveTick) => setTimeout(resolveTick, ms)); }
