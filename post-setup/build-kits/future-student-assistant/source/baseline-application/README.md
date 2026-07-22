# DISCOVER Nurse AI OS Mission Control 2.0.0

**Product ID:** `discover-nurse-ai-os-mission-control`  
**Hermes companion ID:** `NAIOS-MISSION-CONTROL-LOCAL-2.0.0`  
**Dashboard profile schema:** `DISCOVER-MISSION-CONTROL-PROFILE-2`  
**Discover Packet adapter:** `NAIO-DISCOVER-PACKET-ADAPTER-1`  
**Soul Profile adapter:** `NAIO-SOUL-PROFILE-ADAPTER-1`  
**Integration mode:** local static application + manual Hermes handoff

Mission Control is a colorful, role-aware workspace for learning, planning, structured problem-solving, project execution preparation, professional development, and continuous improvement. It converts a reviewed Discover Packet and derived Soul Quiz result into one governed personal workspace with multiple role dashboards.

It is a downloadable local application, not a design mockup. It runs as static HTML, CSS, and JavaScript. No account, database, build step, or network connection is required.

> Start with `README-FIRST.md`. Setup and personalization may take several minutes. Optional Hermes integration may require multiple visible, reviewed turns. Nothing runs in the background.

## What is included

- a first-run safety and onboarding walkthrough;
- one shared identity with primary, supporting, emerging, and contextual role dashboards;
- a versioned, derived Discover Packet import for goals, priorities, working preferences, role goals, workflow recommendations, AI boundaries and governance defaults;
- a versioned Soul Profile import, preview, apply, restore, and clear flow;
- a visible Assess → Define/Diagnose → Plan → Implement → Evaluate mission loop;
- pause, revise, return, iterate, retention, artifact-state, and EDENA controls;
- a sandbox distinction among exploration, simulation, recommendation, draft artifact, approved plan, authorized execution, completed action, and evaluated outcome;
- a synthetic sample mission;
- 24 bounded DISCOVER workflows and 24 capability-oriented SuperPowers;
- a Capabilities & Mastery page with evidence-linked progress;
- Basic, Intermediate, Advanced, and AI Agent Orchestration Master development levels;
- Personal Edition EDENA advisories and an Institutional policy-preview mode;
- local Markdown handoff generation for Hermes, with explicit human review;
- an embedded Guide plus standalone setup, privacy, security, rollback, and uninstall documentation;
- macOS, Windows, and Linux launchers; and
- an optional legacy research/innovation specialization in `base-pack/`.

## Data and accountability boundary

Do not enter or import:

- PHI or patient identifiers;
- participant-level research data;
- confidential institutional, personnel, academic, legal, financial, sponsor, peer-review, or invention information;
- passwords, API keys, access tokens, connection strings, or other secrets; or
- sensitive personal information that would be harmful if exposed.

The browser's `localStorage` is device- and browser-profile-specific but **not encrypted**. A saved mission and an exported backup may contain the text you enter. Session-only missions are intended to disappear after the browser session; they are not a substitute for an approved secure system.

AI supports but does not replace professional judgment. Hermes and Nurse AI OS do not hold a clinical license or assume professional accountability. Every clinical, legal, financial, employment, academic, research, or institutional output requires appropriate human verification and authorization before use.

## Multi-role architecture

The included role templates cover students and nursing assistants, staff nurses, advanced-practice clinicians, nurse educators, medical residents, nurse and clinic managers, hospital administrators, wellness managers, quality and safety contributors, researchers, informatics and responsible-AI leaders, entrepreneurs, community or family advocates, and advanced studies.

One person may select several roles under one Soul Profile. Each role keeps its own dashboard view and can own separate missions. Role labels are self-selected navigation aids. They do not prove identity, education, licensure, delegation, competence, employment, or authority.

## Discover Packet adapter

Mission Control accepts `NAIO-DISCOVER-PACKET-ADAPTER-1`, a strict, replaceable JSON configuration containing only derived non-sensitive settings. It can influence mission language, priority prompts, role goals, workflow order, capability recommendations, AI autonomy cues, EDENA defaults and retention defaults. Every change is previewed before it is applied. It cannot enable an agent, authorize a role, weaken a gate or verify an outcome. Raw interview notes and sensitive source material are prohibited.

The included `config/discover-packet-input.schema.json` and `examples/deidentified-discover-packet.json` support safe preparation and testing when the user’s completed packet is not yet available.

## Soul Profile status

The redesigned Nurse AI OS Soul Quiz is still evolving. Version 2.0.0 therefore uses a replaceable adapter: `NAIO-SOUL-PROFILE-ADAPTER-1`.

- Import only a derived, reviewed Soul Profile JSON.
- Preview the proposed theme and role recommendations before applying them.
- Do not import raw answers.
- Soul personalization may change colors, language, and recommendations.
- It cannot grant a role, change permissions, reduce EDENA safeguards, prove competence, or authorize action.
- The retained 12-question experience is a provisional demonstration, not a validated psychological, employment, educational, credentialing, or competence assessment.

