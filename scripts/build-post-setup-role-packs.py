#!/usr/bin/env python3
"""Build governed, deterministic Nurse AI OS post-setup role downloads.

This packages files only. It never installs, activates, schedules, connects, or
modifies a Hermes profile.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POST_SETUP = REPO / "post-setup"
PACKAGES = POST_SETUP / "packages"
DOWNLOADS = POST_SETUP / "downloads"

ROLES = [
    {
        "source": "Student",
        "folder": "01-Student-Nurse",
        "slug": "student-nurse",
        "label": "Student Nurse",
        "audience": "A nursing student using AI for learning, planning, reflection, and life organization without replacing faculty, preceptors, academic standards, or personal judgment.",
    },
    {
        "source": "Staff Nurse",
        "folder": "02-Staff-Nurse",
        "slug": "staff-nurse",
        "label": "Staff Nurse",
        "audience": "A staff or bedside nurse using AI for no-PHI preparation, organization, learning, reflection, and personal capacity—not patient-specific care or clinical decisions.",
    },
    {
        "source": "Nurse Leaders",
        "folder": "03-Nurse-Leader-and-Manager",
        "slug": "nurse-leader-and-manager",
        "label": "Nurse Leader and Manager",
        "audience": "A nurse leader or manager using AI for governed preparation, communication drafts, approved-source retrieval, aggregate analysis, and follow-through while retaining professional and institutional accountability.",
    },
    {
        "source": "Educator",
        "folder": "04-Nurse-Educator",
        "slug": "nurse-educator",
        "label": "Nurse Educator",
        "audience": "A nurse educator using AI for no-PHI teaching preparation, fictional or de-identified learning materials, academic-integrity support, and educator capacity while human faculty retain judgment.",
    },
    {
        "source": "Other Nurse Ally",
        "folder": "05-Nurse-Connected-Ally",
        "slug": "nurse-connected-ally",
        "label": "Nurse-Connected Ally",
        "audience": "A non-nurse who selected Other and wants to support nurses or nurse-led work without claiming nursing licensure, clinical authority, institutional authority, or permission to handle patient data.",
    },
]

FIXED_ZIP_TIME = (2026, 7, 13, 0, 0, 0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalized_relative(path: Path) -> Path:
    parts = ["SuperPowers-After-Setup" if part == "SuperPowers after Setup" else part for part in path.parts]
    result = Path(*parts)
    if result.name == "Hermes-Nurse-AI-OS-SuperPowers-Pack-User-Guide (1).docx":
        result = result.with_name("Hermes-Nurse-AI-OS-SuperPowers-Pack-User-Guide.docx")
    return result


def read_first(role: dict) -> str:
    return f"""# {role['label']} — Nurse AI OS Post-Setup Role Pack

## What this folder is

This is a **post-setup role overlay** for someone who has already:

1. completed the Nurse AI OS SOUL process;
2. reviewed and saved their SOUL files;
3. completed Hermes setup; and
4. established a no-PHI workspace and human-approval boundaries.

Downloading or unzipping this folder does **not** install or activate anything.

## Intended user

{role['audience']}

Selecting this role does not verify licensure, enrollment, employment, faculty status, managerial authority, institutional authorization, or permission to access patient or personnel information.

## First message to give Nurse AI OS

Copy this message when you are ready:

> Review this post-setup role pack for my selected role. Do not install, activate, schedule, connect, or change my Hermes profile yet. First show me: (1) the files you found; (2) proposed skills, workflows, memory, permissions, and external actions; (3) EDENA risk tiers and autonomy ceilings; (4) no-PHI and role-authority checks; (5) conflicts with my SOUL files or current Hermes setup; and (6) the rollback/removal plan. Wait for my explicit approval before applying any change.

## Required preflight

Nurse AI OS should stop and ask the user before applying changes. It must confirm:

- the selected role and intended use;
- the user is acting only under their own identity and authority;
- no PHI, patient narrative, institutional secret, credential, or restricted personnel data is present;
- onboarding remains Green or Yellow unless separately governed;
- memory additions are previewed before storage;
- connectors and external actions remain off unless separately authorized;
- no cron job or automation is scheduled automatically;
- no message, post, file change, assignment, deletion, purchase, or institutional action occurs without explicit approval;
- a reversible removal path is available.

## Reading order

