# BREATHE Workflows, Launch & Adoption Plan

## Twenty-four runnable, ready-to-preview workflow cards

### WF-01 — Shift Orientation, Capacity, Top Three & Plan B

**Linked assets:** `PWR-01` Shift & Assignment Readiness Navigator; `TPL-05` Shift Capacity, Top Three & Plan B Card; `shift_capacity_recovery`.<br>
**Trigger and intended benefit:** Build a feasible shift plan around verified role, unit, assigned responsibility, workload, breaks, equipment preparation, learning, and life—without creating or changing patient assignments.<br>
**Allowed inputs:** exact role and credential; site and service; professional-owned schedule; nonidentifiable workload categories; local escalation route; break, commute, recovery, and protected-life needs. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) verify SCOPE; separate fixed obligations from choices; identify Top Three; prepare generic equipment and source checks; add a capacity trigger and Plan B; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Shift Readiness Card, Top Three, generic readiness checklist, protected-life item, and escalation Plan B; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** the respiratory care professional confirms feasibility and the official charge, lead, manager, or clinical team retains assignment and care authority.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-02 — Workload Reality, Delay Risk & Human Escalation

**Linked assets:** `PWR-02` Workload, Staffing Evidence & Escalation Shield; `TPL-06` Workload Reality, Staffing Evidence & Escalation Brief; `workload_observation_questions`.<br>
**Trigger and intended benefit:** Make workload pressure, acuity categories, procedures, transports, time demand, coverage questions, and missed-work risk visible without assigning staff, rationing therapy, or certifying staffing adequacy.<br>
**Allowed inputs:** professional-owned workload categories; current local staffing and escalation policy; shift resources; competing priorities; named operational and clinical escalation routes; optional AARC SESG evidence context. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) classify facts, unknowns, time-sensitive work, and local policy questions; distinguish personal observation from official workload data; prepare an escalation brief; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Workload Reality Map, evidence questions, burden and delay risks, and human escalation brief; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** an authorized operational and clinical human reviews priorities; the AI never makes assignments, defers ordered care, or declares staffing safe.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-03 — Break, Recovery, Health-Care Time & Safe Transport

**Linked assets:** `PWR-03` Fatigue, Recovery & Safe-Transport Navigator; `TPL-07` Recovery, Health-Care Time & Safe-Transport Plan; `shift_capacity_recovery`.<br>
**Trigger and intended benefit:** Help protect recovery, hydration, food, breaks, post-shift travel, health care, and support without diagnosing fatigue, impairment, burnout, fitness, or ability to work or drive.<br>
**Allowed inputs:** self-described capacity; schedule; commute options; chosen supports; local fatigue, occupational health, leave, and safe-transport routes. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) show pressure without diagnosis; switch to Minimum Mode; identify immediate human safety routes; build recovery and transport choices; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Capacity Shield, break and recovery plan, safe-transport options, and human-support route; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** the professional chooses a human route; the OS makes no fitness, impairment, employment, or driving determination.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-04 — True North, Family, Finances & Ninety-Day Direction

**Linked assets:** `PWR-04` Mission, Family, Finances & Future Compass; `TPL-27` Whole-Life Capacity, Family, Finance & Minimum-Mode Plan; `whole_life_private`.<br>
**Trigger and intended benefit:** Connect respiratory-care identity to family, finances, education, health, joy, service, leadership, and a life beyond the next shift.<br>
**Allowed inputs:** private mission and values; nonsecret financial categories; family and caregiving needs; education and career interests; time horizon; chosen privacy level. Whole-life inputs are accepted only in `whole_life_private` within a personally controlled isolated store; institution-managed BREATHE Private mode rejects them. Other Private mode inputs remain limited to nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) prove a personally controlled isolated store and route whole-life inputs only to `whole_life_private`, or reject them in institution-managed BREATHE Private mode; 3) translate values into bounded goals, decisions, buffers, mentoring questions, and review dates without storing account credentials or employer analytics; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** private True North, financial organization map, family logistics plan, and ninety-day direction; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** the professional verifies the personally controlled isolated store and controls edit, export, sharing, pause and deletion; institution-managed BREATHE rejects private whole-life data, which never enters employer or competency analytics.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-05 — Evidence, Guideline, Policy & Manufacturer Source Brief

