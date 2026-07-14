# Deploy Under Human Accountability

**File:** `SAFETY.md`
**Status:** binding deployment requirements for official distributions, the hosted service, and any implementation seeking certification. These requirements live here — and in the hosted-service Terms of Use, enterprise agreements, and data-processing agreements — rather than in the software license. The Apache License 2.0 carries no field-of-use restrictions; an open-source license that restricted who may use the software or for what would no longer be open source. Openness applies to the code. Discipline applies to the deployment.

---

## 1. What This Software Is and Is Not

Nurse AI OS is workforce, administrative, and educational infrastructure. It is not a medical device, and it is not cleared, approved, or validated for diagnosis, treatment, or autonomous clinical decision-making.

Three functional categories are kept distinct in every deployment, every interface, and every piece of marketing:

- **Education.** Training content, simulation, and professional development. No patient data.
- **Administrative support.** Scheduling, documentation support, workflow coordination, communication. Operates on operational data under the boundaries in Section 3.
- **Clinical functionality.** Anything that informs the care of an identifiable patient. Not enabled in this software as shipped. Any implementer who builds clinical functionality on this platform assumes full responsibility for validation, regulatory clearance where required, and institutional approval before use.

A deployment must never present educational or administrative output as clinical guidance.

## 2. Human Accountability

- A licensed clinician remains accountable for every clinical decision. Software output is input to human judgment, never a substitute for it.
- No deployment may take autonomous diagnostic or treatment action. Automation is limited to administrative and coordination tasks under human-defined boundaries, with destructive or irreversible actions requiring explicit human confirmation.
- Physicians hold final clinical decision authority; nurses and allied clinicians hold the safety authority of their own disciplines. The software does not reorder professional accountability, and no configuration may claim to.

## 3. Protected Health Information and Data Boundaries

- No deployment stores raw protected health information in agent memory, telemetry, logs, or model context. This boundary is architectural, not aspirational: memory categories that would capture PHI are refused by the system, and the refusal is not user-overridable in official distributions.
- The hosted commercial service operates on non-clinical, non-PHI data only. There is no upgrade path that promotes clinical data into the hosted environment.
- Self-hosted institutional deployments that handle operational healthcare data must run inside the institution's approved environment, under its HIPAA (or jurisdiction-equivalent) compliance program, with a business associate agreement in place wherever one is required.
- Data never pools across organizational boundaries. Each deploying organization's data posture is independent.

## 4. Validation, Logging, and Incident Response

- Validate before use. Any workflow that touches operational healthcare data is tested against the deploying institution's own environment and approved by the institution before production use.
- Log for audit. Official deployments maintain tamper-evident audit logs of agent actions, human confirmations, and refusals. Audit systems fail closed: if logging is unavailable, the gated action does not proceed.
- Report incidents. Suspected safety events, data-boundary violations, or misuse of the platform in a clinical context are reported to the deploying institution's incident process and privately to this project through GitHub's private vulnerability-reporting channel, if enabled, or the maintainer contact in `README.md`. Do not include PHI in the report. Patient-impacting incidents take priority over all other project work.

## 5. Local Approval

Deployment in any healthcare organization requires that organization's own governance approval — compliance, information security, legal, and clinical leadership as applicable. Nothing in this repository substitutes for local regulatory review, and this document is engineering and governance discipline, not legal advice.

---

Before deploying in any healthcare setting, complete your institution's approval process and confirm every boundary in Sections 2 and 3 against your configuration.

