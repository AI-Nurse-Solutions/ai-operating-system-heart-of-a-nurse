# Research, Participant, Workforce, Organization & Community Trust Shield

## 10. Research versus QI versus clinical care versus innovation boundary

### The central rule

The OS never decides the category. It documents facts, highlights possible pathways, and routes the matter to the organization’s authorized human offices. Labels depend on purpose, methods, people/data, interventions, jurisdiction, sponsor/product intent and local policy. Publication or “generalizable knowledge” language alone is not dispositive, and a quality label does not remove possible research or other review obligations.

| Dimension | Human-subjects research may involve | QI/program evaluation may involve | Clinical care/operations may involve | Innovation/product pathway may involve |
|---|---|---|---|---|
| Primary purpose | Systematic investigation to contribute knowledge | Improve/evaluate a local program or process | Benefit an individual patient or operate care | Validate a product, intended use, workflow, business/technical model or scale pathway |
| Human interaction | Recruitment, consent, intervention or identifiable information may trigger review | Staff/patient involvement can still require privacy, ethics or research review | Individual assessment, diagnosis, treatment and care operations | User/patient testing, intended use and risk may trigger research, clinical, device, privacy or other review |
| Methods | Assignment, randomization, prospective data collection, protocolized procedures | Iterative local tests, audits and process measures | Care standards, clinician judgment, operational procedures | Prototype, usability, synthetic test, non-production pilot or product validation |
| Data | Identifiable/private information, biospecimens or coded research data may require governed environments | Operational/clinical data still require approved use and access | Official clinical systems and minimum necessary access | Product telemetry, tracking, training data and vendor flows need explicit governance |
| DISCOVER action | Questions, metadata-level planning and official-review routing only | Aggregate/process planning and human-review routing only | No patient-specific recommendation or workflow action | Synthetic/non-production planning and formal review routes only |

### Boundary output vocabulary

The only allowed pathway statuses are:

- `HUMAN_SUBJECTS_RESEARCH_POSSIBLE`
- `QI_PROGRAM_EVALUATION_POSSIBLE`
- `CLINICAL_CARE_OPERATIONS_POSSIBLE`
- `INNOVATION_PRODUCT_REVIEW_POSSIBLE`
- `MULTIPLE_OR_UNRESOLVED`

The output must show which FRAME facts produced each possible route, what remains unknown, the local authoritative destination, owner, expiry, and evidence needed. If any key fact is missing, authority is expired, local policy conflicts, or more than one pathway is plausible, the record remains `MULTIPLE_OR_UNRESOLVED`.

### Clinical and research-safety separation

DISCOVER may hold only a nonidentifying official-event reference, accountable office/owner, due window and coarse state when needed for portfolio awareness. It must reject adverse-event narratives, complaints, clinical notes and participant-level safety data. It may not determine seriousness, relatedness, expectedness, urgency, reportability or corrective action; it routes immediately to the official safety/clinical/research system and authorized humans.

---

## 11. Safety, data and action ceilings

### Data ceiling

| Class | Allowed use |
|---|---|
| `DATA-D0` | Public authoritative sources, synthetic fixtures and synthetic scenarios |
| `DATA-D1` | Approved internal policies, protocols, portfolio metadata, process definitions and nonsensitive organizational facts |
| `DATA-D2` | Human-approved aggregates or enclave-derived aggregate exports with source system, query/version, suppression, export approval, owner, date and hash evidence |
| `DATA-D3-PRIVATE` | Owner-entered life/career/purpose information in SCH-16 only |
| `DATA-DX-PROHIBITED` | Direct identifiers, PHI/PII, participant-level rows, clinical notes, raw qualitative narratives/quotes, recruitment/contact lists, genomics/biospecimen linkages, images/signals tied to people, employee-level records, payment/account data, credentials/secrets, unapproved confidential inventions and uncontrolled model training data |

“Deidentified,” “limited,” “coded,” “anonymous,” or “public” labels do not create ingestion permission. The base lane accepts no row-level person data. Approved aggregate/enclave exports must be prepared and approved outside DISCOVER. Small-cell suppression and source/export evidence are required before use.

### Permission and agent ceiling

| Level | Meaning |
|---|---|
| `PERM-P0` | Disabled; installed state for all agents/connectors/actions |
| `PERM-P1` | Local render and synthetic/public-source preview with no external write |
| `PERM-P2` | Human-approved read-only bounded sandbox over exact allowed sources/metadata |
| `PERM-P3` | Institution-approved one-run sandbox over exact approved aggregates/enclave exports with ORBIT token and zero production writes |
| `PERM-P4` | Production, clinical, participant-facing, financial, submission or external-write authority; **not implemented in this product** |

### Allowed action verbs

`ask`, `classify-as-possible`, `compare`, `draft`, `extract-from-approved-input`, `map`, `preview`, `question`, `simulate-with-stated-assumptions`, `summarize`, `trace`, `validate-schema`, and `route-to-named-human`.

### Actions that do not exist in the base product

- recruit, screen, consent, enroll, randomize, intervene, monitor or contact a participant;
- diagnose, recommend treatment, triage, alter care, write an order, change an alert/order set, or write to the EHR;
- classify/report an adverse event, submit to HRO/IRB/regulator/registry/sponsor/journal/grant portal, or attest compliance;
- launch a live pilot, connect production data, deploy a model/device, add tracking, run a patient-facing experiment, or choose a winner;
- publish, email, message, post, issue a press release, send a survey or create a contact list;
- sign a contract, share data, file IP, select a vendor, procure, purchase, spend, pay, price, bill, accept funding or commit resources;
- assign authorship, adjudicate conflicts, score an employee, make an employment/credential decision or infer a protected characteristic;
- self-activate, schedule itself, create hidden agents, widen permissions, retry without authority, or continue in the background.

### Stop and escalation conditions

Stop before generation when active-hat authority is missing/expired, the input is person-level or raw narrative, boundary facts are unresolved, a source is retracted/expired for the intended use, a controlled reference/hash mismatches, a requested action exceeds the ceiling, a participant or clinical-safety issue appears, approval evidence is missing, an agent changes version/hash, or a cross-partition/private access is attempted.

---

## Reject before persistence

Accept **no PHI or substantive/direct PII in content**. Reject patient or participant row-level data and identities; recruitment, screening, consent, contact, scheduling or payment records; person-linked biospecimen, genomic, imaging, device, sensor, safety-event or complaint data; raw patient/participant/workforce/source-system/confidential free text or narrative; individual workforce/learner/applicant data; credentials/secrets; export-controlled or restricted security data; sponsor-confidential, vendor-confidential or contract-confidential information; privileged invention material; and raw documents merely labeled deidentified or redacted. A deidentified label does not create ingestion permission. Leader-authored D0/D1 planning narrative is allowed only after the prohibited-input screen and may not contain another person's substantive data. Prove zero retention for rejected input.

**Opaque platform principal-ID envelope exception:** required owner_id, reviewer_id, approver IDs and ACL principal_id may contain only tenant-local opaque platform identifiers. The envelope permits no names, contact details, profile fields, external dereference, analytics, export, linkage or identity inference. All substantive or direct PII remains rejected before persistence. Runtime preflight validates the opaque syntax and authorized local binding without resolving or displaying identity attributes.

Emergencies, live clinical concerns, participant-safety issues, complaints and adverse events stop the lane and route immediately to official local procedures and authorized humans. DISCOVER never assesses seriousness, relatedness, expectedness, reportability, urgency, diagnosis or care.
