# Workflow: Draft a public-facing article on nurse AI adoption

<!-- EXAMPLE — the framework's canonical worked example, filled in.
     This is what a fully governed Yellow/Red workflow looks like. -->

```
Tier:                    Yellow (drafting) → Red (publishing step)
Claim type:              Educational / professional
Evidence requirement:    Source-backed with citations
PHI status:              No PHI allowed
Patient-specific:        No
Human review required:   Yes
Nurse-governed review:   Yes
External-facing:         Yes
Ledger entry required:   Yes
Automation ceiling:      L2 (draft) + L3 (coordination)
Escalation owner:        [owner's name]
```

## Purpose

Produce a source-backed draft article for the owner to review, revise, and publish under their own name and judgment.

## Steps

| # | Step | Who | Level |
|---|------|-----|-------|
| 1 | Owner requests the article and provides topic, audience, and any sources | Human | — |
| 2 | Gather and summarize owner-provided sources; flag anything unverifiable | AI | L1 |
| 3 | Draft the article, every claim tied to a source; list open questions at top | AI | L2 |
| 4 | Create a review checklist (claims vs. sources; tone; no identifiable people) | AI | L3 |
| 5 | **Gate: owner actively reviews** — spot-checks two citations against their sources, confirms no person is identifiable, owns every claim | Human | — |
| 6 | Owner revises and approves the final text | Human | — |
| 7 | **Red step: owner publishes** — the AI never posts, submits, or sends | Human | — |
| 8 | Ledger entry: tier, sources used, what was edited at the gate | AI | L4 |

## Escalation triggers for this workflow

- A claim can't be tied to an owner-provided or verifiable source → halt, list the claim, ask.
- The draft would identify a real patient, colleague, or employer → halt (prohibited zone).
- The owner asks the AI to publish directly → refuse, cite this header, remind: external-facing steps are human-only.

## Last reviewed

2026-07-03 — Initial version, from the Domondon Dominium master framework example.
