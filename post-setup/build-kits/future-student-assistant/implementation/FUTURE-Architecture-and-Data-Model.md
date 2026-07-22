# FUTURE Mission Control — Reference Architecture and Data Model

**Target product:** FUTURE — Nursing Student & Nursing Assistant Mission Control  
**Product ID:** `future-nursing-student-assistant-mission-control`  
**Population lane:** `nursing_student_assistant`  
**Canonical dashboard:** `/nursing-students-assistants/dashboard`  
**Home label:** `FUTURE Mission Control`  
**Namespace:** `future.*`  
**Readiness at build-kit assembly:** **Not operational**

The target identity and route are build-layer implementation decisions. The canonical domain authority remains `NAIO-FUTURE-COMPLETE-1.0`. This architecture becomes executable only after Hermes completes read-only preflight, presents the combined Activation Card, receives explicit approval, implements the application and executes the acceptance ledger.

## 1. Design commitments

Preserve the FUTURE mission, Student/Assistant/Bridge selection, protected spaces, Core Four, guided-learning contract, learner/patient/workforce Trust Shield, EDENA screen, exact-action gate, five cards, AI Literacy Passport, 18 inactive powers, seven- and 90-day launch programs and 136 canonical compatibility checks.

The local application must add—not merely claim—authentication, durable SQLite storage, forward-only migrations, offline CRUD, structured learning and planning, real Hermes capability discovery, genuine streaming/cancel, source/citation integrity, consent-controlled memory, bounded agents/automations, context isolation, complete controls, backup/recovery and reproducible release evidence.

Non-negotiable product qualities:

1. The learner remains author, decision-maker and accountable human.
2. Core work functions with AI and network disabled.
3. No PHI, live-patient narrative or confidential learner/workforce/clinical-site material enters the product.
4. Academic, clinical-placement, employment, personal and public/community contexts do not silently mix.
5. The product teaches and rehearses; it never confers clinical, academic or employment authority.
6. All AI/agent work is visible, bounded, cancellable and subordinate to human review.
7. Every enabled control is real and testable.
8. Readiness comes only from executed evidence against the final package.

## 2. Recommended local architecture

```text
Browser UI
  │ same-origin authenticated API + genuine streamed events
  ▼
Loopback application server (127.0.0.1 by default)
  ├── authentication, rotating sessions, CSRF, Origin/Host, rate/size limits
  ├── pathway, protected-space and active-context authorization
  ├── EDENA + Trust Shield + academic-integrity + scope policy engine
  ├── SQLite repositories, transactions and forward-only migrations
  ├── mission/project/task and guided-learning services
  ├── FUTURE Core Four, 18-Power and activation-state services
  ├── evidence registry, retrieval and claim/citation validation
  ├── AIBackend
  │    ├── Hermes adapter discovered from the installed environment
  │    └── optional compatible adapter
  ├── agent registry, route preview, exact-run coordinator, Pause and Kill
  ├── consent-controlled structured memory
  ├── starter/adoption, backup/restore and diagnostics
  └── redacted governance/audit receipts
       │
       ├── private local application-data directory
       └── configured loopback Hermes service
```

The browser is not a trust boundary. Validate authentication, scope, data class, academic/employer rule, EDENA state, permissions and object revision on the server for every mutation, import, export, retrieval, AI call, agent run, memory operation, approval and cross-record relationship.

Browser storage may contain only non-secret, non-authoritative display preferences and an ephemeral safe cache. SQLite is the durable source of truth.

## 3. Suggested implementation layout

```text
app/
├── client/
│   ├── index.html
│   ├── assets/
│   └── modules/
├── server/
│   ├── main.*
│   ├── auth/
│   ├── api/
│   ├── domain/
│   │   ├── pathways/
│   │   ├── contexts/
│   │   ├── learning/
│   │   ├── future-powers/
│   │   └── work-management/
│   ├── governance/
│   ├── evidence/
│   ├── agents/
│   ├── ai/
│   │   ├── AIBackend.*
│   │   ├── hermes-adapter.*
│   │   └── compatible-adapter.*
│   ├── memory/
│   ├── audit/
│   └── db/
│       ├── connection.*
│       ├── migrations/
│       └── repositories/
├── config/
├── tests/
├── scripts/
├── .env.example
├── package.json
└── lockfile
```

Prefer a supported LTS runtime, locked dependencies and the smallest maintainable local stack. Any departure must be explained in the Activation Card with platform, security, migration and test consequences.

## 4. Identity, pathway and workspace model

One authenticated local owner has one unified identity and one active FUTURE Command Center. The owner explicitly selects one active pathway:

