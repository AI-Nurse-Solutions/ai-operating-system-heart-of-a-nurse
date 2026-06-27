# NAIO OS — the Governed AI Operating System for Nurses

> *Carry the lamp. Keep the ledger.*
> A governed operating system around models — built over Hermes Desktop, with EDENA and Florence-X baked in.

This directory is the **source of truth** for the Nurse AI Operating System: a downloadable, auto-installing, personalized governance layer over Hermes Desktop.

It is **not** a new runtime. Hermes Desktop is the runtime. NAIO is the *control plane* that governs how that runtime thinks and acts — personalized to each nurse by the [SOUL Quiz](https://nurse-ai-os.org/soul-quiz.html).

---

## The three planes

```
┌─────────────────────────────────────────────────────────────┐
│  CONTROL PLANE  — what is ALLOWED                            │
│  EDENA tiers · Florence-X doctrine · Human gates            │
│  (personalized by SOUL Quiz → per-sphere tier ceilings)     │
└───────────────┬─────────────────────────┬───────────────────┘
                │                         │
┌───────────────▼─────────┐   ┌───────────▼───────────────────┐
│  COGNITION PLANE        │   │  EXECUTION PLANE              │
│  how THINKING happens   │   │  how WORK gets done          │
│  • Harnesses            │   │  • Skills (tier-tagged)       │
│  • Memory (SOUL+vault)  │   │  • Agents (delegation)        │
│  • Routing (models)     │   │  • Cron (stewardship rituals) │
└─────────────────────────┘   └──────────────────────────────┘
                    HERMES DESKTOP (the runtime)
```

The control plane can **veto** the other two. That is what makes NAIO *governed* rather than merely *configured*.

---

## Component map

| Component | Hermes primitive it rides on | NAIO governance overlay |
|---|---|---|
| **Harnesses** | toolsets, system prompt, agent loop | EDENA tier decides which toolsets load per sphere |
| **Memory** | `SOUL.md` (always-on) + Obsidian vault (on-demand) | Core + per-sphere SOUL from the quiz; PHI boundary at the harness layer |
| **Routing** | provider/model config, fallbacks | Florence-X model policy: no-PHI posture, evidence-preferring defaults |
| **Cron** | cron jobs | Stewardship rituals (the lamp + the ledger), bounded by tier |
| **Skills** | `SKILL.md` files | Tier-tagged skill pack (`edena_tier:` in frontmatter) |
| **Agents** | delegation / subagents | Inherit sphere SOUL; cannot exceed the sphere's tier ceiling |
| **Human gates** | approval prompts | EDENA tier → required approval level; non-removable for Green/Yellow |

---

## Files in this directory

```
naio-os/
├── README.md                       # this spec
├── GOVERNANCE-RESEARCH.md          # standards crosswalk + gap analysis (the evidence base)
├── config/
│   ├── edena-policy.yaml           # autonomy tiers + functionality + permissions + reversibility (the WHAT-is-allowed)
│   └── florence-x.yaml             # build/quality doctrine + rituals (the HOW-it-behaves)
└── schema/
    ├── naio-soul.schema.json       # identity/personalization bridge contract (SOUL Quiz → installer)
    └── naio-projects.schema.json   # project prompt bridge contract (Life & Projects Quiz → installer)
├── manifest.yaml                   # Phase 20 bundle manifest + checksums
├── release.json                    # Phase 20 current update-channel metadata
├── release-history.json            # Phase 20 rollback protection + trusted key ids
├── manifest.sha256                 # Phase 20 manifest digest
├── manifest.sig                    # Phase 20 detached manifest signature
├── bootstrap.sh                    # Phase 20 signed one-line remote installer entrypoint
├── install.sh                      # Phase 18 installer (dry-run default; signed release gate; --self-test; --check-update; --recovery-drill; --activation-check; --launch-check; --cohort-check; --evidence-check; --contribution-check; --pilot-check; --readiness-check; --registry-check; --orchestration-check; --governance-check; --partner-check; --stewardship-check; --apply target-only)
└── scripts/
    ├── preflight.sh                # OS/dependency/Hermes preflight
    ├── import-soul.py              # validates naio-soul.json
    ├── import-projects.py          # validates naio-projects.json
    ├── render-profile.py           # EDENA → Hermes-ready profile + skill/ritual renderer
    ├── self-test.py                # Phase 12 smoke test + recovery + activation + launch harness
    ├── verify-release.py           # Phase 12 release metadata + signature/history verifier
    ├── check-update.py             # Phase 12 advisory update check; no mutation
    ├── recovery.py                 # Phase 12 local-only snapshot, verify, restore-plan, and drill
    ├── activation.py               # Phase 12 first-run START-HERE + 7-day readiness check
    ├── launch.py                   # Phase 12 public launch pack readiness check
    ├── cohort.py                   # Phase 12 cohort/instructor readiness check
    ├── evidence.py                 # Phase 12 EDENA evidence trail readiness check
    ├── healthcheck.py              # verify-before-claim harness
    └── compute-checksums.sh        # writes manifest sha256 fields
```

---

## The personalization bridge

```
SOUL Quiz          ──►  naio-soul.json     ──┐
Life & Projects    ──►  naio-projects.json ──┼──► install.sh
                                                │
.md files for humans                            ▼
                                  Phase 2: validate + plan only
                                  Phase 3: render governed profile bundle
                                           (SOUL files + project prompts +
                                            EDENA runtime + human gates)
                                  Phase 4: add execution templates
                                           (tier-tagged skills + cron rituals)
                                  Phase 5: one-line installer + self-test
                                           (remote bootstrap + smoke harness)
                                  Phase 6: signed update channel
                                           (release metadata + manifest signature)
                                  Phase 7: release governance
                                           (rollback protection + advisory update check)
```

The SOUL Quiz produces human-readable Markdown and a machine-readable **`naio-soul.json`** (validated against `schema/naio-soul.schema.json`). The Life & Projects Quiz produces governed project prompts and **`naio-projects.json`** (validated against `schema/naio-projects.schema.json`). Phase 2 validates both and shows the exact plan. Phase 3 renders a personalized, governed Hermes-ready profile bundle into an explicit target directory — never directly into `~/.hermes`. Phase 4 adds the execution plane: tier-tagged starter skills and cron ritual templates are rendered into that same target bundle for review-before-activation. Phase 5 adds the real UX: a one-line remote bootstrap plus `--self-test` smoke harness that proves the bundle can validate, render, and refuse unsafe actions before a nurse applies anything. Phase 6 adds the trust layer: release metadata, manifest digest, and a detached RSA-SHA256 manifest signature are verified before artifact checksums are trusted. **Phase 7 now adds release governance:** rollback protection, trusted key-id metadata, release history, and a no-mutation `--check-update` advisory command.

Self-test before applying anything:

```bash
curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- --self-test
```

One-line remote apply after downloading your quiz exports:

```bash
curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- \
  --apply \
  --soul ~/Downloads/naio-soul.json \
  --projects ~/Downloads/naio-projects.json \
  --target ./NAIO-Hermes-Profile
```

Local apply example:

```bash
./install.sh --apply \
  --soul ~/Downloads/naio-soul.json \
  --projects ~/Downloads/naio-projects.json \
  --target ./NAIO-Hermes-Profile
```

Phase 20 output includes `SOUL.md`, per-sphere SOUL files, project system prompts, `skills/*/SKILL.md`, `cron/rituals.yaml`, `cron/prompts/*.md`, `config/edena-runtime.yaml`, `config/human-gates.yaml`, and a suggested `config/hermes-profile.patch.yaml` for review-before-use. Cron rituals are **templates only**; they are not scheduled automatically. The bootstrap downloads into a temporary directory, verifies `release.json`, `release-history.json`, `manifest.sha256`, `manifest.sig`, rollback/key-id trust metadata, and artifact checksums, then runs the installer with the arguments you pass.

Both JSON files contain **no PHI** by design. The installer refuses any SOUL import where `boundaries.no_phi_confirmed` or `boundaries.no_clinical_decisions_confirmed` is not `true`, and refuses either import if PHI indicators are detected.

---

## EDENA in one breath

**EDENA = Ethical Design & Enablement for Nursing Augmentation.** The name states the mission: AI that is ethically *designed*, that *enables* (not just restricts), and that *augments* the nurse — never replaces her judgment (ANA Provision 7.5). Applied through the **EDENA Stewardship Lens**, a five-dimension rubric (Equity & Ethics · Dignity & Data · Environment & Externalities · Nursing relevance & Nurse wellbeing · Agency & Action). *The name says what it is; the Lens says how you check your work.*

A tier governs **autonomy only** — how much the agent acts without the human. Two other levers are scoped *independently* (this is the v2 change, grounded in Knight Columbia 2025 and OWASP LLM06):

- **Lever 1 — Autonomy tier:** Green (draft only) · Yellow (structured assist, gated) · Orange (bounded, written scope + monitoring) · Red (semi-autonomous, audited, reserved).
- **Lever 2 — Functionality:** which tools load, by side-effect class, least-privilege.
- **Lever 3 — Permissions:** what those tools may touch, read-only by default, complete mediation.
- **Cross-cutting — Reversibility:** an irreversible action is gated at *any* tier. The stronger gate always wins.

Hard boundaries apply at **every** tier: no PHI, no clinical decisions for identified patients, non-removable human agency, license respect, confidentiality, data-withdrawal, transparency, health equity. Prohibited practices mirror EU AI Act Art. 5 filtered through nursing ethics.

A nurse **earns** higher tiers through demonstrated competency (graduated trust) — the policy enables as deliberately as it restricts, so nurses are never driven to ungoverned "shadow AI."

---

## Florence-X in one breath

The engineering discipline of the two instruments:

- **Counting mind** — verify before claim, evidence-awareness, observability, reproducibility.
- **Caring heart** — human agency, dignity, wellbeing, presence over throughput.

Expressed as machine policy in `florence-x.yaml`, including the installer contract (idempotent, preflight, healthcheck, never-claim-unverified, rollback-on-failure) and the stewardship rituals.

---

## Build roadmap

| Phase | Deliverable | Status |
|---|---|---|
| **0** | `edena-policy.yaml` + `florence-x.yaml` source of truth | ✅ v2.0.0 (standards-grounded) |
| **1** | Quiz "Export OS Config" → `naio-soul.json` + schema | ✅ done |
| **2** | Bundle skeleton + `manifest.yaml` + dry-run `install.sh` | ✅ done — validates SOUL + Projects imports, checksums, healthcheck; no mutation |
| **3** | EDENA policy → Hermes config mapping (human gates live) | ✅ done — `--apply --target` renders SOUL, project prompts, EDENA runtime, human gates, and profile overlay without mutating `~/.hermes` |
| **4** | Tier-tagged skill pack + cron rituals | ✅ done — renders 5 EDENA-tagged starter skills and 4 reviewable cron ritual templates; nothing scheduled automatically |
| **5** | Healthcheck harness + one-line installer | ✅ done — `bootstrap.sh` remote entrypoint plus `install.sh --self-test`; verifies checksums, safe sample render, and refusal cases before apply |
| **6** | Versioning, update channel, signed checksums | ✅ done — `release.json`, `manifest.sha256`, detached `manifest.sig`, release public key, and fail-closed verifier gate before artifact checksums |
| **7** | Release governance, rollback protection, advisory update check | ✅ done — `release-history.json`, trusted `key_id`, monotonic phase rollback refusal, and `install.sh --check-update` / `scripts/check-update.py` with no automatic mutation |
| **8** | Local recovery snapshots, restore plans, recovery drill | ✅ done — `scripts/recovery.py`, explicit local snapshot directory, checksum sidecar, safe archive verification, `NAIO-RESTORE-PLAN.md`, and `install.sh --recovery-drill` with no automatic restore |
| **9** | First-run activation guide + 7-day nurse onboarding path | ✅ done — `START-HERE.md`, `07-First-Week/*.md`, `scripts/activation.py`, and `install.sh --activation-check` verify the nurse can safely begin without mutation |
| **10** | Public Launch Pack + no-overclaim share readiness | ✅ done — `10-Public-Launch/*.md`, `scripts/launch.py`, and `install.sh --launch-check` verify no-PHI, no clinical-readiness claims, and human-review posture before sharing |
| **11** | Cohort / Instructor Mode + readiness reflection | ✅ done — `11-Cohort-Mode/*.md`, `scripts/cohort.py`, and `install.sh --cohort-check` verify no-PHI, no certification claims, no auto-enrollment, and facilitation safety |
| **12** | EDENA Evidence Trail + evidence-of-learning portfolio | ✅ done — `12-Evidence-Trail/*.md`, `scripts/evidence.py`, and `install.sh --evidence-check` verify no-PHI, no certification claims, no automatic scoring/submission, and evidence safety |
| **13** | NIN Community Contribution Flow + sanitized contribution review | ✅ done — `13-Contribution-Flow/*.md`, `scripts/contribute.py`, and `install.sh --contribution-check` verify no-PHI, no secrets, no endorsement claims, and no automatic publishing/submission |
| **14** | Institutional Pilot Pack + non-clinical pilot readiness | ✅ done — `14-Institutional-Pilot/*.md`, `scripts/pilot.py`, and `install.sh --pilot-check` verify no-PHI, no patient care, no institutional endorsement/compliance/certification claims, and no automatic reporting/enrollment |
| **15** | EDENA Micro-Credential Readiness Pack + formative review | ✅ done — `15-EDENA-Readiness/*.md`, `scripts/readiness.py`, and `install.sh --readiness-check` verify no-PHI, no patient care, no certification/clinical-readiness claims, and no automatic scoring/pass-fail/badge/credential issuance |
| **16** | NAIO Agent Registry Pack + steward review queue | ✅ done — `16-Agent-Registry/*.md`, `scripts/registry.py`, and `install.sh --registry-check` verify no-PHI, no patient care, no endorsement/procurement/deployment/clinical-readiness claims, and no automatic vetting/listing/agent execution |
| **17** | Florence-X Orchestration Preview + shared intent/context cards | ✅ done — `17-Florence-X-Orchestration/*.md`, `scripts/orchestration.py`, and `install.sh --orchestration-check` verify no-PHI, no patient care, Orange-deferred shared memory, no shared memory runtime, and no automatic handoffs/routing/agent execution |
| **18** | Governance Board / Steward Council Pack | ✅ done — `18-Governance-Board/*.md`, `scripts/governance.py`, and `install.sh --governance-check` verify advisory-only stewardship, no legal/compliance/institutional/clinical/procurement/certification/credentialing authority, and no automatic approvals or policy enforcement |
| **19** | Partner / Sponsor Briefing Pack | ✅ done — `19-Partner-Briefing/*.md`, `scripts/partner.py`, and `install.sh --partner-check` verify informational-only partner conversations, no fundraising/investment/legal/compliance/procurement/clinical-deployment/approval claims, and no automatic outreach or follow-up |
| **20** | Institutional Stewardship Operating Model Pack | ✅ done — `20-Stewardship-Operating-Model/*.md`, `scripts/stewardship.py`, and `install.sh --stewardship-check` verify advisory operating cadence, no legal/compliance/procurement/budget/contracting/staffing/clinical-deployment authority, and no automatic implementation, owner assignment, stakeholder notification, escalation, or dashboard publication |

---

## Doctrine

> Agents propose. Humans judge. Nurses steward.

Boundary: no PHI, no patient-specific clinical decisions, no replacement for licensed judgment.


## Phase 9 — First-Run Activation Layer

Phase 9 answers the bedside question: **“I installed this after a hard shift. What do I safely do first?”**

Rendered profile bundles now include:

```text
START-HERE.md
07-First-Week/Day-1-Setup.md
07-First-Week/Day-2-SOUL-Review.md
07-First-Week/Day-3-Project-Triage.md
07-First-Week/Day-4-Lamp-Huddle.md
07-First-Week/Day-5-Knowledge-Inbox.md
07-First-Week/Day-6-Boundary-Review.md
07-First-Week/Day-7-Weekly-Ledger.md
```

Activation can be checked without mutating Hermes:

```bash
./install.sh --activation-check --target ./NAIO-Hermes-Profile
python3 scripts/activation.py --profile ./NAIO-Hermes-Profile --json
```

Remote one-line activation check:

```bash
curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- --activation-check --target ./NAIO-Hermes-Profile
```

Safety posture remains unchanged: no PHI, no clinical decisions, no direct `~/.hermes` mutation, no automatic cron scheduling, and human gates remain non-removable.


## Phase 10 — Public Launch Pack

Phase 10 answers the next launch question: **“How do I share this publicly without overclaiming or risking PHI?”**

Rendered profile bundles now include:

```text
10-Public-Launch/README.md
10-Public-Launch/Launch-Checklist.md
10-Public-Launch/Safety-Boundaries.md
10-Public-Launch/FAQ.md
10-Public-Launch/Founder-Note.md
10-Public-Launch/Demo-Script.md
10-Public-Launch/Social-Post-LinkedIn.md
10-Public-Launch/Social-Post-Instagram-Facebook.md
10-Public-Launch/Email-Invite.md
```

Launch readiness can be checked without mutating Hermes:

```bash
./install.sh --launch-check --target ./NAIO-Hermes-Profile
python3 scripts/launch.py --profile ./NAIO-Hermes-Profile --json
```

Remote one-line launch check:

```bash
curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- --launch-check --target ./NAIO-Hermes-Profile
```

Safety posture remains unchanged: no PHI, no clinical decisions, no direct `~/.hermes` mutation, no automatic cron scheduling, no automatic restore, no automatic publishing, and no clinical-readiness claims.


## Phase 12 — Cohort / Instructor Mode

Phase 12 answers the cohort question: **“How do I teach this safely without becoming a premature certification body?”**

Rendered profiles include:

```text
11-Cohort-Mode/README.md
11-Cohort-Mode/Instructor-Guide.md
11-Cohort-Mode/Cohort-Launch-Checklist.md
11-Cohort-Mode/Week-1-Facilitation-Plan.md
11-Cohort-Mode/Week-2-Facilitation-Plan.md
11-Cohort-Mode/Week-3-Facilitation-Plan.md
11-Cohort-Mode/Week-4-Facilitation-Plan.md
11-Cohort-Mode/Participant-Readiness-Rubric.md
11-Cohort-Mode/Office-Hours-Question-Triage.md
11-Cohort-Mode/Completion-Reflection.md
```

Check readiness locally:

```bash
./install.sh --cohort-check --target ./NAIO-Hermes-Profile
python3 scripts/cohort.py --profile ./NAIO-Hermes-Profile --json
```

Remote one-line cohort check:

```bash
curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- --cohort-check --target ./NAIO-Hermes-Profile
```

Cohort Mode is for readiness reflection, not certification. It verifies no PHI, no clinical-readiness claims, no auto-enrollment, no automatic cron scheduling, and no direct `~/.hermes` mutation.


## Phase 12 — EDENA Evidence Trail

Phase 12 answers the evidence question: **“How do we document learning and stewardship without claiming certification or clinical readiness?”**

Rendered profiles include:

```text
12-Evidence-Trail/README.md
12-Evidence-Trail/Evidence-Capture-Guide.md
12-Evidence-Trail/EDENA-Lens-Reflection.md
12-Evidence-Trail/Artifact-Log.md
12-Evidence-Trail/Human-Gate-Ledger.md
12-Evidence-Trail/Boundary-Incident-Template.md
12-Evidence-Trail/Portfolio-Index.md
12-Evidence-Trail/Facilitator-Review-Notes.md
12-Evidence-Trail/Evidence-Export-Checklist.md
12-Evidence-Trail/Not-Certification-Statement.md
```

Check readiness locally:

```bash
./install.sh --evidence-check --target ./NAIO-Hermes-Profile
python3 scripts/evidence.py --profile ./NAIO-Hermes-Profile --json
```

Remote one-line evidence check:

```bash
curl -fsSL https://nurse-ai-os.org/naio-os/bootstrap.sh | bash -s -- --evidence-check --target ./NAIO-Hermes-Profile
```

Evidence Trail is for evidence of learning, not certification. It verifies no PHI, no clinical-readiness claims, no automatic scoring, no automatic submission, no cron scheduling, and no direct `~/.hermes` mutation.


## Phase 17 — NIN Community Contribution Flow

Phase 17 answers the community question: **“How can nurses contribute safely without leaking PHI, implying endorsement, or turning learning artifacts into clinical claims?”**

It adds a governed contribution path for NIN:

- `13-Contribution-Flow/*.md` — intake, sanitization, contribution template, EDENA review, attribution/consent, triage, and not-endorsement statements.
- `scripts/contribute.py` — readiness checker for no-PHI, no employer-confidential content, no secrets, no endorsement/clinical-readiness claims, no automatic publishing/submission/reviewer assignment, and no direct mutation.
- `install.sh --contribution-check` — local target-only contribution readiness check.

This is a contribution workflow, not a public submission backend. Human stewards review before community use. Inclusion does not mean endorsement, certification, clinical validation, institutional approval, or permission for patient-specific clinical use.

Agents propose. Humans judge. Nurses steward.


## Phase 17 — Institutional Pilot Pack

Phase 17 answers the institutional question: **“How can a nurse leader or educator run a small non-clinical pilot safely without implying deployment, endorsement, compliance, or certification?”**

It adds a governed 30–90 day pilot path:

- `14-Institutional-Pilot/*.md` — pilot charter, stakeholder brief, risk register, no-PHI boundary, participant onboarding, weekly ledger, outcome reflection, escalation path, not-clinical-deployment statement, and closeout brief.
- `scripts/pilot.py` — readiness checker for no-PHI, no patient-care use, no clinical decision support, no endorsement/compliance/certification claims, no automatic reporting, no automatic enrollment, no automatic escalation, and no direct mutation.
- `install.sh --pilot-check` — local target-only pilot readiness check.

This is an institutional learning pilot, not clinical deployment. Human governance review is required before anything leaves the pilot group.

Agents propose. Humans judge. Nurses steward.


## Phase 17 — EDENA Micro-Credential Readiness Pack

Phase 17 answers the credential question safely: **“How can a nurse organize evidence for human review without pretending NAIO is issuing certification or clinical AI-readiness?”**

It adds a formative readiness path:

- `15-EDENA-Readiness/*.md` — readiness overview, eligibility self-check, evidence map, stewardship reflection, boundary competence ledger, reviewer guide, rubric, remediation plan, non-certification statement, cover sheet, and badge deferral notice.
- `scripts/readiness.py` — readiness posture checker for no-PHI, no patient-care use, no clinical decision support, no certification/clinical-readiness/competency claims, no automatic scoring, no automatic pass/fail, no automatic credential issuance, no automatic badge issuance, and no direct mutation.
- `install.sh --readiness-check` — local target-only readiness review check.

This is readiness reflection for human steward review, not certification.

Agents propose. Humans judge. Nurses steward.


## Phase 17 — NAIO Agent Registry Pack

Phase 17 opens the registry doorway safely: **“How can nurses discover and evaluate public agents without mistaking a listing for endorsement, procurement approval, deployment approval, or clinical readiness?”**

It adds a human-reviewed registry path:

- `16-Agent-Registry/*.md` — registry overview, agent intake card, source verification checklist, EDENA agent evaluation, risk review, nurse use-case fit, listing template, not-endorsement statement, review queue, change log, and retirement/recheck plan.
- `scripts/registry.py` — registry posture checker for no-PHI, no patient-care use, no clinical decision support, no endorsement/procurement/deployment/clinical-readiness claims, no automatic vetting, no automatic listing, no automatic agent execution, and no direct mutation.
- `install.sh --registry-check` — local target-only registry listing posture check.

This is a human-reviewed learning registry, not endorsement.

Agents propose. Humans judge. Nurses steward.


## Phase 17 — Florence-X Orchestration Preview Pack

Phase 17 opens the orchestration doorway safely: **“How can nurses design shared-intent, shared-context agent coordination without enabling autonomous multi-agent runtime or shared memory?”**

It adds a dry-run Florence-X path:

- `17-Florence-X-Orchestration/*.md` — orchestration overview, shared intent card, shared context card, semantic state card, role map, handoff contract, interaction fields checklist, human orchestrator review, dry-run plan, stop/escalation rules, trace ledger, and non-deployment statement.
- `scripts/orchestration.py` — orchestration posture checker for no-PHI, no patient-care use, no clinical decision support, Orange-deferred shared memory, no shared-memory runtime, no automatic handoff/routing/escalation/agent execution, and no direct mutation.
- `install.sh --orchestration-check` — local target-only orchestration preview check.

This is a Florence-X dry-run preview, not autonomous orchestration.

Agents propose. Humans judge. Nurses steward.


## Phase 18 — Governance Board / Steward Council Pack

Phase 18 gives nurses a safe governance doorway: **“How can a Steward Council review AI artifacts without pretending to be legal counsel, compliance, clinical governance, procurement, certification, or institutional authority?”**

It adds an advisory-only governance path:

- `18-Governance-Board/*.md` — governance charter, steward council overview, member role card, review intake form, agenda template, advisory decision record, conflict-of-interest disclosure, boundary/scope statement, escalation/referral path, advisory quorum checklist, transparency ledger, and non-authority statement.
- `scripts/governance.py` — governance posture checker for no-PHI, no patient-care use, no clinical decision support, no legal/compliance/institutional/clinical/procurement/certification/credentialing/disciplinary authority, no automatic approvals, no automatic policy enforcement, no automatic member assignment, no automatic publication of minutes, no automatic escalation, and no direct mutation.
- `install.sh --governance-check` — local target-only governance pack check.

This is an advisory Steward Council template, not legal or institutional authority.

Agents propose. Humans judge. Nurses steward.

## Phase 19 — Partner / Sponsor Briefing Pack

Phase 19 gives Robert and future nurse stewards a safe outward-facing collaboration doorway: **“How can we brief hospitals, schools, associations, donors, sponsors, and ecosystem partners without implying solicitation, approval, funding, procurement, institutional endorsement, or clinical deployment?”**

It adds an informational-only partner path:

- `19-Partner-Briefing/*.md` — partner overview, one-page brief, use-case boundary map, stakeholder question prep, claim-vs-proof ledger, demo boundary script, partner intake form, risk/referral notes, sponsor conversation guide, non-solicitation/non-approval statement, and follow-up decision record.
- `scripts/partner.py` — briefing posture checker for no-PHI, no patient-care use, no clinical decision support, no fundraising solicitation, no investment advice, no legal/compliance/procurement/clinical-deployment/approval claims, no automatic outreach/sending/follow-up/data-room/funding acceptance, and no direct mutation.
- `install.sh --partner-check` — local target-only partner briefing check.

This is an informational partner briefing template, not a solicitation, not a partnership approval, not sponsor approval, not procurement approval, not legal/compliance determination, and not clinical deployment authority.

Agents propose. Humans judge. Nurses steward.

## Phase 20 — Institutional Stewardship Operating Model Pack

Phase 20 gives Robert and future nurse stewards a safe institution-facing operating cadence: **“How do we coordinate nurse-led AI stewardship inside schools, hospitals, associations, and partner ecosystems without claiming legal, compliance, procurement, staffing, clinical deployment, or implementation authority?”**

It adds an advisory-only operating model path:

- `20-Stewardship-Operating-Model/*.md` — operating model overview, role/cadence map, intake-to-decision workflow, Human-Gate RACI, meeting agenda, risk escalation map, metrics scorecard, implementation backlog, adoption readiness conversation guide, non-authority/no-deployment statement, and quarterly stewardship review.
- `scripts/stewardship.py` — operating model posture checker for no-PHI, no patient-care use, no clinical decision support, no legal/compliance/procurement/budget/contracting/staffing/clinical-deployment authority, no credentialing/certification, no automatic implementation, no automatic owner assignment, no automatic stakeholder notification, no automatic escalation, no automatic dashboard publication, and no direct mutation.
- `install.sh --stewardship-check` — local target-only institutional stewardship operating model check.

This is an advisory operating model template, not legal advice, not compliance determination, not procurement approval, not budget approval, not contracting authority, not institutional policy authority, not clinical governance authority, not clinical deployment approval, not a staffing or labor decision, not credentialing, not certification, and not automatic implementation.

Agents propose. Humans judge. Nurses steward.

## Phase 21 — Localization / International Readiness Lane Pack

Phase 21 gives Robert and future nurse stewards a safe international expansion doorway: **“How do we adapt NAIO OS for Philippines/SEA/global-English nurses without pretending we have local authority?”**

It renders `21-Localization-Readiness/` with region/audience mapping, language and tone adaptation guidance, jurisdiction boundary checks, cultural stewardship interview prompts, local partner question prep, claim-vs-local-proof ledgers, translation review workflow, cross-border data/privacy questions, a non-authority/no-localization-approval statement, and a localization decision record.

It also adds:

- `scripts/localization.py`
- `install.sh --localization-check --target <rendered-profile-dir>`
- `config/edena-runtime.yaml` localization metadata
- signed release metadata for `2.0.0-phase21`

Phase 21 boundaries:

- No PHI.
- No patient care use.
- No clinical decision support.
- Readiness and adaptation only.
- Not legal advice.
- Not regulatory advice.
- Not compliance determination.
- Not official translation.
- Not translation certification.
- Not localization approval.
- Not cultural validation.
- Not jurisdictional approval.
- Not ministry approval.
- Not institutional endorsement.
- Not procurement approval.
- Not cross-border data transfer approval.
- Not immigration advice.
- Not licensure advice.
- Not recruitment activity.
- Not clinical governance authority.
- Not clinical deployment approval.
- No automatic translation.
- No automatic localized publishing.
- No automatic local partner outreach.
- No automatic local steward assignment.
- No automatic regional data collection.
- No automatic authority submission.
- Human local steward review is required.

Agents propose. Humans judge. Nurses steward.

## Phase 22 — Adoption & Outcomes Ledger Pack

Phase 22 gives Robert, nurse stewards, cohorts, and institutions a safe proof layer: **“What adoption signals and learning evidence can we responsibly track without claiming clinical efficacy, patient outcomes, ROI, staffing impact, compliance validation, certification, or performance evaluation?”**

It renders `22-Adoption-Outcomes-Ledger/` with an adoption ledger overview, safe-use metrics map, time-saved estimate worksheet, human-gate pattern log, friction and risk register, nurse confidence pulse, workflow before-after capture, learning milestone ledger, cohort adoption summary, institutional signal brief, non-clinical outcome/no-efficacy-claim statement, and adoption decision record.

It also adds:

- `scripts/outcomes.py`
- `install.sh --outcomes-check --target <rendered-profile-dir>`
- `config/edena-runtime.yaml` outcomes metadata
- signed release metadata for `2.0.0-phase22`

Phase 22 boundaries:

- No PHI.
- No patient care use.
- No clinical decision support.
- Adoption signal and learning evidence only.
- Not clinical efficacy.
- Not patient outcome improvement.
- Not patient safety validation.
- Not quality-measure impact.
- Not ROI guarantee.
- Not staffing reduction.
- Not compliance validation.
- Not competency certification.
- Not performance evaluation.
- Not research determination, IRB determination, or quality-improvement approval.
- Not billing, reimbursement, procurement, or deployment approval.
- No automatic scoring.
- No automatic dashboard publication.
- No automatic institutional reporting.
- No automatic manager notification.
- No automatic performance evaluation.
- No automatic escalation.
- No automatic badge or credential issuance.
- Human steward review is required.

Agents propose. Humans judge. Nurses steward.
