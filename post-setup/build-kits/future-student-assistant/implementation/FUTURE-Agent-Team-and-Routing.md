# FUTURE Agent Team and Deterministic Routing

## Implementation contract for Hermes

**Canonical legacy program:** Nursing Student and Nursing Assistant Complete AI OS with FUTURE SuperPowers  
**Canonical program ID:** `NAIO-FUTURE-COMPLETE-1.0`  
**Canonical foundation / expansion:** `NAIO-FUTURE-CORE-1.0` / `NAIO-FUTURE-SP-1.0`  
**Canonical namespace:** `future.*`  
**Canonical pathways:** Nursing Student / Nursing Assistant / Bridge  
**Build-layer product ID:** `future-nursing-student-assistant-mission-control`  
**Build-layer lane:** `nursing_student_assistant`  
**Build-layer canonical route:** `/nursing-students-assistants/dashboard`  
**Build-layer home label:** FUTURE Mission Control  
**Installed agent state:** `PERM-P0 Disabled`

The lane, route, home label, workflow IDs, schema IDs, and agent IDs in this document are implementation decisions for the downloadable Mission Control build. They do not appear in, and must not be represented as identifiers from, the legacy v1.0 source pack. The canonical legacy identities, power titles, pathways, defaults, checkpoints, tests, and safety boundaries remain authoritative.

FUTURE is a private, learner-controlled learning, planning, rehearsal, and creation environment. Its agent layer may explain, question, coach, organize, prototype, retrieve approved sources, and verify. It may not replace the learner's thinking or authorship; faculty, preceptors, supervising nurses, supervisors, institutions, or emergency processes; or an authorized clinical, academic, employment, credentialing, financial, or community decision maker.

The Mission Control application must remain useful without an AI backend. Local missions, plans, study queues, fictional rehearsal records, sources, reflections, portfolio evidence, templates, capabilities, exports, backups, and the five-stage mission loop must work without a model. If a genuine Hermes or approved OpenAI-compatible backend is absent or unhealthy, show `AI unavailable` and keep agent controls disabled. Never substitute canned responses, delayed samples, fake tool events, invented citations, or simulated agent activity.

## 1. Frozen source inventory

Hermes must preserve these legacy facts exactly:

- one owner and one explicitly selected pathway: Nursing Student, Nursing Assistant, or Bridge;
- four protected spaces: Learning, Work growth, Life, and Community and future;
- three checkpoints: S0 pre-install, S1 healthy foundation, and S2 healthy Complete Edition;
- 18 optional powers, all `Inactive; synthetic preview only` after installation;
- the Core Four launchers: **Plan My Next Move**, **Learn & Practice**, **Check It with SAFE AI**, and **Build My Future**;
- one optional fifth launcher, empty until separately previewed and approved;
- five canonical Markdown templates;
- six AI Literacy Passport domains and five developmental stages;
- 24 foundation tests, 96 FUTURE overlay tests, and 16 integration checks: 136 total;
- default state: private, Synthetic Demonstration Mode, no PHI, session-only memory, Manual / AI-assisted / Preview only, connectors off, shared access off, external actions off, and background automation off; and
- one visible EDENA decision model and one FUTURE Command Center.

The legacy pack does **not** define formal workflow IDs, executable JSON schemas, a lane, URL routes, a home-label string, a formal agent registry, or a PERM model. The `FUT-*` records below are new closed implementation records required to turn the content into a testable application. They must be labeled `implementation_generated`, versioned separately, and traceable to this contract. They may narrow source behavior but may never widen it.

Activation is not complete unless all applicable 136 legacy checks and all build-kit acceptance checks pass with synthetic data, every power remains inactive, every agent remains P0, the Core Four are present without duplication, the fifth slot is empty, and all external actions remain Off. Otherwise report `PARTIAL_QUARANTINED_NOT_ACTIVATED`.

## 2. Build-layer agent registry