**Linked assets:** `PWR-05` Evidence, Guideline & Source-Freshness Navigator; `TPL-08` Evidence, Guideline, Policy & Manufacturer Source Brief; `evidence_guideline_ledger`.<br>
**Trigger and intended benefit:** Turn generic respiratory-care questions into current, source-aware briefs that preserve version, applicability, uncertainty, contradiction, local policy, and human verification.<br>
**Allowed inputs:** generic question; population and setting; current AARC or other authoritative source; local policy location; source date and version. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) define the question; retrieve only authorized sources; separate evidence, policy, device instructions, and interpretation; identify conflicts and expiry; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Evidence & Guideline Brief with provenance, limits, local-verification queue, and expiry; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** a qualified human applies current orders, protocols, policies, manufacturer instructions, and patient context; no autonomous recommendation changes care.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-06 — Synthetic ABG, Acid–Base & Gas-Exchange Deliberate Practice

**Linked assets:** `PWR-06` Synthetic ABG, Acid–Base & Gas-Exchange Learning Lab; `TPL-09` Synthetic ABG, Acid–Base & Gas-Exchange Learning Sheet; `synthetic_learning_case`.<br>
**Trigger and intended benefit:** Practice arterial or capillary blood-gas reasoning, acid–base patterns, oxygenation, ventilation, compensation, and limitations using fictional or approved educational cases.<br>
**Allowed inputs:** clearly synthetic values or separately approved training case; learning objective; source; expected reasoning level; qualified reviewer. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) label the case synthetic; calculate transparently; surface assumptions and mixed-pattern uncertainty; compare reasoning with the source; request human debrief; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Synthetic Gas-Exchange Learning Sheet, calculation trail, uncertainty check, reflection, and debrief prompts; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** a qualified educator or clinician reviews learning; no real result, diagnosis, ventilator change, oxygen target, or patient action is produced.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-07 — Synthetic Respiratory Assessment, Trend & Bias Rehearsal

**Linked assets:** `PWR-07` Synthetic Respiratory Assessment & Pattern-Recognition Studio; `TPL-10` Synthetic Respiratory Assessment, Trend & Bias Reflection; `synthetic_learning_case`.<br>
**Trigger and intended benefit:** Develop structured observation, respiratory assessment, waveform, trend, and escalation reasoning with fictional scenarios while resisting premature closure.<br>
**Allowed inputs:** synthetic scenario; learning goal; setting; expected role; source; bias and uncertainty prompts; reviewer. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) build a problem representation; distinguish observation from inference; generate alternatives; identify red flags and missing data; rehearse escalation; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Synthetic Assessment Map, alternative explanations, bias check, missing-data list, and human escalation rehearsal; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** the activity remains educational; no diagnosis, triage, patient monitoring, treatment selection, or real-care direction is created.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-08 — SCOPE Role, Credential, Order, Protocol & Permission Check

**Linked assets:** `PWR-08` Orders, Protocols & Scope Boundary Navigator; `TPL-04` SCOPE Authority and Action Gate Receipt; `scope_order_protocol_source`.<br>
**Trigger and intended benefit:** Make the exact relationship among role, credential, competency, order, protocol, medical direction, local policy, and escalation visible before consequential work.<br>
**Allowed inputs:** exact local title; credential and license; verified competency; site; service; order or protocol source; medical and operational owner; date and expiry. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) run SCOPE; verify—not infer—authority; identify missing, stale, conflicting, or out-of-role elements; prepare a question or escalation; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Scope & Order Boundary Card, source ledger, unknowns, and decision-owner queue; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** an authorized human resolves uncertainty; the OS never expands scope, credential, competency, medical direction, or protocol authority.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-09 — Synthetic Ventilator Mode, Waveform & Alarm Learning

