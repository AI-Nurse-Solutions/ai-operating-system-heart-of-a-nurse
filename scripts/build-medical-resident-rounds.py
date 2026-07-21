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
import subprocess
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "medical-residents"
PACKAGE = ROOT / "packages" / "rounds"
DOWNLOADS = ROOT / "downloads"
ZIP_NAME = "medical-resident-rounds-complete-edition.zip"
ZIP_PREFIX = "ROUNDS-Medical-Resident-Complete-Edition"
BUILD_KIT_NAME = "ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_ROOT = "ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0"
BUILD_KIT_SOURCE = ROOT / "build-kit"
BUILD_KIT_SHA256 = "9da287f43df9398eec648addf3524d8f12415a90af33fa2c9d31e92972bef666"
BUILD_KIT_BYTES = 6993919
BUILD_KIT_MEMBERS = 149
BUILD_KIT_VERIFIER_SHA256 = "53a098778079535946867a80cd88880943400815a21c7b0b13e8279a13625f8e"
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


def _safe_build_kit_member(name: str) -> None:
    if not name or name.startswith(("/", "\\")) or "\x00" in name or "\\" in name:
        raise ValueError(f"Unsafe ROUNDS build-kit member path: {name!r}")
    parts = Path(name).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Traversal path is not allowed in ROUNDS build kit: {name!r}")


def build_kit_source_files() -> list[Path]:
    source = BUILD_KIT_SOURCE / BUILD_KIT_ROOT
    if not source.is_dir():
        raise ValueError(f"Missing tracked ROUNDS build-kit source tree: {source}")
    files = sorted(path for path in source.rglob("*") if path.is_file())
    if len(files) != BUILD_KIT_MEMBERS:
        raise ValueError(f"ROUNDS tracked build-kit source inventory changed: {len(files)}")
    if any(path.is_symlink() for path in source.rglob("*")):
        raise ValueError("ROUNDS tracked build-kit source tree must not contain symlinks")
    return files


def build_build_kit_zip() -> None:
    files = build_kit_source_files()
    output = DOWNLOADS / BUILD_KIT_NAME
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            relative = path.relative_to(BUILD_KIT_SOURCE / BUILD_KIT_ROOT).as_posix()
            _safe_build_kit_member(f"{BUILD_KIT_ROOT}/{relative}")
            info = zipfile.ZipInfo(f"{BUILD_KIT_ROOT}/{relative}", FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.name == "verify-build-kit.py" else 0o644
            info.external_attr = (0o100000 | mode) << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)


def run_bundled_build_kit_verifier() -> None:
    package = BUILD_KIT_SOURCE / BUILD_KIT_ROOT
    verifier = package / "tools" / "verify-build-kit.py"
    if not verifier.is_file():
        raise ValueError("Tracked ROUNDS build-kit source missing bundled verifier")
    if sha256(verifier) != BUILD_KIT_VERIFIER_SHA256:
        raise ValueError("ROUNDS tracked bundled verifier bytes changed")
    completed = subprocess.run(
        [sys.executable, str(verifier), "--package", str(package), "--zip", str(DOWNLOADS / BUILD_KIT_NAME)],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise ValueError(f"Bundled ROUNDS build-kit verifier failed:\n{completed.stdout[-4000:]}")
    if "VERIFIED ROUNDS MEDICAL RESIDENT BUILD KIT" not in completed.stdout:
        raise ValueError("Bundled ROUNDS verifier did not emit the expected verification summary")


def _ledger_records(text: str, expected: set[str], label: str) -> dict[str, str]:
    records: dict[str, str] = {}
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  ([^\\]+)", line)
        if not match:
            raise ValueError(f"Malformed ROUNDS {label} checksum line {line_number}")
        relative = Path(match.group(2))
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"Unsafe ROUNDS {label} checksum path: {relative}")
        name = relative.as_posix()
        if name in records:
            raise ValueError(f"Duplicate ROUNDS {label} checksum path: {name}")
        records[name] = match.group(1)
    if set(records) != expected:
        raise ValueError(f"ROUNDS {label} checksum inventory mismatch")
    return records