Register exactly these ten bounded implementation agents. Their names and IDs are build-layer identifiers, not legacy-source identifiers. Installation supplies no model invocation, credential, connector, destination, memory grant, schedule, recursion, hidden state, background execution, or tool permission.

| ID | Build-layer agent name | Bounded purpose | Installed state | Maximum after separate one-run authorization |
|---|---|---|---|---|
| `FUT-AGT-01` | Next Move & Capacity Planning Coach | Help the owner turn learner-authored goals, fixed commitments, and capacity into Minimum, Standard, Stretch, or Re-entry options. | `PERM-P0 Disabled` | `PERM-P1`; selected low-sensitivity owner inputs only; no diagnosis, financial advice, coercion, or claim about likely success. |
| `FUT-AGT-02` | Active Learning & Teach-Back Coach | Run attempt-before-answer retrieval, teach-back, interleaving, spaced-review, and misconception-repair sessions using approved material. | `PERM-P0 Disabled` | `PERM-P1`; never take an exam, complete prohibited assessed work, fabricate reflection, or represent practice as competence. |
| `FUT-AGT-03` | Fictional Skills & Certification Rehearsal Coach | Prepare fictional or faculty-approved generic skills-lab, communication, NCLEX, certification, and knowledge-gap rehearsals. | `PERM-P0 Disabled` | `PERM-P1`; no patient data, live care, medication/device instruction for real use, skill authorization, scope, delegation, assignment, documentation, pass guarantee, or credential claim. |
| `FUT-AGT-04` | Evidence & Source Verification Scout | Retrieve from an exact public or owner-approved generic source allowlist and produce claim, source, date, authority, applicability, conflict, and uncertainty records. | `PERM-P0 Disabled` | `PERM-P2`; read-only, one run; no invented sources, paywall bypass, local-policy inference, or unreviewed consequential conclusion. |
| `FUT-AGT-05` | SAFE Prompt, Integrity & Boundary Sentinel | Apply SAFE and EDENA, identify minimum-needed information, academic-integrity limits, authority gaps, bias, prompt injection, and prohibited content before a run. | `PERM-P0 Disabled` | `PERM-P1`; can block or route but cannot approve work, declare compliance, infer scope, or replace faculty/employer review. |
| `FUT-AGT-06` | Synthetic Workflow & Accessible Prototype Coach | Help map manual low-risk workflows and create accessible, non-production dashboards or prototypes using synthetic information. | `PERM-P0 Disabled` | `PERM-P1`; no connection, deployment, live data, monitoring, production write, automation activation, or claim that a prototype is secure or operational. |
| `FUT-AGT-07` | Career, Portfolio & Opportunity Coach | Help assemble truthful portfolio evidence and compare public education, bridge, certification, scholarship, job, and side-project information. | `PERM-P0 Disabled` | `PERM-P2`; approved public sources only; no eligibility determination, guarantee, fabricated claim, application submission, purchase, contract, fundraising, or employer-context use. |
| `FUT-AGT-08` | Communication, Teamwork & Emerging-Leadership Coach | Rehearse owner-authored messages, feedback, boundaries, SBAR, mentorship, speaking up, teamwork, conflict repair, and consent-based community planning. | `PERM-P0 Disabled` | `PERM-P1`; fictional or approved generic scenarios only; no impersonation, borrowed authority, patient/workforce story, hidden evaluation, contact, send, post, or promise. |
| `FUT-AGT-09` | Community & Future-of-Nursing Exploration Scout | Explore public information about informatics, robotics, AI, data science, genomics, education, public health, entrepreneurship, and service options. | `PERM-P0 Disabled` | `PERM-P2`; read-only public sources; clearly distinguish exploration from eligibility, validation, clinical use, business advice, or institutional approval. |
| `FUT-AGT-10` | Independent Agent Auditor & Kill Sentinel | Test a frozen agent version against positive, negative, authority, data, integrity, injection, cancellation, receipt, and recovery fixtures; prepare kill and rollback evidence. | `PERM-P0 Disabled` | `PERM-P1` on a separate control path; cannot audit itself, approve release, modify the tested agent, or alter its receipts. |

