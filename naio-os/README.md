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
├── manifest.yaml                   # Phase 2 bundle manifest + checksums
├── install.sh                      # Phase 2 dry-run installer (validates + plans, no mutation)
└── scripts/
    ├── preflight.sh                # OS/dependency/Hermes preflight
    ├── import-soul.py              # validates naio-soul.json
    ├── import-projects.py          # validates naio-projects.json
    ├── healthcheck.py              # verify-before-claim harness
    └── compute-checksums.sh        # writes manifest sha256 fields
```

---

## The personalization bridge

```
SOUL Quiz          ──►  naio-soul.json     ──┐
Life & Projects    ──►  naio-projects.json ──┼──► install.sh / validators
                                                │
.md files for humans                            ▼
                                  Phase 2: validate + plan only
                                  Phase 3: write SOUL/project files,
                                           configure gates + rituals
```

The SOUL Quiz produces human-readable Markdown and a machine-readable **`naio-soul.json`** (validated against `schema/naio-soul.schema.json`). The Life & Projects Quiz produces governed project prompts and **`naio-projects.json`** (validated against `schema/naio-projects.schema.json`). Phase 2 validates both and shows the exact plan; Phase 3 will apply them into a personalized, governed Hermes.

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
| **3** | EDENA policy → Hermes config mapping (human gates live) | planned |
| **4** | Tier-tagged skill pack + cron rituals | planned |
| **5** | Healthcheck harness + one-line installer | planned |
| **6** | Versioning, update channel, signed checksums | planned |

---

## Doctrine

> Agents propose. Humans judge. Nurses steward.

Boundary: no PHI, no patient-specific clinical decisions, no replacement for licensed judgment.
