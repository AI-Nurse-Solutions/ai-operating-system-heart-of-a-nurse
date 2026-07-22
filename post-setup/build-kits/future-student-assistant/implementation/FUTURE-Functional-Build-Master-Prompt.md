# Resolved FUTURE Functional Build Contract

> This is the supplied Mission Control functional-build master prompt resolved for Nursing Student & Nursing Assistant FUTURE Mission Control. The original unchanged prompt is retained under `source/`. No real Discover Packet, Soul Quiz result, learner authority, school/employer policy, Hermes capability, or safe backend is assumed.

## Resolved target metadata

- Build-kit ID: `NAIO-FUTURE-FUNCTIONAL-BUILD-KIT-1.0.0`
- Target product ID: `future-nursing-student-assistant-mission-control`
- Target application version: `2.0.0`
- Build-layer population lane: `nursing_student_assistant`
- Build-layer route: `/nursing-students-assistants/dashboard`
- Canonical namespace: `future.*`
- Current target readiness: `not_operational_build_required`

The lane, route, home, agent IDs, workflow/template IDs, schemas, and permission model are implementation additions, not legacy identifiers. They may narrow but never widen the canonical source.

---

# Mission Control Dashboard — Functional Downloadable Build Master Prompt

You are the implementation engineer for **FUTURE — Nursing Student & Nursing Assistant Mission Control**, a downloadable Mission Control Dashboard built for a **Hermes + Nurse AI OS** environment.

Your mission is to transform the supplied Discover packet, Soul Quiz results, role selections, and any existing dashboard source into a genuinely operational, personalized, governed product—not a mockup, visual prototype, empty shell, or hosted-only demonstration.

Do not stop at planning, scaffolding, placeholder handlers, mocked AI responses, static cards, nonfunctional buttons, or simulated tool activity. Implement, test, package, and verify the complete working path.

The downloadable result must retain useful core functionality even when no AI backend is connected. AI-dependent features must use a genuine configured backend and show an honest setup-required or offline state when that backend is unavailable. Never disguise missing connectivity with canned responses.

---

## 1. Package context

- **Package:** FUTURE — Nursing Student & Nursing Assistant Mission Control
- **Product purpose:** A personalized Mission Control for managing goals, learning, projects, decisions, and continuous-improvement loops within the user’s Nurse AI OS.
- **Dashboard source:** source/baseline-application/ — immutable working UI/state-machine baseline; copy it before editing
- **Discover packet:** personalization/FUTURE-Discover-Packet.synthetic.example.json for shape only, or a user-supplied reviewed NAIO-DISCOVER-PACKET-ADAPTER-1 during first run; no real packet is bundled
- **Soul Quiz results:** personalization/FUTURE-Soul-Profile.synthetic.example.json for shape only, or a user-supplied reviewed NAIO-SOUL-PROFILE-ADAPTER-1 during first run; no raw answers or raw SOUL.md are bundled
- **Hermes profile:** AUTO_DETECT_ACTIVE_PROFILE_THEN_REQUIRE_USER_CONFIRMATION; expose only safe identity-loaded status, never raw SOUL.md
- **Primary user:** Nursing students, nursing assistants, patient care assistants or technicians, care aides, returning or bridge learners, and people preparing for nursing education, certification, career growth, responsible AI use, technology creation, leadership and community contribution
- **Selected role lanes:** One isolated nursing_student_assistant population lane with explicit Nursing Student, Nursing Assistant, or Bridge pathway; separate Learning, Work growth, Life, and Community/future protected spaces; Bridge academic and employment contexts never transfer silently
- **Domain:** FUTURE learner development: direction and capacity; deep learning and approved fictional rehearsal; evidence, privacy, academic integrity and SAFE AI; accessible technology and synthetic workflow design; truthful career growth; emerging leadership, community service and future-of-nursing exploration
- **Required agents:** FUT-AGT-01 Next Move & Capacity Planning Coach; FUT-AGT-02 Active Learning & Teach-Back Coach; FUT-AGT-03 Fictional Skills & Certification Rehearsal Coach; FUT-AGT-04 Evidence & Source Verification Scout; FUT-AGT-05 SAFE Prompt, Integrity & Boundary Sentinel; FUT-AGT-06 Synthetic Workflow & Accessible Prototype Coach; FUT-AGT-07 Career, Portfolio & Opportunity Coach; FUT-AGT-08 Communication, Teamwork & Emerging-Leadership Coach; FUT-AGT-09 Community & Future-of-Nursing Exploration Scout; FUT-AGT-10 Independent Agent Auditor & Kill Sentinel — all implementation-generated and installed PERM-P0 Disabled
- **Sensitive-data category:** Private learner OS by default: public/synthetic and minimum owner-authored nonsensitive content after screening; separately approved generic education/employer sources are read-only and context-bound; PHI, identifiable clinical stories, live care, restricted assessments, restricted school/employer/personnel content, secrets, financial credentials and unknown-classification data are rejected before persistence
- **Domain guardrails:** FUTURE Learner, Patient & Workforce Trust Shield + SAFE + EDENA + explicit pathway/protected-space/context/rule/human-authority gates + attempt-before-answer + academic-integrity and AI-use receipts + Bridge partition isolation + all powers Inactive, workflows Preview Only, agents P0 + no live care, scope/competency decisions, surveillance, external actions or background agents
- **Target operating systems:** Target macOS, Windows and Linux; claim support only for exact operating-system versions that pass clean-machine tests
- **Preferred distribution format:** Versioned ZIP containing a loopback-only local full-stack web application, locked source/dependencies, SQLite migrations, launchers, documentation, tests, manifest and checksums

