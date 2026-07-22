# FUTURE Synthetic Sample Mission

## Demonstration boundary

This mission demonstrates the complete Assess–Diagnose/Define–Plan–Implement–Evaluate loop in a private FUTURE sandbox. Every person, schedule, source status and result is synthetic. It contains no patient information, person-level school/employer data, live assessment, clinical direction or real outcome.

It is not evidence of enrollment, employment, scope, delegation, competence, certification, licensure, academic compliance or readiness for care. It must not earn a badge, AI Literacy Passport stage, grade or portfolio validation.

## Mission record

| Field | Synthetic value |
|---|---|
| Mission ID | `future-demo-mission-001` |
| Product/lane | `future-nursing-student-assistant-mission-control` / `nursing_student_assistant` |
| Home/route | FUTURE Mission Control / `/nursing-students-assistants/dashboard` |
| Workspace | Bridge Learning Studio (`bridge_academic_learning`) |
| Relationship | Primary |
| Protected context | Learning |
| Mission type | Learning plan and study-sprint rehearsal |
| Goal | Draft a realistic two-week retrieval-and-teach-back plan for a fictional fundamentals unit using only approved non-sensitive learning material. |
| Build workflow | `FUT-WF-03` — canonical recipe 3, Study sprint and teach-back |
| Primary power | `FUT-PWR-04` — canonical Power 4, Active Learning & Study Sprint Engine |
| Supporting power | `FUT-PWR-07` — canonical Power 7, SAFE Prompt & AI Literacy Lab |
| Templates | `FUT-TPL-02` SAFE Prompt Card; `FUT-TPL-03` AI Use & Integrity Receipt |
| State | Simulation / Draft artifact |
| EDENA | Yellow — academic and professional learning relevance; verify sources, rules and learner authorship |
| Inactive agent candidates | `FUT-AGT-02` learning/teach-back coach and `FUT-AGT-05` SAFE boundary sentinel; recommendations only |
| AI/agent/tool state | AI suggestion only; both candidates remain `PERM-P0 Disabled` with no run grant; tools Disabled/empty; automation Manual/Preview; external action Off |
| Data boundary | Synthetic, public and owner-controlled nonsensitive only |
| Human routes | Authorized faculty/program contact for academic rule and source questions; no route is configured in this demo |

## Start a Mission input

> I want a two-week study rhythm for a fictional fundamentals unit. My schedule changes, and I tend to reread instead of testing what I know. Help me create short retrieval sessions and teach-backs. Do not do assessed work, provide answer keys, use patient information, claim that I am competent, or save/send anything.

Mission Control first shows:

- **Active context:** Learning
- **Data check:** No PHI, person records, live-care content, restricted assessment or secret detected in the synthetic input
- **Authority check:** Academic AI-use rule Unknown; general private study coaching only
- **Integrity check:** Attempt before answer and learner authorship required
- **Action state:** Exploration/Simulation only
- **Controls:** Pause, revise, return to an earlier stage, delete, or start a new iteration

## Stage 1 — Assess

### Verified or bounded facts

- The mission is a synthetic private-learning demonstration.
- The requested output is a study-process draft, not clinical advice or assessed work.
- The user requested short retrieval sessions and teach-backs.
- The build catalog binds `FUT-WF-03` to the canonical Study sprint and teach-back recipe and `FUT-PWR-04`.
- Academic rules, actual course sources and a faculty route are not configured.

### User-provided information

- The fictional schedule varies.
- The fictional learner often rereads instead of retrieving.
- The requested horizon is two weeks.

### Assumptions to display, not silently adopt

- Four 20-minute sessions may fit the synthetic capacity better than long sessions.
- An instructor-approved source would be available in a real mission.
- A teach-back can be written or spoken privately without a second person.

### Unresolved questions

1. Which current program or course AI-use rule applies in a real mission?
2. Which exact approved source and version may the learner use?
3. Are self-generated practice questions permitted?
4. What schedule windows are genuinely available and safe?
5. What should be asked of an authorized faculty member?

