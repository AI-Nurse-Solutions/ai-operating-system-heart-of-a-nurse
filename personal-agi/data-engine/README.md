# Personal Data Analysis Engine — v0.1 pilot

The Data Analysis Engine socket of the [personal AGI module architecture](../MODULES.md), live at **personal scale**: analysis of the nurse's own no-PHI data — study logs, project metrics, adoption signals, manual CSVs — through **closed, declared analyses** rendered deterministically into reports the nurse can read and judge.

Its anchors are the Phase 22 Adoption & Outcomes Ledger (`naio-os/scripts/outcomes.py`), whose boundary doctrine this engine inherits — adoption signals and learning evidence only, never efficacy or performance claims — and the DISCOVER lane's closed-executable-schema discipline: the engine runs only a fixed vocabulary of declared operations, never arbitrary code and never a model.

## The pipeline

```text
analyses/<slug>/spec.json + data.csv   (the human declares columns, analyses, boundaries)
        ↓  analyze.py — fail-closed intake: closed schema, PHI/secret screens, overclaim screen
declared analyses only (count, count_by, sum, mean, min, max)
        ↓  deterministic rendering — no model, no network, no clock
analyses/<slug>/report.md — observations with provenance, guarded in CI by --check
```

Three rules make the engine trustworthy:

1. **Judgment at spec time only.** The human decides what to measure by writing the spec — declared columns, declared operations, declared boundaries. The engine adds no analysis of its own: unknown operations, undeclared columns, and unparseable cells are refused, not guessed at.
2. **Observations, never verdicts.** A report is a set of counts and sums over the nurse's own recorded data — Observe/Draft artifacts, hypotheses for human judgment. Per the Phase 22 boundary, results are adoption signals and learning evidence only: no clinical-efficacy, patient-outcome, safety, ROI, staffing, compliance, certification, or performance-evaluation claim can be produced here, and the overclaim screen refuses specs that reach for one.
3. **Fail closed on data hygiene.** The engine screens every spec and CSV for PHI-like and secret-like content and refuses on a hit. `no_phi_attested` must be true in every spec — the screen is a backstop, not a substitute for the attestation. Checked-in reference data is synthetic D0 only; a nurse's own local data stays on their machine (D0/D1, never higher) and is never committed here.

## Using it

```bash
# from the repository root:
python3 personal-agi/data-engine/analyze.py personal-agi/data-engine/analyses/study-sessions-sample   # render one analysis
python3 personal-agi/data-engine/analyze.py            # render every analysis
python3 personal-agi/data-engine/analyze.py --check    # exit 2 if any report is stale
```

The engine is deterministic and stdlib-only. The spec contract is specified in [`ANALYSIS-CONTRACT.md`](ANALYSIS-CONTRACT.md).

## The reference analysis

[`analyses/study-sessions-sample/`](analyses/study-sessions-sample/) — a **synthetic** study-session log (not a real nurse's data) with a spec asking: *where is my study time going, and am I committing to my own answer before comparing with the AI?* Its rendered [`report.md`](analyses/study-sessions-sample/report.md) shows the format: results with provenance digests, then the boundary.

## Boundaries

No PHI ever enters an analysis directory — not in data, not in specs, not in reports. Reports do not feed employer analytics, competency scoring, or discipline: a nurse's personal data fabric is never employer-readable through this engine, and nothing here publishes, sends, notifies, or escalates anything. The engine activates no dashboard, no automatic reporting, and no institutional authority.

*Agents propose. Humans judge. Nurses steward.*
