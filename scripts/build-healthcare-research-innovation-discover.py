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
import os
import re
import stat
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path
from pathlib import PurePosixPath

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "healthcare-research-innovation-leaders"
PACKAGE = ROOT / "packages" / "discover"
DOWNLOADS = ROOT / "downloads"
ZIP_NAME = "discover-healthcare-research-innovation-leader-complete-edition.zip"
ZIP_PREFIX = "DISCOVER-Healthcare-Research-Innovation-Leader-Complete-Edition"
BUILD_KIT_ZIP_NAME = "DISCOVER-Healthcare-Research-Innovation-Leader-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_ROOT = "DISCOVER-Healthcare-Research-Innovation-Leader-Mission-Control-Hermes-Build-Kit-v1.0.0"
BUILD_KIT_EXPECTED = {
    "bytes": 7287900,
    "members": 116,
    "sha256": "e028046039800232db75c3d0a09e1105b46f4acfc97071e841b3317f0afcf018",
    "verifier_sha256": "b1580412e01da1a02c98d72c43ebae7dd592f5a78a777cdb6d465bc1fbca1383",
}
BUILD_KIT_MAX_MEMBER_BYTES = 32 * 1024 * 1024
BUILD_KIT_MAX_EXPANDED_BYTES = 192 * 1024 * 1024
BUILD_KIT_ALLOWED_COMPRESSION = {zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED}
FIXED_ZIP_TIME = (2026, 7, 16, 0, 0, 0)
PROGRAM_NAME = "Healthcare-Research-and-Innovation-Leader-Complete-AI-OS-with-DISCOVER-SuperPowers-Hermes-Program.md"
SOURCE_PACK = "Healthcare-Research-and-Innovation-Leader-DISCOVER-SuperPowers-Pack-v1.0"
WRAPPER_DIGESTS = {
    "00-READ-FIRST.md": "4acfcfe9461c43ab9548de951a914021288590a4a1e583e47d736aa9dc7b3cbe",
    "ROLE-PACK.json": "fc2e5d22969544e4ee036a7998415c66e9190a367a2107cd5e54f5e2403bd8a6",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_zip_target(root: Path, member: str) -> Path:
    if not member or "\x00" in member or "\\" in member:
        raise ValueError(f"Unsafe DISCOVER build-kit ZIP path: {member!r}")
    relative = PurePosixPath(member)
    if (
        relative.is_absolute()
        or ".." in relative.parts
        or not relative.parts
        or any(":" in part for part in relative.parts)
        or member.rstrip("/") != relative.as_posix()
    ):
        raise ValueError(f"Unsafe DISCOVER build-kit ZIP path: {member}")
    target = root.joinpath(*relative.parts).resolve()
    if not str(target).startswith(str(root.resolve()) + os.sep):
        raise ValueError(f"DISCOVER build-kit ZIP path escapes extraction root: {member}")
    return target


def _extract_build_kit_for_verification(zip_path: Path, root: Path) -> Path:
    seen: set[str] = set()
    canonical_names: set[str] = set()
    expanded_bytes = 0
    with zipfile.ZipFile(zip_path) as archive:
        infos = archive.infolist()
        if len(infos) != BUILD_KIT_EXPECTED["members"]:
            raise ValueError("DISCOVER build-kit ZIP member count mismatch")
        roots: set[str] = set()
        for info in infos:
            name = info.filename
            raw_name = getattr(info, "orig_filename", name)
            if "\x00" in raw_name:
                raise ValueError(f"Unsafe DISCOVER build-kit ZIP path: {raw_name!r}")
            if raw_name != name:
                raise ValueError(
                    f"DISCOVER build-kit ZIP raw/normalized path mismatch: {raw_name!r}"
                )
            _safe_zip_target(root, name)
            roots.add(name.split("/", 1)[0])
            if name in seen:
                raise ValueError(f"Duplicate DISCOVER build-kit ZIP member: {name}")
            seen.add(name)
            canonical = unicodedata.normalize("NFC", name.rstrip("/")).casefold()
            if canonical in canonical_names:
                raise ValueError(f"DISCOVER build-kit ZIP case/Unicode collision: {name}")
            canonical_names.add(canonical)
            if info.flag_bits & 1:
                raise ValueError(f"DISCOVER build-kit ZIP encrypted member is forbidden: {name}")
            if info.compress_type not in BUILD_KIT_ALLOWED_COMPRESSION:
                raise ValueError(f"DISCOVER build-kit ZIP compression method is forbidden: {name}")
            mode = (info.external_attr >> 16) & 0o177777
            mode_type = stat.S_IFMT(mode)
            if mode_type not in {0, stat.S_IFDIR, stat.S_IFREG}:
                raise ValueError(f"DISCOVER build-kit ZIP special file is forbidden: {name}")
            if info.is_dir() and mode_type not in {0, stat.S_IFDIR}:
                raise ValueError(f"DISCOVER build-kit ZIP directory mode mismatch: {name}")
            if not info.is_dir() and mode_type not in {0, stat.S_IFREG}:
                raise ValueError(f"DISCOVER build-kit ZIP file mode mismatch: {name}")
            if info.file_size > BUILD_KIT_MAX_MEMBER_BYTES:
                raise ValueError(f"DISCOVER build-kit ZIP member exceeds byte limit: {name}")
            expanded_bytes += info.file_size
            if expanded_bytes > BUILD_KIT_MAX_EXPANDED_BYTES:
                raise ValueError("DISCOVER build-kit ZIP exceeds expanded-byte limit")
        if roots != {BUILD_KIT_ROOT}:
            raise ValueError(f"DISCOVER build-kit ZIP root mismatch: {sorted(roots)}")

        # CRC reads happen only after all member metadata has passed validation.
        if archive.testzip() is not None:
            raise ValueError("DISCOVER build-kit ZIP CRC verification failed")
        for info in infos:
            name = info.filename
            target = _safe_zip_target(root, name)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info))
            permissions = (info.external_attr >> 16) & 0o777
            if permissions:
                target.chmod(permissions)
    package = root / BUILD_KIT_ROOT
    if not package.is_dir():
        raise ValueError("DISCOVER build-kit ZIP root directory mismatch")
    return package


