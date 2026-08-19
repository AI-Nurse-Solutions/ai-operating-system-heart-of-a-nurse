# NAIO models

Status: **proposed engineering plan.** Nothing here trains, ships, or serves a
model. No corpus exists in this directory, and none may be added without the
review path the plan describes.

| File | What it is |
|---|---|
| [`FINE-TUNING-PLAN.md`](FINE-TUNING-PLAN.md) | The plan: what to build, what to cut, what has to be true before a training run is justified at all |
| [`schema/training-example.schema.json`](schema/training-example.schema.json) | The record format for a governed training example. Every enum is drawn from `../config/edena-policy.yaml`, never invented |
| [`lint_dataset.py`](lint_dataset.py) | The gate. Refuses records carrying PHI-shaped text, unenforceable governance vocabulary, an approval with no reviewer, or an authored preference pair |

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
