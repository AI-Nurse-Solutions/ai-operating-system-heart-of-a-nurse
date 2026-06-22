# Team Lab Core Skills

Start with 3–4 skills only. Do not create a skill for every prompt. Create skills only for workflows the team repeats.

## summarize-meeting

```markdown
---
name: summarize-meeting
description: Summarize a meeting transcript or chat thread and extract decisions, owners, and next actions.
---

You are summarizing a meeting for the Team Lab.

When I give you a transcript, notes, or chat export:
1. Read everything once.
2. Identify key decisions, open questions, action items, important context, and risks.
3. Output:

## Summary
3–7 bullets.

## Decisions
- Decision — context

## Action items
- Owner or suggested owner — task — timing if known

## Open questions
- Question — why it matters

Keep it concise and concrete.
```

## weekly-digest

```markdown
---
name: weekly-digest
description: Create a weekly digest for the Team Lab from notes, issues, PRs, and research.
---

Prepare the weekly Team Lab digest.

Include:
- highlights
- work shipped
- notable research or documents
- risks or blockers
- suggested focus for next week

Use source links when possible. Keep it under about 400 words.
```

## triage-inbox

```markdown
---
name: triage-inbox
description: Triage tasks, messages, or issues into priorities and owners.
---

Given a list of items, group similar items and assign:
- Priority: P0, P1, P2
- Suggested owner
- Suggested next step

Push back if input is too vague.
```

## research-brief

```markdown
---
name: research-brief
description: Create a concise research brief with sources, uncertainty, and next steps.
---

For a research question, produce:
- question
- answer summary
- source links
- evidence strength
- uncertainties
- practical implications
- next research step

Do not process PHI or confidential employer material.
```
