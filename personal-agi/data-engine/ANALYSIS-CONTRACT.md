# Analysis contract — personal pilot v0.1

Every analysis is a directory:

```text
analyses/<slug>/
├── spec.json    # what the human declared: columns, operations, boundaries
├── data.csv     # the data, matching the declared columns exactly
└── report.md    # rendered by analyze.py — never hand-edited
```

## The spec

| Field | Required content |
|---|---|
| `title` | Short human title for the analysis |
| `question` | The question the human is asking of their own data |
| `edena_tier` | `green` or `yellow` — nothing higher runs here |
| `data_class` | `D0` or `D1`. Checked-in reference data must be synthetic `D0`; a nurse's own local data may be `D1` and stays on their machine |
| `columns` | Non-empty list of `{name, type}` with unique names; `type` is `string`, `number`, or `date` |
| `analyses` | Non-empty list of `{op, column?}` drawn from the closed vocabulary below |
| `provenance` | `source` (where the data came from) and `no_phi_attested: true` |
| `boundaries` | Non-empty `intended_use` and `not_claims` lists — what this analysis is for, and what it must never be read as |

## The closed vocabulary

| Op | Column | Result |
|---|---|---|
| `count` | — | Row count |
| `count_by` | any declared column | Frequency table, highest count first |
| `sum` | a declared `number` column | Total |
| `mean` | a declared `number` column | Average (2 decimals) |
| `min` / `max` | a declared `number` column | Smallest / largest value |

That is the whole vocabulary. An unknown op, an undeclared column, or a type mismatch is refused — the engine never improvises an analysis it was not asked for. New operations enter the vocabulary only by changing this contract in a reviewed change.

## Fail-closed intake

- **Closed schema.** The CSV header must match the declared columns exactly, in order. Every `number` cell must parse as a number; every `date` cell must be an ISO date; empty cells are refused. Data beyond 10,000 rows is refused — this is a personal engine, not a warehouse.
- **PHI and secret screens.** The whole spec and CSV are screened for PHI-like patterns (SSN-like, phone-like, clinical identifiers) and secret-like patterns (keys, tokens, credential assignments), inherited from the Phase 22 checker. Any hit refuses the analysis.
- **Overclaim screen.** The spec text is screened for outcome-overclaim phrases (clinical efficacy, patient-outcome improvement, ROI, staffing reduction, compliance validation, competency certification, performance evaluation, and kin). The screen is phrase-based and does not parse negations — keep claims language out of specs entirely; the report template carries the boundary language for you.

## The report

`report.md` is rendered deterministically — no model, no network, no clock — so the same spec and data always produce byte-identical output. It carries the question, the tier and data class, the row count, SHA-256 digests of both `data.csv` and `spec.json` (provenance: a report is bound to exact bytes), each declared result, and a fixed boundary block stating that results are observations for the nurse's own judgment — adoption signals and learning evidence, never efficacy or performance claims. `--check` re-renders every analysis into a temporary directory and fails CI when a checked-in report has drifted from its inputs.

*Agents propose. Humans judge. Nurses steward.*
