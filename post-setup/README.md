# Nurse AI OS Post-Setup Role Packs

These are separate post-setup downloads for users who have already completed their SOUL files and Hermes setup. Lane 05 is a review-first overlay. Lanes 02 and 03 are reproducible self-install Hermes build kits. Lanes 01, 04, and 06 are separately governed Complete Editions. Every lane requires review or read-only preflight and exact human approval before any installation mutation.

## Role folders

| Folder | User-facing role | Download |
|---|---|---|
| `01-Student-Nurse` | Nursing Student and Nursing Assistant | `downloads/nurse-ai-os-post-setup-student-nurse.zip` |
| `02-Staff-Nurse` | Staff Nurse and Quality Contributor | `downloads/STAFF-Nurse-Life-Practice-SHIFT-Mission-Control-Hermes-Build-Kit-v1.0.0.zip` |
| `03-Nurse-Leader-and-Manager` | Nurse Leader and Manager | `downloads/LEAD-Nurse-Leader-Manager-Mission-Control-Hermes-Build-Kit-v1.0.0.zip` |
| `04-Nurse-Educator` | Nurse Educator and Instructional Designer | `downloads/nurse-ai-os-post-setup-nurse-educator.zip` |
| `05-Nurse-Connected-Ally` | Nurse-Connected Ally | `downloads/nurse-ai-os-post-setup-nurse-connected-ally.zip` |
| `06-Nurse-Practitioner-USA` | Nurse Practitioner (USA) | `downloads/nurse-ai-os-post-setup-nurse-practitioner-usa.zip` |

## What downloading does

Nothing is installed or activated. Every package declares:

```json
{
  "install_on_download": false,
  "automatic_memory": false,
  "automatic_connectors": false,
  "automatic_external_actions": false,
  "automatic_cron": false
}
```

Lane 05 uses the review-first prompt and requires proposed changes, risks, permissions, conflicts, and rollback before the user decides whether anything should be applied. Self-install lanes 02 and 03 require the complete ZIP, package verification, read-only environment preflight, and one exact Implementation Activation Card. Complete Edition lanes 01, 04, and 06 use their supplied one-file Hermes programs and exact combined activation cards. No lane mutates the target before explicit approval.

## Package contents

Review-first lane 05 includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- Role-specific Hermes Program
- Role-specific Guide
- Shared SuperPowers README, clearly marked as a design reference because the full module tree was not supplied
- Shared SuperPowers master-installer document, clearly marked as non-executable reference material
- Shared SuperPowers User Guide, retained as reference material
- `PACKAGE-CHECKSUMS.sha256`

The Nursing Student and Nursing Assistant ZIP is a separately governed Complete Edition. It includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- `Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Hermes-Program.md` — complete one-file guided installer
- `Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.md`
- `Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.docx`
- `PACKAGE-CHECKSUMS.sha256`

The FUTURE program supports Nursing Student, Nursing Assistant, and Bridge pathways. It creates, repairs, or binds the foundation first, runs 24 foundation tests, adds the FUTURE Library and Passport as an inactive overlay, and runs 96 FUTURE tests plus 16 integration checks—136 embedded release checks in total. All eighteen optional SuperPowers remain inactive. Bridge keeps academic and employment contexts separate. Downloading does not install it. Pathway selection does not verify enrollment, certification, employment, scope, delegation, supervision, competence, or institutional permission, and private-workspace approval does not authorize school, clinical-site, employer, community, or organizational deployment.

The Staff Nurse and Quality Contributor download is a governed self-install Hermes build kit. Its immutable role source includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- `Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Hermes-Program.md` — complete one-file guided installer
- `Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.md`
- `Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.docx`
- `PACKAGE-CHECKSUMS.sha256`

The public wrapper adds `README-FIRST.md`, `GIVE-THIS-PACKAGE-TO-HERMES.md`, an exact activation-card gate, release manifest, checksums, source provenance, and a verifier. SHIFT supports Direct-Care Staff Nurse; Unit Champion, Preceptor, or Shared-Governance Member; Chartered Staff-Nurse QI Project Lead; and Hybrid / Multiple-Employer adapters. Its canonical contract contains 40 foundation, 120 SHIFT, and 16 integration checks. Downloading does not install it, and all twenty optional powers remain inactive. Role selection verifies no licensure, employment, competence, assignment, delegation, supervision, quality appointment, sponsor authority, institutional access, or data permission. Private-workspace approval does not authorize institutional quality work.

