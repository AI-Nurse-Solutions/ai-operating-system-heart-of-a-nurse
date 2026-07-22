#!/usr/bin/env python3
"""Verify the tracked LEAD build-kit package and optional outer ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

EXPECTED_PACKAGE_ID = "NAIO-NL-LEAD-HERMES-BUILD-KIT-1.0.0"
EXPECTED_PACKAGE_VERSION = "1.0.0"
EXPECTED_PROGRAM_ID = "NAIO-NL-COMPLETE-LEAD-1.0"
EXPECTED_TARGET = {
    "home": "Nurse Leader Command Center",
    "lane": "nurse_leader_manager",
    "namespace": "nl_lead.*",
    "product": "Nurse Leader Complete AI OS with LEAD SuperPowers",
    "product_id": EXPECTED_PROGRAM_ID,
    "readiness": "not_operational_build_required",
    "route_assignment": "activation_card_required_no_route_preassigned",
    "version": "1.0.0",
}
EXPECTED_COUNTS = {
    "canonical_foundation_checks": 21,
    "canonical_integration_checks": 12,
    "canonical_lead_overlay_checks": 80,
    "canonical_total_checks": 113,
    "core_launchers": 4,
    "foundation_departments": 5,
    "optional_superpowers": 16,
}
EXPECTED_DEFAULTS = {
    "agents": "PERM-P0 Disabled",
    "connectors_schedules_sharing_external_actions_background_agents": "Off",
    "data": "Synthetic, public, fictional, or explicitly approved low-sensitivity only; no PHI or restricted workforce records",
    "institutional_deployment": "Unavailable until separately provisioned and authorized",
    "new_persistent_memory_categories": "Off",
    "powers": "Available Inactive",
}
EXPECTED_SOURCE_ARCHIVE = {
    "bytes": 254948,
    "filename": "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Package-v1.0.zip",
    "sha256": "1b5bcc016f56735f7d33b8ada746d971ec9ac313e5ef5339fb05382e44c0f4d8",
    "status": "user_supplied_source_archive_not_executed",
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
SOURCE_ROOT = Path("source/03-Nurse-Leader-and-Manager")
REQUIRED_FILES = {
    Path("FINAL-HANDOFF-REPORT.md"),
    Path("GIVE-THIS-PACKAGE-TO-HERMES.md"),
    Path("IMPLEMENTATION-ACTIVATION-CARD.md"),
    Path("LICENSE"),
    Path("README-FIRST.md"),
    Path("RELEASE-MANIFEST.json"),
    Path("SHA256SUMS.txt"),
    Path("SOURCE-INVENTORY.json"),
    Path("SOURCE-PROVENANCE.json"),
    Path("tools/verify-build-kit.py"),
    SOURCE_ROOT / "00-READ-FIRST.md",
    SOURCE_ROOT / "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Hermes-Program.md",
    SOURCE_ROOT / "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.md",
    SOURCE_ROOT / "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.docx",
    SOURCE_ROOT / "PACKAGE-CHECKSUMS.sha256",
    SOURCE_ROOT / "ROLE-PACK.json",
}
CHECKSUM_RE = re.compile(r"([0-9a-f]{64})  (.+)")
MAX_PACKAGE_FILE_BYTES = 16 * 1024 * 1024
MAX_PACKAGE_BYTES = 64 * 1024 * 1024


class VerificationError(RuntimeError):
    """Raised when release integrity or a safe-default contract fails."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(value: str) -> Path:
    if not value or "\\" in value or "\x00" in value:
        raise VerificationError(f"unsafe relative path: {value!r}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts or not pure.parts or any(":" in part for part in pure.parts):
        raise VerificationError(f"unsafe relative path: {value!r}")
    if value != pure.as_posix():
        raise VerificationError(f"noncanonical relative path: {value!r}")
    return Path(*pure.parts)


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise VerificationError(f"cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise VerificationError(f"JSON root must be an object: {path}")
    return value


def package_files(package: Path) -> dict[Path, Path]:
    files: dict[Path, Path] = {}
    normalized: set[str] = set()
    total = 0
    for path in sorted(package.rglob("*")):
        relative = path.relative_to(package)
        if path.is_symlink():
            raise VerificationError(f"symlink rejected: {relative.as_posix()}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise VerificationError(f"special file rejected: {relative.as_posix()}")
        size = path.stat().st_size
        if size > MAX_PACKAGE_FILE_BYTES:
            raise VerificationError(f"package file exceeds byte limit: {relative.as_posix()}")
        total += size
        if total > MAX_PACKAGE_BYTES:
            raise VerificationError("package exceeds expanded byte limit")
        safe_relative(relative.as_posix())
        folded = unicodedata.normalize("NFC", relative.as_posix()).casefold()
        if folded in normalized:
            raise VerificationError(f"case/Unicode path collision: {relative.as_posix()}")
        normalized.add(folded)
        files[relative] = path
    return files


def parse_ledger(text: str, label: str) -> dict[Path, str]:
    records: dict[Path, str] = {}
    for line_number, line in enumerate(text.splitlines(), start=1):
        match = CHECKSUM_RE.fullmatch(line)
        if not match:
            raise VerificationError(f"invalid {label} line {line_number}")
        relative = safe_relative(match.group(2))
        if relative in records:
            raise VerificationError(f"duplicate {label} path: {relative.as_posix()}")
        records[relative] = match.group(1)
    return records


def verify_source_inventory(package: Path, files: dict[Path, Path]) -> None:
    inventory = read_json(package / "SOURCE-INVENTORY.json")
    if inventory.get("schema_version") != "1.0":
        raise VerificationError("source inventory schema mismatch")
    if inventory.get("source_root") != SOURCE_ROOT.as_posix():
        raise VerificationError("source inventory root mismatch")
    if inventory.get("source_archive") != EXPECTED_SOURCE_ARCHIVE:
        raise VerificationError("source inventory archive provenance mismatch")
    records = inventory.get("files")
    if not isinstance(records, list):
        raise VerificationError("source inventory files must be a list")
    declared: dict[Path, dict] = {}
    for record in records:
        if not isinstance(record, dict):
            raise VerificationError("invalid source inventory record")
        relative = safe_relative(str(record.get("path", "")))
        if relative in declared:
            raise VerificationError(f"duplicate source inventory path: {relative.as_posix()}")
        declared[relative] = record
    expected = {
        relative.relative_to(SOURCE_ROOT)
        for relative in files
        if SOURCE_ROOT in relative.parents
    }
    if set(declared) != expected:
        raise VerificationError("source inventory does not equal packaged source files")
    for relative, record in declared.items():
        path = package / SOURCE_ROOT / relative
        if record.get("bytes") != path.stat().st_size or record.get("sha256") != sha256(path):
            raise VerificationError(f"source inventory mismatch: {relative.as_posix()}")


def verify_source_provenance(package: Path) -> None:
    provenance = read_json(package / "SOURCE-PROVENANCE.json")
    if provenance.get("schema_version") != "1.0":
        raise VerificationError("source provenance schema mismatch")
    if provenance.get("publication_model") != "tracked_source_files_wrapped_as_governed_self_install_hermes_build_kit":
        raise VerificationError("source provenance publication model mismatch")
    if provenance.get("source_archive") != EXPECTED_SOURCE_ARCHIVE:
        raise VerificationError("source archive provenance mismatch")
    source_records = provenance.get("source_files")
    if not isinstance(source_records, list) or not all(isinstance(record, dict) for record in source_records):
        raise VerificationError("source provenance must identify the three supplied files")
    declared: dict[str, dict] = {}
    for record in source_records:
        relative = safe_relative(str(record.get("path", "")))
        key = relative.as_posix()
        if key in declared:
            raise VerificationError(f"duplicate source provenance path: {key}")
        declared[key] = {"bytes": record.get("bytes"), "sha256": record.get("sha256")}
        path = package / SOURCE_ROOT / relative
        if not path.is_file():
            raise VerificationError(f"provenance source missing: {relative.as_posix()}")
        if record.get("bytes") != path.stat().st_size or record.get("sha256") != sha256(path):
            raise VerificationError(f"provenance source mismatch: {relative.as_posix()}")
    if declared != EXPECTED_SOURCE_FILES:
        raise VerificationError("supplied-source provenance hashes changed")
    if provenance.get("published_state") != "published_not_installed_not_activated_not_operational_not_institutionally_authorized":
        raise VerificationError("source provenance publication boundary mismatch")


def verify_role_package(package: Path) -> None:
    role_root = package / SOURCE_ROOT
    manifest = read_json(role_root / "ROLE-PACK.json")
    expected_fields = {
        "acceptance_tests": {"foundation": 21, "integration": 12, "lead_overlay": 80, "total": 113},
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "automatic_connectors": False,
        "automatic_cron": False,
        "automatic_external_actions": False,
        "automatic_memory": False,
        "automatic_shared_access": False,
        "clinical_decisions": False,
        "foundation_first": True,
        "install_on_download": False,
        "lead_overlay_second": True,
        "no_phi": True,
        "onboarding_edena_ceiling": "yellow",
        "optional_superpowers_active_after_install": 0,
        "optional_superpowers_total": 16,
        "organizational_deployment_requires_separate_authorization": True,
        "package_id": "naio-post-setup-nurse-leader-manager-complete-lead",
        "package_version": "2026.07.14.1",
        "pre_install_disclosure_required": True,
        "program_id": EXPECTED_PROGRAM_ID,
        "restricted_workforce_information_default": "excluded",
        "role": "Nurse Leader and Manager",
        "role_selection_verifies_credentials_or_authority": False,
        "schema_version": "1.0",
    }
    for key, expected in expected_fields.items():
        if manifest.get(key) != expected:
            raise VerificationError(f"role manifest mismatch for {key}")
    source_records = manifest.get("source_files")
    if not isinstance(source_records, list) or not all(isinstance(record, dict) for record in source_records):
        raise VerificationError("role manifest source records are malformed")
    role_sources = {
        record.get("packaged_path"): {
            "bytes": record.get("bytes"),
            "sha256": record.get("source_sha256"),
        }
        for record in source_records
    }
    if len(role_sources) != len(source_records) or role_sources != EXPECTED_SOURCE_FILES:
        raise VerificationError("role manifest supplied-source hashes changed")
    ledger = parse_ledger((role_root / "PACKAGE-CHECKSUMS.sha256").read_text(encoding="utf-8"), "role-package checksum")
    actual = {
        path.relative_to(role_root)
        for path in role_root.rglob("*")
        if path.is_file() and path.name != "PACKAGE-CHECKSUMS.sha256"
    }
    if set(ledger) != actual:
        raise VerificationError("role-package checksum inventory mismatch")
    for relative, expected in ledger.items():
        if sha256(role_root / relative) != expected:
            raise VerificationError(f"role-package checksum mismatch: {relative.as_posix()}")
    for relative, expected in EXPECTED_ROLE_WRAPPER_DIGESTS.items():
        if sha256(role_root / relative) != expected:
            raise VerificationError(f"trusted role-wrapper checksum mismatch: {relative}")


def verify_package(package: Path) -> dict:
    package = package.resolve()
    if not package.is_dir():
        raise VerificationError(f"package directory not found: {package}")
    files = package_files(package)
    missing = REQUIRED_FILES - set(files)
    if missing:
        raise VerificationError("required files missing: " + ", ".join(sorted(path.as_posix() for path in missing)))
    unexpected = set(files) - REQUIRED_FILES
    if unexpected:
        raise VerificationError("unexpected package files: " + ", ".join(sorted(path.as_posix() for path in unexpected)))

    manifest = read_json(package / "RELEASE-MANIFEST.json")
    if manifest.get("schema_version") != "1.0" or manifest.get("package_id") != EXPECTED_PACKAGE_ID:
        raise VerificationError("release identity mismatch")
    if manifest.get("package_version") != EXPECTED_PACKAGE_VERSION:
        raise VerificationError("release version mismatch")
    if manifest.get("package_root") != package.name:
        raise VerificationError("package root mismatch")
    if manifest.get("canonical_program_id") != EXPECTED_PROGRAM_ID:
        raise VerificationError("canonical program mismatch")
    if manifest.get("target") != EXPECTED_TARGET:
        raise VerificationError("target contract mismatch")
    if manifest.get("counts") != EXPECTED_COUNTS:
        raise VerificationError("count contract mismatch")
    if manifest.get("defaults") != EXPECTED_DEFAULTS:
        raise VerificationError("safe-default contract mismatch")
    if manifest.get("published_state") != "published_not_installed_not_activated_not_operational_not_institutionally_authorized":
        raise VerificationError("published-state boundary mismatch")
    if manifest.get("source_provenance") != {
        "source_archive": EXPECTED_SOURCE_ARCHIVE,
        "transformation": "wrapper_only_source_files_unchanged",
    }:
        raise VerificationError("release source-provenance contract mismatch")
    license_path = files[Path("LICENSE")]
    if license_path.stat().st_size != EXPECTED_LICENSE["bytes"] or sha256(license_path) != EXPECTED_LICENSE["sha256"]:
        raise VerificationError("tracked license mismatch")

    records = manifest.get("files")
    if not isinstance(records, list):
        raise VerificationError("release manifest files must be a list")
    declared: dict[Path, dict] = {}
    for record in records:
        if not isinstance(record, dict):
            raise VerificationError("invalid release manifest record")
        relative = safe_relative(str(record.get("path", "")))
        if relative in declared:
            raise VerificationError(f"duplicate release manifest path: {relative.as_posix()}")
        declared[relative] = record
    expected_manifest_files = set(files) - {Path("RELEASE-MANIFEST.json"), Path("SHA256SUMS.txt")}
    if set(declared) != expected_manifest_files:
        raise VerificationError("release manifest inventory mismatch")
    for relative, record in declared.items():
        path = files[relative]
        expected_mode = "0755" if relative == Path("tools/verify-build-kit.py") else "0644"
        if record.get("bytes") != path.stat().st_size or record.get("sha256") != sha256(path):
            raise VerificationError(f"release manifest mismatch: {relative.as_posix()}")
        if record.get("mode") != expected_mode:
            raise VerificationError(f"release manifest mode mismatch: {relative.as_posix()}")

    ledger = parse_ledger((package / "SHA256SUMS.txt").read_text(encoding="utf-8"), "build-kit checksum")
    expected_ledger = set(files) - {Path("SHA256SUMS.txt")}
    if set(ledger) != expected_ledger:
        raise VerificationError("build-kit checksum inventory mismatch")
    for relative, expected in ledger.items():
        if sha256(files[relative]) != expected:
            raise VerificationError(f"build-kit checksum mismatch: {relative.as_posix()}")

    verify_source_inventory(package, files)
    verify_source_provenance(package)
    verify_role_package(package)
    return manifest


def verify_zip(package: Path, archive_path: Path, manifest: dict) -> None:
    package = package.resolve()
    archive_path = archive_path.resolve()
    if not archive_path.is_file():
        raise VerificationError(f"outer ZIP not found: {archive_path}")
    package_map = {relative.as_posix(): path.read_bytes() for relative, path in package_files(package).items()}
    root = manifest["package_root"]
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise VerificationError("duplicate outer ZIP members")
        normalized = {unicodedata.normalize("NFC", name).casefold() for name in names}
        if len(normalized) != len(names):
            raise VerificationError("case/Unicode-colliding outer ZIP members")
        archive_map: dict[str, bytes] = {}
        for info in infos:
            if info.is_dir():
                raise VerificationError(f"unexpected directory member: {info.filename}")
            name = info.filename
            relative_value = name[len(root) + 1:] if name.startswith(root + "/") else ""
            relative = safe_relative(relative_value)
            mode = (info.external_attr >> 16) & 0o177777
            if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                raise VerificationError(f"symlink or special outer ZIP member: {name}")
            expected_mode = 0o100755 if relative == Path("tools/verify-build-kit.py") else 0o100644
            if mode != expected_mode:
                raise VerificationError(f"outer ZIP mode mismatch: {name}")
            if info.flag_bits & 0x1:
                raise VerificationError(f"encrypted outer ZIP member: {name}")
            relative_key = relative.as_posix()
            if relative_key not in package_map:
                raise VerificationError(f"unexpected outer ZIP member: {name}")
            if info.file_size != len(package_map[relative_key]):
                raise VerificationError(f"outer ZIP size mismatch: {name}")
            archive_map[relative_key] = archive.read(info)
        if archive.testzip() is not None:
            raise VerificationError("outer ZIP CRC failure")
    if set(archive_map) != set(package_map):
        raise VerificationError("outer ZIP inventory does not equal package directory")
    for relative, expected in package_map.items():
        if archive_map[relative] != expected:
            raise VerificationError(f"outer ZIP byte mismatch: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--zip", dest="archive", type=Path)
    args = parser.parse_args()
    try:
        manifest = verify_package(args.package)
        if args.archive:
            verify_zip(args.package, args.archive, manifest)
    except VerificationError as exc:
        print(f"LEAD_BUILD_KIT_VERIFICATION=failed reason={exc}", file=sys.stderr)
        return 1
    print(
        "LEAD_BUILD_KIT_VERIFICATION=passed "
        f"package={manifest['package_id']} checks={manifest['counts']['canonical_total_checks']} "
        f"outer_zip={'verified' if args.archive else 'not_requested'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
