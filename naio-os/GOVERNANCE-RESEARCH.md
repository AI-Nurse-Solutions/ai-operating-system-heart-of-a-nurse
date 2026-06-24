# NAIO Governance — Standards Crosswalk & Gap Analysis

> The research foundation for the EDENA + Florence-X policy rewrite (v2.0.0).
> Every design decision below is traceable to a primary source.

This document explains *why* the policy files are shaped the way they are. It maps
the Nurse AI OS governance model to the external standards it must remain compatible
with, and records the gaps in the v1 policy that v2 closes.

---

## 1. Primary sources consulted

| # | Source | Date | What it gives us |
|---|---|---|---|
| S1 | **Knight Columbia — "Levels of Autonomy for AI Agents"** (Feng, McDonald, Zhang, U. Washington) | Jul 2025 | Agency ≠ autonomy; 5 user-role levels (Operator→Observer); autonomy as a *design decision* |
| S2 | **NIST AI RMF 1.0** (AI 100-1) | Jan 2023 | GOVERN / MAP / MEASURE / MANAGE; 7 trustworthiness characteristics |
| S3 | **NIST Generative AI Profile** (AI 600-1) | Jul 2024 | 12 GenAI risk areas; automation-bias under "Human-AI Configuration" |
| S4 | **CSA — NIST AI RMF Agentic Profile** (draft) | Mar 2026 | Autonomy-tier classification; tool-use risk; runtime monitoring; delegation accountability |
| S5 | **EU AI Act** (Reg. 2024/1689) | 2024–2027 rollout | Risk tiers; prohibited practices (Art. 5); transparency duty; deployer vs provider |
| S6 | **ISO/IEC 42001:2023** (AIMS) | 2023 | Management-system discipline; PDCA continual improvement; certifiable |
| S7 | **WHO — Ethics & governance of AI for health: LMMs** | Jan 2024 | 40+ recommendations; automation bias; inclusive design; reversibility; post-release audit |
| S8 | **ANA Code of Ethics (2025), Provision 7.5** + ANA "Ethical Use of AI in Nursing Practice" (2022, under revision) | 2022–2025 | Augmented (not autonomous) intelligence; reversibility/data-withdrawal; health equity; dignity; voice of nursing present |
| S9 | **ICN — Digital health transformation & nursing practice** (position statement) | 2023 | Technology must be compatible with safety, dignity, and rights |
| S10 | **OWASP Top 10 for LLM Apps (2025)** — esp. **LLM06 Excessive Agency** | 2025 | Three root causes: excessive functionality / permissions / autonomy; least-privilege mitigations |
| S11 | **OWASP Top 10 for Agentic Applications** (ASI01–ASI10, Black Hat EU) | 2025 | Goal hijack, tool misuse, privilege abuse, memory poisoning, cascading failures, human-trust exploitation, rogue agents |

---

## 2. The two insights that reshape the architecture

### Insight A — Agency and autonomy are *different levers* (S1, S10)

> *"An agent can have low agency (few tools) but high autonomy (runs unsupervised), or high agency (many tools) but low autonomy (frequently requests feedback)."* — Knight Columbia (S1)

OWASP's **Excessive Agency** (S10) decomposes the same idea into **three independent root causes**:

1. **Excessive functionality** — the agent *has* tools it doesn't need.
2. **Excessive permissions** — those tools *can touch* more than they should.
3. **Excessive autonomy** — the agent *acts* without verification.

**Consequence for NAIO:** a single "tier" must NOT bundle these. v2 treats a tier as an **autonomy ceiling only**, and scopes **functionality** and **permissions** *independently* with least-privilege defaults. This is the central change from v1.

### Insight B — Irreversibility and the temporal gap are first-class risks (S4)

> *"The temporal gap between action initiation and human observation is a fundamental new risk dimension... irreversible real-world actions initiated before human observation."* — CSA Agentic Profile (S4)

**Consequence for NAIO:** **reversibility** becomes a property that can *force a gate regardless of tier*. An irreversible action is gated even at higher tiers. ANA 7.5 (S8) independently demands reversibility/data-withdrawal, so this is doubly grounded.

---

## 3. EDENA tier ↔ external framework crosswalk

