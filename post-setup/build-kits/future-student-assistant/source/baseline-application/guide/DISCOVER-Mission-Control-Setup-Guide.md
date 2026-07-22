# Nurse AI OS Mission Control — Setup and User Guide

**Version:** 2.0.0  
**Product ID:** `discover-nurse-ai-os-mission-control`  
**Hermes companion ID:** `NAIOS-MISSION-CONTROL-LOCAL-2.0.0`  
**Use:** governed local workspace + manual Hermes handoff

## 1. What Mission Control is

Mission Control is a local dashboard for turning a Discover Packet, a derived Soul Quiz result, and the user's chosen roles into a disciplined workspace. It supports learning, planning, project work, role development, solution exploration, and continuous improvement.

It is designed to help a person:

- keep one identity while using several role-specific dashboards;
- turn a goal or problem into a five-stage mission;
- separate exploration from authorized execution;
- prepare clear, bounded requests for Hermes;
- record sanitized evidence of capability development; and
- keep human judgment, permissions, and accountability visible.

It is not an EHR, approved record system, clinical decision system, credentialing platform, autonomous agent, or institutionally managed governance service.

## 2. Before installation

Choose a personal or organization-approved computer, browser profile, and folder. Keep the following out of the dashboard, its exports, and Hermes handoffs unless a separate approved deployment is explicitly configured for that data class:

- PHI and patient identifiers;
- participant-level research information;
- confidential institutional, personnel, academic, sponsor, legal, financial, contract, peer-review, or invention information;
- passwords, API keys, tokens, connection strings, or authentication data; and
- sensitive personal data.

Browser `localStorage` is local to a browser profile but **unencrypted**. A locally saved mission and a dashboard backup may contain the text you enter. Treat both as readable files, not protected records.

AI supports—but does not replace—professional judgment. The user remains responsible for verifying facts, evidence, recommendations, artifacts, permissions, and final actions.

> **Allow time:** Local launch normally takes seconds. First-run review, Discover Packet adaptation, Soul Profile adaptation, Role Constellation setup, and backup inspection may take several minutes. Hermes registration can require multiple visible, reviewed turns. Nothing runs in the background; wait for each visible result.

## 3. Exact installation order

Follow these steps in order.

### Step 1 — Extract the package

Unzip the complete package into a folder you control. Do not run it from inside the ZIP. Keep `index.html`, `assets/`, `guide/`, `hermes/`, and the launcher files together.

### Step 2 — Review the package

Read:

1. `README-FIRST.md`
2. `PRIVACY.md`
3. `SECURITY.md`

If release checksums are provided, compare them before first use. A checksum confirms file identity, not clinical safety, institutional approval, or trustworthy content.

### Step 3 — Start the local dashboard

Use one of the following methods.

**macOS**

1. Double-click `Start-DISCOVER.command`.
2. If macOS blocks it, right-click the file, choose **Open**, and confirm.
3. Keep the Terminal window open while using Mission Control.
4. Press `Control+C` in that window to stop the local server.

**Windows**

1. Double-click `Start-DISCOVER.bat`.
2. Keep the command window open.
3. Press `Control+C` to stop the local server.

**Linux**

1. If needed, run `chmod +x start-discover.sh`.
2. Run `./start-discover.sh`.
3. Press `Control+C` to stop the local server.

**Portable fallback**

Open `index.html` directly. Portable mode needs no local server or administrator access. Clipboard and browser-storage behavior may vary under `file://`, so test an export before relying on it.

When Node.js is available, the launcher uses a loopback-only server at `http://127.0.0.1:43127`. It does not expose a write API or an internet-facing service.

### Step 4 — Complete the first-run walkthrough

Read the processing message, local-storage boundary, multi-role explanation, and manual-Hermes boundary. Acknowledge that:

- locally saved text is not encrypted;
- prohibited data must stay out;
- the app does not send or execute prompts; and
- real-world actions require separate human authority.

### Step 5 — Build the Role Constellation

Open **My Role Dashboards** and select one or more views. Describe each as:

- **Primary:** the main current dashboard;
- **Supporting:** an active complementary role;
- **Emerging:** a role being developed; or
- **Contextual:** a role used for a particular situation.

