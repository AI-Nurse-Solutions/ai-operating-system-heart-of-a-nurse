#!/usr/bin/env python3
"""Verify the FUTURE Nursing Student & Nursing Assistant Hermes build kit.

This standard-library verifier checks the build kit as a supply-chain and
implementation-contract artifact. It does not claim that Hermes has built or
tested the target full-stack application.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import stat
import sys
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


SCRIPT = Path(__file__).resolve()
PACKAGE_NAME = "FUTURE-Nursing-Student-Nursing-Assistant-Mission-Control-Hermes-Build-Kit-v1.0.0"
EXTRACTED = SCRIPT.parent.name == "tools" and (SCRIPT.parents[1] / "README-FIRST.md").is_file()
WORKSPACE = None if EXTRACTED else SCRIPT.parents[1]
DEFAULT_PACKAGE = SCRIPT.parents[1] if EXTRACTED else SCRIPT.parents[1] / "deliverables" / PACKAGE_NAME

BUILD_ID = "NAIO-FUTURE-FUNCTIONAL-BUILD-KIT-1.0.0"
PROMPT_SHA = "ce884cfc6345cc93a6baec0852cf44feb44d859234ef1dc2b5ac2138df18ebe2"
BASELINE_ZIP_SHA = "69a4dd86659b41136ce9ceb2ceb52512ab567637ab0be29fdc6f6ab6573223c1"
LEGACY_ZIP_SHA = "4d1dbeb08ef5689f7193cc233a79da2f126a20be09435ea552ef1de5d77f2999"
BASELINE_MANIFEST_SHA = "22fed55fd789c933f4e7eb50266f88f8dda47f9fba91ebbe9c2cbe4f0ab99702"
BASELINE_CHECKSUMS_SHA = "e178993d6185b126cc915f0d3026ddb3b07e7c5c7dd432aaf581152db8a5a40e"

FUTURE_TREE_HASHES = {
    "README.md": "f7db2c16b573c60550e554fe84a682866a0e4727f3112a7c083d67256afdc89c",
    "core/00-FUTURE-Foundation-Runtime.md": "4607969829fcfec52ca48fb71e930331b6d69d0c646ebe7e669352e63f80e31e",
    "core/01-Learner-Patient-and-Workforce-Trust-Shield.md": "d33d3612d3308aa72d347fb1ca195ee2b7702ca40b83d73b1ff94204a552cf2b",
    "future/01-FUTURE-SuperPowers-System.md": "5ca378064c9a76bf14a0c7b7cf87c46e8e5e32fbdc1368179a5289987b646715",
    "manifest.md": "dc7b69fbf2b8fe70a854e62d2416190a56e1bfb6626c9ad0f1ae26950061b072",
    "templates/FUTURE-Cards-and-Templates.md": "2e62e0423f2a334bbf287824829c18b0b5cf3ffffe45f3784ff99ac7521f9302",
    "tests/Acceptance-Tests.md": "d51e58ec885884fa63190598edc30be1fc128fe19a149b5007ba37b4d620d589",
    "workflows/FUTURE-Command-Center.md": "d4d08daa703db70e74abdf0b54fc2f505837fb34e477e4fa39e27b5615005910",
    "workflows/Seven-Day-and-Ninety-Day-Launch.md": "e045bf66fc6376d99064ae62c5879dedbb58a0488f8d5bdb2dc85f8ea61c4853",
}

BASELINE_ARCHIVE = Path("source/archives/DISCOVER-Nurse-AI-OS-Mission-Control-v2.0.0.zip")
LEGACY_ARCHIVE = Path("source/archives/Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Package-v1.0.zip")
PROMPT = Path("source/original-functional-build-master-prompt.md")
BASELINE = Path("source/baseline-application")
FUTURE_SOURCE = Path("source/future-domain-pack")
LEGACY = Path("source/legacy-reference")

REQUIRED = (
    ".env.example",
    "README-FIRST.md",
    "GIVE-THIS-PACKAGE-TO-HERMES.md",
    "BUILD-STATUS.md",
    "INPUT-PRECEDENCE.md",
    "SOURCE-NOTES.md",
    "CHANGELOG.md",
    "LICENSE-NOTICE.md",
    "VERSION",
    "RELEASE-MANIFEST.json",
    "SHA256SUMS.txt",
    "SOURCE-INVENTORY.json",
    "implementation/FUTURE-Functional-Build-Master-Prompt.md",
    "implementation/FUTURE-Product-Specification.md",
    "implementation/FUTURE-Architecture-and-Data-Model.md",
    "implementation/FUTURE-Governance-EDENA-and-Data-Boundaries.md",
    "implementation/FUTURE-Agent-Team-and-Routing.md",
    "implementation/FUTURE-Personalization-Mapping-Crosswalk.md",
    "implementation/FUTURE-Starter-Workspace-Crosswalk.md",
    "implementation/FUTURE-Capability-and-Badge-Evidence-Model.md",
    "implementation/FUTURE-Guide-Page-Content.md",
    "implementation/FUTURE-Baseline-Gap-Report.md",
    "implementation/FUTURE-Technical-Implementation-Guide.md",
    "implementation/FUTURE-User-Installation-Guide.md",
    "implementation/FUTURE-Security-and-Privacy-Checklist.md",
    "implementation/FUTURE-Synthetic-Sample-Mission.md",
    "implementation/FUTURE-Control-Completeness-Matrix.csv",
    "implementation/FUTURE-Acceptance-and-Test-Ledger.md",
    "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md",
    "personalization/README.md",
    "personalization/FUTURE-Discover-Packet.synthetic.example.json",
    "personalization/FUTURE-Soul-Profile.synthetic.example.json",
    "personalization/FUTURE-Mission-Profile.synthetic.example.json",
    "personalization/input-schemas/discover-packet-input.schema.json",
    "personalization/input-schemas/soul-profile-input.schema.json",
    "schemas/FUTURE-Mission-Profile.schema.json",
    "config/FUTURE-Capability-Mastery-Criteria.v1.json",
    PROMPT.as_posix(),
    BASELINE_ARCHIVE.as_posix(),
    LEGACY_ARCHIVE.as_posix(),
    "tools/verify-build-kit.py",
    "source/legacy-reference/Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Hermes-Program.md",
    "source/legacy-reference/Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.md",
    "source/legacy-reference/Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.docx",
    *(f"source/future-domain-pack/{path}" for path in FUTURE_TREE_HASHES),
)

PLACEHOLDERS = (
    "[PACKAGE_NAME]",
    "[SOURCE_DIRECTORY_OR_REPOSITORY]",
    "[DISCOVER_PACKET_PATH_OR_SOURCE]",
    "[SOUL_QUIZ_RESULTS_PATH_OR_SOURCE]",
    "[HERMES_PROFILE_NAME_OR_AUTO_DETECT]",
    "[USER_TYPE]",
    "[ROLE_LANES]",
    "[DOMAIN]",
    "[AGENT_LIST]",
    "[DATA_CLASSIFICATION]",
    "[DOMAIN_GUARDRAILS]",
    "[MACOS_WINDOWS_LINUX]",
    "[ZIP_INSTALLER_DESKTOP_APP_LOCAL_WEB_APP]",
)


class Checks:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []
        self.warnings: list[str] = []

    def check(self, condition: bool, label: str, detail: Any = None) -> bool:
        if condition:
            self.passed.append(label)
            print(f"PASS  {label}")
            return True
        suffix = "" if detail in (None, "", [], {}) else f" — {detail}"
        self.failed.append(label + suffix)
        print(f"FAIL  {label}{suffix}")
        return False

    def warn(self, label: str, detail: Any = None) -> None:
        suffix = "" if detail in (None, "", [], {}) else f" — {detail}"
        self.warnings.append(label + suffix)
        print(f"WARN  {label}{suffix}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_name(name: str) -> bool:
    if not name or "\x00" in name or "\\" in name or name.startswith("/") or "//" in name:
        return False
    candidate = name[:-1] if name.endswith("/") else name
    if not candidate:
        return False
    parts = candidate.split("/")
    pure = PurePosixPath(candidate)
    return all(part not in {"", ".", ".."} and ":" not in part for part in parts) and not pure.is_absolute() and pure.parts == tuple(parts)


def files(root: Path) -> dict[str, Path]:
    if not root.is_dir():
        return {}
    return {
        path.relative_to(root).as_posix(): path
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def load_json(c: Checks, path: Path, label: str) -> Any | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        c.check(False, label, error)
        return None
    c.check(True, label)
    return value


def parse_checksums(path: Path) -> tuple[dict[str, str], list[str]]:
    result: dict[str, str] = {}
    errors: list[str] = []
    collisions: set[str] = set()
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        digest, separator, relative = line.partition("  ")
        if separator != "  " or not re.fullmatch(r"[0-9a-f]{64}", digest) or not safe_name(relative) or relative.endswith("/"):
            errors.append(f"line {number}")
            continue
        key = unicodedata.normalize("NFC", relative).casefold()
        if relative in result or key in collisions:
            errors.append(f"duplicate/collision line {number}")
            continue
        collisions.add(key)
        result[relative] = digest
    return result, errors


def check_package_inventory(c: Checks, package: Path) -> Any | None:
    checksum_path = package / "SHA256SUMS.txt"
    manifest_path = package / "RELEASE-MANIFEST.json"
    if not c.check(checksum_path.is_file(), "Release checksum file exists"):
        return None
    parsed, errors = parse_checksums(checksum_path)
    c.check(not errors, "Checksum syntax and paths are safe", errors)
    actual = files(package)
    expected_checksum_names = set(actual) - {"SHA256SUMS.txt"}
    c.check(set(parsed) == expected_checksum_names, "Checksum inventory is exact", {
        "missing": sorted(expected_checksum_names - set(parsed)), "extra": sorted(set(parsed) - expected_checksum_names)
    })
    mismatches = [name for name in parsed if name in actual and sha256(actual[name]) != parsed[name]]
    c.check(not mismatches, "Every package checksum matches", mismatches)

    manifest = load_json(c, manifest_path, "Release manifest parses") if c.check(manifest_path.is_file(), "Release manifest exists") else None
    if not isinstance(manifest, dict):
        return manifest
    raw = manifest.get("files_excluding_manifest_and_checksums")
    entries: dict[str, dict[str, Any]] = {}
    malformed: list[Any] = []
    if isinstance(raw, list):
        for item in raw:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str) or not safe_name(item["path"]):
                malformed.append(item)
            elif item["path"] in entries:
                malformed.append(item["path"])
            else:
                entries[item["path"]] = item
    else:
        malformed.append("missing list")
    c.check(not malformed, "Manifest file entries are well formed", malformed[:5])
    expected_manifest_names = set(actual) - {"RELEASE-MANIFEST.json", "SHA256SUMS.txt"}
    c.check(set(entries) == expected_manifest_names, "Manifest inventory is exact", {
        "missing": sorted(expected_manifest_names - set(entries)), "extra": sorted(set(entries) - expected_manifest_names)
    })
    bad = [
        name for name, item in entries.items() if name in actual and
        (item.get("sha256") != sha256(actual[name]) or item.get("bytes") != actual[name].stat().st_size)
    ]
    c.check(not bad, "Manifest hashes and byte counts match", bad)
    return manifest


def archive_files(c: Checks, path: Path, label: str) -> tuple[str | None, dict[str, bytes]]:
    try:
        archive = zipfile.ZipFile(path)
    except Exception as error:
        c.check(False, f"{label} opens", error)
        return None, {}
    with archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        c.check(all(safe_name(name) for name in names), f"{label} paths are safe")
        c.check(len(names) == len(set(names)), f"{label} has no duplicate names")
        normalized = [unicodedata.normalize("NFC", name).casefold() for name in names]
        c.check(len(normalized) == len(set(normalized)), f"{label} has no case/Unicode collisions")
        roots = {PurePosixPath(name).parts[0] for name in names if safe_name(name)}
        root = next(iter(roots)) if len(roots) == 1 else None
        c.check(root is not None, f"{label} has one root", sorted(roots))
        symlinks = [item.filename for item in infos if stat.S_ISLNK((item.external_attr >> 16) & 0xFFFF)]
        c.check(not symlinks, f"{label} contains no symlinks", symlinks)
        bad_crc = archive.testzip()
        c.check(bad_crc is None, f"{label} CRC passes", bad_crc)
        data = {item.filename: archive.read(item) for item in infos if not item.is_dir()}
        return root, data


def compare_tree_archive(c: Checks, tree: Path, archive_path: Path, label: str) -> None:
    root, archived = archive_files(c, archive_path, label)
    if root is None:
        return
    stripped = {name[len(root) + 1:]: data for name, data in archived.items() if name.startswith(root + "/")}
    disk = files(tree)
    c.check(set(disk) == set(stripped), f"{label} unpacked inventory matches", {
        "missing": sorted(set(stripped) - set(disk)), "extra": sorted(set(disk) - set(stripped))
    })
    mismatches = [name for name in set(disk) & set(stripped) if disk[name].read_bytes() != stripped[name]]
    c.check(not mismatches, f"{label} unpacked bytes match", mismatches)


def check_required(c: Checks, package: Path, preassembly: bool) -> None:
    generated_or_copied = {
        "RELEASE-MANIFEST.json", "SHA256SUMS.txt", "SOURCE-INVENTORY.json",
        "implementation/FUTURE-Functional-Build-Master-Prompt.md", "tools/verify-build-kit.py",
        "personalization/input-schemas/discover-packet-input.schema.json",
        "personalization/input-schemas/soul-profile-input.schema.json",
    }
    expected = [
        x for x in REQUIRED
        if not (preassembly and (x in generated_or_copied or x.startswith("source/")))
    ]
    missing = [name for name in expected if not (package / name).is_file()]
    empty = [name for name in expected if (package / name).is_file() and (package / name).stat().st_size == 0]
    c.check(not missing, "All required contracts and sources exist", missing)
    c.check(not empty, "All required contracts and sources are nonempty", empty)
    if (package / "VERSION").is_file():
        c.check((package / "VERSION").read_text(encoding="utf-8").strip() == "1.0.0", "Build-kit VERSION is 1.0.0")


def check_sources(c: Checks, package: Path, manifest: Any | None) -> None:
    prompt = package / PROMPT
    baseline_zip = package / BASELINE_ARCHIVE
    legacy_zip = package / LEGACY_ARCHIVE
    c.check(prompt.is_file() and sha256(prompt) == PROMPT_SHA, "Original functional prompt hash is exact", sha256(prompt) if prompt.is_file() else "missing")
    c.check(baseline_zip.is_file() and sha256(baseline_zip) == BASELINE_ZIP_SHA, "Baseline ZIP hash is exact", sha256(baseline_zip) if baseline_zip.is_file() else "missing")
    c.check(legacy_zip.is_file() and sha256(legacy_zip) == LEGACY_ZIP_SHA, "Legacy FUTURE ZIP hash is exact", sha256(legacy_zip) if legacy_zip.is_file() else "missing")
    if (package / BASELINE).is_dir() and baseline_zip.is_file():
        compare_tree_archive(c, package / BASELINE, baseline_zip, "Baseline source archive")
    else:
        c.check(False, "Baseline unpacked source and archive are present")
    if (package / LEGACY).is_dir() and legacy_zip.is_file():
        compare_tree_archive(c, package / LEGACY, legacy_zip, "Legacy FUTURE source archive")
    else:
        c.check(False, "Legacy FUTURE unpacked source and archive are present")
    future = package / FUTURE_SOURCE
    observed = {name: sha256(future / name) for name in FUTURE_TREE_HASHES if (future / name).is_file()}
    c.check(observed == FUTURE_TREE_HASHES and set(files(future)) == set(FUTURE_TREE_HASHES), "FUTURE source tree has exact nine files and hashes", observed)
    base_manifest = package / BASELINE / "RELEASE-MANIFEST.json"
    base_sums = package / BASELINE / "SHA256SUMS.txt"
    c.check(base_manifest.is_file() and sha256(base_manifest) == BASELINE_MANIFEST_SHA, "Baseline manifest hash is exact")
    c.check(base_sums.is_file() and sha256(base_sums) == BASELINE_CHECKSUMS_SHA, "Baseline checksum hash is exact")

    inventory = load_json(c, package / "SOURCE-INVENTORY.json", "Source inventory parses")
    if isinstance(inventory, dict):
        c.check(inventory.get("schema") == "NAIO-FUTURE-BUILD-KIT-SOURCE-INVENTORY-1", "Source inventory schema is exact")
        source_text = json.dumps(inventory, sort_keys=True)
        c.check(all(value in source_text for value in (PROMPT_SHA, BASELINE_ZIP_SHA, LEGACY_ZIP_SHA, *FUTURE_TREE_HASHES.values())), "Source inventory records every pinned hash")
        personal = inventory.get("personalization", {})
        c.check(isinstance(personal, dict) and all(personal.get(key) is False for key in (
            "real_discover_packet_bundled", "real_soul_quiz_result_bundled", "raw_soul_or_quiz_answers_bundled", "synthetic_examples_are_personal_facts", "synthetic_examples_are_badge_evidence"
        )), "Source inventory truthfully labels personalization")
    if isinstance(manifest, dict):
        sources = manifest.get("sources", {})
        c.check(sources == {
            "original_functional_build_prompt": PROMPT_SHA,
            "baseline_application_zip": BASELINE_ZIP_SHA,
            "future_legacy_outer_zip": LEGACY_ZIP_SHA,
        }, "Release manifest records pinned source archives")


def check_domain(c: Checks, package: Path) -> None:
    source = package / FUTURE_SOURCE
    powers_text = (source / "future/01-FUTURE-SuperPowers-System.md").read_text(encoding="utf-8")
    workflow_text = (source / "workflows/Seven-Day-and-Ninety-Day-Launch.md").read_text(encoding="utf-8")
    template_text = (source / "templates/FUTURE-Cards-and-Templates.md").read_text(encoding="utf-8")
    tests_text = (source / "tests/Acceptance-Tests.md").read_text(encoding="utf-8")
    powers = [int(x) for x in re.findall(r"(?m)^### Power (\d+) —", powers_text)]
    recipes = [int(x) for x in re.findall(r"(?m)^(\d+)\. .+$", workflow_text)]
    templates = re.findall(r"(?m)^## (.+)$", template_text)
    foundation = re.findall(r"(?m)^- \*\*C\d{2} —", tests_text)
    overlay = re.findall(r"(?m)^- \*\*[A-L]\d:", tests_text)
    integration = re.findall(r"(?m)^- \*\*I\d{2}:", tests_text)
    c.check(powers == list(range(1, 19)), "Exactly 18 ordered canonical FUTURE powers")
    c.check(powers_text.count("Inactive; synthetic preview only") == 18, "All 18 canonical powers start inactive")
    c.check(recipes == list(range(1, 19)), "Exactly 18 ordered canonical priority recipes", recipes)
    c.check(templates == [
        "FUTURE Power Activation Card", "SAFE Prompt Card", "AI Use & Integrity Receipt", "Synthetic Workflow Canvas", "Portfolio Evidence Card"
    ], "Exactly five canonical templates", templates)
    c.check((len(foundation), len(overlay), len(integration)) == (24, 96, 16), "Canonical checks are exactly 24 + 96 + 16 = 136", (len(foundation), len(overlay), len(integration)))


def check_contracts(c: Checks, package: Path, manifest: Any | None) -> None:
    prompt = package / "implementation/FUTURE-Functional-Build-Master-Prompt.md"
    if prompt.is_file():
        text = prompt.read_text(encoding="utf-8")
        c.check(not [p for p in PLACEHOLDERS if p in text], "Resolved master prompt has no unresolved placeholders")
        for needle in (BUILD_ID, "future-nursing-student-assistant-mission-control", "nursing_student_assistant", "/nursing-students-assistants/dashboard", "not_operational_build_required"):
            c.check(needle in text, f"Resolved master prompt contains {needle}")

    json_errors: list[str] = []
    for path in package.rglob("*.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as error:
            json_errors.append(f"{path.relative_to(package)}: {error}")
    c.check(not json_errors, "Every JSON file parses", json_errors)

    agent_text = (package / "implementation/FUTURE-Agent-Team-and-Routing.md").read_text(encoding="utf-8")
    agent_ids = sorted(set(re.findall(r"FUT-AGT-(\d{2})", agent_text)))
    c.check(agent_ids == [f"{i:02d}" for i in range(1, 11)], "Exactly ten build-layer agent IDs are frozen", agent_ids)
    c.check("**Installed agent state:** `PERM-P0 Disabled`" in agent_text and "PERM-P1" in agent_text and "PERM-P2" in agent_text and "PERM-P3" in agent_text and "Not an agent permission" in agent_text and "PERM-P4" in agent_text and "Not implemented" in agent_text, "Agent contract records P0 default, P1/P2 ceiling, P3 reminder-only, and absent P4")

    cap = load_json(c, package / "config/FUTURE-Capability-Mastery-Criteria.v1.json", "Capability criteria parse")
    if isinstance(cap, dict):
        c.check(cap.get("schema") == "NAIO-FUTURE-CAPABILITY-MASTERY-CRITERIA-1", "Capability criteria schema ID is exact")
        c.check(cap.get("counts") == {"domains": 17, "levels": 4, "domain_criteria": 68, "capstone_criteria": 9, "total_criteria": 77}, "Capability criteria counts are 17/4/68+9=77", cap.get("counts"))
        domains = cap.get("domains", [])
        c.check(isinstance(domains, list) and [d.get("id") for d in domains] == [f"CAP-{i:02d}" for i in range(1, 18)], "Capability domains are exactly CAP-01..CAP-17")
        c.check(cap.get("passport", {}).get("stages") == ["Explorer", "Safe User", "Verified Creator", "Workflow Builder", "Future Steward"], "Canonical Passport stages remain separate")

    schema = load_json(c, package / "schemas/FUTURE-Mission-Profile.schema.json", "Mission Profile schema parses")
    profile = load_json(c, package / "personalization/FUTURE-Mission-Profile.synthetic.example.json", "Synthetic Mission Profile parses")
    if isinstance(schema, dict) and isinstance(profile, dict):
        required = set(schema.get("required", []))
        properties = set(schema.get("properties", {}))
        c.check(required <= set(profile) <= properties, "Synthetic profile matches declared top-level property set", {"missing": sorted(required-set(profile)), "extra": sorted(set(profile)-properties)})
        c.check(profile.get("schema") == "NAIO-FUTURE-MISSION-PROFILE-1" and profile.get("profile_version") == "1.0-draft", "Synthetic profile contract/version is exact")
        c.check((profile.get("product_id"), profile.get("lane"), profile.get("namespace"), profile.get("canonical_route")) == (
            "future-nursing-student-assistant-mission-control", "nursing_student_assistant", "future.*", "/nursing-students-assistants/dashboard"
        ), "Synthetic profile target identity is exact")
        workspaces = profile.get("role_workspaces", [])
        c.check(isinstance(workspaces, list) and len(workspaces) >= 1 and sum(w.get("relationship") == "primary" for w in workspaces) == 1, "Synthetic profile has exactly one Primary workspace")
        errors: list[str] = []
        for workspace in workspaces if isinstance(workspaces, list) else []:
            rec = workspace.get("recommended_assets", {})
            if rec.get("activation_state") != "recommendations_only_inactive" or rec.get("agent_permission_state") != "PERM-P0 Disabled" or rec.get("tool_ids") != []:
                errors.append(str(workspace.get("workspace_type")))
            if any(not re.fullmatch(r"FUT-AGT-(?:0[1-9]|10)", value) for value in rec.get("agent_ids", [])):
                errors.append(f"agent:{workspace.get('workspace_type')}")
        c.check(not errors, "Profile recommendations remain inactive, P0, and tool-free", errors)

    matrix_path = package / "implementation/FUTURE-Control-Completeness-Matrix.csv"
    try:
        with matrix_path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
    except Exception as error:
        c.check(False, "Control matrix parses", error)
        rows = []
    ids = [row.get("control_id", "") for row in rows]
    expected_pattern = r"^(?:APP|AUTH|ONB|HOME|CTX|MISS|WORK|LEARN|FUT|EVID|AI|AGENT|MEM|CAP|GOV|DATA|DIAG|GUIDE|ACCESS)-[0-9]{3}$"
    c.check(len(rows) == 169 and len(set(ids)) == 169 and all(re.fullmatch(expected_pattern, x) for x in ids), "Control matrix has 169 unique valid IDs")
    c.check(rows and all(row.get("status") == "required_not_implemented" for row in rows), "Every matrix control starts required_not_implemented")

    ledger = (package / "implementation/FUTURE-Acceptance-and-Test-Ledger.md").read_text(encoding="utf-8")
    ctl = re.findall(r"(?m)^\| (CTL-[A-Z0-9-]+) \|.*\| Not Run \|$", ledger)
    integration = re.findall(r"(?m)^\| (INT-[0-9]{3}) \|.*\| Not Run \|$", ledger)
    c.check(len(ctl) == len(set(ctl)) == 169 and set(ctl) == {"CTL-" + x for x in ids}, "Ledger has one Not Run CTL test per matrix row")
    c.check(integration == [f"INT-{i:03d}" for i in range(1, 45)], "Ledger has exactly INT-001..INT-044, all Not Run")
    c.check(all(needle in ledger for needle in ("**169**", "**44**", "**136**", "**349**", "CORE-C01", "OVERLAY-A1", "OVERLAY-L8", "INTEGRATION-I01")), "Ledger preserves 169 + 44 + 136 = 349 and canonical namespaces")

    handoff = (package / "implementation/HERMES-FINAL-HANDOFF-REPORT-TEMPLATE.md").read_text(encoding="utf-8")
    readiness = (
        "**Operational:** All acceptance criteria passed, including a genuine end-to-end streamed response through the downloaded application.",
        "**Core operational; AI setup pending:** All offline/core acceptance criteria passed, but a live configured backend was not available for the genuine-streaming acceptance test.",
        "**Not operational:** One or more core acceptance criteria failed; list each blocker.",
    )
    c.check(all(line in handoff for line in readiness), "Handoff contains the three exact readiness statements")

    boundary_text = "\n".join((package / name).read_text(encoding="utf-8") for name in (
        "README-FIRST.md", "GIVE-THIS-PACKAGE-TO-HERMES.md", "implementation/FUTURE-Governance-EDENA-and-Data-Boundaries.md", "implementation/FUTURE-Guide-Page-Content.md"
    )).casefold()
    needles = ["no phi", "patient", "live care", "academic integrity", "attempt before answer", "session only", "external actions", "pause all", "safe reset", "bridge", "perM-p0".casefold(), "not operational"]
    c.check(all(needle in boundary_text for needle in needles), "Core learner, patient, integrity, memory, action, recovery, and readiness boundaries are documented")

    if isinstance(manifest, dict):
        build = manifest.get("build_kit", {})
        target = manifest.get("target", {})
        counts = manifest.get("counts", {})
        defaults = json.dumps(manifest.get("defaults", {}), sort_keys=True)
        c.check(build.get("id") == BUILD_ID and build.get("version") == "1.0.0", "Manifest build identity is exact")
        c.check((target.get("product_id"), target.get("version"), target.get("lane"), target.get("route"), target.get("namespace"), target.get("home"), target.get("readiness")) == (
            "future-nursing-student-assistant-mission-control", "2.0.0", "nursing_student_assistant", "/nursing-students-assistants/dashboard", "future.*", "FUTURE Mission Control", "not_operational_build_required"
        ), "Manifest target identity and readiness are exact")
        expected_counts = {
            "pathways": 3, "protected_spaces": 4, "core_launchers": 4, "superpowers": 18,
            "workflows": 18, "templates": 5, "agents": 10, "passport_domains": 6,
            "passport_stages": 5, "mastery_levels": 4, "capability_domains": 17,
            "capability_criteria_including_capstone": 77, "canonical_foundation_checks": 24,
            "canonical_overlay_checks": 96, "canonical_integration_checks": 16,
            "canonical_compatibility_checks": 136, "control_matrix_rows": 169,
            "acceptance_ledger_explicit_target_test_rows": 213, "target_control_tests": 169,
            "cross_cutting_full_stack_scenarios": 44, "total_target_full_stack_tests": 213,
            "total_required_execution_records": 349,
        }
        c.check(counts == expected_counts, "Manifest counts are exact", counts)
        c.check(all(value in defaults for value in ("Available Inactive", "Preview Only", "PERM-P0 Disabled", "Off", "session_only", "Empty")), "Manifest records all safe defaults", defaults)


def check_modes(c: Checks, package: Path) -> None:
    symlinks: list[str] = []
    bad: list[str] = []
    for path in package.rglob("*"):
        relative = path.relative_to(package).as_posix()
        if path.is_symlink():
            symlinks.append(relative)
            continue
        mode = stat.S_IMODE(path.stat().st_mode)
        if path.is_dir():
            expected = 0o755
        else:
            expected = 0o755 if relative == "tools/verify-build-kit.py" or relative.endswith(".sh") or relative.endswith(".command") else 0o644
        if mode != expected:
            bad.append(f"{relative}:{oct(mode)} expected {oct(expected)}")
    c.check(not symlinks, "Package contains no symlinks", symlinks)
    if os.name == "nt":
        c.warn(
            "Package mode normalization is not enforceable on Windows",
            "Outer-ZIP mode metadata is still checked when --zip is supplied",
        )
        return
    c.check(not bad, "Package modes are normalized", bad[:20])


def check_outer_zip(c: Checks, package: Path, zip_path: Path) -> None:
    if not c.check(zip_path.is_file() and zip_path.stat().st_size > 0, "Final downloadable ZIP exists", zip_path):
        return
    root, archived = archive_files(c, zip_path, "Final downloadable ZIP")
    c.check(root == PACKAGE_NAME, "Final ZIP root name is exact", root)
    if root is None:
        return
    stripped = {name[len(root)+1:]: data for name, data in archived.items() if name.startswith(root + "/")}
    disk = files(package)
    c.check(set(stripped) == set(disk), "Final ZIP inventory equals release directory", {"missing": sorted(set(disk)-set(stripped)), "extra": sorted(set(stripped)-set(disk))})
    mismatch = [name for name in set(stripped) & set(disk) if stripped[name] != disk[name].read_bytes()]
    c.check(not mismatch, "Final ZIP bytes equal release directory", mismatch)
    try:
        with zipfile.ZipFile(zip_path) as archive:
            bad_modes: list[str] = []
            for info in archive.infolist():
                if info.is_dir():
                    continue
                relative = info.filename[len(root)+1:]
                mode = stat.S_IMODE((info.external_attr >> 16) & 0xFFFF)
                expected = 0o755 if relative == "tools/verify-build-kit.py" or relative.endswith(".sh") or relative.endswith(".command") else 0o644
                if mode != expected:
                    bad_modes.append(f"{relative}:{oct(mode)}")
            c.check(not bad_modes, "Final ZIP preserves normalized file modes", bad_modes[:20])
    except Exception as error:
        c.check(False, "Final ZIP mode check completes", error)


def summary(c: Checks) -> int:
    print("\nValidation summary")
    print(f"PASS={len(c.passed)} FAIL={len(c.failed)} WARN={len(c.warnings)}")
    if c.failed:
        print("Failures:")
        for failure in c.failed:
            print(f"- {failure}")
        return 1
    print("VERIFIED BUILD KIT — target application remains not operational until Hermes builds and executes the acceptance ledger.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--zip", dest="zip_path", type=Path)
    parser.add_argument("--pre-assembly", action="store_true")
    args = parser.parse_args(argv)
    package = args.package.resolve()
    c = Checks()
    c.check(package.is_dir(), "Package directory exists", package)
    if not package.is_dir():
        return summary(c)
    if not args.pre_assembly:
        c.check(package.name == PACKAGE_NAME, "Versioned package directory name is exact", package.name)
    check_required(c, package, args.pre_assembly)
    if args.pre_assembly:
        return summary(c)
    manifest = check_package_inventory(c, package)
    check_sources(c, package, manifest)
    check_domain(c, package)
    check_contracts(c, package, manifest)
    check_modes(c, package)
    zip_path = args.zip_path
    if zip_path is None and WORKSPACE is not None:
        candidate = WORKSPACE / "deliverables" / f"{PACKAGE_NAME}.zip"
        zip_path = candidate if candidate.exists() else None
    if zip_path is not None:
        check_outer_zip(c, package, zip_path.resolve())
    elif EXTRACTED:
        c.warn("Outer ZIP was not supplied; extracted directory was fully verified")
    else:
        c.warn("Outer ZIP was not found; release directory was fully verified")
    return summary(c)


if __name__ == "__main__":
    sys.exit(main())
