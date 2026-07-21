
# Medical Resident ROUNDS Mission Control — Product Specification

## Identity and inventory

| Item | Value |
|---|---|
| Product | `ROUNDS — Medical Resident Complete AI OS Mission Control` |
| Product ID | `medical-resident-rounds-mission-control` |
| Target version | `2.0.0` |
| Complete source | `MRAIOS-ROUNDS-COMPLETE-1.0` |
| Foundation | `MRAIOS-LIFE-TRAINING-PRACTICE-1.0` |
| Overlay | `MRAIOS-ROUNDS-1.0` |
| Lane / route | `medical_resident` / `/medical-residents` |
| Namespace / home | `medres_rounds.*` / `My ROUNDS` |
| Readiness | `not_operational_build_required` |

Canonical inventory: one home, five role adapters, 11 hats, 17 resident-owned record types, Core Four + empty fifth, 24 powers, 24 workflows, 30 templates, 10 suggested agents, and 160 release checks.

## Purpose

The product supports private residency orientation, duty/recovery planning, deliberate learning from public sources, fictional reasoning exercises, supervision-question preparation, synthetic communication and CIRCLE rehearsal, resident-controlled feedback reflection, exam/credential planning, teaching, synthetic QI/research planning, career/contract preparation, family/finance/purpose planning, and bounded AI stewardship.

It does not provide or carry out patient care, supervision, evaluation, credentialing, duty compliance, QI/research classification, institutional action, or external communication.

## One home and five protected record scopes

`My ROUNDS` is the only dashboard. These source-defined departments appear as record scopes and filters inside it:

1. Role, Duty & Life
2. Learning, Reasoning & Evidence
3. Supervision, Communication & Orchestration
4. Development, Quality & Scholarship
5. Credentials, Career & Future

They are not separate dashboards, data stores, or authority domains. Every mission selects one active scope and one partition. It has one primary hat and may have one secondary hat; every applicable gate runs and least privilege wins.

Nine resident-only views are required: Home; Rotation/Duty/Readiness; Learning/Evidence/Synthetic Reasoning; CIRCLE Studio; Supervision/ATTEND/Human Decision Queue; Training/Feedback/Milestones/Credentials; Teaching/Quality/Safety/Research/Scholarship; ORBIT Tower; and Fellowship/Career/Whole Life.

## Contexts

The active personal context is `private_resident_os`. Approved clinical, education, quality/safety, research, and GME/administrative contexts are declared for future interoperability but technically unavailable. This kit cannot certify or unlock them.

## Core Four and mission loop

The Core Four are: Orient My Day & Duty, Learn & Reason, Orchestrate & Communicate, Review, Escalate & Close. The optional fifth launcher remains empty.

The implementation-generated loop is Assess → Define → Plan → Implement preparation → Evaluate. “Define” is not a clinical diagnosis. “Implement” creates local drafts, tasks, questions, or fictional simulations; it never performs care, a real handoff, a QI pilot, research, submission, communication, or release.

## Records and truth

Retain exactly the 17 canonical record types in `config/MR-Professional-Schema-Registry.v1.json`. All consequential artifacts show primary/secondary hats, program, specialty, PGY, site, rotation/service, context, supervision state, source, human decision-owner role, and expiry.

Artifact lifecycle reference vocabulary: Exploration → Simulation → Recommendation → Draft Artifact → Approved Plan → Authorized Execution → Completed Action → Evaluated Outcome. This personal target can reach no state after Approved Plan. Authorized Execution, Completed Action, and Evaluated Outcome are reference-only labels for an external accountable-human process and have no route, transition, connector, executor, imported attestation, or official-status store here. `MR-DATA-R` is only a locally generated, content-free, nonresolving receipt ID; it cannot prove or advance external completion. An optional owner note may say only `resident-reported_external_status_unverified` and never changes lifecycle state.
