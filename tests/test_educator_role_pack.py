#!/usr/bin/env python3
"""Acceptance and packaging tests for the Educator/Designer TEACH build kit."""

from __future__ import annotations

import ast
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

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "post-setup" / "packages" / "04-Nurse-Educator"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Nurse-Educator-and-Instructional-Designer-Complete-AI-OS-with-TEACH-SuperPowers-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_ROOT = "TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-Build-Kit-v1.0.0"
BUILD_KIT_SHA256 = "39d7a83a79b6137d50b6b5da639cd44d0427e4e06e30fc9d7f3b19805b4080f3"
BUILD_KIT_BYTES = 6820684
BUILD_KIT_MEMBER_COUNT = 121
BUILD_KIT_VERIFIER_SHA256 = "3b6017d9e07793f06a470d74f7a1632fbe34f6f5f5c02b7322172cfd9d4e1cfb"
SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE = "8b7e8290382f7df5830554ad740a8fd280c3d2be5e8948d1a539afe074416cb9"
RESUME = "Resume TEACH Complete Edition installation from the last approved checkpoint."
GOVERNED_VERIFY_COMMAND = (
    "python3 tools/verify-build-kit.py --package . --zip "
    "../TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class EducatorBuildKitTests(unittest.TestCase):
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

    def test_public_copy_classifies_lane_four_as_self_install_build_kit(self):
        page = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Nurse Educator &amp; Instructional Designer",
            "TEACH SuperPowers",
            "169 canonical checks",
            "264 explicit target rows",
            "433 required execution records",
            "self-install Hermes build kit",
            "exactly 6,820,684 bytes",
            "not operational—build required",
            "TEACH Implementation Activation Card",
            "all twenty optional TEACH SuperPowers remain inactive",
            "Self-install build-kit lanes 01, 02, 03, 04, and 06",
            "For review-first lane 05",
        ):
            self.assertIn(phrase, page)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        public = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        record = next(item for item in public["packages"] if item["role"] == "Nurse Educator and Instructional Designer")
        self.assertEqual(record["download"], f"downloads/{ZIP.name}")
        self.assertEqual(record["download_type"], "self_install_hermes_build_kit")
        self.assertEqual(record["activation"], "user_initiated_read_only_preflight_with_exact_implementation_activation_card")
        self.assertEqual(record["legacy_source_activation_contract"], "user_initiated_guided_complete_setup_with_combined_activation_card")
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
        self.assertTrue(record["teach_overlay_second"])
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

    def test_documented_verification_and_portability_contract_are_archive_native(self):
        with zipfile.ZipFile(ZIP) as archive:
            for relative in (
                "README-FIRST.md",
                "INSTALL.md",
                "START_HERE.md",
                "implementation/EDUCATOR-User-Installation-Guide.md",
            ):
                text = archive.read(f"{BUILD_KIT_ROOT}/{relative}").decode("utf-8")
                self.assertIn(GOVERNED_VERIFY_COMMAND, text, relative)
                command_lines = [line.strip() for line in text.splitlines() if "verify-build-kit.py" in line]
                self.assertTrue(command_lines, relative)
                self.assertEqual(command_lines, [GOVERNED_VERIFY_COMMAND], relative)

            verifier_name = f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py"
            verifier = archive.read(verifier_name).decode("utf-8")
            ast.parse(verifier)
            self.assertIn("def check_modes(c: Checks, package: Path, enforce_modes: bool) -> None:", verifier)
            self.assertIn("if enforce_modes:", verifier)
            self.assertIn("Extracted filesystem modes are non-authoritative; outer-ZIP modes remain mandatory", verifier)
            self.assertIn('check_modes(c, package, enforce_modes=args.zip_path is None and os.name != "nt")', verifier)
            self.assertIn("check_outer_zip(c, package, resolved_zip)", verifier)
            verifier_mode = (archive.getinfo(verifier_name).external_attr >> 16) & 0o777
            self.assertEqual(verifier_mode, 0o755)

    def test_workflow_path_filters_cover_all_enforced_public_documents(self):
        required = (
            '"README.md"',
            '"architecture-report.html"',
            '"assets/2026-07-13-nurse-ai-os-updated-architecture-report.md"',
            '"assets/2026-07-13-nurse-ai-os-updated-architecture-report.pdf"',
            '"assets/nurse-ai-os-architecture-report.md"',
            '"assets/nurse-ai-os-architecture-report.pdf"',
            '"assets/nurse-ai-os-media-packet.md"',
            '"assets/nurse-ai-os-media-packet.pdf"',
        )
        for relative in (".github/workflows/setup-helper.yml", ".github/workflows/switchboard.yml"):
            workflow = (ROOT / relative).read_text(encoding="utf-8")
            for path in required:
                self.assertEqual(workflow.count(path), 2, f"{relative} must cover pull and push changes to {path}")
        switchboard = (ROOT / ".github/workflows/switchboard.yml").read_text(encoding="utf-8")
        self.assertEqual(switchboard.count('"post-setup/README.md"'), 2)

    def test_rotation_utility_rejects_unsafe_archive_metadata_before_payload_reads(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "rotate-teach-verifier-portability.py"))
        validate_infos = namespace["validate_infos"]
        max_member = namespace["MAX_MEMBER_BYTES"]
        max_expanded = namespace["MAX_EXPANDED_BYTES"]

        def info(name: str, *, mode: int = 0o100644, size: int = 1, encrypted: bool = False):
            item = zipfile.ZipInfo(name)
            item.external_attr = mode << 16
            item.file_size = size
            item.flag_bits = 0x1 if encrypted else 0
            return item

        safe = f"{BUILD_KIT_ROOT}/safe.txt"
        with self.assertRaisesRegex(ValueError, "member count mismatch"):
            validate_infos([info(safe)])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_infos([info(safe), info(safe)], expected_count=2)
        with self.assertRaisesRegex(ValueError, "case/Unicode-colliding"):
            validate_infos(
                [info(f"{BUILD_KIT_ROOT}/Case.txt"), info(f"{BUILD_KIT_ROOT}/case.txt")],
                expected_count=2,
            )
        with self.assertRaisesRegex(ValueError, "case/Unicode-colliding"):
            validate_infos(
                [info(f"{BUILD_KIT_ROOT}/caf\u00e9.txt"), info(f"{BUILD_KIT_ROOT}/cafe\u0301.txt")],
                expected_count=2,
            )
        for unsafe in (
            f"{BUILD_KIT_ROOT}/a//b.txt",
            f"{BUILD_KIT_ROOT}/a/./b.txt",
            f"{BUILD_KIT_ROOT}/drive:C.txt",
            f"{BUILD_KIT_ROOT}/../escape.txt",
            f"{BUILD_KIT_ROOT}/nul\x00suffix.txt",
        ):
            with self.subTest(unsafe=unsafe), self.assertRaisesRegex(ValueError, "Unsafe TEACH ZIP path"):
                validate_infos([info(unsafe)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "Encrypted"):
            validate_infos([info(safe, encrypted=True)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "symlink"):
            validate_infos([info(safe, mode=0o120777)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "special-file"):
            validate_infos([info(safe, mode=0o010644)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "member exceeds byte limit"):
            validate_infos([info(safe, size=max_member + 1)], expected_count=1)
        expanded = [
            info(f"{BUILD_KIT_ROOT}/{index}.bin", size=max_member)
            for index in range((max_expanded // max_member) + 1)
        ]
        with self.assertRaisesRegex(ValueError, "expanded bytes exceed limit"):
            validate_infos(expanded, expected_count=len(expanded))

    def test_rotation_utility_rejection_preserves_malformed_candidate_bytes(self):
        script = ROOT / "scripts" / "rotate-teach-verifier-portability.py"
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / ZIP.name
            shutil.copy2(ZIP, candidate)
            with zipfile.ZipFile(candidate, "a") as archive:
                archive.writestr(f"{BUILD_KIT_ROOT}/unexpected.txt", b"unsafe inventory")
            before = candidate.read_bytes()
            result = subprocess.run(
                [sys.executable, str(script), "--zip", str(candidate)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("member count mismatch", result.stderr)
            self.assertEqual(candidate.read_bytes(), before)

    def test_rotation_utility_is_idempotent_and_preserves_current_identity(self):
        script = ROOT / "scripts" / "rotate-teach-verifier-portability.py"
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / ZIP.name
            shutil.copy2(ZIP, candidate)
            for _ in range(2):
                subprocess.run(
                    [sys.executable, str(script), "--zip", str(candidate)],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                self.assertEqual(candidate.stat().st_size, BUILD_KIT_BYTES)
                self.assertEqual(sha256(candidate), BUILD_KIT_SHA256)

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