def validate_build_kit_zip_structure(path: Path, *, enforce_pins: bool = True) -> dict:
    if not path.is_file():
        raise ValueError(f"Missing ROUNDS build kit: {path}")
    if enforce_pins and (path.stat().st_size != BUILD_KIT_BYTES or sha256(path) != BUILD_KIT_SHA256):
        raise ValueError("ROUNDS build kit bytes changed")
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise ValueError("ROUNDS build kit ZIP CRC check failed")
        infos = archive.infolist()
        if enforce_pins and len(infos) != BUILD_KIT_MEMBERS:
            raise ValueError(f"ROUNDS build kit member count changed: {len(infos)}")
        seen: set[str] = set()
        normalized: set[str] = set()
        for info in infos:
            if info.filename in seen:
                raise ValueError(f"Duplicate ROUNDS build-kit ZIP member: {info.filename}")
            seen.add(info.filename)
            key = info.filename.casefold()
            if key in normalized:
                raise ValueError(f"Case-colliding ROUNDS build-kit ZIP member: {info.filename}")
            normalized.add(key)
            _safe_build_kit_member(info.filename)
            mode = info.external_attr >> 16
            if mode & 0o170000 != 0o100000:
                raise ValueError(f"ROUNDS build kit allows only regular-file entries: {info.filename}")
        roots = {info.filename.split("/", 1)[0] for info in infos if info.filename}
        if roots != {BUILD_KIT_ROOT}:
            raise ValueError(f"ROUNDS build kit root mismatch: {sorted(roots)}")
        required = {
            f"{BUILD_KIT_ROOT}/README-FIRST.md",
            f"{BUILD_KIT_ROOT}/GIVE-THIS-PACKAGE-TO-HERMES.md",
            f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json",
            f"{BUILD_KIT_ROOT}/SHA256SUMS.txt",
            f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py",
        }
        if not required.issubset(seen):
            raise ValueError("ROUNDS build kit missing required handoff, manifest, checksum, or verifier files")
        manifest = json.loads(archive.read(f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json"))
        if hashlib.sha256(archive.read(f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py")).hexdigest() != BUILD_KIT_VERIFIER_SHA256:
            raise ValueError("ROUNDS bundled verifier bytes changed")
        expected_files = {name.removeprefix(f"{BUILD_KIT_ROOT}/") for name in seen if name != f"{BUILD_KIT_ROOT}/SHA256SUMS.txt"}
        ledger = _ledger_records(archive.read(f"{BUILD_KIT_ROOT}/SHA256SUMS.txt").decode("utf-8"), expected_files, "build-kit")
        for name, digest in ledger.items():
            if hashlib.sha256(archive.read(f"{BUILD_KIT_ROOT}/{name}")).hexdigest() != digest:
                raise ValueError(f"ROUNDS build-kit checksum mismatch: {name}")
    return manifest


def validate_build_kit() -> dict:
    path = DOWNLOADS / BUILD_KIT_NAME
    manifest = validate_build_kit_zip_structure(path)
    run_bundled_build_kit_verifier()
    if manifest["target"] != {
        "foundation_namespace": "medres_rounds.*",
        "home": "My ROUNDS",
        "lane": "medical_resident",
        "namespace": "medres_rounds.*",
        "product": "ROUNDS — Medical Resident Complete AI OS Mission Control",
        "product_id": "medical-resident-rounds-mission-control",
        "readiness": "not_operational_build_required",
        "route": "/medical-residents",
        "version": "2.0.0",
    }:
        raise ValueError("ROUNDS build kit target contract changed")
    expected_counts = {
        "active_deployment_contexts": 1,
        "agents": 10,
        "canonical_assurance_checks": 160,
        "capability_criteria_including_capstone": 77,
        "capability_domains": 17,
        "control_matrix_rows": 216,
        "core_launchers": 4,
        "cross_cutting_full_stack_scenarios": 48,
        "declared_deployment_contexts": 2,
        "declared_partitions": 9,
        "declared_record_types": 17,
        "institutional_declared_unavailable_partitions": 6,
        "machine_record_contracts": 17,
        "mastery_levels": 4,
        "personal_available_partitions": 3,
        "protected_record_scopes": 5,
        "role_adapters": 5,
        "role_lane": 1,
        "superpowers": 24,
        "task_hats": 11,
        "templates": 30,
        "total_required_execution_records": 424,
        "workflows": 24,
    }
    for key, value in expected_counts.items():
        if manifest["counts"].get(key) != value:
            raise ValueError(f"ROUNDS build kit count changed: {key}")
    if manifest["defaults"] != {
        "agents": "PERM-P0 Disabled",
        "external_actions": "Off",
        "memory": "session_only",
        "optional_fifth_launcher": "Empty",
        "perm_p5": "Prohibited",
        "personal_perm_p4": "Unavailable",
        "powers": "Available Inactive",
        "workflows": "Preview Only",
    }:
        raise ValueError("ROUNDS build kit defaults changed")
    return manifest


def build() -> dict:
    manifest = validate_package()
    refresh_ledger()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    build_build_kit_zip()
    build_kit_manifest = validate_build_kit()
    output = DOWNLOADS / ZIP_NAME
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(EXPECTED_FILES):
            path = PACKAGE / name
            info = zipfile.ZipInfo(f"{ZIP_PREFIX}/{name}", FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    source_record = {
        "acceptance_tests": manifest["acceptance_tests"],
        "activation": manifest["activation"],
        "artifact_class": "legacy_complete_edition_source_package",
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
    build_kit_record = {
        "activation_available": True,
        "activation_contract": "user_initiated_read_only_preflight_then_exact_implementation_activation_card_approval",
        "artifact_class": "hermes_functional_build_kit_self_install",
        "bytes": BUILD_KIT_BYTES,
        "build_kit_version": "1.0.0",
        "complete_ai_os_claim": "not_operational_build_required",
        "download": f"downloads/{BUILD_KIT_NAME}",
        "install_on_download": False,
        "institutional_authorization": False,
        "operational_data_authorized": False,
        "population_lane": "medical_resident",
        "pre_install_disclosure_required": True,
        "readiness": build_kit_manifest["target"]["readiness"],
        "route": "/medical-residents/",
        "runtime_status": "not_built_until_user_hermes_runs_approved_program",
        "sha256": BUILD_KIT_SHA256,
        "target_application_version": build_kit_manifest["target"]["version"],
        "total_required_execution_records": build_kit_manifest["counts"]["total_required_execution_records"],
    }
    public = {
        "installation_status": "not_installed",
        "packages": [source_record, build_kit_record],
        "purpose": "standalone adjacent clinical lane for medical residents; separate from Nurse AI OS post-setup lanes",
        "release": manifest["package_version"],
        "release_posture": "source_package_available_build_kit_available_runtime_not_operational_until_user_approved_build",
        "schema_version": "1.0",
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DOWNLOADS / "CHECKSUMS.sha256").write_text(
        f"{source_record['sha256']}  {ZIP_NAME}\n{BUILD_KIT_SHA256}  {BUILD_KIT_NAME}\n",
        encoding="utf-8",
    )
    print("ROUNDS_PACKAGES=1")
    print("ROUNDS_BUILD_KIT_PACKAGES=1")
    print("INSTALLATION_STATUS=not_installed")
    print(f"ROUNDS_ZIP_SHA256={source_record['sha256']}")
    print(f"ROUNDS_ZIP_BYTES={source_record['bytes']}")
    print(f"ROUNDS_BUILD_KIT_SHA256={BUILD_KIT_SHA256}")
    print(f"ROUNDS_BUILD_KIT_BYTES={BUILD_KIT_BYTES}")
    return build_kit_record


def main() -> int:
    try:
        build()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
