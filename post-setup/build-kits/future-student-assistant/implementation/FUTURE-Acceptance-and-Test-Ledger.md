# FUTURE Acceptance and Test Ledger

## Release-evidence contract

**Product:** FUTURE — Nursing Student & Nursing Assistant Mission Control  
**Target version:** 2.0.0  
**Product ID:** `future-nursing-student-assistant-mission-control`  
**Population lane:** `nursing_student_assistant`  
**Canonical corpus:** `NAIO-FUTURE-COMPLETE-1.0`  
**Default state of every test in this ledger:** **Not Run**

This ledger is an execution contract, not proof. Hermes must carry it into the built application, execute the packaged production path, attach independently reviewable evidence and update results without weakening expected behavior. The source packet and build kit are not the operational application.

Until executed evidence supports a narrower decision, report:

> **Not operational:** One or more core acceptance criteria failed or has not been run; blockers are documented in this ledger.

A specification, code comment, static match, screenshot, synthetic AI transcript, model assertion or previous-release result is not runtime proof.

## 1. Allowed result states

| Result | Meaning | Counts as passed? |
|---|---|---|
| Not Run | No valid execution evidence exists for this exact build/environment. | No |
| Running | Execution began but has no final result. | No |
| Passed | Packaged production path ran and matched the expected result with evidence. | Yes |
| Failed | Observed behavior differed from expected. | No |
| Blocked | A prerequisite authorization, environment or dependency prevented execution. | No |
| Unsupported | The release or environment cannot perform a required check. | No |
| Not Applicable | Genuinely inapplicable to the declared target with approved rationale and no hidden loss of promised behavior. | Only with release-owner approval |

Do not substitute Implemented, Specified, Expected, Looks correct, Previously passed, Partial or Manual review recommended.

## 2. Evidence required for Passed

Each Passed result links to `qa/evidence/<TEST-ID>/` and a machine-readable result at `qa/results/<TEST-ID>.json` containing:

- test ID and exact application, schema, canonical-corpus and policy versions;
- source revision/tree hash, final package SHA-256 and dependency-lock hash;
- OS, architecture, runtime, browser, SQLite and Hermes/backend versions;
- pathway, protected context, workspace, partition, data class, rule source/version, fixture and permission state;
- exact command or manual procedure, start/end UTC, expected and observed result;
- sanitized UI/API event, database assertion, state transition, screenshot, log or receipt as appropriate;
- proof that production used no mock, canned AI, fake citation/tool/progress/connection or timer-simulated stream;
- test owner and independent reviewer for critical security, governance, integrity, clinical-boundary, AI/agent, migration and recovery tests;
- defect/blocker reference when not Passed; and
- evidence-file SHA-256.

Evidence must contain no secret, raw Soul/quiz/interview material, PHI, patient narrative, restricted assessment, confidential learner/workforce/clinical-site content or sensitive message body.

## 3. Execution rules

1. Test the installable/reproducibly runnable final package, not only a development server.
2. Core CRUD, Core Four, guided learning, governance, Guide, starters, backup and diagnostics work with AI/retrieval disabled.
3. Production cannot select test doubles; mocks remain test-build only.
4. Negative-input tests prove reject before persistence, zero body in database/files/log/export/memory and zero AI forwarding.
5. Client checks never substitute for server and repository enforcement.
6. A connected state requires a recent authenticated provider capability result.
7. Streaming passes only with multiple ordered provider-originated deltas and honest cancellation.
8. A citation passes only with a real source and persisted exact claim-source relationship.
9. Student/Assistant/Bridge and academic/placement/employment/personal/community boundaries are tested at API, repository, search, cache, memory, AI context, export and awards.
10. A supported OS requires clean install, first run, restart, update/rollback, backup/restore and uninstall for this artifact.
11. Unsupported critical probes are blockers.
12. Material code, dependency, migration, policy, power, agent, criteria or package changes invalidate affected evidence.
13. The 136 canonical FUTURE checks remain separate from full-stack target tests; neither suite substitutes for the other.

## 4. Critical blockers

Any of the following forces **Not operational**:

- install, normal launch, auth, durable SQLite CRUD, migration rollback, backup/restore or local deletion fails;
- an enabled visible control is a no-op, placeholder, fake action or dead link;
- a secret appears in client, browser storage, URL, log, export, evidence, source or package;
- PHI, live-patient content or confidential learner/workforce/clinical-site content persists or reaches AI;
- a pathway, workspace or protected-context boundary leaks without an exact allowed bridge;
- live/prohibited assessment help, fabricated evidence or hidden AI authorship is produced;
- the product determines scope, competence, assignment, delegation, care, diagnosis, treatment, medication/device action or documentation;
- a pathway/title is treated as enrollment, employment, authority, scope, competence or permission;
- general guidance is presented as local school/employer/clinical-site policy;
- a claim has a fabricated citation or stale/superseded source silently supports current use;
- an agent/automation starts above its approved level, self-approves, widens scope, retries silently, runs in background, writes externally or survives Kill;
- any send, submit, post, schedule, purchase, apply, contact, score/rank-person or official-system-write surface exists;
- fake AI, tool, citation, progress, connection or completion state exists;
- AI failure disables or corrupts core work;
- starter/synthetic work counts as outcome, Passport evidence or mastery;
- a Passport stage/badge implies grade, credential, licensure, certification, competence or authority;
- hidden surveillance, sentiment, ranking, profiling or prediction exists;
- any critical target or canonical compatibility result is Failed, Blocked, Unsupported or Not Run; or
- final readiness contradicts this ledger.

## 5. Release metadata

| Field | Value |
|---|---|
| Application version | TBD |
| Product ID | future-nursing-student-assistant-mission-control |
| Canonical program | NAIO-FUTURE-COMPLETE-1.0 |
| Source revision/tree hash | TBD |
| Package filename and SHA-256 | TBD |
| Database schema and migration range | TBD |
| Pathway(s) tested | Nursing Student / Nursing Assistant / Bridge / TBD |
| Protected contexts tested | Academic / clinical placement / employment / personal / community-public / TBD |
| Target OS/architectures | TBD |
| Live Hermes available | Yes / No |
| Compatible backend available | Yes / No |
| Retrieval provider available | Yes / No |
| Test start/end UTC | TBD |
| Release owner / independent reviewer | TBD |
| Unresolved critical defects | TBD |

## 6. Control-derived tests

There is exactly one explicit test below for each of the 169 rows in `FUTURE-Control-Completeness-Matrix.csv`. Passing requires intended behavior, persistence, permission, offline behavior, error behavior and named verification—not merely the happy path.

