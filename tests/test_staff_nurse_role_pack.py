#!/usr/bin/env python3
"""Acceptance and packaging tests for the Staff Nurse/Quality Contributor SHIFT Complete Edition."""

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
PACKAGE = ROOT / "post-setup" / "packages" / "02-Staff-Nurse"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "nurse-ai-os-post-setup-staff-nurse.zip"
RESUME = "Resume SHIFT Complete Edition installation from the last approved checkpoint."


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StaffNurseCompleteEditionTests(unittest.TestCase):
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

    def test_source_archive_and_file_provenance_is_exact(self):
        self.assertEqual(
            self.manifest["source_archive"],
            {
                "bytes": 250478,
                "filename": "Staff-Nurse-and-Quality-Contributor-Complete-AI-OS-with-SHIFT-SuperPowers-Package-v1.0.zip",
                "sha256": "b3a78f0b6a86bc1bc67dcc95d087fe8c71226889ca02a285a2c4504194d8ccf5",
            },
        )
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        for path in (PROGRAM, GUIDE, DOCX):
            record = records[path.name]
            self.assertEqual(path.stat().st_size, record["bytes"])
            self.assertEqual(sha256(path), record["source_sha256"])
        self.assertEqual(records[PROGRAM.name]["upstream_sha256"], "549c499c1d0d9fa5cd68c2147314c476a3596da08b943d186a009ec5e60bb4d4")
        self.assertEqual(records[GUIDE.name]["upstream_sha256"], "b284742b9a70827cf4aeebdd036cf81e8f1561b00250cbc6d176d68b377342f4")
        self.assertEqual(records[DOCX.name]["source_sha256"], "f8e4381fafaeec746663dc8ebc18c707369ed5c1591537890c5004659d73a0ec")

    def test_markdown_hard_break_normalization_is_renderable_and_provenanced(self):
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        self.assertIn("twenty-four supplied Markdown trailing-space hard breaks", records[PROGRAM.name]["transformation"])
        self.assertIn("three supplied Markdown trailing-space hard breaks", records[GUIDE.name]["transformation"])
        self.assertEqual(self.program.count("<br>"), 24)
        self.assertEqual(self.guide.count("<br>"), 3)
        self.assertFalse(any(line.endswith(" ") for line in self.program.splitlines()))
        self.assertFalse(any(line.endswith(" ") for line in self.guide.splitlines()))

    def test_pre_install_consent_and_institutional_boundary(self):
        self.assertEqual(self.manifest["role"], "Staff Nurse and Quality Contributor")
        self.assertFalse(self.manifest["role_selection_verifies_credentials_or_authority"])
        self.assertTrue(self.manifest["pre_install_disclosure_required"])
        self.assertTrue(self.manifest["institutional_deployment_requires_separate_authorization"])
        for phrase in (
            "Complete and review your SOUL files and Hermes setup",
            "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
            "approve that exact card",
            "If you do not approve the exact card, Hermes must make no installation changes",
            "A private installation does not create or certify this workspace",
            "176 embedded release checks in total",
        ):
            self.assertIn(phrase, self.read_first)

    def test_release_check_inventory_is_exact(self):
        foundation = self.program.split("# 20. Acceptance tests", 1)[1].split("---", 1)[0]
        foundation_checks = re.findall(r"^- ", foundation, flags=re.MULTILINE)
        overlay = self.program.split("## 120 SHIFT overlay tests", 1)[1].split("## 16 Complete Edition integration checks", 1)[0]
        integration = self.program.split("## 16 Complete Edition integration checks", 1)[1].split("## Critical release blockers", 1)[0]
        overlay_ids = re.findall(r"^- \*\*([A-O]\d):", overlay, flags=re.MULTILINE)
        integration_ids = re.findall(r"^- \*\*(INT\d{2}):", integration, flags=re.MULTILINE)
        self.assertEqual(len(foundation_checks), 40)
        self.assertEqual(overlay_ids, [f"{letter}{i}" for letter in "ABCDEFGHIJKLMNO" for i in range(1, 9)])
        self.assertEqual(integration_ids, [f"INT{i:02d}" for i in range(1, 17)])
        self.assertEqual(
            self.manifest["acceptance_tests"],
            {"foundation": 40, "shift_overlay": 120, "integration": 16, "total": 176},
        )

    def test_installation_order_and_safe_defaults(self):
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["shift_overlay_second"])
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
        self.assertIn("All twenty optional SHIFT SuperPowers install inactive", self.read_first)

    def test_role_adapters_never_create_or_transfer_authority(self):
        self.assertEqual(
            self.manifest["role_adapters"],
            [
                "Direct-Care Staff Nurse",
                "Unit Champion / Preceptor / Shared-Governance Member",
                "Chartered Staff-Nurse QI Project Lead",
                "Hybrid / Multiple-Employer",
            ],
        )
        for phrase in (
            "cannot authorize QI",
            "gains no management, staffing, disciplinary",
            "cannot self-authorize data",
            "Switching hats, employers, projects",
            "Access is not authority. Least privilege wins.",
        ):
            self.assertIn(phrase, self.read_first)

    def test_clinical_incident_quality_employment_and_surveillance_boundaries(self):
        for phrase in (
            "No PHI, identifiable patient or event narrative",
            "No diagnosis, prescription, medication, device, alarm, triage",
            "Immediate clinical, safety, deterioration, violence, emergency, or security concerns",
            "AI never decides QI versus EBP versus evaluation versus research",
            "No hidden patient, worker, clinician, unit, or project ranking",
            "No fabricated clinical records, incident facts, quality evidence",
            "A generated quality artifact is a draft for authorized human review",
        ):
            self.assertIn(phrase, self.read_first)

    def test_progress_checkpoint_resume_and_recovery_contract(self):
        for checkpoint in ("S0", "S1", "S2"):
            self.assertIn(checkpoint, self.program)
            self.assertIn(checkpoint, self.guide)
            self.assertIn(checkpoint, self.read_first)
        self.assertIn(RESUME, self.program)
        self.assertIn("exact resume command", self.guide)
        self.assertIn("does not continue in the background", self.read_first)
        for control in ("Pause All", "Safe Reset", "Overlay removal", "Full uninstall"):
            self.assertIn(control, self.read_first)

    def test_public_copy_classifies_lane_two_as_complete_edition(self):
        page = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Staff Nurse &amp; Quality Contributor",
            "SHIFT SuperPowers",
            "176 embedded release checks",
            "all twenty optional SHIFT SuperPowers remain inactive",
            "Complete Edition lanes 01, 02, 03, 04, and 06",
            "review-first lane 05",
        ):
            self.assertIn(phrase, page)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        public = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(public["release"], "2026.07.15.5")
        record = next(item for item in public["packages"] if item["role"] == "Staff Nurse and Quality Contributor")
        self.assertEqual(record["sha256"], sha256(ZIP))
        self.assertEqual(record["acceptance_tests"]["total"], 176)
        self.assertEqual(record["optional_superpowers_active_after_install"], 0)
        with zipfile.ZipFile(ZIP) as archive:
            prefix = "02-Staff-Nurse/"
            expected = {prefix + path.relative_to(PACKAGE).as_posix() for path in PACKAGE.rglob("*") if path.is_file()}
            self.assertEqual(set(archive.namelist()), expected)
            for path in PACKAGE.rglob("*"):
                if path.is_file():
                    self.assertEqual(archive.read(prefix + path.relative_to(PACKAGE).as_posix()), path.read_bytes())

    def test_import_source_can_seed_separately_governed_staff_package(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        role = next(item for item in namespace["ROLES"] if item["folder"] == "02-Staff-Nurse")
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
