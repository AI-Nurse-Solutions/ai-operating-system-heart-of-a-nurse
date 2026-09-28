---
title: "ADR 0004: No model by default; one cloud AI service and a local option"
status: Accepted
date: 2026-09-28
decided_by: Robert Domondon (project steward, GOVERNANCE.md §1)
decided_on: 2026-09-28
---

# ADR 0004: No model by default; one cloud AI service and a local option

## Context

G4 adds bounded AI assistance. The plan requires the product to work
with no model and no API key. Connected AI must be optional, budgets
must be enforced, and provider failure must degrade to the no-model
path without silently choosing another cloud service.

## Decision

1. **Default: no model.** A new workspace has no AI provider configured,
   and every workflow works without one.
2. **Local option for privacy.** A manager may connect a model running
   on their own computer through a local server (the Ollama-compatible
   HTTP API on localhost). Text never leaves the device.
3. **One cloud AI service.** Exactly one cloud provider is offered. Which
   provider is a separate steward decision; until it is made, no cloud
   adapter ships.
4. **The same gates for every provider:**
   - Only material the workspace's data rules admit may be sent. The
     privacy screen runs before any request.
   - Assistant work is evaluated by the EDENA engine at `recommend`, per
     ADR 0002.
   - A cost budget is checked before any request.
   - Provider output is always a draft that a human must accept.
   - Provider failure returns to the no-model path and is reported; it
     never falls back to a different service.
5. **The manager chooses.** Connecting a provider is an explicit action
   in the workspace. It is never preselected, and never inferred from
   an environment variable.

## Consequences

- AI features are built provider-neutral: an adapter interface, budgets,
  and fallback are testable without any account.
- The local option depends on the manager's hardware. The app must say
  so, and must not claim capability it lacks.
- Before the cloud adapter ships: the provider's data-use, retention,
  and pricing terms must be reviewed; the key is stored in the
  operating system's credential store and is never written to logs,
  records, or exports.

## Decision record

Accepted by the project steward, Robert Domondon, on 2026-09-28. The
decision in the Claude Code session was: "default to no model, and offer
one cloud AI service plus the local option for privacy". The specific
cloud provider remains open.
