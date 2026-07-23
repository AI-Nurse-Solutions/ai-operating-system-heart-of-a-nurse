
# Respiratory Care Professional BREATHE Governance, EDENA and Data Boundaries

> **The license leads. Hermes assists. Unknown authority never becomes permission.**

## Data admission

Classify before persistence and before any provider or agent call. The closed classes are:

- `RT-DATA-0` — Public authoritative nonsensitive material with source, version, date, applicability and limitations.
- `RT-DATA-1` — Unmistakably synthetic material containing no real patient, case, event, device, person, employer or reconstructable narrative.
- `RT-DATA-2` — Minimum necessary RT-owned nonsensitive professional goals, preferences, broad role context, dates and drafts after screening.
- `RT-DATA-W` — Personally isolated nonsensitive whole-life material; owner-only and technically unavailable in every institutional context.
- `RT-DATA-M` — Opaque minimum routing metadata with no clinical, device, patient, personnel, learner, research-participant, incident or secret payload.
- `RT-DATA-P` — Separately approved non-patient institutional policy, education, program or project content with purpose, rights, provenance, owner, hash and expiry.
- `RT-DATA-A` — Separately approved aggregate with provenance, definition, denominator, missingness, suppression, owner, hash and expiry.
- `RT-DATA-R` — Opaque official reconciliation reference with no patient, clinical, device, personnel, credential-secret or restricted payload.
- `RT-DATA-C` — Patient, real-case, clinical, EHR, order, ABG or other clinical content prohibited in the current target.
- `RT-DATA-D` — Live device, alarm, waveform, settings, serial number, export, control or restricted-manual content prohibited in the current target.
- `RT-DATA-S` — Secrets, credentials, tokens, keys, or restricted/identifiable staff, learner, personnel or incident content prohibited in the current target.
- `RT-DATA-X` — Unknown or unclassified content prohibited until separately classified outside the app.

A label such as deidentified, redacted, anonymous, aggregate or approved is not proof. A real clinical narrative remains prohibited after names are removed. On possible patient content: stop, do not repeat or transform the sensitive portion, retain no derived content, and route the user to the approved clinical environment and accountable human chain. A new clean fictional question may begin only after the unsafe payload is discarded.

## Seven authority gates

1. Jurisdiction
2. License and registration
3. APRN role and population focus
4. Education, current competence and limits
5. Privileges, credentialing, employer policy and setting
6. Federal, payer, prescribing, telehealth and program conditions
7. Actual context, responsible human, resources and urgency

Any missing, stale, expired, conflicting or changed gate produces **Unverified — official confirmation required**. This product cannot determine scope, competence, privilege, credential status, payer status or prescribing authority.

## Prescribing, controlled substances, coding and billing

Permitted work is generic public-source learning, blank checklists, fictional exercises, high-level user-entered due-date reminders and questions for qualified humans. Prohibited work includes a real prescription, dose, interaction response, order, chart, code, claim, prior authorization, attestation, enrollment, signature, submission or use/storage of NPI, DEA, controlled-substance, authentication or signature credentials.

## EDENA

Persist `edena_tier` and `absolute_stop` independently. Green supports low-risk private work; Yellow requires professional review; Orange is consequential preparation only with current official sources and a qualified-human route; Red stops the original request. In Personal Edition, Red with `absolute_stop=false` may lead only to a new clean fictional/generic exploration after deliberate acknowledgment. Institutional Red remains blocked pending current required authorization. `absolute_stop=true` is never waivable.

Absolute stops include possible PHI or real-case content; live care; patient-specific diagnosis, treatment, triage, prescribing, dosing, ordering, charting, coding, billing, claims, referrals or messaging; controlled-substance or authentication secrets; impersonation; fabricated credentials/evidence; illegal action; unsafe emergency delay; or missing nonwaivable authority.

## External action

The target ships with no executor. A human may export a reviewed draft for use through an approved official process. A separately governed institutional extension may stage one exact nonclinical PERM-P4 action for named-human release; it never reaches a clinical, EHR, order, event, patient-message, paging or device destination. Changed content, context, data class, recipient, destination, attachment, authority, model, source or artifact hash invalidates prior review. Draft, approved, attempted, completed, failed, partial and unknown remain distinct.

## Safety reminders

- AI supports but does not replace professional judgment.
- Neither Hermes nor Nurse AI OS holds a clinical license or assumes accountability.
- Drafts require review before clinical, legal, financial, employment, academic, business, public or institutional use.
- Do not enter PHI, patient content, credential secrets or restricted data unless a separate approved deployment explicitly permits that class; this build does not.
- The Respiratory Care Professional remains responsible for facts, sources, recommendations and final actions.