Possible role lanes may include, but are not limited to:

- Pre-licensure nursing student or nursing assistant
- Bedside nurse or advanced-practice nurse
- Medical resident or physician
- Nurse educator
- Advanced studies, certification, or degree-seeking learner
- Charge nurse, nurse manager, clinic manager, or hospital administrator
- Quality, governance, research, or innovation leader
- Wellness or personal-life manager
- Entrepreneur, consultant, creator, or founder

A user may activate several complementary roles at the same time. Do not force one identity or one dashboard when the Soul Quiz indicates that the user wears multiple hats.

---

## 2. Non-negotiable product outcome

The completed download must include a working application, not merely a design or code sample. It must provide:

- A real first-run setup and personalization flow
- One or more dashboards generated from the user’s selected roles and approved Soul Quiz-derived profile
- A functional Assess → Diagnose/Define → Plan → Implement → Evaluate continuous-improvement loop
- Working project, mission, task, note, evidence, review, and progress controls
- Durable local persistence across refreshes, restarts, and application upgrades
- Seeded, personalized starter missions so the first screen is useful rather than empty
- A clear distinction between starter/example content and the user’s real records
- Genuine streamed AI responses when a backend is configured
- Hermes as the preferred AI backend
- An optional OpenAI-compatible backend
- Automatic, safe use of the active Hermes profile and its `SOUL.md`
- Transparent agent routing and a user-selectable agent override
- Persistent, consent-controlled memory
- Real evidence retrieval with traceable, validated citations when retrieval is configured
- Authentication and server-side secret management
- Nurse AI OS and domain-specific governance controls
- A Guide page and contextual help throughout the product
- A real achievement system with four levels: **Basic, Intermediate, Advanced, and AI Agent Orchestration Master**
- Honest setup, connection, limited-capability, failure, and offline states
- An installable or reproducibly runnable local package with complete instructions
- No canned AI responses, simulated tool calls, decorative controls, or runtime placeholders

The product may contain intentionally read-only informational elements, but every element styled as an interactive control must perform its stated action.

---

## 3. What “functional when downloaded” means

### 3.1 Core functions must work without an AI connection

Immediately after installation and first-run setup, the user must be able to:

- Create, view, edit, archive, restore, and delete missions and projects
- Enter and revise content in every stage of the improvement loop
- Add goals, milestones, tasks, due dates, priorities, owners, notes, attachments, reflections, and evaluation measures
- Move work through valid states
- Reopen a completed loop when evaluation shows that another cycle is needed
- Use filters, search, sort, navigation, and dashboard controls
- Save and recover work after closing and reopening the application
- Export and import their permitted dashboard data
- View progress and earned badges based on real saved activity
- Read the Guide and setup documentation
- View an honest AI setup-required or offline state