**Linked assets:** `PWR-09` Ventilator Modes, Waveforms & Alarm Learning Studio; `TPL-12` Synthetic Ventilator Mode, Waveform & Alarm Worksheet; `synthetic_learning_case`.<br>
**Trigger and intended benefit:** Build deliberate practice with ventilator concepts, modes, waveforms, loops, synchrony, alarms, and troubleshooting sequences using synthetic cases and current sources.<br>
**Allowed inputs:** synthetic settings and waveforms; ventilator model only when public or approved; educational objective; current manufacturer and clinical sources; reviewer. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) label all data synthetic; explain concepts and uncertainty; distinguish patient, circuit, interface, device, and source questions; rehearse human escalation; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Synthetic Ventilator Learning Worksheet, source map, alarm reasoning tree, and debrief prompts; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** no connection to a ventilator, alarm system, monitor, EHR, or patient; no setting, mode, alarm-limit, or treatment recommendation for live care.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-10 — Oxygen, Aerosol, Humidification & Device Education Comparison

**Linked assets:** `PWR-10` Oxygen, Aerosol, Humidification & Delivery-Device Learning and Comparison Studio; `TPL-13` Oxygen, Aerosol, Humidification & Delivery-Device Comparison; `equipment_readiness_generic`.<br>
**Trigger and intended benefit:** Compare generic delivery principles, device characteristics, preparation steps, teaching points, and source requirements without selecting therapy for a patient.<br>
**Allowed inputs:** generic learning objective; device class; public manufacturer information; current guideline; local policy location; approved education context. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) separate device facts from local policy and patient-specific decisions; extract source-stated contraindications and limits for qualified-human verification; prepare a generic checklist and questions; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Device Comparison Brief, generic readiness and teaching checklist, source and policy queue; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** only an authorized prescriber or protocol, plus humans acting within verified local scope and policy, determine patient-specific device, medication, flow, dose, target, and response; the official record remains authoritative.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-11 — Generic Equipment, Circuit, Interface, Supply & Backup Readiness

**Linked assets:** `PWR-11` Equipment, Circuit, Interface & Supply Readiness Mapper; `TPL-14` Generic Equipment, Circuit, Interface, Supply & Backup Map; `equipment_readiness_generic`.<br>
**Trigger and intended benefit:** Prepare generic equipment, circuit, interface, consumable, backup, cleaning, inspection, and escalation maps without functioning as biomedical maintenance or an official inventory system.<br>
**Allowed inputs:** approved equipment class; manufacturer instructions; local cleaning and maintenance policy; supply owners; backup and biomedical routes. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) map readiness categories, owner, source, expiry, failure and backup; keep patient-specific settings and restricted device data out of Private mode; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Generic Equipment Readiness Map, owner matrix, backup path, and discrepancy escalation card; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** authorized clinical, supply, infection prevention, and biomedical teams verify readiness in official systems; the OS never certifies equipment.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-12 — Synthetic Transport, Procedure & Equipment-Failure Rehearsal

**Linked assets:** `PWR-12` Transport, Procedure & Equipment-Failure Rehearsal; `TPL-15` Synthetic Transport, Procedure & Equipment-Failure Rehearsal; `synthetic_learning_case`.<br>
**Trigger and intended benefit:** Rehearse role clarity, generic equipment readiness, contingencies, communication, and failure response for transport or procedures using synthetic or approved training scenarios.<br>
**Allowed inputs:** synthetic scenario; transport or procedure type; roles; equipment classes; contingency questions; current policy; qualified reviewer. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) run SCOPE and CIRCLE; identify human leaders, equipment and backup categories, handoffs, failure triggers, destination, and debrief; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Synthetic Transport or Procedure Readiness Rehearsal, role map, equipment questions, contingency card, and debrief; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** authorized clinicians make all live transport, procedure, airway, monitoring, equipment, and readiness decisions through official workflows.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-13 — CIRCLE Respiratory Care-Orchestration Map