### Assess output

`ART-FUT-DEMO-001 — Synthetic Mission Brief`, status **Draft / Not externally reviewed**.

The user may edit the goal, answer one question, skip a nonessential item, choose session-only handling, or return to the dashboard.

## Stage 2 — Diagnose or Define

### Central need

Create a small, repeatable study process that makes recall and uncertainty visible while preserving learner authorship and academic rules.

### Contributing factors

- Variable available time
- Passive rereading habit
- Unknown program AI-use rule
- No approved source configured
- Risk of mistaking AI fluency for learning

### Root-cause statement

The synthetic problem is not a lack of generated content. It is the absence of a realistic retrieval rhythm, a verified source boundary and an independent check of what the learner can explain without AI.

### Risk and boundary review

- **Academic integrity:** Yellow. No live or restricted assessment; learner attempts first; disclose AI assistance if applicable.
- **Clinical:** No live care or patient content. General learning process only.
- **Privacy:** No PHI or person-level school/employer information.
- **Authority:** The system cannot determine permission, competence or clinical readiness.
- **Automation:** Manual/preview only. No calendar write, reminder, message, submission or storage action.

### Define output

`ART-FUT-DEMO-002 — Problem and Boundary Statement`, status **Draft / Learner review required**.

## Stage 3 — Plan

### Options

| Option | Benefit | Time/burden | Risk | Fit with values and boundaries |
|---|---|---|---|---|
| A. Four short retrieval sprints plus two teach-backs | Makes recall and uncertainty visible; manageable | About 80–100 synthetic minutes over two weeks | May reveal gaps; needs approved source | Strong fit; learner does the work |
| B. Two longer review blocks | Fewer schedule decisions | About 120 minutes; higher fatigue risk | Can drift into rereading | Moderate fit |
| C. Generate a large AI study guide | Fast artifact | Low initial time, high verification burden | Dependency, inaccuracies, ghost authorship | Poor fit; reject for this mission |

### Selected draft plan

Select Option A only as a proposal:

1. Learner chooses one small topic from an approved source.
2. Learner writes what they remember before asking AI.
3. AI may ask process-focused retrieval questions or help organize the learner's gaps; it does not provide a live answer key.
4. Learner checks claims against the approved source and records unresolved questions.
5. Learner produces a short teach-back without AI visible.
6. Learner compares the teach-back with the source, corrects it, and names one question for a human.
7. Repeat four times; evaluate the process, not clinical competence.

### Success and balancing measures

- Four planned synthetic sprints, with completion recorded honestly
- At least two learner-authored teach-backs
- Each claim checked against the selected approved source
- Every uncertainty retained in the human-question queue
- Zero patient/person-level/restricted-assessment data
- Zero external action
- Burden remains within the learner's selected capacity mode
- Ability to describe one independent next step without AI

### Stop conditions

Stop and route if the user introduces patient details, a live-care question, restricted assessment content, an answer key, an instruction to deceive, a request for scope/competency determination, person-level school/employer information, a credential or secret. Pause and ask a human if the academic rule or source authority is unclear.

### Plan outputs

- `ART-FUT-DEMO-003 — SAFE Prompt Card`, using `FUT-TPL-02`
- `ART-FUT-DEMO-004 — Two-Week Study Sprint Draft`

Both remain **Draft / Synthetic / Not approved for external use**.

## Stage 4 — Implement

Implementation here means creating draft local artifacts, not carrying out clinical, school, employment or external actions.

### Synthetic SAFE Prompt Card

- **Situation:** Private synthetic study-process rehearsal for a fictional fundamentals unit; no patient, person-level school/employer or live-assessment content.
- **Aim:** Help the learner organize four short retrieval sprints and two teach-backs.
- **Facts:** Only learner-provided non-sensitive schedule constraints and a human-approved source may be used. No source is configured in the demo.
- **Expectations:** Ask the learner to attempt first; label uncertainty; do not supply an answer key, complete coursework, claim competence, save, send, schedule or activate anything; end with verification and a human-question queue.

