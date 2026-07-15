#!/usr/bin/env python3
"""Acceptance and packaging tests for the USA-only Nurse Practitioner lane."""

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
PACKAGE = ROOT / "post-setup" / "packages" / "06-Nurse-Practitioner-USA"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "NP-Complete-AI-OS-with-Wings-Hermes-Program.md"
GUIDE = PACKAGE / "NP-Complete-AI-OS-with-Wings-Setup-Guide.md"
DOCX = PACKAGE / "NP-Complete-AI-OS-with-Wings-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "nurse-ai-os-post-setup-nurse-practitioner-usa.zip"
RESUME = (
    "Resume NP Complete Edition installation from the last approved checkpoint. "
    "Revalidate identity, privacy, permissions, versions, current dashboard state, "
    "and all critical controls before continuing. Do not repeat completed mutations, "
    "assume a prior result, enable a connector, save new memory, or skip a failed or "
    "unknown test. Show the refreshed progress ledger and continue with the next "
    "incomplete phase only."
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_ids(section: str) -> list[str]:
    return re.findall(r"^- \*\*([A-Z]\d+) —", section, flags=re.MULTILINE)


class NursePractitionerLaneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.manifest = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))

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

    def test_usa_only_role_and_nonverification_contract(self):
        self.assertEqual(self.manifest["role"], "Nurse Practitioner (USA)")
        self.assertEqual(self.manifest["country_availability"], ["United States"])
        self.assertFalse(self.manifest["role_selection_verifies_credentials_or_authority"])
        read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
        self.assertIn("United States-only", read_first)
        self.assertIn("does not verify NP licensure", read_first)
        self.assertTrue(self.manifest["pre_install_disclosure_required"])
        for phrase in (
            "Downloading and unzipping this package does not install or activate anything",
            "Installation begins only when you intentionally give Hermes the complete one-file NP program",
            "approve the exact **Combined Activation Card**",
            "After that approval, Hermes performs the governed installation automatically",
            "All 15 optional Wings remain inactive",
        ):
            self.assertIn(phrase, read_first)

    def test_foundation_and_wings_test_inventory_is_exact(self):
        foundation = self.program.split("# 20. Acceptance tests", 1)[1].split("## Critical release rule", 1)[0]
        wings = self.program.split("# NP Wings Acceptance Tests", 1)[1].split("## Critical release rule", 1)[0]
        foundation_ids = test_ids(foundation)
        wings_ids = test_ids(wings)
        self.assertEqual(len(foundation_ids), 63)
        self.assertEqual(len(set(foundation_ids)), 63)
        self.assertEqual(len(wings_ids), 82)
        self.assertEqual(len(set(wings_ids)), 82)
        self.assertEqual(self.manifest["acceptance_tests"], {"foundation": 63, "np_wings": 82, "total": 145})

    def test_installation_order_and_safe_defaults(self):
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["wings_overlay_second"])
        self.assertEqual(self.manifest["optional_wings_active_after_install"], 0)
        for key in ("automatic_connectors", "automatic_external_actions", "automatic_memory", "automatic_cron"):
            self.assertFalse(self.manifest[key], key)
        self.assertIn("# Phase 2 — Install and verify the foundation", self.program)
        self.assertIn("# Phase 3 — Add NP Wings as an inactive overlay", self.program)
        self.assertLess(
            self.program.index("# Phase 2 — Install and verify the foundation"),
            self.program.index("# Phase 3 — Add NP Wings as an inactive overlay"),
        )

    def test_all_fifteen_optional_wings_are_registered_but_inactive(self):
        registry = self.program.split("## 4. Register the WINGS systems", 1)[1].split("## 5. First-run Wings conversation", 1)[0]
        powers = re.findall(r"^\d+\. (.+)$", registry, flags=re.MULTILINE)
        self.assertEqual(len(powers), 15)
        self.assertIn("Register their power profiles without activating them", registry)
        self.assertIn("No power may activate itself", registry)

    def test_progress_checkpoint_and_resume_contract(self):
        for phrase in (
            "Show a progress receipt after every phase",
            "stop at the next safe phase boundary",
            "provide the exact resume command",
            "S0: \"verified pre-install state\"",
            "S1: \"healthy foundation\"",
            "S2: \"healthy Complete Edition\"",
        ):
            self.assertIn(phrase, self.program)
        self.assertIn(RESUME, self.program)
        self.assertIn(RESUME, self.guide)

    def test_preservation_and_no_duplicate_contract(self):
        for phrase in (
            "Detect, verify, bind, and skip; never duplicate",
            "preserve compatible existing profiles, records, dashboards, files, permissions, and unrelated data",
            "create-if-absent",
            "bind-if-present",
        ):
            self.assertIn(phrase, self.program)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        self.assertTrue(ZIP.is_file(), ZIP)
        manifest = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        record = next(item for item in manifest["packages"] if item["role"] == "Nurse Practitioner (USA)")
        self.assertFalse(record["install_on_download"])
        self.assertTrue(record["pre_install_disclosure_required"])
        self.assertEqual(record["activation"], "user_initiated_guided_complete_setup_with_combined_activation_card")
        self.assertEqual(record["acceptance_tests"]["total"], 145)
        self.assertEqual(record["sha256"], sha256(ZIP))
        ledger = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{sha256(ZIP)}  {ZIP.name}", ledger)
        with zipfile.ZipFile(ZIP) as archive:
            names = set(archive.namelist())
            prefix = "06-Nurse-Practitioner-USA/"
            for path in PACKAGE.iterdir():
                if path.is_file():
                    self.assertIn(prefix + path.name, names)
                    self.assertEqual(archive.read(prefix + path.name), path.read_bytes())

    def test_import_source_can_seed_separately_governed_np_package(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        role = next(item for item in namespace["ROLES"] if item["label"] == "Nurse Practitioner (USA)")
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

    def test_import_source_rejects_missing_np_before_partial_import(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        build = namespace["build"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            source_root.mkdir()
            for role in namespace["ROLES"]:
                if "activation" not in role:
                    (source_root / role["source"]).mkdir()
            build.__globals__["PACKAGES"] = root / "packages"
            build.__globals__["DOWNLOADS"] = root / "downloads"
            with self.assertRaisesRegex(FileNotFoundError, "06-Nurse-Practitioner-USA"):
                build(source_root)
            self.assertEqual(list((root / "packages").iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