**Linked assets:** `PWR-13` Scope-Aware Respiratory Care Orchestration Mapper; `TPL-16` CIRCLE Respiratory Care-Orchestration Map; `respiratory_care_orchestration`.<br>
**Trigger and intended benefit:** Prepare human-owned respiratory care coordination by making goals, accountable clinicians, respiratory role, orders or protocols, dependencies, closed loops, contingencies, and transitions visible.<br>
**Allowed inputs:** synthetic scenario or separately authorized official workflow; exact role; source; accountable clinician; team roles; dependencies; status; escalation and destination. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) run SCOPE then CIRCLE; separate preparation from decision; attribute every owner; show official system, acknowledgment, contingency, end state, and expiry; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Respiratory Care Orchestration Map, ownership and dependency view, closed-loop queue, and transition card; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** the official clinical team and systems retain care authority and responsibility; the map is never a patient list, task manager, shadow chart, order, or handoff.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-14 — Synthetic Airway, Code, Rapid Response & Escalation Rehearsal

**Linked assets:** `PWR-14` Airway, Code, Rapid Response & Escalation Rehearsal; `TPL-18` Synthetic Airway, Code & Rapid-Response Rehearsal; `synthetic_learning_case`.<br>
**Trigger and intended benefit:** Practice communication, roles, equipment categories, contingencies, and escalation in fictional airway, code, rapid-response, or deterioration scenarios.<br>
**Allowed inputs:** fictional scenario; current training source; local response structure; exact learner role; equipment categories; qualified facilitator. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) declare simulation; run SCOPE; rehearse call-outs, check-backs, role clarity, equipment and backup questions, escalation, and debrief; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Synthetic Acute Response Rehearsal, communication script, role and equipment questions, omissions check, and human debrief; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** no real alert, page, triage, airway procedure, drug, device action, treatment, or emergency direction is initiated by the OS.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-15 — Rounds, Consult, Recommendation & Closed-Loop Preparation

**Linked assets:** `PWR-15` Interdisciplinary Rounds, Consult & Closed-Loop Coordination Studio; `TPL-17` Rounds, Consult, Recommendation & Check-Back Brief; `respiratory_care_orchestration`.<br>
**Trigger and intended benefit:** Help respiratory professionals prepare concise observations, questions, recommendations for human consideration, dependencies, and acknowledgment checks without contacting the team or moving care.<br>
**Allowed inputs:** synthetic or approved context; role; purpose; source; accountable clinician; team roles; pending questions; official channel. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) distinguish observation, source, interpretation, question, and human decision; rehearse concise communication; record acknowledgment criteria and expiry; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Rounds or Consult Preparation Brief, role map, check-back prompts, and human-decision queue; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** the respiratory professional communicates through the official channel and qualified humans decide; AI transmission is never acceptance or responsibility transfer.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-16 — Synthetic Liberation, NIV, Tracheostomy & Transition Reliability

**Linked assets:** `PWR-16` Liberation, NIV, Tracheostomy & Transition Reliability Planner; `TPL-19` Synthetic Liberation, NIV, Tracheostomy & Transition Map; `handoff_transition_rehearsal`.<br>
**Trigger and intended benefit:** Rehearse generic evidence, roles, readiness questions, barriers, contingencies, education, handoffs, and follow-up for respiratory transitions without determining patient readiness.<br>
**Allowed inputs:** synthetic case or approved workflow; current guideline and local protocol; exact role; accountable clinician; team owners; transition and contingency questions. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) run SCOPE and CIRCLE; separate criteria from patient determination; map roles, barriers, checkpoints, education, official reconciliation, and expiry; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Synthetic Transition Reliability Map, human-owner matrix, barrier and contingency prompts, and debrief; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** authorized clinicians determine weaning, liberation, NIV, tracheostomy, decannulation, disposition, or follow-up; the OS makes no readiness decision.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-17 — Patient, Family, Caregiver Education & Teach-Back Rehearsal