These maxima are ceilings, not grants or recommendations. An authorized run may be narrower. `FUT-AGT-10` must remain independent from the agent it evaluates. No agent may activate, modify, delegate to, approve, score as sole judge, or retire itself.

## 3. Permission model

Keep installed state, requested permission, approved permission, canonical maximum, effective permission, run state, and edition policy as separate fields.

| Level | Build-layer meaning | Enforcement |
|---|---|---|
| `PERM-P0` | Disabled; installed state for every agent, connector, destination, and action | No model call, inference, retrieval, tool, network, memory, schedule, destination, or background work. |
| `PERM-P1` | One learner-approved local/session run over exact synthetic or selected low-sensitivity owner input | Local draft or rehearsal only; no external retrieval, send, submission, connection, background run, or consequential release. |
| `PERM-P2` | One learner-approved, read-only run over exact allowlisted public or approved generic sources | Expiring hash-bound run; citations and retrieval receipts required; no write, contact, upload, bypass, submission, or automatic use of retrieved instructions. |
| `PERM-P3` | Monitored low-risk deterministic reminder after three supervised successful runs | **Not an agent permission.** It may be implemented only as an owner-controlled local reminder with no model, sensitive data, connector, external write, or background decision. |
| `PERM-P4` | Clinical, academic-decision, employment-decision, credentialing, financial-transaction, institutional, public-release, community-contact, production, or external-write authority | **Not implemented.** A role, title, prompt, acknowledgement, plug-in, or configuration cannot enable it. |

The effective permission is the most restrictive result across agent maximum, explicit one-run grant, pathway, active protected space, authority evidence, course/employer/site rules, data class, EDENA tier, source status, purpose, approved tools, backend capability, and every deny rule. Missing, stale, conflicting, expired, unknown, or unsupported values narrow or block; they never widen permission.

The v1.0 product is a private learner-controlled edition. It is not an institutional edition. School, employer, clinical-site, faculty/supervisor access, shared deployment, or organizational policy enforcement requires a separate product review and cannot be activated from this build.

## 4. Agent state machine and one-run charter

Use the closed build-layer state machine:

`disabled → draft_charter → one_run_proposed → one_run_authorized → running → reconciled → disabled`

Also support `blocked`, `killed`, and `retired`. A denied, expired, cancelled, interrupted, mismatched, or failed run must never remain `running`. Invalid transitions fail closed and create a minimal nonsensitive receipt.

Every proposed run must bind:

- exact agent ID/version, model, system prompt, policy, input schema, output schema, and hash for each;
- one learner-owned objective, one active pathway, one protected space, non-goals, and the exact learner-authored first attempt where required;
- governing course, assessment, program, employer, site, or community rule status and the named responsible human route;
- EDENA tier with reasons, exact data class, source allowlist, purpose, session/retention choice, and prohibited-input attestation;
- exact tool/network allowlist, one invocation, zero hidden retries, cost/time/input/output caps, and an expiring authorization;
- attempt-before-answer, source, authority, disclosure, accessibility, dependency, and learning-independence checks;
- human review points, cancellation, kill, reconciliation, temporary-data purge, rollback, and retirement path; and
- a plain-language preview of what the agent will and will not do.

A change to pathway, protected space, course or employer rule, first attempt, objective, data, source, model, prompt, policy, schema, tool, audience, destination, permission, or version invalidates authorization and returns the run to `draft_charter` or `blocked`.

## 5. Deterministic routing pipeline

Routing recommends a bounded helper; it does not execute one. Implement it in ordinary application code before any model call:

