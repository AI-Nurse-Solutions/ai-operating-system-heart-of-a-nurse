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
├── manifest.yaml                   # Phase 8 bundle manifest + checksums
├── release.json                    # Phase 8 current update-channel metadata
├── release-history.json            # Phase 8 rollback protection + trusted key ids
├── manifest.sha256                 # Phase 8 manifest digest
├── manifest.sig                    # Phase 8 detached manifest signature
├── bootstrap.sh                    # Phase 8 signed one-line remote installer entrypoint
├── install.sh                      # Phase 8 installer (dry-run default; signed release gate; --self-test; --check-update; --recovery-drill; --apply target-only)
└── scripts/
    ├── preflight.sh                # OS/dependency/Hermes preflight
    ├── import-soul.py              # validates naio-soul.json
    ├── import-projects.py          # validates naio-projects.json
    ├── render-profile.py           # EDENA → Hermes-ready profile + skill/ritual renderer
    ├── self-test.py                # Phase 8 smoke test + recovery drill harness
    ├── verify-release.py           # Phase 8 release metadata + signature/history verifier
    ├── check-update.py             # Phase 8 advisory update check; no mutation
    ├── recovery.py                 # Phase 8 local-only snapshot, verify, restore-plan, and drill
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

Phase 8 output includes `SOUL.md`, per-sphere SOUL files, project system prompts, `skills/*/SKILL.md`, `cron/rituals.yaml`, `cron/prompts/*.md`, `config/edena-runtime.yaml`, `config/human-gates.yaml`, and a suggested `config/hermes-profile.patch.yaml` for review-before-use. Cron rituals are **templates only**; they are not scheduled automatically. The bootstrap downloads into a temporary directory, verifies `release.json`, `release-history.json`, `manifest.sha256`, `manifest.sig`, rollback/key-id trust metadata, and artifact checksums, then runs the installer with the arguments you pass.

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

---

## Doctrine

> Agents propose. Humans judge. Nurses steward.

Boundary: no PHI, no patient-specific clinical decisions, no replacement for licensed judgment.
