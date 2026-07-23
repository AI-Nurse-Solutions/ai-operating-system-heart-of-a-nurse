---
component_id: "RCAIOS-LIFE-PRACTICE-1.0"
lane: "respiratory_care"
namespace: "resp_breathe.*"
default_context: "private_respiratory_os"
---

# Respiratory Care Life, Practice & Professional Foundation

Build a private, respiratory-professional-controlled operating foundation for shift readiness, learning, role and scope verification, equipment preparation, human-owned coordination, quality, teaching, credentials, career, finances, family, recovery and purpose. It is an organizational and learning system—not a clinical device, ventilator controller, alarm, monitoring service, EHR, staffing engine, credentialing authority or medical decision system.

## Names and role truth

Many people say *respiratory tech*. Local titles can include respiratory therapist, respiratory care practitioner, registered respiratory therapist, certified respiratory therapist, technician, assistant, student, educator, lead or manager. Record the user's exact local title, credential, license, verified competency, site and role. Never infer that one title, credential or education level grants another's scope.

## Default boundary

Private Respiratory OS • no PHI • no patient-specific live care • no EHR or device data • conversation/model memory session-only • connectors Off • external actions Off • agents PERM-P0 Disabled • Preview-first. Only explicitly approved workspace artifacts may persist, with visible owner, ACL, retention and deletion; persistence is never hidden model memory. An institution-approved workspace requires separate authorization for the exact platform, vendor, model, data, purpose, integrations, logging, retention, monitoring, incident route and human owners. Installation never creates or certifies that authorization.

## Eighteen professional-owned record schemas

Create only under `resp_breathe.*`. Type notation: `str`, `bool`, `date`, `datetime`, `datetime_range`, `enum`, `list[T]`, `object` and same-partition `ref`.