## Mission and artifact lifecycle

Every mission uses a repeatable five-stage loop:

1. **Assess:** distinguish verified facts, user-provided information, assumptions, unresolved questions, constraints, resources, stakeholders, and sources.
2. **Define or Diagnose:** bound the problem, opportunity, or decision; identify causes, dependencies, risks, gaps, and competing interpretations.
3. **Plan:** compare options, define outcomes, milestones, owners, measures, safeguards, stop rules, and rollback.
4. **Implement:** prepare tasks, prompts, agents, checklists, and draft artifacts. The dashboard does not perform external action.
5. **Evaluate:** compare results with goals, record evidence and uncertainty, and choose to continue, modify, escalate, stop, or begin another iteration.

Artifact labels describe maturity, not approval by the software. An `approved_plan`, `authorized_execution`, or `completed_action` label is a user record and does not independently verify approval, authorization, or completion.

## EDENA behavior

- **Green:** bounded, reversible, low-consequence sandbox work.
- **Yellow:** deliberate fact, evidence, scope, destination, or intended-use verification is required.
- **Orange:** structured qualified-human review is required.
- **Red:** serious potential consequence, prohibited data/scope, or missing authority; sanitized exploration only in Personal Edition.
- **Unclassified:** remain in preview until the context is classified.

Personal Edition uses advisories, acknowledgment, and review gates. Institutional policy preview demonstrates more restrictive blocking, but it is not tamper-resistant or institutionally managed. An actual Institutional Edition must add institution-controlled policy, identity, authorization, audit, retention, access, and approval systems.

## Capabilities and badges

Progress is based on user-added, sanitized evidence such as evaluated missions, reviewed artifacts, measurements, feedback, reflections, safety drills, and governed agent records. Sample missions do not count as achievement evidence. Badges never unlock agents, permissions, data classes, or external actions.

All levels are developmental and noncredential:

1. Basic
2. Intermediate
3. Advanced
4. AI Agent Orchestration Master

They are not licensure, certification, continuing-education credit, institutional authorization, or proof of clinical competence.

## Honest Hermes integration

Mission Control has no hidden Hermes API or live synchronization. The normal handoff is:

1. Open a mission stage or workflow.
2. Keep the text non-sensitive.
3. Generate the local Markdown preview.
4. Review and acknowledge it.
5. Copy or download it.
6. Open Hermes separately and paste it into the correct Nurse AI OS workspace.
7. Review Hermes's response before using any artifact.

Copy or Download does not mean Sent or Executed. The optional integration installer may register a local launch link or Guide entry only when the installed Hermes version visibly supports it. Manual handoff only is a complete, supported result.

## Start locally

After unzipping, use one of these methods:

- macOS: double-click `Start-DISCOVER.command`;
- Windows: double-click `Start-DISCOVER.bat`;
- Linux: run `./start-discover.sh`; or
- portable fallback: open `index.html` directly.

The optional local server binds only to `127.0.0.1:43127`. It does not create an internet-facing service or a write API. Keep its terminal window open while using the dashboard and press `Control+C` to stop it.

## File map

```text
DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0/
├── README-FIRST.md
├── README.md
├── index.html
├── assets/
│   ├── app.js
│   └── styles.css
├── guide/
│   └── DISCOVER-Mission-Control-Setup-Guide.md
├── hermes/
│   ├── DISCOVER-Dashboard-Hermes-Integration-Installer.md
│   └── Hermes-Capability-State.md
├── config/                         # versioned policies and strict JSON schemas
├── examples/                       # synthetic, deidentified adapter examples
├── base-pack/                       # optional legacy research specialization
├── Start-DISCOVER.command
├── Start-DISCOVER.bat
├── start-discover.sh
├── server.mjs
├── PRIVACY.md
├── SECURITY.md
├── UNINSTALL.md
├── CHANGELOG.md
├── LICENSE.md
├── VERSION
├── RELEASE-MANIFEST.json
└── SHA256SUMS.txt
```

The release manifest and checksums describe the packaged release after the release builder completes. See the setup guide for verification, backup, update, rollback, and uninstall.

## Optional legacy DISCOVER research specialization

The material under `base-pack/` is the earlier `HRIL-AIOS-DISCOVER-COMPLETE-1.0` package for Healthcare Research & Innovation Leaders. Preserve it as an optional specialization. It is not the universal core, is not required for the multi-role Mission Control, and should not be installed into unrelated roles.

## Working-name notice

DISCOVER, Nurse AI OS, Hermes integration objects, EDENA, and capability labels are working product concepts in this package. No endorsement, certification, accreditation, licensure, institutional approval, or standards-body validation is implied.