**Linked assets:** `PWR-17` Patient, Family & Caregiver Education Rehearsal; `TPL-20` Patient, Family, Caregiver Education & Teach-Back Plan; `teaching_preceptor_development`.<br>
**Trigger and intended benefit:** Prepare understandable, culturally humble, accessible respiratory education and teach-back plans with synthetic scenarios and approved sources.<br>
**Allowed inputs:** generic topic; learner needs; language and accessibility requirements; source; approved education policy; qualified reviewer. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) set learning goal; separate universal education from individualized instruction; create plain-language explanation, demonstration, teach-back, warning, and escalation questions; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Education Rehearsal Plan, teach-back prompts, accessibility and interpreter plan, source list, and review queue; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** a qualified clinician personalizes and delivers patient-specific education; the OS does not obtain consent, verify competence, or replace interpreter and accessibility services.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-18 — Preceptor, Competency, Simulation & Feedback Development

**Linked assets:** `PWR-18` Preceptor, Competency & Simulation Development Studio; `TPL-21` Preceptor, Simulation, Deliberate-Practice & Feedback Plan; `teaching_preceptor_development`.<br>
**Trigger and intended benefit:** Support preceptors and learners with objectives, deliberate practice, simulation, feedback, and evidence portfolios while keeping formal competency decisions human.<br>
**Allowed inputs:** role and learner level; approved competency framework; learning objectives; synthetic scenario; evaluator; assessment and documentation policy. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) define observable practice; build synthetic rehearsal and rubric prompts; separate coaching evidence from formal evaluation; route official decisions; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Preceptor or Simulation Plan, deliberate-practice steps, feedback prompts, and human evaluation queue; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** authorized educators and leaders determine validation, competency, remediation, assignment eligibility, and personnel consequences; no hidden scoring.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-19 — Quality, Safety, Infection Prevention & PDSA Project

**Linked assets:** `PWR-19` Quality, Safety, Infection Prevention & Implementation Lab; `TPL-22` Quality, Safety, Infection Prevention & PDSA Charter; `quality_safety_project`.<br>
**Trigger and intended benefit:** Prepare systems-focused quality work, PDSA cycles, measures, infection-prevention questions, equipment reliability reviews, and implementation plans without replacing official reporting or governance.<br>
**Allowed inputs:** approved project purpose; sponsor; human QI or research determination; approved data plan; current policy; measure owners; affected people; review and stop routes. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) define aim and boundaries; verify project classification; map process and equity; select measures; propose the smallest reversible test; require a named sponsor to authorize, execute, and monitor it in official systems; track burden, balancing measures, and learning; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Quality Charter, process map, PDSA plan, measure dictionary, equity and burden review, and sponsor queue; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** authorized humans decide QI versus research, reportability, cause, policy, and clinical change; no event detail or patient data enters Private mode.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-20 — Feedback, Conflict, Safety Concern & Advocacy Preparation

**Linked assets:** `PWR-20` Feedback, Conflict, Psychological Safety & Advocacy Navigator; `TPL-24` Feedback, Conflict, Psychological Safety & Advocacy Brief; `control_audit_receipt`.<br>
**Trigger and intended benefit:** Help respiratory professionals seek feedback, prepare difficult conversations, raise safety concerns, and locate human support without deciding fault, rights, retaliation, impairment, or discipline.<br>
**Allowed inputs:** professional-owned facts; desired outcome; audience; current policy or support routes; privacy and sharing choices; immediate safety status. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) separate observation from interpretation; identify urgency; prepare concise facts, questions, request, boundary, and escalation choices; preserve control of sharing; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Conversation Brief, feedback plan, safety or advocacy route map, and follow-up date; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** urgent safety routes go directly to authorized humans; the OS makes no legal, HR, retaliation, fitness, blame, or disciplinary determination.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-21 — Credential, Specialty, Career, Research & Leadership Growth