| EDENA tier | Knight Columbia user role (S1) | CSA autonomy tier (S4) | NIST oversight (S2/S3) | Nursing framing (S8) |
|---|---|---|---|---|
| **Green** | Operator (user in charge; on-demand support) | Tier 1 (fully supervised; outputs need approval) | Human-in-the-loop | Augmented intelligence; nurse decides everything |
| **Yellow** | Consultant / Approver (agent drafts; human approves before external use) | Tier 2 (constrained autonomy; pre-approved action types) | Human-on-the-loop with gates | Nurse stewards; reviews before anything leaves |
| **Orange** | Approver (engaged at blockers/sign-offs within written scope) | Tier 3 (broad autonomy within boundary; continuous monitoring) | Human-on-the-loop + telemetry | Requires governance competency; logged |
| **Red** | Observer (monitor logs + off-switch) | Tier 4 (high autonomy; audited) | Human-out-of-the-loop with audit | Reserved; review-board only; never for care |

This crosswalk makes EDENA legible to regulators, auditors, and academics — and future-proof: if a hospital standardizes on NIST or an academic cites Knight Columbia, NAIO already maps.

---

## 4. Prohibited practices (grounded in EU AI Act Art. 5 + nursing ethics)

NAIO refuses these at **every tier**, mirroring EU AI Act prohibitions (S5) filtered through nursing ethics (S8, S9):

- No **manipulation or exploitation of vulnerabilities** (age, disability, illness, socio-economic).
- No **social scoring** or ranking of patients/colleagues by traits.
- No **emotion inference for surveillance** of staff or students (S5 carves out medical/safety; NAIO stays clear of surveillance entirely).
- No **autonomous clinical decisions** for an identified patient (S8).
- No **PHI** outside an approved BAA-covered environment.
- No action that **stratifies care** to exclude those who cannot afford options (S8 health-equity duty).

---

## 5. Gap analysis — what v1 missed and v2 fixes

| # | Gap in v1 | Source | v2 fix |
|---|---|---|---|
| G1 | Tier bundled functionality + permissions + autonomy | S1, S10 | Separate the three levers; tier = autonomy ceiling only |
| G2 | No reversibility concept | S4, S8 | `reversibility` class forces a gate for irreversible actions at any tier |
| G3 | No tool-use / permission scoping model | S10 | `permission_scoping` block: least-privilege, read-only defaults, user-context execution, complete mediation |
| G4 | No runtime monitoring / behavioral drift | S4 | `monitoring` block: telemetry, drift detection, anomaly response |
| G5 | No crosswalk to external standards | S1–S11 | `crosswalk` block embedded in policy |
| G6 | No explicit prohibited practices | S5, S8 | `prohibited_practices` block |
| G7 | Automation-bias / rubber-stamping unaddressed | S1, S3, S7 | Anti-rubber-stamp gate design; meaningful-review requirements |
| G8 | Memory/context poisoning unaddressed | S11 (ASI06) | Memory-integrity rules in florence-x |
| G9 | Delegation accountability shallow | S4 | Delegation boundary: oversight follows delegation; provenance + tier inheritance |
| G10 | No enablement / graduated-trust path (over-restriction → shadow AI) | S6, balance | `progression` block: how a nurse earns higher tiers responsibly |
| G11 | No continual-improvement loop | S6 (ISO 42001 PDCA) | `lifecycle` block: plan-do-check-act review cadence |
| G12 | No transparency/disclosure duty | S5 | Transparency rule: AI involvement disclosed; no impersonation of a licensed human |

---

## 6. The balance principle (why this is not just restriction)

Over-restriction has its own failure mode: nurses route around a system that won't help them, into ungoverned consumer tools ("shadow AI"). A *balanced* policy must **enable as deliberately as it restricts**:

- **Green is genuinely useful**, not a sandbox — drafting, learning, organizing, synthesis.
- **A graduated-trust path** lets a nurse *earn* Orange through demonstrated competency, not be permanently capped.
- **Least-privilege is scoped per task, not blanket-denied** — the agent gets exactly what the task needs.
- **The human gate is designed against rubber-stamping** — gates that fire too often train dismissal; gates are reserved for irreversibility, external effect, and scope boundaries.

> Stewardship is not fear. It is a nurse keeping the lamp *and* the ledger — present to the work, accountable for the outcome.

---

## 7. Doctrine, unchanged

> Agents propose. Humans judge. Nurses steward.

Boundary: no PHI, no patient-specific clinical decisions, no replacement for licensed judgment.
