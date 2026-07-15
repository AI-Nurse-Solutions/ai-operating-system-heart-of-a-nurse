#!/usr/bin/env python3
"""Acceptance and packaging tests for the Nurse Leader and Manager Complete Edition."""

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
PACKAGE = ROOT / "post-setup" / "packages" / "03-Nurse-Leader-and-Manager"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "nurse-ai-os-post-setup-nurse-leader-and-manager.zip"
RESUME = (
    "Resume Nurse Leader Complete Edition installation from the last approved checkpoint. "
    "Revalidate the authenticated owner, workspace scope, privacy and workforce-data boundaries, "
    "decision authority, permissions, component versions, current Command Center, source state, "
    "and every critical control before continuing."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NurseLeaderCompleteEditionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.manifest = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))
        cls.read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")

    def test_required_source_artifacts_exist(self):
        for path in (PROGRAM, GUIDE, DOCX, ROLE_MANIFEST, PACKAGE / "00-READ-FIRST.md"):
            self.assertTrue(path.is_file(), path)
            self.assertGreater(path.stat().st_size, 500, path)
        self.assertTrue(DOCX.read_bytes().startswith(b"PK"))

    def test_source_hashes_and_sizes_match_manifest(self):
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        for path in (PROGRAM, GUIDE, DOCX):
            record = records[path.name]
            self.assertEqual(path.stat().st_size, record["bytes"])
            self.assertEqual(sha256(path), record["source_sha256"])

    def test_pre_install_consent_and_authority_boundary(self):
        self.assertEqual(self.manifest["role"], "Nurse Leader and Manager")
        self.assertFalse(self.manifest["role_selection_verifies_credentials_or_authority"])
        self.assertTrue(self.manifest["pre_install_disclosure_required"])
        self.assertTrue(self.manifest["organizational_deployment_requires_separate_authorization"])
        for phrase in (
            "Downloading and unzipping this package does not install or activate anything",
            "Installation begins only when you intentionally give Hermes the complete one-file Nurse Leader program",
            "approve the exact **Nurse Leader Complete Edition Activation Card**",
            "After that approval, Hermes performs the governed installation automatically",
            "If you do not approve the exact card, Hermes must make no installation changes",
            "A private leader-workspace approval does not authorize organizational deployment",
        ):
            self.assertIn(phrase, self.read_first)

    def test_release_check_inventory_is_exact(self):
        foundation = self.program.split("# 18. Acceptance tests", 1)[1].split("\n---", 1)[0]
        foundation_tests = [line for line in foundation.splitlines() if line.startswith("- ")]
        lead = self.program.split("# Nurse Leader LEAD Acceptance Tests", 1)[1]
        lead_ids = re.findall(r"^- \*\*([A-Z]\d+) —", lead, flags=re.MULTILINE)
        integration = self.program.split("# Phase 4 — Combined verification", 1)[1].split(
            "Any critical failure", 1
        )[0]
        integration_ids = re.findall(r"^([0-9]+)\.", integration, flags=re.MULTILINE)
        self.assertEqual(len(foundation_tests), 21)
        self.assertEqual(len(lead_ids), 80)
        self.assertEqual(len(set(lead_ids)), 80)
        self.assertEqual(integration_ids, [str(i) for i in range(1, 13)])
        self.assertEqual(
            self.manifest["acceptance_tests"],
            {"foundation": 21, "lead_overlay": 80, "integration": 12, "total": 113},
        )

    def test_installation_order_and_safe_defaults(self):
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["lead_overlay_second"])
        self.assertEqual(self.manifest["optional_superpowers_total"], 16)
        self.assertEqual(self.manifest["optional_superpowers_active_after_install"], 0)
        for key in (
            "automatic_connectors",
            "automatic_external_actions",
            "automatic_memory",
            "automatic_cron",
            "automatic_shared_access",
        ):
            self.assertFalse(self.manifest[key], key)
        self.assertLess(
            self.program.index("# Phase 2 — Install and verify the Nurse Leader foundation"),
            self.program.index("# Phase 3 — Add LEAD as an inactive overlay"),
        )

    def test_progress_checkpoint_and_resume_contract(self):
        for phrase in (
            'S0: "verified pre-install state"',
            'S1: "healthy Nurse Leader foundation"',
            'S2: "healthy Nurse Leader Complete Edition"',
            "provide the exact command to resume",
            "I do not continue in the background",
        ):
            self.assertIn(phrase, self.program)
        self.assertIn(RESUME, self.program)
        self.assertIn(RESUME, self.guide)
        self.assertIn(RESUME, self.read_first)

    def test_restricted_people_data_and_autonomous_decisions_are_prohibited(self):
        for phrase in (
            'restricted_workforce_information: "excluded by default"',
            'connectors: "off"',
            'shared_access: "off"',
            'external_actions: "off"',
            'new_memory_categories: "off"',
            'background_automation: "off"',
            "must not score, rank, profile, surveil, diagnose, or predict",
        ):
            self.assertTrue(phrase in self.program or phrase in self.read_first, phrase)

    def test_public_lane_copy_distinguishes_complete_editions(self):
        page = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Nurse Leader Complete AI OS with LEAD SuperPowers",
            "113 release checks in total",
            "all sixteen optional SuperPowers remain inactive",
            "Without that approval, Hermes must make no installation changes",
            "Complete Edition lanes 03 and 06",
            "For review-first lanes 01, 02, 04, and 05",
        ):
            self.assertIn(phrase, page)
        self.assertNotIn("Lanes 01–05 require review before changes", page)
        self.assertNotIn("Lanes 01–05 contain", page)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        self.assertTrue(ZIP.is_file(), ZIP)
        manifest = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        record = next(item for item in manifest["packages"] if item["role"] == "Nurse Leader and Manager")
        self.assertFalse(record["install_on_download"])
        self.assertTrue(record["pre_install_disclosure_required"])
        self.assertEqual(record["activation"], "user_initiated_guided_complete_setup_with_combined_activation_card")
        self.assertEqual(record["acceptance_tests"]["total"], 113)
        self.assertTrue(record["foundation_first"])
        self.assertTrue(record["lead_overlay_second"])
        self.assertEqual(record["sha256"], sha256(ZIP))
        ledger = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{sha256(ZIP)}  {ZIP.name}", ledger)
        with zipfile.ZipFile(ZIP) as archive:
            prefix = "03-Nurse-Leader-and-Manager/"
            names = set(archive.namelist())
            for path in PACKAGE.iterdir():
                if path.is_file():
                    self.assertIn(prefix + path.name, names)
                    self.assertEqual(archive.read(prefix + path.name), path.read_bytes())

    def test_import_source_can_seed_separately_governed_leader_package(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        role = next(item for item in namespace["ROLES"] if item["label"] == "Nurse Leader and Manager")
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

    def test_import_source_rejects_missing_leader_before_partial_import(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        build = namespace["build"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            source_root.mkdir()
            for role in namespace["ROLES"]:
                if not role.get("prebuilt"):
                    (source_root / role["source"]).mkdir()
                elif role["label"] == "Nurse Practitioner (USA)":
                    shutil.copytree(
                        ROOT / "post-setup" / "packages" / role["folder"],
                        source_root / role["folder"],
                    )
            build.__globals__["PACKAGES"] = root / "packages"
            build.__globals__["DOWNLOADS"] = root / "downloads"
            with self.assertRaisesRegex(FileNotFoundError, "03-Nurse-Leader-and-Manager"):
                build(source_root)
            self.assertEqual(list((root / "packages").iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