The available templates include student/nursing assistant, staff nurse, advanced-practice clinician, nurse educator, medical resident, nurse or healthcare manager, clinic manager, hospital administrator, wellness manager, quality/safety contributor, researcher, responsible-AI/informatics leader, entrepreneur/consultant, community/family advocate, and advanced studies.

The role switcher changes context and recommendations. It does not verify identity, employment, education, delegation, licensure, competence, or authority. A role dashboard cannot expand the user's lawful or organizational scope.

### Step 6 — Import a derived Discover Packet only when ready

Open **Soul Profile & Personalization**, then use the Discover Packet adapter. Download the template or inspect the synthetic example. Import only `NAIO-DISCOVER-PACKET-ADAPTER-1` derived settings—never raw interview notes, identifying details, PHI, confidential organizational content or secrets.

Preview the mission statement, current priorities, short-/medium-/long-term goals, role goals, working preferences, recommended workflows, capability pathways, AI boundaries, EDENA default and retention default. Applying a packet can tune those local settings and add supporting role dashboards. It cannot grant a role, enable an agent, approve an action or weaken safety gates. Clear or replace the packet as the user evolves.

### Step 7 — Import a Soul Profile only when ready

Remain on **Soul Profile & Personalization**. The Nurse AI OS Soul Quiz is being redesigned, so version 2.0.0 uses the replaceable adapter `NAIO-SOUL-PROFILE-ADAPTER-1`.

Recommended sequence:

1. Download the adapter template.
2. Obtain or create a reviewed, derived result that matches the schema.
3. Remove raw answers, identifying details, and sensitive information.
4. Import the JSON.
5. Preview proposed wording, theme, priorities, and role recommendations.
6. Apply only after review.
7. Use restore or clear if the result is wrong or outdated.

Soul Profile data can influence appearance, communication cues, role recommendations, and workflow emphasis. It cannot grant authority, verify competence, alter permissions, weaken EDENA safeguards, or make a professional decision. The retained 12-question quiz is a provisional local demonstration and is not a validated psychological, educational, employment, credentialing, or competence assessment.

### Step 8 — Start a safe mission

Open **Missions** and choose **Start a Mission** or **Load sample mission**. The sample is synthetic and exists to demonstrate the complete loop; it does not count as capability evidence.

For a new mission:

1. Enter a non-sensitive title and desired outcome.
2. Select the owning role dashboard.
3. Choose Personal Edition or Institutional policy preview.
4. Assign an EDENA advisory and record a brief, non-sensitive classification reason.
5. Choose an artifact state.
6. Select session-only or local non-sensitive retention.
7. Work through the five stages.

### Step 9 — Create and inspect a backup

Open **My Role Dashboards** and choose **Export dashboard profile**. Open the JSON in a text editor and confirm it contains no prohibited data. Store it only in an appropriate location.

### Step 10 — Add the local dashboard to Hermes

Only after the local app works, give Hermes:

1. `hermes/DISCOVER-Dashboard-Hermes-Integration-Installer.md`
2. `hermes/Hermes-Capability-State.md`

Provide the exact absolute folder or `index.html` path when Hermes asks. Do not let Hermes guess the location. Approve only a visible, lane-scoped link, Guide entry, or capability record your Hermes version supports.

Manual handoff only is a valid final state. A local link does not create synchronization, permission, or execution capability.

## 4. The five-stage Mission Loop

Mission Control uses the nursing process and continuous-improvement logic as a visible, repeatable loop.

### Assess

Record the current state. Separate:

- verified facts;
- user-provided information;
- assumptions;
- unresolved questions;
- constraints and resources;
- stakeholder views; and
- credible sources.

### Define or Diagnose

State the bounded problem, opportunity, need, or decision. Identify root or contributing factors, dependencies, risks, gaps, and competing interpretations. The label “Diagnose” does not authorize an AI-generated clinical diagnosis.

### Plan

Compare alternatives by likely benefit, feasibility, time, cost, burden, equity, ethics, and risk. Document outcomes, milestones, owners, measures, safeguards, human approval gates, stop rules, and rollback.

