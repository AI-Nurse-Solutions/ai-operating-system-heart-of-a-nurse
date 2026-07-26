# Workflow: [name]

<!-- GOVERNANCE HEADER — the AI reads this before every run. Classify risk,
     data, and action independently. If any field is blank or exceeds the public
     ceiling, stop and ask the human. -->

```
Risk tier:               [Green / Yellow]
Data class:              [D0 / D1]
Action ceiling:          [Observe / Draft / Recommend]
Claim type:              [none / educational / personal / professional]
Evidence requirement:    [none / owner-provided sources only / source-backed with citations]
PHI status:              No PHI allowed        # this line never changes
Patient-specific:        No                    # this line never changes
Human review required:   [Yes / No — "Yes" for every Recommend step]
Nurse-governed review:   [Yes / No]
External-facing intent:  [Yes / No — the human performs every external action]
Ledger draft required:   [Yes / No — "Yes" for all Yellow]
Escalation owner:        [owner's name — from CHARTER.md]
```

## Purpose

[One sentence: what this workflow produces and for whom.]

## Steps

<!-- Declare the action mode per AI step. Green allows Observe/Draft only.
     Recommend begins at Yellow. The human performs all actions. -->

| # | Step | Who | Action mode |
|---|------|-----|-------|
| 1 | [Trigger — what starts this workflow] | — | — |
| 2 | [e.g., Read inputs the owner provides] | AI | Observe |
| 3 | [e.g., Draft the output] | AI | Draft |
| 4 | **Gate: owner reviews** — [what the owner actually checks, actively] | Human | — |
| 5 | [e.g., Owner sends/files/uses the output] | Human | — |
| 6 | Draft a ledger entry for the owner to review and append | AI | Draft |

## Escalation triggers for this workflow

- [e.g., "A source can't be verified" / "The draft would name a real person" / anything in GOVERNANCE.yaml escalation triggers]

## Last reviewed

[date] — [what changed, if anything] <!-- review in the monthly improvement loop -->