These capabilities must not depend on API keys, internet access, or a running model.

### 3.2 AI functions must never be simulated

AI-dependent controls may become available only when a real backend passes health and capability checks. When no backend is available:

- Disable or clearly mark AI-only actions.
- Explain what is needed to activate them.
- Preserve all non-AI functionality.
- Never display canned completions, delayed sample text, fake citations, fake agents, fake progress events, or fabricated tool results.

### 3.3 The package must not open as an empty shell

After the user completes onboarding, automatically create:

- A personalized home dashboard
- A safe derived mission profile approved by the user
- A role workspace for each activated role lane, or a clearly designed shared workspace when roles overlap
- One editable starter mission per active role
- A first continuous-improvement loop with suggested but editable outcomes, measures, and next actions
- A short “Start Here” checklist
- A visible connection/setup checklist for Hermes and optional services
- Initial badge progress derived from completed onboarding actions

Starter records must be labeled **Starter content** until the user adopts or deletes them. Provide **Clear starter content** and **Restore starter content** controls. Do not mix starter content into analytics as if it were completed real work.

If Soul Quiz results are unavailable, onboarding must collect the minimum information needed to create a useful dashboard. Do not silently invent personal values, goals, credentials, preferences, or risk tolerance.

### 3.4 The download must be self-contained and reproducible

Deliver the actual application source and all files needed to install and run it, including:

- Locked dependency manifest
- Database schema and migrations
- Safe seed process
- `.env.example` containing variable names only
- First-run wizard or setup command
- Health-check or diagnostic command
- Development and production start commands
- Build command
- Test command
- Backup, export, import, and uninstall guidance
- A concise README for a non-developer user
- Technical documentation for an implementer
- Platform-specific launch helpers where required

Do not make successful use depend on undocumented manual edits.

---

## 4. Phase 0 — inspect and verify before editing

Before implementation:

1. Locate the actual application source.
2. Confirm its framework, package manager, runtime, data layer, deployment configuration, supported operating systems, and tests.
3. Identify every interaction currently using a mock, placeholder, timer, static response, fabricated tool result, dead link, or no-op handler.
4. Create a control inventory that maps every clickable or editable interface element to its real implementation and verification test.
5. Preserve the existing product design unless a change is required for functionality, safety, accessibility, or clarity.
6. Check the installed Hermes version and active package profile.
7. Discover Hermes capabilities through the available health, models, capabilities, sessions, and AI endpoints. Do not hardcode capabilities without checking.
8. Inspect the Discover packet and Soul Quiz schema before designing personalization mappings.
9. Identify existing user changes and preserve unrelated work.
10. Identify operating-system, browser, packaging, database, and migration constraints.
11. Record all prerequisites that cannot be bundled legally or securely.

If the actual application source is missing, stop and state exactly what source package or repository access is required. Do not reconstruct the product from screenshots.

If live Hermes is not available during implementation, the core local application must still be built and tested. AI integration may use a test double only inside automated tests; production runtime code must never substitute it for a missing backend. Do not claim the AI path is operational until a real streamed response has passed end to end.

---

## 5. Personalization from the Discover packet and Soul Quiz

Map the approved results into a versioned, user-editable **Mission Profile**. The mapping may include:

- Active roles and the relationship among them
- Purpose, priorities, and desired outcomes
- Values and non-negotiable boundaries
- Preferred working, learning, and communication styles
- Current capabilities and desired capabilities
- Near-, medium-, and long-term goals
- Constraints, responsibilities, available time, and preferred cadence
- Governance preferences and risk tolerance
- Topics the system should remember and topics it must not remember
- Visual-density and accessibility preferences
- Desired agent support and permitted levels of autonomy

Requirements:

- Show the proposed mapping before saving it.
- Require user approval before persisting derived profile fields.
- Let the user edit, reject, regenerate, export, or delete the derived profile.
- Preserve provenance: original input, derived field, approval status, and last-updated time.
- Store only fields required for the product.
- Do not treat a personality inference as fact.
- Do not infer licensure, competence, authority, diagnosis, or employment status.
- Keep role workspaces distinct where privacy, safety, or cognitive clarity requires separation.
- Allow the user to add, pause, merge, or retire role dashboards later.

