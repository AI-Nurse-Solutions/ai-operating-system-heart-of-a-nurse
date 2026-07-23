#!/usr/bin/env python3
"""Acceptance, deterministic-build, and packaging tests for FUTURE Lane 01."""

from __future__ import annotations

import contextlib
import hashlib
import io
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
PACKAGE = ROOT / "post-setup" / "packages" / "01-Student-Nurse"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Hermes-Program.md"
GUIDE = PACKAGE / "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.md"
DOCX = PACKAGE / "Nursing-Student-and-Assistant-Complete-AI-OS-with-FUTURE-SuperPowers-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
KIT_SOURCE = ROOT / "post-setup" / "build-kits" / "future-student-assistant"
BUILDER = ROOT / "scripts" / "build-future-student-assistant-build-kit.py"
ROOT_NAME = "FUTURE-Nursing-Student-Nursing-Assistant-Mission-Control-Hermes-Build-Kit-v1.0.0"
ZIP = DOWNLOADS / f"{ROOT_NAME}.zip"
RETIRED_ZIP = DOWNLOADS / ("nurse-ai-os-post-setup-" + "student-nurse.zip")
EXPECTED_BYTES = 6520918
EXPECTED_SHA256 = "b95b413fc25f990f3505fcf7af81c2c483a62da2150f4f77b371ff847b173e76"
EXPECTED_MEMBER_COUNT = 105
EXPECTED_VERIFIER_SHA256 = "172060eab15f32887edd75f8b0736de65c70c13c59b7b8c04059218c87ecd375"
RESUME = (
    "Resume FUTURE Complete Edition installation from the last approved checkpoint. "
    "Revalidate the authenticated owner, selected pathway, active context, privacy and no-PHI boundaries, "
    "academic and employer rules, clinical and role authority, permissions, component versions, current "
    "Command Center, source state, and every critical control."
)


