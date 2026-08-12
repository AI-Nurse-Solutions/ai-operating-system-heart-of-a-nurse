# Market Signal Engine — v0.1

The Signals socket of the [personal AGI module architecture](../MODULES.md), live end-to-end: external AI and healthcare signals are distilled through the NAIO ontology into structured records, and each record carries **role-tuned briefs** rendered into per-role markdown a nurse can read in under a minute.

## The pipeline

```text
external signal (news, launch, paper, policy)
        ↓  NAIO distillation (judgment happens here, once)
signals/<date>-<slug>.json     ← schema-valid record + role_briefs
        ↓  render_briefs.py (deterministic — no model, no network)
signals/briefs/<slug>/<role>.md
```

Two rules make the pipeline trustworthy:

1. **Judgment at distillation time only.** The role-tuned text is written when the signal is distilled and lives in the record's `role_briefs` field. The renderer adds no role-specific judgment of its own — only a fixed template of headings, provenance labels, and boundary text. It is testable in CI, and `--check` fails the build if the checked-in briefs drift from their records.
2. **A brief is a hypothesis, never an instruction.** Every rendered brief says so, cites its source record, and inherits the record's evidence tier. Briefs are Green/D0, Observe/Draft artifacts.

## The brief format

Each record may carry `role_briefs`: a map of role lane → five one-line fields.

| Field | Question it answers |
|---|---|
| `what_happened` | The signal, stripped of hype, in one line |
| `why_it_matters_to_you` | Why *this role* should care |
| `do_now` | One governed action available today |
| `dont_do` | The boundary this signal makes tempting to cross |
| `watch` | The early-warning sign for this role |

Role lanes in v0.1: `student`, `staff`, `np`, `leader`, `educator`. Adjacent lanes (ROUNDS, BREATHE, DISCOVER, STEWARD, THRIVE) can be added per record as relevant. A record without `role_briefs` is a valid distillation that simply has no briefs yet.

`role_briefs` is a NAIO-local extension of the distillation schema (records without it remain valid; nothing else in the record changes).

## Rendering

```bash
python3 personal-agi/signals/render_briefs.py            # regenerate briefs/ in place
python3 personal-agi/signals/render_briefs.py --check    # exit 2 if briefs/ is stale
```

Rendered briefs are checked in under [`briefs/`](briefs/) so nurses can read them on GitHub or the site without running anything. Do not hand-edit rendered briefs — edit the record and re-render.

## Boundaries

No PHI ever appears in a signal record or brief. Briefs do not instruct clinical action, do not certify vendors, and do not substitute for institutional review. The Refusal Posture governs every distillation: compression, substitution, and sidelining exposures are tested per record, and a brief's `dont_do` line is where those findings reach the bedside reader.

*Agents propose. Humans judge. Nurses steward.*
