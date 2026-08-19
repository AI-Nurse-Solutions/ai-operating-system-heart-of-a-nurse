# NAIO models

Status: **proposed engineering plan.** Nothing here trains, ships, or serves a
model. No corpus exists in this directory, and none may be added without the
review path the plan describes.

| File | What it is |
|---|---|
| [`FINE-TUNING-PLAN.md`](FINE-TUNING-PLAN.md) | The plan: what to build, what to cut, what has to be true before a training run is justified at all |
| [`schema/training-example.schema.json`](schema/training-example.schema.json) | The record format for a governed training example. Every enum is drawn from `../config/edena-policy.yaml`, never invented |
| [`lint_dataset.py`](lint_dataset.py) | The gate. Validates every record against the schema above, then refuses PHI-shaped text found anywhere in the record, ids reused across files, duplicated JSON keys, and sealed splits holding harvested records |

The single idea underneath all three: **the model proposes, the policy engine
decides.** `edena-policy.yaml` is read by the runtime on every turn and is the
authority on tiers, tool classes, permissions, and gates. A fine-tuned model's
job is to read a nurse's request into the inputs that engine needs, and to write
a rationale a human can audit. It never holds the decision.

Run the gate before any corpus is used:

```bash
python3 naio-os/models/lint_dataset.py path/to/corpus/*.jsonl
```

It imports `PHI_PATTERNS` from `../mission-control/adapters/phi.py` so the corpus
gate cannot drift from the runtime gate. It is detection, not proof, and it never
replaces the reviewer's read.

Two rules keep the checks from drifting apart. Structure — types, patterns,
enums, required fields, closed objects, conditionals — lives only in the schema
and is enforced by validating against it, never by a second hand-rolled copy of
the same rule. Everything the schema cannot express is explicit in the gate: PHI
anywhere in the record, ids reused across files, sealed splits staying sealed.

Validation is required, not best-effort: a missing `jsonschema` refuses the run
rather than passing the corpus, the same posture `../scripts/import-soul.py`
takes. Install `../requirements-import-soul.txt` to run the gate.