The Mission Profile personalizes the dashboard; it does not silently redefine the user’s Hermes identity.

---

## 6. Mission Control information architecture

At minimum, implement these working areas:

### Home / Command Deck

- Current priorities
- Active missions
- Next actions
- Upcoming reviews
- Alerts and blockers
- Connection and governance status
- Recent progress
- Role selector
- Agent selector
- Quick capture
- Continue-last-session action

### Mission Workspace

- Mission statement and desired outcome
- Scope and boundaries
- Current phase
- Evidence and assumptions
- Measures of success
- Milestones and tasks
- Decision log
- Risks and safeguards
- Timeline and review cadence
- Activity history

### Continuous-Improvement Loop

Implement these as real stateful stages rather than static labels:

1. **Assess** — capture the current state, known facts, stakeholder needs, constraints, baseline measures, and research questions.
2. **Diagnose / Define** — identify the problem, opportunity, root causes, uncertainties, and working hypotheses without presenting unsupported conclusions as facts.
3. **Plan** — define outcomes, interventions, owners, resources, measures, safeguards, milestones, and stop or escalation conditions.
4. **Implement** — execute permitted tasks, document actions, track changes, surface blockers, and require confirmation for consequential actions.
5. **Evaluate** — compare outcomes with baseline and targets, record lessons, decide whether to close, sustain, revise, escalate, or begin another cycle.

Each stage must support save, edit, history, evidence, attachments or references, AI assistance when connected, and a human confirmation checkpoint.

### Evidence Center

- User-supplied sources
- Retrieved sources
- Claim-to-source mapping
- Appraisal or confidence status
- Verification queue
- Citation export

### Agent Console

- Available agents
- Selected agent and reason
- Agent scope and prohibited actions
- Current session
- Tool activity
- Pending approval requests
- Stop/cancel control

### Progress and Badges

- Competency or activity domains
- Current level and next criteria
- Evidence of completed criteria
- Date earned
- Revocation or correction history where applicable
- Exportable achievement record

### Memory and Data Controls

- What is remembered
- Why it is stored
- Source and creation time
- Retention period
- Edit, forget, delete, and export controls
- Temporary workspace cleanup

### Guide

- First-run instructions
- How the improvement loop works
- How role dashboards work together
- What agents can and cannot do
- How Hermes, the Soul, memory, and Mission Profile differ
- How evidence and citations work
- How badges are earned
- How to connect, disconnect, back up, export, import, update, and recover
- Safety, privacy, and human-accountability guidance
- Troubleshooting and diagnostic steps

### Setup and Diagnostics

- Application status
- Local database status
- Backend health
- Connected Hermes profile
- Available model
- Streaming capability
- Session capability
- Soul detected
- Memory availability
- Tool availability
- Retrieval availability
- Authentication status
- Version and migration status
- Last successful connection
- Last connection error, safely redacted

Do not reveal secrets or raw `SOUL.md` content.

---

## 7. State model and persistent local data

Use a durable local data layer appropriate to the inspected application. Prefer a server-side local database such as SQLite for a local full-stack application unless the existing architecture has a justified equivalent.

At minimum, model:

- User and local authentication state
- Mission Profile and user approvals
- Role workspaces
- Missions and projects
- Improvement-loop cycles and stages
- Goals, milestones, tasks, measures, and reviews
- Notes, decisions, assumptions, risks, and safeguards
- Evidence records and citation metadata
- Agent sessions and routing metadata
- Consent-controlled structured memory
- Badge criteria, activity evidence, progress, and awards
- Connection capabilities and safe diagnostics
- Audit events without sensitive message bodies
- App version and migration status

Requirements:

- Persist across browser refresh, process restart, and computer restart.
- Use schema migrations rather than destructive reinitialization.
- Make seed operations idempotent.
- Never overwrite real user data when restoring starter content.
- Provide export, backup, restore, and complete local deletion.
- Validate imported data and reject malformed or unsafe records.
- Keep temporary sessions separate from durable data.
- Handle interrupted writes and failed migrations safely.
- Do not use browser storage for provider secrets.
- Do not claim that data is durable if it exists only in in-memory state.

