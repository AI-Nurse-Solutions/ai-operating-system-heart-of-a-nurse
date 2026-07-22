#!/usr/bin/env python3
"""Build the tracked FUTURE public-safe source tree into a deterministic ZIP."""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

REPO = Path(__file__).resolve().parents[1]
SOURCE = REPO / "post-setup" / "build-kits" / "future-student-assistant"
DOWNLOADS = REPO / "post-setup" / "downloads"
ROOT_NAME = "FUTURE-Nursing-Student-Nursing-Assistant-Mission-Control-Hermes-Build-Kit-v1.0.0"
OUTPUT = DOWNLOADS / f"{ROOT_NAME}.zip"
FIXED_ZIP_TIME = (2026, 7, 20, 0, 0, 0)
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
EXPECTED_MEMBER_COUNT = 105
EXPECTED_VERIFIER_SHA256 = "172060eab15f32887edd75f8b0736de65c70c13c59b7b8c04059218c87ecd375"
SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE = "737968eac95347887eb55f3146c1d964541193e7843ea1f94b5bdc4e171a96c6"
SOURCE_ZIP_BYTES_BEFORE_DERIVATIVE = 6520141
EXPECTED_TARGET = {
    "home": "FUTURE Mission Control",
    "lane": "nursing_student_assistant",
    "namespace": "future.*",
    "product": "FUTURE — Nursing Student & Nursing Assistant Mission Control",
    "product_id": "future-nursing-student-assistant-mission-control",
    "readiness": "not_operational_build_required",
    "route": "/nursing-students-assistants/dashboard",
    "version": "2.0.0",
}
EXPECTED_COUNTS = {
    "acceptance_ledger_explicit_target_test_rows": 213,
    "agents": 10,
    "canonical_compatibility_checks": 136,
    "canonical_foundation_checks": 24,
    "canonical_integration_checks": 16,
    "canonical_overlay_checks": 96,
    "capability_criteria_including_capstone": 77,
    "capability_domains": 17,
    "control_matrix_rows": 169,
    "core_launchers": 4,
    "cross_cutting_full_stack_scenarios": 44,
    "mastery_levels": 4,
    "passport_domains": 6,
    "passport_stages": 5,
    "pathways": 3,
    "protected_spaces": 4,
    "superpowers": 18,
    "target_control_tests": 169,
    "templates": 5,
    "total_required_execution_records": 349,
    "total_target_full_stack_tests": 213,
    "workflows": 18,
}
EXPECTED_DEFAULTS = {
    "agents": "PERM-P0 Disabled",
    "connectors_schedules_sharing_external_actions_background_agents": "Off",
    "data": "public_synthetic_owner_authored_nonsensitive_only_after_screening",
    "memory": "session_only",
    "mode": "private_learner_os_synthetic_demonstration",
    "optional_fifth_launcher": "Empty",
    "powers": "Available Inactive",
    "workflows": "Preview Only",
}
REQUIRED_FILES = {
    ".env.example",
    "BUILD-STATUS.md",
    "GIVE-THIS-PACKAGE-TO-HERMES.md",
    "LICENSE-NOTICE.md",
    "README-FIRST.md",
    "RELEASE-MANIFEST.json",
    "SHA256SUMS.txt",
    "SOURCE-INVENTORY.json",
    "SOURCE-NOTES.md",
    "tools/verify-build-kit.py",
}