- `nursing_student`
- `nursing_assistant`
- `bridge`

The system never infers pathway from imported text, title, schedule or usage. A pathway does not prove status, enrollment, employment, scope, competence or authority. A pathway transition requires preview, confirmation and invalidation of incompatible assumptions, rules, permissions and optional-power approvals.

### Protected-space implementation

```text
local_owner
└── unified_identity
    └── FUTURE Command Center (one active pathway)
        ├── learning context
        │   ├── private self-study
        │   ├── declared course/rule scope
        │   └── fictional skills/clinical rehearsal
        ├── work-growth context
        │   └── general development; no employer or worker confidential data
        ├── life context
        │   └── private goals, capacity and logistics
        └── community-and-future context
            └── public/synthetic/consent-based planning
```

For authorization and testing, persist the more precise active context enum:

- `academic_learning`
- `clinical_placement_learning`
- `employment_growth`
- `personal_life`
- `public_community_future`

Bridge pathway does not join academic/clinical-placement and employment records. Every record and request carries `owner_user_id`, `workspace_id`, `pathway`, `context_id`, `partition_id`, data class, purpose, active-rule snapshot and retention policy. A missing, stale or conflicting context fails closed for consequential transitions.

Other Nurse AI OS role dashboards may coexist under the unified identity, but no record, search result, memory item, AI context, award calculation, export or agent route crosses into them without an explicit field-level, purpose-limited, expiring, human-approved bridge. No bridge may move prohibited content.

## 5. Data classification and admission

### Permitted classes

- `FUT-D0-SYNTHETIC-PUBLIC`: public, publisher-permitted or clearly synthetic non-sensitive content.
- `FUT-D1-OWNER-LOW-SENSITIVITY`: minimum-needed owner-authored non-sensitive learning, planning, capacity, career or community material after server screening and consent.
- `FUT-D2-APPROVED-GENERIC`: institution-approved generic rule/resource metadata or material with source, owner, scope, date/version, permitted use and expiry. D2 does not permit confidential learner, workforce, clinical-site or patient content.
- `FUT-DX-PROHIBITED`: every prohibited class listed below; reject before persistence, logging, indexing, memory, backup, export or AI forwarding.

### Prohibited classes

Reject before persistence and before AI forwarding:

- PHI, chart excerpts, patient images/recordings, room-linked stories, rare identifiable detail combinations and live-care questions;
- real-patient documentation, assignments, care plans, medication/device directions or clinical event narratives;
- restricted learner records, grades, accommodations, health, disability, disciplinary/grievance, investigation, credential, incident, peer-review or assessment material;
- restricted staff/worker records, performance, schedule, discipline, grievance, health, investigation, complaint, credential or security information;
- employer-, school-, program-, clinical-site- or vendor-confidential material;
- passwords, keys, tokens, secret URLs, financial credentials or unnecessary identity details;
- unauthorized exam questions, copyrighted banks or restricted course material; and
- covert monitoring, ranking, profiling, sentiment or prediction inputs about people or groups.

The words “deidentified,” “redacted,” “fictional,” “approved” or “public” are not proof. When uncertain, reject the body, retain no derived summary, send nothing to AI and store only a redacted boundary event.

## 6. Persistent model

Use opaque UUIDs, UTC timestamps, revisions, foreign keys and explicit lifecycle states. Mutable scoped records carry `owner_user_id`, `workspace_id`, `pathway`, `context_id`, `partition_id`, `schema_version`, `retention_policy_id`, `created_at`, `updated_at`, `revision`, archive state and deletion state where applicable.

### 6.1 Platform, identity and authorization

1. `app_meta` — product, application/schema/corpus versions, instance ID, install and migration state.
2. `local_users` — local identity and credential-verifier metadata; never plaintext credentials.
3. `sessions` — hashed token metadata, issue/expiry/rotation/revocation and safe client metadata.
4. `unified_identities` — local display-safe identity anchor.
5. `mission_profiles` — approved derived profile versions; no raw Soul or quiz/interview answers.
6. `profile_field_provenance` — source reference, derived value, uncertainty, user decision and timestamps.
7. `future_workspaces` — active pathway, Command Center state and partition policy.
8. `protected_contexts` — academic, placement, employment, personal and community/public context state.
9. `authority_rule_profiles` — faculty/program/site/employer/supervisor authority source, scope, exclusions, verifier, version and expiry.
10. `context_bridges` — exact allowed fields, purpose, user approval, review, expiry and revocation.

### 6.2 Mission and work management