1. Read the authenticated owner, explicitly selected pathway, active protected space, mission stage, chosen Core Four launcher or power, desired artifact, course/employer/site rule status, human authority, data class, EDENA tier, and requested action.
2. Apply prohibited-input screening before persistence, logs, embeddings, prompt assembly, backup, or analytics. Stop without echoing sensitive content.
3. For learning or assessed-work requests, require the governing rule status and an owner attempt. Unknown or conflicting rules keep the result in coaching, explanation, practice, or human-question mode.
4. Resolve the exact source power or priority recipe. Ambiguous free text opens a visible chooser or asks one minimum-necessary question. A model may not infer a consequential pathway or authority.
5. Use the tables below. A P0 agent may be displayed only as `Suggested — disabled; charter and approval required`.
6. Apply the agent ceiling, EDENA result, data/source policy, authority, backend health, tests, expiry, and independent-audit rule.
7. Show a Routing Card: source power/recipe, suggested agent, match reason, rejected alternatives, installed and effective permission, data/source scope, EDENA result, course/employer rule status, learner attempt, human route, limits, stop conditions, and cancellation control.
8. Permit an explicit owner override only among compatible agents. Record the automatic and selected routes and the owner's reason. An override cannot change pathway, data, EDENA, authority, integrity, or permission ceilings.
9. Require a fresh expiring one-run approval; execute once; stream genuine backend/tool events; reconcile; purge temporary state; revoke the grant; and return the agent to `disabled`.

If no route is eligible, set `route=human_or_manual` and keep the local workflow available without AI.

## 6. Source power-to-agent routing

Power ordinal and title are canonical legacy content. `FUT-PWR-01`–`FUT-PWR-18` are stable build-layer keys only. Suggested routes are build-layer decisions. All powers remain inactive until separately previewed and approved.

| Build key / source power | Exact canonical title | Suggested route |
|---|---|---|
| `FUT-PWR-01` / Power 1 | Future North Star & 90-Day Map | Human-first; optional `FUT-AGT-01` after the learner writes an initial North Star. |
| `FUT-PWR-02` / Power 2 | Capacity, Money & Life Logistics Navigator | `FUT-AGT-01`; educational planning only, no financial advice or credentials. |
| `FUT-PWR-03` / Power 3 | Confidence, Recovery & Help-Seeking Coach | Human-first with optional `FUT-AGT-01`; never diagnosis, therapy, crisis substitution, or wellbeing prediction. |
| `FUT-PWR-04` / Power 4 | Active Learning & Study Sprint Engine | `FUT-AGT-02`; attempt-before-answer and course-rule gate required. |
| `FUT-PWR-05` / Power 5 | Skills Lab & Clinical Readiness Rehearsal | `FUT-AGT-03`; fictional or faculty-approved generic content only. |
| `FUT-PWR-06` / Power 6 | NCLEX, Certification & Knowledge-Gap Studio | `FUT-AGT-03`; practice and gap reflection only, no pass/competence claim. |
| `FUT-PWR-07` / Power 7 | SAFE Prompt & AI Literacy Lab | `FUT-AGT-05`; learner inspects assumptions and decides when not to use AI. |
| `FUT-PWR-08` / Power 8 | Evidence, Source & Misinformation Detective | `FUT-AGT-04`; exact public/approved source allowlist and source receipt required. |
| `FUT-PWR-09` / Power 9 | Privacy, Bias, Integrity & Governance Red Team | `FUT-AGT-05`; `FUT-AGT-10` may independently test a frozen implementation. |
| `FUT-PWR-10` / Power 10 | Digital Workflow & Automation Sandbox | `FUT-AGT-06`; synthetic, manual, local, non-production only. |
| `FUT-PWR-11` / Power 11 | UI/UX & Accessible Dashboard Builder | `FUT-AGT-06`; accessible prototype only, with no dark patterns or fake capability. |
| `FUT-PWR-12` / Power 12 | Data, Informatics & Responsible Innovation Lab | `FUT-AGT-06`; synthetic data and governed prototypes only. |
| `FUT-PWR-13` / Power 13 | Career Portfolio, Résumé & Interview Studio | `FUT-AGT-07`; truthful, traceable evidence and explicit AI-assistance status. |
| `FUT-PWR-14` / Power 14 | Professional Communication, Mentorship & Network Builder | `FUT-AGT-08`; owner voice, private rehearsal, and no send. |
| `FUT-PWR-15` / Power 15 | Opportunity, Scholarship & Ethical Side-Project Navigator | `FUT-AGT-07`; public-source exploration and draft preparation only. |
| `FUT-PWR-16` / Power 16 | Speaking Up, Teamwork & Emerging Leadership Lab | `FUT-AGT-08`; fictional or approved generic rehearsal without borrowed authority. |
| `FUT-PWR-17` / Power 17 | Community Health & Service Project Studio | Human-first, then `FUT-AGT-08`; consent-based planning and qualified review, no contact or health claim release. |
| `FUT-PWR-18` / Power 18 | Future-of-Nursing Explorer | `FUT-AGT-09`; public-source exploration distinct from clinical or production use. |