---

## 8. Backend architecture

Create one `AIBackend` interface with interchangeable adapters. It should support:

- Health checks
- Capability discovery
- Model discovery
- Session creation and resumption
- Streamed responses
- Tool-progress events
- Cancellation
- Conversation history
- Structured errors
- Usage metadata when available

### Hermes adapter

Use the package’s installed Hermes profile.

Expected private configuration:

```dotenv
AI_BACKEND=hermes
HERMES_BASE_URL=http://127.0.0.1:8642
HERMES_API_KEY=<server-side secret>
APP_ACCESS_SECRET=<strong local access secret>
```

Requirements:

- Discover the available model instead of hardcoding it.
- Prefer Hermes’ session-aware streaming API when supported.
- Fall back to an available OpenAI-compatible streaming endpoint when necessary.
- Put a server-side proxy between the browser and Hermes.
- Never expose `HERMES_API_KEY` to client code.
- Bind locally by default.
- Do not make a publicly hosted page attempt to contact the user’s localhost Hermes service.
- Provide a local operational build when connecting to a local Hermes instance.
- Report capability limitations honestly and adapt the interface accordingly.

### OpenAI-compatible adapter

Support another compatible backend through:

```dotenv
AI_BACKEND=openai-compatible
AI_BASE_URL=<provider URL>
AI_API_KEY=<server-side secret>
AI_MODEL=<model identifier>
```

Keep provider-specific logic inside the adapter. The rest of the application must not depend on a particular provider.

---

## 9. Hermes profile, Soul, and Mission Profile boundaries

The installed Hermes profile owns its `SOUL.md`; Hermes should load that file as its identity.

Therefore:

- Do not upload the Soul through the dashboard during normal operation.
- Do not append the entire Soul to every request.
- Do not duplicate it in application storage.
- Do not expose its contents through diagnostics, logs, exports, or browser APIs.
- Display only a safe status such as **Soul identity loaded**.
- Layer package, role, mission, and agent instructions on top of the Hermes identity.
- Never let package instructions silently replace the user’s Soul.
- Keep the user-approved Mission Profile distinct from the Soul.

When using an external provider instead of Hermes, require explicit, informed consent before sending the raw Soul or a derived identity profile outside the local environment. Default to sending only the minimum approved context needed for the current task.

---

## 10. Genuine streaming and tool visibility

Remove every canned or simulated AI response. Implement:

- Incremental streamed rendering
- Tool-start, progress, completion, and failure indicators
- Stop-generation control
- Retry
- Reconnection handling
- Stream error recovery
- Accessible status announcements
- Conversation persistence
- Clear separation of assistant text, tools, citations, safety warnings, approval requests, and errors

When the backend is unavailable, show an honest disconnected state. Never substitute a fake response.

---

## 11. Agent routing

Implement the package’s agent team from `FUT-AGT-01 Next Move & Capacity Planning Coach; FUT-AGT-02 Active Learning & Teach-Back Coach; FUT-AGT-03 Fictional Skills & Certification Rehearsal Coach; FUT-AGT-04 Evidence & Source Verification Scout; FUT-AGT-05 SAFE Prompt, Integrity & Boundary Sentinel; FUT-AGT-06 Synthetic Workflow & Accessible Prototype Coach; FUT-AGT-07 Career, Portfolio & Opportunity Coach; FUT-AGT-08 Communication, Teamwork & Emerging-Leadership Coach; FUT-AGT-09 Community & Future-of-Nursing Exploration Scout; FUT-AGT-10 Independent Agent Auditor & Kill Sentinel — all implementation-generated and installed PERM-P0 Disabled`.

Create:

- One shared Nurse AI OS package-governance prompt
- One bounded instruction profile per agent
- A deterministic, testable routing policy
- A visible selected-agent indicator
- A user override
- Per-turn routing metadata
- Independent sessions where separation is useful
- An explanation of why an automatic route was selected

Routing rules:

- Explicit user selection always wins unless safety policy prohibits the requested action.
- Product modules may choose a documented default agent.
- Automatic routing must be explainable.
- Agents must not silently broaden their roles, access, or authority.
- Changing the selected agent must change actual instructions and behavior, not only the interface label.
- Role context must not grant professional authority that the user does not possess.

