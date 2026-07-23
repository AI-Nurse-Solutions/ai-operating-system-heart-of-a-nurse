#!/usr/bin/env python3
"""Acceptance, safety, isolation, and packaging tests for ROUNDS."""

from __future__ import annotations

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
from unittest import mock
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROUNDS = ROOT / "medical-residents"
PACKAGE = ROUNDS / "packages" / "rounds"
DOWNLOADS = ROUNDS / "downloads"
PROGRAM = PACKAGE / "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Medical-Resident-Complete-AI-OS-with-ROUNDS-SuperPowers-Setup-Guide.docx"
MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "medical-resident-rounds-complete-edition.zip"
ZIP_PREFIX = "ROUNDS-Medical-Resident-Complete-Edition/"
BUILD_KIT = DOWNLOADS / "ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_ROOT = "ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0/"
BUILD_KIT_SOURCE = ROUNDS / "build-kit" / BUILD_KIT_ROOT.rstrip("/")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RoundsMedicalResidentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    def test_required_artifacts_and_source_provenance(self):
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        expected = {
            PROGRAM.name: "33a8e8dbd963bb21d21582d520f3d98c161ed7b900a9cdfa7a13df1039da365c",
            GUIDE.name: "bff68f996a605dc71c92609b6e20d4d5e1a1a95a24b92c84c3dfad7f746bc0f9",
            DOCX.name: "a0c4483ca3b51d0597db52b8c32c5dcc93e9916ae2374277b1962f1832f50d4b",
        }
        for path in (PROGRAM, GUIDE, DOCX):
            self.assertTrue(path.is_file(), path)
            self.assertEqual(records[path.name]["bytes"], path.stat().st_size)
            self.assertEqual(records[path.name]["source_sha256"], expected[path.name])
            self.assertEqual(sha256(path), expected[path.name])

        program_record = records[PROGRAM.name]
        self.assertEqual(
            program_record["upstream_sha256"],
            "63524f871de3a28842d04e936b7bce7bd2b3a76724f08222179a7a8c7365d35e",
        )
        self.assertIn("trailing-space hard breaks", program_record["transformation"])
        self.assertIn("four-space indentation", program_record["transformation"])
        self.assertFalse(any(line.endswith(" ") for line in self.program.splitlines()))
        self.assertNotRegex(self.program, r"(?m)^    (?:##|\|)")

    def test_markdown_normalization_is_renderable_and_provenanced(self):
        record = next(item for item in self.manifest["source_files"] if item["packaged_path"] == GUIDE.name)
        self.assertEqual(record["upstream_sha256"], "5afbd0e56253167d6fe4247aaa081b520d648a232af98e212c0f2a355d2e4ead")
        self.assertIn("four-space indentation", record["transformation"])
        self.assertIn("trailing-space hard breaks", record["transformation"])
        self.assertTrue(self.guide.startswith("# ROUNDS — Medical Resident Complete AI OS\n"))
        self.assertNotRegex(self.guide, r"(?m)^    #")
        self.assertFalse(any(line.endswith(" ") for line in self.guide.splitlines()))
        self.assertIn("## Installation phases", self.guide)
        self.assertIn("| Phase | What Hermes does | Receipt or result |", self.guide)

    def test_program_embeds_exact_component_inventory(self):
        markers = re.findall(r"^<!-- BEGIN EMBEDDED COMPONENT: (.+) -->$", self.program, re.MULTILINE)
        self.assertEqual(len(markers), 16)
        self.assertEqual(len(set(markers)), 16)
        for required in (
            "foundation/Medical-Resident-Life-Training-and-Practice-Foundation.md",
            "core/00-Standalone-Medical-Resident-Lane-and-Human-Standard.md",
            "core/01-Resident-Patient-Training-and-Institution-Trust-Shield.md",
            "core/02-ROUNDS-ATTEND-CIRCLE-ORBIT-Operating-Core.md",
            "workflows/My-ROUNDS-Resident-Command-Center.md",
            "tests/ROUNDS-Release-Assurance.md",
            "manifest.md",
        ):
            self.assertIn(required, markers)
            self.assertIn(f"<!-- END EMBEDDED COMPONENT: {required} -->", self.program)

    def test_declared_release_checks_are_exact_and_unique(self):
        release = self.program.split("<!-- BEGIN EMBEDDED COMPONENT: tests/ROUNDS-Release-Assurance.md -->", 1)[1]
        release = release.split("<!-- END EMBEDDED COMPONENT: tests/ROUNDS-Release-Assurance.md -->", 1)[0]
        ids = re.findall(r"^- \[ \] \*\*([A-R]\d+|INT\d+)\b", release, re.MULTILINE)
        self.assertEqual(len(ids), 160)
        self.assertEqual(len(set(ids)), 160)
        self.assertEqual(len([x for x in ids if x[0] in "ABCDEFGHI" and not x.startswith("INT")]), 72)
        self.assertEqual(len([x for x in ids if x[0] in "JKLMNOPQR" and not x.startswith("INT")]), 72)
        self.assertEqual([x for x in ids if x.startswith("INT")], [f"INT{i:02d}" for i in range(1, 17)])
        self.assertEqual(
            self.manifest["acceptance_tests"],
            {"foundation": 72, "rounds_overlay": 72, "integration": 16, "total": 160},
        )

    def test_power_workflow_template_record_and_agent_inventories(self):
        powers = [int(x) for x in re.findall(r"^## Power (\d+)\b", self.program, re.MULTILINE)]
        # Each power appears once in the source component and once in the embedded manifest/program inventory.
        self.assertGreaterEqual(powers.count(1), 1)
        self.assertEqual(sorted(set(powers)), list(range(1, 25)))
        workflow_section = self.program.split("## Twenty-four ready-to-launch workflows", 1)[1].split("## Suggested software agents", 1)[0]
        workflows = re.findall(r"^(\d+)\. \*\*", workflow_section, re.MULTILINE)
        self.assertEqual(workflows, [str(i) for i in range(1, 25)])
        template_section = self.program.split("# ROUNDS Cards & Templates", 1)[1].split(
            "<!-- END EMBEDDED COMPONENT: templates/ROUNDS-Cards-and-Templates.md -->", 1
        )[0]
        templates = re.findall(r"^## Template (\d+)\b", template_section, re.MULTILINE)
        self.assertEqual(templates, [str(i) for i in range(1, 31)])
        foundation = self.program.split("## Foundation records", 1)[1].split("## Foundation workflows", 1)[0]
        self.assertEqual(len(re.findall(r"^- `([a-z_]+)`$", foundation, re.MULTILINE)), 17)
        agents = self.program.split("## Suggested software agents — all inactive", 1)[1].split(
            "## Seven-day safe launch", 1
        )[0]
        self.assertEqual(len(re.findall(r"^- [^\n]+ — P[123]\b", agents, re.MULTILINE)), 10)

    def test_standalone_non_nurse_identity_and_no_shared_state(self):
        self.assertEqual(self.manifest["population_lane"], "medical_resident")
        self.assertEqual(self.manifest["route"], "/medical-residents/")
        self.assertEqual(self.manifest["namespace"], "medres_rounds.*")
        self.assertTrue(self.manifest["standalone_non_nurse_lane"])
        self.assertFalse(self.manifest["nursing_population_state_shared"])
        for phrase in (
            "adjacent, standalone medical-resident lane",
            "not a nursing role",
            "It must not share a profile, dashboard state, records, schemas, memory, permissions, agents",
            "If isolation cannot be proven, installation must stop before mutation",
        ):
            self.assertIn(phrase, self.read_first)
        nurse_manifest = json.loads((ROOT / "post-setup" / "downloads" / "manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("ROUNDS", json.dumps(nurse_manifest))
        setup_model = (ROOT / "setup-helper" / "setup-helper-model.mjs").read_text(encoding="utf-8")
        self.assertNotIn("medical_resident", setup_model)

    def test_preinstall_consent_and_installation_order(self):
        for phrase in (
            "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
            "allows a read-only owner, target, isolation",
            "reviews the exact combined ROUNDS Activation Card",
            "Silence, timeout, download, role selection",
            "create S0 and the rollback snapshot",
            "run 72 foundation-domain checks and issue S1",
            "issue S2",
            "72 ROUNDS-domain checks plus 16 integration checks",
        ):
            self.assertIn(phrase, self.read_first)
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["rounds_overlay_second"])
        self.assertFalse(self.manifest["install_on_download"])

    def test_safe_defaults_and_authority_boundaries(self):
        for key in (
            "automatic_connectors",
            "automatic_cron",
            "automatic_external_actions",
            "automatic_memory",
            "automatic_shared_access",
            "clinical_decisions",
            "live_patient_specific_private_use",
            "role_selection_verifies_credentials_or_authority",
        ):
            self.assertFalse(self.manifest[key], key)
        self.assertEqual(self.manifest["optional_superpowers_active_after_install"], 0)
        self.assertEqual(self.manifest["suggested_agents_active_after_install"], 0)
        for phrase in (
            "No surveillance or autonomous decisions",
            "Immediate deterioration or safety concerns bypass ROUNDS",
            "AI cannot infer or change supervision, entrustment, competence",
            "Removing a name is not sufficient de-identification",
        ):
            self.assertIn(phrase, self.read_first)

    def test_institutional_mode_and_assurance_nonclaims(self):
        self.assertTrue(self.manifest["institutional_deployment_requires_separate_authorization"])
        for phrase in (
            "This download does not create, connect, approve, certify, or validate such an environment",
            "A private ROUNDS approval does not authorize hospital deployment",
            "They do **not** prove the checks ran in a resident's environment",
            "clinical validation, HIPAA compliance, accreditation, certification, institutional approval",
        ):
            self.assertIn(phrase, self.read_first)

    def test_docx_has_no_macros_embedded_objects_or_external_relationships(self):
        with zipfile.ZipFile(DOCX) as archive:
            self.assertIsNone(archive.testzip())
            names = archive.namelist()
            lowered = [name.lower() for name in names]
            self.assertFalse(any("vbaproject" in name or "activex" in name or "embeddings/" in name for name in lowered))
            for name in names:
                if name.endswith(".rels"):
                    rels = archive.read(name).decode("utf-8", errors="replace")
                    self.assertNotIn('TargetMode="External"', rels)

    def test_public_page_contract_and_separate_route(self):
        page = (ROUNDS / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Standalone adjacent clinical lane · Medical residents",
            "Non-nurse means separate—not absorbed",
            "24 powers inactive",
            "10 agents disabled",
            "160 assurance checks",
            "424 execution records",
            "Download ≠ build, activation, operation, or authorization",
            "Downloading, opening, or unzipping changes nothing",
            "Give this ZIP to your own Hermes",
            "Implementation Activation Card",
            "Not operational:",
            "AI prepares. Residents reason and escalate. Authorized humans decide",
        ):
            self.assertIn(phrase, page)
        self.assertIn('href="downloads/ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"', page)
        self.assertIn('href="downloads/medical-resident-rounds-complete-edition.zip"', page)
        self.assertIn('href="build-kit/ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0/README-FIRST.md"', page)
        self.assertNotIn('href="packages/rounds/00-READ-FIRST.md"', page)

    def test_homepage_embeds_resident_short_below_all_nurse_videos(self):
        page = (ROOT / "index.html").read_text(encoding="utf-8")
        video_region = page.split("<!-- ============ HOMEPAGE SHORT", 1)[1].split(
            "<!-- ============ ROLE CARDS", 1
        )[0]
        ordered_ids = [
            "79xHeOuH_1k",
            "M-dIPB-pSp0",
            "8FvTTp-sZVk",
            "W1eOXb-l2EI",
            "ZE9pg_vnL8g",
            "InXb8EN9Hcs",
            "MKKx9Ie6GmY",
        ]
        positions = [video_region.index(video_id) for video_id in ordered_ids]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(video_region.count("InXb8EN9Hcs"), 1)
        self.assertIn("Adjacent clinical lane · Medical residents", video_region)
        self.assertIn("Now everyone in the hospital has an AI OS", video_region)
        self.assertIn("For Medical Residents: ROUNDS", video_region)
        self.assertIn('class="home-resident-video"', video_region)
        self.assertIn('class="home-short-frame"', video_region.split("InXb8EN9Hcs", 1)[0])
        self.assertIn("https://www.youtube-nocookie.com/embed/InXb8EN9Hcs", video_region)
        self.assertIn('loading="lazy"', video_region)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', video_region)
        self.assertIn("allowfullscreen", video_region)
        self.assertIn('href="medical-residents/"', video_region)
        self.assertEqual(video_region.count("MKKx9Ie6GmY"), 1)
        self.assertIn("Adjacent clinical lane · Respiratory care professionals", video_region)
        self.assertIn("BREATHE — Respiratory Care Mission Control Build Kit", video_region)
        self.assertIn("Download/unzip does nothing", video_region)
        self.assertIn('class="home-rt-video"', video_region)
        self.assertIn("https://www.youtube-nocookie.com/embed/MKKx9Ie6GmY", video_region)
        rt_region = video_region.split('class="home-rt-video"', 1)[1]
        self.assertIn('loading="lazy"', rt_region)
        self.assertIn('referrerpolicy="strict-origin-when-cross-origin"', rt_region)
        self.assertIn("allowfullscreen", rt_region)
        self.assertIn('href="respiratory-care/"', rt_region)
        css = (ROOT / "assets" / "nurse-ai.css").read_text(encoding="utf-8")
        self.assertIn(".home-resident-video", css)
        self.assertIn(".home-rt-video", css)
        self.assertIn("aspect-ratio: 9 / 16", css)

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
            expected = {ZIP_PREFIX + path.name for path in PACKAGE.iterdir() if path.is_file()}
            self.assertEqual(set(archive.namelist()), expected)
            self.assertIsNone(archive.testzip())
            for info in archive.infolist():
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.date_time, (2026, 7, 16, 0, 0, 0))
                self.assertEqual(info.external_attr >> 16, 0o100644)
            for path in PACKAGE.iterdir():
                if path.is_file():
                    self.assertEqual(archive.read(ZIP_PREFIX + path.name), path.read_bytes())

    def test_self_install_build_kit_is_pinned_and_not_operational(self):
        self.assertEqual(sha256(BUILD_KIT), "cc1f458055ee47c311733d8cd38b5ede80c5ce886c4523e28f246fb8cac17784")
        self.assertEqual(BUILD_KIT.stat().st_size, 6994006)
        with zipfile.ZipFile(BUILD_KIT) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(len(archive.infolist()), 149)
            names = archive.namelist()
            self.assertTrue(all(name.startswith(BUILD_KIT_ROOT) for name in names))
            self.assertIn(BUILD_KIT_ROOT + "README-FIRST.md", names)
            self.assertIn(BUILD_KIT_ROOT + "GIVE-THIS-PACKAGE-TO-HERMES.md", names)
            self.assertIn(BUILD_KIT_ROOT + "RELEASE-MANIFEST.json", names)
            self.assertIn(BUILD_KIT_ROOT + "SHA256SUMS.txt", names)
            self.assertIn(BUILD_KIT_ROOT + "tools/verify-build-kit.py", names)
            manifest = json.loads(archive.read(BUILD_KIT_ROOT + "RELEASE-MANIFEST.json"))
            handoff = archive.read(BUILD_KIT_ROOT + "GIVE-THIS-PACKAGE-TO-HERMES.md").decode("utf-8")
            read_first = archive.read(BUILD_KIT_ROOT + "README-FIRST.md").decode("utf-8")
            baseline_qa = archive.read(BUILD_KIT_ROOT + "source/baseline-qa-reference/test_discover_mission_control_v2_dom.mjs").decode("utf-8")
        self.assertEqual(manifest["target"]["lane"], "medical_resident")
        self.assertEqual(manifest["target"]["namespace"], "medres_rounds.*")
        self.assertEqual(manifest["target"]["readiness"], "not_operational_build_required")
        self.assertEqual(manifest["counts"]["total_required_execution_records"], 424)
        self.assertEqual(manifest["counts"]["canonical_assurance_checks"], 160)
        self.assertEqual(manifest["defaults"]["agents"], "PERM-P0 Disabled")
        self.assertEqual(manifest["defaults"]["powers"], "Available Inactive")
        self.assertEqual(manifest["defaults"]["external_actions"], "Off")
        self.assertEqual(manifest["defaults"]["memory"], "session_only")
        self.assertIn("RESTRICTED_RECORD_PLACEHOLDER_123456", baseline_qa)
        self.assertNotIn("MRN: 123456", baseline_qa)
        for phrase in (
            "Perform only read-only preflight",
            "read-only preflight",
            "Implementation Activation Card",
            "Stop for exact approval",
            "Do not use PHI",
            "Keep connectors, external actions, new persistent memory, schedules, tools, agents, and background work Off",
            "Not operational",
        ):
            self.assertIn(phrase, handoff + read_first)

    def test_builder_tracks_build_kit_with_independent_validator(self):
        builder = (ROOT / "scripts" / "build-medical-resident-rounds.py").read_text(encoding="utf-8")
        workflow = (ROOT / ".github" / "workflows" / "medical-resident-rounds.yml").read_text(encoding="utf-8")
        for phrase in (
            "build_build_kit_zip",
            "BUILD_KIT_SOURCE",
            "validate_build_kit",
            "validate_build_kit_zip_structure",
            "run_bundled_build_kit_verifier",
            "ROUNDS bundled verifier bytes changed",
            "Case-colliding ROUNDS build-kit ZIP member",
            "ROUNDS build kit allows only regular-file entries",
            "BUILD_KIT_VERIFIER_SHA256",
        ):
            self.assertIn(phrase, builder)
        for phrase in (
            "git ls-files --error-unmatch medical-residents/downloads/ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip",
            "git ls-files --error-unmatch medical-residents/build-kit/ROUNDS-Medical-Resident-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0/tools/verify-build-kit.py",
            "test -z \"$(git status --porcelain --untracked-files=all)\"",
        ):
            self.assertIn(phrase, workflow)

    def test_bundled_build_kit_verifier_runs_against_package_and_zip(self):
        verifier = ROOT / "medical-residents" / "build-kit" / BUILD_KIT_ROOT.strip("/") / "tools" / "verify-build-kit.py"
        package = ROOT / "medical-residents" / "build-kit" / BUILD_KIT_ROOT.strip("/")
        completed = subprocess.run(
            [sys.executable, str(verifier), "--package", str(package), "--zip", str(BUILD_KIT)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout[-4000:])
        self.assertIn("VERIFIED ROUNDS MEDICAL RESIDENT BUILD KIT", completed.stdout)

    def test_build_kit_validator_rejects_socket_and_other_special_entries(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-medical-resident-rounds.py"))
        validator = namespace["validate_build_kit_zip_structure"]
        special_modes = {
            "socket": 0o140000,
            "symlink": 0o120000,
            "directory": 0o040000,
        }
        for label, mode in special_modes.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp:
                archive_path = Path(temp) / f"{label}.zip"
                with zipfile.ZipFile(archive_path, "w") as archive:
                    info = zipfile.ZipInfo(BUILD_KIT_ROOT + "README-FIRST.md")
                    info.create_system = 3
                    info.external_attr = mode << 16
                    archive.writestr(info, b"not a regular file")
                with self.assertRaisesRegex(ValueError, "regular-file entries"):
                    validator(archive_path, enforce_pins=False)

    def test_bundled_verifier_warns_for_windows_filesystem_modes(self):
        namespace = runpy.run_path(str(BUILD_KIT_SOURCE / "tools" / "verify-build-kit.py"))
        checks_type = namespace["Checks"]
        check_filesystem = namespace["check_package_filesystem"]
        verifier_os = namespace["os"]
        with tempfile.TemporaryDirectory() as temp:
            package = Path(temp)
            sample = package / "README-FIRST.md"
            sample.write_text("safe\n", encoding="utf-8")
            sample.chmod(0o600)
            checks = checks_type()
            with mock.patch.object(verifier_os, "name", "nt"):
                check_filesystem(checks, package)
            self.assertFalse(checks.failed)
            self.assertTrue(any("not enforceable on Windows" in item for item in checks.warnings))

    def test_public_safety_scanner_covers_extensionless_env_and_script_files(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "scan-public-healthcare-artifacts.py"))
        extract_text = namespace["extract_text"]
        patterns = namespace["PATTERNS"]
        probes = {
            ".env": b"API_KEY=abcdefghijklmnop",
            ".env.example": b"Patient: John",
            "VERSION": b"MRN: A1B2C3",
            "start-discover.sh": b"TOKEN=abcdefghijklmnop",
            "Start-DISCOVER.command": b"MRN number=A1B2C3",
            "Start-DISCOVER.bat": b"Patient: John",
        }
        for name, payload in probes.items():
            with self.subTest(name=name):
                texts = extract_text(name, payload)
                self.assertTrue(texts, name)
                text = "\n".join(value for _, value in texts)
                self.assertTrue(
                    patterns["patient or mrn example"].search(text) or patterns["generic api key"].search(text),
                    name,
                )

    def test_builder_rejects_source_wrapper_and_ledger_tampering(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-medical-resident-rounds.py"))
        validator = namespace["validate_package"]
        for target in (PROGRAM.name, "00-READ-FIRST.md", "PACKAGE-CHECKSUMS.sha256"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                copied = Path(temp) / "rounds"
                shutil.copytree(PACKAGE, copied)
                with (copied / target).open("ab") as handle:
                    handle.write(b"\nTAMPER")
                validator.__globals__["PACKAGE"] = copied
                with self.assertRaises(ValueError):
                    validator()
        validator.__globals__["PACKAGE"] = PACKAGE

    def test_deterministic_builder_reproduces_committed_zip(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-medical-resident-rounds.py"))
        build = namespace["build"]
        before = sha256(ZIP)
        record = build()
        self.assertEqual(record["sha256"], sha256(BUILD_KIT))
        self.assertEqual(sha256(ZIP), before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
