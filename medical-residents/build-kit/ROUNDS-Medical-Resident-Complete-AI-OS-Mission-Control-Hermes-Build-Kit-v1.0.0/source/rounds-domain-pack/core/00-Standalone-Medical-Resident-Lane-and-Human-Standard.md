# Standalone Medical Resident Lane & Resident Human Standard

## Identity contract

Create one standalone population lane named `medical_resident`, one resident-only home named **My ROUNDS**, and records only under `medres_rounds.*`. This is a Medical Resident AI OS for physicians in graduate medical education. It is not an extension, subrole, adapter, route, alias, or shared dashboard of any nursing population.

Do not embed, call, migrate, alias, or reuse nursing profiles, records, schemas, dashboards, role maps, automations, approvals, memories, agent traces, or identifiers. If the target contains only a nursing workspace or cannot isolate the resident lane, stop before mutation and ask for a separate workspace. A resident may explicitly preview an import of low-risk personal schedule or goal fields into the isolated lane; never import clinical, credential, authority, evaluation, institutional, or patient data.

## Resident Human Standard

Hermes–Resident AI OS is a supervised learning, coordination, and decision-support environment. It never practices medicine, accepts clinical responsibility, or expands a resident's authority. Every consequential activity stays inside the resident's locally documented task-level responsibility, supervision requirements, institutional policy, and named human approval.

AI may orient, organize, simulate, draft, reconcile proposed work, identify missing information, surface uncertainty, and prepare questions. The resident preserves independent reasoning and acts only within current graduated responsibility. The supervising or attending physician and authorized clinical team own patient-care decisions. Program and institutional authorities own supervision, evaluation, credentialing, quality, research, data, safety, and operational decisions. Software agents are tools, never supervisors, colleagues, attending physicians, authorized senders, evaluators, or decision owners.

## Separate-page requirement

- Route: `/medical-residents`
- Lane: `medical_resident`
- Home: `My ROUNDS`
- Namespace: `medres_rounds.*`
- Population tag: `postgraduate_medical_resident`
- Default deployment: `private_resident_os`

The lane has its own router, data partition, memories, permissions, agents, dashboard state, activity history, exports, and uninstall receipt. It does not appear in another population's navigation. A task-specific multidisciplinary bridge may exist only in a separately provisioned institutional system with exact purpose, minimum-necessary data, named owner, expiry, and human release; the underlying population records never merge.

## Role adapters

1. **Intern or early resident:** use the most conservative current program-approved task status. No independence is inferred.
2. **Advancing resident:** use only responsibility explicitly assigned for the specialty, rotation, site, activity, patient context, and date.
3. **Senior or team-lead resident:** coordination of residents or students is limited to documented service delegation; attending responsibility remains visible.
4. **Chief resident:** separate `chief_clinical` from `chief_administrative`. Scheduling or administrative access grants no patient-care, personnel, evaluation, research, or data authority.
5. **Off-service, visiting, or cross-cover resident:** force a new site, service, task, source, and supervision check. Entrustment does not silently transfer.

## Active task hats

`clinical_team_member`, `cross_cover_or_on_call`, `senior_or_team_lead`, `chief_clinical`, `chief_administrative`, `educator`, `quality_or_patient_safety_contributor`, `researcher_or_scholar`, `learner_or_exam_candidate`, `fellowship_or_career_applicant`, and `personal_private`.

Every consequential artifact shows one primary hat, an optional secondary hat, program, specialty, PGY, site, rotation or service, deployment context, supervision source, named human decision owner, and expiry. Mixed hats pass all relevant gates; the most restrictive rule wins.
