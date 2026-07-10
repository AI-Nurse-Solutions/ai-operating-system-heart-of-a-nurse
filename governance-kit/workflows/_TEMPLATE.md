# Workflow: [name]

<!-- GOVERNANCE HEADER — the AI reads this before every run. All eleven fields required.
     Rules of the header: tier per GOVERNANCE.yaml; ceiling may be LOWER than the
     tier default, never higher; if any field is blank, treat the workflow as Red. -->

```
Tier:                    [Green / Yellow / Red]
Claim type:              [none / educational / personal / professional]
Evidence requirement:    [none / owner-provided sources only / source-backed with citations]
PHI status:              No PHI allowed        # this line never changes
Patient-specific:        No                    # this line never changes
Human review required:   [Yes / No — "No" only permitted on Green]
Nurse-governed review:   [Yes / No]
External-facing:         [Yes / No — "Yes" forces Tier: Red on the sending step]
Ledger entry required:   [Yes / No — "Yes" for all Yellow/Red]
Automation ceiling:      [L1 / L2 / L3 / L4]
Escalation owner:        [owner's name — from CHARTER.md]
```

## Purpose

[One sentence: what this workflow produces and for whom.]

## Steps

<!-- Declare the level per STEP. A workflow can be L4 at organizing and L1 at deciding. -->

| # | Step | Who | Level |
|---|------|-----|-------|
| 1 | [Trigger — what starts this workflow] | — | — |
| 2 | [e.g., Gather inputs the owner provides] | AI | L1 |
| 3 | [e.g., Draft the output] | AI | L2 |
| 4 | **Gate: owner reviews** — [what the owner actually checks, actively] | Human | — |
| 5 | [e.g., Owner sends/files/uses the output] | Human | — |
| 6 | Ledger entry | AI | L4 |

## Escalation triggers for this workflow

- [e.g., "A source can't be verified" / "The draft would name a real person" / anything in GOVERNANCE.yaml escalation triggers]

## Last reviewed

[date] — [what changed, if anything] <!-- review in the monthly improvement loop -->
