# Nurse AI OS Post-Setup Role Packs

These are separate, review-first downloads for users who have already completed their SOUL files and Hermes setup.

## Role folders

| Folder | User-facing role | Download |
|---|---|---|
| `01-Student-Nurse` | Student Nurse | `downloads/nurse-ai-os-post-setup-student-nurse.zip` |
| `02-Staff-Nurse` | Staff Nurse | `downloads/nurse-ai-os-post-setup-staff-nurse.zip` |
| `03-Nurse-Leader-and-Manager` | Nurse Leader and Manager | `downloads/nurse-ai-os-post-setup-nurse-leader-and-manager.zip` |
| `04-Nurse-Educator` | Nurse Educator | `downloads/nurse-ai-os-post-setup-nurse-educator.zip` |
| `05-Nurse-Connected-Ally` | Non-nurse user who selected Other | `downloads/nurse-ai-os-post-setup-nurse-connected-ally.zip` |

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

The user unzips one role folder and asks Nurse AI OS to review the package. The system must present proposed changes, risks, permissions, conflicts, and rollback before the user decides whether anything should be applied.

## Package contents

Each role ZIP includes:

- `00-READ-FIRST.md`
- `ROLE-PACK.json`
- Role-specific Hermes Program
- Role-specific Guide
- Shared SuperPowers post-setup README
- Shared SuperPowers installer reference
- Shared SuperPowers User Guide
- `PACKAGE-CHECKSUMS.sha256`

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

No PHI. No patient-specific clinical decisions. No automatic installation, memory, connectors, cron, external actions, or profile changes. Onboarding remains Green or Yellow unless separately governed.

*Agents propose. Humans judge. Nurses steward.*
