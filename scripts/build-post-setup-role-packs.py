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
    {
        "source": "Nurse Practitioner USA",
        "folder": "06-Nurse-Practitioner-USA",
        "slug": "nurse-practitioner-usa",
        "label": "Nurse Practitioner (USA)",
        "audience": "A nurse practitioner or transitioning NP using the English-language United States program after completing SOUL files and Hermes setup; selection never verifies license, certification, population focus, privileges, prescribing authority, or institutional approval.",
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
    },
]

FIXED_ZIP_TIME = (2026, 7, 13, 0, 0, 0)


def sha256(path: Path) -> str:
    """Return the SHA-256 digest for a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalized_relative(path: Path) -> Path:
    """Normalize supplied filenames while preserving role-source provenance."""
    parts = ["SuperPowers-After-Setup" if part == "SuperPowers after Setup" else part for part in path.parts]
    result = Path(*parts)
    if result.name == "Hermes-Nurse-AI-OS-SuperPowers-Pack-User-Guide (1).docx":
        result = result.with_name("Hermes-Nurse-AI-OS-SuperPowers-Pack-User-Guide.docx")
    if result.parent.name == "SuperPowers-After-Setup" and result.name == "README.md":
        result = result.with_name("REFERENCE-SUPERPOWERS-README.md")
    if result.parent.name == "SuperPowers-After-Setup" and result.name == "MASTER-INSTALLER.md":
        result = result.with_name("REFERENCE-SUPERPOWERS-MASTER-INSTALLER.md")
    return result


def reference_only_text(path: Path, text: str) -> str:
    """Mark incomplete SuperPowers documents as non-executable references."""
    if path.name not in {"REFERENCE-SUPERPOWERS-README.md", "REFERENCE-SUPERPOWERS-MASTER-INSTALLER.md"}:
        return text
    notice = (
        "> **ROLE-PACK REFERENCE NOTICE:** This source describes a larger SuperPowers distribution whose "
        "`manifest.yaml`, `core/`, `workflows/`, `templates/`, and `tests/` files were not supplied with "
        "this role pack. Do not execute its installation directives, claim the full pack is present, or "
        "invent missing modules. Use it only as design context during the review-first process in "
        "`../00-READ-FIRST.md`. The role-specific Program and Guide are the supplied post-setup materials.\n\n"
    )
    text = text.replace('status: "Implementation-ready"', 'status: "Reference-only in this role pack"', 1)
    if path.name == "REFERENCE-SUPERPOWERS-README.md":
        text = text.replace("This package contains:", "The original full SuperPowers design describes:", 1)
        text = text.replace("## Installation", "## Original full-distribution installation concept — do not execute from this role pack", 1)
        text = text.replace("## Package map", "## Original full-distribution package map — files below are not included", 1)
    if path.name == "REFERENCE-SUPERPOWERS-MASTER-INSTALLER.md":
        text = text.replace("## Master Installer and Operating Program", "## Original Full-Distribution Installer Reference — Do Not Execute", 1)
        text = text.replace("**Execution directive:**", "**Original design directive (not executable from this role pack):**", 1)
    marker = "---\n\n# Hermes"
    if marker in text:
        text = text.replace(marker, f"---\n\n{notice}# Hermes", 1)
    else:
        text = notice + text
    return text.rstrip() + "\n"


def read_first(role: dict) -> str:
    """Render the role-specific review-first and no-installation instructions."""
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
5. `SuperPowers-After-Setup/REFERENCE-SUPERPOWERS-README.md` — design reference; the full distribution is not supplied
6. `SuperPowers-After-Setup/REFERENCE-SUPERPOWERS-MASTER-INSTALLER.md` — design reference only; do not execute or invent missing modules
7. The SuperPowers User Guide (`*.docx`) — reference material
8. `PACKAGE-CHECKSUMS.sha256`

## Non-negotiable boundaries

- No PHI or patient-specific clinical decision support.
- AI may prepare, organize, explain, draft, and propose; authorized humans decide and act.
- Role selection never creates professional or institutional authority.
- Source documents are references and may not override current SOUL files, signed Nurse AI OS governance, EDENA policy, or the user's present decision.
- A downloaded package is not proof of installation, compatibility, clinical readiness, compliance, certification, or endorsement.

*Agents propose. Humans judge. Nurses steward.*
"""