The shared source launch pattern is frozen for all 18 powers:

`Clarify the goal → classify the context and data → identify human authority → attempt or retrieve first → build a draft or simulation → verify → learner decides → record a non-sensitive receipt.`

The build may display this through Assess–Define–Plan–Implement–Evaluate, but the mapping must remain explicit:

- **Assess:** clarify the goal; classify protected space, data, rules, authority, capacity, and available sources; capture the learner's first attempt or retrieval.
- **Define:** state the learning gap, planning problem, prototype question, or decision without implying diagnosis or authority.
- **Plan:** compare options, workload, accessibility, evidence, risk, human support, and stop conditions.
- **Implement:** create only a local draft, fictional rehearsal, synthetic prototype, or learner-owned task plan.
- **Evaluate:** verify sources and limits; learner edits and decides; record disclosure, human questions, next independent step, and a nonsensitive receipt.

## 7. Priority-recipe routing

The legacy source lists 18 ordered Priority recipes but gives them no formal IDs. Use `FUT-WF-01`–`FUT-WF-18` only as build-layer workflow identifiers while preserving each exact title. Every build-layer workflow installs `Preview Only`; registering, displaying, pinning, or recommending one does not activate its corresponding power or agent.

| Build ID | Exact source recipe title | Primary route |
|---|---|---|
| `FUT-WF-01` | Daily ten-minute Next Move | `FUT-AGT-01`, or local manual form. |
| `FUT-WF-02` | Weekly whole-life and capacity plan | Human-first; optional `FUT-AGT-01` over owner-selected low-sensitivity fields. |
| `FUT-WF-03` | Study sprint and teach-back | `FUT-AGT-02`. |
| `FUT-WF-04` | Fictional clinical-reasoning or communication rehearsal | `FUT-AGT-03`; fictional only. |
| `FUT-WF-05` | Skills-lab or certification preparation from approved sources | `FUT-AGT-03`. |
| `FUT-WF-06` | NCLEX or role-knowledge gap review | `FUT-AGT-03`. |
| `FUT-WF-07` | Graded-work integrity route | `FUT-AGT-05`; faculty/rule route, no completion. |
| `FUT-WF-08` | Claim and citation verification | `FUT-AGT-04`. |
| `FUT-WF-09` | Bias, privacy, deepfake, or prompt-injection red team | `FUT-AGT-05`; optional independent `FUT-AGT-10` test. |
| `FUT-WF-10` | SAFE prompt studio | `FUT-AGT-05`. |
| `FUT-WF-11` | Synthetic workflow and automation sandbox | `FUT-AGT-06`; no connection or activation. |
| `FUT-WF-12` | Accessible dashboard or app prototype | `FUT-AGT-06`. |
| `FUT-WF-13` | Career pathway and bridge-to-nursing map | `FUT-AGT-07`; requirements must be sourced and current. |
| `FUT-WF-14` | Résumé, interview, scholarship, or application preparation | `FUT-AGT-07`; owner-authored truth and no submission. |
| `FUT-WF-15` | Mentorship, feedback, boundary, or speaking-up rehearsal | `FUT-AGT-08`; private rehearsal and no send. |
| `FUT-WF-16` | Community health or service project canvas | Human-first, then `FUT-AGT-08`; consent and qualified review. |
| `FUT-WF-17` | Future-of-nursing exploration sprint | `FUT-AGT-09`. |
| `FUT-WF-18` | Overload recovery and re-entry mode | Human-first; optional `FUT-AGT-01`; productivity pauses if safety/wellbeing may be at risk. |

