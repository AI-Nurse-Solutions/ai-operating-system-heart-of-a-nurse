# FUTURE Capability, Passport, and Badge Evidence Model

## Two complementary systems

FUTURE presents two systems without blending their meanings:

1. **Canonical AI Literacy Passport** — six domains and five developmental stages from the v1 FUTURE corpus.
2. **Mission Control Capabilities & Mastery** — 17 activity domains using the functional build contract's four levels: Basic, Intermediate, Advanced, and AI Agent Orchestration Master.

Both are evidence-linked development records. Neither is a grade, course credit, certification, licensure, clinical competence finding, employment authorization, delegation, privilege, or permission to practice. “Master” means the user demonstrated governed AI-agent orchestration inside this sandbox; it does not mean mastery of nursing or patient care.

The normative build-layer criteria are in `config/FUTURE-Capability-Mastery-Criteria.v1.json`. Human-readable descriptions here cannot silently weaken that file.

## Canonical AI Literacy Passport

Domains:

1. Privacy and data judgment
2. SAFE prompting
3. Source verification
4. Fairness and integrity
5. Human authority and escalation
6. Workflow design and recovery

Stages:

1. Explorer
2. Safe User
3. Verified Creator
4. Workflow Builder
5. Future Steward

Passport progress records real practice, evidence, reflection, and review. It cannot be auto-translated into a badge level or exported as a credential. A user may be at different stages in different domains.

## Four build-layer levels

- **Basic:** completes a bounded task with transparent AI use, source/data checks, and learner reflection.
- **Intermediate:** repeats the capability in more than one eligible real mission, handles a meaningful correction or limitation, and receives required human review.
- **Advanced:** designs, evaluates, and improves a reusable governed method; compares outcomes and burden; teaches or documents it for safe reuse.
- **AI Agent Orchestration Master:** supervises a bounded multi-agent or multi-step run with frozen objectives, P1–P2 permissions only, approved nonsensitive data, routing rationale, budget/retry/stop limits, independent verification, failure recovery, complete receipt, and accountable-human review.

Level 4 may be displayed for a domain only when its domain criterion and the global orchestration capstone are both satisfied. It never unlocks permissions. P3 model/agent operation and P4 external action are unsupported in this target.

## Seventeen activity domains

| ID | Capability | FUTURE emphasis |
|---|---|---|
| `CAP-01` | AI literacy | Explain limits, false fluency, automation bias, and when not to use AI |
| `CAP-02` | SAFE prompt design | Situation, Aim, Facts, Expectations with minimum necessary context |
| `CAP-03` | Evidence-informed research | Real sources, authority, applicability, conflicts, freshness, and claim mapping |
| `CAP-04` | Critical thinking and reasoning | Separate fact, explanation, inference, recommendation, uncertainty, and human decision |
| `CAP-05` | Structured problem-solving | Repeatable Assess–Define–Plan–Implement–Evaluate cycles |
| `CAP-06` | Workflow design | Manual-first mapping, approvals, failure states, fallback, rollback, and receipts |
| `CAP-07` | Project management | Humane priorities, milestones, capacity, ownership, measures, minimum/re-entry mode, and recovery |
| `CAP-08` | Data and privacy stewardship | No-PHI boundary, context separation, minimization, consent, retention, deletion |
| `CAP-09` | Ethical AI practice | Learner authorship, integrity-rule checks, disclosure, fairness, no deception or fabrication |
| `CAP-10` | EDENA governance | Consistent tiering, accountable human, authority limits, escalation, and hard stops |
| `CAP-11` | Agent supervision | Select, constrain, inspect, stop, verify, correct, and retire one bounded agent |
| `CAP-12` | Multi-agent orchestration | Plan dependencies, permissions, handoffs, independent checks, recovery, and receipts |
| `CAP-13` | Knowledge-base development | Curate versioned sources, scope, claim links, conflicts, freshness, access, and removal |
| `CAP-14` | Automation design | Map and test only low-risk synthetic/manual workflows with gates, fallback, rollback, and honest eligibility |
| `CAP-15` | Artifact creation | Produce accessible, own-voice, source-linked drafts, prototypes, plans, portfolios, or teaching artifacts with AI disclosure |
| `CAP-16` | Evaluation and quality improvement | Measure outcome, burden, accessibility, independence, unintended effects, corrections, and next-cycle decisions |
| `CAP-17` | Role-specific professional development | Build truthful, reviewed evidence of student/assistant learning, communication, career growth, leadership, and safe technology stewardship |