def validate_role_package(destination: Path, role: dict) -> dict:
    """Fail closed unless a tracked role package preserves required boundaries."""
    manifest_path = destination / "ROLE-PACK.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("role") != role["label"]:
        raise ValueError(f"Role mismatch in {manifest_path}")
    expected_activation = role.get("activation", "user_initiated_two_step_review_and_explicit_approval")
    if manifest.get("activation") != expected_activation:
        raise ValueError(f"Unsafe activation setting in {manifest_path}")
    if manifest.get("no_phi") is not True or manifest.get("onboarding_edena_ceiling") != "yellow":
        raise ValueError(f"No-PHI or EDENA ceiling failure in {manifest_path}")
    false_keys = (
        "install_on_download",
        "role_selection_verifies_credentials_or_authority",
        "clinical_decisions",
        "automatic_memory",
        "automatic_connectors",
        "automatic_external_actions",
        "automatic_cron",
    )
    for key in false_keys:
        if manifest.get(key) is not False:
            raise ValueError(f"Unsafe {key} setting in {manifest_path}")
    if role["slug"] == "nurse-practitioner-usa":
        if manifest.get("country_availability") != ["United States"]:
            raise ValueError(f"Nurse Practitioner lane must remain USA-only: {manifest_path}")
        if manifest.get("foundation_first") is not True or manifest.get("wings_overlay_second") is not True:
            raise ValueError(f"Unsafe NP installation order in {manifest_path}")
        if manifest.get("optional_wings_active_after_install") != 0:
            raise ValueError(f"NP Wings must remain inactive after installation: {manifest_path}")
        if manifest.get("acceptance_tests") != {"foundation": 63, "np_wings": 82, "total": 145}:
            raise ValueError(f"NP acceptance-test inventory mismatch in {manifest_path}")
    for record in manifest.get("source_files", []):
        source_path = destination / record["packaged_path"]
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if role["slug"] == "nurse-practitioner-usa":
            if sha256(source_path) != record.get("source_sha256"):
                raise ValueError(f"Source checksum mismatch: {source_path}")
            if source_path.stat().st_size != record.get("bytes"):
                raise ValueError(f"Source byte-count mismatch: {source_path}")
    return manifest


def refresh_package_checksums(destination: Path) -> None:
    """Regenerate and verify the internal checksum ledger before every ZIP build."""
    targets = [p for p in sorted(destination.rglob("*")) if p.is_file() and p.name != "PACKAGE-CHECKSUMS.sha256"]
    ledger = destination / "PACKAGE-CHECKSUMS.sha256"
    lines = [f"{sha256(path)}  {path.relative_to(destination).as_posix()}" for path in targets]
    ledger.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for line in ledger.read_text(encoding="utf-8").splitlines():
        digest, rel = line.split("  ", 1)
        if sha256(destination / rel) != digest:
            raise ValueError(f"Internal checksum verification failed: {destination / rel}")


def import_role(source_root: Path, role: dict) -> None:
    """Import one authorized role source without overwriting an existing package."""
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
        if target.name.startswith("REFERENCE-SUPERPOWERS-") and target.suffix == ".md":
            target.write_text(reference_only_text(target, path.read_text(encoding="utf-8")), encoding="utf-8")
        else:
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
    validate_role_package(destination, role)
    refresh_package_checksums(destination)


def deterministic_zip(role: dict) -> dict:
    """Validate a role package, refresh its ledger, and write a deterministic ZIP."""
    source = PACKAGES / role["folder"]
    if not source.is_dir():
        raise FileNotFoundError(source)
    validate_role_package(source, role)
    refresh_package_checksums(source)
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
    role_manifest = json.loads((source / "ROLE-PACK.json").read_text(encoding="utf-8"))
    record = {
        "role": role["label"],
        "folder": role["folder"],
        "download": output.relative_to(POST_SETUP).as_posix(),
        "bytes": output.stat().st_size,
        "sha256": sha256(output),
        "install_on_download": False,
        "intended_stage": "after_soul_files_and_hermes_setup",
        "activation": role_manifest["activation"],
        "package_version": role_manifest["package_version"],
        "pre_install_disclosure_required": role_manifest.get("pre_install_disclosure_required", False),
    }
    for key in ("acceptance_tests", "country_availability", "foundation_first", "wings_overlay_second"):
        if key in role_manifest:
            record[key] = role_manifest[key]
    return record


def build(source_root: Path | None) -> None:
    """Optionally import sources, then build all governed role downloads."""
    PACKAGES.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    if source_root:
        # The USA-only NP Complete Edition is a separately governed one-file
        # package and must not be rewritten by the generic five-role importer.
        for role in (item for item in ROLES if "activation" not in item):
            import_role(source_root, role)
    records = [deterministic_zip(role) for role in ROLES]
    manifest = {
        "schema_version": "1.0",
        "release": "2026.07.14.2",
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
    """Parse command-line arguments and return a shell-friendly status code."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--import-source", type=Path, help="Import role folders before building downloads")
    args = parser.parse_args()
    try:
        build(args.import_source.expanduser().resolve() if args.import_source else None)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