---

## 12. Consent-controlled memory

Separate conversational memory from structured application memory.

### Hermes memory

Use Hermes sessions and profile memory for durable preferences and longitudinal context when enabled by the user.

### Structured application memory

Store only product-relevant information approved by the user.

Requirements:

- Explicit consent before saving
- A per-item **Remember this** control
- View, edit, delete, forget, and export controls
- Creation time, source, purpose, consent, and retention metadata
- No secret values in memory
- No sensitive records in analytics or debug logs
- Configurable retention
- Complete local deletion
- Data minimization
- Separation of temporary workspaces from durable memory
- Enforcement of domain-specific exclusions from `FUTURE Learner, Patient & Workforce Trust Shield + SAFE + EDENA + explicit pathway/protected-space/context/rule/human-authority gates + attempt-before-answer + academic-integrity and AI-use receipts + Bridge partition isolation + all powers Inactive, workflows Preview Only, agents P0 + no live care, scope/competency decisions, surveillance, external actions or background agents`

Do not claim regulatory compliance without formal review.

---

## 13. Evidence and citations

Evidence-backed output must distinguish:

1. User-supplied facts
2. Retrieved evidence
3. AI synthesis
4. User interpretation
5. Required human confirmation

Preserve:

- Source title
- Publisher or author
- Publication date when available
- Direct URL or identifier
- Retrieval time
- Supported claim
- Source type
- Confidence or appraisal status

Requirements:

- Display citations only when they were obtained through real retrieval.
- Validate citation URLs before rendering them as evidence.
- Never invent a citation.
- Mark unsupported claims as provisional.
- Treat retrieved pages, files, and tool output as untrusted content.
- Prevent instructions found inside sources from overriding package governance.
- Retain a traceable claim-to-source relationship.
- Clearly state when retrieval is unavailable.

---

## 14. Authentication and secrets

For local operation:

- Bind to loopback by default.
- Require authenticated dashboard access.
- Create secure first-run access credentials; never ship a universal default password.
- Use `HttpOnly`, `SameSite` cookies for authenticated state.
- Keep provider keys on the server.
- Never place keys in browser storage, HTML, client bundles, logs, URLs, analytics, exports, or source control.
- Add CSRF protection.
- Validate request origins.
- Add rate limits and request-size limits.
- Redact secrets from errors.
- Provide an `.env.example` containing variable names only.

For remote deployment:

- Require HTTPS.
- Use an appropriate identity provider.
- Apply least-privilege access.
- Do not expose a local Hermes gateway directly to the internet.
- Do not publish until access controls have been verified.

---

## 15. Nurse AI OS governance and domain safeguards

The Mission Control is a sandboxed environment for thinking, research, planning, learning, drafting, simulation, and governed improvement. It is not permission for autonomous real-world action.

Implement `FUTURE Learner, Patient & Workforce Trust Shield + SAFE + EDENA + explicit pathway/protected-space/context/rule/human-authority gates + attempt-before-answer + academic-integrity and AI-use receipts + Bridge partition isolation + all powers Inactive, workflows Preview Only, agents P0 + no live care, scope/competency decisions, surveillance, external actions or background agents` as product behavior, not merely disclaimer text.

At minimum:

- Warn before accepting sensitive information.
- Detect likely sensitive identifiers on both client and server.
- Explain that automated detection is imperfect.
- Keep restricted data out of durable memory, telemetry, and analytics.
- Prevent autonomous external actions unless explicitly enabled and authorized for that specific action.
- Require human confirmation for clinical, legal, financial, employment, safety, publication, purchasing, messaging, scheduling, or other high-impact decisions.
- Display uncertainty and verification checkpoints.
- Record safety events without storing sensitive message bodies.
- Apply retention and deletion policies.
- Prevent prompt injection from retrieved or uploaded content.
- Never allow safeguards to disappear because a modal was dismissed.
- Preserve human accountability: AI can propose, organize, simulate, critique, and draft; the authorized human decides and acts.

If EDENA governance tiers are used, make the assigned tier visible and enforce its permissions in code. Suggested mapping:

