# Stage 2 — Hermes EDENA Shadow Plugin

This plugin registers Hermes `pre_tool_call` and computes an EDENA decision without changing tool execution.

## Privacy

It records only timestamp, random event ID, profile, tool name, mapped capability ID, decision, reason code, and argument **field names**. It does not record argument values, prompts, results, sessions, users, credentials, or PHI.

## Canary installation

Do not enable in the default profile. Copy or symlink this directory into a dedicated Hermes canary profile and set:

```text
NAIO_HARNESS_ROOT=/absolute/path/to/naio-harness-v2
```

Stage 3 replaces observational behavior with fail-closed directives only after tests prove complete coverage and safe failure behavior.
