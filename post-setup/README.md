# Nurse AI OS Post-Setup Role Packs

These are separate post-setup downloads for users who have already completed their SOUL files and Hermes setup. Lanes 02, 04, and 05 are review-first overlays. Lanes 01, 03, and 06 are separately governed Complete Editions with read-only preflight and exact activation-card approval before any installation mutation.

## Role folders

| Folder | User-facing role | Download |
|---|---|---|
| `01-Student-Nurse` | Nursing Student and Nursing Assistant | `downloads/nurse-ai-os-post-setup-student-nurse.zip` |
| `02-Staff-Nurse` | Staff Nurse | `downloads/nurse-ai-os-post-setup-staff-nurse.zip` |
| `03-Nurse-Leader-and-Manager` | Nurse Leader and Manager | `downloads/nurse-ai-os-post-setup-nurse-leader-and-manager.zip` |
| `04-Nurse-Educator` | Nurse Educator | `downloads/nurse-ai-os-post-setup-nurse-educator.zip` |
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

The user unzips one role folder. Lanes 02, 04, and 05 use the review-first prompt and require proposed changes, risks, permissions, conflicts, and rollback before the user decides whether anything should be applied. The Nursing Student and Nursing Assistant, Nurse Leader, and USA-only Nurse Practitioner Complete Editions use their supplied one-file Hermes programs, read-only preflights, exact combined activation cards, phased checkpoints, and explicit approval before any installation mutation.

## Package contents

Review-first lanes 02, 04, and 05 include:

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

The Nurse Leader and Manager ZIP is a separately governed Complete Edition. It includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- `Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Hermes-Program.md` — complete one-file guided installer
- `Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.md`
- `Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.docx`
- `PACKAGE-CHECKSUMS.sha256`

The Leader program establishes, repairs, or binds the foundation first, runs 21 foundation tests, adds the LEAD Library as an inactive overlay, and runs 80 LEAD tests plus 12 integration checks. All sixteen optional SuperPowers remain inactive. Downloading does not install it. Role selection does not verify managerial or organizational authority, and private-workspace approval does not authorize organizational deployment.

The Nurse Practitioner ZIP is a separately governed Complete Edition. It includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- `NP-Complete-AI-OS-with-Wings-Hermes-Program.md` — complete one-file guided installer
- `NP-Complete-AI-OS-with-Wings-Setup-Guide.md`
- `NP-Complete-AI-OS-with-Wings-Setup-Guide.docx`
- `PACKAGE-CHECKSUMS.sha256`

The NP program is English-language and United States-only. It establishes the foundation first, adds NP Wings as an inactive overlay, and contains 63 foundation plus 82 Wings acceptance tests. Downloading does not install it. Role selection does not verify NP licensure, certification, population focus, privileges, prescriptive authority, competence, employment authority, or institutional approval.

Role selection provides personalization only. It does not verify licensure, enrollment, employment, faculty status, managerial authority, institutional authorization, or permission to process patient or personnel information.

## Rebuild

Rebuild ZIPs deterministically from the tracked package folders:

```bash
python3 scripts/build-post-setup-role-packs.py
```

To import a new user-authorized source bundle into an empty package tree, supply the three review-first source folders plus intact prebuilt `01-Student-Nurse`, `03-Nurse-Leader-and-Manager`, and `06-Nurse-Practitioner-USA` folders:

```bash
python3 scripts/build-post-setup-role-packs.py --import-source /path/to/source
```

The importer refuses to overwrite an existing role package. Review and version source changes deliberately.

## Governance boundary

No PHI. No patient-specific clinical decisions. Downloading never installs. Connectors, shared access, external actions, new memory categories, and background automation remain off unless separately governed. Onboarding remains Green or Yellow unless separately governed. Private-workspace approval never authorizes organizational deployment.

*Agents propose. Humans judge. Nurses steward.*
