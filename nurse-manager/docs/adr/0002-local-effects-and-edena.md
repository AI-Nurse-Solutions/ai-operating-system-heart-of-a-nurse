---
title: "ADR 0002: Human-initiated local effects in a Personal workspace"
status: Accepted
date: 2026-09-28
decided_by: Robert Domondon (project steward, GOVERNANCE.md §1)
decided_on: 2026-09-28
---

# ADR 0002: Human-initiated local effects in a Personal workspace

## Context

The authoritative gateway policy
(`naio-integrations/config/edena-gateway-policy.json`) permits side
effects as follows:

- `prepare_action` and above need a tier whose action ceiling allows them.
- Yellow stops at `recommend`.
- Orange allows `act_with_approval`, but only with an authenticated
  organizational context that matches the workspace.

So in a personal tenant, **no request with side effects can pass the
gateway.**

For assistants, that is the right answer, and this ADR does not change
it. But G2 requires the manager to *save and export* their own brief.
The gateway was written to govern agents, models, memory, and tools. It
does not say how a person acting directly on their own local records is
governed.

## Decision

1. **Assistant-originated proposals** are evaluated by the authoritative
   EDENA engine at `recommend` mode, yellow tier, D1, in the
   `shared_professional` zone. Allowed means *the assistant may recommend
   it*. Execution still requires the manager's own approval and runs
   under the manager's authority. If EDENA denies, the action is recorded
   as denied with EDENA's reason codes.
2. **Human-originated local effects** are governed by a narrow profile
   table, `nurse-manager/config/manager-profile-policy.json`:
   - It **admits** only `export_markdown`, of an accepted revision, to a
     plain filename inside the workspace's `exports/` folder, after
     approval bound to the content hash and destination.
   - It **blocks** send, post, publish, upload, and external delete.
   - Unknown effects are denied.
3. The table can only narrow. It cannot grant any assistant capability.
   The EDENA policy stays authoritative wherever the two overlap.
4. The executor rechecks both the table and the approval immediately
   before acting. It re-reads the table from disk, so a change made after
   approval is seen.

## Alternatives considered

- **Model local export as `draft` mode so it passes Green.** Rejected:
  it mislabels a side effect, and that is how audit trails stop meaning
  anything.
- **Amend the gateway policy with a personal-tenant local-effect rule.**
  This is viable, and it is the long-term home. It changes EDENA posture,
  though, so it needs the steward's explicit decision. Until then, the
  profile table keeps the exception visible and small.

## Consequences

- Every effect in a Personal workspace has a proposal, an approval, a
  recheck, and a receipt, even though only one person is involved.
- Adding a new effect, such as "export to PDF", means editing a reviewed
  JSON table plus its tests. No code path can add one silently.

## Decision record

Accepted by the project steward, Robert Domondon, on 2026-09-28. This is a steward decision on EDENA posture under `GOVERNANCE.md` §3. He gave the approval as a direct instruction in the Claude Code session that drafted this ADR. He then explicitly authorized recording it here.
