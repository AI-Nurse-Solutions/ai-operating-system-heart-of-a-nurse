---
title: "Personal AGI Module Architecture — Core plus Six Sockets"
status: "Proposed design doctrine"
version: "0.1"
applicability: "Design record; no operational capability, hosted service, RAG index, analytics engine, or institutional authority is created by publication"
---

# Personal AGI Module Architecture — Core plus Six Sockets

## 1. Purpose

This document records the module architecture of the personal AGI: **every nursing role gets the same core system, and grows it incrementally by connecting modules** — their knowledge base, their learning academy, their projects (including a business), a data analysis engine, a market signal engine, and a guide. One core, six sockets, role-tuned connections.

It extends [`DESIGN.md`](DESIGN.md) (the Sphere-First doctrine): the core is what DESIGN.md already defines and the [Memory Fabric Kit](memory-fabric-kit/) already ships; the sockets are where the ecosystem's existing assets plug in, one at a time, without widening any ceiling.

## 2. The core (already shipped)

No module connects before the core exists, because every module inherits its discipline from the core:

- **SOUL file** — who this nurse is (SOUL Quiz / role profiles);
- **Sphere-scoped memory fabric** — what the AI knows about them (Memory Fabric Kit);
- **Trust ledger and handoff cards** — what the AI is allowed to do, with evidence (Memory Fabric Kit);
- **EDENA ceilings** — Green/Yellow, D0/D1, Observe → Draft → Recommend, per `governance-kit/GOVERNANCE.yaml`.

The core is the personal AGI. The modules are how it becomes *useful for a particular role* — they add reach, never authority.

## 3. The six sockets

Each socket names its existing anchor in this ecosystem — none of these starts from nothing.

| # | Socket | What it gives the nurse | Existing anchor | State today |
|---|---|---|---|---|
| 1 | **Knowledge Base** | Their own governed library: packs they trust, adapted to their school, specialty, and locality, retrieved with citations | NIN Knowledge Commons doctrine and playbook (`knowledge-commons/`); Knowledge Pack format; graph-ready hybrid RAG reference implementation in `naio-integrations/` | **Live (v0.1 pilot):** a personal governed library — pack manifest contract, fail-closed validator, human-accepted library lock, one reference pack, CI-guarded ([knowledge-base/README](knowledge-base/README.md)); the public Commons remains proposed doctrine |
| 2 | **Learning Academy** | AI-assisted formation for their role: commit-then-compare study, human evaluative authority, tiered AI literacy | Nurse Formation doctrine (`nurse-formation/`); Builder Academy; ASCEND; the role lanes' study workflows (FUTURE, TEACH); AI mentors and study-coach profile | Live as pages, doctrine, and role lanes |
| 3 | **Projects** | Every active life area — including a side business — as a governed project with its own prompt, 90-day win, and human gate | Life & Projects Quiz → `naio-projects.json` + per-project system prompts; Side-Gig Starter Kit and Playbook; Deliverable Studio (`naio-integrations/deliverables.py`) | Live end-to-end for personal projects; business lane live as kit |
| 4 | **Data Analysis Engine** | Analysis of the nurse's own no-PHI data: adoption signals, learning evidence, project metrics, manual CSVs | Phase 22 Adoption & Outcomes Ledger (`naio-os/scripts/outcomes.py`); DISCOVER lane's closed executable schemas | **Live (v0.1 pilot):** closed, declared analyses over the nurse's own no-PHI CSVs — fail-closed intake with PHI/secret/overclaim screens, deterministic per-analysis reports with provenance, CI-guarded ([data-engine/README](data-engine/README.md)) |
| 5 | **Market Signal Engine** | External AI and healthcare signals distilled through the NAIO ontology into role-relevant briefs | The NAIO distillation pipeline and its first records (`personal-agi/signals/`); Care Intelligence working paper (`care-intelligence/`) | **Live (v0.1):** records carry role-tuned five-line briefs rendered deterministically to `signals/briefs/`, CI-guarded ([signals/README](signals/README.md)) |
| 6 | **Guide** | The always-on front desk: orientation, boundaries, recovery, "what do I do next" | Mentor launcher; AI mentors; `when-things-go-wrong.html`; Hermes as Chief of Staff | Live as pages and SOUL posture |

## 4. Incremental activation doctrine

- **One socket at a time.** A module connects only after the previous one has settled into routine use. The order is role-tuned: a student connects the Academy first, a nurse entrepreneur connects Projects first, a leader may connect Signals first.
- **Connection is a ledger event.** Connecting a module is recorded in the trust ledger like a handoff-card change: what was connected, when, and what it may touch.
- **Modules enter at Observe/Draft.** A newly connected module starts at the bottom of the action-mode ladder regardless of how mature its anchor is, and climbs only by the ledger's promotion rules.
- **No module widens a ceiling.** Recommend remains the kit ceiling; D0/D1 remains the data boundary; the hard governance break before institutional-clinical surfaces applies to every socket. A knowledge base never becomes clinical authority; an analysis engine never touches PHI; a signal brief never becomes an instruction.
- **Role editions are configurations, not forks.** FUTURE, SHIFT, WINGS, LEAD, TEACH — and the adjacent lanes — differ in which sockets connect first and which anchors they point to, never in the core.

## 5. The surface: Mission Control Lite

The visible face of core-plus-sockets is [`mission-control-lite/`](mission-control-lite/) — a single-file, browser-local dashboard in the Life Dashboard's lineage: sphere tabs populated by the Life & Projects Quiz export, a module rail showing each socket's honest state (live, doctrine-ready, or planned) with role-tuned links, and the standing no-PHI and human-gate boundaries. It stores everything in the browser, uploads nothing, and activates nothing.

Its relationship to the rest of the surface family: the **Switchboard** preview remains the multi-role, multi-context navigation architecture; the **Hermes-built Mission Control** (`mission-control/`) remains the destination where role packets, the ADPIE workbench, and the Deliverable Studio run on the Integration Contract. Mission Control Lite is the incremental first rung a nurse can hold today.

## 6. What this document does not do

It does not activate a knowledge catalog, RAG service, analytics engine, signal automation, hosted dashboard, marketplace, curriculum, or institutional authority. Each socket's full activation is governed by its own doctrine and, where applicable, `GOVERNANCE.md` §3.

---

*Agents propose. Humans judge. Nurses steward.*
