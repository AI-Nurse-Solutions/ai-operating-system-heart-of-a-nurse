#!/usr/bin/env python3
"""Acceptance and packaging tests for the Educator/Designer TEACH Complete Edition."""

from __future__ import annotations

import hashlib
import json
import re
import runpy
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "post-setup" / "packages" / "04-Nurse-Educator"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_ROOT = "TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-Build-Kit-v1.0.0"
BUILD_KIT_SHA256 = "fe9f96b4b908602cdae1e35f1643225d70b6f5068049cba1b707f2b8e66104dd"
BUILD_KIT_BYTES = 6823419
BUILD_KIT_MEMBER_COUNT = 121
BUILD_KIT_VERIFIER_SHA256 = "c79581cde1a4ede0c49bd2bc806d6ec74150859d34700a9fad19fc57873f7ae3"
SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE = "8b7e8290382f7df5830554ad740a8fd280c3d2be5e8948d1a539afe074416cb9"
RESUME = "Resume TEACH Complete Edition installation from the last approved checkpoint."


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EducatorCompleteEditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
        cls.manifest = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))

    def test_required_source_artifacts_exist(self):
        for path in (PROGRAM, GUIDE, DOCX):
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 1000)

    def test_source_hashes_and_sizes_match_manifest(self):
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        for path in (PROGRAM, GUIDE, DOCX):
            record = records[path.name]
            self.assertEqual(path.stat().st_size, record["bytes"])
            self.assertEqual(sha256(path), record["source_sha256"])

    def test_markdown_hard_break_normalization_is_renderable_and_provenanced(self):
        record = next(item for item in self.manifest["source_files"] if item["packaged_path"] == GUIDE.name)
        self.assertEqual(record["upstream_sha256"], "fd90028796a066f7854baf456fa761ba212979a584ba18088dc123df4915967a")
        self.assertIn("explicit <br> tags", record["transformation"])
        self.assertIn("**Program:** `NAIO-NEID-COMPLETE-TEACH-1.0`<br>", self.guide)
        self.assertIn("Hybrid or Faculty Developer<br>", self.guide)
        self.assertFalse(any(line.endswith(" ") for line in self.guide.splitlines()))

    def test_embedded_template_normalization_is_renderable_and_provenanced(self):
        record = next(item for item in self.manifest["source_files"] if item["packaged_path"] == PROGRAM.name)
        self.assertEqual(record["upstream_sha256"], "d16b693d5a28b706e8f20b1b1f1b8941f2e81d93ce2f70cf00b151833b22f035")
        self.assertIn("semantic Markdown", record["transformation"])
        section = self.program.split("# TEACH Cards and Templates", 1)[1].split(
            "<!-- END EMBEDDED COMPONENT: templates/TEACH-Cards-and-Templates.md -->", 1
        )[0]
        for phrase in (
            "## Required library",
            "1. Teaching/Design True North Card",
            "## Optional Power Activation Card",
            "- [ ] Preview only",
            "## TEACH Gate Release Receipt",
            "## Human Teaching Anti-Slop Check",
        ):
            self.assertIn(phrase, section)
        self.assertNotRegex(section, r"(?m)^    (?:##|1\.|-|Remove generic filler)")

    def test_pre_install_consent_and_institutional_boundary(self):
        self.assertEqual(self.manifest["role"], "Nurse Educator and Instructional Designer")
        self.assertFalse(self.manifest["role_selection_verifies_credentials_or_authority"])
        self.assertTrue(self.manifest["pre_install_disclosure_required"])
        self.assertTrue(self.manifest["institutional_deployment_requires_separate_authorization"])
        for phrase in (
            "Complete and review your SOUL files and Hermes setup",
            "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
            "allow Hermes to complete the read-only",
            "approve that exact card",
            "If you do not approve the exact card, Hermes must make no installation changes",
            "A private educator/designer-workspace approval does not authorize",
            "169 embedded release checks in total",
        ):
            self.assertIn(phrase, self.read_first)

    def test_release_check_inventory_is_exact(self):
        foundation = self.program.split("# 20. Acceptance tests", 1)[1].split("---", 1)[0]
        foundation_checks = re.findall(r"^- ", foundation, flags=re.MULTILINE)
        overlay = self.program.split("## 120 TEACH overlay tests", 1)[1].split("## 16 Complete Edition integration checks", 1)[0]
        integration = self.program.split("## 16 Complete Edition integration checks", 1)[1].split("## Critical release blockers", 1)[0]
        overlay_ids = re.findall(r"^- \*\*([A-O]\d):", overlay, flags=re.MULTILINE)
        integration_ids = re.findall(r"^- \*\*(INT\d{2}):", integration, flags=re.MULTILINE)
        self.assertEqual(len(foundation_checks), 33)
        self.assertEqual(overlay_ids, [f"{letter}{i}" for letter in "ABCDEFGHIJKLMNO" for i in range(1, 9)])
        self.assertEqual(integration_ids, [f"INT{i:02d}" for i in range(1, 17)])
        self.assertEqual(
            self.manifest["acceptance_tests"],
            {"foundation": 33, "teach_overlay": 120, "integration": 16, "total": 169},
        )

    def test_installation_order_and_safe_defaults(self):
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["teach_overlay_second"])
        self.assertEqual(self.manifest["optional_superpowers_total"], 20)
        self.assertEqual(self.manifest["optional_superpowers_active_after_install"], 0)
        for key in (
            "install_on_download",
            "automatic_connectors",
            "automatic_cron",
            "automatic_external_actions",
            "automatic_memory",
            "automatic_shared_access",
            "clinical_decisions",
        ):
            self.assertFalse(self.manifest[key], key)
        self.assertIn("all twenty optional TEACH SuperPowers inactive", self.read_first)

    def test_role_adapters_never_create_or_transfer_authority(self):
        self.assertEqual(
            self.manifest["role_adapters"],
            ["Nurse Educator", "Instructional Designer", "Hybrid / Faculty Developer"],
        )
        for phrase in (
            "Design access does not create faculty",
            "Switching hats triggers a new authority check",
            "Access is not authority",
            "does not verify employment, faculty status",
        ):
            self.assertIn(phrase, self.read_first)

    def test_student_data_grading_surveillance_and_release_are_prohibited(self):
        for phrase in (
            "no student records, restricted employee records, secure exams, or item banks",
            "no hidden learner scoring, ranking, profiling, surveillance",
            "AI-detection output is not proof",
            "must not autonomously grade, progress, discipline, dismiss, accommodate",
            "Secure assessments remain in approved systems",
        ):
            self.assertIn(phrase, self.read_first)

    def test_progress_checkpoint_and_resume_contract(self):
        for checkpoint in ("S0", "S1", "S2"):
            self.assertIn(checkpoint, self.program)
            self.assertIn(checkpoint, self.guide)
            self.assertIn(checkpoint, self.read_first)
        self.assertIn(RESUME, self.program)
        self.assertIn("exact resume command", self.guide)
        self.assertIn("exact **Resume TEACH Complete Edition installation", self.read_first)
        self.assertIn("does not continue in the background", self.read_first)

    def test_public_copy_classifies_lane_four_as_complete_edition(self):
        page = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Nurse Educator &amp; Instructional Designer",
            "TEACH SuperPowers",
            "169 canonical checks",
            "264 explicit target rows",
            "433 required execution records",
            "self-install Hermes build kit",
            "approximately 6.82 MB",
            "not operational—build required",
            "TEACH Implementation Activation Card",
            "all twenty optional TEACH SuperPowers remain inactive",
            "Complete Edition lanes 01, 02, 03, 04, and 06",
            "For review-first lane 05",
        ):
            self.assertIn(phrase, page)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        public = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        record = next(item for item in public["packages"] if item["role"] == "Nurse Educator and Instructional Designer")
        self.assertEqual(record["download"], f"downloads/{ZIP.name}")
        self.assertEqual(record["download_type"], "self_install_hermes_build_kit")
        self.assertEqual(record["published_state"], "published_not_installed_not_activated_not_operational_not_institutionally_authorized")
        self.assertEqual(record["ci_validation"], "tracked_repository_validator_no_artifact_controlled_code_execution")
        self.assertEqual(record["sha256"], BUILD_KIT_SHA256)
        self.assertEqual(record["sha256"], sha256(ZIP))
        self.assertEqual(record["bytes"], BUILD_KIT_BYTES)
        self.assertEqual(ZIP.stat().st_size, BUILD_KIT_BYTES)
        self.assertEqual(record["readiness"], "not_operational_build_required")
        self.assertEqual(record["target_product"], "TEACH — Nurse Educator & Instructional Designer Mission Control")
        self.assertEqual(record["target_route"], "/nurse-educators-designers/dashboard")
        self.assertEqual(record["target_version"], "2.0.0")
        self.assertEqual(record["target_namespace"], "neid_teach.*")
        self.assertEqual(record["build_kit_root"], BUILD_KIT_ROOT)
        self.assertEqual(record["build_kit_member_count"], BUILD_KIT_MEMBER_COUNT)
        self.assertEqual(record["build_kit_verifier_sha256"], BUILD_KIT_VERIFIER_SHA256)
        self.assertEqual(record["source_zip_sha256_before_derivative"], SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE)
        self.assertEqual(record["acceptance_tests"]["total"], 169)
        self.assertEqual(record["build_kit_counts"]["canonical_compatibility_checks"], 169)
        self.assertEqual(record["build_kit_counts"]["total_target_full_stack_tests"], 264)
        self.assertEqual(record["build_kit_counts"]["total_required_execution_records"], 433)
        self.assertEqual(record["build_kit_counts"]["agents"], 10)
        self.assertEqual(record["build_kit_counts"]["workflows"], 18)
        self.assertEqual(record["build_kit_counts"]["templates"], 24)
        self.assertEqual(record["optional_superpowers_active_after_install"], 0)
        with zipfile.ZipFile(ZIP) as archive:
            self.assertEqual(len(archive.infolist()), BUILD_KIT_MEMBER_COUNT)
            self.assertEqual({name.split("/", 1)[0] for name in archive.namelist()}, {BUILD_KIT_ROOT})
            manifest = json.loads(archive.read(f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json"))
            self.assertEqual(manifest["target"]["readiness"], "not_operational_build_required")
            self.assertEqual(manifest["defaults"]["agents"], "PERM-P0 Disabled")
            self.assertEqual(manifest["defaults"]["powers"], "Available Inactive")
            self.assertEqual(manifest["defaults"]["workflows"], "Preview Only")
            self.assertEqual(manifest["defaults"]["connectors_schedules_sharing_external_actions_background_agents"], "Off")
            self.assertEqual(manifest["public_safe_derivative"]["source_zip_sha256_before_derivative"], SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE)
            self.assertIn("PUBLIC_SAFE_EDUCATOR_QA_CONTEXT_PLACEHOLDER", archive.read(f"{BUILD_KIT_ROOT}/source/baseline-qa-reference/test_discover_mission_control_v2_dom.mjs").decode("utf-8"))
            self.assertEqual(hashlib.sha256(archive.read(f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py")).hexdigest(), BUILD_KIT_VERIFIER_SHA256)

    def test_import_source_can_seed_separately_governed_educator_package(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        role = next(item for item in namespace["ROLES"] if item["folder"] == "04-Nurse-Educator")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            source_root.mkdir()
            shutil.copytree(PACKAGE, source_root / role["folder"])
            function = namespace["import_prebuilt_role"]
            function.__globals__["PACKAGES"] = root / "packages"
            function.__globals__["PACKAGES"].mkdir()
            function(source_root, role)
            imported = function.__globals__["PACKAGES"] / role["folder"]
            self.assertEqual((imported / "ROLE-PACK.json").read_bytes(), ROLE_MANIFEST.read_bytes())
            self.assertTrue((imported / "PACKAGE-CHECKSUMS.sha256").is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