The Nurse Leader and Manager download is a reproducible governed self-install Hermes build kit. The public wrapper includes:

- `README-FIRST.md`
- `GIVE-THIS-PACKAGE-TO-HERMES.md`
- `IMPLEMENTATION-ACTIVATION-CARD.md`
- `FINAL-HANDOFF-REPORT.md`
- `RELEASE-MANIFEST.json`
- `SOURCE-PROVENANCE.json` and `SOURCE-INVENTORY.json`
- `SHA256SUMS.txt`
- `tools/verify-build-kit.py`
- the exact tracked `03-Nurse-Leader-and-Manager` source folder, including its original program, guides, role manifest, and checksums

The source archive's three supplied files are preserved byte-for-byte. The builder copies the tracked source into a temporary package, generates inventories and ledgers, creates a deterministic outer ZIP, and executes the tracked verifier against both the package directory and the ZIP. The canonical 21 foundation, 80 LEAD, and 12 integration checks—113 total—begin `Not Run` in each target environment. All sixteen optional powers remain `Available Inactive`; agents remain `PERM-P0 Disabled`; connectors, sharing, schedules, external actions, new persistent memory categories, and organizational-system access remain off. No route is preassigned. Downloading does not install or activate anything, role selection verifies no managerial or organizational authority, and a private build does not authorize organizational deployment.

The Nurse Educator and Instructional Designer ZIP is a separately governed Complete Edition. It includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- `Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Hermes-Program.md` — complete one-file guided installer
- `Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.md`
- `Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.docx`
- `PACKAGE-CHECKSUMS.sha256`

The TEACH program supports Nurse Educator, Instructional Designer, and Hybrid / Faculty Developer adapters. It creates, repairs, or binds the Nurse Educator foundation first, runs 33 foundation checks, adds the Trust Shield, TEACH Core, Command Studio, templates, and twenty optional SuperPowers as an inactive overlay, and runs 120 TEACH tests plus 16 integration checks—169 embedded release checks in total. All twenty optional TEACH SuperPowers remain inactive. Downloading does not install it. Adapter selection does not verify employment, faculty status, instructional-design assignment, teaching, grading, clinical, accommodation, academic-integrity, curriculum, accreditation, research, release, or institutional authority. Private-workspace approval does not authorize LMS, classroom, clinical-site, program, employer, accreditation, research, multi-user, or institutional deployment.

The Nurse Practitioner ZIP is a separately governed Complete Edition. It includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- `NP-Complete-AI-OS-with-Wings-Hermes-Program.md` — complete one-file guided installer
- `NP-Complete-AI-OS-with-Wings-Setup-Guide.md`
- `NP-Complete-AI-OS-with-Wings-Setup-Guide.docx`
- `PACKAGE-CHECKSUMS.sha256`

The NP program is English-language and United States-only. It establishes the foundation first, adds NP Wings as an inactive overlay, and contains 63 foundation plus 82 Wings acceptance tests. Downloading does not install it. Role selection does not verify NP licensure, certification, population focus, privileges, prescriptive authority, competence, employment authority, or institutional approval.

Role selection provides personalization only. It does not verify licensure, enrollment, employment, faculty status, instructional-design assignment, teaching or grading authority, managerial authority, accreditation authority, institutional authorization, or permission to process patient, student, employee, or personnel information.

## Rebuild

Rebuild ZIPs deterministically from the tracked package folders and tracked build-kit wrapper sources:

```bash
python3 scripts/build-post-setup-role-packs.py
```

To import a new user-authorized source bundle into an empty package tree, supply the review-first lane-05 source folder plus intact prebuilt `01-Student-Nurse`, `02-Staff-Nurse`, `03-Nurse-Leader-and-Manager`, `04-Nurse-Educator`, and `06-Nurse-Practitioner-USA` folders:

```bash
python3 scripts/build-post-setup-role-packs.py --import-source /path/to/source
```

The importer refuses to overwrite an existing role package. Review and version source changes deliberately.

## Governance boundary

No PHI. No patient-specific clinical decisions. Downloading never installs. Connectors, shared access, external actions, new memory categories, and background automation remain off unless separately governed. Onboarding remains Green or Yellow unless separately governed. Private-workspace approval never authorizes organizational deployment.

*Agents propose. Humans judge. Nurses steward.*
