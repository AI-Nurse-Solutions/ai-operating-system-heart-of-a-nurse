# FUTURE Personalization Package

## Purpose

This folder demonstrates how a supported, derived Discover Packet and Soul Profile can become a proposed FUTURE Mission Profile for `FUTURE Mission Control` at `/nursing-students-assistants/dashboard`.

Personalization can change wording, layout, role-workspace candidates, learning cadence, dashboard modules and the inactive recommendation queue. It cannot establish enrollment, employment, role, local scope, delegation, supervision, competence, certification, licensure, authority, permission, academic compliance or clinical readiness.

## Files

- `FUTURE-Discover-Packet.synthetic.example.json` — valid synthetic input for the baseline `NAIO-DISCOVER-PACKET-ADAPTER-1` schema.
- `FUTURE-Soul-Profile.synthetic.example.json` — valid synthetic input for the baseline `NAIO-SOUL-PROFILE-ADAPTER-1` schema. It contains exactly one Primary role.
- `FUTURE-Mission-Profile.synthetic.example.json` — proposed normalized result for the closed schema at `../schemas/FUTURE-Mission-Profile.schema.json`.
- `../implementation/FUTURE-Personalization-Mapping-Crosswalk.md` — deterministic field, role and catalog mappings.
- `../implementation/FUTURE-Starter-Workspace-Crosswalk.md` — optional role-workspace starters and their hard stops.

All three examples are synthetic. They must remain visibly labeled and excluded from badges, credentials, analytics, educational records, employment records and claims about outcomes.

## Safe import sequence

1. Work in the private local owner session. Do not upload raw quiz answers, interview notes, course records, employee records or patient material.
2. Enforce the package file-size, depth, unsafe-key, direct-identifier, credential and prohibited-content checks before parsing.
3. Validate each adapter against the exact bundled baseline schema and version. Reject unknown properties and unsupported versions.
4. Build a transient proposal. Do not persist the raw adapter.
5. Display source conflicts, missing values, uncertainty and the practical effect of each proposed field.
6. Ask the minimum first-run questions one at a time. Keep **Skip**, **Not now**, **Use this session only**, **Show an example** and **Ask a human** visible.
7. Ask the user to select Nursing Student, Nursing Assistant or Bridge and choose exactly one Primary role workspace. A label never proves scope or authority.
8. Confirm the active protected space and precise operational context: academic learning, clinical-placement learning, employment growth, personal life, or public/community future. Bridge school and work partitions never merge automatically.
9. Resolve only pinned catalog relations. FUTURE recommendations remain inactive. A bounded agent ID may be recommended by explicit task intent, but every agent remains PERM-P0 Disabled and receives no run, data, memory, model, tool or permission grant. Tool IDs remain empty.
10. Show a complete review screen. Save only after explicit approval, closed-schema validation and semantic validation.
11. Write atomically, record bounded field provenance and retain no raw source. Memory remains Off or session-only until a separate consent step.

## Prohibited inputs

Do not import or retain:

- PHI, patient stories, screenshots, chart excerpts, recordings, room-linked narratives, rare identifying combinations or live-care questions;
- names, student or employee identifiers, person-level school or employer records, disciplinary, accommodation, grievance, investigation or health information;
- live exams, restricted assessment content, answer keys or a request for deceptive completion;
- passwords, tokens, secrets, financial credentials or secret URLs;
- fabricated sources, experiences, hours, competencies, reflections, credentials or signatures; or
- confidential school, clinical-site or employer information.

The sensitive-content response is: stop without repeating the content, prevent further use or retention where controls permit, show deletion and activity options, and route the user to the responsible privacy, faculty, clinical-site, supervisor, security, HR, compliance or emergency process.

## Required invariants

- Product ID: `future-nursing-student-assistant-mission-control`
- Lane: `nursing_student_assistant`
- Namespace: `future.*`
- Canonical route: `/nursing-students-assistants/dashboard`
- Home label: **FUTURE Mission Control**
- Exactly one Primary role workspace
- One visible active protected context per mission
- Attempt before answer for learning tasks
- Learner authorship and applicable AI-use disclosure preserved
- No clinical direction, scope widening or competency determination
- No PHI or person-level school/employer data
- All FUTURE powers and workflows inactive until separately previewed and approved
- Agent recommendations, if shown, remain PERM-P0 Disabled; tools disabled with empty tool IDs; connectors off; external actions off; automation manual/preview only

## Meaning of the examples

The examples prove only that the proposed data shape can be validated and rendered. They do not prove that a real person has the stated identity, role, education, employment, authority or ability. They are not a clinical competency record, school credential, employer certification, licensure record, or guarantee of examination success.

Before release, test Discover-only, Soul-only, both consistent, both conflicting, neither, unknown role, unsupported version, invalid enum, multiple/no Primary, prohibited-content rejection, catalog missing/duplicate/version mismatch, approve/edit/reject/delete/export, context switching, demo exclusion and provenance completeness.
