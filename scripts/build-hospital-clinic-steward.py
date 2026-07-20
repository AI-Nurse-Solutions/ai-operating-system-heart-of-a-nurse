#!/usr/bin/env python3
"""Build STEWARD public download manifests.

The governance-preview bundle remains documentation-only. The functional build
kit is distributed as an inert ZIP for a user to give to their own Hermes. This
builder does not install, activate, configure, connect, schedule, execute,
authorize, or send anything.
"""

from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "hospital-clinic-administrators"
PREVIEW = ROOT / "preview"
DOWNLOADS = ROOT / "downloads"
ZIP_NAME = "steward-governance-preview.zip"
ZIP_PREFIX = "STEWARD-Governance-Preview"
BUILD_KIT_NAME = "STEWARD-Hospital-Clinic-Administrator-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_SHA256 = "c7efccc78b6947466f0e5c48cbd0f1321f9eeecc6ca0b0ce675c07dd4837c306"
BUILD_KIT_BYTES = 6818049
BUILD_KIT_MEMBERS = 116
BUILD_KIT_ROOT = "STEWARD-Hospital-Clinic-Administrator-Mission-Control-Hermes-Build-Kit-v1.0.0"
FIXED_ZIP_TIME = (2026, 7, 16, 0, 0, 0)
PINNED = {
    "README.md": (1835, "fc6dc00ae16fd1179faa13d113279c1b3a0b70fd8beaa343b4131e8b8684e768"),
    "STEWARD-Governance-Specification.md": (21268, "3be24aeb2405ec1020261888166696ab8758ca510df8b563214199deac0a0925"),
    "STEWARD-Governance-Specification.pdf": (563521, "ce56db69ce02ed1ff2968b57d2ea53eba1e7f22b9095b9c3acb7835d2af25e45"),
    "STEWARD-Enforcement-Gap-Register.md": (8595, "4d67d3a13891c603ed188aa9ddec812ba84e5b879567c75400e3786396273abd"),
    "SOURCE-PROVENANCE.json": (3426, "3364dd9bb999beb6e294d19e0514cef38ced87629f9dc190e1e1c6171dc680d5"),
    "LICENSE": (11358, "c95bae1d1ce0235ecccd3560b772ec1efb97f348a79f0fbe0a634f0c2ccefe2c"),
}
CHECKSUM_NAME = "PACKAGE-CHECKSUMS.sha256"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_path(name: str) -> Path:
    return REPO / "LICENSE" if name == "LICENSE" else PREVIEW / name


def validate_sources() -> None:
    actual = {p.name for p in PREVIEW.iterdir() if p.is_file() and p.name != CHECKSUM_NAME}
    expected = set(PINNED) - {"LICENSE"}
    if actual != expected:
        raise ValueError(f"STEWARD preview inventory mismatch: {sorted(actual)}")
    for name, (size, digest) in PINNED.items():
        path = source_path(name)
        if not path.is_file() or path.stat().st_size != size or sha256(path) != digest:
            raise ValueError(f"Pinned STEWARD preview artifact changed: {name}")
    spec = source_path("STEWARD-Governance-Specification.md").read_text(encoding="utf-8")
    readme = source_path("README.md").read_text(encoding="utf-8")
    gap = source_path("STEWARD-Enforcement-Gap-Register.md").read_text(encoding="utf-8")
    for phrase in (
        "Public governance preview · non-executable · not institution-approved",
        "Complete AI OS claim | **Paused**",
        "This preview accepts **no operational data**",
        "This preview ships **zero agents**",
    ):
        if phrase not in spec:
            raise ValueError(f"Missing STEWARD preview boundary: {phrase}")
    if "installer or activation instructions" not in readme or "runtime: **not implemented**" not in readme:
        raise ValueError("STEWARD preview README does not state the non-runtime boundary")
    if "STW-G01" not in gap or "Smallest next step" not in gap:
        raise ValueError("STEWARD enforcement gap register is incomplete")
    provenance = json.loads(source_path("SOURCE-PROVENANCE.json").read_text(encoding="utf-8"))
    public = provenance["public_distribution"]
    if public != {
        "activation_instructions_included": False,
        "complete_ai_os_claim": "paused",
        "executable_or_installer_included": False,
        "operational_data_authorized": False,
        "original_source_payload_included": False,
        "published_artifact_class": "non_executable_governance_preview",
    }:
        raise ValueError("STEWARD provenance publication state changed")
    kit = provenance.get("build_kit_distribution", {})
    if kit.get("sha256") != BUILD_KIT_SHA256 or kit.get("install_on_download") is not False:
        raise ValueError("STEWARD build-kit provenance is not pinned")