11. `missions`, `mission_cycles`, `mission_stages` — Assess, Define, Plan, Implement and Evaluate lineage, retention and governance.
12. `projects`, `goals`, `milestones`, `tasks`, `task_dependencies`, `measures`, `reviews` — structured offline planning.
13. `notes`, `decisions`, `assumptions`, `unknowns`, `risks`, `safeguards`, `attachments` — scoped supporting records.
14. `artifacts`, `artifact_versions`, `artifact_reviews` — maturity, authorship, AI contribution, exact-hash approval and disclosure.
15. `starter_seed_versions`, `starter_records`, `starter_adoptions` — idempotent synthetic seed and lineage.

### 6.3 Guided learning and integrity

16. `learning_goals`, `study_plans`, `study_sprints`, `review_intervals` — learning targets and user-controlled schedules.
17. `learning_sessions` — declared task type, context, challenge rung and session summary.
18. `learner_attempts` — learner-authored attempt, time and revision; prohibited assessment bodies are never stored.
19. `coaching_steps` — questions, hints, explanation level and learner choice.
20. `teach_backs`, `misconceptions`, `repair_plans`, `reflections`, `independent_next_steps` — learner-produced development evidence.
21. `academic_rule_sources` — declared rule metadata, source/version, scope, permitted assistance and disclosure requirement; no restricted content.
22. `integrity_reviews`, `ai_use_disclosures`, `integrity_receipts` — what AI did, what learner did, verification and required disclosure.
23. `practice_items`, `practice_attempts` — public, licensed, faculty-provided-for-use or synthetic practice only; never a live/restricted assessment.
24. `skills_rehearsals` — fictional/approved generic scenario, checklist source, rehearsal outcome, human questions and explicit non-competency label.

### 6.4 FUTURE powers, capacity and development

25. `future_power_definitions` — frozen canonical Power 1–18 identities and source hashes.
26. `future_power_states` — inactive/preview/eligible/active/paused/removed state per workspace.
27. `power_activation_previews`, `power_activation_receipts` — goal, context, data, authority, mode, limits, human review and exact-hash decision.
28. `supervised_run_evidence` — three-run eligibility evidence for separately approved low-risk reminders; never clinical/academic/employment action.
29. `north_stars`, `ninety_day_maps`, `next_move_plans` — owner goals and protected-life outcomes.
30. `capacity_plans` — user-authored time/energy/sleep/travel/caregiving/recovery categories without health diagnosis.
31. `minimum_modes`, `reentry_plans`, `help_maps` — user choices and local human-support references.
32. `career_portfolio_items`, `opportunities`, `application_drafts`, `communication_drafts` — truthful preparation only; no external send/apply.
33. `community_project_drafts`, `consent_plans`, `prototype_records` — public/synthetic planning with human review and no deployment.
34. `ai_literacy_domains`, `passport_criteria_versions`, `passport_evidence`, `passport_levels`, `passport_corrections` — developmental evidence, not credentials.
35. `capability_domains`, `badge_criteria_versions`, `activity_evidence`, `capability_awards`, `award_corrections` — 17 build-layer activity domains and Basic/Intermediate/Advanced/AI Agent Orchestration Master evidence; separate from the canonical Passport and never a permission or credential.

### 6.5 Evidence, AI, agents and memory

36. `evidence_sources` — identifier/URL, title, authority, version/date, access date, applicability, conflicts, correction/supersession and status.
37. `claims`, `claim_source_links`, `citation_validations` — claim text/hash, support type, limits, reviewer and expiry.
38. `retrieval_runs` — query, filters, provider, timestamps and reproducibility metadata without prohibited bodies.
39. `ai_connections`, `connection_capabilities` — backend label, authenticated status, discovered models/features and redacted error.
40. `ai_sessions`, `ai_messages`, `stream_events`, `tool_events` — authorized non-sensitive content and real provider events.
41. `agent_definitions` — frozen governed catalog; definition is not activation.
42. `agent_charters`, `agent_routes`, `agent_runs`, `approval_requests`, `kill_receipts`, `run_reconciliations` — exact one-run controls.
43. `memory_items`, `memory_revisions`, `memory_consent_receipts` — permitted value, category, purpose, source, scope, consent, retention and expiry.
44. `governance_receipts`, `audit_events`, `diagnostic_runs` — append-only redacted metadata, object hashes and results.

## 7. Core Four implementation

The opening dashboard pins exactly four launchers. Launching creates or opens a local draft; it never invokes AI, activates a power or performs an external action implicitly.