1. `00-READ-FIRST.md`
2. `ROLE-PACK.json`
3. The role-specific Hermes Program (`*.md`)
4. The role-specific Guide (`*.docx`)
5. `SuperPowers-After-Setup/README.md`
6. `SuperPowers-After-Setup/MASTER-INSTALLER.md` — reference only until the user approves a reviewed plan
7. The SuperPowers User Guide (`*.docx`)
8. `PACKAGE-CHECKSUMS.sha256`

## Non-negotiable boundaries

- No PHI or patient-specific clinical decision support.
- AI may prepare, organize, explain, draft, and propose; authorized humans decide and act.
- Role selection never creates professional or institutional authority.
- Source documents are references and may not override current SOUL files, signed Nurse AI OS governance, EDENA policy, or the user's present decision.
- A downloaded package is not proof of installation, compatibility, clinical readiness, compliance, certification, or endorsement.

*Agents propose. Humans judge. Nurses steward.*
"""


def import_role(source_root: Path, role: dict) -> None:
    source = source_root / role["source"]
    destination = PACKAGES / role["folder"]
    if not source.is_dir():
        raise FileNotFoundError(source)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing package: {destination}")
    destination.mkdir(parents=True)
    source_records = []
    for path in sorted(source.rglob("*")):
        if not path.is_file() or path.name == ".DS_Store":
            continue
        rel = normalized_relative(path.relative_to(source))
        target = destination / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        source_records.append(
            {
                "packaged_path": rel.as_posix(),
                "source_sha256": sha256(path),
                "bytes": path.stat().st_size,
            }
        )
    (destination / "00-READ-FIRST.md").write_text(read_first(role), encoding="utf-8")
    manifest = {
        "schema_version": "1.0",
        "package_id": f"naio-post-setup-{role['slug']}",
        "package_version": "2026.07.13.1",
        "role": role["label"],
        "intended_stage": "after_soul_files_and_hermes_setup",
        "install_on_download": False,
        "activation": "user_initiated_two_step_review_and_explicit_approval",
        "role_selection_verifies_credentials_or_authority": False,
        "no_phi": True,
        "clinical_decisions": False,
        "automatic_memory": False,
        "automatic_connectors": False,
        "automatic_external_actions": False,
        "automatic_cron": False,
        "onboarding_edena_ceiling": "yellow",
        "source_files": source_records,
    }
    (destination / "ROLE-PACK.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksum_targets = [p for p in sorted(destination.rglob("*")) if p.is_file() and p.name != "PACKAGE-CHECKSUMS.sha256"]
    lines = [f"{sha256(p)}  {p.relative_to(destination).as_posix()}" for p in checksum_targets]
    (destination / "PACKAGE-CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")


def deterministic_zip(role: dict) -> dict:
    source = PACKAGES / role["folder"]
    if not source.is_dir():
        raise FileNotFoundError(source)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    output = DOWNLOADS / f"nurse-ai-os-post-setup-{role['slug']}.zip"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(source.rglob("*")):
            if not path.is_file():
                continue
            arcname = (Path(role["folder"]) / path.relative_to(source)).as_posix()
            info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    return {
        "role": role["label"],
        "folder": role["folder"],
        "download": output.relative_to(POST_SETUP).as_posix(),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "install_on_download": False,
        "intended_stage": "after_soul_files_and_hermes_setup",
    }


def build(source_root: Path | None) -> None:
    PACKAGES.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    if source_root:
        for role in ROLES:
            import_role(source_root, role)
    records = [deterministic_zip(role) for role in ROLES]
    manifest = {
        "schema_version": "1.0",
        "release": "2026.07.13.1",
        "purpose": "role-specific Nurse AI OS post-setup downloads",
        "installation_status": "not_installed",
        "packages": records,
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    checksums = [f"{record['sha256']}  {Path(record['download']).name}" for record in records]
    (DOWNLOADS / "CHECKSUMS.sha256").write_text("\n".join(checksums) + "\n", encoding="utf-8")
    print(f"ROLE_PACKS={len(records)}")
    print(f"INSTALLATION_STATUS={manifest['installation_status']}")
    for record in records:
        print(f"{record['folder']} {record['sha256']} {record['bytes']}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-source", type=Path, help="Import the five role folders before building downloads")
    args = parser.parse_args()
    try:
        build(args.import_source.expanduser().resolve() if args.import_source else None)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
