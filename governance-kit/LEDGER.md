# LEDGER

*Append-only. The AI adds an entry for every significant piece of work; the owner adds gate decisions and reviews. Never rewrite or delete past entries. Never any patient information — describe work generically.*

*Why this file exists: the record protects the people affected by the work, then your license, then you. If it isn't in the ledger, it didn't happen.*

**Entry format:**

```
### YYYY-MM-DD · [short task name]
- Tier: Green / Yellow / Red
- Level used: L1–L4 (ceiling: Lx, from workflow header)
- AI did: [one line — retrieved / drafted / organized / halted / escalated]
- Human decision: [approved / approved with edits / rejected / authorized Red task / n/a]
- Notes: [anything worth remembering — what was edited and why, escalation outcome, near-miss]
```

---

### 2026-07-03 · Example — weekly brief drafted
- Tier: Green
- Level used: L3 (ceiling: L4)
- AI did: Drafted Monday brief from task list and calendar notes; created two reminders.
- Human decision: Approved with edits (reordered priorities).
- Notes: Owner moved certification deadline to top — brief template updated to always lead with deadlines. (Improvement loop item.)

### 2026-07-03 · Example — boundary refusal
- Tier: Red (prohibited)
- Level used: L0
- AI did: Halted. A pasted document included what appeared to be patient-identifying details; refused processing, reminded owner of the No-PHI rule, suggested removing identifiers before resubmitting.
- Human decision: Confirmed — resubmitted with identifiers removed; reclassified Green.
- Notes: Correct halt. Praised per andon rule. This is the system working, not failing.

<!-- New entries below this line. Append only. -->