| Test ID | Area | Priority | Verification target | Required evidence | Result |
|---|---|---|---|---|---|
| CTL-APP-001 | Launcher | Required | macOS launch: Clean macOS package launch; intended: Verify prerequisites; initialize or migrate; start loopback server; open authenticated UI.; offline: Fully available; failure: Stop with recovery guidance; never change storage origin | Packaged UI/API, persistence, scope and permission assertions for APP-001 | Not Run |
| CTL-APP-002 | Launcher | Required | Windows launch: Clean Windows package launch; intended: Verify prerequisites; initialize or migrate; start loopback server; open authenticated UI.; offline: Fully available; failure: Stop with recovery guidance | Packaged UI/API, persistence, scope and permission assertions for APP-002 | Not Run |
| CTL-APP-003 | Launcher | Required | Linux launch: Clean Linux package launch; intended: Verify prerequisites; initialize or migrate; start loopback server; open authenticated UI.; offline: Fully available; failure: Stop with recovery guidance | Packaged UI/API, persistence, scope and permission assertions for APP-003 | Not Run |
| CTL-APP-004 | Server | Required | Loopback binding: Loopback and remote-bind negative tests; intended: Bind to 127.0.0.1 by default and reject unsafe remote binding.; offline: Fully available; failure: Refuse unsafe startup | Packaged UI/API, persistence, scope and permission assertions for APP-004 | Not Run |
| CTL-APP-005 | Server | Required | Single instance: Concurrent launch test; intended: Prevent conflicting writers and explain lock or port conflicts.; offline: Fully available; failure: Do not start a second writer | Packaged UI/API, persistence, scope and permission assertions for APP-005 | Not Run |
| CTL-APP-006 | About | Required | Version consistency: Version consistency test; intended: Show identical app schema corpus manifest and health versions.; offline: Fully available; failure: Show integrity failure on mismatch | Packaged UI/API, persistence, scope and permission assertions for APP-006 | Not Run |
| CTL-AUTH-001 | First run | Critical | Create local credential: Credential and no-default-secret tests; intended: Create a user-chosen credential with no default password.; offline: Fully available; failure: Reject weak malformed or oversized input | Packaged UI/API, persistence, scope and permission assertions for AUTH-001 | Not Run |
| CTL-AUTH-002 | Sign in | Critical | Authenticate: Valid invalid and rate-limit tests; intended: Issue an opaque rotating session after valid credential.; offline: Fully available; failure: Generic failure and rate limit | Packaged UI/API, persistence, scope and permission assertions for AUTH-002 | Not Run |
| CTL-AUTH-003 | Session | Critical | Rotate and expire: Rotation expiry fixation tests; intended: Rotate identifiers and enforce idle and absolute expiry.; offline: Fully available; failure: Require reauthentication without data loss | Packaged UI/API, persistence, scope and permission assertions for AUTH-003 | Not Run |
| CTL-AUTH-004 | All mutations | Critical | CSRF and origin: CSRF Origin Host tests; intended: Require CSRF plus strict Origin and Host validation.; offline: Fully available; failure: Reject before mutation | Packaged UI/API, persistence, scope and permission assertions for AUTH-004 | Not Run |
| CTL-AUTH-005 | Session | Critical | Sign out and revoke: Logout and replay tests; intended: Revoke current or all sessions and clear cookies.; offline: Fully available; failure: Fail closed if revocation cannot commit | Packaged UI/API, persistence, scope and permission assertions for AUTH-005 | Not Run |
| CTL-AUTH-006 | Configuration | Critical | Secret boundary: Static dynamic artifact secret scans; intended: Keep keys tokens and credentials server-side and out of artifacts.; offline: Core works without AI; failure: Disable provider and show setup state | Packaged UI/API, persistence, scope and permission assertions for AUTH-006 | Not Run |
| CTL-ONB-001 | First run | Required | Preparation message: Message and accessibility tests; intended: Display truthful processing and time warning before setup.; offline: Fully available; failure: Offer retry without fake progress | Packaged UI/API, persistence, scope and permission assertions for ONB-001 | Not Run |
| CTL-ONB-002 | First run | Required | Safety acknowledgment: Acknowledgment gate test; intended: Require judgment privacy integrity and non-authorization acknowledgment.; offline: Fully available; failure: Block completion | Packaged UI/API, persistence, scope and permission assertions for ONB-002 | Not Run |
| CTL-ONB-003 | First run | Required | Pathway selection: Selection and no-inference tests; intended: Require explicit Student Assistant or Bridge; never infer.; offline: Fully available; failure: Unknown remains unverified | Packaged UI/API, persistence, scope and permission assertions for ONB-003 | Not Run |
| CTL-ONB-004 | First run | Required | Discover import: Valid invalid oversize import tests; intended: Validate versioned Discover Packet; preview before Apply.; offline: Fully available; failure: Reject atomically; retain no invalid body | Packaged UI/API, persistence, scope and permission assertions for ONB-004 | Not Run |
| CTL-ONB-005 | First run | Required | Soul result import: Raw-answer exclusion tests; intended: Import approved derived results without raw answers.; offline: Fully available; failure: Reject raw or malformed input | Packaged UI/API, persistence, scope and permission assertions for ONB-005 | Not Run |
| CTL-ONB-006 | First run | Required | Mission Profile review: Field provenance tests; intended: Edit approve or reject each derived field and uncertainty.; offline: Fully available; failure: Unused until approved | Packaged UI/API, persistence, scope and permission assertions for ONB-006 | Not Run |
| CTL-ONB-007 | First run | Required | Synthetic starters: First rerun interruption tests; intended: Seed Core Four and safe learning starters idempotently.; offline: Fully available; failure: Roll back entire seed transaction | Packaged UI/API, persistence, scope and permission assertions for ONB-007 | Not Run |
| CTL-ONB-008 | First run | Required | Setup completion: Interrupted setup resume test; intended: Complete only after database profile safety pathway and starter checks.; offline: Fully available; failure: Remain resumable | Packaged UI/API, persistence, scope and permission assertions for ONB-008 | Not Run |
| CTL-HOME-001 | Command Center | Required | Core Four: Launcher count and no-side-effect tests; intended: Pin exactly four canonical launchers with no implicit AI or action.; offline: Fully available; failure: Disable with exact reason | Packaged UI/API, persistence, scope and permission assertions for HOME-001 | Not Run |
| CTL-HOME-002 | Command Center | Required | Optional fifth slot: Fifth-slot lifecycle tests; intended: Remain empty until one power is separately previewed and approved.; offline: Fully available; failure: Return to empty on invalidation | Packaged UI/API, persistence, scope and permission assertions for HOME-002 | Not Run |
| CTL-HOME-003 | Command Center | Required | Summary cards: Count and scope tests; intended: Show real scoped counts for missions learning tasks sources and reviews.; offline: Fully available; failure: Show unavailable not fabricated counts | Packaged UI/API, persistence, scope and permission assertions for HOME-003 | Not Run |
| CTL-HOME-004 | Command Center | Required | Start a Mission: Mission creation test; intended: Create a governed mission draft in active context.; offline: Fully available; failure: Reject missing context or prohibited input | Packaged UI/API, persistence, scope and permission assertions for HOME-004 | Not Run |
| CTL-HOME-005 | Command Center | Required | Today's Top Three: Top-three ordering tests; intended: Manage a maximum of three prioritized user-chosen items.; offline: Fully available; failure: No AI ranking or shame | Packaged UI/API, persistence, scope and permission assertions for HOME-005 | Not Run |
| CTL-HOME-006 | Command Center | Required | Attention queue: Queue and scope tests; intended: Show deterministic due blocked stale and human-review items.; offline: Fully available; failure: Show rule error honestly | Packaged UI/API, persistence, scope and permission assertions for HOME-006 | Not Run |
| CTL-HOME-007 | Command Center | Required | Global Pause: Pause concurrency tests; intended: Prevent new AI agent tool and automation work; preserve CRUD.; offline: Fully available; failure: Fail closed for new runs | Packaged UI/API, persistence, scope and permission assertions for HOME-007 | Not Run |
| CTL-HOME-008 | Command Center | Required | Governance bar: Cross-screen consistency test; intended: Show pathway context EDENA source rule authority memory and AI state.; offline: Fully available; failure: Show Unknown or Unclassified | Packaged UI/API, persistence, scope and permission assertions for HOME-008 | Not Run |
| CTL-CTX-001 | Context selector | Critical | Active pathway: Single-pathway tests; intended: Show exactly one selected Student Assistant or Bridge pathway.; offline: Fully available; failure: No inference from title | Packaged UI/API, persistence, scope and permission assertions for CTX-001 | Not Run |
| CTL-CTX-002 | Context selector | Critical | Active context: Context-required tests; intended: Select academic placement employment personal or community/public.; offline: Fully available; failure: Missing context blocks promotion | Packaged UI/API, persistence, scope and permission assertions for CTX-002 | Not Run |
| CTL-CTX-003 | Bridge mode | Critical | Academic separation: Bridge isolation tests; intended: Keep academic and clinical-placement records from employment records.; offline: Fully available; failure: Default deny cross-context join | Packaged UI/API, persistence, scope and permission assertions for CTX-003 | Not Run |
| CTL-CTX-004 | Pathway transition | Critical | Preview transition: Transition and stale-approval tests; intended: Preview invalidations before changing Student Assistant or Bridge.; offline: Fully available; failure: Roll back incomplete transition | Packaged UI/API, persistence, scope and permission assertions for CTX-004 | Not Run |
| CTL-CTX-005 | Rules | Critical | Academic rules: Academic-rule lifecycle tests; intended: Record current rule source scope permitted assistance disclosure and expiry.; offline: Fully available; failure: Unknown blocks graded-work support | Packaged UI/API, persistence, scope and permission assertions for CTX-005 | Not Run |
| CTL-CTX-006 | Rules | Critical | Employer and site rules: Employer/site rule tests; intended: Record source scope restrictions verifier and expiry without confidential content.; offline: Fully available; failure: Never infer local rule | Packaged UI/API, persistence, scope and permission assertions for CTX-006 | Not Run |
| CTL-CTX-007 | Context settings | Critical | Create role workspace: Workspace create tests; intended: Create only a scoped FUTURE workspace with explicit pathway and contexts.; offline: Fully available; failure: Reject collision or incomplete boundary | Packaged UI/API, persistence, scope and permission assertions for CTX-007 | Not Run |
| CTL-CTX-008 | Context settings | Critical | Switch role dashboard: Cross-role isolation tests; intended: Clear prior scoped caches selections memory and AI context.; offline: Fully available; failure: Deny inaccessible workspace | Packaged UI/API, persistence, scope and permission assertions for CTX-008 | Not Run |
| CTL-CTX-009 | Context settings | Critical | Field-level bridge: Bridge allowlist tests; intended: Permit exact non-prohibited fields for stated purpose and expiry.; offline: Fully available; failure: Default deny and expire immediately | Packaged UI/API, persistence, scope and permission assertions for CTX-009 | Not Run |
| CTL-CTX-010 | Context settings | Critical | Delete workspace: Scoped delete restore tests; intended: Preview impact; soft-delete only selected workspace.; offline: Fully available; failure: Preserve other roles and contexts | Packaged UI/API, persistence, scope and permission assertions for CTX-010 | Not Run |
| CTL-MISS-001 | Missions | Critical | Create: Mission create validation; intended: Create with goal pathway context EDENA retention and data class.; offline: Fully available; failure: Reject prohibited or unscoped input | Packaged UI/API, persistence, scope and permission assertions for MISS-001 | Not Run |
| CTL-MISS-002 | Missions | Critical | Read: Read authorization test; intended: Display only authorized active-scope records.; offline: Fully available; failure: Return not found without leakage | Packaged UI/API, persistence, scope and permission assertions for MISS-002 | Not Run |
| CTL-MISS-003 | Missions | Critical | Edit: Concurrency invalidation tests; intended: Update with revision check and downstream invalidation.; offline: Fully available; failure: Reject stale revision atomically | Packaged UI/API, persistence, scope and permission assertions for MISS-003 | Not Run |
| CTL-MISS-004 | Missions | Critical | Duplicate: Duplicate sanitization test; intended: Copy permitted content without approvals awards tokens or restricted links.; offline: Fully available; failure: Exclude stale or inaccessible data | Packaged UI/API, persistence, scope and permission assertions for MISS-004 | Not Run |
| CTL-MISS-005 | Missions | Critical | Archive: Archive test; intended: Archive without destroying history or evidence links.; offline: Fully available; failure: Block active run | Packaged UI/API, persistence, scope and permission assertions for MISS-005 | Not Run |
| CTL-MISS-006 | Missions | Critical | Restore: Restore test; intended: Restore after scope dependency and rule validation.; offline: Fully available; failure: Remain archived on failure | Packaged UI/API, persistence, scope and permission assertions for MISS-006 | Not Run |
| CTL-MISS-007 | Missions | Critical | Soft delete: Soft-delete test; intended: Move to recoverable trash after impact preview and confirmation.; offline: Fully available; failure: Block active dependency | Packaged UI/API, persistence, scope and permission assertions for MISS-007 | Not Run |
| CTL-MISS-008 | Missions | Critical | Recover: Recovery no-token test; intended: Recover without reviving approvals consents or run tokens.; offline: Fully available; failure: Require renewed review | Packaged UI/API, persistence, scope and permission assertions for MISS-008 | Not Run |
| CTL-MISS-009 | Missions | Critical | Search filter sort: Mission query tests; intended: Query title status pathway context tier date and starter state.; offline: Fully available; failure: No cross-scope counts/snippets | Packaged UI/API, persistence, scope and permission assertions for MISS-009 | Not Run |
| CTL-MISS-010 | Mission Workspace | Critical | Assess: Assess classification test; intended: Separate user facts sources assumptions unknowns constraints and human perspectives.; offline: Fully available; failure: Reject prohibited data before save | Packaged UI/API, persistence, scope and permission assertions for MISS-010 | Not Run |
| CTL-MISS-011 | Mission Workspace | Critical | Define: Define gate test; intended: Define learning need problem opportunity factors dependencies and gaps.; offline: Fully available; failure: Require meaningful content | Packaged UI/API, persistence, scope and permission assertions for MISS-011 | Not Run |
| CTL-MISS-012 | Mission Workspace | Critical | Plan: Plan completeness test; intended: Compare options; define goals measures tasks capacity safeguards and human review.; offline: Fully available; failure: Block unresolved consequential fields | Packaged UI/API, persistence, scope and permission assertions for MISS-012 | Not Run |
| CTL-MISS-013 | Mission Workspace | Critical | Implement: Implement action-ceiling test; intended: Create local tasks prompts rehearsals and draft artifacts only.; offline: Fully available; failure: No external execution | Packaged UI/API, persistence, scope and permission assertions for MISS-013 | Not Run |
| CTL-MISS-014 | Mission Workspace | Critical | Evaluate: Evaluate evidence-link test; intended: Compare observed results; record learning continue modify escalate or stop.; offline: Fully available; failure: Do not invent outcomes | Packaged UI/API, persistence, scope and permission assertions for MISS-014 | Not Run |
| CTL-MISS-015 | Mission Workspace | Critical | Stage review: Ordered-stage tests; intended: Advance in order after content governance authorship and human checks.; offline: Fully available; failure: Fail stale hash/rule/authority | Packaged UI/API, persistence, scope and permission assertions for MISS-015 | Not Run |
| CTL-MISS-016 | Mission Workspace | Critical | New iteration: Iteration lineage test; intended: Carry selected learning into a new Assess cycle with lineage.; offline: Fully available; failure: Never overwrite prior cycle | Packaged UI/API, persistence, scope and permission assertions for MISS-016 | Not Run |
| CTL-WORK-001 | Projects | Required | Project CRUD: Project CRUD tests; intended: Create read edit archive restore and delete scoped projects.; offline: Fully available; failure: Enforce context and dependency | Packaged UI/API, persistence, scope and permission assertions for WORK-001 | Not Run |
| CTL-WORK-002 | Goals | Required | Goal CRUD: Goal CRUD tests; intended: Manage measurable learning life career and community goals.; offline: Fully available; failure: Reject invalid target/unit | Packaged UI/API, persistence, scope and permission assertions for WORK-002 | Not Run |
| CTL-WORK-003 | Milestones | Required | Milestone CRUD: Milestone tests; intended: Manage dates dependencies and status.; offline: Fully available; failure: Detect impossible or circular links | Packaged UI/API, persistence, scope and permission assertions for WORK-003 | Not Run |
| CTL-WORK-004 | Tasks | Required | Task CRUD: Task CRUD cycle tests; intended: Manage tasks subtasks priority due date status and links.; offline: Fully available; failure: Reject cycles stale edits and context leak | Packaged UI/API, persistence, scope and permission assertions for WORK-004 | Not Run |
| CTL-WORK-005 | Measures | Required | Measure CRUD: Measure version tests; intended: Manage definition baseline target source cadence and result.; offline: Fully available; failure: Unknown definition blocks interpretation | Packaged UI/API, persistence, scope and permission assertions for WORK-005 | Not Run |
| CTL-WORK-006 | Reviews | Required | Human review CRUD: Review lifecycle tests; intended: Schedule and record exact human review scope decision and expiry.; offline: Fully available; failure: Expired or missing review fails | Packaged UI/API, persistence, scope and permission assertions for WORK-006 | Not Run |
| CTL-WORK-007 | Records | Required | Notes decisions assumptions risks safeguards: Supporting-record tests; intended: Create edit correct archive and link supporting records.; offline: Fully available; failure: Reject prohibited input/link | Packaged UI/API, persistence, scope and permission assertions for WORK-007 | Not Run |
| CTL-WORK-008 | Attachments | Required | Safe metadata registration: Attachment boundary tests; intended: Register approved local file metadata after boundary scan.; offline: Fully available; failure: Reject prohibited body type or path | Packaged UI/API, persistence, scope and permission assertions for WORK-008 | Not Run |
| CTL-WORK-009 | History | Required | Activity history: Audit redaction tests; intended: Show redacted append-only material transitions and receipts.; offline: Fully available; failure: Hide bodies and other scopes | Packaged UI/API, persistence, scope and permission assertions for WORK-009 | Not Run |
| CTL-WORK-010 | Artifacts | Required | Maturity and authorship: Artifact transition tests; intended: Gate maturity and preserve learner/AI contribution and disclosure.; offline: Fully available; failure: Invalidate on material change | Packaged UI/API, persistence, scope and permission assertions for WORK-010 | Not Run |
| CTL-LEARN-001 | Learn & Practice | Critical | Declare task: Task classification tests; intended: Capture context task type source/rule and desired coaching level.; offline: Fully available; failure: Unknown assessment state limits support | Packaged UI/API, persistence, scope and permission assertions for LEARN-001 | Not Run |
| CTL-LEARN-002 | Learn & Practice | Critical | Attempt before answer: Attempt-gate tests; intended: Require attempt or retrieval before expanded explanation where appropriate.; offline: Fully available; failure: Offer skip/example/human route | Packaged UI/API, persistence, scope and permission assertions for LEARN-002 | Not Run |
| CTL-LEARN-003 | Learn & Practice | Critical | Challenge ladder: Rung transition tests; intended: Support Explain Coach Rehearse Create Teach back Reflect.; offline: Fully available; failure: Never imply validation | Packaged UI/API, persistence, scope and permission assertions for LEARN-003 | Not Run |
| CTL-LEARN-004 | Learn & Practice | Critical | Study sprint: Study-sprint tests; intended: Create retrieval interleaving spacing and error-repair plan.; offline: Fully available; failure: No addictive streaks | Packaged UI/API, persistence, scope and permission assertions for LEARN-004 | Not Run |
| CTL-LEARN-005 | Learn & Practice | Critical | Teach-back: Teach-back evidence tests; intended: Capture learner explanation and unresolved questions.; offline: Fully available; failure: No auto-competence claim | Packaged UI/API, persistence, scope and permission assertions for LEARN-005 | Not Run |
| CTL-LEARN-006 | Academic integrity | Critical | Assessment screen: Assessment refusal zero-retention tests; intended: Detect live/prohibited assessment request before AI or storage.; offline: Fully available; failure: Block and convert to coaching | Packaged UI/API, persistence, scope and permission assertions for LEARN-006 | Not Run |
| CTL-LEARN-007 | Academic integrity | Critical | Authorship and disclosure: Authorship disclosure tests; intended: Record AI role learner edits verification and required disclosure.; offline: Fully available; failure: Block promotion when unresolved | Packaged UI/API, persistence, scope and permission assertions for LEARN-007 | Not Run |
| CTL-LEARN-008 | Academic integrity | Critical | Truthful evidence: Fabrication negative tests; intended: Reject fabricated hours competence citations reflections signatures credentials or experience.; offline: Fully available; failure: No body retention | Packaged UI/API, persistence, scope and permission assertions for LEARN-008 | Not Run |
| CTL-LEARN-009 | Skills rehearsal | Critical | Fictional/approved mode: Fictional/live boundary tests; intended: Require fictional or approved generic scenario and source.; offline: Fully available; failure: Live patient exits immediately | Packaged UI/API, persistence, scope and permission assertions for LEARN-009 | Not Run |
| CTL-LEARN-010 | Skills rehearsal | Critical | Non-authorization label: Non-credential copy tests; intended: Show rehearsal is not competence clearance or care authority.; offline: Fully available; failure: Block misleading export | Packaged UI/API, persistence, scope and permission assertions for LEARN-010 | Not Run |
| CTL-LEARN-011 | Clinical boundary | Critical | No care direction: Clinical action negative matrix; intended: Block diagnosis treatment medication device assignment delegation documentation and care plans.; offline: Fully available; failure: Route to approved human/process | Packaged UI/API, persistence, scope and permission assertions for LEARN-011 | Not Run |
| CTL-LEARN-012 | Session close | Critical | Independence review: Learning-independence tests; intended: Record learning verification uncertainty human needs and next independent step.; offline: Fully available; failure: Allow session-only deletion | Packaged UI/API, persistence, scope and permission assertions for LEARN-012 | Not Run |
| CTL-FUT-001 | FUTURE Library | Critical | Power 1 North Star: Power 1 lifecycle test; intended: Open inactive synthetic preview; create local direction draft only.; offline: Fully available; failure: No activation or outcome claim | Packaged UI/API, persistence, scope and permission assertions for FUT-001 | Not Run |
| CTL-FUT-002 | FUTURE Library | Critical | Power 2 Capacity and logistics: Power 2 boundary test; intended: Create user-controlled planning scenarios without financial/health decisions.; offline: Fully available; failure: No guarantee or diagnosis | Packaged UI/API, persistence, scope and permission assertions for FUT-002 | Not Run |
| CTL-FUT-003 | FUTURE Library | Critical | Power 3 Confidence and recovery: Power 3 help-seeking test; intended: Support reflection re-entry and human-help map without diagnosis.; offline: Fully available; failure: Pause productivity on safety concern | Packaged UI/API, persistence, scope and permission assertions for FUT-003 | Not Run |
| CTL-FUT-004 | FUTURE Library | Critical | Power 4 Active learning: Power 4 learning test; intended: Instantiate learner-authored study sprint.; offline: Fully available; failure: Respect assessment rules | Packaged UI/API, persistence, scope and permission assertions for FUT-004 | Not Run |
| CTL-FUT-005 | FUTURE Library | Critical | Power 5 Skills readiness: Power 5 clinical-boundary test; intended: Instantiate fictional or approved rehearsal only.; offline: Fully available; failure: No live care or competence claim | Packaged UI/API, persistence, scope and permission assertions for FUT-005 | Not Run |
| CTL-FUT-006 | FUTURE Library | Critical | Power 6 Exam knowledge gaps: Power 6 assessment test; intended: Create practice/gap plan without restricted items or pass guarantees.; offline: Fully available; failure: No credential/competence prediction | Packaged UI/API, persistence, scope and permission assertions for FUT-006 | Not Run |
| CTL-FUT-007 | FUTURE Library | Critical | Power 7 SAFE Prompt: Power 7 SAFE test; intended: Build Situation Aim Facts Expectations and when-not-to-use review.; offline: Fully available; failure: Reject prohibited data | Packaged UI/API, persistence, scope and permission assertions for FUT-007 | Not Run |
| CTL-FUT-008 | FUTURE Library | Critical | Power 8 Evidence detective: Power 8 evidence test; intended: Compare real sources authority freshness conflict and uncertainty.; offline: Manual source work available; failure: Never invent metadata/citation | Packaged UI/API, persistence, scope and permission assertions for FUT-008 | Not Run |
| CTL-FUT-009 | FUTURE Library | Critical | Power 9 Governance red team: Power 9 adversarial test; intended: Test privacy bias surveillance injection deception and authority gaps.; offline: Fully available; failure: No people profiling | Packaged UI/API, persistence, scope and permission assertions for FUT-009 | Not Run |
| CTL-FUT-010 | FUTURE Library | Critical | Power 10 Automation sandbox: Power 10 sandbox test; intended: Map/test low-risk synthetic manual workflow with rollback.; offline: Fully available; failure: No external or background action | Packaged UI/API, persistence, scope and permission assertions for FUT-010 | Not Run |
| CTL-FUT-011 | FUTURE Library | Critical | Power 11 UI/UX builder: Power 11 accessibility test; intended: Create accessible prototype without dark patterns or fake controls.; offline: Fully available; failure: Label prototype non-operational | Packaged UI/API, persistence, scope and permission assertions for FUT-011 | Not Run |
| CTL-FUT-012 | FUTURE Library | Critical | Power 12 Data innovation lab: Power 12 data-boundary test; intended: Use synthetic/public data for definitions visualization and prototypes.; offline: Fully available; failure: Reject live restricted data | Packaged UI/API, persistence, scope and permission assertions for FUT-012 | Not Run |
| CTL-FUT-013 | FUTURE Library | Critical | Power 13 Career studio: Power 13 truthfulness test; intended: Build truthful portfolio résumé/interview preparation with evidence status.; offline: Fully available; failure: No send/apply or credential inflation | Packaged UI/API, persistence, scope and permission assertions for FUT-013 | Not Run |
| CTL-FUT-014 | FUTURE Library | Critical | Power 14 Communication: Power 14 communication test; intended: Rehearse private messages SBAR feedback and mentorship in user's voice.; offline: Fully available; failure: No send/impersonation | Packaged UI/API, persistence, scope and permission assertions for FUT-014 | Not Run |
| CTL-FUT-015 | FUTURE Library | Critical | Power 15 Opportunity navigator: Power 15 action-ceiling test; intended: Explore verified opportunities scholarships jobs and side projects.; offline: Manual work available; failure: No apply/purchase/contract/guarantee | Packaged UI/API, persistence, scope and permission assertions for FUT-015 | Not Run |
| CTL-FUT-016 | FUTURE Library | Critical | Power 16 Leadership lab: Power 16 authority test; intended: Rehearse speaking up teamwork conflict and delegation questions.; offline: Fully available; failure: No borrowed authority/personnel action | Packaged UI/API, persistence, scope and permission assertions for FUT-016 | Not Run |
| CTL-FUT-017 | FUTURE Library | Critical | Power 17 Community studio: Power 17 community test; intended: Design consent-based public/synthetic community project draft.; offline: Fully available; failure: No outreach/deployment/health advice | Packaged UI/API, persistence, scope and permission assertions for FUT-017 | Not Run |
| CTL-FUT-018 | FUTURE Library | Critical | Power 18 Future explorer: Power 18 future-boundary test; intended: Explore technology pathways while separating learning from use.; offline: Fully available; failure: No clinical deployment claim | Packaged UI/API, persistence, scope and permission assertions for FUT-018 | Not Run |
| CTL-EVID-001 | Sources | Critical | Source CRUD: Source lifecycle tests; intended: Create edit archive correct and link permitted sources.; offline: Manual records available; failure: Mark verification pending | Packaged UI/API, persistence, scope and permission assertions for EVID-001 | Not Run |
| CTL-EVID-002 | Sources | Critical | Real retrieval: Real retrieval test; intended: Search configured providers and persist reproducible query metadata.; offline: Show unavailable; failure: Never substitute canned results | Packaged UI/API, persistence, scope and permission assertions for EVID-002 | Not Run |
| CTL-EVID-003 | Sources | Critical | Identifier or URL: Resolution positive/negative tests; intended: Resolve real metadata where supported.; offline: Manual unresolved record allowed; failure: Do not invent fields | Packaged UI/API, persistence, scope and permission assertions for EVID-003 | Not Run |
| CTL-EVID-004 | Claims | Critical | Claim CRUD: Claim lifecycle tests; intended: Create edit correct archive and link exact claims.; offline: Fully available; failure: Reject prohibited/empty body | Packaged UI/API, persistence, scope and permission assertions for EVID-004 | Not Run |
| CTL-EVID-005 | Claims | Critical | Claim-source link: Relationship tests; intended: Record supports qualifies contradicts or context-only.; offline: Fully available; failure: Unsupported remains unsupported | Packaged UI/API, persistence, scope and permission assertions for EVID-005 | Not Run |
| CTL-EVID-006 | Citations | Critical | Citation validator: Citation matrix tests; intended: Verify real source link current status scope and claim relationship.; offline: Local validation only; failure: Never fabricate or auto-pass | Packaged UI/API, persistence, scope and permission assertions for EVID-006 | Not Run |
| CTL-EVID-007 | Sources | Critical | Freshness and correction: Freshness propagation tests; intended: Propagate stale superseded corrected or retracted status.; offline: Manual status updates work; failure: Invalidate dependent current use | Packaged UI/API, persistence, scope and permission assertions for EVID-007 | Not Run |
| CTL-EVID-008 | Retrieval | Critical | Injection quarantine: Direct indirect encoded injection tests; intended: Prevent retrieved content changing policy tools routes or permissions.; offline: Fully available; failure: Block unsafe context | Packaged UI/API, persistence, scope and permission assertions for EVID-008 | Not Run |
| CTL-AI-001 | AI setup | Critical | Backend selection: Provider selection tests; intended: Select only implemented provider adapter.; offline: Core remains available; failure: Show Setup required | Packaged UI/API, persistence, scope and permission assertions for AI-001 | Not Run |
| CTL-AI-002 | AI setup | Critical | Authenticated health: Health truthfulness tests; intended: Verify real endpoint and capabilities.; offline: Show Offline; failure: Redact raw error/credential | Packaged UI/API, persistence, scope and permission assertions for AI-002 | Not Run |
| CTL-AI-003 | AI setup | Critical | Model discovery: Model discovery tests; intended: List models from live capability response.; offline: Show unavailable; failure: No hardcoded connected model | Packaged UI/API, persistence, scope and permission assertions for AI-003 | Not Run |
| CTL-AI-004 | Assistant | Critical | Create session: Session creation tests; intended: Create a real scoped provider session.; offline: Unavailable; failure: No fake local session | Packaged UI/API, persistence, scope and permission assertions for AI-004 | Not Run |
| CTL-AI-005 | Assistant | Critical | Resume session: Resume isolation tests; intended: Resume only authorized scoped supported session.; offline: Unavailable; failure: Reject stale/inaccessible | Packaged UI/API, persistence, scope and permission assertions for AI-005 | Not Run |
| CTL-AI-006 | Assistant | Critical | Send message: Real request boundary tests; intended: Call real backend after context data integrity and rule gates.; offline: Disabled clearly; failure: Reject before provider call | Packaged UI/API, persistence, scope and permission assertions for AI-006 | Not Run |
| CTL-AI-007 | Assistant | Critical | Genuine stream: Multi-delta genuine stream test; intended: Render multiple ordered provider-originated deltas/events.; offline: Unavailable; failure: Never timer-simulate | Packaged UI/API, persistence, scope and permission assertions for AI-007 | Not Run |
| CTL-AI-008 | Assistant | Critical | Stop generation: Slow-stream cancellation test; intended: Propagate cancellation and close stream honestly.; offline: Not applicable; failure: No accepted delta after stop | Packaged UI/API, persistence, scope and permission assertions for AI-008 | Not Run |
| CTL-AI-009 | Assistant | Critical | Retry safely: Retry idempotency tests; intended: Retry only retryable work without duplication.; offline: Unavailable; failure: Require confirmation on risk | Packaged UI/API, persistence, scope and permission assertions for AI-009 | Not Run |
| CTL-AI-010 | Assistant | Critical | Tool visibility: Real tool-event tests; intended: Show actual tool input summary progress result error and approval.; offline: Unavailable; failure: Unknown tool blocks | Packaged UI/API, persistence, scope and permission assertions for AI-010 | Not Run |
| CTL-AGENT-001 | Agent Center | Critical | Registry: Registry/default-state tests; intended: Show frozen catalog and hashes; all install P0 disabled.; offline: Definitions visible; failure: Integrity mismatch disables | Packaged UI/API, persistence, scope and permission assertions for AGENT-001 | Not Run |
| CTL-AGENT-002 | Agent Center | Critical | Route preview: Route determinism tests; intended: Show exact agents sequence inputs tools sources outputs and reviews.; offline: Draft available; failure: No hidden route | Packaged UI/API, persistence, scope and permission assertions for AGENT-002 | Not Run |
| CTL-AGENT-003 | Agent Center | Critical | Charter: Charter completeness tests; intended: Require purpose scope data context model tools limits and stop conditions.; offline: Draft available; failure: Unknown blocks run | Packaged UI/API, persistence, scope and permission assertions for AGENT-003 | Not Run |
| CTL-AGENT-004 | Agent Center | Critical | One-run authorization: Token fixture tests; intended: Bind exact hashes expiry one invocation and zero retry default.; offline: Unavailable without backend; failure: Mismatch blocks pre-call | Packaged UI/API, persistence, scope and permission assertions for AGENT-004 | Not Run |
| CTL-AGENT-005 | Agent Center | Critical | Activate: Activation gate tests; intended: Move above P0 only after exact approval and dependencies.; offline: P0 only; failure: Atomic rollback | Packaged UI/API, persistence, scope and permission assertions for AGENT-005 | Not Run |
| CTL-AGENT-006 | Agent Center | Critical | Run: Run-boundary tests; intended: Execute only allowlisted local/sandbox actions visibly.; offline: Unavailable without backend; failure: Terminate on ceiling breach | Packaged UI/API, persistence, scope and permission assertions for AGENT-006 | Not Run |
| CTL-AGENT-007 | Agent Center | Critical | Pause all: Concurrency pause tests; intended: Block new runs tools and retries while preserving local work.; offline: Fully available; failure: Fail closed | Packaged UI/API, persistence, scope and permission assertions for AGENT-007 | Not Run |
| CTL-AGENT-008 | Agent Center | Critical | Kill: Slow-run kill tests; intended: Terminate selected run and prevent resume without new authorization.; offline: Available for local coordinator; failure: Report provider limit honestly | Packaged UI/API, persistence, scope and permission assertions for AGENT-008 | Not Run |
| CTL-AGENT-009 | Agent Center | Critical | Reconcile: Reconciliation tests; intended: Compare intended and observed state before completion.; offline: Local metadata available; failure: Never infer success | Packaged UI/API, persistence, scope and permission assertions for AGENT-009 | Not Run |
| CTL-AGENT-010 | Agent Center | Critical | No external authority: Forbidden-action surface tests; intended: Expose no clinical academic employment financial send submit post or write action.; offline: Fully enforced; failure: Block and route to human | Packaged UI/API, persistence, scope and permission assertions for AGENT-010 | Not Run |
| CTL-MEM-001 | Memory | Critical | Default off: Default-off tests; intended: Store nothing persistently until explicit consent.; offline: Fully available; failure: Fail closed | Packaged UI/API, persistence, scope and permission assertions for MEM-001 | Not Run |
| CTL-MEM-002 | Memory | Critical | Preview and remember: Consent preview tests; intended: Show exact value category purpose context retention and expiry.; offline: Fully available; failure: Reject prohibited/stale scope | Packaged UI/API, persistence, scope and permission assertions for MEM-002 | Not Run |
| CTL-MEM-003 | Memory | Critical | Edit: Memory edit tests; intended: Version permitted memory with renewed consent where material.; offline: Fully available; failure: Keep prior safe state on failure | Packaged UI/API, persistence, scope and permission assertions for MEM-003 | Not Run |
| CTL-MEM-004 | Memory | Critical | Forget: Forget context tests; intended: Immediately exclude item from all local context.; offline: Fully available; failure: Fail closed retrieval | Packaged UI/API, persistence, scope and permission assertions for MEM-004 | Not Run |
| CTL-MEM-005 | Memory | Critical | Delete: Deletion truthfulness tests; intended: Transactionally remove local value/references and state provider limitation.; offline: Fully available; failure: Report undeleted external copies | Packaged UI/API, persistence, scope and permission assertions for MEM-005 | Not Run |
| CTL-MEM-006 | Memory | Critical | Scope and expiry: Cross-context expiry tests; intended: Retrieve only active owner workspace context purpose and unexpired consent.; offline: Fully available; failure: Default deny | Packaged UI/API, persistence, scope and permission assertions for MEM-006 | Not Run |
| CTL-CAP-001 | Capabilities | Required | Two-system inventory: Passport and capability inventory tests; intended: Show the canonical six-domain Passport separately from 17 build-layer activity domains.; offline: Fully available; failure: Show Not assessed; never auto-map systems | Packaged UI/API, persistence, scope and permission assertions for CAP-001 | Not Run |
| CTL-CAP-002 | Capabilities | Required | Evidence CRUD: Evidence lifecycle and separation tests; intended: Add edit correct archive and link eligible learner-produced evidence for either system.; offline: Fully available; failure: Reject synthetic duplicate prohibited or cross-context evidence | Packaged UI/API, persistence, scope and permission assertions for CAP-002 | Not Run |
| CTL-CAP-003 | Capabilities | Required | Level calculation: Passport and mastery threshold tests; intended: Apply five Passport stages and separate Basic Intermediate Advanced and orchestration criteria.; offline: Fully available; failure: Never infer an unsupported stage or level | Packaged UI/API, persistence, scope and permission assertions for CAP-003 | Not Run |
| CTL-CAP-004 | Capabilities | Required | Reflection and review: Reflection authorship and reviewer tests; intended: Require learner reflection independent next step and named human review where criteria specify.; offline: Fully available; failure: No AI-generated or self-review proof substitution | Packaged UI/API, persistence, scope and permission assertions for CAP-004 | Not Run |
| CTL-CAP-005 | Capabilities | Required | Correction revocation: Correction expiry revocation tests; intended: Correct expire revoke and recompute Passport progress and awards transparently.; offline: Fully available; failure: Remove invalid display promptly | Packaged UI/API, persistence, scope and permission assertions for CAP-005 | Not Run |
| CTL-CAP-006 | Capabilities | Required | Non-credential boundary: Non-credential and no-permission tests; intended: Never imply grade licensure certification competence eligibility authority or expanded permission.; offline: Fully available; failure: Block misleading copy/export and permission change | Packaged UI/API, persistence, scope and permission assertions for CAP-006 | Not Run |
| CTL-GOV-001 | All workflows | Critical | EDENA: EDENA matrix tests; intended: Compute Exposure Decision Evidence Needed authority Automation server-side.; offline: Fully available; failure: Unknown fails closed | Packaged UI/API, persistence, scope and permission assertions for GOV-001 | Not Run |
| CTL-GOV-002 | All inputs | Critical | PHI/live-patient guard: PHI bypass zero-retention tests; intended: Reject PHI screenshots narratives and live-care questions before persistence/AI.; offline: Fully available; failure: Zero body retention/forwarding | Packaged UI/API, persistence, scope and permission assertions for GOV-002 | Not Run |
| CTL-GOV-003 | All inputs | Critical | Learner/workforce confidentiality guard: Confidential-data negative tests; intended: Reject restricted school employee site and personnel content.; offline: Fully available; failure: Zero body retention/forwarding | Packaged UI/API, persistence, scope and permission assertions for GOV-003 | Not Run |
| CTL-GOV-004 | Academic | Critical | Integrity gate: Integrity bypass tests; intended: Apply current rules assessment state authorship and disclosure.; offline: Fully available; failure: Block unresolved/prohibited support | Packaged UI/API, persistence, scope and permission assertions for GOV-004 | Not Run |
| CTL-GOV-005 | Clinical learning | Critical | Authority ceiling: Clinical ceiling tests; intended: Block care direction scope competence assignment delegation documentation and devices.; offline: Fully available; failure: Route to approved human | Packaged UI/API, persistence, scope and permission assertions for GOV-005 | Not Run |
| CTL-GOV-006 | All workflows | Critical | Institutional authority: Authority precedence tests; intended: Current faculty program site employer and supervisor rules override general guidance.; offline: Fully available; failure: Unknown stays unverified | Packaged UI/API, persistence, scope and permission assertions for GOV-006 | Not Run |
| CTL-GOV-007 | Actions | Critical | Exact-action gate: Approval invalidation tests; intended: Show content destination context class consequence permission reviewer reversibility rollback.; offline: Draft available; failure: Changed field invalidates | Packaged UI/API, persistence, scope and permission assertions for GOV-007 | Not Run |
| CTL-GOV-008 | Actions | Critical | No external action: Forbidden route inventory tests; intended: Provide no send submit schedule purchase apply share post or official-write endpoint.; offline: Fully enforced; failure: No hidden endpoint | Packaged UI/API, persistence, scope and permission assertions for GOV-008 | Not Run |
| CTL-GOV-009 | All screens | Critical | No surveillance: Surveillance absence tests; intended: Prohibit hidden scoring ranking sentiment profiling prediction and reporting.; offline: Fully enforced; failure: Block feature/fixture | Packaged UI/API, persistence, scope and permission assertions for GOV-009 | Not Run |
| CTL-GOV-010 | All workflows | Critical | Prompt injection defense: Injection suite; intended: Untrusted files/pages cannot change policy tools permission or destination.; offline: Fully available; failure: Quarantine and block | Packaged UI/API, persistence, scope and permission assertions for GOV-010 | Not Run |
| CTL-GOV-011 | Wellbeing | Critical | Help-seeking boundary: Help-seeking tests; intended: Pause productivity coaching and show local human/emergency routes without diagnosis.; offline: Fully available; failure: No triage or diagnosis | Packaged UI/API, persistence, scope and permission assertions for GOV-011 | Not Run |
| CTL-GOV-012 | Audit | Critical | Governance receipts: Receipt integrity tests; intended: Commit redacted append-only object-hash decisions for consequential transitions.; offline: Fully available; failure: Fail transition if commit fails | Packaged UI/API, persistence, scope and permission assertions for GOV-012 | Not Run |
| CTL-DATA-001 | Data | Critical | Readable export: Export round-trip scans; intended: Export selected permitted records with versions checksums and exclusions.; offline: Fully available; failure: Exclude secrets/prohibited/other scope | Packaged UI/API, persistence, scope and permission assertions for DATA-001 | Not Run |
| CTL-DATA-002 | Data | Critical | Create backup: Backup interruption tests; intended: Produce consistent SQLite backup and manifest; optional encryption.; offline: Fully available; failure: Leave prior backup intact | Packaged UI/API, persistence, scope and permission assertions for DATA-002 | Not Run |
| CTL-DATA-003 | Data | Critical | Restore preview: Restore negative matrix; intended: Validate archive checksums schema scope foreign keys and secrets temporarily.; offline: Fully available; failure: Reject malformed/incompatible | Packaged UI/API, persistence, scope and permission assertions for DATA-003 | Not Run |
| CTL-DATA-004 | Data | Critical | Execute restore: Atomic restore tests; intended: Back up current data then atomically swap validated restore.; offline: Fully available; failure: Roll back any failure | Packaged UI/API, persistence, scope and permission assertions for DATA-004 | Not Run |
| CTL-DATA-005 | Data | Critical | Update: Update failure tests; intended: Verify package back up migrate and validate before promotion.; offline: Fully available; failure: Stop before damage | Packaged UI/API, persistence, scope and permission assertions for DATA-005 | Not Run |
| CTL-DATA-006 | Data | Critical | Rollback: Rollback expiry tests; intended: Restore compatible app/data without reviving expired authority/consent/tokens.; offline: Fully available; failure: Block incompatible rollback | Packaged UI/API, persistence, scope and permission assertions for DATA-006 | Not Run |
| CTL-DATA-007 | Data | Critical | Delete local data: Deletion tests; intended: Preview scope and verify local deletion paths.; offline: Fully available; failure: Report locked/external data | Packaged UI/API, persistence, scope and permission assertions for DATA-007 | Not Run |
| CTL-DATA-008 | Data | Critical | Uninstall: Per-OS uninstall tests; intended: Separate application removal from optional user-data deletion.; offline: Fully available; failure: Never delete data implicitly | Packaged UI/API, persistence, scope and permission assertions for DATA-008 | Not Run |
| CTL-DIAG-001 | Diagnostics | Required | Application and database: Database diagnostic tests; intended: Report versions migrations integrity and storage path read-only.; offline: Fully available; failure: Show recovery on failure | Packaged UI/API, persistence, scope and permission assertions for DIAG-001 | Not Run |
| CTL-DIAG-002 | Diagnostics | Required | Hermes status: Hermes diagnostic tests; intended: Report authenticated health capability time and redacted error.; offline: Show Offline/Setup required; failure: No credentials/raw responses | Packaged UI/API, persistence, scope and permission assertions for DIAG-002 | Not Run |
| CTL-DIAG-003 | Diagnostics | Required | Model stream session cancel: Capability freshness tests; intended: Report actual discovered support and freshness.; offline: Show unavailable; failure: Stale becomes Limited | Packaged UI/API, persistence, scope and permission assertions for DIAG-003 | Not Run |
| CTL-DIAG-004 | Diagnostics | Required | Memory tools retrieval: Capability redaction tests; intended: Report enabled/disabled support without record bodies.; offline: Show disabled; failure: No secret/destination/body | Packaged UI/API, persistence, scope and permission assertions for DIAG-004 | Not Run |
| CTL-DIAG-005 | Diagnostics | Required | Run diagnostics: Read-only diagnostic tests; intended: Execute read-only local checks and optional provider probes.; offline: Local checks available; failure: Never mutate | Packaged UI/API, persistence, scope and permission assertions for DIAG-005 | Not Run |
| CTL-DIAG-006 | Diagnostics | Required | Control completeness: DOM API matrix reconciliation; intended: Reconcile every enabled UI control route and API with this matrix.; offline: Fully available; failure: Any unregistered control fails release | Packaged UI/API, persistence, scope and permission assertions for DIAG-006 | Not Run |
| CTL-GUIDE-001 | Guide | Required | Guide navigation: Guide section/link tests; intended: Explain setup pathway contexts Core Four missions safety powers agents memory and recovery.; offline: Fully available; failure: Always available without AI | Packaged UI/API, persistence, scope and permission assertions for GUIDE-001 | Not Run |
| CTL-GUIDE-002 | Guide | Required | Contextual help: Help coverage tests; intended: Open concise help/tooltips without losing work.; offline: Fully available; failure: Critical safety help remains visible | Packaged UI/API, persistence, scope and permission assertions for GUIDE-002 | Not Run |
| CTL-GUIDE-003 | Guide | Required | Restart walkthrough: Restart no-duplicate tests; intended: Restart onboarding without deleting data or duplicating starters.; offline: Fully available; failure: Explain policy renewal separately | Packaged UI/API, persistence, scope and permission assertions for GUIDE-003 | Not Run |
| CTL-GUIDE-004 | Guide | Required | Learner examples: Guide language tests; intended: Use accessible synthetic examples and state human authority clearly.; offline: Fully available; failure: Never present as answer/approval/competence | Packaged UI/API, persistence, scope and permission assertions for GUIDE-004 | Not Run |
| CTL-ACCESS-001 | All screens | Required | Keyboard navigation: Automated/manual keyboard tests; intended: Operate all controls with logical focus and no traps.; offline: Fully available; failure: Unavailable reason announced | Packaged UI/API, persistence, scope and permission assertions for ACCESS-001 | Not Run |
| CTL-ACCESS-002 | Dynamic UI | Required | Status announcements: Screen-reader announcement tests; intended: Announce validation stream cancellation governance and errors.; offline: Fully available; failure: Critical errors remain visible | Packaged UI/API, persistence, scope and permission assertions for ACCESS-002 | Not Run |
| CTL-ACCESS-003 | All screens | Required | Responsive reflow: Viewport zoom tests; intended: Support mobile zoom text spacing and reflow without clipping.; offline: Fully available; failure: No hidden controls | Packaged UI/API, persistence, scope and permission assertions for ACCESS-003 | Not Run |
| CTL-ACCESS-004 | Preferences | Required | Motion contrast density text: Preference tests; intended: Honor accessible preferences without weakening meaning.; offline: Fully available; failure: Reset invalid preference safely | Packaged UI/API, persistence, scope and permission assertions for ACCESS-004 | Not Run |
| CTL-ACCESS-005 | Artifacts | Required | Accessible exports: Export accessibility tests; intended: Produce structured Markdown/HTML and optional accessible PDF.; offline: Markdown available; failure: Fail honestly if renderer unavailable | Packaged UI/API, persistence, scope and permission assertions for ACCESS-005 | Not Run |