def sha256(path: Path) -> str:
    """Return a file's SHA-256 digest."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StudentAssistantBuildKitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.program = PROGRAM.read_text(encoding="utf-8")
        cls.guide = GUIDE.read_text(encoding="utf-8")
        cls.manifest = json.loads(ROLE_MANIFEST.read_text(encoding="utf-8"))
        cls.read_first = (PACKAGE / "00-READ-FIRST.md").read_text(encoding="utf-8")
        cls.kit_manifest = json.loads((KIT_SOURCE / "RELEASE-MANIFEST.json").read_text(encoding="utf-8"))
        cls.kit_readme = (KIT_SOURCE / "README-FIRST.md").read_text(encoding="utf-8")
        cls.kit_handoff = (KIT_SOURCE / "GIVE-THIS-PACKAGE-TO-HERMES.md").read_text(encoding="utf-8")

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

    def test_public_copy_classifies_lane_one_as_self_install_build_kit(self):
        page = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Nursing Student &amp; Nursing Assistant Complete AI OS with FUTURE SuperPowers",
            "Hermes Build Kit",
            "136 canonical compatibility checks",
            "349 required execution records",
            "Every written result begins <code>Not Run</code>",
            "All eighteen optional FUTURE SuperPowers remain <code>Available Inactive</code>",
            "all ten suggested agents remain <code>PERM-P0 Disabled</code>",
            "Nursing Student, Nursing Assistant, or Bridge",
            "Self-install build-kit lanes 01, 02, 03, 04, and 06",
            "one exact Implementation Activation Card",
            EXPECTED_SHA256,
            "exactly 6,520,918 bytes (approximately 6.52 MB)",
            "Download FUTURE Build Kit",
            "For review-first lane 05",
        ):
            self.assertIn(phrase, page)
        self.assertNotIn(RETIRED_ZIP.name, page)
        self.assertNotIn("FUTURE Complete Edition Activation Card", page)
        readme = (ROOT / "post-setup" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Lanes 01, 02, 03, 04, and 06 are governed self-install Hermes build kits", readme)
        self.assertIn("Review-first lane 05 includes", readme)
        self.assertIn("The Nursing Student and Nursing Assistant download is a reproducible governed self-install Hermes build kit", readme)
        self.assertNotIn(RETIRED_ZIP.name, readme)
        current_surfaces = {
            "architecture HTML": (ROOT / "architecture-report.html").read_text(encoding="utf-8"),
            "architecture Markdown": (ROOT / "assets" / "nurse-ai-os-architecture-report.md").read_text(encoding="utf-8"),
            "dated architecture Markdown": (
                ROOT / "assets" / "2026-07-13-nurse-ai-os-updated-architecture-report.md"
            ).read_text(encoding="utf-8"),
            "media packet": (ROOT / "assets" / "nurse-ai-os-media-packet.md").read_text(encoding="utf-8"),
            "repository README": (ROOT / "README.md").read_text(encoding="utf-8"),
        }
        for label, text in current_surfaces.items():
            self.assertNotIn(RETIRED_ZIP.name, text, label)
        self.assertIn("five governed self-install Hermes build kits", current_surfaces["architecture HTML"])
        self.assertIn("five governed self-install Hermes build kits", current_surfaces["architecture Markdown"])
        self.assertIn("five governed self-install Hermes build kits", current_surfaces["media packet"])
        for architecture_pdf in (
            ROOT / "assets" / "nurse-ai-os-architecture-report.pdf",
            ROOT / "assets" / "2026-07-13-nurse-ai-os-updated-architecture-report.pdf",
        ):
            data = architecture_pdf.read_bytes()
            self.assertIn(ZIP.name.encode("ascii"), data)
            self.assertNotIn(RETIRED_ZIP.name.encode("ascii"), data)

    def test_tracked_build_kit_source_contract_and_provenance_are_exact(self):
        files = [path for path in KIT_SOURCE.rglob("*") if path.is_file()]
        self.assertEqual(len(files), EXPECTED_MEMBER_COUNT)
        self.assertEqual(self.kit_manifest["build_kit"]["version"], "1.0.0")
        self.assertEqual(self.kit_manifest["target"]["version"], "2.0.0")
        self.assertEqual(self.kit_manifest["target"]["readiness"], "not_operational_build_required")
        self.assertEqual(self.kit_manifest["counts"]["canonical_compatibility_checks"], 136)
        self.assertEqual(self.kit_manifest["counts"]["total_required_execution_records"], 349)
        self.assertEqual(self.kit_manifest["defaults"]["agents"], "PERM-P0 Disabled")
        self.assertEqual(self.kit_manifest["defaults"]["powers"], "Available Inactive")
        derivative = self.kit_manifest["public_safe_derivative"]
        self.assertEqual(
            derivative["source_zip_sha256_before_derivative"],
            "737968eac95347887eb55f3146c1d964541193e7843ea1f94b5bdc4e171a96c6",
        )
        self.assertEqual(derivative["source_zip_bytes_before_derivative"], 6520141)
        self.assertEqual(sha256(KIT_SOURCE / "tools" / "verify-build-kit.py"), EXPECTED_VERIFIER_SHA256)
        for phrase in ("build kit", "Not operational", "Before any mutation"):
            self.assertTrue(phrase in self.kit_readme or phrase in self.kit_handoff, phrase)
        for phrase in ("Implementation Activation Card", "APPROVE", "REVISE", "CANCEL"):
            self.assertIn(phrase, self.kit_handoff)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        self.assertTrue(ZIP.is_file(), ZIP)
        manifest = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["release"], "2026.07.22.1")
        record = next(item for item in manifest["packages"] if item["role"] == "Nursing Student and Nursing Assistant")
        self.assertFalse(record["install_on_download"])
        self.assertTrue(record["pre_install_disclosure_required"])
        self.assertEqual(
            record["activation"],
            "user_initiated_read_only_preflight_with_exact_implementation_activation_card",
        )
        self.assertEqual(record["package_version"], "1.0.0")
        self.assertEqual(record["legacy_source_package_version"], "2026.07.15.3")
        self.assertEqual(
            record["legacy_source_activation_contract"],
            "user_initiated_guided_complete_setup_with_combined_activation_card",
        )
        self.assertEqual(record["download"], f"downloads/{ZIP.name}")
        self.assertEqual(record["download_type"], "self_install_hermes_build_kit")
        self.assertEqual(
            record["published_state"],
            "published_not_installed_not_activated_not_operational_not_institutionally_authorized",
        )
        self.assertEqual(record["readiness"], "not_operational_build_required")
        self.assertEqual(record["build_kit_version"], "1.0.0")
        self.assertEqual(record["build_kit_member_count"], EXPECTED_MEMBER_COUNT)
        self.assertEqual(record["build_kit_verifier_sha256"], EXPECTED_VERIFIER_SHA256)
        self.assertEqual(record["ci_validation"], "tracked_source_builder_and_tracked_verifier_package_and_outer_zip")
        self.assertEqual(record["bytes"], EXPECTED_BYTES)
        self.assertEqual(record["sha256"], EXPECTED_SHA256)
        self.assertEqual(record["source_zip_bytes_before_derivative"], 6520141)
        self.assertEqual(
            record["source_zip_sha256_before_derivative"],
            "737968eac95347887eb55f3146c1d964541193e7843ea1f94b5bdc4e171a96c6",
        )
        self.assertEqual(record["target_product_id"], "future-nursing-student-assistant-mission-control")
        self.assertEqual(record["target_namespace"], "future.*")
        self.assertEqual(record["target_route"], "/nursing-students-assistants/dashboard")
        self.assertEqual(record["target_version"], "2.0.0")
        self.assertEqual(record["acceptance_tests"]["total"], 136)
        self.assertTrue(record["foundation_first"])
        self.assertTrue(record["future_overlay_second"])
        self.assertEqual(record["optional_superpowers_total"], 18)
        self.assertEqual(record["optional_superpowers_active_after_install"], 0)
        self.assertEqual(ZIP.stat().st_size, EXPECTED_BYTES)
        self.assertEqual(sha256(ZIP), EXPECTED_SHA256)
        self.assertFalse(RETIRED_ZIP.exists())
        ledger = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{EXPECTED_SHA256}  {ZIP.name}", ledger)
        self.assertNotIn(RETIRED_ZIP.name, ledger)
        with zipfile.ZipFile(ZIP) as archive:
            prefix = f"{ROOT_NAME}/"
            names = set(archive.namelist())
            expected = {
                prefix + path.relative_to(KIT_SOURCE).as_posix()
                for path in KIT_SOURCE.rglob("*")
                if path.is_file()
            }
            self.assertEqual(names, expected)
            self.assertEqual(len(names), EXPECTED_MEMBER_COUNT)
            self.assertEqual({item.date_time for item in archive.infolist()}, {(2026, 7, 20, 0, 0, 0)})
            for path in KIT_SOURCE.rglob("*"):
                if path.is_file():
                    relative = path.relative_to(KIT_SOURCE).as_posix()
                    self.assertEqual(archive.read(prefix + relative), path.read_bytes())

    def test_dedicated_builder_recreates_committed_artifact_from_scratch(self):
        namespace = runpy.run_path(str(BUILDER))
        with tempfile.TemporaryDirectory() as tmp:
            rebuilt = Path(tmp) / ZIP.name
            config = namespace["build"](rebuilt)
            self.assertEqual(config["bytes"], EXPECTED_BYTES)
            self.assertEqual(config["sha256"], EXPECTED_SHA256)
            self.assertEqual(config["member_count"], EXPECTED_MEMBER_COUNT)
            self.assertEqual(rebuilt.read_bytes(), ZIP.read_bytes())

    def test_dedicated_builder_zip_modes_ignore_host_checkout_modes(self):
        namespace = runpy.run_path(str(BUILDER))
        build = namespace["build"]
        verifier_success = subprocess.CompletedProcess(
            args=["tracked-verifier"],
            returncode=0,
            stdout="",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(KIT_SOURCE, source)
            for path in source.rglob("*"):
                if path.is_file():
                    path.chmod(0o644)
            build.__globals__["SOURCE"] = source
            rebuilt = Path(tmp) / ZIP.name
            with mock.patch.object(namespace["subprocess"], "run", return_value=verifier_success):
                build(rebuilt)
            prefix = ROOT_NAME + "/"
            with zipfile.ZipFile(rebuilt) as archive:
                modes = {
                    item.filename.removeprefix(prefix): (item.external_attr >> 16) & 0o777
                    for item in archive.infolist()
                }
            self.assertEqual(modes["tools/verify-build-kit.py"], 0o755)
            self.assertEqual(modes["source/baseline-application/start-discover.sh"], 0o755)
            self.assertEqual(modes["source/baseline-application/Start-DISCOVER.command"], 0o755)
            self.assertEqual(modes["README-FIRST.md"], 0o644)

    def test_tracked_verifier_passes_package_and_outer_zip(self):
        verifier = KIT_SOURCE / "tools" / "verify-build-kit.py"
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / ROOT_NAME
            shutil.copytree(KIT_SOURCE, package)
            completed = subprocess.run(
                [sys.executable, str(verifier), "--package", str(package), "--zip", str(ZIP)],
                cwd=package,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn("FAIL=0", completed.stdout)
        self.assertIn("WARN=0", completed.stdout)

    def test_tracked_verifier_mode_policy_is_cross_platform(self):
        namespace = runpy.run_path(str(KIT_SOURCE / "tools" / "verify-build-kit.py"))
        check_modes = namespace["check_modes"]
        checks_type = namespace["Checks"]
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "package"
            tools = package / "tools"
            tools.mkdir(parents=True)
            verifier = tools / "verify-build-kit.py"
            verifier.write_text("# test fixture\n", encoding="utf-8")
            verifier.chmod(0o644)

            posix_checks = checks_type()
            with contextlib.redirect_stdout(io.StringIO()):
                with mock.patch.object(namespace["os"], "name", "posix"):
                    check_modes(posix_checks, package)
            self.assertTrue(any("Package modes are normalized" in item for item in posix_checks.failed))

            windows_checks = checks_type()
            with contextlib.redirect_stdout(io.StringIO()):
                with mock.patch.object(namespace["os"], "name", "nt"):
                    check_modes(windows_checks, package)
            self.assertFalse(windows_checks.failed)
            self.assertTrue(
                any("not enforceable on Windows" in item for item in windows_checks.warnings),
                windows_checks.warnings,
            )

    def test_builder_rejects_tampered_tracked_source(self):
        namespace = runpy.run_path(str(BUILDER))
        validate = namespace["validate_source"]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(KIT_SOURCE, source)
            with (source / "README-FIRST.md").open("a", encoding="utf-8") as stream:
                stream.write("\nunauthorized source mutation\n")
            validate.__globals__["SOURCE"] = source
            with self.assertRaisesRegex(ValueError, "source checksum mismatch"):
                validate()

    def test_verifier_failure_preserves_existing_release_artifact(self):
        namespace = runpy.run_path(str(BUILDER))
        build = namespace["build"]
        forced_failure = subprocess.CompletedProcess(
            args=["tracked-verifier"],
            returncode=1,
            stdout="forced verifier failure",
            stderr="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / ZIP.name
            sentinel = b"previous verified artifact"
            output.write_bytes(sentinel)
            with mock.patch.object(namespace["subprocess"], "run", return_value=forced_failure):
                with self.assertRaisesRegex(RuntimeError, "Tracked FUTURE verifier failed"):
                    build(output)
            self.assertEqual(output.read_bytes(), sentinel)
            self.assertFalse(any(path.name.startswith(".future-build-") for path in output.parent.iterdir()))

    def test_builder_rejects_self_consistent_provenance_replacement(self):
        namespace = runpy.run_path(str(BUILDER))
        validate = namespace["validate_source"]
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "source"
            shutil.copytree(KIT_SOURCE, source)
            manifest_path = source / "RELEASE-MANIFEST.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["public_safe_derivative"]["source_zip_sha256_before_derivative"] = "0" * 64
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            ledger_path = source / "SHA256SUMS.txt"
            lines = ledger_path.read_text(encoding="utf-8").splitlines()
            ledger_path.write_text(
                "\n".join(
                    f"{sha256(manifest_path)}  RELEASE-MANIFEST.json" if line.endswith("  RELEASE-MANIFEST.json") else line
                    for line in lines
                )
                + "\n",
                encoding="utf-8",
            )
            validate.__globals__["SOURCE"] = source
            with self.assertRaisesRegex(ValueError, "provenance hash mismatch"):
                validate()

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
                with self.assertRaisesRegex(
                    ValueError,
                    "(?:Checksum mismatch|Trusted wrapper checksum mismatch).*00-READ-FIRST.md",
                ):
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

    def test_import_source_rejects_self_consistent_wrapper_replacement_for_every_prebuilt_role(self):
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
                wrapper = source / "00-READ-FIRST.md"
                wrapper.write_text(wrapper.read_text(encoding="utf-8") + "\nself-consistent unsafe wrapper\n", encoding="utf-8")
                refresh(source)
                function.__globals__["PACKAGES"] = root / "packages"
                function.__globals__["PACKAGES"].mkdir()
                with self.assertRaisesRegex(ValueError, "Trusted wrapper checksum mismatch"):
                    function(source_root, role)
                self.assertFalse((function.__globals__["PACKAGES"] / role["folder"]).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