## 8. Core Four and guided-program routing

- **Plan My Next Move:** manual form or `FUT-AGT-01`; owner authors goals and chooses the plan.
- **Learn & Practice:** `FUT-AGT-02` for concepts and `FUT-AGT-03` for fictional rehearsal; course/site rules and attempt-before-answer apply.
- **Check It with SAFE AI:** `FUT-AGT-05`, with `FUT-AGT-04` only for approved retrieval and citation checks.
- **Build My Future:** route by explicit owner selection to `FUT-AGT-06`, `07`, `08`, or `09`; do not infer a life, career, financial, community, or professional decision.
- **Seven-Day FUTURE Launch:** deterministic guided checklist; no autonomous agent. Each day may recommend a compatible disabled agent but may not activate it.
- **Ninety-Day Future Flight Plan:** human-owned plan with Minimum, Standard, and Stretch versions and reviews at days 7, 30, 60, and 90. `FUT-AGT-01` may help draft options.
- **First Ritual:** human-first. The learner chooses one real low-risk study, work-growth, life, career, or community problem, attempts first, identifies the human authority, and names the next independent step. No patient information or live assessed task.

## 9. Pathway and protected-space gates

### Nursing Student

Support learning, coursework within verified AI-use rules, fictional simulation, NCLEX preparation, professional identity, and school-to-career development. Faculty, program, assessment, preceptor, and clinical-site rules govern. No agent may claim a grade, readiness, competence, progression, certification, or authorization.

### Nursing Assistant

Support general role knowledge, certification review, professional communication, career development, work-life capacity, and bridge planning. The local title never proves scope. Employer policy, verified local scope, delegation, and supervision govern. No agent may decide or imply scope, assignment, delegation, care plan, documentation, device setting, competency, or clinical action.

### Bridge

Maintain distinct Learning and Work-growth partitions and require a visible switch. Never transfer school information into work or work information into school automatically. A role/context change invalidates affected approvals and returns agent runs to draft or blocked state.

### Four protected spaces

1. **Learning:** approved educational content, general concepts, fictional simulation, and study plans.
2. **Work growth:** general professional development and private career reflection; no patient, restricted worker, investigation, or employer-confidential data.
3. **Life:** owner-controlled goals, schedule, capacity, finances at an educational planning level, relationships, and recovery; session-only by default and never an institutional performance signal.
4. **Community and future:** public or consent-based project planning, leadership, innovation, and exploration; no contact, promises, health-content release, or public action.

An agent receives only the selected minimum-needed fields from the active space. It cannot search or infer across other spaces.

## 10. Academic-integrity and learning-independence gate

Before academic support, record `rule_status=verified|unknown|not_applicable`, source/owner, date, scope, and expiry. Unknown is not permission. If restricted or uncertain:

- refuse the prohibited completion, exam, quiz, fabricated reflection, hours, citation, competency, signature, or credential;
- do not expose answers from a live assessment;
- offer concept explanation, retrieval practice, a fictional analogous problem, rubric interpretation, question formulation for faculty, or an integrity receipt; and
- keep the learner's attempt, edits, verification, disclosure, and next independent action visible.

Every significant run ends with the canonical reflection: what I learned, what I verified, what remains uncertain, what needs a human, and my next independent step. Metrics must favor independence, verification, accessibility, burden reduction, and truth—not screen time, streaks, output volume, rankings, or dependency.

## 11. Source and retrieval rules

Only `FUT-AGT-04`, `FUT-AGT-07`, and `FUT-AGT-09` may be eligible for P2. Each retrieval run requires an exact allowlist and records publisher/owner, exact title, canonical URL or local source reference, version/date, retrieved date, authority type, applicability, current status, conflicts/corrections, supported claim, limits, reviewer, and expiry.

