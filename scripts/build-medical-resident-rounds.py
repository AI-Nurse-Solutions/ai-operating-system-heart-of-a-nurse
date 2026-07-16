#!/usr/bin/env python3
"""Build the standalone, deterministic ROUNDS Medical Resident release.

This script packages files only. It never installs ROUNDS, modifies a Hermes
profile, enables memory, connects a system, schedules work, or performs a
clinical or external action.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "medical-residents"
PACKAGE = ROOT / "packages" / "rounds"
DOWNLOADS = ROOT / "downloads"
ZIP_NAME = "medical-resident-rounds-complete-edition.zip"
ZIP_PREFIX = "ROUNDS-Medical-Resident-Complete-Edition"
FIXED_ZIP_TIME = (2026, 7, 16, 0, 0, 0)

SOURCE_DIGESTS = {
    "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Hermes-Program.md": "33a8e8dbd963bb21d21582d520f3d98c161ed7b900a9cdfa7a13df1039da365c",
    "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.md": "bff68f996a605dc71c92609b6e20d4d5e1a1a95a24b92c84c3dfad7f746bc0f9",
    "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.docx": "a0c4483ca3b51d0597db52b8c32c5dcc93e9916ae2374277b1962f1832f50d4b",
}
WRAPPER_DIGESTS = {
    "00-READ-FIRST.md": "45cae20cc87a1dac6674b07a897612180f4010c6a98e1f32648d5fda67db2de9",
    "ROLE-PACK.json": "a6406228f83365c91c9f9b50303b08993c2f393bc78d3b85d2e95b412a300f85",
}
EXPECTED_FILES = set(SOURCE_DIGESTS) | set(WRAPPER_DIGESTS) | {"PACKAGE-CHECKSUMS.sha256"}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    manifest = json.loads((PACKAGE / "ROLE-PACK.json").read_text(encoding="utf-8"))
    expected = {
        "role": "Medical Resident — ROUNDS",
        "population_lane": "medical_resident",
        "route": "/medical-residents/",
        "namespace": "medres_rounds.*",
        "resident_home": "My ROUNDS",
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "package_version": "2026.07.16.1",
        "optional_superpowers_total": 24,
        "optional_superpowers_active_after_install": 0,
        "suggested_agents_total": 10,
        "suggested_agents_active_after_install": 0,
        "workflows_total": 24,
        "templates_total": 30,
        "records_total": 17,
        "acceptance_tests": {"foundation": 72, "rounds_overlay": 72, "integration": 16, "total": 160},
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"ROUNDS manifest mismatch for {key}")
    true_keys = (
        "standalone_non_nurse_lane",
        "no_phi",
        "pre_install_disclosure_required",
        "foundation_first",
        "rounds_overlay_second",
        "institutional_deployment_requires_separate_authorization",
    )
    false_keys = (
        "install_on_download",
        "nursing_population_state_shared",
        "role_selection_verifies_credentials_or_authority",
        "live_patient_specific_private_use",
        "clinical_decisions",
        "automatic_memory",
        "automatic_connectors",
        "automatic_shared_access",
        "automatic_external_actions",
        "automatic_cron",
    )
    for key in true_keys:
        if manifest.get(key) is not True:
            raise ValueError(f"ROUNDS safety flag must be true: {key}")
    for key in false_keys:
        if manifest.get(key) is not False:
            raise ValueError(f"ROUNDS safety flag must be false: {key}")
    declared = {item.get("packaged_path"): item.get("source_sha256") for item in manifest.get("source_files", [])}
    if declared != SOURCE_DIGESTS:
        raise ValueError("ROUNDS source inventory or digest declarations changed")
    program = next(item for item in manifest["source_files"] if item["packaged_path"].endswith("Hermes-Program.md"))
    if program.get("upstream_sha256") != "63524f871de3a28842d04e936b7bce7bd2b3a76724f08222179a7a8c7365d35e":
        raise ValueError("ROUNDS upstream program provenance changed")
    if "trailing-space hard breaks" not in program.get("transformation", ""):
        raise ValueError("ROUNDS program transformation record missing")
    if "four-space indentation" not in program.get("transformation", ""):
        raise ValueError("ROUNDS program indentation normalization record missing")
    guide = next(item for item in manifest["source_files"] if item["packaged_path"].endswith("Setup-Guide.md"))
    if guide.get("upstream_sha256") != "5afbd0e56253167d6fe4247aaa081b520d648a232af98e212c0f2a355d2e4ead":
        raise ValueError("ROUNDS upstream Markdown provenance changed")
    if "four-space indentation" not in guide.get("transformation", ""):
        raise ValueError("ROUNDS Markdown transformation record missing")
    return manifest


def parse_ledger() -> dict[str, str]:
    ledger = PACKAGE / "PACKAGE-CHECKSUMS.sha256"
    records: dict[str, str] = {}
    for line_number, line in enumerate(ledger.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\\]+)", line)
        if not match:
            raise ValueError(f"Malformed ROUNDS checksum line {line_number}")
        relative = Path(match.group(2))
        if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 1:
            raise ValueError(f"Unsafe ROUNDS checksum path: {relative}")
        name = relative.as_posix()
        if name in records:
            raise ValueError(f"Duplicate ROUNDS checksum path: {name}")
        records[name] = match.group(1)
    expected = EXPECTED_FILES - {"PACKAGE-CHECKSUMS.sha256"}
    if set(records) != expected:
        raise ValueError("ROUNDS checksum ledger inventory mismatch")
    for name, digest in records.items():
        if sha256(PACKAGE / name) != digest:
            raise ValueError(f"ROUNDS checksum mismatch: {name}")
    return records


def validate_package() -> dict:
    if not PACKAGE.is_dir():
        raise FileNotFoundError(PACKAGE)
    actual_files = {p.name for p in PACKAGE.iterdir() if p.is_file()}
    unexpected_dirs = [p.name for p in PACKAGE.iterdir() if p.is_dir()]
    symlinks = [p.name for p in PACKAGE.iterdir() if p.is_symlink()]
    if actual_files != EXPECTED_FILES or unexpected_dirs or symlinks:
        raise ValueError(
            f"ROUNDS package inventory mismatch: files={sorted(actual_files)}, "
            f"dirs={unexpected_dirs}, symlinks={symlinks}"
        )
    for name, digest in {**SOURCE_DIGESTS, **WRAPPER_DIGESTS}.items():
        if sha256(PACKAGE / name) != digest:
            raise ValueError(f"Trusted ROUNDS digest mismatch: {name}")
    manifest = load_manifest()
    parse_ledger()
    return manifest


def refresh_ledger() -> None:
    targets = [PACKAGE / name for name in sorted(EXPECTED_FILES - {"PACKAGE-CHECKSUMS.sha256"})]
    content = "\n".join(f"{sha256(path)}  {path.name}" for path in targets) + "\n"
    (PACKAGE / "PACKAGE-CHECKSUMS.sha256").write_text(content, encoding="utf-8")
    parse_ledger()


def build() -> dict:
    manifest = validate_package()
    refresh_ledger()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    output = DOWNLOADS / ZIP_NAME
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(EXPECTED_FILES):
            path = PACKAGE / name
            info = zipfile.ZipInfo(f"{ZIP_PREFIX}/{name}", FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    record = {
        "acceptance_tests": manifest["acceptance_tests"],
        "activation": manifest["activation"],
        "bytes": output.stat().st_size,
        "download": f"downloads/{ZIP_NAME}",
        "foundation_first": True,
        "install_on_download": False,
        "installation_status": "not_installed",
        "institutional_deployment_requires_separate_authorization": True,
        "nursing_population_state_shared": False,
        "optional_superpowers_active_after_install": 0,
        "optional_superpowers_total": 24,
        "package_version": manifest["package_version"],
        "population_lane": manifest["population_lane"],
        "pre_install_disclosure_required": True,
        "records_total": 17,
        "role": manifest["role"],
        "rounds_overlay_second": True,
        "route": manifest["route"],
        "sha256": sha256(output),
        "standalone_non_nurse_lane": True,
        "suggested_agents_active_after_install": 0,
        "suggested_agents_total": 10,
        "templates_total": 30,
        "workflows_total": 24,
    }
    public = {
        "installation_status": "not_installed",
        "packages": [record],
        "purpose": "standalone adjacent clinical lane for medical residents; separate from Nurse AI OS post-setup lanes",
        "release": manifest["package_version"],
        "schema_version": "1.0",
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DOWNLOADS / "CHECKSUMS.sha256").write_text(f"{record['sha256']}  {ZIP_NAME}\n", encoding="utf-8")
    print("ROUNDS_PACKAGES=1")
    print("INSTALLATION_STATUS=not_installed")
    print(f"ROUNDS_ZIP_SHA256={record['sha256']}")
    print(f"ROUNDS_ZIP_BYTES={record['bytes']}")
    return record


def main() -> int:
    try:
        build()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