Clinical skills, patient-care decisions, scope, delegation, medication, charting, certification, exam outcomes, grades, and employment decisions are deliberately outside these domains.

## Eligible evidence

An evidence record is eligible only when it is:

- linked to an existing, non-synthetic, adopted mission and exact cycle/revision;
- inside the learner's active pathway/context and permitted data ceiling;
- a recognized type: evaluated mission, reviewed artifact, source audit, correction, reflection, assessment, safety drill, supervised workflow run, accessibility review, agent receipt, or validated project outcome;
- specific about the learner's contribution and any AI assistance/disclosure;
- supported by inspectable artifacts/events rather than a self-rating alone;
- current within the criterion's validity period;
- reviewed by the named accountable human when the criterion requires it; and
- free of unresolved integrity, privacy, authority, source, context, or deletion conflicts.

Clicks, page views, time-in-app, AI praise, prompt count, conversation count, synthetic Starters, demos, fabricated outcomes, titles, credentials entered by the user, and unverified external claims are never eligible.

## Evidence states

`draft` → `submitted` → `under_review` → `accepted` or `needs_revision` or `rejected` → optionally `expired`, `superseded`, or `revoked`.

Each record stores: immutable ID; owner/workspace/mission/cycle; domain/criterion/level; evidence type; artifact/event references; learner contribution; AI contribution/disclosure; source and data classification; pathway/context; created/submitted/reviewed dates; reviewer identity and authority basis; decision/reason; expiry; conflicts; and content hash.

The app must never turn a self-review into human verification. Reviewer names are assertions until the reviewer authenticates or the user attaches permitted verification; the UI must show that distinction.

## Award algorithm

For each domain and level:

1. Load the exact current criteria version.
2. Select only eligible accepted evidence owned by the user in allowed contexts.
3. Exclude synthetic, deleted, expired, superseded, revoked, conflicted, unreviewed-required, and stale-revision evidence.
4. Satisfy every required criterion and required evidence-type/context-diversity rule.
5. For higher levels, verify prerequisite level and distinct evidence; do not reuse one event where the criterion requires repetition.
6. Create an explainable award event containing criteria version, evidence IDs/hashes, computation time, and reviewer state.
7. Recompute after correction, deletion, expiry, rule-version change, or evidence conflict. Downgrade visibly with a reason; never preserve a badge solely for engagement.

Progress is the count of satisfied required criteria divided by required criteria for that level, not a model-generated percentage. Show each satisfied and unmet criterion, eligible evidence, excluded evidence with reason, next safe challenge, governance behaviors demonstrated, review need, and expiration.

## Global orchestration capstone

The label `AI Agent Orchestration Master` additionally requires one real, low-risk, nonsensitive sandbox mission that:

- begins with a learner-authored objective and success/burden/independence measures;
- uses at least two frozen build-layer agents or an agent plus an independent reviewer in P1–P2 only;
- records routing reason, exact context/data/tools, cost/time/retry ceilings, human gates, stop/kill/fallback, and expiry;
- preserves distinct agent outputs and rejects unauthorized handoffs;
- includes an intentionally tested safe failure, cancellation, or recovery case;
- verifies claims and artifacts independently and records unresolved uncertainty;
- completes Evaluate and a new-cycle or stop decision;
- has a complete activity/integrity receipt and learner reflection explaining what they can now do independently; and
- is reviewed by an appropriate named human for process quality, without implying clinical or institutional validation.

The capstone cannot use patient data, live care, graded work, restricted school/employer information, external action, a production automation, or a synthetic-only mission.

## Portable export

Export a signed-or-checksummed JSON evidence bundle containing product/schema/criteria versions, noncredential disclaimer, award status, criteria results, permitted evidence metadata/hashes, review assertions and verification status, revocations, and export time. Omit protected content by default. “Open Badges compatible” may be claimed only after the exact standard version and validation tests pass; otherwise label it `future_portable_evidence`, not a credential.

## Suggested next challenges

Recommendations come only from unmet criteria and user-approved goals. They must remain low-risk, accessible, feasible, and reversible; include a manual option; name the responsible human; and avoid engagement pressure. The user may dismiss, defer, or delete them without penalty.