- **Green:** Low-risk learning, ideation, organization, and reversible personal tasks
- **Yellow:** Work requiring review, evidence checks, or bounded data handling
- **Orange:** High-impact or sensitive work requiring explicit human approval and stronger controls
- **Red:** Prohibited, unauthorized, or unsafe actions that the system must block and explain

The same action must receive the same governance behavior regardless of which page or agent initiates it.

---

## 16. Product integration: no decorative interactivity

For every interactive control:

1. Identify its intended local action, agent, or workflow.
2. Connect it to a real implementation.
3. Validate inputs on client and server where applicable.
4. Persist only permitted state.
5. Stream genuine AI results when applicable.
6. Expose genuine tool activity.
7. Surface verified citations when applicable.
8. Handle cancellation, retry, timeout, and failure.
9. Provide accessible feedback for success and error.
10. Remove the previous mock or no-op implementation.
11. Add a test proving the control works.

Maintain a control-completeness matrix containing:

- Screen
- Control
- Intended behavior
- Implementation location
- Persisted data
- Required permission
- Offline behavior
- Error behavior
- Verification test
- Status

Before handoff, there must be zero unresolved controls marked placeholder, mock, TODO, coming soon, or unverified unless the user explicitly approved their removal from scope. Do not leave nonfunctional controls visible.

---

## 17. Achievement and badging system

Badges must reflect real evidence, not button clicks or arbitrary AI judgments.

Implement four levels:

1. **Basic**
2. **Intermediate**
3. **Advanced**
4. **AI Agent Orchestration Master**

Requirements:

- Define observable criteria for each level and activity domain.
- Calculate progress from saved, auditable events.
- Require human verification where competence cannot be established by application activity alone.
- Distinguish participation, knowledge, demonstrated skill, and formally verified competence.
- Never imply licensure, certification, employer authorization, or clinical privileging.
- Show why a badge was earned and what remains for the next level.
- Recalculate correctly after eligible records are deleted or corrected.
- Provide a portable export compatible with a future verifiable-credential or Open Badges implementation where feasible.

---

## 18. Connection and capability states

Add a global connection indicator supporting:

- Connected
- Connecting
- Setup required
- Offline
- Authentication failed
- Hermes unavailable
- Provider unavailable
- Limited capabilities
- Reconnecting

The interface must derive these states from real checks, not timers or assumptions. A connected status must mean that an authenticated health/capability check has succeeded recently.

---

## 19. Installation, launch, update, and recovery

Provide a first-run experience suitable for the intended user, including:

1. Verify system prerequisites.
2. Initialize or migrate the local database safely.
3. Create local access credentials.
4. Import or collect Discover and Soul Quiz results.
5. Preview and approve the derived Mission Profile.
6. Detect Hermes and the active profile without exposing the Soul.
7. Configure an optional compatible backend if Hermes is unavailable.
8. Run backend health and capability checks.
9. Generate personalized role dashboards and starter missions.
10. Confirm local save, reload, export, and restore behavior.
11. Present the Start Here checklist.

Also provide:

- A one-command or one-click normal launch path after setup
- Clear application and data locations
- Safe update instructions that preserve user data
- Backup before migration
- Recovery from a failed update
- Diagnostics that do not expose secrets or raw Soul content
- Uninstall instructions that distinguish removing the application from deleting user data

Tell the user during installation that setup, model detection, dependency installation, migration, indexing, and initial personalization may take several minutes. Show real progress and current activity rather than an indefinite spinner or fabricated percentage.

---

## 20. Testing requirements

Add and run:

- Unit tests for all state transitions in the improvement loop
- CRUD and persistence tests for missions, projects, tasks, and notes
- Refresh and restart persistence tests
- Database migration, backup, restore, export, and import tests
- Starter-content creation, clearing, and restoration tests
- Multi-role workspace isolation and switching tests
- Mission Profile consent, edit, and deletion tests
- Agent-routing tests
- Authorization tests
- Secret-exposure tests
- Streaming-parser tests
- Cancellation tests
- Reconnection tests
- Backend-adapter contract tests
- Test-only Hermes integration tests
- Session create, resume, and failure tests
- Memory consent and deletion tests
- Citation-validation tests
- Domain-safeguard and EDENA-tier tests
- Sensitive-identifier handling tests
- Prompt-injection tests
- Badge calculation and evidence tests
- Accessibility checks
- Keyboard-navigation and screen-reader status tests
- Production build and type checks
- Clean-machine installation test for every supported operating system
- First-run onboarding test
- End-to-end test for a genuine streamed response
- End-to-end test proving canned responses are gone
- End-to-end test proving core features work while AI is offline
- Automated scan proving no visible interactive control lacks an implementation or explicit disabled state