def validate_build_kit() -> None:
    path = DOWNLOADS / BUILD_KIT_NAME
    if not path.is_file():
        raise ValueError(f"Missing STEWARD build kit: {BUILD_KIT_NAME}")
    if path.stat().st_size != BUILD_KIT_BYTES or sha256(path) != BUILD_KIT_SHA256:
        raise ValueError("STEWARD build kit bytes changed")
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("STEWARD build kit ZIP CRC check failed")
        infos = archive.infolist()
        if len(infos) != BUILD_KIT_MEMBERS:
            raise ValueError(f"STEWARD build kit member count changed: {len(infos)}")
        roots = {info.filename.split("/", 1)[0] for info in infos if info.filename}
        if roots != {BUILD_KIT_ROOT}:
            raise ValueError(f"STEWARD build kit root mismatch: {sorted(roots)}")
        manifest_name = f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json"
        if manifest_name not in archive.namelist():
            raise ValueError("STEWARD build kit missing RELEASE-MANIFEST.json")
        manifest = json.loads(archive.read(manifest_name))
    if manifest["target"] != {
        "home": "My STEWARD",
        "lane": "hospital_clinic_administration",
        "namespace": "hcadmin_steward.*",
        "product": "STEWARD — Hospital & Clinic Administrator Mission Control",
        "product_id": "steward-hospital-clinic-administrator-mission-control",
        "readiness": "not_operational_build_required",
        "route": "/hospital-clinic-administrators",
        "version": "2.0.0",
    }:
        raise ValueError("STEWARD build kit target contract changed")
    counts = manifest["counts"]
    expected_counts = {
        "acceptance_checks": 200,
        "acceptance_ledger_rows_including_environment_rows": 203,
        "administrator_workspace_starters": 12,
        "agents": 10,
        "control_matrix_rows": 149,
        "legacy_steward_release_criteria": 160,
        "superpowers": 24,
        "templates": 30,
        "workflows": 24,
    }
    for key, value in expected_counts.items():
        if counts.get(key) != value:
            raise ValueError(f"STEWARD build kit count changed: {key}")
    if manifest["defaults"] != {
        "agents": "PERM-P0 Disabled",
        "connectors_schedules_sharing_external_actions": "Off",
        "data": "public_synthetic_or_administrator_owned_nonsensitive_only",
        "mode": "private_administrator_os",
        "model_memory": "session_only_until_separate_consent",
        "powers": "Available Inactive",
    }:
        raise ValueError("STEWARD build kit defaults changed")


def refresh_package_checksums() -> Path:
    lines = [f"{PINNED[name][1]}  {name}" for name in sorted(PINNED)]
    output = PREVIEW / CHECKSUM_NAME
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def build() -> dict:
    validate_sources()
    validate_build_kit()
    checksum = refresh_package_checksums()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    output = DOWNLOADS / ZIP_NAME
    names = sorted(PINNED) + [CHECKSUM_NAME]
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in names:
            path = checksum if name == CHECKSUM_NAME else source_path(name)
            info = zipfile.ZipInfo(f"{ZIP_PREFIX}/{name}", FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    preview_record = {
        "activation_available": False,
        "artifact_class": "non_executable_governance_preview",
        "bytes": output.stat().st_size,
        "complete_ai_os_claim": "paused",
        "download": f"downloads/{ZIP_NAME}",
        "executable_or_installer_included": False,
        "institutional_authorization": False,
        "operational_data_authorized": False,
        "original_source_payload_included": False,
        "population_architecture": "one_lane_with_explicit_context_variants",
        "population_lane_proposed": "hospital_clinic_administration",
        "route": "/hospital-clinic-administrators/",
        "runtime_status": "not_implemented",
        "sha256": sha256(output),
        "version": "2026.07.16-preview.1",
    }
    build_kit_record = {
        "activation_available": True,
        "activation_contract": "user_initiated_read_only_preflight_then_exact_activation_card_approval",
        "artifact_class": "hermes_functional_build_kit_self_install",
        "bytes": BUILD_KIT_BYTES,
        "build_kit_version": "1.0.0",
        "complete_ai_os_claim": "not_operational_build_required",
        "download": f"downloads/{BUILD_KIT_NAME}",
        "install_on_download": False,
        "institutional_authorization": False,
        "operational_data_authorized": False,
        "population_architecture": "one_lane_with_explicit_context_variants",
        "population_lane": "hospital_clinic_administration",
        "pre_install_disclosure_required": True,
        "route": "/hospital-clinic-administrators/",
        "runtime_status": "not_built_until_user_hermes_runs_approved_program",
        "sha256": BUILD_KIT_SHA256,
        "target_application_version": "2.0.0",
    }
    manifest = {
        "packages": [preview_record, build_kit_record],
        "purpose": "STEWARD hospital and clinic administration public preview plus verified self-install Hermes build kit",
        "release_posture": "preview_available_build_kit_available_runtime_not_operational_until_user_approved_build",
        "schema_version": "1.0",
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DOWNLOADS / "CHECKSUMS.sha256").write_text(
        f"{preview_record['sha256']}  {ZIP_NAME}\n{BUILD_KIT_SHA256}  {BUILD_KIT_NAME}\n",
        encoding="utf-8",
    )
    print("STEWARD_PREVIEW_PACKAGES=1")
    print("STEWARD_BUILD_KIT_PACKAGES=1")
    print("ARTIFACT_CLASS=non_executable_governance_preview")
    print("RUNTIME_STATUS=not_implemented")
    print("COMPLETE_AI_OS_CLAIM=paused")
    print(f"STEWARD_PREVIEW_SHA256={preview_record['sha256']}")
    print(f"STEWARD_PREVIEW_BYTES={preview_record['bytes']}")
    print(f"STEWARD_BUILD_KIT_SHA256={BUILD_KIT_SHA256}")
    print(f"STEWARD_BUILD_KIT_BYTES={BUILD_KIT_BYTES}")
    return manifest


def main() -> int:
    try:
        build()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
