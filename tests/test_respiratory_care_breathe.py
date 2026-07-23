#!/usr/bin/env python3
"""Acceptance, safety, isolation, provenance, and packaging tests for BREATHE."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
BREATHE = ROOT / "respiratory-care"
PACKAGE = BREATHE / "packages" / "breathe"
SOURCE_PACK = PACKAGE / "Respiratory-Care-BREATHE-SuperPowers-Pack-v1.0"
DOWNLOADS = BREATHE / "downloads"
PROGRAM = PACKAGE / "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Respiratory-Care-Complete-AI-OS-with-BREATHE-SuperPowers-Setup-Guide.docx"
MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "breathe-respiratory-care-complete-edition.zip"
ZIP_PREFIX = "BREATHE-Respiratory-Care-Complete-Edition/"
BUILD_KIT = DOWNLOADS / "BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_ROOT = "BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0/"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BreatheRespiratoryCareTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_required_artifacts_and_archive_provenance(self):
        for path in (PROGRAM, GUIDE, DOCX, PACKAGE / "UPSTREAM-SHA256SUMS.txt"):
            self.assertTrue(path.is_file(), path)
        package_readme = (PACKAGE / "README.md").read_text(encoding="utf-8")
        self.assertIn("`PACKAGE-CHECKSUMS.sha256`", package_readme)
        self.assertIn("`UPSTREAM-SHA256SUMS.txt`", package_readme)
        self.assertNotIn("`SHA256SUMS.txt`", package_readme)
        archive = self.manifest["source_archive"]
        self.assertEqual(archive["sha256"], "7fc1d4b0a8dec362bcd41e5e049b1498d70fc2cbfd9d0348f5d7b240172f2edb")
        self.assertEqual(archive["bytes"], 317428)
        self.assertEqual(archive["members"], 23)
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        self.assertEqual(len(records), 23)
        expected_key_sources = {
            PROGRAM.name: (
                "63821c41bd20b34edd7245d2eb640d695b7a80b33e0586893a8387e444d813bb",
                "0250340ba2b1603d84c56603f7271ac6531e20cb6979bc2a0e25d62ab896406a",
            ),
            GUIDE.name: (
                "1ff712f65a167c812b66e32cfa4d588be247617506640772da349592c2e988ff",
                "f80690b24eacbe2b2724119107be78e887b166115ea95ebdef19f84e3ec33cbd",
            ),
            DOCX.name: (
                "d2bf6752d59cffb0ca772a0387326a7fb918dc846bc14a080b86fc7ea90ae8dc",
                "d2bf6752d59cffb0ca772a0387326a7fb918dc846bc14a080b86fc7ea90ae8dc",
            ),
        }
        for name, (upstream, packaged) in expected_key_sources.items():
            self.assertEqual(records[name]["upstream_sha256"], upstream)
            self.assertEqual(records[name]["source_sha256"], packaged)
            self.assertEqual(sha256(PACKAGE / name), packaged)
            self.assertEqual((PACKAGE / name).stat().st_size, records[name]["bytes"])

    def test_markdown_normalization_and_embedded_source_parity(self):
        markdown = list(PACKAGE.rglob("*.md"))
        self.assertEqual(len(markdown), 22)
        for path in markdown:
            text = path.read_text(encoding="utf-8")
            self.assertFalse(any(line.endswith(" ") for line in text.splitlines()), path)
            self.assertNotRegex(text, r"(?m)^    (?:#|\|)")
        records = self.manifest["source_files"]
        normalized = [item for item in records if item["transformation"].startswith("replaced supplied Markdown")]
        self.assertEqual(len(normalized), 7)
        markers = re.findall(r"^<!-- BEGIN EMBEDDED COMPONENT: (.+) -->$", self.program, re.MULTILINE)
        self.assertEqual(len(markers), 17)
        self.assertEqual(len(set(markers)), 17)
        for relative in markers:
            start = f"<!-- BEGIN EMBEDDED COMPONENT: {relative} -->"
            end = f"<!-- END EMBEDDED COMPONENT: {relative} -->"
            segment = self.program.split(start, 1)[1].split(end, 1)[0].strip("\n")
            source = (SOURCE_PACK / relative).read_text(encoding="utf-8").strip("\n")
            self.assertEqual(segment, source, relative)

    def test_power_workflow_template_schema_and_agent_inventories(self):
        powers = sorted({int(x) for x in re.findall(r"^## Power (\d+)\b", self.program, re.MULTILINE)})
        self.assertEqual(powers, list(range(1, 25)))
        workflow_text = (SOURCE_PACK / "workflows" / "BREATHE-Workflows-Launch-and-Adoption-Plan.md").read_text(encoding="utf-8")
        workflows = [int(x) for x in re.findall(r"^### WF-(\d{2})\b", workflow_text, re.MULTILINE)]
        self.assertEqual(workflows, list(range(1, 25)))
        templates_text = (SOURCE_PACK / "templates" / "BREATHE-Cards-and-Templates.md").read_text(encoding="utf-8")
        templates = [int(x) for x in re.findall(r"^## Template (\d+)\b", templates_text, re.MULTILINE)]
        self.assertEqual(templates, list(range(1, 31)))
        foundation = (SOURCE_PACK / "foundation" / "Respiratory-Care-Life-Practice-and-Professional-Foundation.md").read_text(encoding="utf-8")
        schema_section = foundation.split("## Eighteen professional-owned record schemas", 1)[1].split("## Canonical Source Watch registry", 1)[0]
        schemas = re.findall(r"^\| `([^`]+)` \|", schema_section, re.MULTILINE)
        self.assertEqual(len(schemas), 18)
        self.assertEqual(len(set(schemas)), 18)
        agents = re.findall(r"^- \*\*AGT-(\d{2}):.*PERM-P0 Disabled", workflow_text, re.MULTILINE)
        self.assertEqual(agents, [f"{i:02d}" for i in range(1, 11)])

    def test_reviewed_data_approval_and_agent_contracts_are_representable(self):
        workflow = (SOURCE_PACK / "workflows" / "BREATHE-Workflows-Launch-and-Adoption-Plan.md").read_text(encoding="utf-8")
        templates = (SOURCE_PACK / "templates" / "BREATHE-Cards-and-Templates.md").read_text(encoding="utf-8")
        agent_powers = (SOURCE_PACK / "breathe" / "07-E-Engineer-Ethical-Agents.md").read_text(encoding="utf-8")
        lane = (SOURCE_PACK / "core" / "00-Standalone-Respiratory-Care-Lane-and-Human-Standard.md").read_text(encoding="utf-8")

        headers = re.findall(r"^\*\*Common header:\*\* (.+)$", templates, re.MULTILINE)
        self.assertEqual(len(headers), 30)
        for header in headers:
            for field in ("fact-versus-interpretation", "human decision owner", "status"):
                self.assertIn(field, header)

        receipts = re.findall(r"^\*\*Completion receipt:\*\* (.+)$", workflow, re.MULTILINE)
        self.assertEqual(len(receipts), 24)
        for receipt in receipts:
            for field in ("named approver", "approval scope", "approval timestamp", "receipt ID", "approved artifact/version"):
                self.assertIn(field, receipt)

        wf04 = workflow.split("### WF-04", 1)[1].split("### WF-05", 1)[0]
        self.assertIn("whole_life_private", wf04)
        self.assertIn("institution-managed BREATHE Private mode rejects", wf04)

        wf22 = workflow.split("### WF-22", 1)[1].split("### WF-23", 1)[0]
        self.assertIn("apply ORBIT once", wf22)
        self.assertIn("add CIRCLE only", wf22)
        self.assertNotIn("or ORBIT for a named agent", wf22)

        tpl28 = templates.split("## Template 28", 1)[1].split("## Template 29", 1)[0]
        for field in ("Agent sequence", "Permission intersection", "transfer contracts", "Disagreement", "Named human review order", "Failure, containment", "Termination, kill"):
            self.assertIn(field, tpl28)
        self.assertIn("completed `TPL-28` Multi-Agent Sequence Map", agent_powers)
        self.assertIn("Powers 22–24 remain `Available Inactive`", lane)
        self.assertIn("associated suggested agents remain `PERM-P0 Disabled`", lane)

    def test_declared_release_checks_are_exact_unique_and_not_claimed_as_executed(self):
        release = (SOURCE_PACK / "tests" / "BREATHE-Release-Assurance.md").read_text(encoding="utf-8")
        ids = re.findall(r"^- \[ \] \*\*(RA-(?:[A-R]\d{2}|INT\d{2}))\b", release, re.MULTILINE)
        self.assertEqual(len(ids), 160)
        self.assertEqual(len(set(ids)), 160)
        self.assertEqual(len([x for x in ids if not x.startswith("RA-INT")]), 144)
        self.assertEqual([x for x in ids if x.startswith("RA-INT")], [f"RA-INT{i:02d}" for i in range(1, 17)])
        self.assertIn("They do **not** prove the checks ran in a respiratory professional's environment", self.read_first)
        self.assertIn("not evidence that all scenarios ran in a respiratory professional's environment", (BREATHE / "index.html").read_text(encoding="utf-8"))

    def test_standalone_identity_and_no_cross_population_state(self):
        self.assertEqual(self.manifest["population_lane"], "respiratory_care")
        self.assertEqual(self.manifest["route"], "/respiratory-care/")
        self.assertEqual(self.manifest["namespace"], "resp_breathe.*")
        self.assertEqual(self.manifest["respiratory_home"], "My BREATHE")
        self.assertTrue(self.manifest["standalone_non_nurse_lane"])
        self.assertFalse(self.manifest["nursing_population_state_shared"])
        self.assertFalse(self.manifest["medical_resident_population_state_shared"])
        for phrase in (
            "adjacent, standalone respiratory-care lane",
            "not a nursing role",
            "ROUNDS extension",
            "If isolation cannot be proven, installation must stop before mutation",
        ):
            self.assertIn(phrase, self.read_first)
        nurse_manifest = json.loads((ROOT / "post-setup" / "downloads" / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("BREATHE", json.dumps(nurse_manifest))
        self.assertNotIn("respiratory_care", json.dumps(nurse_manifest))
        setup_model = (ROOT / "setup-helper" / "setup-helper-model.mjs").read_text(encoding="utf-8")
        self.assertNotIn("respiratory_care", setup_model)
        rounds_manifest = (ROOT / "medical-residents" / "packages" / "rounds" / "ROLE-PACK.json").read_text(encoding="utf-8")
        self.assertNotIn("resp_breathe", rounds_manifest)

    def test_preinstall_consent_and_installation_order(self):
        for phrase in (
            "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
            "allows a read-only owner, target, isolation, role, credential",
            "reviews the exact combined BREATHE Activation Card",
            "Silence, timeout, download, title, credential",
            "create S0 and the rollback snapshot",
            "run 72 foundation-domain checks and issue S1",
            "issue S2",
            "72 BREATHE-domain checks plus 16 integration checks",
        ):
            self.assertIn(phrase, self.read_first)
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["breathe_overlay_second"])
        self.assertFalse(self.manifest["install_on_download"])
        self.assertIn("exact complete-program SHA-256 digest", self.program)
        self.assertIn("Any program-byte, policy, target or card change after approval invalidates that approval", self.program)

    def test_emergencies_leave_breathe_instead_of_creating_a_gate_state(self):
        templates = (SOURCE_PACK / "templates" / "BREATHE-Cards-and-Templates.md").read_text(encoding="utf-8")
        self.assertNotIn("emergency bypass", templates)
        self.assertNotIn("emergency bypass", self.program)
        self.assertIn("An emergency is never a BREATHE gate state", templates)
        self.assertIn("emergencies leave BREATHE for official procedures", templates)

    def test_safe_defaults_device_and_clinical_authority_boundaries(self):
        for key in (
            "automatic_connectors", "automatic_cron", "automatic_device_access", "automatic_external_actions",
            "automatic_memory", "automatic_shared_access", "clinical_decisions", "device_control",
            "device_data_private_use", "live_patient_specific_private_use", "role_selection_verifies_credentials_or_authority",
        ):
            self.assertFalse(self.manifest[key], key)
        self.assertTrue(self.manifest["no_phi"])
        self.assertEqual(self.manifest["optional_superpowers_active_after_install"], 0)
        self.assertEqual(self.manifest["suggested_agents_active_after_install"], 0)
        for phrase in (
            "no device, monitor, ventilator, oxygen, alarm, network, or clinical-system connection or control",
            "no autonomous diagnosis, triage, therapy selection",
            "Immediate deterioration, airway or device hazards",
            "Removing names is not sufficient de-identification",
        ):
            self.assertIn(phrase, self.read_first)

    def test_institutional_mode_and_assurance_nonclaims(self):
        self.assertTrue(self.manifest["institutional_deployment_requires_separate_authorization"])
        for phrase in (
            "This download does not create, connect, approve, certify, or validate such an environment",
            "A private BREATHE approval does not authorize hospital deployment",
            "clinical validation, HIPAA compliance, accreditation, certification, institutional approval",
            "device safety",
        ):
            self.assertIn(phrase, self.read_first)

    def test_docx_has_no_macros_embedded_objects_or_external_relationships(self):
        with zipfile.ZipFile(DOCX) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            lowered = [name.lower() for name in names]
            self.assertFalse(any(
                "vbaproject" in name or "activex" in name or "embeddings/" in name or "oleobject" in name
                for name in lowered
            ))
            for name in names:
                if name.endswith(".rels"):
                    rels = archive.read(name).decode("utf-8", errors="replace")
                    self.assertNotIn('TargetMode="External"', rels)

    def test_public_scanner_reads_zip_docx_and_nested_text_members(self):
        scanner = runpy.run_path(str(ROOT / "scripts" / "scan-public-healthcare-artifacts.py"))
        scan_paths = scanner["scan_paths"]
        scanner["run_self_probes"]()
        with tempfile.TemporaryDirectory() as tmp:
            docx = Path(tmp) / "unsafe.docx"
            with zipfile.ZipFile(docx, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("word/document.xml", "<w:t>MRN number=A1B2C3</w:t>")
            findings = scan_paths([docx])
            self.assertTrue(any(label == "patient or mrn example" for label, _ in findings))

    def test_public_page_contract_and_separate_route(self):
        page = (BREATHE / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Standalone adjacent clinical lane · Respiratory care professionals",
            "Respiratory care means separate—not absorbed",
            "No PHI or real cases",
            "No device data or control",
            "24 powers inactive",
            "10 agents disabled",
            "424 required execution records",
            "Download ≠ build, activation, operation, or authorization",
            "Give the ZIP to your own Hermes",
            "BREATHE Implementation Activation Card",
            "AI prepares. Respiratory professionals verify and escalate. Authorized humans decide",
        ):
            self.assertIn(phrase, page)
        self.assertIn('href="downloads/BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"', page)
        self.assertIn('href="downloads/breathe-respiratory-care-complete-edition.zip"', page)
        self.assertIn('href="packages/breathe/UPSTREAM-SHA256SUMS.txt"', page)

    def test_homepage_promotes_rt_story_to_adjacent_lane_after_rounds(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        video_region = page.split("<!-- ============ HOMEPAGE SHORT", 1)[1].split("<!-- ============ ROLE CARDS", 1)[0]
        ordered_ids = ["79xHeOuH_1k", "M-dIPB-pSp0", "8FvTTp-sZVk", "W1eOXb-l2EI", "ZE9pg_vnL8g", "InXb8EN9Hcs", "MKKx9Ie6GmY"]
        positions = [video_region.index(video_id) for video_id in ordered_ids]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(video_region.count("MKKx9Ie6GmY"), 1)
        rt = video_region.split('class="home-rt-video"', 1)[1]
        self.assertIn("Adjacent clinical lane · Respiratory care professionals", rt)
        self.assertIn("BREATHE — Respiratory Care Mission Control Build Kit", rt)
        self.assertIn("Download/unzip does nothing", rt)
        self.assertIn("https://www.youtube-nocookie.com/embed/MKKx9Ie6GmY", rt)
        self.assertIn('loading="lazy"', rt)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', rt)
        self.assertIn("allowfullscreen", rt)
        self.assertIn('href="respiratory-care/"', rt)

    def test_upstream_and_package_ledgers_are_exact(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        namespace["validate_upstream_ledger"]()
        expected = namespace["EXPECTED_FILES"] - {"PACKAGE-CHECKSUMS.sha256"}
        ledger = namespace["parse_ledger"]("PACKAGE-CHECKSUMS.sha256", expected)
        self.assertEqual(set(ledger), expected)
        for name, digest in ledger.items():
            self.assertEqual(sha256(PACKAGE / name), digest)

    def test_public_manifest_checksum_and_zip_bytes(self):
        public = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(public["packages"]), 2)
        record = next(p for p in public["packages"] if p["artifact_class"] == "legacy_complete_edition_source_package")
        kit = next(p for p in public["packages"] if p["artifact_class"] == "hermes_functional_build_kit_self_install")
        self.assertEqual(public["installation_status"], "not_installed")
        self.assertEqual(public["release_posture"], "source_package_available_build_kit_available_runtime_not_operational_until_user_approved_build")
        self.assertEqual(record["sha256"], sha256(ZIP))
        self.assertEqual(record["bytes"], ZIP.stat().st_size)
        self.assertEqual(record["acceptance_tests"]["total"], 160)
        self.assertFalse(record["nursing_population_state_shared"])
        self.assertFalse(record["medical_resident_population_state_shared"])
        self.assertFalse(record["device_control"])
        self.assertTrue(kit["activation_available"])
        self.assertEqual(kit["activation_contract"], "user_initiated_read_only_preflight_then_exact_implementation_activation_card_approval")
        self.assertFalse(kit["install_on_download"])
        self.assertFalse(kit["institutional_authorization"])
        self.assertFalse(kit["operational_data_authorized"])
        self.assertTrue(kit["pre_install_disclosure_required"])
        self.assertEqual(kit["complete_ai_os_claim"], "not_operational_build_required")
        self.assertEqual(kit["runtime_status"], "not_built_until_user_hermes_runs_approved_program")
        self.assertEqual(kit["readiness"], "not_operational_build_required")
        self.assertEqual(kit["total_required_execution_records"], 424)
        self.assertEqual(kit["sha256"], sha256(BUILD_KIT))
        self.assertEqual(kit["bytes"], BUILD_KIT.stat().st_size)
        checksum = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertEqual(checksum, f"{sha256(ZIP)}  {ZIP.name}\n{sha256(BUILD_KIT)}  {BUILD_KIT.name}\n")
        with zipfile.ZipFile(ZIP) as archive:
            package_files = {p.relative_to(PACKAGE).as_posix() for p in PACKAGE.rglob("*") if p.is_file()}
            expected = {ZIP_PREFIX + name for name in package_files}
            self.assertEqual(set(archive.namelist()), expected)
            self.assertEqual(len(expected), 26)
            self.assertIsNone(archive.testzip())
            for info in archive.infolist():
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.date_time, (2026, 7, 16, 0, 0, 0))
                self.assertEqual(info.external_attr >> 16, 0o100644)
            for path in PACKAGE.rglob("*"):
                if path.is_file():
                    self.assertEqual(archive.read(ZIP_PREFIX + path.relative_to(PACKAGE).as_posix()), path.read_bytes())

    def test_self_install_build_kit_is_pinned_and_not_operational(self):
        self.assertEqual(sha256(BUILD_KIT), "896394e5a6ed63de5342281edc9e5d96cbbca86c94f632a902214d31261a0e22")
        self.assertEqual(BUILD_KIT.stat().st_size, 6966473)
        with zipfile.ZipFile(BUILD_KIT) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.infolist()), 151)
            names = archive.namelist()
            self.assertTrue(all(name.startswith(BUILD_KIT_ROOT) for name in names))
            self.assertIn(BUILD_KIT_ROOT + "README-FIRST.md", names)
            self.assertIn(BUILD_KIT_ROOT + "GIVE-THIS-PACKAGE-TO-HERMES.md", names)
            self.assertIn(BUILD_KIT_ROOT + "RELEASE-MANIFEST.json", names)
            self.assertIn(BUILD_KIT_ROOT + "SHA256SUMS.txt", names)
            self.assertIn(BUILD_KIT_ROOT + "tools/verify-build-kit.py", names)
            executable = BUILD_KIT_ROOT + "tools/verify-build-kit.py"
            for info in archive.infolist():
                expected_mode = 0o100755 if info.filename == executable else 0o100644
                self.assertEqual(info.external_attr >> 16, expected_mode, info.filename)
            manifest = json.loads(archive.read(BUILD_KIT_ROOT + "RELEASE-MANIFEST.json"))
            handoff = archive.read(BUILD_KIT_ROOT + "GIVE-THIS-PACKAGE-TO-HERMES.md").decode("utf-8")
            read_first = archive.read(BUILD_KIT_ROOT + "README-FIRST.md").decode("utf-8")
        self.assertEqual(manifest["target"]["lane"], "respiratory_care")
        self.assertEqual(manifest["target"]["namespace"], "resp_breathe.*")
        self.assertEqual(manifest["target"]["readiness"], "not_operational_build_required")
        self.assertEqual(manifest["counts"]["total_required_execution_records"], 424)
        self.assertEqual(manifest["counts"]["canonical_assurance_checks"], 160)
        self.assertEqual(manifest["defaults"]["agents"], "PERM-P0 Disabled")
        self.assertEqual(manifest["defaults"]["powers"], "Available Inactive")
        self.assertEqual(manifest["defaults"]["external_actions"], "Off")
        self.assertEqual(manifest["defaults"]["memory"], "session_only")
        for phrase in (
            "Perform only the read-only preflight first",
            "read-only preflight",
            "Implementation Activation Card",
            "Stop for exact approval",
            "Do not use PHI, real-case content",
            "Keep connectors, external actions, new memory, schedules, tools, agents and background automation off",
            "Not operational",
        ):
            self.assertIn(phrase, handoff + read_first)

    def test_builder_tracks_build_kit_with_independent_validator(self):
        builder = (ROOT / "scripts" / "build-respiratory-care-breathe.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "respiratory-care-breathe.yml").read_text(encoding="utf-8")
        for phrase in (
            "build_build_kit_zip",
            "BUILD_KIT_SOURCE",
            "validate_build_kit",
            "validate_build_kit_zip_structure",
            "run_bundled_build_kit_verifier",
            "BREATHE bundled verifier bytes changed",
            "Case/Unicode-colliding BREATHE build-kit ZIP member",
            "BREATHE build-kit ZIP mode mismatch",
            "CRC verification reads payloads",
            "os.replace(candidate, output)",
            "BUILD_KIT_VERIFIER_SHA256",
        ):
            self.assertIn(phrase, builder)
        for phrase in (
            "actions/checkout@34e114876b0b11c390a56381ad16ebd13914f8d5",
            "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
            "jsonschema[format]==4.25.1",
            "python3 -m unittest discover -s tests -p 'test_*.py'",
            "git ls-files --error-unmatch respiratory-care/downloads/BREATHE-Respiratory-Care-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip",
            "test -z \"$(git status --porcelain --untracked-files=all)\"",
        ):
            self.assertIn(phrase, workflow)

    def test_bundled_build_kit_verifier_runs_against_package_and_zip(self):
        verifier = ROOT / "respiratory-care" / "build-kit" / BUILD_KIT_ROOT.strip("/") / "tools" / "verify-build-kit.py"
        package = ROOT / "respiratory-care" / "build-kit" / BUILD_KIT_ROOT.strip("/")
        completed = subprocess.run(
            [sys.executable, str(verifier), "--package", str(package), "--zip", str(BUILD_KIT)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout[-4000:])
        self.assertIn("VERIFIED BREATHE RESPIRATORY CARE BUILD KIT", completed.stdout)

    def test_bundled_verifier_rejects_metadata_before_crc_reads(self):
        verifier_path = BREATHE / "build-kit" / BUILD_KIT_ROOT.strip("/") / "tools/verify-build-kit.py"
        verifier = runpy.run_path(str(verifier_path))
        archive_analysis = verifier["archive_analysis"]
        package_root = BUILD_KIT_ROOT.strip("/")

        def regular(name: str) -> zipfile.ZipInfo:
            info = zipfile.ZipInfo(name)
            info.create_system = 3
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            info.file_size = 1
            info.compress_size = 1
            return info

        class MetadataOnlyArchive:
            def __init__(self, infos):
                self.infos = infos
                self.payload_touched = False

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def infolist(self):
                return self.infos

            def testzip(self):
                self.payload_touched = True
                return None

        cases = []
        raw = regular(f"{package_root}/safe.txt")
        raw.orig_filename = f"{package_root}/safe.txt\x00hidden"
        cases.append([raw])
        encrypted = regular(f"{package_root}/encrypted.txt")
        encrypted.flag_bits |= 1
        cases.append([encrypted])
        compression = regular(f"{package_root}/compression.txt")
        compression.compress_type = zipfile.ZIP_BZIP2
        cases.append([compression])
        oversized = regular(f"{package_root}/oversized.txt")
        oversized.file_size = verifier["ARCHIVE_MAX_MEMBER_BYTES"] + 1
        cases.append([oversized])
        mode_zero = regular(f"{package_root}/mode-zero.txt")
        mode_zero.external_attr = 0
        cases.append([mode_zero])
        unexpected_executable = regular(f"{package_root}/unexpected-executable.txt")
        unexpected_executable.external_attr = 0o100755 << 16
        cases.append([unexpected_executable])
        cases.append([regular(f"{package_root}/../escape.txt")])
        cases.append([regular(f"{package_root}/duplicate.txt"), regular(f"{package_root}/duplicate.txt")])
        cases.append([regular(f"{package_root}/Case.txt"), regular(f"{package_root}/case.txt")])
        cases.append([regular(f"{package_root}/prefix"), regular(f"{package_root}/prefix/child.txt")])

        for infos in cases:
            fake = MetadataOnlyArchive(infos)
            with self.subTest(names=[getattr(info, "orig_filename", info.filename) for info in infos]):
                with mock.patch.object(zipfile, "ZipFile", return_value=fake):
                    _, errors, duplicates, collisions, _, symlinks = archive_analysis(Path("untrusted.zip"))
                self.assertTrue(errors or duplicates or collisions or symlinks)
                self.assertFalse(fake.payload_touched)
    def test_build_kit_metadata_is_rejected_before_crc_or_payload_reads(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        validator = namespace["validate_build_kit_zip_structure"]
        with zipfile.ZipFile(BUILD_KIT) as source:
            baseline = [copy.copy(info) for info in source.infolist()]

        class MetadataOnlyArchive:
            def __init__(self, infos):
                self.infos = infos
                self.payload_accessed = False

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def infolist(self):
                return self.infos

            def testzip(self):
                self.payload_accessed = True
                raise AssertionError("CRC read occurred before metadata rejection")

            def read(self, _name):
                self.payload_accessed = True
                raise AssertionError("payload read occurred before metadata rejection")

        def set_name(info, name):
            info.filename = name
            info.orig_filename = name

        def raw_nul(infos):
            infos[0].orig_filename = infos[0].filename + "\x00suffix"

        def raw_noncanonical(infos):
            infos[0].orig_filename = infos[0].filename.replace("/", "//", 1)

        def repeated_terminal_slash(infos):
            set_name(infos[0], BUILD_KIT_ROOT.rstrip("/") + "/noncanonical//")

        def backslash(infos):
            set_name(infos[0], infos[0].filename.replace("/", "\\", 1))

        def absolute(infos):
            set_name(infos[0], "/" + infos[0].filename)

        def drive_prefix(infos):
            set_name(infos[0], "C:/" + infos[0].filename)

        def duplicate(infos):
            set_name(infos[1], infos[0].filename)

        def unicode_collision(infos):
            set_name(infos[0], BUILD_KIT_ROOT.rstrip("/") + "/collision-é.txt")
            set_name(infos[1], BUILD_KIT_ROOT.rstrip("/") + "/collision-e\u0301.txt")

        def file_directory_collision(infos):
            set_name(infos[0], BUILD_KIT_ROOT.rstrip("/") + "/collision")
            set_name(infos[1], BUILD_KIT_ROOT.rstrip("/") + "/collision/child")

        def directory_entry(infos):
            set_name(infos[0], BUILD_KIT_ROOT.rstrip("/") + "/directory/")
            infos[0].external_attr = (0o040000 | 0o755) << 16

        def missing_file_type(infos):
            infos[0].external_attr = 0o644 << 16

        def special_file(infos):
            infos[0].external_attr = (0o140000 | 0o644) << 16

        def privileged_world_writable(infos):
            infos[0].external_attr = (0o100000 | 0o4000 | 0o777) << 16

        def unexpected_executable(infos):
            info = next(item for item in infos if item.filename not in namespace["BUILD_KIT_EXECUTABLE_MEMBERS"])
            info.external_attr = (0o100000 | 0o755) << 16

        def expected_executable_not_executable(infos):
            info = next(item for item in infos if item.filename in namespace["BUILD_KIT_EXECUTABLE_MEMBERS"])
            info.external_attr = (0o100000 | 0o644) << 16

        def encrypted(infos):
            infos[0].flag_bits |= 1

        def unsupported_compression(infos):
            infos[0].compress_type = 99

        def oversized_member(infos):
            infos[0].file_size = namespace["BUILD_KIT_MAX_MEMBER_BYTES"] + 1

        def expanded_limit(infos):
            for info in infos:
                info.file_size = 2 * 1024 * 1024

        cases = {
            "raw-nul": raw_nul,
            "raw-noncanonical": raw_noncanonical,
            "repeated-terminal-slash": repeated_terminal_slash,
            "backslash": backslash,
            "absolute": absolute,
            "drive-prefix": drive_prefix,
            "duplicate": duplicate,
            "unicode-collision": unicode_collision,
            "file-directory-collision": file_directory_collision,
            "directory-entry": directory_entry,
            "missing-file-type": missing_file_type,
            "special-file": special_file,
            "privileged-world-writable": privileged_world_writable,
            "unexpected-executable": unexpected_executable,
            "expected-executable-not-executable": expected_executable_not_executable,
            "encrypted": encrypted,
            "unsupported-compression": unsupported_compression,
            "oversized-member": oversized_member,
            "expanded-limit": expanded_limit,
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                infos = [copy.copy(info) for info in baseline]
                mutate(infos)
                fake = MetadataOnlyArchive(infos)
                with mock.patch.object(namespace["zipfile"], "ZipFile", return_value=fake):
                    with self.assertRaises(ValueError):
                        validator(BUILD_KIT, enforce_pins=False)
                self.assertFalse(fake.payload_accessed, label)

    def test_failed_staged_candidate_cannot_replace_governed_output(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        before = BUILD_KIT.read_bytes()
        original = namespace["run_bundled_build_kit_verifier"]

        def reject(_candidate=None):
            raise ValueError("forced verifier rejection")

        namespace["build_build_kit_zip"].__globals__["run_bundled_build_kit_verifier"] = reject
        try:
            with self.assertRaisesRegex(ValueError, "forced verifier rejection"):
                namespace["build_build_kit_zip"]()
        finally:
            namespace["build_build_kit_zip"].__globals__["run_bundled_build_kit_verifier"] = original
        self.assertEqual(BUILD_KIT.read_bytes(), before)
        self.assertEqual(list(DOWNLOADS.glob(f".{BUILD_KIT.name}.*.candidate")), [])

    def test_builder_rejects_source_wrapper_and_ledger_tampering(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        validator = namespace["validate_package"]
        targets = (PROGRAM.name, "00-READ-FIRST.md", "PACKAGE-CHECKSUMS.sha256")
        for target in targets:
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                copied = Path(temp) / "breathe"
                shutil.copytree(PACKAGE, copied)
                with (copied / target).open("ab") as handle:
                    handle.write(b"\nTAMPER")
                validator.__globals__["PACKAGE"] = copied
                with self.assertRaises(ValueError):
                    validator()
        validator.__globals__["PACKAGE"] = PACKAGE

    def test_ledger_parser_rejects_parent_backslash_and_duplicate_paths(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        parser = namespace["parse_ledger"]
        with tempfile.TemporaryDirectory() as temp:
            copied = Path(temp) / "breathe"
            copied.mkdir()
            parser.__globals__["PACKAGE"] = copied
            cases = {
                "parent": "0" * 64 + "  ../escape\n",
                "backslash": "0" * 64 + "  nested\\escape\n",
                "duplicate": "0" * 64 + "  same\n" + "1" * 64 + "  same\n",
            }
            for label, content in cases.items():
                with self.subTest(label=label):
                    (copied / "ledger").write_text(content, encoding="utf-8")
                    with self.assertRaises(ValueError):
                        parser("ledger", {"same"})
        parser.__globals__["PACKAGE"] = PACKAGE

    def test_deterministic_builder_reproduces_committed_zip(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-respiratory-care-breathe.py"))
        build = namespace["build"]
        before = sha256(ZIP)
        record = build()
        self.assertEqual(record["sha256"], sha256(BUILD_KIT))
        self.assertEqual(sha256(ZIP), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
