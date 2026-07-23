# My ROUNDS — Resident Command Center

Create exactly one responsive, accessible home in the isolated `medical_resident` lane. Do not place it inside, beside, or under a nursing population page. Do not share dashboard state, navigation, record queries, memories, permissions, approvals, agents, or history with another population.

## Core Four

1. **Orient My Day & Duty** — active hat, rotation and supervision, fixed commitments, Top Three, required human check, recovery anchor, protected-life item, and Plan B.
2. **Learn & Reason** — generic evidence, synthetic cases and reasoning, skills, exams, uncertainty, bias reflection, and source verification.
3. **Orchestrate & Communicate** — CIRCLE, synthetic handoff, consult, transition, teaching, or team communication; patient-specific use only in a separately approved clinical workspace.
4. **Review, Escalate & Close** — ATTEND, sources, duty and recovery, exact human decisions, closed loops, official destination, agent review, expiry, and fallback.

Keep the optional fifth launcher empty until a resident separately previews and approves one of: Teach; Improve Safety; Research; Career Sprint; or Agent Control Tower. Never auto-fill it.

## Ready-to-render resident-only dashboard

Render the following Markdown in `My ROUNDS`. Use `Unknown — human verification required` rather than inventing values. In Private mode, care-orchestration panels are synthetic or process-only and contain no patient content. In an approved institutional context, omit the private whole-life panel and never import its records.

~~~markdown
# My ROUNDS

**RESIDENT:** {{authenticated_owner}} • **SPECIALTY / PGY:** {{specialty}} / {{pgy}}  
**ACTIVE HAT:** {{primary_hat}} {{secondary_hat_or_none}} • **SITE / ROTATION:** {{site}} / {{rotation_or_service}}  
**CONTEXT:** {{private_resident_os_or_approved_subcontext}} • **SUPERVISION:** {{task_specific_status_or_unverified}}  
**ACCOUNTABLE ATTENDING / ROUTE:** {{human_owner_and_contact_route}} • **SOURCE FRESHNESS:** {{current_stale_or_unknown}}  
**STATE:** No-PHI {{state}} • Private memory {{state}} • Connectors {{off_or_approved}} • Agents {{active_count}}/10 • Powers {{active_count}}/24

| Core Four | Resident-controlled launch |
|---|---|
| 1. Orient My Day & Duty | `[Open orientation]` |
| 2. Learn & Reason | `[Open learning studio]` |
| 3. Orchestrate & Communicate | `[Open synthetic or approved CIRCLE studio]` |
| 4. Review, Escalate & Close | `[Run ATTEND and close loops]` |
| Optional fifth | Empty — requires separate preview and approval |

## Focus now — maximum seven

| # | Attention item | Human owner | State / source | Next safe action |
|---:|---|---|---|---|
| 1 | {{top_priority}} | {{owner}} | {{state}} | {{next_action}} |
| 2 | {{supervision_or_attending_check}} | {{owner}} | {{state}} | {{next_action}} |
| 3 | {{duty_recovery_or_safe_transport}} | {{owner}} | {{state}} | {{next_action}} |
| 4 | {{learning_or_evidence_item}} | {{owner}} | {{state}} | {{next_action}} |
| 5 | {{closed_loop_or_communication_item}} | {{owner}} | {{state}} | {{next_action}} |
| 6 | {{human_decision_or_agent_review}} | {{owner}} | {{state}} | {{next_action}} |
| 7 | {{protected_life_or_expiry_item}} | {{owner}} | {{state}} | {{next_action}} |

## Orient My Day & Duty

- Fixed commitments / call / conference / clinic / study: {{summary}}
- Top Three: {{items}}
- Current task-level supervision source and expiry: {{source}}
- Required attending or program check: {{question_or_none}}
- Sleep opportunity, food, recovery, commute, and safe-transport route: {{private_summary}}
- Protected-life promise: {{private_item}}
- Plan B / Minimum Mode / relief route: {{plan}}

## ATTEND authority receipt

| Gate | Current answer | Source / human owner | State |
|---|---|---|---|
| Activity & active hat | {{answer}} | {{source_or_owner}} | {{state}} |
| Training level & task responsibility | {{answer}} | {{source_or_owner}} | {{state}} |
| Team & attending | {{answer}} | {{source_or_owner}} | {{state}} |
| Environment, evidence & data | {{answer}} | {{source_or_owner}} | {{state}} |
| Need for escalation | {{answer}} | {{source_or_owner}} | {{state}} |
| Decision, documentation & destination | {{answer}} | {{source_or_owner}} | {{state}} |

**Gate result:** {{proceed_to_preview_or_block_and_escalate}} • **Expiry:** {{date_or_transition}}

## Learn & Reason

| Learning item | Synthetic / general | Source & date | Uncertainty / conflict | Human verification | Next review |
|---|---|---|---|---|---|
| {{item}} | {{classification}} | {{source}} | {{limits}} | {{owner}} | {{date}} |