If a live Hermes gateway is available, perform at least one real smoke test using safe, nonsensitive content.

Automated tests may use mocks only in the test environment. Production runtime paths must never fall back to those mocks.

---

## 21. Acceptance criteria

The implementation is complete only when all applicable criteria pass:

1. A clean download can be installed or started by following the included instructions.
2. First-run onboarding creates a useful personalized dashboard rather than an empty page.
3. The user can create, edit, advance, evaluate, reopen, archive, and delete a mission loop without AI.
4. Saved work survives refresh and full application restart.
5. Starter content is clearly labeled, editable, removable, and excluded from real achievement analytics until adopted.
6. Every visible interactive control works or is explicitly disabled with an accurate reason.
7. No runtime placeholder, canned response, simulated tool call, fabricated citation, or fake progress indicator remains.
8. The dashboard streams a genuine backend response when a backend is configured.
9. Tool activity is distinguishable from assistant text.
10. Cancellation works.
11. Authorized sessions resume after refresh.
12. Agent selection changes real instructions and behavior.
13. Hermes uses the profile’s Soul without exposing or duplicating it.
14. Evidence responses contain retrieved, working citations.
15. Unsupported claims never receive fabricated citations.
16. Memory requires consent and can be inspected, edited, exported, forgotten, and deleted.
17. Restricted data is excluded from durable memory and analytics.
18. Unauthorized requests are rejected.
19. No API key appears in client code, logs, browser storage, URLs, or exports.
20. Backend outages create an honest disconnected state while core local functions remain usable.
21. Multiple role dashboards preserve appropriate separation and share only user-approved context.
22. Badge progress is calculated from real, reviewable evidence.
23. Data export, backup, restore, and complete deletion work.
24. The application remains responsive, keyboard-accessible, and understandable to its intended users.
25. Installation, diagnostics, production build, and all required tests pass.
26. A real user can complete this full path: install → onboard → personalize → create a mission → complete an improvement stage → save → restart → resume → connect Hermes → receive a streamed response → stop a response → inspect evidence and memory controls.

Any failed criterion must be reported as a blocker. Do not relabel a failed or untested criterion as a future enhancement.

---

## 22. Required deliverables

Deliver:

- Complete working source
- Installable package or reproducible local build
- Database schema and migrations
- Safe seed and starter-content logic
- Backend adapters
- Agent and governance profiles
- Automated test suite
- Control-completeness matrix
- Security and privacy checklist
- User Guide
- Technical README
- `.env.example` without values
- Change log
- Known limitations and production-readiness report

Do not deliver only screenshots, a hosted preview, design files, or generated source fragments.

---

## 23. Final handoff report

When finished, report:

- Downloadable package path and checksum
- Supported operating systems and tested versions
- Local application URL or desktop launch method
- Command used to start the Hermes profile gateway
- Command used to start the application
- Required environment-variable names without values
- Data and backup locations
- Selected AI API surface and why
- Agent-routing design
- Mission Profile mapping and approval flow
- Memory location and controls
- Citation-verification method
- Enforced Nurse AI OS and domain safeguards
- Authentication model
- Control-completeness result
- Installation and clean-machine test result
- Production build and automated test results
- Real Hermes end-to-end smoke-test result
- Remaining blockers before production use

End with one of these exact readiness statements:

- **Operational:** All acceptance criteria passed, including a genuine end-to-end streamed response through the downloaded application.
- **Core operational; AI setup pending:** All offline/core acceptance criteria passed, but a live configured backend was not available for the genuine-streaming acceptance test.
- **Not operational:** One or more core acceptance criteria failed; list each blocker.

Never describe the package as fully operational until a genuine streamed response has passed end to end through the installed or downloaded interface.