def sha256(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_files() -> dict[str, Path]:
    """Return the exact regular-file inventory under the tracked source root."""
    if not SOURCE.is_dir():
        raise FileNotFoundError(SOURCE)
    records: dict[str, Path] = {}
    normalized: set[str] = set()
    total = 0
    for path in sorted(SOURCE.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"FUTURE source symlink rejected: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(SOURCE).as_posix()
        candidate = PurePosixPath(relative)
        key = unicodedata.normalize("NFC", relative).casefold()
        if (
            not relative
            or relative.startswith("/")
            or "\\" in relative
            or "\x00" in relative
            or ".." in candidate.parts
            or any(":" in part for part in candidate.parts)
            or relative != candidate.as_posix()
            or key in normalized
        ):
            raise ValueError(f"Unsafe or colliding FUTURE source path: {relative!r}")
        if path.stat().st_size > MAX_MEMBER_BYTES:
            raise ValueError(f"FUTURE source member exceeds byte limit: {relative}")
        total += path.stat().st_size
        if total > MAX_EXPANDED_BYTES:
            raise ValueError("FUTURE source exceeds expanded byte limit")
        normalized.add(key)
        records[relative] = path
    if len(records) != EXPECTED_MEMBER_COUNT:
        raise ValueError(f"FUTURE tracked source member count mismatch: {len(records)}")
    if not REQUIRED_FILES.issubset(records):
        raise ValueError("FUTURE tracked source missing: " + ", ".join(sorted(REQUIRED_FILES - set(records))))
    return records


def parse_ledger(path: Path) -> dict[str, str]:
    """Parse a strict two-space SHA-256 ledger."""
    records: dict[str, str] = {}
    normalized: set[str] = set()
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"Invalid FUTURE checksum line {line_number}")
        relative = match.group(2)
        candidate = PurePosixPath(relative)
        key = unicodedata.normalize("NFC", relative).casefold()
        if (
            relative in records
            or key in normalized
            or relative.startswith("/")
            or "\\" in relative
            or ".." in candidate.parts
            or any(":" in part for part in candidate.parts)
            or relative != candidate.as_posix()
        ):
            raise ValueError(f"Unsafe or duplicate FUTURE checksum path: {relative!r}")
        normalized.add(key)
        records[relative] = match.group(1)
    return records


def validate_source() -> tuple[dict[str, Path], dict[str, Any]]:
    """Validate source inventory, ledgers, contract, defaults, and provenance."""
    files = source_files()
    ledger = parse_ledger(SOURCE / "SHA256SUMS.txt")
    expected_ledger = set(files) - {"SHA256SUMS.txt"}
    if set(ledger) != expected_ledger:
        raise ValueError("FUTURE checksum inventory does not match tracked source")
    mismatches = [name for name, digest in ledger.items() if sha256(files[name]) != digest]
    if mismatches:
        raise ValueError("FUTURE source checksum mismatch: " + ", ".join(sorted(mismatches)))

    manifest = json.loads((SOURCE / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))
    if manifest.get("build_kit", {}).get("version") != "1.0.0":
        raise ValueError("FUTURE build-kit version mismatch")
    if manifest.get("target") != EXPECTED_TARGET:
        raise ValueError("FUTURE target contract mismatch")
    if manifest.get("counts") != EXPECTED_COUNTS:
        raise ValueError("FUTURE count contract mismatch")
    if manifest.get("defaults") != EXPECTED_DEFAULTS:
        raise ValueError("FUTURE safe-default contract mismatch")
    derivative = manifest.get("public_safe_derivative", {})
    if derivative.get("source_zip_sha256_before_derivative") != SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE:
        raise ValueError("FUTURE source-archive provenance hash mismatch")
    if derivative.get("source_zip_bytes_before_derivative") != SOURCE_ZIP_BYTES_BEFORE_DERIVATIVE:
        raise ValueError("FUTURE source-archive provenance byte count mismatch")

    manifest_records = manifest.get("files_excluding_manifest_and_checksums")
    if not isinstance(manifest_records, list):
        raise ValueError("FUTURE manifest inventory missing")
    indexed: dict[str, dict[str, Any]] = {}
    for item in manifest_records:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise ValueError("FUTURE manifest inventory record is malformed")
        name = item["path"]
        if name in indexed:
            raise ValueError(f"FUTURE manifest inventory path is duplicated: {name}")
        indexed[name] = item
    expected_manifest = set(files) - {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}
    if set(indexed) != expected_manifest or len(indexed) != len(manifest_records):
        raise ValueError("FUTURE manifest inventory is not exact")
    bad_manifest = [
        name
        for name, item in indexed.items()
        if item.get("sha256") != sha256(files[name]) or item.get("bytes") != files[name].stat().st_size
    ]
    if bad_manifest:
        raise ValueError("FUTURE manifest hash/byte mismatch: " + ", ".join(sorted(bad_manifest)))
    if sha256(SOURCE / "tools" / "verify-build-kit.py") != EXPECTED_VERIFIER_SHA256:
        raise ValueError("FUTURE tracked verifier bytes changed")
    return files, manifest


def zip_member_mode(relative: str) -> int:
    """Return the canonical ZIP mode without consulting host checkout metadata."""
    executable = (
        relative == "tools/verify-build-kit.py"
        or relative.endswith(".sh")
        or relative.endswith(".command")
    )
    return 0o100755 if executable else 0o100644


def build(output: Path = OUTPUT) -> dict[str, Any]:
    """Build and verify the deterministic FUTURE outer ZIP."""
    files, manifest = validate_source()
    output.parent.mkdir(parents=True, exist_ok=True)
    verifier = SOURCE / "tools" / "verify-build-kit.py"
    with tempfile.TemporaryDirectory(prefix=".future-build-", dir=output.parent) as temporary:
        staging = Path(temporary)
        candidate = staging / output.name
        with zipfile.ZipFile(candidate, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for relative, path in files.items():
                info = zipfile.ZipInfo(f"{ROOT_NAME}/{relative}", FIXED_ZIP_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = zip_member_mode(relative) << 16
                archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        package = staging / ROOT_NAME
        shutil.copytree(SOURCE, package)
        completed = subprocess.run(
            [sys.executable, str(verifier), "--package", str(package), "--zip", str(candidate)],
            cwd=package,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode:
            details = (completed.stdout + completed.stderr).strip()
            raise RuntimeError("Tracked FUTURE verifier failed:\n" + details[-8000:])
        candidate.replace(output)
    return {
        "activation": "user_initiated_read_only_preflight_with_exact_implementation_activation_card",
        "build_kit_version": manifest["build_kit"]["version"],
        "bytes": output.stat().st_size,
        "ci_validation": "tracked_source_builder_and_tracked_verifier_package_and_outer_zip",
        "counts": EXPECTED_COUNTS,
        "filename": output.name,
        "member_count": len(files),
        "package_version": manifest["build_kit"]["version"],
        "root": ROOT_NAME,
        "sha256": sha256(output),
        "source_zip_bytes_before_derivative": SOURCE_ZIP_BYTES_BEFORE_DERIVATIVE,
        "source_zip_sha256_before_derivative": SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE,
        "target": EXPECTED_TARGET,
        "verifier_sha256": EXPECTED_VERIFIER_SHA256,
    }


def main() -> int:
    """Build the release ZIP and print its receipt."""
    try:
        config = build()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"FUTURE_BUILD_KIT={OUTPUT}")
    print(f"FUTURE_BUILD_KIT_BYTES={config['bytes']}")
    print(f"FUTURE_BUILD_KIT_SHA256={config['sha256']}")
    print(f"FUTURE_BUILD_KIT_MEMBERS={config['member_count']}")
    print("FUTURE_BUILD_KIT_TRACKED_VERIFIER=passed package+zip")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