**Linked assets:** `PWR-21` Credential, Specialty, Career, Research & Leadership Growth Map; `TPL-25` NBRC, License, CE, Specialty & Renewal Radar; `credential_ce_career`.<br>
**Trigger and intended benefit:** Organize licensure, NBRC credential maintenance, CE, specialty pathways, education, research, leadership, portfolio, and opportunity decisions around capacity and purpose.<br>
**Allowed inputs:** verified credential and license sources; renewal dates; CE categories; interests; truthful evidence; capacity; mentors; family and financial constraints. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) separate official requirements from goals; track sources and expiry; identify one bounded growth track; build mentorship, evidence, and review steps; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Credential Radar, specialty and career map, evidence portfolio, mentoring questions, and ninety-day plan; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** official boards, employers, educators, investigators, and credentialing bodies verify status and decisions; the OS never certifies, scores, authors, or fabricates achievement.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-22 — ORBIT Agent Charter, Tool, Permission & Data Registry

**Linked assets:** `PWR-22` AI Agent Charter, Tool, Permission & Data Registry; `TPL-28` ORBIT Agent Charter, Permission & Device-Boundary Envelope; `agent_charter_trace`.<br>
**Trigger and intended benefit:** Define every software agent before use: objective, owner, non-goals, data, tools, sources, permission, human checkpoints, expiry, kill, purge, rollback, and retirement.<br>
**Allowed inputs:** one narrow objective; owner and beneficiary; context; data classification; tools and destinations; risk; human decision owner; budget and expiry. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) apply ORBIT once; keep PERM-P0 Disabled by default; propose at most PERM-P1 through PERM-P4; block PERM-P5; preview exact behavior; test synthetic, missing-source, prompt-injection and failure cases; 4) add CIRCLE only if human coordination is needed, without changing the ORBIT charter or permission envelope; 5) preview the linked template and exact tested limits; 6) wait once for the named human approval of that immutable charter, evidence and one-run limit.<br>
**Output contract:** Agent Charter, permission envelope, test plan, human review gate, kill and retirement plan; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** the agent remains Disabled until exact approval; it has no license, credential, clinical authority, device access, self-approval, or permission-escalation path.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-23 — Multi-Agent Device-Boundary & Human-Handoff Design

**Linked assets:** `PWR-23` Multi-Agent Workflow, Device-Boundary & Human-Handoff Designer; `TPL-28` ORBIT Agent or Multi-Agent Charter, Permission & Device-Boundary Envelope; `agent_charter_trace`.<br>
**Trigger and intended benefit:** Design bounded agent sequences with minimal data, explicit dependencies, disagreement handling, device separation, human review order, and exact termination.<br>
**Allowed inputs:** approved nonclinical or separately governed objective; agent charters; parent permissions; data and tool boundaries; transfer points; human owners; stop and expiry. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) map agent-to-agent and agent-to-human transfers; intersect permissions; prevent recursion; quarantine external instructions; require independent sources and human resolution; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** completed `TPL-28` Multi-Agent Sequence Map with agent sequence and dependencies, permission intersections, transfer contracts, disagreement resolution, device boundary, named human review order, failure and containment paths, and termination evidence; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** no recursive delegation, hidden subagent, device or alarm access, clinical authority, autonomous contact, agent consensus as truth, or verifier-agent approval.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

### WF-24 — Agent Output Audit, Incident, Kill, Rollback & Retirement

**Linked assets:** `PWR-24` Agent Output Audit, Incident, Kill, Rollback & Retirement Controller; `TPL-29` Agent Preview, Test, Run, Review, Incident & Retirement Receipt; `control_audit_receipt`.<br>
**Trigger and intended benefit:** Inspect source provenance, uncertainty, bias, prompt injection, drift, security, action state, cost, and human edits while providing visible incident and retirement controls.<br>
**Allowed inputs:** agent charter and trace; nonsensitive receipt; sources; outputs; edits; tool and action state; test evidence; owner; incident, retention, purge, and rollback routes. Private mode accepts only nonsensitive professional-owned information, public sources and clearly synthetic material; the role-to-power entitlement gate still applies.<br>
**Run:** 1) verify role entitlement and SCOPE; 2) declare Private synthetic/generic or exact approved partition; 3) reconcile charter to behavior; verify sources and permissions; detect mismatch or unauthorized action; pause or kill; contain; use manual fallback; route incident; purge and retire; 4) add CIRCLE for coordination or ORBIT for a named agent; 5) preview the linked template; 6) wait for the named human gate.<br>
**Output contract:** Agent Audit, accept-or-reject receipt, incident record, containment status, rollback and purge evidence, and retirement receipt; include facts, sources, uncertainty, human owner, action state, official destination if any, expiry and deletion.<br>
**Human gate:** a named human owns every decision and incident; the agent cannot conceal, restart, widen scope, retain prohibited data, or authorize release.<br>
**Stop and fallback:** stop on missing or stale authority, prohibited data, urgent care, real device data, source conflict, role mismatch, failed accessibility, agent drift or unavailable human owner; use the official human process and last safe state.<br>
**Completion receipt:** record workflow ID, power/template/schema IDs, owner, context, inputs accepted or rejected, sources, SCOPE result, human decision, named approver, approval scope, approval timestamp, receipt ID, approved artifact/version, output state, no-action confirmation, expiry, correction, rollback, purge and Retain–Revise–Pause–Remove choice.

