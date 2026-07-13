# Trust cells, budgets, model routing, and connectors

Hermes profiles separate configuration and state; they are not host sandboxes. NAIO therefore compiles permissions through explicit trust cells and requires OS/container isolation for higher-consequence deployments.

## Cells

- **Steward local:** private non-PHI reading and drafting; no external side effects.
- **Untrusted intake:** public web reading only; no private files, memory writes, drafting, or execution.
- **Governed executor:** public-data execution against explicit targets, with proposal and approval.

A child cell may narrow but never re-grant authority.

## Budgets

- Calls are counted by a hashed run identifier and capability ID.
- The pre-call gate blocks when `max_calls` is exhausted.
- Oversized tool results are truncated before returning to the model.
- Tool timeout remains enforced by the underlying Hermes tool and manifest ceiling.

## Model fallback

Private non-PHI work may not silently change providers. Public work may use one manifested fallback. PHI is blocked rather than routed.

## MCP and connectors

Canary connectors require a strict manifest, HTTPS, an allowlisted host, public data, declared capabilities, and no token passthrough. Loopback, private-network, unknown-host, and redirecting endpoints are denied by default.