### Synthetic two-week checklist

- [ ] Confirm the real academic AI-use rule before a real run.
- [ ] Select one approved current source; record owner, title/version/date and access path without restricted content.
- [ ] Choose four 20-minute private windows manually.
- [ ] Sprint 1: retrieval attempt → source check → correction → one human question.
- [ ] Sprint 2: retrieval attempt → source check → first teach-back → correction.
- [ ] Sprint 3: retrieval attempt → source check → misconception repair.
- [ ] Sprint 4: retrieval attempt → source check → second teach-back → correction.
- [ ] Write an AI Use & Integrity Receipt using `FUT-TPL-03`.
- [ ] Evaluate process burden and independent next step.

### Human confirmation gate

Before adopting the plan, Mission Control asks:

> Approve this exact private draft for local manual use only? It will not write a calendar, send a reminder, submit work, contact a person, activate a power, call an agent/tool or claim learning/competence. If the source, rule, context or task changes, approval expires.

The demo records **No approval provided**. It therefore remains a simulation.

### Implementation outputs

- `ART-FUT-DEMO-004 — Two-Week Study Sprint Draft`, **Simulation only**
- `ART-FUT-DEMO-005 — AI Use & Integrity Receipt`, **Draft**
- Activity event: `draft_created`; no `authorized_execution` event

## Stage 5 — Evaluate

For interface testing only, load this explicitly synthetic result set:

| Measure | Synthetic target | Synthetic observation | Interpretation |
|---|---:|---:|---|
| Planned sprints | 4 | 3 | Process was partly feasible; reduce or reschedule rather than claim failure. |
| Teach-backs | 2 | 2 | Artifact count met; quality and competence were not determined. |
| Source checks | Every completed sprint | 3 of 3 | Synthetic process adherence only. |
| Human questions captured | At least 1 | 2 | Questions remain unresolved until a responsible human responds. |
| Prohibited data used | 0 | 0 | Synthetic fixture passed the data-boundary check. |
| External actions | 0 | 0 | No send, schedule, submission or connection occurred. |
| Reported burden | Sustainable | One skipped sprint during a high-load week | Minimum/re-entry mode may fit better. |

### What worked

- Attempt-before-answer made the learner's own recall visible.
- Short sessions fit the synthetic schedule better than long blocks.
- Source checks and the human-question queue preserved uncertainty.

### What did not work or remains unknown

- One sprint was not completed.
- The demo cannot establish durable knowledge, competence or exam readiness.
- Academic rule, approved source and faculty review are still Unknown.
- No real person validated the artifacts.

### Decision

**Modify and iterate.** Keep three required sprints and make the fourth optional Stretch work. Before any real use, verify the academic rule and source with an authorized human. Do not activate automation.

### Evaluate outputs

- `ART-FUT-DEMO-006 — Synthetic Evaluation Note`
- mission state `evaluated_demo`
- no badge evidence and no Passport advancement

## Next Assess iteration

The visible loop returns to Assess with:

- revised capacity mode: Minimum during high-load weeks;
- proposed target: three required sprints plus one optional sprint;
- unresolved academic rule and source questions carried forward;
- all prior assumptions, changes and synthetic labels preserved; and
- powers inactive, agents/tools disabled, external action Off.

The user can pause, revise an earlier stage, discard the demo, or start a new mission. Deleting the demo must not delete a real user mission.

## Required interface labels for this sample

- `SYNTHETIC DEMO — NOT A REAL LEARNER RECORD`
- `LEARNING CONTEXT`
- `EDENA YELLOW — VERIFY RULES, SOURCES AND AUTHORSHIP`
- `DRAFT / SIMULATION — NOT AUTHORIZED EXECUTION`
- `NO PHI OR PERSON-LEVEL SCHOOL/EMPLOYER DATA`
- `NO CLINICAL, ACADEMIC, EMPLOYMENT OR CREDENTIAL CLAIM`
- `AGENTS DISABLED · TOOLS DISABLED · EXTERNAL ACTION OFF`
