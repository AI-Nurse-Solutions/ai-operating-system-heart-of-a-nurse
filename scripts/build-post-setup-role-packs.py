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
import re
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
        "source": "01-Student-Nurse",
        "folder": "01-Student-Nurse",
        "slug": "student-nurse",
        "label": "Nursing Student and Nursing Assistant",
        "audience": "A nursing student, nursing assistant, or bridge learner using a private no-PHI workspace for learning, career growth, technology fluency, life organization, and safe rehearsal without replacing faculty, preceptors, supervising nurses, supervisors, verified scope, academic rules, or personal judgment.",
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "prebuilt": True,
        "required_prebuilt_sources": (
            "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Hermes-Program.md",
            "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.md",
            "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.docx",
        ),
        "required_prebuilt_digests": {
            "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Hermes-Program.md": "6c4826e3f4c9d6decd743be1588f429ce2204ee5917989866fd408f7fd522148",
            "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.md": "f0942ba0670465a4a2a426070c802192682ba9b1b2d6ecdcd79ed8a69745b326",
            "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.docx": "6efefb44e28c70767b565d9607e71919312407454095cadb3568b6482cac9b21",
        },
        "required_prebuilt_wrapper_digests": {
            "00-READ-FIRST.md": "3e92e58bf5968eab8202d7f5aebfeacdff9720f5b1ce42082ecd667c7673a875",
            "ROLE-PACK.json": "20ca38fd696f02652193baf831be6b35fce55e955945a7b94c2263b3ab5beb49",
        },
    },
    {
        "source": "02-Staff-Nurse",
        "folder": "02-Staff-Nurse",
        "slug": "staff-nurse",
        "label": "Staff Nurse and Quality Contributor",
        "audience": "A direct-care staff nurse, unit champion, preceptor, shared-governance member, chartered staff-nurse QI project lead, or multi-employer nurse using a private no-PHI workspace for life and practice support and governed quality preparation while authorized humans and institutions retain all clinical, reporting, data, staffing, quality, research, policy, release, and employment authority.",
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "prebuilt": True,
        "required_prebuilt_sources": (
            "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Hermes-Program.md",
            "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.md",
            "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.docx",
        ),
        "required_prebuilt_digests": {
            "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Hermes-Program.md": "6fa391b8000d7b5c0e6a922b9ed61446143d6b1ddf70c88950a8171a9176b828",
            "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.md": "1d23c026f251b2826b839f5b65f64a1ea59988d014ff9c8e44f079a9eb38e86d",
            "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.docx": "f8e4381fafaeec746663dc8ebc18c707369ed5c1591537890c5004659d73a0ec",
        },
        "required_prebuilt_wrapper_digests": {
            "00-READ-FIRST.md": "f56d0802cabfac2468458891c8969af2874e8332108bb3fff08927231d421682",
            "ROLE-PACK.json": "d82606ed0a12adfa85464902545840c4b30724166517b4bc91e19a4b90e5cb0c",
        },
    },
    {
        "source": "Nurse Leaders",
        "folder": "03-Nurse-Leader-and-Manager",
        "slug": "nurse-leader-and-manager",
        "label": "Nurse Leader and Manager",
        "audience": "A nurse leader or manager using AI for governed preparation, communication drafts, approved-source retrieval, aggregate analysis, and follow-through while retaining professional and institutional accountability.",
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "prebuilt": True,
        "required_prebuilt_sources": (
            "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Hermes-Program.md",
            "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.md",
            "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.docx",
        ),
        "required_prebuilt_digests": {
            "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Hermes-Program.md": "5ac88fdc530c23b7b1b72cb1eefa4d41cf4bfc2996cd383dfff1867315893a08",
            "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.md": "79503858ae693d7b4a2f5961e50ffcef5e1f7c3c63af35db156d0a127ee40cc3",
            "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.docx": "fc44cf7e636a354d836b44dc924d4710341afcff9fe937458383d0d9a835cfe7",
        },
        "required_prebuilt_wrapper_digests": {
            "00-READ-FIRST.md": "07ceddf57630c6ad931ac6fff3638f77e3dd7bf9f3e1e7f80468829e71d1e2e6",
            "ROLE-PACK.json": "f25e93648e5450d05feb318552e72501d699dd54308cde46d01eb59b348bc91c",
        },
    },
    {
        "source": "04-Nurse-Educator",
        "folder": "04-Nurse-Educator",
        "slug": "nurse-educator",
        "label": "Nurse Educator and Instructional Designer",
        "audience": "A nurse educator, instructional designer, or hybrid/faculty developer using a private no-PHI and no-student-record workspace for governed teaching and design preparation while authorized humans retain grading, clinical, academic-integrity, accommodation, curriculum, accreditation, research, release, and institutional authority.",
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "prebuilt": True,
        "required_prebuilt_sources": (
            "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Hermes-Program.md",
            "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.md",
            "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.docx",
        ),
        "required_prebuilt_digests": {
            "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Hermes-Program.md": "c34aee05bdad5cc2d56f3b6e0268e1e2c45e1584be3efc15133b6042cdab9cc7",
            "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.md": "b3c0a088f0fd72db372ac176a4bbf31082297a13249d85525cbbe1eebddd7294",
            "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.docx": "12a1176b4c08cbab842204d9c24228e76809383a16c05b02817273e45b526e16",
        },
        "required_prebuilt_wrapper_digests": {
            "00-READ-FIRST.md": "f1a2cb2c6339eac2a14c4e76f42430bca7d705a7388fed1562a4776a9c121513",
            "ROLE-PACK.json": "976e0db91b193bacfc0fc28944dec4b106c8bf4df59ac2c2dabda4ddd47f951d",
        },
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
        "prebuilt": True,
        "required_prebuilt_sources": (
            "NP-Complete-AI-OS-with-Wings-Hermes-Program.md",
            "NP-Complete-AI-OS-with-Wings-Setup-Guide.md",
            "NP-Complete-AI-OS-with-Wings-Setup-Guide.docx",
        ),
        "required_prebuilt_digests": {
            "NP-Complete-AI-OS-with-Wings-Hermes-Program.md": "46734b8ecb72e4fa8dc58f4b03ba4cc7db9e15b4eae4db9d7a7eaf4879cd5e30",
            "NP-Complete-AI-OS-with-Wings-Setup-Guide.md": "6ea5ebd1fec5303ff8479f94c19435d9d3a89b7c7fc57d513a4305a3a6776f37",
            "NP-Complete-AI-OS-with-Wings-Setup-Guide.docx": "430f6c3fe5046202cc7de3df2edbb594b20dc62931f5645bce22787cf4644ecb",
        },
        "required_prebuilt_wrapper_digests": {
            "00-READ-FIRST.md": "525b5fee48fe4a4af0d4e0ffce14628ca98ce5c2e6633416cc77d63e0a442158",
            "ROLE-PACK.json": "234ec9548c9f7cc9f02b80f6c074fae3ffebd89ba9200494631e743edcefc320",
        },
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
    if role["slug"] == "student-nurse":
        if manifest.get("pathways") != ["Nursing Student", "Nursing Assistant", "Bridge"]:
            raise ValueError(f"Student/Assistant pathway inventory mismatch in {manifest_path}")
        if manifest.get("foundation_first") is not True or manifest.get("future_overlay_second") is not True:
            raise ValueError(f"Unsafe Student/Assistant installation order in {manifest_path}")
        if manifest.get("optional_superpowers_total") != 18:
            raise ValueError(f"Student/Assistant SuperPowers inventory mismatch in {manifest_path}")
        if manifest.get("optional_superpowers_active_after_install") != 0:
            raise ValueError(f"Student/Assistant SuperPowers must remain inactive after installation: {manifest_path}")
        if manifest.get("automatic_shared_access") is not False:
            raise ValueError(f"Student/Assistant shared access must remain off: {manifest_path}")
        if manifest.get("bridge_context_transfer_automatic") is not False:
            raise ValueError(f"Bridge context transfer must remain off: {manifest_path}")
        if manifest.get("organizational_deployment_requires_separate_authorization") is not True:
            raise ValueError(f"Student/Assistant deployment boundary missing: {manifest_path}")
        if manifest.get("acceptance_tests") != {
            "foundation": 24,
            "future_overlay": 96,
            "integration": 16,
            "total": 136,
        }:
            raise ValueError(f"Student/Assistant release-check inventory mismatch in {manifest_path}")
    if role["slug"] == "staff-nurse":
        if manifest.get("foundation_first") is not True or manifest.get("shift_overlay_second") is not True:
            raise ValueError(f"Unsafe Staff Nurse installation order in {manifest_path}")
        if manifest.get("optional_superpowers_total") != 20:
            raise ValueError(f"SHIFT SuperPower inventory mismatch in {manifest_path}")
        if manifest.get("optional_superpowers_active_after_install") != 0:
            raise ValueError(f"SHIFT SuperPowers must remain inactive after installation: {manifest_path}")
        if manifest.get("automatic_shared_access") is not False:
            raise ValueError(f"Staff Nurse shared access must remain off: {manifest_path}")
        if manifest.get("institutional_deployment_requires_separate_authorization") is not True:
            raise ValueError(f"Staff Nurse institutional-deployment boundary missing: {manifest_path}")
        if manifest.get("role_adapters") != [
            "Direct-Care Staff Nurse",
            "Unit Champion / Preceptor / Shared-Governance Member",
            "Chartered Staff-Nurse QI Project Lead",
            "Hybrid / Multiple-Employer",
        ]:
            raise ValueError(f"Staff Nurse role-adapter inventory mismatch in {manifest_path}")
        if manifest.get("acceptance_tests") != {
            "foundation": 40,
            "integration": 16,
            "shift_overlay": 120,
            "total": 176,
        }:
            raise ValueError(f"Staff Nurse release-check inventory mismatch in {manifest_path}")
    if role["slug"] == "nurse-practitioner-usa":
        if manifest.get("country_availability") != ["United States"]:
            raise ValueError(f"Nurse Practitioner lane must remain USA-only: {manifest_path}")
        if manifest.get("foundation_first") is not True or manifest.get("wings_overlay_second") is not True:
            raise ValueError(f"Unsafe NP installation order in {manifest_path}")
        if manifest.get("optional_wings_active_after_install") != 0:
            raise ValueError(f"NP Wings must remain inactive after installation: {manifest_path}")
        if manifest.get("acceptance_tests") != {"foundation": 63, "np_wings": 82, "total": 145}:
            raise ValueError(f"NP acceptance-test inventory mismatch in {manifest_path}")
    if role["slug"] == "nurse-educator":
        if manifest.get("foundation_first") is not True or manifest.get("teach_overlay_second") is not True:
            raise ValueError(f"Unsafe educator installation order in {manifest_path}")
        if manifest.get("optional_superpowers_active_after_install") != 0:
            raise ValueError(f"TEACH SuperPowers must remain inactive after installation: {manifest_path}")
        if manifest.get("optional_superpowers_total") != 20:
            raise ValueError(f"TEACH SuperPower inventory mismatch in {manifest_path}")
        if manifest.get("role_adapters") != [
            "Nurse Educator",
            "Instructional Designer",
            "Hybrid / Faculty Developer",
        ]:
            raise ValueError(f"Educator role-adapter inventory mismatch in {manifest_path}")
        if manifest.get("institutional_deployment_requires_separate_authorization") is not True:
            raise ValueError(f"Educator institutional-deployment boundary missing: {manifest_path}")
        if manifest.get("automatic_shared_access") is not False:
            raise ValueError(f"Educator shared access must remain off: {manifest_path}")
        if manifest.get("acceptance_tests") != {
            "foundation": 33,
            "teach_overlay": 120,
            "integration": 16,
            "total": 169,
        }:
            raise ValueError(f"Educator release-check inventory mismatch in {manifest_path}")
    if role["slug"] == "nurse-leader-and-manager":
        if manifest.get("foundation_first") is not True or manifest.get("lead_overlay_second") is not True:
            raise ValueError(f"Unsafe Nurse Leader installation order in {manifest_path}")
        if manifest.get("optional_superpowers_total") != 16:
            raise ValueError(f"Nurse Leader SuperPowers inventory mismatch in {manifest_path}")
        if manifest.get("optional_superpowers_active_after_install") != 0:
            raise ValueError(f"Nurse Leader SuperPowers must remain inactive after installation: {manifest_path}")
        if manifest.get("automatic_shared_access") is not False:
            raise ValueError(f"Nurse Leader shared access must remain off: {manifest_path}")
        if manifest.get("organizational_deployment_requires_separate_authorization") is not True:
            raise ValueError(f"Nurse Leader organizational deployment boundary missing: {manifest_path}")
        if manifest.get("acceptance_tests") != {
            "foundation": 21,
            "integration": 12,
            "lead_overlay": 80,
            "total": 113,
        }:
            raise ValueError(f"Nurse Leader release-check inventory mismatch in {manifest_path}")
    for record in manifest.get("source_files", []):
        source_path = destination / record["packaged_path"]
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        if role.get("prebuilt"):
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


def validate_prebuilt_inventory(package: Path, role: dict) -> None:
    """Fail closed unless a prebuilt package has exactly its governed inventory."""
    validate_role_package(package, role)
    manifest = json.loads((package / "ROLE-PACK.json").read_text(encoding="utf-8"))
    pinned_sources = {Path(path) for path in role["required_prebuilt_sources"]}
    declared_sources = [Path(record.get("packaged_path", "")) for record in manifest.get("source_files", [])]
    if len(declared_sources) != len(set(declared_sources)) or set(declared_sources) != pinned_sources:
        raise ValueError(
            f"Pinned source inventory mismatch for {role['folder']}; "
            f"required: {', '.join(sorted(path.as_posix() for path in pinned_sources))}; "
            f"declared: {', '.join(sorted(path.as_posix() for path in declared_sources))}"
        )
    pinned_digests = {Path(path): digest for path, digest in role["required_prebuilt_digests"].items()}
    if set(pinned_digests) != pinned_sources:
        raise ValueError(f"Trusted digest configuration mismatch for {role['folder']}")
    declared_digests = {
        Path(record["packaged_path"]): record.get("source_sha256")
        for record in manifest.get("source_files", [])
    }
    for path, expected_digest in pinned_digests.items():
        if declared_digests.get(path) != expected_digest or sha256(package / path) != expected_digest:
            raise ValueError(f"Trusted source checksum mismatch: {package / path}")
    wrapper_digests = {
        Path(path): digest for path, digest in role["required_prebuilt_wrapper_digests"].items()
    }
    if set(wrapper_digests) != {Path("00-READ-FIRST.md"), Path("ROLE-PACK.json")}:
        raise ValueError(f"Trusted wrapper configuration mismatch for {role['folder']}")
    for path, expected_digest in wrapper_digests.items():
        if sha256(package / path) != expected_digest:
            raise ValueError(f"Trusted wrapper checksum mismatch: {package / path}")
    expected_files = {
        Path("00-READ-FIRST.md"),
        Path("PACKAGE-CHECKSUMS.sha256"),
        Path("ROLE-PACK.json"),
    }
    expected_files.update(pinned_sources)
    expected_dirs = {
        parent
        for path in expected_files
        for parent in path.parents
        if parent != Path(".")
    }
    actual_files = {
        path.relative_to(package)
        for path in package.rglob("*")
        if path.is_file()
    }
    actual_dirs = {
        path.relative_to(package)
        for path in package.rglob("*")
        if path.is_dir()
    }
    symlinks = {
        path.relative_to(package)
        for path in package.rglob("*")
        if path.is_symlink()
    }
    missing = expected_files - actual_files
    unexpected = actual_files - expected_files
    unexpected_dirs = actual_dirs - expected_dirs
    if missing or unexpected or unexpected_dirs or symlinks:
        details = []
        for label, paths in (
            ("missing files", missing),
            ("unexpected files", unexpected),
            ("unexpected directories", unexpected_dirs),
            ("symlinks", symlinks),
        ):
            if paths:
                details.append(f"{label}: {', '.join(sorted(path.as_posix() for path in paths))}")
        raise ValueError(
            f"Prebuilt package inventory mismatch for {role['folder']}; " + "; ".join(details)
        )

    ledger_path = package / "PACKAGE-CHECKSUMS.sha256"
    ledger_records: dict[Path, str] = {}
    for line_number, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(
                f"Invalid checksum ledger line for {role['folder']} at line {line_number}"
            )
        relative = Path(match.group(2))
        if relative.is_absolute() or ".." in relative.parts or "\\" in match.group(2):
            raise ValueError(
                f"Unsafe checksum ledger path for {role['folder']}: {match.group(2)}"
            )
        if relative in ledger_records:
            raise ValueError(
                f"Duplicate checksum ledger path for {role['folder']}: {relative.as_posix()}"
            )
        ledger_records[relative] = match.group(1)

    expected_ledger_files = expected_files - {Path("PACKAGE-CHECKSUMS.sha256")}
    if set(ledger_records) != expected_ledger_files:
        raise ValueError(f"Checksum ledger inventory mismatch for {role['folder']}")
    mismatches = [
        relative
        for relative, expected_hash in ledger_records.items()
        if sha256(package / relative) != expected_hash
    ]
    if mismatches:
        raise ValueError(
            f"Checksum mismatch for {role['folder']}: "
            + ", ".join(sorted(path.as_posix() for path in mismatches))
        )


def import_prebuilt_role(source_root: Path, role: dict) -> None:
    """Import an exact separately governed package without rewriting it."""
    source = source_root / role["folder"]
    destination = PACKAGES / role["folder"]
    if not source.is_dir():
        raise FileNotFoundError(source)
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing package: {destination}")
    validate_prebuilt_inventory(source, role)
    shutil.copytree(source, destination)
    validate_prebuilt_inventory(destination, role)
    refresh_package_checksums(destination)


def deterministic_zip(role: dict) -> dict:
    """Validate a role package, refresh its ledger, and write a deterministic ZIP."""
    source = PACKAGES / role["folder"]
    if not source.is_dir():
        raise FileNotFoundError(source)
    if role.get("prebuilt"):
        validate_prebuilt_inventory(source, role)
    else:
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
    for key in (
        "acceptance_tests",
        "country_availability",
        "foundation_first",
        "future_overlay_second",
        "lead_overlay_second",
        "teach_overlay_second",
        "wings_overlay_second",
        "pathways",
        "role_adapters",
        "bridge_context_transfer_automatic",
        "automatic_shared_access",
        "optional_superpowers_total",
        "optional_superpowers_active_after_install",
        "organizational_deployment_requires_separate_authorization",
        "institutional_deployment_requires_separate_authorization",
    ):
        if key in role_manifest:
            record[key] = role_manifest[key]
    return record


def build(source_root: Path | None) -> None:
    """Optionally import sources, then build all governed role downloads."""
    PACKAGES.mkdir(parents=True, exist_ok=True)
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    if source_root:
        # Complete Editions are separately governed one-file packages and must
        # be imported intact, not rewritten by the generic review-pack importer.
        generic_roles = [item for item in ROLES if not item.get("prebuilt")]
        prebuilt_roles = [item for item in ROLES if item.get("prebuilt")]
        required_sources = [source_root / role["source"] for role in generic_roles]
        required_sources.extend(source_root / role["folder"] for role in prebuilt_roles)
        missing = [path for path in required_sources if not path.is_dir()]
        if missing:
            raise FileNotFoundError("Import source is incomplete; missing: " + ", ".join(str(path) for path in missing))
        conflicts = [PACKAGES / role["folder"] for role in ROLES if (PACKAGES / role["folder"]).exists()]
        if conflicts:
            raise FileExistsError("Refusing partial import; package destinations already exist: " + ", ".join(str(path) for path in conflicts))
        # Validate every immutable Complete Edition before any generic importer
        # can create a destination. A bad prebuilt source must leave no partial
        # package tree behind and must be safe to correct and retry.
        for role in prebuilt_roles:
            validate_prebuilt_inventory(source_root / role["folder"], role)
        for role in generic_roles:
            import_role(source_root, role)
        for role in prebuilt_roles:
            import_prebuilt_role(source_root, role)
    records = [deterministic_zip(role) for role in ROLES]
    manifest = {
        "schema_version": "1.0",
        "release": "2026.07.15.5",
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
    parser.add_argument(
        "--import-source",
        type=Path,
        help=(
            "Import the review-first lane-05 source plus prebuilt 01-Student-Nurse, "
            "02-Staff-Nurse, 03-Nurse-Leader-and-Manager, 04-Nurse-Educator, and "
            "06-Nurse-Practitioner-USA folders before building"
        ),
    )
    args = parser.parse_args()
    try:
        build(args.import_source.expanduser().resolve() if args.import_source else None)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