## 7. Cross-cutting full-stack acceptance scenarios

| Test ID | Area | Priority | Expected result | Required evidence | Result |
|---|---|---|---|---|---|
| INT-001 | Clean install | Critical | A fresh package installs/launches with no undeclared dependency or preexisting state. | Clean-machine transcript, package hash, screenshot | Not Run |
| INT-002 | Restart durability | Critical | Mission, project, task, learning, source, profile and governance records survive server/browser restart. | Before/after database assertions | Not Run |
| INT-003 | Offline core | Critical | CRUD, Core Four, guided learning, Guide, starters, governance and backup work with network/AI denied. | Network-denied checklist and trace | Not Run |
| INT-004 | No fake AI | Critical | Production has no canned response, fake tool/citation/progress/connection or simulated stream. | Source/build scan and runtime trace | Not Run |
| INT-005 | Legacy migration | Critical | Approved legacy import previews, backs up, validates and migrates once without overwrite. | Migration transcript and row reconciliation | Not Run |
| INT-006 | Failed migration | Critical | Injected failure rolls back and prior application/data remain usable. | Database hashes and recovery transcript | Not Run |
| INT-007 | Restore atomicity | Critical | Corrupt, incompatible, unsafe or cross-owner backups fail; valid restore swaps atomically. | Fixture matrix and database hashes | Not Run |
| INT-008 | Personalization privacy | Critical | Raw Soul/quiz/interview answers never persist, log, export, enter memory or reach AI. | Database/log/export/context scans | Not Run |
| INT-009 | Multi-role isolation | Critical | Other Nurse AI OS role data never appears through route, API, search, cache, memory, AI, awards or export. | Cross-role attack matrix | Not Run |
| INT-010 | Protected-context isolation | Critical | Academic, placement, employment, personal and community/public scopes do not leak. | Cross-context repository/API matrix | Not Run |
| INT-011 | Bridge separation | Critical | Bridge creates separate school and work partitions with no silent transfer. | Positive/negative bridge tests | Not Run |
| INT-012 | PHI zero retention | Critical | Patient identifiers, screenshots, chart excerpts and identifiable stories are rejected before any durable or provider use. | Database/files/log/export/provider capture | Not Run |
| INT-013 | Confidential-data zero retention | Critical | Restricted learner, worker and site fixtures are rejected before any durable/provider use. | Database/files/log/export/provider capture | Not Run |
| INT-014 | Pathway transition | Critical | Role change previews and invalidates incompatible rules, permissions, approvals and context. | State-transition and cache assertions | Not Run |
| INT-015 | Academic integrity | Critical | Live/prohibited assessment is blocked and converted to general coaching without item retention. | Adversarial task matrix and zero-retention evidence | Not Run |
| INT-016 | Human authorship | Critical | Learner attempt, edits, verification, AI contribution and disclosure remain inspectable. | Artifact lineage and integrity receipt | Not Run |
| INT-017 | Fictional rehearsal | Critical | Skills/clinical rehearsal requires fictional/approved generic content and never implies competence. | Scenario-state and export assertions | Not Run |
| INT-018 | Clinical authority ceiling | Critical | Diagnosis, treatment, medication, device, assignment, delegation, care plan, scope and documentation attempts block. | UI/API/provider negative matrix | Not Run |
| INT-019 | Core Four reality | Critical | Exactly four launchers create real editable local drafts with no implicit AI/action. | Launcher traversal, database and network trace | Not Run |
| INT-020 | All 18 Powers | Critical | Every `FUT-PWR-01`–`FUT-PWR-18` opens its correct preview/workflow and safe finish. | ID traversal and state report | Not Run |
| INT-021 | Inactive installation | Critical | All 18 powers install inactive; optional fifth pin remains empty. | Registry, UI and database assertions | Not Run |
| INT-022 | Three-run reminder limit | Critical | Only deterministic local reminders become P3-eligible after three supervised successes and separate approval; no agent/model/background/external authority. | Eligibility fixtures and execution trace | Not Run |
| INT-023 | Evidence reality | Critical | Real retrieval/source entry records source, authority, date, applicability, conflicts and uncertainty without invention. | Provider trace and source rows | Not Run |
| INT-024 | Claim-citation integrity | Critical | Every citation maps to a real source and exact relationship; unsupported claims remain marked. | Claim-source database and rendered artifact | Not Run |
| INT-025 | Local-policy truth | Critical | General guidance is never represented as current local school, program, site or employer policy. | Source/rule fixture matrix | Not Run |
| INT-026 | Retrieval injection | Critical | Direct, indirect and encoded content cannot change policy, tools, route, model or permission. | Adversarial source fixtures and traces | Not Run |
| INT-027 | Genuine Hermes stream | Critical | Real Hermes produces multiple ordered deltas, typed events and terminal state. | Sanitized provider/network timeline | Not Run |
| INT-028 | Stream cancellation | Critical | Stop reaches provider/tool and prevents further accepted delta or side effect. | Slow-stream timeline and receipts | Not Run |
| INT-029 | Retry idempotency | Critical | Retry duplicates no message, tool call, artifact, approval or receipt. | Fault injection and database assertions | Not Run |
| INT-030 | Backend offline transition | Critical | Connection loss is truthful; core data remains usable and uncorrupted. | Network-fault transcript | Not Run |
| INT-031 | Agent default | Critical | Exact catalog installs P0 disabled with no credentials, tools, memory, network, destination, schedule or hidden work. | Registry and runtime capability dump | Not Run |
| INT-032 | Exact one-run agent | Critical | P1/P2 token permits one scoped invocation; mismatch, expiry or second call blocks before provider. | Authorization fixture matrix | Not Run |
| INT-033 | Pause and Kill | Critical | Pause blocks new work; Kill terminates selected run and prevents tokenless resume. | Concurrent-run timeline and receipts | Not Run |
| INT-034 | No external action | Critical | No UI, API, tool or agent can care, submit, send, post, schedule, buy, apply, contact, score or write officially. | Route/API/tool inventory and adversarial calls | Not Run |
| INT-035 | Memory consent | Critical | Memory is off; each allowed item needs category, purpose, context, consent, retention and expiry. | Memory database and context tests | Not Run |
| INT-036 | Forget/delete truth | Critical | Forget removes local context; Delete removes local value; provider limitations remain explicit. | Context capture, database scan and UI copy | Not Run |
| INT-037 | Starter integrity | Critical | Seed is idempotent; Adopt/Clear/Restore preserve real work; starters do not count as evidence/outcomes. | Seed lineage and award assertions | Not Run |
| INT-038 | Passport noncredential | Critical | Six domains/five stages require eligible learner evidence and never imply grade, credential or competence. | Criteria fixtures and copy scan | Not Run |
| INT-039 | Capacity and help-seeking | Critical | Minimum/re-entry mode lowers burden; wellbeing concern pauses productivity without diagnosis. | Scenario matrix and route assertions | Not Run |
| INT-040 | No surveillance | Critical | No hidden score, rank, sentiment, profile, prediction or school/employer reporting exists. | Schema/API/UI/analytics scan | Not Run |
| INT-041 | Accessibility | Required | Keyboard, focus, reflow, zoom, reduced motion, announcements and accessible exports pass. | Automated results and manual review | Not Run |
| INT-042 | Control completeness | Critical | Every enabled UI control/route/API appears once in the matrix and works in success/offline/error states. | DOM-route-API reconciliation | Not Run |
| INT-043 | Release integrity | Critical | Manifest, checksums, versions, lockfile, SBOM, secret scan, archive safety and validator pass. | Release validator output | Not Run |
| INT-044 | Canonical compatibility import | Critical | Exact canonical 136-check definitions and IDs are imported without altered expected behavior. | Source hash, parsed inventory and diff | Not Run |

