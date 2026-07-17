#!/usr/bin/env python3
"""Build the standalone deterministic DISCOVER Healthcare Research & Innovation release.

This script packages files only. It never installs DISCOVER, modifies a Hermes
profile, creates memory, connects a system, schedules work, runs an agent,
contacts a person, or performs a research, clinical, institutional, or external
action.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "healthcare-research-innovation-leaders"
PACKAGE = ROOT / "packages" / "discover"
DOWNLOADS = ROOT / "downloads"
ZIP_NAME = "discover-healthcare-research-innovation-leader-complete-edition.zip"
ZIP_PREFIX = "DISCOVER-Healthcare-Research-Innovation-Leader-Complete-Edition"
FIXED_ZIP_TIME = (2026, 7, 16, 0, 0, 0)
PROGRAM_NAME = "Healthcare-Research-and-Innovation-Leader-Complete-AI-OS-with-DISCOVER-SuperPowers-Hermes-Program.md"
SOURCE_PACK = "Healthcare-Research-and-Innovation-Leader-DISCOVER-SuperPowers-Pack-v1.0"
WRAPPER_DIGESTS = {
    "00-READ-FIRST.md": "4acfcfe9461c43ab9548de951a914021288590a4a1e583e47d736aa9dc7b3cbe",
    "ROLE-PACK.json": "cc560b71525ca23c7ee7384ff74ebf7b8944e8ad763a659faf5aaefbd1a83294",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def package_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in PACKAGE.rglob("*"):
        if path.is_symlink():
            raise ValueError(f"DISCOVER package symlink is forbidden: {path.relative_to(PACKAGE)}")
        if path.is_file():
            files[path.relative_to(PACKAGE).as_posix()] = path
    return files


def load_manifest() -> dict:
    for name, digest in WRAPPER_DIGESTS.items():
        if sha256(PACKAGE / name) != digest:
            raise ValueError(f"DISCOVER trusted wrapper digest mismatch: {name}")
    manifest = json.loads((PACKAGE / "ROLE-PACK.json").read_text(encoding="utf-8"))
    expected = {
        "activation": "user_initiated_guided_complete_setup_with_combined_activation_card",
        "canonical_dashboard_route": "/healthcare-research-innovation-leaders/dashboard",
        "dashboard_alias": "/healthcare-research-innovation-leaders/mission-control",
        "fixtures_adapters_total": 10,
        "mission_control": "My DISCOVER Mission Control",
        "namespace": "research_innovation_discover.*",
        "optional_superpowers_active_after_install": 0,
        "optional_superpowers_total": 24,
        "package_version": "2026.07.16.1",
        "population_lane": "healthcare_research_innovation_leadership",
        "program_id": "HRIL-AIOS-DISCOVER-COMPLETE-1.0",
        "records_total": 18,
        "role": "Healthcare Research & Innovation Leader — DISCOVER",
        "route": "/healthcare-research-innovation-leaders/",
        "runtime_criteria": {"publication_status": "specified_not_prepassed", "s1": 40, "s2": 120, "total": 160},
        "schemas_total": 18,
        "suggested_agents_active_after_install": 0,
        "suggested_agents_total": 10,
        "templates_total": 30,
        "workflows_total": 24,
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            raise ValueError(f"DISCOVER manifest mismatch for {key}")
    true_keys = (
        "discover_overlay_second",
        "foundation_first",
        "institutional_deployment_requires_separate_authorization",
        "no_phi",
        "pre_install_disclosure_required",
        "standalone_interdisciplinary_lane",
    )
    false_keys = (
        "automatic_connectors",
        "automatic_cron",
        "automatic_external_actions",
        "automatic_memory",
        "automatic_shared_access",
        "clinical_decisions",
        "hospital_administration_population_state_shared",
        "install_on_download",
        "live_person_contact",
        "medical_resident_population_state_shared",
        "nursing_population_state_shared",
        "official_system_writes",
        "participant_recruitment_or_enrollment",
        "person_level_data_allowed",
        "research_or_qi_determinations",
        "respiratory_care_population_state_shared",
        "role_selection_verifies_credentials_or_authority",
    )
    for key in true_keys:
        if manifest.get(key) is not True:
            raise ValueError(f"DISCOVER safety flag must be true: {key}")
    for key in false_keys:
        if manifest.get(key) is not False:
            raise ValueError(f"DISCOVER safety flag must be false: {key}")
    if manifest.get("source_archive") != {
        "bytes": 594992,
        "members": 23,
        "sha256": "79b4a3c6a974061e52348ea9c6b7e5027afc95982802397b4fe203933d2655c6",
        "supplied_name": "DISCOVER-Healthcare-Research-Innovation-Leader-Pack.zip",
    }:
        raise ValueError("DISCOVER source archive provenance changed")
    records = manifest.get("source_files", [])
    if len(records) != 23 or len({item.get("packaged_path") for item in records}) != 23:
        raise ValueError("DISCOVER source record inventory changed")
    for record in records:
        name = record.get("packaged_path", "")
        path = PACKAGE / name
        if not name or not path.is_file():
            raise FileNotFoundError(path)
        if path.stat().st_size != record.get("bytes") or sha256(path) != record.get("source_sha256"):
            raise ValueError(f"DISCOVER trusted source digest or byte mismatch: {name}")
    return manifest


def parse_ledger(name: str, expected: set[str]) -> dict[str, str]:
    records: dict[str, str] = {}
    for line_number, line in enumerate((PACKAGE / name).read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"Malformed DISCOVER checksum line {line_number} in {name}")
        relative = Path(match.group(2))
        if "\\" in match.group(2) or relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError(f"Unsafe DISCOVER checksum path: {relative}")
        path_name = relative.as_posix()
        if path_name in records:
            raise ValueError(f"Duplicate DISCOVER checksum path: {path_name}")
        records[path_name] = match.group(1)
    if set(records) != expected:
        raise ValueError(f"DISCOVER checksum ledger inventory mismatch in {name}")
    return records


def validate_upstream_ledger(manifest: dict) -> None:
    declared = {
        item["upstream_path"]: item["upstream_sha256"]
        for item in manifest["source_files"]
        if item["upstream_path"] != "SHA256SUMS.txt"
    }
    records = parse_ledger("UPSTREAM-SHA256SUMS.txt", set(declared))
    if records != declared:
        raise ValueError("DISCOVER upstream checksum ledger does not match pinned provenance")


def validate_embedded_parity() -> None:
    program = (PACKAGE / PROGRAM_NAME).read_text(encoding="utf-8")
    markers = re.findall(
        r"^<!-- BEGIN COMPONENT: (.+?) \| SHA256: ([0-9a-f]{64}) -->$",
        program,
        re.MULTILINE,
    )
    if len(markers) != 17 or len({relative for relative, _ in markers}) != 17:
        raise ValueError("DISCOVER embedded component inventory mismatch")
    for relative, digest in markers:
        if relative.startswith(("/", "\\")) or ".." in Path(relative).parts or "\\" in relative:
            raise ValueError(f"Unsafe DISCOVER embedded component path: {relative}")
        start = f"<!-- BEGIN COMPONENT: {relative} | SHA256: {digest} -->"
        end = f"<!-- END COMPONENT: {relative} -->"
        segment = program.split(start, 1)[1].split(end, 1)[0].strip("\n")
        source = (PACKAGE / SOURCE_PACK / relative).read_text(encoding="utf-8").strip("\n")
        if segment != source or sha256(PACKAGE / SOURCE_PACK / relative) != digest:
            raise ValueError(f"DISCOVER embedded/source parity mismatch: {relative}")


def validate_declared_contracts() -> None:
    pack = PACKAGE / SOURCE_PACK
    power_text = "\n".join(path.read_text(encoding="utf-8") for path in sorted((pack / "discover").glob("*.md")))
    powers = sorted(set(re.findall(r"^## PWR-(\d{2})\b", power_text, re.MULTILINE)))
    if powers != [f"{index:02d}" for index in range(1, 25)]:
        raise ValueError("DISCOVER power inventory mismatch")
    workflows = (pack / "workflows" / "01-DISCOVER-Runnable-Workflows.md").read_text(encoding="utf-8")
    if re.findall(r"^## WF-(\d{2})\b", workflows, re.MULTILINE) != [f"{index:02d}" for index in range(1, 25)]:
        raise ValueError("DISCOVER workflow inventory mismatch")
    templates = (pack / "templates" / "01-DISCOVER-Functional-Templates.md").read_text(encoding="utf-8")
    if re.findall(r"^## TPL-(\d{2}) —", templates, re.MULTILINE) != [f"{index:02d}" for index in range(1, 31)]:
        raise ValueError("DISCOVER template inventory mismatch")
    schemas = (pack / "workflows" / "03-DISCOVER-Schemas-and-Agents.md").read_text(encoding="utf-8")
    schema_blocks = re.findall(
        r"^### `https://nurse-ai-os\.local/schemas/research_innovation_discover/([^/]+)/1\.0\.0`\n\n"
        r"\*\*Canonical SHA-256:\*\* `([0-9a-f]{64})`\n\n```json\n([^\n]+)\n```",
        schemas,
        re.MULTILINE,
    )
    if len(schema_blocks) != 18 or len({name for name, _, _ in schema_blocks}) != 18:
        raise ValueError("DISCOVER schema inventory mismatch")
    for name, digest, payload in schema_blocks:
        document = json.loads(payload)
        canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        if payload != canonical or hashlib.sha256(payload.encode()).hexdigest() != digest:
            raise ValueError(f"DISCOVER canonical schema hash mismatch: {name}")
        if document.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            raise ValueError(f"DISCOVER schema dialect mismatch: {name}")
        if document.get("type") != "object" or document.get("additionalProperties") is not False or document.get("unevaluatedProperties") is not False:
            raise ValueError(f"DISCOVER schema root is not closed: {name}")
    agents = re.findall(r"^\| `AGT-(\d{2})` \|", schemas, re.MULTILINE)
    if agents != [f"{index:02d}" for index in range(1, 11)]:
        raise ValueError("DISCOVER agent inventory mismatch")
    release = (pack / "tests" / "01-DISCOVER-Release-and-Runtime-Tests.md").read_text(encoding="utf-8")
    expected = [f"RA-{letter}{index:02d}" for letter in "ABCDEFGHIJKLMNOPQR" for index in range(1, 9)]
    expected += [f"RA-INT{index:02d}" for index in range(1, 17)]
    criteria = re.findall(r"^\| (RA-(?:[A-R]\d{2}|INT\d{2})) \|", release, re.MULTILINE)
    variants = re.findall(r"^### `(RA-(?:[A-R]\d{2}|INT\d{2})-VAR@1\.0\.0)`$", release, re.MULTILINE)
    if criteria != expected or len(set(criteria)) != 160:
        raise ValueError("DISCOVER runtime criterion inventory mismatch")
    if variants != [item + "-VAR@1.0.0" for item in expected] or len(set(variants)) != 160:
        raise ValueError("DISCOVER criterion-variant inventory mismatch")
    if "Status vocabulary is `specified`, `executed`, `passed`, `failed`, `blocked`, `unsupported`" not in release:
        raise ValueError("DISCOVER runtime evidence status vocabulary missing")


def validate_consent_contract() -> None:
    read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
    program = (PACKAGE / PROGRAM_NAME).read_text(encoding="utf-8")
    required = (
        "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
        "INSPECT DISCOVER INSTALLER ONLY — CREATE NO STATE.",
        "exact combined **DISCOVER Activation Card**",
        "INSTALL DISCOVER AFTER S0 — USE EXACT VERIFIED COMPONENT HASHES AND KEEP ALL POWERS AND AGENTS INACTIVE.",
        "Silence, timeout, download, file opening, title, credentials, access, earlier work",
        "specified—not pre-passed",
        "A private DISCOVER approval does not authorize organizational or institutional deployment",
    )
    for phrase in required:
        if phrase not in read_first:
            raise ValueError(f"DISCOVER consent or nonclaim contract missing: {phrase}")
    if "Wait for explicit install authority" not in program or "Nothing continues in the background" not in read_first:
        raise ValueError("DISCOVER phase gate or no-background contract missing")


def validate_package() -> dict:
    if not PACKAGE.is_dir():
        raise FileNotFoundError(PACKAGE)
    manifest = load_manifest()
    expected_files = {item["packaged_path"] for item in manifest["source_files"]}
    expected_files.update(WRAPPER_DIGESTS)
    expected_files.add("PACKAGE-CHECKSUMS.sha256")
    files = package_files()
    if set(files) != expected_files:
        raise ValueError(f"DISCOVER package inventory mismatch: {sorted(set(files) ^ expected_files)}")
    validate_upstream_ledger(manifest)
    validate_embedded_parity()
    validate_declared_contracts()
    validate_consent_contract()
    ledger = parse_ledger("PACKAGE-CHECKSUMS.sha256", expected_files - {"PACKAGE-CHECKSUMS.sha256"})
    for name, digest in ledger.items():
        if sha256(PACKAGE / name) != digest:
            raise ValueError(f"DISCOVER package checksum mismatch: {name}")
    return manifest


def refresh_ledger(manifest: dict) -> None:
    names = {item["packaged_path"] for item in manifest["source_files"]}
    names.update(WRAPPER_DIGESTS)
    content = "\n".join(f"{sha256(PACKAGE / name)}  {name}" for name in sorted(names)) + "\n"
    (PACKAGE / "PACKAGE-CHECKSUMS.sha256").write_text(content, encoding="utf-8")


def build() -> dict:
    manifest = validate_package()
    refresh_ledger(manifest)
    files = package_files()
    DOWNLOADS.mkdir(parents=True, exist_ok=True)
    output = DOWNLOADS / ZIP_NAME
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(files):
            path = files[name]
            info = zipfile.ZipInfo(f"{ZIP_PREFIX}/{name}", FIXED_ZIP_TIME)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    record = {
        "activation": manifest["activation"],
        "bytes": output.stat().st_size,
        "discover_overlay_second": True,
        "download": f"downloads/{ZIP_NAME}",
        "foundation_first": True,
        "install_on_download": False,
        "installation_status": "not_installed",
        "institutional_deployment_requires_separate_authorization": True,
        "no_phi": True,
        "optional_superpowers_active_after_install": 0,
        "optional_superpowers_total": 24,
        "package_version": manifest["package_version"],
        "person_level_data_allowed": False,
        "population_lane": manifest["population_lane"],
        "pre_install_disclosure_required": True,
        "role": manifest["role"],
        "route": manifest["route"],
        "runtime_criteria": manifest["runtime_criteria"],
        "schemas_total": 18,
        "sha256": sha256(output),
        "standalone_interdisciplinary_lane": True,
        "suggested_agents_active_after_install": 0,
        "suggested_agents_total": 10,
        "templates_total": 30,
        "workflows_total": 24,
    }
    public = {
        "installation_status": "not_installed",
        "packages": [record],
        "purpose": "standalone Healthcare Research and Innovation leadership lane within Nurse AI OS; isolated from nursing, medical-resident, respiratory-care, and hospital-administration state",
        "release": manifest["package_version"],
        "schema_version": "1.0",
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DOWNLOADS / "CHECKSUMS.sha256").write_text(f"{record['sha256']}  {ZIP_NAME}\n", encoding="utf-8")
    print("DISCOVER_PACKAGES=1")
    print("INSTALLATION_STATUS=not_installed")
    print(f"DISCOVER_ZIP_SHA256={record['sha256']}")
    print(f"DISCOVER_ZIP_BYTES={record['bytes']}")
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