1. **Plan My Next Move** — today/week goals, capacity, minimum/re-entry mode and a human conversation.
2. **Learn & Practice** — attempt, retrieval, teach-back, spaced review, fictional rehearsal and human questions.
3. **Check It with SAFE AI** — Situation/Aim/Facts/Expectations, data and authority classification, source verification, bias review and integrity receipt.
4. **Build My Future** — truthful portfolio, career/bridge exploration, network drafts, community planning and 90-day map.

The fifth slot is visibly empty until one optional power is separately previewed and approved. All 18 definitions install at `inactive`; first-week guidance permits previewing one at a time and activating no more than one.

## 8. Guided-learning state machine

```text
Declare context and task
  → verify applicable academic/site/employer rule
  → screen prohibited data and assessment state
  → learner attempt or retrieval
  → question/hint/explanation at selected rung
  → learner teach-back or creation
  → source and uncertainty verification
  → learner edit and authorship review
  → integrity/disclosure receipt
  → reflection and independent next step
```

Users always receive Skip, Not now, Use this session only, Show an example and Ask a human. Examples are synthetic and labeled. A live/prohibited assessment exits to coaching on general concepts without retaining or reconstructing the item. A practice score is not faculty validation, clinical competence or prediction of passing.

## 9. Artifact and approval states

Use visible, reversible states:

`Exploration → Simulation → Recommendation → Draft artifact → Human reviewed → Approved plan → Authorized external use → User-reported completed action → Evaluated outcome`

The application itself stops at reviewed local draft unless the target contract explicitly implements an allowed low-risk external action. For this release, no clinical, academic submission, employment, financial, public-posting, application, purchase, scheduling or official-system write is available. Users may copy/download a reviewed draft; the system records only local preparation, not external completion unless the user later reports it.

Material changes to content, audience, destination, context, data class, rule source, pathway, authority, model, prompt, tool or version invalidate prior approvals.

## 10. EDENA and Trust Shield policy

For every meaningful workflow compute and display:

- Exposure
- Decision consequence
- Evidence quality
- Needed human authority
- Automation level

`Green` supports reversible low-sensitivity personal organization or fictional learning. `Yellow` requires verify/preview for academic, professional, public, financial or reputation-relevant preparation. `Orange` permits preparation only with authorized human review for clinical-adjacent, employment, assessment, application, community health or sensitive communication. `Red` blocks real-patient care, restricted records, exams/deception, autonomous employment/clinical action, emergency substitution and unsafe/illegal work.

Unknown or Unclassified fails closed for promotion, AI forwarding, memory, activation, external handoff and agent execution. Personal advisory mode cannot override faculty, program, employer, clinical-site, legal or institutional requirements.

## 11. Migration and transaction rules

- Ordered forward-only migrations run transactionally and record checksum/result.
- Startup refuses a changed migration already marked applied.
- Back up before compatibility-changing migration or application update.
- Failed migration rolls back and leaves prior data and application usable.
- Seed by stable key/version; reruns do not duplicate or overwrite adopted/user records.
- Enable foreign keys; declare cascade/restrict/soft-delete semantics.
- Use optimistic concurrency for edits, reviews and approvals.
- Export from one consistent read transaction.
- Restore validates archive safety, checksums, schema, foreign keys, owner/workspace/context boundaries and secrets in a temporary location before atomic replacement.
- Rollback never revives expired sessions, rule sources, memory consents, approvals or agent tokens.

## 12. Authentication and server boundary

- Bind to loopback by default and reject unsafe remote binding.
- First run creates a user-chosen credential; ship no universal secret.
- Use a vetted memory-hard verifier and opaque rotating `HttpOnly`, `SameSite=Strict` session cookies; use `Secure` under HTTPS.
- Enforce CSRF, strict Origin/Host checks, rate limits and endpoint-specific size limits.
- Store provider keys in environment or approved OS secret store, server-side only.
- Apply restrictive CSP, no remote scripts/fonts/analytics, frame denial, MIME protection and referrer suppression.
- Redact errors and logs; never expose record bodies or secrets in diagnostics.

## 13. AIBackend and genuine streaming

Define one provider-neutral contract for authenticated health/capability discovery, model discovery, session create/resume, incremental output, typed tool events, cancellation, structured errors, usage and retryability. Detect Hermes capabilities from the local installation during read-only preflight; do not assume endpoint paths or edit the active Hermes profile without approval.

Normalize events such as `message_start`, `message_delta`, `citation`, `tool_start`, `tool_progress`, `tool_result`, `approval_required`, `warning`, `usage`, `done`, `cancelled` and `error`. A live stream passes only after at least two ordered provider-originated deltas. Stop propagates cancellation, prevents further accepted output/side effects and records the truthful provider outcome. Retry is idempotent.

