#!/usr/bin/env python3
"""Acceptance and packaging tests for the Student/Assistant FUTURE Complete Edition."""

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
PACKAGE = ROOT / "post-setup" / "packages" / "01-Student-Nurse"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "nurse-ai-os-post-setup-student-nurse.zip"
RESUME = (
    "Resume FUTURE Complete Edition installation from the last approved checkpoint. "
    "Revalidate the authenticated owner, selected pathway, active context, privacy and no-PHI boundaries, "
    "academic and employer rules, clinical and role authority, permissions, component versions, current "
    "Command Center, source state, and every critical control."
)


def sha256(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StudentAssistantCompleteEditionTests(unittest.TestCase):
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

    def test_markdown_guide_is_renderable_and_normalization_is_provenanced(self):
        records = {item["packaged_path"]: item for item in self.manifest["source_files"]}
        record = records[GUIDE.name]
        self.assertEqual(
            record["upstream_sha256"],
            "872d913a46e3bf1655c8b4f8d3b945c5bcee363c7567240400842341d6412e87",
        )
        self.assertIn("four-space leading indent", record["transformation"])
        self.assertFalse(any(line.startswith("    ##") for line in self.guide.splitlines()))
        self.assertFalse(any(line.startswith("    >") for line in self.guide.splitlines()))
        self.assertIn("## Setup, Benefits, and First-Use Guide", self.guide)
        self.assertIn("> **Please allow time.**", self.guide)

    def test_pre_install_consent_and_deployment_boundary(self):
        self.assertEqual(self.manifest["role"], "Nursing Student and Nursing Assistant")
        self.assertFalse(self.manifest["role_selection_verifies_credentials_or_authority"])
        self.assertTrue(self.manifest["pre_install_disclosure_required"])
        self.assertTrue(self.manifest["organizational_deployment_requires_separate_authorization"])
        for phrase in (
            "Complete and review your SOUL files and Hermes setup before using this post-setup package",
            "If either prerequisite is incomplete or uncertain, stop here",
            "Downloading, selecting, opening, or unzipping this package does not install or activate anything",
            "allow Hermes to complete the read-only",
            "approve that exact card",
            "If you do not approve the exact card, Hermes must make no installation changes",
            "A private learner-workspace approval does not authorize",
            "136 embedded release checks in total",
        ):
            self.assertIn(phrase, self.read_first)

    def test_release_check_inventory_is_exact(self):
        acceptance = self.program.split("# Acceptance Tests", 1)[1]
        foundation = acceptance.split("## 24 foundation tests", 1)[1].split("## 96 FUTURE overlay tests", 1)[0]
        overlay = acceptance.split("## 96 FUTURE overlay tests", 1)[1].split("## 16 integration checks", 1)[0]
        integration = acceptance.split("## 16 integration checks", 1)[1].split("## Critical release blockers", 1)[0]
        foundation_ids = re.findall(r"^- \*\*(C\d{2}) —", foundation, flags=re.MULTILINE)
        overlay_ids = re.findall(r"^- \*\*([A-L]\d):", overlay, flags=re.MULTILINE)
        integration_ids = re.findall(r"^- \*\*(I\d{2}):", integration, flags=re.MULTILINE)
        self.assertEqual(foundation_ids, [f"C{i:02d}" for i in range(1, 25)])
        self.assertEqual(len(overlay_ids), 96)
        self.assertEqual(len(set(overlay_ids)), 96)
        self.assertEqual(overlay_ids, [f"{letter}{i}" for letter in "ABCDEFGHIJKL" for i in range(1, 9)])
        self.assertEqual(integration_ids, [f"I{i:02d}" for i in range(1, 17)])
        self.assertEqual(
            self.manifest["acceptance_tests"],
            {"foundation": 24, "future_overlay": 96, "integration": 16, "total": 136},
        )

    def test_installation_order_and_safe_defaults(self):
        self.assertTrue(self.manifest["foundation_first"])
        self.assertTrue(self.manifest["future_overlay_second"])
        self.assertEqual(self.manifest["optional_superpowers_total"], 18)
        self.assertEqual(self.manifest["optional_superpowers_active_after_install"], 0)
        for key in (
            "automatic_connectors",
            "automatic_external_actions",
            "automatic_memory",
            "automatic_cron",
            "automatic_shared_access",
            "bridge_context_transfer_automatic",
        ):
            self.assertFalse(self.manifest[key], key)
        self.assertLess(
            self.program.index("## Phase 2 — Foundation"),
            self.program.index("## Phase 3 — Inactive expansion"),
        )

    def test_pathways_do_not_create_authority_or_transfer_context(self):
        self.assertEqual(self.manifest["pathways"], ["Nursing Student", "Nursing Assistant", "Bridge"])
        for phrase in (
            "A title never proves authority, scope, competence, or permission",
            "Nursing-assistant scope is verified locally rather than inferred from a title",
            "Bridge mode creates separate academic and employment contexts with no silent transfer",
            "The AI Literacy Passport is developmental and cannot be represented as licensure, certification, or competency validation",
        ):
            self.assertIn(phrase, self.program)

    def test_progress_checkpoint_and_resume_contract(self):
        for phrase in (
            "S0 pre-install, S1 healthy foundation, S2 healthy Complete Edition",
            "No background continuation",
            "A dashboard preview is not completion",
            "After every phase report completed work",
        ):
            self.assertIn(phrase, self.program)
        self.assertIn(RESUME, self.program)
        self.assertIn(RESUME, self.read_first)
        self.assertIn("use the exact resume command in the program", self.guide)

    def test_prohibited_data_academic_deception_surveillance_and_actions(self):
        for phrase in (
            "PHI, patient screenshots, chart excerpts",
            "live examinations, deceptive completion of restricted assessed work",
            "restricted student, employee, disciplinary, grievance, accommodation",
            "hidden monitoring, sentiment analysis, ranking, profiling",
            "No connector, shared access, external action, new memory category, or background automation is enabled",
        ):
            self.assertTrue(phrase in self.program or phrase in self.read_first, phrase)

    def test_public_copy_classifies_lane_one_as_complete_edition(self):
        page = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Nursing Student &amp; Nursing Assistant Complete AI OS with FUTURE SuperPowers",
            "136 embedded release checks",
            "all eighteen optional FUTURE SuperPowers remain inactive",
            "Nursing Student, Nursing Assistant, or Bridge",
            "Complete Edition lanes 01, 03, 04, and 06",
            "For review-first lanes 02 and 05",
        ):
            self.assertIn(phrase, page)
        readme = (ROOT / "post-setup" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Lanes 01, 03, 04, and 06 are separately governed Complete Editions", readme)
        self.assertIn("Review-first lanes 02 and 05 include", readme)
        self.assertIn("Nursing Student and Nursing Assistant ZIP is a separately governed Complete Edition", readme)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        self.assertTrue(ZIP.is_file(), ZIP)
        manifest = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        record = next(item for item in manifest["packages"] if item["role"] == "Nursing Student and Nursing Assistant")
        self.assertFalse(record["install_on_download"])
        self.assertTrue(record["pre_install_disclosure_required"])
        self.assertEqual(record["activation"], "user_initiated_guided_complete_setup_with_combined_activation_card")
        self.assertEqual(record["acceptance_tests"]["total"], 136)
        self.assertTrue(record["foundation_first"])
        self.assertTrue(record["future_overlay_second"])
        self.assertEqual(record["optional_superpowers_total"], 18)
        self.assertEqual(record["optional_superpowers_active_after_install"], 0)
        self.assertEqual(record["sha256"], sha256(ZIP))
        ledger = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{sha256(ZIP)}  {ZIP.name}", ledger)
        with zipfile.ZipFile(ZIP) as archive:
            prefix = "01-Student-Nurse/"
            names = set(archive.namelist())
            expected = {prefix + path.name for path in PACKAGE.iterdir() if path.is_file()}
            self.assertEqual(names, expected)
            for path in PACKAGE.iterdir():
                if path.is_file():
                    self.assertEqual(archive.read(prefix + path.name), path.read_bytes())

    def test_import_source_can_seed_separately_governed_student_assistant_package(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        role = next(item for item in namespace["ROLES"] if item["label"] == "Nursing Student and Nursing Assistant")
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

    def test_import_source_rejects_missing_student_assistant_before_partial_import(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        build = namespace["build"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            source_root.mkdir()
            for role in namespace["ROLES"]:
                if not role.get("prebuilt"):
                    (source_root / role["source"]).mkdir()
                elif role["folder"] != "01-Student-Nurse":
                    shutil.copytree(ROOT / "post-setup" / "packages" / role["folder"], source_root / role["folder"])
            build.__globals__["PACKAGES"] = root / "packages"
            build.__globals__["DOWNLOADS"] = root / "downloads"
            with self.assertRaisesRegex(FileNotFoundError, "01-Student-Nurse"):
                build(source_root)
            self.assertEqual(list((root / "packages").iterdir()), [])

    def test_import_source_rejects_unmanifested_files_for_every_prebuilt_role(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        function = namespace["import_prebuilt_role"]
        for role in (item for item in namespace["ROLES"] if item.get("prebuilt")):
            with self.subTest(role=role["folder"]), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source_root = root / "source"
                source_root.mkdir()
                source = source_root / role["folder"]
                shutil.copytree(ROOT / "post-setup" / "packages" / role["folder"], source)
                (source / "STALE-UNMANIFESTED-FILE.md").write_text("must fail closed\n", encoding="utf-8")
                function.__globals__["PACKAGES"] = root / "packages"
                function.__globals__["PACKAGES"].mkdir()
                with self.assertRaisesRegex(ValueError, "unexpected files.*STALE-UNMANIFESTED-FILE.md"):
                    function(source_root, role)
                self.assertFalse((function.__globals__["PACKAGES"] / role["folder"]).exists())

    def test_import_source_rejects_self_consistent_manifest_that_omits_pinned_sources(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        function = namespace["import_prebuilt_role"]
        for role in (item for item in namespace["ROLES"] if item.get("prebuilt")):
            with self.subTest(role=role["folder"]), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source_root = root / "source"
                source_root.mkdir()
                source = source_root / role["folder"]
                shutil.copytree(ROOT / "post-setup" / "packages" / role["folder"], source)
                omitted = role["required_prebuilt_sources"][0]
                (source / omitted).unlink()
                manifest_path = source / "ROLE-PACK.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["source_files"] = [
                    record for record in manifest["source_files"] if record["packaged_path"] != omitted
                ]
                manifest_path.write_text(
                    json.dumps(manifest, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8",
                )
                ledger = source / "PACKAGE-CHECKSUMS.sha256"
                ledger.write_text(
                    "\n".join(
                        f"{sha256(path)}  {path.relative_to(source).as_posix()}"
                        for path in sorted(source.rglob("*"))
                        if path.is_file() and path != ledger
                    )
                    + "\n",
                    encoding="utf-8",
                )
                function.__globals__["PACKAGES"] = root / "packages"
                function.__globals__["PACKAGES"].mkdir()
                with self.assertRaisesRegex(ValueError, "Pinned source inventory mismatch"):
                    function(source_root, role)
                self.assertFalse((function.__globals__["PACKAGES"] / role["folder"]).exists())

    def test_import_source_rejects_macos_metadata_for_every_prebuilt_role(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        function = namespace["import_prebuilt_role"]
        for role in (item for item in namespace["ROLES"] if item.get("prebuilt")):
            with self.subTest(role=role["folder"]), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source_root = root / "source"
                source_root.mkdir()
                source = source_root / role["folder"]
                shutil.copytree(ROOT / "post-setup" / "packages" / role["folder"], source)
                (source / ".DS_Store").write_bytes(b"macOS metadata must not ship")
                function.__globals__["PACKAGES"] = root / "packages"
                function.__globals__["PACKAGES"].mkdir()
                with self.assertRaisesRegex(ValueError, r"unexpected files.*\.DS_Store"):
                    function(source_root, role)
                self.assertFalse((function.__globals__["PACKAGES"] / role["folder"]).exists())

    def test_import_source_verifies_wrapper_checksums_before_copying(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        function = namespace["import_prebuilt_role"]
        for role in (item for item in namespace["ROLES"] if item.get("prebuilt")):
            with self.subTest(role=role["folder"]), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source_root = root / "source"
                source_root.mkdir()
                source = source_root / role["folder"]
                shutil.copytree(ROOT / "post-setup" / "packages" / role["folder"], source)
                with (source / "00-READ-FIRST.md").open("a", encoding="utf-8") as handle:
                    handle.write("\nunauthorized safety-wrapper change\n")
                function.__globals__["PACKAGES"] = root / "packages"
                function.__globals__["PACKAGES"].mkdir()
                with self.assertRaisesRegex(ValueError, "Checksum mismatch.*00-READ-FIRST.md"):
                    function(source_root, role)
                self.assertFalse((function.__globals__["PACKAGES"] / role["folder"]).exists())

    def test_build_validates_all_prebuilt_sources_before_any_import_mutation(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        build = namespace["build"]
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_root = root / "source"
            source_root.mkdir()
            for role in namespace["ROLES"]:
                if role.get("prebuilt"):
                    shutil.copytree(
                        ROOT / "post-setup" / "packages" / role["folder"],
                        source_root / role["folder"],
                    )
                else:
                    (source_root / role["source"]).mkdir()
            (source_root / "01-Student-Nurse" / "STALE.md").write_text(
                "must fail before generic imports\n", encoding="utf-8"
            )
            build.__globals__["PACKAGES"] = root / "packages"
            build.__globals__["DOWNLOADS"] = root / "downloads"
            with self.assertRaisesRegex(ValueError, "unexpected files.*STALE.md"):
                build(source_root)
            self.assertEqual(list((root / "packages").iterdir()), [])

    def test_import_source_rejects_self_consistent_source_replacement_for_every_prebuilt_role(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        function = namespace["import_prebuilt_role"]
        refresh = namespace["refresh_package_checksums"]
        for role in (item for item in namespace["ROLES"] if item.get("prebuilt")):
            with self.subTest(role=role["folder"]), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                source_root = root / "source"
                source_root.mkdir()
                source = source_root / role["folder"]
                shutil.copytree(ROOT / "post-setup" / "packages" / role["folder"], source)
                target = source / role["required_prebuilt_sources"][0]
                target.write_bytes(target.read_bytes() + b"\nself-consistent but unauthorized replacement\n")
                manifest_path = source / "ROLE-PACK.json"
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                record = next(item for item in manifest["source_files"] if item["packaged_path"] == target.name)
                record["source_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
                record["bytes"] = target.stat().st_size
                manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                refresh(source)
                function.__globals__["PACKAGES"] = root / "packages"
                function.__globals__["PACKAGES"].mkdir()
                with self.assertRaisesRegex(ValueError, "Trusted source checksum mismatch"):
                    function(source_root, role)
                self.assertFalse((function.__globals__["PACKAGES"] / role["folder"]).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
