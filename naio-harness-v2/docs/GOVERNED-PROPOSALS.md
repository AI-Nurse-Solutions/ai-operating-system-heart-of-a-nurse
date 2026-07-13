# Durable governed proposals

Orange or side-effecting work is represented as a proposal, not a suspended model stack.

## Binding

Approval binds:

- proposal ID
- capability manifest hash
- target
- action digest
- reviewer role
- approval time

The persisted proposal never contains the action payload. The executor must present the original arguments; a changed digest invalidates approval.

## Restart rule

| Interrupted work | Recovery |
|---|---|
| Read-only and idempotent | May return to `approved` within retry ceiling |
| Side-effecting or non-idempotent | Returns to `needs_review`; prior approval is cleared |
| Retry ceiling reached | Tombstoned |
| Red risk | Cannot become an executable proposal |

The Kanban card is a review surface, not an authorization boundary. Runtime execution still validates proposal status, digest, lease, manifest, and approval.