| Schema | Context and ACL | Required typed fields | Validation, relationships and retention |
|---|---|---|---|
| `professional_identity_context` | Private or approved; owner writes | exact_role:str; local_title:str; jurisdiction:str; site:str; service:str; active_hat:enum; verification_source:ref; verified_at:datetime; expiry:datetime | No title equivalence; material role, site, service or jurisdiction change expires the record |
| `credential_license_competency` | Private or approved; owner plus named verifier | credential_type:enum; credential_status:enum; license_or_permit_type:str; jurisdiction:str; competency_name:list[str]; source:ref; verified_by:str; verified_at:datetime; expiry:datetime | No document image or secret identifier by default; official bodies and local humans verify; record never certifies authority |
| `scope_order_protocol_source` | Generic in Private; exact approved partition otherwise | task_or_question:str; scope_source:ref; order_required:bool; protocol_source:ref; policy_source:ref; manufacturer_source:ref; decision_owner:str; freshness:enum; expiry:datetime | Private records contain no patient order; stale, missing or conflicting authority blocks consequential output |
| `shift_capacity_recovery` | Personally controlled Private store only | shift_window:datetime_range; self_capacity:enum; top_three:list[str]; break_plan:list[str]; commute_options:list[str]; protected_life_item:str; plan_b:str; review_at:datetime | No patient assignment or employer fitness score; delete or expire at user-selected short interval |
| `workload_observation_questions` | Private generic or approved operational partition | observation_window:datetime_range; nonidentifiable_categories:list[str]; source:ref; unknowns:list[str]; delay_risks:list[str]; escalation_owner:str; status:enum | No patient list, productivity score, staff ranking, assignment, rationing or staffing-adequacy conclusion |
| `equipment_readiness_generic` | Private generic or approved equipment partition | device_class:str; public_or_approved_manual:ref; generic_components:list[str]; readiness_questions:list[str]; backup_categories:list[str]; failure_route:str; expiry:datetime | No serial number, settings, alarm, live device feed or biomedical-maintenance certification |
| `evidence_guideline_ledger` | Private or approved read-only source store | question:str; publisher:str; title:str; url_or_approved_ref:ref; publication_date:date; version:str; status:enum; retrieved_at:datetime; applicability:str; local_override:ref; expiry:datetime | Status is current, proposed, retired, superseded or unknown; citations are never local authority |
| `synthetic_learning_case` | Private synthetic or approved education partition | synthetic_flag:bool; case_id:str; objective:str; fictional_inputs:object; reasoning_steps:list[str]; sources:list[ref]; uncertainty:list[str]; reviewer:str; debrief_at:datetime | synthetic_flag must be true in Private mode; no copied real case, ABG, waveform, image, alarm or device export |
| `respiratory_care_orchestration` | Synthetic in Private; separately approved clinical partition | context:str; goal:str; decision_owner:str; action_owner:str; accountable_clinician:str; respiratory_role:str; order_or_protocol_source:ref; dependencies:list[ref]; closed_loop_evidence:list[str]; official_destination:str; expiry:datetime | CIRCLE required; no shadow chart, order, task, responsibility transfer or AI release |
| `handoff_transition_rehearsal` | Synthetic in Private; approved workflow partition otherwise | synthetic_flag:bool; setting:str; sender_role:str; receiver_role:str; dependencies:list[str]; check_back_prompts:list[str]; contingencies:list[str]; human_acknowledgment:str; expiry:datetime | No real handoff or patient list in Private mode; human acknowledgment and official-system reconciliation are mandatory |
| `quality_safety_project` | Synthetic in Private; approved quality partition otherwise | project_id:str; named_sponsor:str; human_qi_research_determination:ref; aim:str; scope:str; approved_data_plan:ref; measures:list[str]; balancing_measures:list[str]; equity_review:str; stop_rule:str | AI cannot classify QI versus research, access event details in Private mode, start a test or release results |
| `infection_prevention_learning` | Private generic or approved education/quality partition | topic:str; source:ref; version:str; generic_process:list[str]; equipment_boundary:str; questions:list[str]; reviewer:str; expiry:datetime | No exposure record, patient data, staff surveillance, compliance finding or policy substitution |
| `teaching_preceptor_development` | Private synthetic or approved education partition | learner_level:str; objectives:list[str]; framework:ref; synthetic_scenario:ref; deliberate_practice:list[str]; feedback_prompts:list[str]; formal_evaluator:str; expiry:datetime | No hidden scoring, grading, competency decision, remediation or assignment eligibility |
| `credential_ce_career` | Personally controlled Private store only | official_source:ref; credential_or_license_type:str; status:enum; renewal_date:date; ce_category:str; evidence_ref:ref; goal:str; mentor_questions:list[str]; review_at:datetime | No login credential or secret ID; official source verifies status; disable in institution-managed context unless a separate personal store is proven |
| `research_scholarship_portfolio` | Private public/nonsensitive or approved research partition | project_or_topic:str; sponsor:str; human_determination:ref; approval_refs:list[ref]; data_class:enum; authorship_plan:str; dissemination_owner:str; status:enum; expiry:datetime | No research determination, approval, authorship, result or publication is fabricated or released by AI |
| `whole_life_private` | Personally controlled isolated store only; disabled institutionally | values:list[str]; goals:list[str]; family_logistics_categories:list[str]; finance_categories:list[str]; recovery_commitment:str; sharing_choice:enum; review_at:datetime; delete_at:datetime | Owner-only ACL; no account numbers, passwords, diagnoses or employer access; UI hiding is insufficient separation |
| `agent_charter_trace` | Private synthetic or separately approved agent partition | agent_id:str; objective:str; owner:str; beneficiary:str; state:enum; permission:enum; data_classes:list[str]; tools:list[str]; destinations:list[str]; tests:list[ref]; stop_rules:list[str]; expiry:datetime; kill_status:enum | ORBIT required; PERM-P0 Disabled by default; no clinical/device write, recursion, permission escalation or hidden persistence |
| `control_audit_receipt` | Same partition as controlled object; immutable to agent | receipt_id:str; object_ref:ref; action:enum; before_state:object; after_state:object; requested_by:str; approved_by:str; executed_by:str; occurred_at:datetime; result:enum; blocker:str; rollback_ref:ref; purge_ref:ref | Named human approval for consequential action; append-only audit; receipt cannot itself grant authority |

Every schema also requires `record_id:str`, `schema_version:str`, `owner_id:str`, `context:enum`, `data_class:enum`, `source_version:str`, `fact_interpretation:enum`, `human_decision_owner:str`, `status:enum`, `created_at:datetime`, `updated_at:datetime`, `expiry:datetime`, `retention_rule:str`, `correction_state:enum`, `export_state:enum` and `deletion_state:enum`. References may resolve only inside the same authorized lane and partition. Private, clinical, quality, research, education, personnel, agent and whole-life records cannot be joined across partitions. Conversation/model memory stays session-only; only an explicitly approved workspace artifact may persist with visible owner, ACL, retention and deletion. Unknown consequential fields display `Unknown — human verification required` and fail closed.

Whole-life, finance, family, health-care-time and recovery details require a personally controlled private workspace and isolated owner-only store. Disable those fields and the Career & Whole-Life agent in any institution-managed context unless that separation is technically proven; route labels—not personal details—are the safe default.