### Implement

Prepare tasks, prompts, checklists, agents, and draft artifacts. The local application performs no external action. Record action as user-reported or independently verified; never imply the app executed or approved it.

### Evaluate

Compare observed results with the intended outcome. Record evidence, variance, unintended effects, uncertainty, and what worked or failed. Choose to continue, modify, escalate, stop, declare the bounded goal achieved, or begin another iteration.

Users may pause, revise, return to an earlier stage, and start a new cycle. Revising an earlier stage can make later work require review again.

## 5. Sandbox artifact states

Use artifact labels precisely:

- **Exploration:** investigating a question without committing to a solution.
- **Simulation:** testing a hypothetical scenario or model.
- **Recommendation:** a proposed direction requiring review.
- **Draft artifact:** unfinished content requiring verification.
- **Approved plan:** a plan the user attests was reviewed outside the app; the app does not verify approval.
- **Authorized execution:** the user records that separate authority exists; the app does not grant it.
- **Completed action:** user-reported or independently verified real-world completion.
- **Evaluated outcome:** an action whose result and limitations were reviewed.

Do not jump labels merely to make a mission look complete. Artifact state does not override EDENA classification, professional scope, law, policy, or required authorization.

## 6. EDENA governance

### Personal Edition

EDENA is advisory. Green supports bounded low-consequence exploration. Yellow requires deliberate verification. Orange requires qualified-human review. Red triggers a prominent warning and requires deliberate acknowledgment before sanitized sandbox exploration. Red never approves direct clinical, legal, financial, employment, academic, research, or institutional use.

Personal Edition does not silently suppress safe exploration, but it also cannot authorize real-world action.

### Institutional policy preview

This setting demonstrates stricter stopping behavior. It is a **policy preview**, not tamper-resistant enforcement. A static local app cannot validate identity, policy state, external approvals, immutable logs, segregation of duties, technical access controls, or institutional authorization.

A real Institutional or Departmental Edition requires centrally managed policy, authentication, authorization, audit, retention, monitoring, approval pathways, and incident response. Those controls take precedence over personal preferences.

## 7. Capabilities and Mastery

Open **Capabilities** to add sanitized evidence. Accepted evidence categories can include evaluated missions, reviewed artifacts, measures, feedback, reflection, safety or governance drills, and governed agent records.

Each record should state:

- the capability;
- the evidence or activity;
- the date and provenance;
- the mission or artifact when relevant;
- the EDENA behavior demonstrated; and
- the next challenge.

The four development levels are Basic, Intermediate, Advanced, and AI Agent Orchestration Master. Progress requires evidence; clicking a button is not achievement. Sample missions are excluded. Badges never unlock agents, permissions, data classes, automations, or external actions.

These levels are development records only. They are not licensure, certification, CE credit, institutional authorization, clinical privilege, or proof of professional competence.

## 8. Prepare a Hermes handoff

Mission and workflow handoffs are manual:

1. Open the relevant mission stage or workflow card.
2. Include only public, synthetic, or approved non-sensitive information.
3. Generate the Markdown preview locally.
4. Read the complete content and remove prohibited data.
5. Check the review acknowledgment.
6. Copy or download the Markdown.
7. Open Hermes separately.
8. Paste into the appropriate Nurse AI OS workspace and role context.
9. Review Hermes's visible output.
10. Obtain any required qualified or institutional review before real use.

The dashboard never sends a prompt, starts a Hermes agent, schedules a task, polls for results, or writes to an external system. The optional **Open Hermes** control opens only the user-supplied trusted `http://` or `https://` address and does not include prompt content in the URL.

## 9. Suggested operating rhythm

- **Daily:** choose the active role, review one mission, and confirm the safety boundary.
- **Weekly:** update the mission loop, verify open assumptions, and review evidence freshness.
- **Monthly:** review role priorities, stalled missions, artifacts, risks, and capability evidence.
- **Quarterly:** revisit the Discover Packet, Soul Profile, Role Constellation, permissions, governance preferences, and stop/continue choices.