**Never here:** patient-specific advice, real chart data, restricted exam content, a competence score, or a live-care recommendation.

## CIRCLE care-orchestration studio

**Mode:** {{synthetic_process_only_or_institution_approved}} • **Official source of truth:** {{none_or_approved_system}}  
**Context & goals:** {{summary}} • **Accountable attending:** {{human}} • **Resident task:** {{bounded_role}}

| Orchestration item | Decision owner | Action owner | Receiver | Closed-loop evidence | Escalation / contingency | Expiry |
|---|---|---|---|---|---|---|
| {{item}} | {{human}} | {{human}} | {{human}} | {{acknowledgment_or_open}} | {{trigger_and_route}} | {{date_or_transition}} |

**CIRCLE check:** Context & goals {{state}} • Identified accountability {{state}} • Roles & consults {{state}} • Closed loops {{state}} • Limits & escalation {{state}} • End state & transition {{state}}

**Boundary:** CIRCLE prepares or reconciles human-owned work. It does not create a care decision, authority, patient task, shadow chart, sign-out, autonomous contact, or responsibility transfer.

## Training, development & opportunity

- Feedback / Milestones self-evidence: {{resident_controlled_summary}}
- Exam / license / procedure authorization / credentials: {{official_source_and_questions}}
- Teaching / QI / research / scholarship: {{approved_or_synthetic_project_state}}
- Fellowship / career / contract / mentorship: {{next_step}}
- Formal evaluation or certification by AI: **Prohibited**

## ORBIT Agent Control Tower

| Agent | Objective / owner | Context / permission | Data & tools | Lifecycle state | Human review | Expiry / kill |
|---|---|---|---|---|---|---|
| {{agent_or_none}} | {{bounded_objective_and_owner}} | {{context_and_p0_to_p4}} | {{allowed_only}} | {{state}} | {{human}} | {{expiry_and_kill_state}} |

**Agent rules:** all Off by default • one bounded run • no recursive delegation • no permission escalation • no hidden retry • no patient-care authority • no self-approval • human release only.

## Human decision, release & closed-loop queue

| Exact human decision or acknowledgment | Artifact / audience / destination | Context & data class | Source | Owner / approver | Fallback / rollback | State |
|---|---|---|---|---|---|---|
| {{decision}} | {{artifact_and_destination}} | {{context_and_class}} | {{source}} | {{human}} | {{fallback}} | {{state}} |

## Private whole-life panel — Private Resident OS only

- Recovery, health-care time, food, commute, and buffer: {{private_summary}}
- Family, relationships, caregiving, and protected commitments: {{private_summary}}
- Finances, benefits, debt categories, and questions: {{private_summary}}
- Mission, joy, service, and future direction: {{private_summary}}
- Program or institutional export: **Off and prohibited by default**

## 24 power states

**Available inactive:** {{powers}}  
**Previewed:** {{powers_or_none}} • **Active bounded:** {{powers_or_none}} • **Paused:** {{powers_or_none}}  
Each power needs its own activation card, exact approval, expiry, fallback, rollback, purge, and removal.

**Permanent controls:** `[Context & Active Hat]` `[Supervision & Attending]` `[Privacy & Data]` `[Sources & Freshness]` `[Duty & Recovery]` `[Human Approval Queue]` `[Agent Registry & Kill Switch]` `[History]` `[Pause All]` `[Safe Reset]` `[Correct]` `[Export]` `[Delete]` `[Rollback]` `[Remove Power]` `[Full Uninstall]`
~~~

## Required resident-only pages

- My ROUNDS Home
- Rotation, Duty & Readiness
- Learning, Evidence & Synthetic Reasoning
- CIRCLE Care-Orchestration Studio
- Supervision, ATTEND & Human Decision Queue
- Training, Feedback, Milestones & Credentials
- Teaching, Quality, Safety, Research & Scholarship
- ORBIT Agent Control Tower
- Fellowship, Career & Whole Life

All pages remain subviews of the one resident home and one resident data partition. Do not duplicate the Command Center.

## Attention, accessibility, and degraded mode

The opening view displays no more than seven attention items. Meaning never depends on color. Do not label a person with a red, yellow, or green risk status. Support semantic headings, screen readers, keyboard-only operation, visible focus, contrast, 200% zoom and reflow, reduced motion, accessible tables and forms, text alternatives, plain language, print, mobile, and Markdown. If tools or integrations fail, show the failure and switch to instructions and copyable templates. Never imply an action completed when it did not.

## Permanent Pause All

Pause stops every pending and new optional power, connector, agent, scheduled workflow, and external action. It does not delete work, hide state, delay emergency routing, or alter unrelated records. The resident controls restart, correction, export, purge, deletion, rollback, power removal, and uninstall.