## Canonical Source Watch registry

| Authority | Source | Canonical URL | Intended use and precedence | Reviewed |
|---|---|---|---|---|
| AARC | Clinical Practice Guidelines | https://www.aarc.org/resource/clinical-practice-guidelines/ | Evidence hub; track each document's date and current/retired category | 2026-07-15 |
| AARC | Model Practice Act | https://www.aarc.org/advocacy/aarc-model-practice-act/ | Model only; never substitute for current state law or board rules | 2026-07-15 |
| AARC | Safe and Effective Staffing Guide | https://sesg.aarc.org/ | Optional licensed evidence context; never assign staff, prove adequacy or override local policy | 2026-07-15 |
| NBRC | Credentialed Practitioners and Credential Maintenance | https://www.nbrc.org/credentialed-practitioners/ | Official credential-status source; credential does not itself grant local licensure or scope | 2026-07-15 |
| CoARC | Accreditation and Program Resources | https://coarc.com/ | Education-program context; never infer an individual's competency or claim product accreditation | 2026-07-15 |
| HHS | HIPAA Minimum Necessary | https://www.hhs.gov/hipaa/for-professionals/privacy/guidance/minimum-necessary-requirement/index.html | Institutional privacy design; local privacy/legal owners interpret applicability | 2026-07-15 |
| HHS | De-identification Guidance | https://www.hhs.gov/hipaa/for-professionals/special-topics/de-identification/index.html | Real de-identification requires an approved method; self-redaction is not accepted in Private mode | 2026-07-15 |
| HHS | HIPAA Cloud Computing | https://www.hhs.gov/hipaa/for-professionals/special-topics/health-information-technology/cloud-computing/index.html | Institutional cloud authorization, risk analysis and agreement context | 2026-07-15 |
| AHRQ | TeamSTEPPS 3.0 | https://www.ahrq.gov/teamstepps-program/index.html | Human teamwork and communication reference; AI never closes the loop | 2026-07-15 |
| NIST | AI Risk Management Framework | https://www.nist.gov/itl/ai-risk-management-framework | Governance reference; version and revision status must be watched | 2026-07-15 |
| FDA | Clinical Decision Support Software Guidance | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software | January 2026 final guidance reference; regulatory review remains a qualified-human function | 2026-07-15 |
| FDA | Medical-Device Cybersecurity Guidance | https://www.fda.gov/regulatory-information/search-fda-guidance-documents/cybersecurity-medical-devices-quality-management-system-considerations-and-content-premarket | February 2026 final guidance reference; base product has no device connection | 2026-07-15 |
| W3C | Web Content Accessibility Guidelines 2.2 | https://www.w3.org/TR/WCAG22/ | Accessibility design and test reference | 2026-07-15 |

For every retrieved document, record exact title, publisher, publication/revision date, version, URL or approved reference, retrieved date, current/proposed/retired/superseded status, applicability, contradiction, local override, reviewer and expiry. A hub page's date never substitutes for the individual document's date. Retired, proposed, paywalled, unavailable and superseded items remain visibly labeled. Do not copy or redistribute licensed content.

BREATHE is an independent organizational and learning concept. It is not endorsed, certified, accredited or approved by AARC, NBRC, CoARC, HHS, AHRQ, NIST, FDA or W3C. Their publications are references, not product validation. Official NBRC records verify credential status; current law, licensing-board rules, license or permit, employer privileging and policy, medical direction, orders, protocols, manufacturer instructions and authorized humans determine local authority.

## My BREATHE foundation shell

Create one accessible home with the Core Four:

1. **Orient Shift & Capacity**
2. **Learn & Verify**
3. **Coordinate Care & Equipment**
4. **Review, Escalate & Close**

Leave the optional fifth launcher empty. Show at most seven attention items. Permanent controls: Context & Role; Scope & Credential; Orders & Protocols; Privacy & Data; Sources & Freshness; Capacity & Recovery; Human Decision Queue; Agent Registry & Kill Switch; History; Pause All; Safe Reset; Correct; Export; Delete; Rollback; Remove Power; Remove Overlay; Full Uninstall.

## Human and professional standard

The respiratory care professional remains the accountable human for their observations, communication and practice. The authorized prescriber, medical director, clinical team, operational leader, educator, credentialing body, quality or research authority and institution retain their own decisions. The OS prepares, explains, organizes, rehearses and checks. It never grants scope, places an order, controls a device, changes therapy, certifies competence or becomes the source of truth.
