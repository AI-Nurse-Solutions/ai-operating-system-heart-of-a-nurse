# Stage 3 Canary

This is an enforcement canary, not a production or clinical profile.

## Required environment

```text
NAIO_HARNESS_ROOT=/absolute/path/to/naio-harness-v2
NAIO_EDENA_MODE=enforce
NAIO_RUNTIME_CONFIG=/absolute/path/to/naio-harness-v2/config/runtime-profile-enforce.json
NAIO_SHADOW_LOG=/private/local/path/edena-canary-events.jsonl
```

## Boundaries

- Synthetic, public, or private non-PHI test data only.
- No patient stories, employer systems, personnel records, payments, or credentials.
- Unknown tools fail closed.
- Safe local reads and local drafts may proceed.
- External publication-class calls require Hermes native human approval.
- Evaluator/config/plugin errors block.

Do not enable in the default profile until the full evaluation suite and rollback drill pass.
