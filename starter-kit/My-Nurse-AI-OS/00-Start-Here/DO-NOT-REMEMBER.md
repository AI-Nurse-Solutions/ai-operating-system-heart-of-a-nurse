# Do Not Remember — the memory boundary

Your AI's memory is powerful precisely because it persists. That is why some things must never enter it. This file is loaded at every session start (see the Governance boot in your SOUL file): items below are **refused at intake** — not stored and later deleted, never stored at all. If something on this list appears in conversation, the AI may use it for the current task only and must not write it to Memory, USER files, skills, or summaries.

## The global baseline — applies to every nurse, every sphere

1. **Patient information of any kind.** Names, initials, rooms, dates, diagnoses, story-shaped fragments that could re-identify ("the 34-weeker from Tuesday"). If it could identify a patient, it counts.
2. **Credentials and secrets.** Passwords, API keys, tokens, recovery codes, payment card or bank numbers — yours or anyone's.
3. **Other people's personal data.** Colleagues, classmates, clients, family members: no health information, no performance judgments, no private circumstances beyond a first name and context you explicitly pin.
4. **Employer-confidential material.** Internal policies, incident details, staffing disputes with named people, anything from systems your organization controls.
5. **Inferential health data about you.** Health regulators reach further than you may think — "health information" includes anything that lets someone *infer* a condition (searches, purchases, patterns). Your own health mentions stay session-only unless you explicitly say "remember this."
6. **Anything you wouldn't want resurfacing.** The standing test: *would I be comfortable if this appeared, verbatim, in a session six months from now with someone looking over my shoulder?*

## Audience extensions (added by your module)

| If you are… | Additionally never remember |
|---|---|
| **Student** | Grades and GPA · other students · clinical-placement patients (absolute) · the text of graded assignments (process logs only) · accommodation status unless re-confirmed each term |
| **Bedside / APRN** | Patient story-fragments in any form · unit conflicts with named colleagues · your own health beyond explicit pins |
| **Manager / Leader** | Named-staff performance information (HR systems only) · grievance and disciplinary content · incident details with identifiable actors |
| **Entrepreneur** | Client personal or health details beyond a pinned first name + context · anything about clients usable for marketing without their affirmative consent |

## How to use this file

- **Tell your AI once** (the Governance boot already does): *"Apply my Do-Not-Remember rules from 00-Start-Here/DO-NOT-REMEMBER.md at intake — refuse to store these, don't store-then-redact."*
- **Audit quarterly:** ask *"Show me everything in Memory and USER files that might violate my Do-Not-Remember rules"* and delete on sight.
- **When in doubt, session-only.** Memory is earned, not default.

> Agents propose. Humans judge. Nurses steward. · No PHI, ever.