## Suggested software agents — all PERM-P0 Disabled


- **AGT-01:** Shift & Capacity Planner — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P1 nonsensitive private draft.
- **AGT-02:** Evidence Scout — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P2 exact private read-only sources.
- **AGT-03:** Synthetic ABG Coach — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P1 fictional values only.
- **AGT-04:** Synthetic Ventilator Learning Coach — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P1 synthetic, with no device connection.
- **AGT-05:** Source & Claim Verifier — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P2 exact read-only sources.
- **AGT-06:** Equipment Readiness Mapper — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P3 approved read or sandbox, never device-connected.
- **AGT-07:** Care-Orchestration Draft Assistant — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P3 exact institution read or sandbox.
- **AGT-08:** Quality & Infection-Prevention Mapper — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P3 approved project sandbox.
- **AGT-09:** Teaching & Simulation Builder — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P3 approved education sandbox.
- **AGT-10:** Career & Whole-Life Planner — install state: PERM-P0 Disabled; proposed maximum if separately approved: PERM-P2 personally controlled isolated read-only store; disabled institutionally.

Never create an AI medical director, respiratory supervisor, prescriber, credentialer, evaluator, staffing allocator, ventilator controller, oxygen titrator, alarm monitor, airway agent, patient-messaging agent or device-connected autonomous agent.

## Seven-day safe launch

**Day 1 — Isolation and role truth:** verify separate lane, exact title, credential, site, service, human routes, Private no-PHI and no-device boundary.<br>
**Day 2 — Shift and life reality:** add a professional-owned schedule, generic workload categories, recovery, commute and one protected-life commitment only in a personally controlled private store.<br>
**Day 3 — Learn safely:** create one generic evidence brief and one clearly synthetic ABG or assessment exercise.<br>
**Day 4 — Equip synthetically:** complete one synthetic ventilator or equipment learning worksheet with current sources; connect to nothing.<br>
**Day 5 — Coordinate synthetically:** complete one CIRCLE map and one synthetic rounds, handoff, transport or transition rehearsal.<br>
**Day 6 — Preview one PERM-P1 agent:** inspect charter, permissions, device boundary, failures, kill, purge and receipt; keep it PERM-P0 Disabled unless separately approved.<br>
**Day 7 — Retain, Revise, Pause or Remove:** preview at most one low-risk power. Activating none is acceptable.

**Day 30:** at most three low-risk powers, one at a time; review benefit, burden, source freshness, failures and ability to remove.<br>
**Day 90:** choose one bounded track—learning, teaching, quality, career or governed agents—not all. Institution-specific clinical work requires separate governance.

## First safe use

After the final Activation Report, choose one low-risk issue: shift orientation, recovery plan, generic evidence question, synthetic ABG or ventilator learning case, generic equipment checklist, synthetic CIRCLE rehearsal, teaching outline, credential step or career decision. A private-life priority is allowed only in a personally controlled isolated store. Run SCOPE; add CIRCLE or ORBIT only when relevant; create one page; identify the exact human owner; set expiry; use no patient, device or restricted institutional data.