## 8. Canonical FUTURE compatibility suite — separate and mandatory

The canonical source `tests/Acceptance-Tests.md` contains exactly 136 checks. Preserve its exact text as immutable source authority and execute it against the final package with synthetic information. Do not rewrite a canonical expected block into a successful action, and do not mark a canonical criterion Passed merely because a target full-stack test passed.

| Canonical group | Exact IDs | Count | Initial state |
|---|---|---:|---|
| Foundation | `C01`–`C24` | 24 | All Not Run |
| FUTURE A — Installation and recovery | `A1`–`A8` | 8 | All Not Run |
| FUTURE B — Privacy, security and context | `B1`–`B8` | 8 | All Not Run |
| FUTURE C — Academic integrity and learning | `C1`–`C8` | 8 | All Not Run |
| FUTURE D — Clinical and role authority | `D1`–`D8` | 8 | All Not Run |
| FUTURE E — Evidence and information judgment | `E1`–`E8` | 8 | All Not Run |
| FUTURE F — Fairness, dignity and wellbeing | `F1`–`F8` | 8 | All Not Run |
| FUTURE G — Prompting and AI fluency | `G1`–`G8` | 8 | All Not Run |
| FUTURE H — Workflow, design and automation | `H1`–`H8` | 8 | All Not Run |
| FUTURE I — Communication and professional identity | `I1`–`I8` | 8 | All Not Run |
| FUTURE J — Career, money and opportunity | `J1`–`J8` | 8 | All Not Run |
| FUTURE K — Community, leadership and innovation | `K1`–`K8` | 8 | All Not Run |
| FUTURE L — Dashboard, adoption and stewardship | `L1`–`L8` | 8 | All Not Run |
| Integration | `I01`–`I16` | 16 | All Not Run |
| **Total** |  | **136** | **All Not Run** |

