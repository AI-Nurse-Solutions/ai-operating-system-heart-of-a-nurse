# Nurse AI OS Post-Setup Role Packs

These are separate, review-first downloads for users who have already completed their SOUL files and Hermes setup.

## Role folders

| Folder | User-facing role | Download |
|---|---|---|
| `01-Student-Nurse` | Student Nurse | `downloads/nurse-ai-os-post-setup-student-nurse.zip` |
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

The user unzips one role folder. Lanes 01–05 use the review-first prompt and require proposed changes, risks, permissions, conflicts, and rollback before the user decides whether anything should be applied. The USA-only Nurse Practitioner lane uses its supplied one-file Hermes program, read-only preflight, one combined activation card, phased checkpoints, and explicit approval before any installation mutation.

## Package contents

Lanes 01–05 include:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- Role-specific Hermes Program
- Role-specific Guide
- Shared SuperPowers README, clearly marked as a design reference because the full module tree was not supplied
- Shared SuperPowers master-installer document, clearly marked as non-executable reference material
- Shared SuperPowers User Guide, retained as reference material
- `PACKAGE-CHECKSUMS.sha256`

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

To import a new user-authorized source bundle into an empty package tree:

```bash
python3 scripts/build-post-setup-role-packs.py --import-source /path/to/source
```

The importer refuses to overwrite an existing role package. Review and version source changes deliberately.

## Governance boundary

No PHI. No patient-specific clinical decisions. Downloading never installs. Connectors, external actions, new memory categories, and background automation remain off unless separately governed. Onboarding remains Green or Yellow unless separately governed.

*Agents propose. Humans judge. Nurses steward.*
