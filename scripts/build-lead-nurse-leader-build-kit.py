#!/usr/bin/env python3
"""Build the tracked LEAD Nurse Leader governed self-install Hermes build kit."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
POST_SETUP = REPO / "post-setup"
TEMPLATE = POST_SETUP / "build-kits" / "lead-nurse-leader"
SOURCE = POST_SETUP / "packages" / "03-Nurse-Leader-and-Manager"
DOWNLOADS = POST_SETUP / "downloads"
ROOT_NAME = "LEAD-Nurse-Leader-Manager-Mission-Control-Hermes-Build-Kit-v1.0.0"
FILENAME = ROOT_NAME + ".zip"
OUTPUT = DOWNLOADS / FILENAME
LICENSE_SOURCE = REPO / "LICENSE"
FIXED_ZIP_TIME = (2026, 7, 21, 0, 0, 0)
STATIC_FILES = (
    Path("FINAL-HANDOFF-REPORT.md"),
    Path("GIVE-THIS-PACKAGE-TO-HERMES.md"),
    Path("IMPLEMENTATION-ACTIVATION-CARD.md"),
    Path("README-FIRST.md"),
    Path("SOURCE-PROVENANCE.json"),
    Path("tools/verify-build-kit.py"),
)
TARGET = {
    "home": "Nurse Leader Command Center",
    "lane": "nurse_leader_manager",
    "namespace": "nl_lead.*",
    "product": "Nurse Leader Complete AI OS with LEAD SuperPowers",
    "product_id": "NAIO-NL-COMPLETE-LEAD-1.0",
    "readiness": "not_operational_build_required",
    "route_assignment": "activation_card_required_no_route_preassigned",
    "version": "1.0.0",
}
COUNTS = {
    "canonical_foundation_checks": 21,
    "canonical_integration_checks": 12,
    "canonical_lead_overlay_checks": 80,
    "canonical_total_checks": 113,
    "core_launchers": 4,
    "foundation_departments": 5,
    "optional_superpowers": 16,
}
DEFAULTS = {
    "agents": "PERM-P0 Disabled",
    "connectors_schedules_sharing_external_actions_background_agents": "Off",
    "data": "Synthetic, public, fictional, or explicitly approved low-sensitivity only; no PHI or restricted workforce records",
    "institutional_deployment": "Unavailable until separately provisioned and authorized",
    "new_persistent_memory_categories": "Off",
    "powers": "Available Inactive",
}
EXPECTED_ROLE_FILES = {
    "00-READ-FIRST.md",
    "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Hermes-Program.md",
    "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.docx",
    "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.md",
    "PACKAGE-CHECKSUMS.sha256",
    "ROLE-PACK.json",
}
EXPECTED_SOURCE_FILES = {
    "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Hermes-Program.md": {
        "bytes": 215044,
        "sha256": "5ac88fdc530c23b7b1b72cb1eefa4d41cf4bfc2996cd383dfff1867315893a08",
    },
    "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.docx": {
        "bytes": 183332,
        "sha256": "fc44cf7e636a354d836b44dc924d4710341afcff9fe937458383d0d9a835cfe7",
    },
    "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.md": {
        "bytes": 19054,
        "sha256": "79503858ae693d7b4a2f5961e50ffcef5e1f7c3c63af35db156d0a127ee40cc3",
    },
}
EXPECTED_ROLE_WRAPPER_DIGESTS = {
    "00-READ-FIRST.md": "07ceddf57630c6ad931ac6fff3638f77e3dd7bf9f3e1e7f80468829e71d1e2e6",
    "ROLE-PACK.json": "f25e93648e5450d05feb318552e72501d699dd54308cde46d01eb59b348bc91c",
}
EXPECTED_LICENSE = {
    "bytes": 11358,
    "sha256": "c95bae1d1ce0235ecccd3560b772ec1efb97f348a79f0fbe0a634f0c2ccefe2c",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_ledger(path: Path) -> dict[str, str]:
    records: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            digest, relative = line.split("  ", 1)
        except ValueError as exc:
            raise ValueError(f"Malformed checksum line in {path}: {line!r}") from exc
        if len(digest) != 64 or any(character not in "0123456789abcdef" for character in digest):
            raise ValueError(f"Malformed checksum digest in {path}: {digest!r}")
        if relative in records:
            raise ValueError(f"Duplicate checksum path in {path}: {relative}")
        records[relative] = digest
    return records


def verify_role_package(provenance: dict) -> None:
    if not SOURCE.is_dir() or SOURCE.is_symlink():
        raise ValueError(f"Missing or unsafe LEAD role package: {SOURCE}")
    for path in SOURCE.rglob("*"):
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"Unsupported LEAD role-package entry: {path}")
    actual = {path.name for path in SOURCE.iterdir() if path.is_file()}
    if actual != EXPECTED_ROLE_FILES:
        raise ValueError(f"LEAD role-package inventory mismatch: {sorted(actual ^ EXPECTED_ROLE_FILES)}")

    manifest = json.loads((SOURCE / "ROLE-PACK.json").read_text(encoding="utf-8"))
    expected_fields = {
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "foundation_first": True,
        "install_on_download": False,
        "lead_overlay_second": True,
        "no_phi": True,
        "optional_superpowers_active_after_install": 0,
        "optional_superpowers_total": 16,
        "organizational_deployment_requires_separate_authorization": True,
        "package_id": "naio-post-setup-nurse-leader-manager-complete-lead",
        "program_id": "NAIO-NL-COMPLETE-LEAD-1.0",
        "role": "Nurse Leader and Manager",
        "role_selection_verifies_credentials_or_authority": False,
    }
    for key, expected in expected_fields.items():
        if manifest.get(key) != expected:
            raise ValueError(f"LEAD role manifest mismatch for {key}: {manifest.get(key)!r}")
    if manifest.get("acceptance_tests") != {
        "foundation": 21,
        "integration": 12,
        "lead_overlay": 80,
        "total": 113,
    }:
        raise ValueError("LEAD role manifest acceptance-test inventory changed")
    for key in (
        "automatic_connectors",
        "automatic_cron",
        "automatic_external_actions",
        "automatic_memory",
        "automatic_shared_access",
        "clinical_decisions",
    ):
        if manifest.get(key) is not False:
            raise ValueError(f"LEAD role manifest safe default changed: {key}")

    source_records = provenance.get("source_files", [])
    if not isinstance(source_records, list) or not all(isinstance(record, dict) for record in source_records):
        raise ValueError("LEAD supplied-source provenance records are malformed")
    supplied = {
        record.get("path"): {"bytes": record.get("bytes"), "sha256": record.get("sha256")}
        for record in source_records
    }
    if len(supplied) != len(source_records) or supplied != EXPECTED_SOURCE_FILES:
        raise ValueError("LEAD supplied-source provenance hashes changed")
    role_source_records = manifest.get("source_files", [])
    if not isinstance(role_source_records, list) or not all(isinstance(record, dict) for record in role_source_records):
        raise ValueError("LEAD role manifest source records are malformed")
    role_sources = {record.get("packaged_path"): record for record in role_source_records}
    if len(role_sources) != len(role_source_records):
        raise ValueError("LEAD role manifest contains duplicate source records")
    if set(supplied) != set(role_sources):
        raise ValueError("LEAD role manifest source inventory differs from supplied-source provenance")
    for relative, source_record in supplied.items():
        role_record = role_sources[relative]
        if role_record.get("bytes") != source_record["bytes"] or role_record.get("source_sha256") != source_record["sha256"]:
            raise ValueError(f"LEAD role manifest source provenance mismatch: {relative}")
        path = SOURCE / relative
        if path.stat().st_size != source_record["bytes"] or sha256(path) != source_record["sha256"]:
            raise ValueError(f"LEAD immutable source mismatch: {path}")

    ledger = parse_ledger(SOURCE / "PACKAGE-CHECKSUMS.sha256")
    expected_ledger_paths = EXPECTED_ROLE_FILES - {"PACKAGE-CHECKSUMS.sha256"}
    if set(ledger) != expected_ledger_paths:
        raise ValueError("LEAD role-package checksum inventory mismatch")
    for relative, digest in ledger.items():
        if sha256(SOURCE / relative) != digest:
            raise ValueError(f"LEAD role-package checksum mismatch: {relative}")
    for relative, digest in EXPECTED_ROLE_WRAPPER_DIGESTS.items():
        if sha256(SOURCE / relative) != digest:
            raise ValueError(f"LEAD trusted wrapper checksum mismatch: {relative}")


def copy_inputs(stage: Path) -> None:
    for relative in STATIC_FILES:
        source = TEMPLATE / relative
        if not source.is_file() or source.is_symlink():
            raise ValueError(f"Missing or unsafe LEAD build-kit template: {source}")
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    if (
        not LICENSE_SOURCE.is_file()
        or LICENSE_SOURCE.is_symlink()
        or LICENSE_SOURCE.stat().st_size != EXPECTED_LICENSE["bytes"]
        or sha256(LICENSE_SOURCE) != EXPECTED_LICENSE["sha256"]
    ):
        raise ValueError("Tracked repository license changed")
    shutil.copyfile(LICENSE_SOURCE, stage / "LICENSE")
    source_target = stage / "source" / SOURCE.name
    shutil.copytree(SOURCE, source_target, copy_function=shutil.copyfile)
    for path in stage.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"Symlink rejected in LEAD build-kit source: {path}")
        if path.is_file():
            path.chmod(0o755 if path.relative_to(stage) == Path("tools/verify-build-kit.py") else 0o644)


def source_inventory(stage: Path, provenance: dict) -> dict:
    root = stage / "source" / SOURCE.name
    files = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            files.append(
                {
                    "bytes": path.stat().st_size,
                    "path": path.relative_to(root).as_posix(),
                    "sha256": sha256(path),
                }
            )
    return {
        "schema_version": "1.0",
        "source_archive": provenance["source_archive"],
        "source_root": f"source/{SOURCE.name}",
        "files": files,
    }


def release_inventory(stage: Path) -> list[dict]:
    records = []
    for path in sorted(stage.rglob("*")):
        if not path.is_file() or path.name in {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}:
            continue
        relative = path.relative_to(stage)
        records.append(
            {
                "bytes": path.stat().st_size,
                "mode": "0755" if relative == Path("tools/verify-build-kit.py") else "0644",
                "path": relative.as_posix(),
                "sha256": sha256(path),
            }
        )
    return records


def write_ledger(stage: Path) -> None:
    paths = [
        path
        for path in sorted(stage.rglob("*"))
        if path.is_file() and path.name != "SHA256SUMS.txt"
    ]
    text = "\n".join(f"{sha256(path)}  {path.relative_to(stage).as_posix()}" for path in paths) + "\n"
    (stage / "SHA256SUMS.txt").write_text(text, encoding="utf-8")
    (stage / "SHA256SUMS.txt").chmod(0o644)


def deterministic_zip(stage: Path) -> None:
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_STORED) as archive:
        for path in sorted(stage.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(stage)
            info = zipfile.ZipInfo(f"{ROOT_NAME}/{relative.as_posix()}", FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_STORED
            info.create_system = 3
            info.external_attr = (0o100755 if relative == Path("tools/verify-build-kit.py") else 0o100644) << 16
            archive.writestr(info, path.read_bytes())


def build() -> dict:
    provenance = json.loads((TEMPLATE / "SOURCE-PROVENANCE.json").read_text(encoding="utf-8"))
    if provenance.get("source_archive") != {
        "bytes": 254948,
        "filename": "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Package-v1.0.zip",
        "sha256": "1b5bcc016f56735f7d33b8ada746d971ec9ac313e5ef5339fb05382e44c0f4d8",
        "status": "user_supplied_source_archive_not_executed",
    }:
        raise ValueError("LEAD source archive provenance changed")
    source_records = provenance.get("source_files", [])
    if not isinstance(source_records, list) or not all(isinstance(record, dict) for record in source_records):
        raise ValueError("LEAD supplied-source provenance records are malformed")
    pinned_sources = {
        record.get("path"): {"bytes": record.get("bytes"), "sha256": record.get("sha256")}
        for record in source_records
    }
    if len(pinned_sources) != len(source_records) or pinned_sources != EXPECTED_SOURCE_FILES:
        raise ValueError("LEAD supplied-source provenance hashes changed")
    verify_role_package(provenance)

    with tempfile.TemporaryDirectory(prefix="lead-build-kit-") as temporary:
        stage = Path(temporary) / ROOT_NAME
        stage.mkdir()
        copy_inputs(stage)
        write_json(stage / "SOURCE-INVENTORY.json", source_inventory(stage, provenance))
        manifest = {
            "canonical_program_id": "NAIO-NL-COMPLETE-LEAD-1.0",
            "counts": COUNTS,
            "defaults": DEFAULTS,
            "files": release_inventory(stage),
            "package_id": "NAIO-NL-LEAD-HERMES-BUILD-KIT-1.0.0",
            "package_root": ROOT_NAME,
            "package_version": "1.0.0",
            "published_state": "published_not_installed_not_activated_not_operational_not_institutionally_authorized",
            "schema_version": "1.0",
            "source_provenance": {
                "source_archive": provenance["source_archive"],
                "transformation": "wrapper_only_source_files_unchanged",
            },
            "target": TARGET,
        }
        write_json(stage / "RELEASE-MANIFEST.json", manifest)
        write_ledger(stage)
        deterministic_zip(stage)
        verifier = TEMPLATE / "tools" / "verify-build-kit.py"
        subprocess.run(
            [sys.executable, str(verifier), "--package", str(stage), "--zip", str(OUTPUT)],
            check=True,
        )
        member_count = len([path for path in stage.rglob("*") if path.is_file()])

    config = {
        "build_kit_version": "1.0.0",
        "bytes": OUTPUT.stat().st_size,
        "counts": COUNTS,
        "filename": FILENAME,
        "member_count": member_count,
        "root": ROOT_NAME,
        "sha256": sha256(OUTPUT),
        "source_zip_bytes": provenance["source_archive"]["bytes"],
        "source_zip_sha256": provenance["source_archive"]["sha256"],
        "target": TARGET,
        "verifier_sha256": sha256(TEMPLATE / "tools" / "verify-build-kit.py"),
    }
    print(
        "LEAD_BUILD_KIT_BUILT "
        f"bytes={config['bytes']} sha256={config['sha256']} members={config['member_count']} "
        f"verifier_sha256={config['verifier_sha256']}"
    )
    return config


def main() -> int:
    try:
        build()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
