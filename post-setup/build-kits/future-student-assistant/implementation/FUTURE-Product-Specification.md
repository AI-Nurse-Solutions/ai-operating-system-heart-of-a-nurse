# FUTURE Nursing Student & Nursing Assistant Mission Control — Product Specification

## Product identity

- Name: `FUTURE — Nursing Student & Nursing Assistant Mission Control`
- Target product ID: `future-nursing-student-assistant-mission-control`
- Target application version: `2.0.0`
- Canonical source program: `NAIO-FUTURE-COMPLETE-1.0`
- Foundation: `NAIO-FUTURE-CORE-1.0`
- Expansion: `NAIO-FUTURE-SP-1.0`
- Build-layer lane: `nursing_student_assistant`
- Build-layer canonical dashboard: `/nursing-students-assistants/dashboard`
- Namespace: `future.*`
- Home: `FUTURE Mission Control`
- Default mode: Private learner OS; synthetic demonstration; no PHI; session-only; Preview first
- Distribution target: versioned local full-stack ZIP bound to loopback with tested launchers

The lane, route, home, schema, agent, permission, and `FUT-*` identifiers are implementation decisions in this build contract; they were not present in the legacy text. No global route may collide with another Nurse AI OS role lane. A parent Mission Control may receive only product/version, coarse state, and an approved deep link—not learner records, values, goals, school/work context, memory, agent traces, or badge evidence.

## Purpose

FUTURE gives nursing students and nursing assistants a governed workspace for learning, life planning, work growth, career transition, safe technology practice, professional identity, community contribution, and iterative problem solving. It is designed to increase independent capability, judgment, source literacy, integrity, help-seeking, and recovery—not output volume or dependence on AI.

It is not a clinical system, school LMS, exam service, employer system, HR file, EHR, charting tool, competency validator, financial adviser, credential, certification, license, or substitute for faculty, a preceptor, a supervising nurse, a supervisor, institutional policy, or emergency services.

## Pathways and protected contexts

First run requires an explicit choice; Hermes may not infer it from a title:

- **Nursing Student:** coursework, approved practice, fictional simulation, exam preparation, professional identity, and education-to-career development, under current faculty/program/clinical-site/assessment rules.
- **Nursing Assistant:** role knowledge, approved certification review, professional communication, career development, and work-life capacity, under verified local scope, delegation, supervision, and employer policy.
- **Bridge:** both roles with school and employment partitions kept separate. Switching active context is explicit; data and authority never transfer silently.

Within each pathway, maintain four protected spaces: Learning; Work growth; Life; Community/future. Academic, clinical-placement, employment, personal, and public/community contexts are distinct partitions. One mission has exactly one active pathway, space, context, accountable human, and data ceiling.

## Operating core

### Core Four

1. Plan My Next Move
2. Learn & Practice
3. Check It with SAFE AI
4. Build My Future

The fifth pinned position starts and remains empty until the learner separately previews and approves one optional power. No more than five primary launchers may be pinned.

### FUTURE Library

Expose exactly 18 canonical numbered SuperPowers, 18 paired guided recipes, and 5 reusable cards. The catalog may use `FUT-PWR-01…18`, `FUT-WF-01…18`, and `FUT-TPL-01…05` as stable build-layer keys, always displayed with and mapped one-to-one to the exact canonical names. Every power begins `Available Inactive`; every workflow begins `Preview Only`.

One-run activation requires purpose, pathway/context, learner attempt, approved inputs, prohibited inputs, sources, EDENA result, responsible human, memory mode, external-action Off, limits, success/burden/independence measures, stop/fallback/removal plan, expiry, and exact approval. Preview or pinning is not activation. A power returns to Inactive when the run ends or expires.

## Mission loop

Every mission is durable, revisable, and repeatable:

1. **Assess:** separate verified fact, learner-provided information, source-backed explanation, assumption, and unknown; collect minimum context and applicable rules.
2. **Diagnose/Define:** frame the learning need, problem, opportunity, or decision; explore causes, constraints, dependencies, competing interpretations, and knowledge gaps without clinical diagnosis.
3. **Plan:** compare options by learner effort, feasibility, time, cost, benefit, burden, accessibility, ethics, authority, reversibility, and fit with values; set measures and review gates.
4. **Implement:** create learner-owned tasks, practice, drafts, rehearsals, prototypes, checklists, or questions. Consequential or external steps remain human handoffs.
5. **Evaluate:** compare results with measures; record what worked, failed, remains uncertain, and what to retain, revise, pause, stop, escalate, or send into a new Assess cycle.

A material upstream revision invalidates dependent approvals and returns affected workflows to Preview. Users can pause, reopen, branch, archive, restore, export, and delete without AI.

## Guided-learning contract

