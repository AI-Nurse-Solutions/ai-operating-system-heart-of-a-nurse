# Nurse AI OS Post-Setup Role Packs

These are separate post-setup downloads for users who have already completed their SOUL files and Hermes setup. Lane 05 is a review-first overlay. Lanes 01, 02, 03, and 04 are governed self-install Hermes build kits. Lane 06 is a separately governed Complete Edition. Every lane requires review or read-only preflight and exact human approval before any installation mutation.

## Role folders

| Folder | User-facing role | Download |
|---|---|---|
| `01-Student-Nurse` | Nursing Student and Nursing Assistant | `downloads/FUTURE-Nursing-Student-Nursing-Assistant-Mission-Control-Hermes-Build-Kit-v1.0.0.zip` |
| `02-Staff-Nurse` | Staff Nurse and Quality Contributor | `downloads/STAFF-Nurse-Life-Practice-SHIFT-Mission-Control-Hermes-Build-Kit-v1.0.0.zip` |
| `03-Nurse-Leader-and-Manager` | Nurse Leader and Manager | `downloads/LEAD-Nurse-Leader-Manager-Mission-Control-Hermes-Build-Kit-v1.0.0.zip` |
| `04-Nurse-Educator` | Nurse Educator and Instructional Designer | `downloads/TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-Build-Kit-v1.0.0.zip` |
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

Lane 05 uses the review-first prompt and requires proposed changes, risks, permissions, conflicts, and rollback before the user decides whether anything should be applied. Self-install lanes 01, 02, 03, and 04 require the complete ZIP, package verification, read-only environment preflight, and one exact Implementation Activation Card. Complete Edition lane 06 uses its supplied one-file Hermes program and exact combined activation card. No lane mutates the target before explicit approval.

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

The Nursing Student and Nursing Assistant download is a reproducible governed self-install Hermes build kit. The tracked public-safe source includes:

- `README-FIRST.md` and `GIVE-THIS-PACKAGE-TO-HERMES.md`
- `RELEASE-MANIFEST.json`, `SOURCE-INVENTORY.json`, and `SHA256SUMS.txt`
- `BUILD-STATUS.md`, implementation contracts, personalization schemas, and safe synthetic fixtures
- the pinned working Mission Control baseline and FUTURE specialization corpus under `source/`
- the legacy Complete Edition program and guides under `source/legacy-reference/` as provenance—not as the public handoff
- `tools/verify-build-kit.py`

The dedicated tracked-source builder normalizes the outer ZIP, validates all 105 members and the original-source derivative provenance, and executes the tracked verifier against both the package directory and outer ZIP. FUTURE supports Nursing Student, Nursing Assistant, and Bridge pathways. Its target contract contains 24 foundation, 96 FUTURE overlay, and 16 integration checks—136 canonical compatibility checks—plus 169 control tests and 44 cross-cutting scenarios, for 349 required execution records. Every result begins `Not Run`. All eighteen optional SuperPowers remain `Available Inactive`; all ten suggested agents remain `PERM-P0 Disabled`; workflows remain `Preview Only`; connectors, sharing, schedules, external actions, new persistent memory categories, and background automation remain off. Downloading does not install it. Pathway selection does not verify enrollment, certification, employment, scope, delegation, supervision, competence, or institutional permission, and a private build does not authorize school, clinical-site, employer, community, or organizational deployment.

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

The Nurse Educator and Instructional Designer TEACH ZIP is a separately governed self-install Hermes build kit. It includes:

- `README-FIRST.md`
- `GIVE-THIS-PACKAGE-TO-HERMES.md`
- `RELEASE-MANIFEST.json`
- `SHA256SUMS.txt`
- `SOURCE-INVENTORY.json`
- `tools/verify-build-kit.py`
- TEACH implementation, schemas, controls, templates, synthetic examples, and baseline QA references needed for a future local build

The TEACH build kit supports Nurse Educator, Instructional Designer, and Hybrid / Faculty Developer adapters. It remains `not_operational_build_required` on download. A local Hermes must verify the manifest, checksums, and unchanged outer ZIP; complete read-only preflight; show the exact TEACH Implementation Activation Card; and receive explicit approval before any local build mutation. Its pinned contract preserves 33 foundation checks, 120 TEACH overlay checks, and 16 integration checks—169 canonical checks, 264 explicit target rows, and 433 required execution records. All twenty optional TEACH SuperPowers remain inactive. Downloading does not install it. Adapter selection does not verify employment, faculty status, instructional-design assignment, teaching, grading, clinical, accommodation, academic-integrity, curriculum, accreditation, research, release, or institutional authority. Private-workspace approval does not authorize LMS, classroom, clinical-site, program, employer, accreditation, research, multi-user, or institutional deployment.

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