Update the derived Discover Packet when goals, priorities, workflows, or AI boundaries materially change. Update the Soul Profile when roles, values, communication style, or learning preferences materially change. Preview both before applying every update; neither change authorizes action.

## 10. Backup

1. Review open session-only missions intentionally. They are not written to persistent browser storage, but any non-sample mission still open in the page is included in an explicit backup export.
2. Export the dashboard profile only when you are ready to create that readable copy.
3. Open the JSON and review every mission, evidence record, role, Discover Packet field, and Soul Profile field.
4. Remove prohibited or unnecessary text in Mission Control, then export again.
5. Record the app version and export date.
6. Store the file in an approved location.

The export is readable JSON, not encrypted. Do not email, sync, or share it without reviewing its contents and destination.

## 11. Update and rollback

### Safe update

1. Export and inspect a backup from the current version.
2. Keep the entire current folder unchanged.
3. Unzip the new version into a new folder; do not overwrite the old folder.
4. Read the new `CHANGELOG.md`, `PRIVACY.md`, and `SECURITY.md`.
5. Verify release checksums when supplied.
6. Open the new version side by side.
7. Import the reviewed backup only if the new version accepts that schema.
8. Verify roles, Discover Packet, Soul Profile, missions, evidence, EDENA behavior, Guide, and manual handoff.
9. Update the Hermes local link only after the new version works.
10. Retain the old folder and backup until the new release is accepted.

### Rollback

1. Stop the new local launcher.
2. Do not delete the old folder or its backup.
3. Reopen the old version using its original launcher or `index.html`.
4. If required, import the backup created by that version. Do not force a newer schema into an older release.
5. Restore the prior Hermes local link or return to manual handoff.
6. Record why the update was rejected.

Browser storage is separated by origin and storage key, so two releases may not automatically see the same data. A link rollback does not migrate data by itself.

## 12. Uninstall

See `UNINSTALL.md`. In brief:

1. Export and inspect anything you intend to retain.
2. Use **Reset all local personalization** in the version being removed.
3. Remove only this package's local link and Guide entry from Hermes.
4. Stop the local launcher.
5. Delete the package folder and any unneeded backups.

Do not remove the broader Nurse AI OS, another role dashboard, or the optional legacy research specialization unless that is a separate, explicit decision.

## 13. Troubleshooting

**The page is unstyled.** Keep `index.html` beside `assets/` and reopen the page.

**The launcher does not start.** Confirm Node.js is available and port `43127` is free. Portable `index.html` mode remains available.

**Copy is blocked.** Use Download Markdown or manually select the visible prompt. Some browsers restrict clipboard access for local pages.

**Personalization disappeared.** Private browsing, browser cleanup, a different browser profile, a different origin, or a reset may create an empty store. Import a reviewed compatible backup.

**A session-only mission disappeared.** That is the intended retention behavior. Use local non-sensitive retention only for content permitted in unencrypted browser storage.

**Hermes cannot open the local page.** Give Hermes the exact local path. If local-file links are unsupported, keep a desktop shortcut and use manual copy/paste. Do not expose the loopback server to the network or invent a custom URL scheme.

**The Soul Profile is rejected.** Confirm the exact adapter schema, size limits, allowed roles, and absence of raw answers or sensitive fields. Start from the included template.

**The Discover Packet is rejected.** Confirm `NAIO-DISCOVER-PACKET-ADAPTER-1`, the 100 KB limit, allowed role/workflow/capability IDs, exact fields, and the absence of raw interview notes or sensitive material. Start from `config/discover-packet-input.schema.json` and the included deidentified example.

**The Institutional mode does not enforce organization policy.** It is intentionally labeled a policy preview. Use an institution-managed deployment for real enforcement.

**A badge seems too high or too low.** Review the underlying evidence. Delete weak or duplicate records and add only observable, sanitized, appropriately governed evidence. The badge is not a credential.

## 14. Optional legacy research specialization

`base-pack/` contains an earlier DISCOVER package for Healthcare Research & Innovation Leaders. It is preserved as an optional research/innovation specialization. It is not required for Mission Control 2.0.0, is not the universal Nurse AI OS core, and should not be installed automatically for unrelated roles.