To avoid ID collisions, machine-readable result IDs must be namespaced as `CORE-C01`–`CORE-C24`, `OVERLAY-A1`–`OVERLAY-L8`, and `INTEGRATION-I01`–`INTEGRATION-I16`, while preserving the displayed canonical IDs and exact source text.

Minimum compatibility evidence per criterion:

- canonical ID, namespace, exact source-text hash and fixture ID;
- final package/environment hash and start/end UTC;
- expected/observed action and data deltas;
- before/after state hashes and redacted raw trace;
- explicit Passed, Failed, Blocked, Unsupported or Not Run;
- defect reference when not Passed; and
- independent review for critical safeguard probes.

## 9. Test inventory and readiness rules

- Control-derived target tests: **169**
- Cross-cutting target scenarios: **44**
- Total target full-stack tests: **213**
- Canonical compatibility checks: **136**
- Total required execution records before environment-specific expansions: **349**
- Default state at build-kit assembly: **all Not Run**

### Operational

Allowed only when all 169 control tests, all 44 target scenarios, all 136 canonical checks, every critical security/governance/recovery check and every claimed supported-OS suite Passed with no unresolved critical defect. AI claims additionally require real backend evidence.

### Core operational; AI setup pending

Allowed only when every offline/core, security, database, pathway/context, academic-integrity, clinical-boundary, starter, evidence-record, backup/recovery, packaging and accessibility gate Passed; AI/retrieval-specific checks are Blocked solely because the user has not configured a provider; the UI shows Setup required/Offline; and no promised offline function is missing. Canonical checks applicable to offline/core must have Passed.

### Not operational

Required when any core/critical target or canonical result is Failed, Blocked, Unsupported or Not Run; control completeness is unresolved; or the artifact is the source/build kit instead of the installed tested application.

## 10. Sign-off

| Role | Name or local label | Decision | UTC | Evidence/signature reference |
|---|---|---|---|---|
| Build owner | TBD | TBD | TBD | TBD |
| Independent security/governance reviewer | TBD | TBD | TBD | TBD |
| Nursing education/academic-integrity reviewer | TBD | TBD | TBD | TBD |
| Nursing-assistant scope/supervision reviewer | TBD | TBD | TBD | TBD |
| Accessibility reviewer | TBD | TBD | TBD | TBD |
| Release owner | TBD | TBD | TBD | TBD |
