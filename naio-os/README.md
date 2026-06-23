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
├── config/
│   ├── edena-policy.yaml           # tier → autonomy/gate/toolset (the WHAT-is-allowed)
│   └── florence-x.yaml             # build/quality doctrine + rituals (the HOW-it-behaves)
└── schema/
    └── naio-soul.schema.json       # the personalization bridge contract (quiz → installer)
```

Planned (subsequent phases):

```
├── manifest.yaml                   # version, components, signed checksums
├── install.sh                      # idempotent one-line bootstrap
├── scripts/
│   ├── import-soul.py              # consumes naio-soul.json
│   └── healthcheck.py              # verify-before-claim harness
├── skills/                         # tier-tagged NAIO skill pack
├── vault/                          # Obsidian vault skeleton
└── cron/                           # seed stewardship rituals
```

---

## The personalization bridge

```
SOUL Quiz  ──►  naio-soul.json  ──►  install.sh / import-soul.py
   │                  │                        │
 .md files      tier ceilings,           writes SOUL.md,
 (for humans)   voice, boundaries,       personalizes edena-policy,
                spheres                  configures gates + rituals
```

The quiz already produces human-readable Markdown. It now also exports a machine-readable **`naio-soul.json`** (validated against `schema/naio-soul.schema.json`) that the installer ingests to produce a *personalized, governed* Hermes.

`naio-soul.json` contains **no PHI**. The installer refuses any import where `boundaries.no_phi_confirmed` or `boundaries.no_clinical_decisions_confirmed` is not `true`.

---

## EDENA in one breath

- **Green** — draft only, every output gated, read/draft toolsets. *(onboarding)*
- **Yellow** — structured assist, side effects gated, review before external use. *(onboarding)*
- **Orange** — bounded autonomy inside a written scope, logged. *(requires governance module)*
- **Red** — semi-autonomous inside a verified scope, audited. *(reserved, review board)*

Hard boundaries apply at **every** tier: no PHI, no clinical decisions for identified patients, non-removable human agency, license respect, confidentiality.

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
| **0** | `edena-policy.yaml` + `florence-x.yaml` source of truth | ✅ done |
| **1** | Quiz "Export OS Config" → `naio-soul.json` + schema | ✅ done |
| **2** | Bundle skeleton + `manifest.yaml` + dry-run `install.sh` | planned |
| **3** | EDENA policy → Hermes config mapping (human gates live) | planned |
| **4** | Tier-tagged skill pack + cron rituals | planned |
| **5** | Healthcheck harness + one-line installer | planned |
| **6** | Versioning, update channel, signed checksums | planned |

---

## Doctrine

> Agents propose. Humans judge. Nurses steward.

Boundary: no PHI, no patient-specific clinical decisions, no replacement for licensed judgment.