- Ask only the minimum needed; `Skip`, `Not now`, `Use this session only`, `Show an example`, and `Ask a human` are always available.
- Require an attempt or retrieval before a full answer when learning or assessed work is involved.
- Use Explain → Coach → Rehearse → Create → Teach back → Reflect.
- Preserve the learner's voice, reasoning, uncertainty, edits, and disclosure.
- Make applicable school/employer rules and the accountable human visible.
- Prefer minimum, recovery, and re-entry plans over shame, streaks, rankings, or pressure.

## Mission Control information architecture

- **Home:** pathway, active context, North Star, current season, capacity, privacy/edition banner, Hermes state, Core Four, Top Three, minimum step, re-entry, maximum-seven attention queue, and first-run checklist.
- **Missions & Projects:** complete loop, tasks, milestones, notes, measures, reviews, artifacts, decisions, sources, history, search/filter/sort, archive/restore/delete.
- **Learning & Practice:** targets, retrieval, misconceptions, teach-back, approved generic/fictional rehearsal, human questions, and academic-integrity receipt.
- **FUTURE Library:** 18 power previews, one-run cards, 18 workflows, and 5 templates.
- **Evidence Center:** source identity, author/authority, date/status, scope/applicability, claim mapping, conflict, correction/retraction, freshness, uncertainty, reviewer, and expiry.
- **SAFE AI Lab:** Situation, Aim, Facts, Expectations; prompt-risk classification; model-output verification; disclosure and learner-next-action controls.
- **Capabilities & Mastery:** four-level evidence badges plus the separate canonical AI Literacy Passport.
- **Career & Community:** truthful portfolio, opportunities, mentorship, networking, leadership rehearsal, service, and future-of-nursing exploration.
- **Agent Console:** selected agent, routing reason, P0/one-run permission, data/context ceiling, tools, events, approvals, limits, Stop/Kill, and receipt.
- **Guide:** the full supplied page plus contextual help and first-run walkthrough.
- **Settings & Recovery:** profile, contexts, rules, privacy, memory, export/import, backup/restore, Pause All, Safe Reset, overlay removal, rollback, and uninstall.

Every element styled as a control must work or be disabled with an exact reason. Status meaning cannot rely on color alone.

## Sandboxed states

Persist and display these distinctly: Exploration; Simulation; Recommendation; Draft artifact; Approved plan; Authorized execution; Completed action; Evaluated outcome. In this target, real external execution is absent. “Authorized execution” may only describe an explicitly human-owned local/manual step and may never imply the app sent, submitted, purchased, posted, charted, scheduled, or changed an official system.

## AI Literacy Passport and evidence badges

Preserve the canonical Passport domains: privacy/data judgment; SAFE prompting; source verification; fairness/integrity; human authority/escalation; workflow design/recovery. Preserve stages Explorer, Safe User, Verified Creator, Workflow Builder, and Future Steward. They are developmental—not credentials or competence determinations.

Alongside the Passport, implement Basic, Intermediate, Advanced, and AI Agent Orchestration Master across the build contract's activity domains. Awards require eligible, auditable, nonsynthetic mission evidence and human review where appropriate. Clicking, opening, previewing, asking AI, completing a synthetic Starter, or AI self-scoring never awards a badge. Deletion or correction recalculates progress.

## Data, authority, and action invariants

Default permitted content is public, synthetic, or learner-authored nonsensitive information after screening. Reject PHI and identifiable clinical narratives before persistence and do not echo them into logs, errors, receipts, exports, memory, or analytics. Also reject live-care requests, chart material, exams/prohibited assessments, fabricated hours/skills/citations/credentials/reflections/signatures, restricted student/employee/discipline/accommodation/investigation/peer-review/incident/security data, secrets, unnecessary identifiers, and financial credentials.

The system never decides diagnosis, treatment, medication administration, device settings, care plans, assignment, delegation, scope, competency, grades, certification, employment, discipline, eligibility, or financial outcomes. No connector, send, submit, post, share, schedule, purchase, sign, apply, chart, or official-system write exists in this target. Personal EDENA advisories and Institutional enforcement may add review or stronger stops; neither can override absolute prohibitions or create authority.

## Offline and connected truth

Without AI, all records, state changes, starter controls, search, evidence capture, Guide, badge calculations, backup/export/import/restore/delete, and diagnostics remain useful. AI controls show one of the verified states: Connected, Connecting, Setup required, Offline, Authentication failed, Hermes unavailable, Provider unavailable, Limited capabilities, or Reconnecting. A timer, configured URL, page load, or cached result does not prove Connected.

## Success condition

A nondeveloper can install the final release; choose a pathway and safe contexts; approve a derived profile; start a useful synthetic dashboard; complete, save, restart, resume, evaluate, reopen, export, restore, and delete a mission without AI; understand why every control is enabled or blocked; verify sources and AI disclosures; supervise a bounded agent; and recover or uninstall. Operational status additionally requires a genuine configured Hermes response streamed through the packaged UI, cancellation, session behavior, and all applicable acceptance evidence.
