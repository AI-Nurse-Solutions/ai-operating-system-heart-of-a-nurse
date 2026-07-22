# FUTURE Mission Control — Hermes Functional Build Kit

**Build-kit ID:** `NAIO-FUTURE-FUNCTIONAL-BUILD-KIT-1.0.0`  
**Target product:** `FUTURE — Nursing Student & Nursing Assistant Mission Control`  
**Target product ID:** `future-nursing-student-assistant-mission-control`  
**Target application version:** `2.0.0`  
**Lane:** `nursing_student_assistant`  
**Build-layer canonical dashboard:** `/nursing-students-assistants/dashboard`  
**Namespace:** `future.*`  
**Home:** `FUTURE Mission Control`

This is the downloadable package to give Hermes so it can build, test, and package the real local FUTURE application. It combines the working Nurse AI OS Mission Control v2 source baseline, the complete immutable FUTURE learner corpus, a resolved functional-build contract, implementation contracts, safe synthetic personalization fixtures, acceptance controls, recovery instructions, and an independent verifier.

The lane, URL, home label, `FUT-*` catalog IDs, data schemas, agents, and permission model are **build-layer decisions**. The legacy corpus did not define them. The immutable legacy authority remains `NAIO-FUTURE-COMPLETE-1.0`, `NAIO-FUTURE-CORE-1.0`, `NAIO-FUTURE-SP-1.0`, and namespace `future.*`.

## Honest status

This ZIP is a verified **functional-build kit**, not the already-finished target application. The bundled baseline is a working offline dashboard, but Hermes must implement and verify the FUTURE specialization, durable server-side storage, authenticated access, genuine streamed AI, consent-controlled memory, evidence retrieval, agent sessions, and clean installation before calling the target Operational.

Initial target readiness: **Not operational — build required.**

## Pinned FUTURE baseline

- 3 pathways: Nursing Student, Nursing Assistant, and Bridge.
- 4 Core launchers and 1 deliberately empty optional launcher.
- 18 optional SuperPowers, all installed `Available Inactive`.
- 18 guided recipe mappings and 5 reusable templates.
- 6 AI Literacy Passport domains and 5 developmental stages.
- 24 foundation tests + 96 overlay tests + 16 integration checks = **136 canonical compatibility checks**.
- 169 one-to-one control tests + 44 cross-cutting full-stack scenarios + 136 canonical checks = **349 required execution records**, all initially `Not Run`.
- All external actions, connectors, schedules, sharing, background automation, and agents start off.
- Private, synthetic demonstration, no PHI, session-only, manual/preview defaults.

## Give the ZIP to Hermes

1. Keep the original ZIP unchanged in a learner-controlled local folder.
2. Extract it. On macOS/Linux, use Finder/Archive Utility or `unzip`; Python's `zipfile.extractall()` does not preserve executable mode bits and the strict package check will fail. If that occurs, discard that extraction and extract the unchanged ZIP again with a mode-preserving tool rather than changing modes blindly. From the extracted package root run:

   ```text
   python3 tools/verify-build-kit.py --package .
   ```

   On Windows use `py` or `python` if needed. To check the outer archive too:

   ```text
   python3 tools/verify-build-kit.py --package . --zip ../FUTURE-Nursing-Student-Nursing-Assistant-Mission-Control-Hermes-Build-Kit-v1.0.0.zip
   ```

3. Start Hermes in a new or verified-isolated implementation workspace.
4. Give Hermes the ZIP and say:

   > Unpack this build kit, open `GIVE-THIS-PACKAGE-TO-HERMES.md`, verify the manifest and checksums, and follow the program exactly. Start with read-only preflight. Do not install dependencies, edit files, start services, change my Hermes profile, or enable any SuperPower or agent until you show the Implementation Activation Card and I approve it.

5. Save every checkpoint receipt and the final handoff report.

## Allow enough time

This can take **many minutes and several visible Hermes turns**. Source inspection, dependency installation, database migrations, UI conversion, capability discovery, security tests, accessibility tests, clean-install verification, and packaging are real work. Nothing continues invisibly after a Hermes turn ends; Hermes must report any running process by identifier.

## Read in this order

1. `GIVE-THIS-PACKAGE-TO-HERMES.md`
2. `implementation/FUTURE-Functional-Build-Master-Prompt.md`
3. `implementation/FUTURE-Product-Specification.md`
4. `implementation/FUTURE-Architecture-and-Data-Model.md`
5. `implementation/FUTURE-Personalization-Mapping-Crosswalk.md`
6. `implementation/FUTURE-Starter-Workspace-Crosswalk.md`
7. `implementation/FUTURE-Governance-EDENA-and-Data-Boundaries.md`
8. `implementation/FUTURE-Agent-Team-and-Routing.md`
9. `implementation/FUTURE-Capability-and-Badge-Evidence-Model.md`
10. `config/FUTURE-Capability-Mastery-Criteria.v1.json`
11. `implementation/FUTURE-Guide-Page-Content.md`
12. `implementation/FUTURE-Security-and-Privacy-Checklist.md`
13. `implementation/FUTURE-Control-Completeness-Matrix.csv`
14. `implementation/FUTURE-Acceptance-and-Test-Ledger.md`
15. `implementation/FUTURE-Synthetic-Sample-Mission.md`
16. the immutable source material under `source/`

## Non-negotiable boundary

Never enter patient information, identifiable clinical stories, chart content, live-care questions, exams, prohibited assessed work, restricted school/employer material, credentials, secrets, or financial account data. The target must not decide care, diagnosis, treatment, medication administration, device settings, scope, assignment, delegation, documentation, competence, grades, certification, employment, or eligibility. Faculty, programs, clinical sites, employers, supervising nurses, policies, and accountable humans remain authoritative.
