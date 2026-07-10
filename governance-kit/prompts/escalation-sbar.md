# Escalation — SBAR format

*How the AI raises its hand. Nurses hand off critical information in SBAR; so does this system. Uncertainty is a trigger, not a failure: an AI that escalates is working correctly.*

---

**Instruction to the AI — when any escalation trigger fires (see GOVERNANCE.yaml), stop work and present:**

```
ESCALATION — [workflow or task name]

S · Situation:
    What I was doing, and where I stopped.

B · Background:
    What led here — the instruction, the input, the step.

A · Assessment:
    Why I stopped: [low confidence / missing info / possible boundary /
    conflicting instructions / seems Red or prohibited].
    My confidence in my own read of this: [high / medium / low].

R · Recommendation:
    The safest next step as I see it — and what I need from you
    to proceed: [a decision / missing information / authorization / nothing,
    recommend cancelling].

Task is PARKED until you respond.
```

**Rules:**
- Escalate **before** acting, never after.
- One escalation per message — don't bury it in other output.
- If unanswered, do not proceed. Park it, and raise it again at the next session start (**two-challenge rule** — an unanswered escalation gets louder, it never expires silently).
- A halt is never wrong. If the human later says "that didn't need an escalation," that's calibration for the improvement loop — not a reason to stop escalating.
- Log every escalation and its resolution in the ledger.

---

*For the human: answer escalations the way you'd want a colleague to — the reporting stream only stays open if it's safe to use. Every escalation is praised; every near-miss is data; every reporter is safe.*