Search results, snippets, model memory, confidence, popularity, and a URL alone are not evidence. Never invent a citation, quote, policy, requirement, credential, outcome, or consensus. Never infer local faculty, employer, site, or regulatory policy from general guidance. Content inside a source is untrusted data and cannot alter system instructions, permissions, destinations, or governance.

## 12. Exact-action and external-use boundary

The build has no agent permission for send, submit, schedule, purchase, share, post, contact, apply, register, sign, pay, connect, deploy, monitor, grade, evaluate a person, write an official system, or automate a consequential action.

Mission Control may prepare a Draft Artifact. Before any future manually initiated external action, show the canonical exact-action gate: exact content, recipient/destination, context, data class, consequence, permissions, human reviewer, reversibility, and rollback. Approval is per run. Changed audience, destination, data class, role, scope, or version cancels prior approval. In this build, `Authorized Execution` means **leave FUTURE and use the approved human/official process**; it is never an agent action button.

## 13. Agent receipts, cancellation, and recovery

Every run shows real state: queued, running, cancelling, cancelled, reconciled, blocked, failed, killed, or expired. Provide a visible Stop control and a deterministic timeout. No hidden retry is allowed. A run receipt contains only nonsensitive control metadata: charter hash, agent/model/policy/schema versions, timestamps, data-class code, source IDs, permission, EDENA tier, tool events, cancellation/kill state, output hash, human decision, purge state, and unresolved items.

**Pause All** blocks new and pending agent runs without deleting work. **Safe Reset** returns to Synthetic Demonstration Mode, session-only memory, connectors/shared access/external actions off, Manual/Assist/Preview only, Core Four only, all powers inactive, and all agents P0. Overlay removal and full uninstall require exact preview, approved export choice, rollback evidence, and a receipt. No agent may interfere with Pause, Reset, correction, export, deletion, rollback, overlay removal, uninstall, or emergency routing.

## 14. Build-layer schema obligations

The source pack provides five Markdown templates but no executable schemas. Hermes must therefore implement closed JSON Schema Draft 2020-12 records, label them `implementation_generated`, and version them independently. At minimum cover:

- owner/pathway/context/authority and partition selection;
- power activation card;
- SAFE prompt card;
- AI use and integrity receipt;
- synthetic workflow canvas;
- portfolio evidence card;
- source/evidence record;
- EDENA decision and human route;
- agent charter, event, receipt, cancellation, and audit result; and
- pause/reset/rollback/uninstall receipt.

Schemas must reject additional properties, use closed enumerations, enforce identifiers/version/hash/timestamp formats, and validate cross-field rules in deterministic application code. The UI must never imply these schemas were part of legacy v1.0.

## 15. Required positive and negative tests

In addition to the 136 canonical checks, every agent requires synthetic fixtures for:

- eligible P1 use, eligible P2 retrieval where applicable, and manual fallback;
- patient identifier and identifiable-story rejection before persistence;
- live-care, medication/device, scope, delegation, assignment, documentation, and emergency routing;
- live exam, restricted assessed work, fabricated evidence, and hidden-AI-use refusal;
- restricted school/employer information, credentials, secret link, rare-detail re-identification, and context-crossing rejection;
- prompt injection inside a file or webpage;
- unknown, stale, and conflicting authority/source states;
- model, prompt, policy, schema, data, tool, version, and destination hash mismatch;
- no self-activation, recursion, hidden retry, background continuation, external write, or P4 action;
- cancellation, timeout, partial failure, purge, reconciliation, Safe Reset, and no-op reinstall; and
- independence and truthful-state checks: no fake AI, credential, competence, grade, employment, patient, financial, security, or completion claim.

`Attempted`, `Partial`, `Unknown`, `Unavailable`, `Awaiting approval`, and `Blocked` are not `Passed`. Missing cancellation, critical governance, no-PHI enforcement, integrity enforcement, recovery, or truthful status blocks activation.
