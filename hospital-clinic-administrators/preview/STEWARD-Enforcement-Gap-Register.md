# STEWARD Enforcement Gap Register

**Status:** Active design backlog · no runtime authorization
**Version:** 2026.07.16-preview.1
**Applies to:** Proposed STEWARD Hospital & Clinic Administration architecture

This register translates the independent review into implementation gates. Closing a documentation item does not close an enforcement gap. Each gap requires an implementation artifact, executable test, evidence receipt, independent review, and explicit human disposition.

## Decision vocabulary

- **KEEP** — doctrine is retained.
- **REVISE** — design remains but requires correction.
- **PAUSE** — implementation or claim cannot proceed yet.
- **STOP** — prohibited in the base architecture.

## Current release decision

| Item | Decision | Current evidence |
|---|---|---|
| STEWARD doctrine | KEEP | Source and independent governance review |
| One lane with context variants | KEEP | Coherent population, route, namespace, and authority model |
| Public governance preview | KEEP | Non-executable specification with explicit nonclaims |
| Installable Complete AI OS claim | PAUSE | No enforceable adapter or completed runtime ledger |
| Institutional deployment | PAUSE | No authenticated, validated deployment environment |
| PHI or sensitive organizational data | STOP | No pre-model ingress control or approved data environment |
| Consequential actions | STOP | Categorical human-authority boundary |

## Gap register

| ID | Priority | Gap | Risk if unresolved | Required implementation evidence | Current state |
|---|---|---|---|---|---|
| STW-G01 | Critical | Controls are prose rather than enforced runtime policy | Users may mistake requirements for protection | Versioned Florence-X/EDENA adapter; executable policy; adversarial tests; independent release receipt | Open |
| STW-G02 | Critical | No pre-model PHI/sensitive-data control | Prohibited data may reach a model before refusal | Pre-ingress classification/deny layer; provider-routing rules; false-negative evaluation; non-retaining block receipts | Open |
| STW-G03 | Critical | Memory, retention, purge, rollback, and uninstall are unproven | Data may persist in logs, provider systems, backups, or orphan state | Provider contracts; local state map; deletion adapters; backup policy; purge/rollback/uninstall probes | Open |
| STW-G04 | Critical | Real-incident pathways conflict with aggregate/process-only boundary | Shadow incident, patient, workforce, privileged, or legal records | Remove event intake from base; synthetic-only fixture contract; separate future governed product if justified | Open |
| STW-G05 | High | Authority is self-declared rather than authenticated | Institutional-looking outputs may be produced without valid delegation | Identity-provider binding; signed/verifiable delegation; source and expiry; revocation; authority-conflict tests | Open |
| STW-G06 | High | Requester, approver, and executor separation is not enforced | Self-approval and concentrated authority | Authenticated principals; role constraints; mandatory independent approval by risk tier; segregation tests | Open |
| STW-G07 | High | Whole-life, professional development, delegation, and succession are structurally mixed | Personal data may enter institution-governed workforce processes | Separate schemas, stores, keys, access policies, retention, UI, exports, and cross-domain denial tests | Open |
| STW-G08 | High | Aggregate controls are free text | Small groups and repeated queries can re-identify people | Minimum cohort rules; complementary suppression; differencing/longitudinal controls; rare-category handling; re-identification tests | Open |
| STW-G09 | High | The categorical consequential-action prohibition is documented but not runtime-enforced | Prohibited conduct may be staged, transmitted, or executed despite the policy | One categorical prohibition model in runtime; destination denylist; action-class tests | Open |
| STW-G10 | High | Tools, connectors, and destinations lack capability typing | Least privilege and non-authoritative destinations cannot be proven | Typed capability registry; allowlists; capability tokens; deny-by-default adapter; destination verification | Open |
| STW-G11 | Medium | Daily-management language can create a shadow command/task system | AI-generated assignment or closure may transfer responsibility | Official-system reference-only model; human-designated owner/status; no task creation; reconciliation tests | Open |
| STW-G12 | Medium | Listening and psychological-safety artifacts can become surveillance proxies | Retaliation, chilling effects, hidden workforce monitoring | Voluntary participation; purpose limits; labor/workforce review; anti-retaliation controls; aggregation and retention enforcement | Open |
| STW-G13 | Medium | Schema declarations are Markdown, not executable contracts | Runtime data can drift or accept prohibited fields | Versioned JSON Schema or equivalent; closed enums; fixtures; migration rules; validator tests | Open |
| STW-G14 | Medium | The 160 criteria have no completed evidence ledger | Release status cannot advance beyond blocked | Automated test harness; per-criterion evidence; timestamps; versions; reviewer; limitations; signed final ledger | Open |
| STW-G15 | Medium | Accessibility and human-factors controls are untested | Administrators may misread risk, status, authority, or stop controls | Keyboard/screen-reader/contrast tests; fatigue and interruption scenarios; comprehension testing | Open |
| STW-G16 | Medium | No institution-specific legal/privacy/security/workforce review model | Reference safety may be mistaken for local authorization | Deployment dossier template; accountable owners; counsel/privacy/security/workforce/clinical sign-offs; expiry | Open |

## Proposed implementation sequence

### Phase A — Specification and synthetic fixtures

- Freeze terminology and categorical prohibitions.
- Split whole-life, development, delegation, and succession domains.
- Remove real-incident intake from the base design.
- Define executable schemas using synthetic fixtures only.
- Define claim-versus-proof and evidence-ledger formats.

**Exit evidence:** schema validation, prohibited-field tests, source integrity, independent documentation review.

### Phase B — Local reference adapter

- Implement deny-by-default profile configuration.
- Implement pre-model screening using synthetic adversarial fixtures.
- Implement typed tools/destinations with no production connectors.
- Implement authenticated test identities and segregation-of-duties simulation.
- Implement local retention, purge, rollback, and uninstall probes.

**Exit evidence:** completed local test ledger; no PHI or organizational data; independent red-team review.

### Phase C — Institution-governed pilot design

- Select one bounded, low-consequence workflow.
- Establish institution-specific identity, delegation, contracts, data, access, logging, retention, incident response, manual fallback, and accountable owners.
- Include privacy, security, workforce/labor, legal, clinical, accessibility, and operational review.
- Prohibit production actions and consequential decisions.

**Exit evidence:** formal pilot authorization for the exact workflow and environment. Reference-adapter evidence alone is insufficient.

### Phase D — Categorical prohibited boundary

The base STEWARD architecture will not perform, stage, execute, or transmit clinical, employment, credentialing, financial, contracting, legal, policy, security, emergency, incident-closure, or official-record actions. Human review or approval does not convert any of these prohibited functions into an allowed STEWARD capability.

## Evidence receipt required to close any gap

Every closure must record:

- gap ID;
- implementation artifact and exact version;
- test method and fixtures;
- expected and actual result;
- accountable owner;
- independent reviewer;
- limitations and residual risk;
- dependencies;
- approval scope;
- approval timestamp;
- expiry or revalidation trigger;
- rollback disposition.

## Smallest next step

Build and test one synthetic, local-only **authority-and-data preflight adapter** that:

1. accepts no free-form operational narrative;
2. binds a test identity to one explicit context variant;
3. rejects prohibited data classes before any model call;
4. emits a machine-readable Pass/Question/Block receipt;
5. performs no connector, write, scheduling, messaging, or external action.

This is the smallest credible bridge from STEWARD doctrine to Florence-X/EDENA enforcement.