def _parse_checksum_ledger(package: Path) -> dict[str, str]:
    ledger: dict[str, str] = {}
    for line_number, line in enumerate(
        (package / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines(), 1
    ):
        if not line.strip():
            continue
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match:
            raise ValueError(f"DISCOVER build-kit checksum ledger line is invalid: {line_number}")
        digest, relative = match.groups()
        if relative in ledger:
            raise ValueError(f"DISCOVER build-kit checksum ledger duplicate path: {relative}")
        _safe_zip_target(package, relative)
        ledger[relative] = digest
    return ledger


def _validate_extracted_build_kit(package: Path) -> dict:
    actual_files = sorted(path.relative_to(package).as_posix() for path in package.rglob("*") if path.is_file())
    if len(actual_files) != BUILD_KIT_EXPECTED["members"]:
        raise ValueError("DISCOVER build-kit extracted file count mismatch")
    required_files = {
        "BUILD-STATUS.md",
        "GIVE-THIS-PACKAGE-TO-HERMES.md",
        "README-FIRST.md",
        "RELEASE-MANIFEST.json",
        "SHA256SUMS.txt",
        "SOURCE-NOTES.md",
        "tools/verify-build-kit.py",
    }
    if not required_files.issubset(actual_files):
        raise ValueError("DISCOVER build-kit required-file inventory mismatch")
    if any((package / relative).stat().st_size == 0 for relative in actual_files):
        raise ValueError("DISCOVER build-kit contains an empty file")
    manifest = json.loads((package / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))
    inventory = manifest.get("files_excluding_manifest_and_checksums")
    if not isinstance(inventory, list):
        raise ValueError("DISCOVER build-kit manifest inventory missing")
    declared: dict[str, dict] = {}
    for record in inventory:
        if not isinstance(record, dict):
            raise ValueError("DISCOVER build-kit manifest inventory record is invalid")
        relative = record.get("path")
        if not isinstance(relative, str) or relative in declared:
            raise ValueError(f"DISCOVER build-kit manifest inventory path invalid: {relative!r}")
        if relative in {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}:
            raise ValueError(f"DISCOVER build-kit manifest inventory includes generated ledger file: {relative}")
        _safe_zip_target(package, relative)
        if not isinstance(record.get("bytes"), int) or record["bytes"] < 0:
            raise ValueError(f"DISCOVER build-kit manifest byte count invalid: {relative}")
        if not isinstance(record.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", record["sha256"]):
            raise ValueError(f"DISCOVER build-kit manifest digest invalid: {relative}")
        declared[relative] = record
    expected_inventory = set(actual_files) - {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}
    if set(declared) != expected_inventory:
        raise ValueError("DISCOVER build-kit manifest inventory does not match extracted files")

    ledger = _parse_checksum_ledger(package)
    if set(ledger) != set(actual_files) - {"SHA256SUMS.txt"}:
        raise ValueError("DISCOVER build-kit checksum ledger does not cover every expected file")
    for relative in actual_files:
        if relative == "SHA256SUMS.txt":
            continue
        path = package / relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if ledger[relative] != digest:
            raise ValueError(f"DISCOVER build-kit checksum ledger mismatch: {relative}")
        if relative in declared:
            record = declared[relative]
            if record.get("sha256") != digest or record.get("bytes") != path.stat().st_size:
                raise ValueError(f"DISCOVER build-kit manifest byte/hash mismatch: {relative}")
    if ledger.get("tools/verify-build-kit.py") != BUILD_KIT_EXPECTED["verifier_sha256"]:
        raise ValueError("DISCOVER build-kit bundled verifier hash mismatch")

    expected_target = {
        "home": "My DISCOVER Mission Control",
        "lane": "healthcare_research_innovation_leadership",
        "namespace": "research_innovation_discover.*",
        "product_id": "discover-healthcare-research-innovation-leader-mission-control",
        "readiness": "not_operational_build_required",
        "route": "/healthcare-research-innovation-leaders/dashboard",
        "version": "2.0.0",
    }
    target = manifest.get("target")
    if not isinstance(target, dict) or any(target.get(key) != value for key, value in expected_target.items()):
        raise ValueError("DISCOVER build-kit target or readiness contract mismatch")
    expected_defaults = {
        "agents": "PERM-P0 Disabled",
        "connectors_schedules_sharing_external_actions": "Off",
        "data": "data_d0_d1_only_by_default_conditional_approved_aggregate_d2",
        "mode": "private_research_innovation_leader_os",
        "model_memory": "session_only_until_separate_consent",
        "powers": "Available Inactive",
        "workflows": "Preview Only",
    }
    if manifest.get("defaults") != expected_defaults:
        raise ValueError("DISCOVER build-kit safe-default contract mismatch")
    expected_counts = {
        "agents": 10,
        "canonical_corpus_criteria_to_execute": 160,
        "research_innovation_domain_schemas": 18,
        "superpowers": 24,
        "templates": 30,
        "workflows": 24,
    }
    counts = manifest.get("counts")
    if not isinstance(counts, dict) or any(counts.get(key) != value for key, value in expected_counts.items()):
        raise ValueError("DISCOVER build-kit governed inventory count mismatch")
    build_kit = manifest.get("build_kit")
    if not isinstance(build_kit, dict) or {
        "id": build_kit.get("id"),
        "version": build_kit.get("version"),
    } != {
        "id": "HRILAIOS-DISCOVER-FUNCTIONAL-BUILD-KIT-1.0.0",
        "version": "1.0.0",
    }:
        raise ValueError("DISCOVER build-kit identity contract mismatch")

    read_first = (package / "README-FIRST.md").read_text(encoding="utf-8")
    handoff = (package / "GIVE-THIS-PACKAGE-TO-HERMES.md").read_text(encoding="utf-8")
    status = (package / "BUILD-STATUS.md").read_text(encoding="utf-8")
    for phrase in (
        "Begin with read-only preflight",
        "Do not install dependencies, edit source, start a service or change my Hermes profile",
        "Implementation Activation Card",
    ):
        if phrase not in read_first:
            raise ValueError(f"DISCOVER build-kit README safety contract missing: {phrase}")
    for phrase in (
        "Required first response: read-only preflight",
        "Do not create the work copy until the Activation Card is approved",
        "Implementation Activation Card",
        "`APPROVE`, `REVISE` and `CANCEL` choices",
    ):
        if phrase not in handoff:
            raise ValueError(f"DISCOVER build-kit Hermes handoff contract missing: {phrase}")
    if "Not operational" not in status:
        raise ValueError("DISCOVER build-kit non-operational status contract missing")
    return manifest


def validate_build_kit() -> dict:
    zip_path = DOWNLOADS / BUILD_KIT_ZIP_NAME
    if not zip_path.is_file():
        raise FileNotFoundError(zip_path)
    if zip_path.stat().st_size != BUILD_KIT_EXPECTED["bytes"] or sha256(zip_path) != BUILD_KIT_EXPECTED["sha256"]:
        raise ValueError("DISCOVER public build-kit derivative digest or byte count mismatch")
    with tempfile.TemporaryDirectory() as tmp:
        package = _extract_build_kit_for_verification(zip_path, Path(tmp))
        manifest = _validate_extracted_build_kit(package)
        if manifest.get("build_kit", {}).get("id") != "HRILAIOS-DISCOVER-FUNCTIONAL-BUILD-KIT-1.0.0":
            raise ValueError("DISCOVER build-kit manifest ID mismatch")
        if manifest.get("target", {}).get("version") != "2.0.0":
            raise ValueError("DISCOVER build-kit target version mismatch")
        if manifest.get("defaults", {}).get("agents") != "PERM-P0 Disabled":
            raise ValueError("DISCOVER build-kit does not default agents to P0 disabled")
        if manifest.get("defaults", {}).get("powers") != "Available Inactive":
            raise ValueError("DISCOVER build-kit does not default powers to inactive")
        if manifest.get("defaults", {}).get("connectors_schedules_sharing_external_actions") != "Off":
            raise ValueError("DISCOVER build-kit connectors/actions default is not Off")
        notes = (package / "SOURCE-NOTES.md").read_text(encoding="utf-8")
        if "Public-safe derivative note" not in notes or "RESTRICTED_RECORD_PLACEHOLDER_123456" not in notes:
            raise ValueError("DISCOVER public-safe derivative note missing")
    return {
        "artifact_class": "hermes_functional_build_kit_self_install",
        "bytes": BUILD_KIT_EXPECTED["bytes"],
        "download": f"downloads/{BUILD_KIT_ZIP_NAME}",
        "installation_status": "not_installed",
        "institutional_authorization": False,
        "package_id": "HRILAIOS-DISCOVER-FUNCTIONAL-BUILD-KIT-1.0.0",
        "public_safety": "public_safe_derivative_mrn_shaped_qa_probe_replaced",
        "readiness": "not_operational_build_required",
        "role": "Healthcare Research & Innovation / Researcher & Innovator — DISCOVER",
        "runtime_status": "not_built_until_user_hermes_runs_approved_program",
        "sha256": BUILD_KIT_EXPECTED["sha256"],
        "target_product": "discover-healthcare-research-innovation-leader-mission-control",
        "target_version": "2.0.0",
        "version": "1.0.0",
    }


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
        "package_version": "2026.07.16.2",
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
    program_required = (
        "exact combined **DISCOVER Activation Card**",
        "Stop after displaying the card. Create no state and wait for explicit post-card authority.",
        "Silence, timeout, download, file opening, title, credentials, access, earlier work, or a general request to “publish and install” is never approval",
        "Any change to the target, program bytes/hash, component hashes, policy, data classes, routes, partitions, permissions, actions, or card invalidates approval and requires a new card",
    )
    if any(phrase not in program for phrase in program_required) or "Nothing continues in the background" not in read_first:
        raise ValueError("DISCOVER exact-card, phase-gate, or no-background contract missing")


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
    build_kit_record = validate_build_kit()
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
        "packages": [record, build_kit_record],
        "purpose": "standalone Healthcare Research and Innovation leadership lane within Nurse AI OS; isolated from nursing, medical-resident, respiratory-care, and hospital-administration state",
        "release": manifest["package_version"],
        "schema_version": "1.0",
    }
    (DOWNLOADS / "manifest.json").write_text(json.dumps(public, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (DOWNLOADS / "CHECKSUMS.sha256").write_text(
        f"{build_kit_record['sha256']}  {BUILD_KIT_ZIP_NAME}\n"
        f"{record['sha256']}  {ZIP_NAME}\n",
        encoding="utf-8",
    )
    print("DISCOVER_PACKAGES=2")
    print("INSTALLATION_STATUS=not_installed")
    print(f"DISCOVER_BUILD_KIT_SHA256={build_kit_record['sha256']}")
    print(f"DISCOVER_BUILD_KIT_BYTES={build_kit_record['bytes']}")
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
