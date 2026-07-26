# LEDGER

*Append-only. The AI may draft an entry for significant work; the owner reviews and appends it. Never rewrite or delete past entries. Never any patient information — describe work generically.*

*Why this file exists: the record protects the people affected by the work, then your license, then you. If it isn't in the ledger, it didn't happen.*

**Entry format:**

```
### YYYY-MM-DD · [short task name]
- Risk tier: Green / Yellow / Orange / Red-P / Red-E
- Data class: D0 / D1 (D2–D4 unavailable in this public kit)
- Action mode: Observe / Draft / Recommend
- AI did: [one line — retrieved / drafted / organized / halted / escalated]
- Human decision: [approved / approved with edits / rejected / escalated outside this public kit / n/a]
- Notes: [anything worth remembering — what was edited and why, escalation outcome, near-miss]
```

---

### 2026-07-03 · Example — weekly brief drafted
- Risk tier: Green
- Data class: D1
- Action mode: Draft
- AI did: Drafted Monday brief from task list and calendar notes; proposed two reminders without creating them.
- Human decision: Approved with edits (reordered priorities).
- Notes: Owner moved certification deadline to top — brief template updated to always lead with deadlines. (Improvement loop item.)

### 2026-07-03 · Example — boundary refusal
- Risk tier: Red-P
- Data class: D3 suspected
- Action mode: none — refused
- AI did: Halted. A pasted document included what appeared to be patient-identifying details; refused processing, reminded owner of the No-PHI rule, suggested removing identifiers before resubmitting.
- Human decision: Confirmed — resubmitted with identifiers removed; reclassified Green.
- Notes: Correct halt. Praised per andon rule. This is the system working, not failing.

<!-- New entries below this line. Append only. -->
