#!/usr/bin/env python3
"""Build the deterministic non-executable STEWARD governance preview.

This builder packages public documents only. It does not install, activate,
configure, connect, schedule, execute, authorize, or send anything.
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
FIXED_ZIP_TIME = (2026, 7, 16, 0, 0, 0)
PINNED = {
    "README.md": (1835, "fc6dc00ae16fd1179faa13d113279c1b3a0b70fd8beaa343b4131e8b8684e768"),
    "STEWARD-Governance-Specification.md": (21268, "3be24aeb2405ec1020261888166696ab8758ca510df8b563214199deac0a0925"),
    "STEWARD-Governance-Specification.pdf": (563521, "ce56db69ce02ed1ff2968b57d2ea53eba1e7f22b9095b9c3acb7835d2af25e45"),
    "STEWARD-Enforcement-Gap-Register.md": (8595, "4d67d3a13891c603ed188aa9ddec812ba84e5b879567c75400e3786396273abd"),
    "SOURCE-PROVENANCE.json": (2396, "df1db5f0f3e7325a99b296e03936828765a0d15338e34926ce1b90417795acbd"),
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


def refresh_package_checksums() -> Path:
    lines = [f"{PINNED[name][1]}  {name}" for name in sorted(PINNED)]
    output = PREVIEW / CHECKSUM_NAME
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def build() -> dict:
    validate_sources()
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
    record = {
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
    manifest = {
        "packages": [record],
        "purpose": "public non-executable STEWARD governance preview for hospital and clinic administration",
        "release_posture": "doctrine_kept_installable_complete_ai_os_paused",
        "schema_version": "1.0",
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DOWNLOADS / "CHECKSUMS.sha256").write_text(f"{record['sha256']}  {ZIP_NAME}\n", encoding="utf-8")
    print("STEWARD_PREVIEW_PACKAGES=1")
    print("ARTIFACT_CLASS=non_executable_governance_preview")
    print("RUNTIME_STATUS=not_implemented")
    print("COMPLETE_AI_OS_CLAIM=paused")
    print(f"STEWARD_PREVIEW_SHA256={record['sha256']}")
    print(f"STEWARD_PREVIEW_BYTES={record['bytes']}")
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