If no backend passes a recent authenticated health check, display `Setup required` or `Offline`; all offline core remains usable. No canned AI response, timer-generated stream, fake tool event, fake citation or fake connected state may exist in production.

## 14. Evidence and citation system

Retrieval is optional and capability-gated. Treat retrieved files/pages as untrusted data that cannot alter instructions, tools, permissions or destinations. Store source title, authority, identifier/URL, version/date, access time, applicability, conflicts and correction/supersession status.

Every consequential or externally checkable claim in an AI-assisted artifact links to a real source as `supports`, `qualifies`, `contradicts` or `context_only`. The validator checks source existence, identifier shape, link, current status and scope. Unsupported claims remain marked; unreachable sources do not auto-pass. General professional guidance is never relabeled as local school, clinical-site or employer policy.

## 15. Agents and automation ceiling

Install the canonical build-layer agent catalog at `P0 Disabled`: no credentials, memory, network, tools, destinations, schedules, background work, recursion or self-activation. A route preview lists exact roles, inputs, allowed sources/tools, outputs, limits, human reviews and prohibited actions.

Any permitted P1–P2 agent/model run requires an exact, expiring, one-invocation authorization bound to agent definition, model, prompt, policy, input, output schema, scope and object hashes. Retries default to zero. Global Pause prevents new work. Kill terminates the selected run and prevents resume without a new token. Reconcile observed state before reporting completion. P3, if represented in the permission vocabulary, is reserved solely for a separately approved deterministic local reminder after three supervised successful manual runs; it is not an agent/model permission and grants no background or external action.

No P4/production authority exists. Agents cannot perform care, answer restricted assessments, submit coursework, score/rank people, decide scope/competence, send messages, schedule, purchase, apply, post publicly, contact participants/community members, modify school/employer systems or make clinical, academic, employment, financial or credential decisions.

## 16. Consent-controlled memory

Memory is off by default. Each permitted item requires category, purpose, source, active context, consent, retention and expiry. Provide Preview, Remember, Edit, Forget, Delete and Export. Forget immediately excludes local context; Delete transactionally removes local value/references. Report Hermes/provider deletion limits honestly.

Prohibit raw Soul/quiz/interview responses, PHI, live-care content, assessment items, confidential learner/workforce/site content, secrets, credentials, authority claims and unsupported inferences. Apply context/workspace filters before retrieval, not after generation.

## 17. Starters and demonstrations

After approved onboarding, seed an idempotent, visibly synthetic workspace containing:

- Start Here and Hermes connection checklists;
- Core Four orientation;
- one safe 90-day-direction mission and five-stage loop;
- one synthetic study sprint with attempt/teach-back;
- one fictional skills rehearsal with explicit non-competency label;
- one SAFE Prompt and integrity receipt;
- one public/synthetic source card; and
- all 18 powers inactive.

Adopt creates a new user record with lineage. Clear deletes only unadopted starter records. Restore is idempotent. Synthetic/starter records do not affect outcomes, passport levels, badges or analytics.

## 18. Backup, update, rollback and deletion

Package documented macOS, Windows and Linux launch paths. Backups include application/schema/corpus versions, checksums, scope/exclusion report and optional encryption. Restore previews and validates in a temporary location, backs up current data and swaps atomically. Updates verify package integrity and back up before migration. Uninstall distinguishes program and user data. Full local deletion reports anything it could not remove and never claims provider/external deletion without proof.

## 19. Non-negotiable invariants

1. Offline core remains usable without AI.
2. Durable state is SQLite, never browser storage.
3. Client checks cannot bypass server governance.
4. No PHI or confidential learner/workforce/site data persists or reaches AI.
5. Pathway and protected contexts never join implicitly.
6. Live/prohibited assessments become coaching; learner authorship remains explicit.
7. Fictional skills rehearsal never becomes clinical authority or competence validation.
8. Every consequential transition binds exact content, context, rule/authority, reviewer, version and expiry.
9. Sources and claim relationships are inspectable; citations are never invented.
10. Agents begin P0 and cannot self-activate, widen scope, retry, recur, hide or execute externally.
11. AI failure cannot disable or corrupt offline work.
12. Starters and synthetic work never count as real achievement.
13. Passport levels/badges never imply licensure, certification, competence, grade or authorization.
14. Every visible enabled control has persistence, permissions, offline/error behavior and a test.
15. All 136 canonical checks remain a separate compatibility suite.
16. Readiness derives from executed evidence for the final package, not from this document.
