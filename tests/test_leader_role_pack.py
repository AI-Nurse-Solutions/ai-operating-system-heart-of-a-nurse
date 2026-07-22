#!/usr/bin/env python3
"""Acceptance and release-integrity tests for the Nurse Leader LEAD build kit."""

from __future__ import annotations

import hashlib
import json
import os
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import textwrap
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
KIT_SOURCE = ROOT / "post-setup" / "build-kits" / "lead-nurse-leader"
ZIP = DOWNLOADS / "LEAD-Nurse-Leader-Manager-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
OLD_ZIP = DOWNLOADS / "nurse-ai-os-post-setup-nurse-leader-and-manager.zip"
BUILDER = ROOT / "scripts" / "build-lead-nurse-leader-build-kit.py"
SCANNER = ROOT / "scripts" / "scan-public-healthcare-artifacts.py"
VERIFIER = KIT_SOURCE / "tools" / "verify-build-kit.py"
KIT_ROOT = "LEAD-Nurse-Leader-Manager-Mission-Control-Hermes-Build-Kit-v1.0.0"
EXPECTED_BYTES = 494164
EXPECTED_SHA256 = "78293c6eaef4fa277f4afecf14eeb87b90f3385ba71be3189faaca2466c90974"
EXPECTED_VERIFIER_SHA256 = "3cc461d3b932af8c9d58e178c4c6e219e5f595f198b8b5540b9b923a7abc58c4"
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
        cls.kit_readme = (KIT_SOURCE / "README-FIRST.md").read_text(encoding="utf-8")
        cls.kit_handoff = (KIT_SOURCE / "GIVE-THIS-PACKAGE-TO-HERMES.md").read_text(encoding="utf-8")
        cls.kit_provenance = json.loads((KIT_SOURCE / "SOURCE-PROVENANCE.json").read_text(encoding="utf-8"))

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

    def test_supplied_archive_and_tracked_source_provenance_is_exact(self):
        self.assertEqual(
            self.kit_provenance["source_archive"],
            {
                "bytes": 254948,
                "filename": "Nurse-Leader-Complete-AI-OS-with-LEAD-SuperPowers-Package-v1.0.zip",
                "sha256": "1b5bcc016f56735f7d33b8ada746d971ec9ac313e5ef5339fb05382e44c0f4d8",
                "status": "user_supplied_source_archive_not_executed",
            },
        )
        records = {item["path"]: item for item in self.kit_provenance["source_files"]}
        for path in (PROGRAM, GUIDE, DOCX):
            self.assertEqual(records[path.name]["bytes"], path.stat().st_size)
            self.assertEqual(records[path.name]["sha256"], sha256(path))
        self.assertEqual(self.kit_provenance["transformations"][0]["class"], "wrapper_only")
        self.assertIn("No source content is rewritten", self.kit_provenance["transformations"][0]["description"])

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

    def test_build_kit_wrapper_is_preflight_first_and_claim_proof_separated(self):
        combined = self.kit_readme + self.kit_handoff
        for phrase in (
            "Downloading, selecting, opening, or unzipping this ZIP does **not** install anything",
            "does not contain a prebuilt operational application",
            "All checks begin `Not Run`",
            "read-only preflight",
            "Implementation Activation Card",
            "APPROVE",
            "REVISE",
            "CANCEL",
            "No route is assigned by the source package",
            "PERM-P0 Disabled",
            "Available Inactive",
            "Nothing continues invisibly",
            "Core operational; AI setup pending",
            "Not operational",
        ):
            self.assertIn(phrase, combined)
        for forbidden in (
            "already-installed application",
            "automatically operational",
            "institution-approved by download",
        ):
            self.assertNotIn(forbidden, combined)

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

    def test_public_lane_copy_classifies_lead_as_self_install_build_kit(self):
        page = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        for phrase in (
            "Nurse Leader Complete AI OS with LEAD SuperPowers",
            "transparent self-install Hermes build kit",
            "one exact Implementation Activation Card",
            "113 canonical checks in total",
            "Written checks begin <code>Not Run</code>",
            "No application route is preassigned",
            "PERM-P0 Disabled",
            "exactly 494,164 bytes (approximately 0.49 MB)",
            EXPECTED_SHA256,
            "Download LEAD Build Kit",
            "Browse tracked package source on GitHub",
            "tree/main/post-setup\"",
            "What happens after a self-install build-kit download?",
            "Core operational; AI setup pending",
            "Self-install build-kit lanes 01, 02, 03, and 04",
            "Complete Edition lane 06",
        ):
            self.assertIn(phrase, page)
        self.assertIn("rel=\"icon\" href=\"data:image/svg+xml", page)
        self.assertIn(".role-pack-card code{white-space:normal;overflow-wrap:anywhere;word-break:break-word}", page)
        self.assertNotIn(OLD_ZIP.name, page)
        self.assertNotIn("Nurse Leader Complete Edition Activation Card", page)

        readme = (ROOT / "post-setup" / "README.md").read_text(encoding="utf-8")
        self.assertIn("Lanes 01, 02, 03, and 04 are governed self-install Hermes build kits", readme)
        self.assertIn("Review-first lane 05 includes", readme)
        self.assertIn("The Nurse Leader and Manager download is a reproducible governed self-install Hermes build kit", readme)
        self.assertIn("All sixteen optional powers remain `Available Inactive`", readme)
        self.assertIn("No route is preassigned", readme)
        self.assertNotIn(OLD_ZIP.name, readme)
        current_surfaces = {
            "architecture HTML": (ROOT / "architecture-report.html").read_text(encoding="utf-8"),
            "architecture Markdown": (ROOT / "assets" / "nurse-ai-os-architecture-report.md").read_text(encoding="utf-8"),
            "media packet": (ROOT / "assets" / "nurse-ai-os-media-packet.md").read_text(encoding="utf-8"),
            "repository README": (ROOT / "README.md").read_text(encoding="utf-8"),
        }
        for label, text in current_surfaces.items():
            self.assertNotIn("Staff Nurse and Quality Contributor Complete Edition", text, label)
            self.assertNotIn("Nurse Leader and Manager Complete Edition", text, label)
        self.assertIn("four governed self-install Hermes build kits", current_surfaces["architecture HTML"])
        self.assertIn("four governed self-install Hermes build kits", current_surfaces["architecture Markdown"])
        self.assertIn("four governed self-install Hermes build kits", current_surfaces["media packet"])
        self.assertIn("Lanes 01, 02, 03, and 04 are governed self-install Hermes build kits", current_surfaces["repository README"])
        self.assertIn("separate post-merge gate", current_surfaces["architecture Markdown"])
        for architecture_source in (
            ROOT / "assets" / "nurse-ai-os-architecture-report.md",
            ROOT / "assets" / "2026-07-13-nurse-ai-os-updated-architecture-report.md",
        ):
            text = architecture_source.read_text(encoding="utf-8")
            self.assertIn(ZIP.name, text)
            self.assertNotIn(OLD_ZIP.name, text)
        for architecture_pdf in (
            ROOT / "assets" / "nurse-ai-os-architecture-report.pdf",
            ROOT / "assets" / "2026-07-13-nurse-ai-os-updated-architecture-report.pdf",
        ):
            data = architecture_pdf.read_bytes()
            self.assertIn(ZIP.name.encode("ascii"), data)
            self.assertNotIn(OLD_ZIP.name.encode("ascii"), data)

    def test_download_is_manifested_and_byte_integrity_is_verifiable(self):
        self.assertTrue(ZIP.is_file(), ZIP)
        self.assertFalse(OLD_ZIP.exists(), OLD_ZIP)
        self.assertEqual(ZIP.stat().st_size, EXPECTED_BYTES)
        self.assertEqual(sha256(ZIP), EXPECTED_SHA256)
        manifest = json.loads((DOWNLOADS / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["release"], "2026.07.22.1")
        record = next(item for item in manifest["packages"] if item["role"] == "Nurse Leader and Manager")
        self.assertFalse(record["install_on_download"])
        self.assertTrue(record["pre_install_disclosure_required"])
        self.assertEqual(record["activation"], "user_initiated_guided_complete_setup_with_combined_activation_card")
        self.assertEqual(record["acceptance_tests"]["total"], 113)
        self.assertTrue(record["foundation_first"])
        self.assertTrue(record["lead_overlay_second"])
        self.assertEqual(record["download"], f"downloads/{ZIP.name}")
        self.assertEqual(record["download_type"], "self_install_hermes_build_kit")
        self.assertEqual(record["build_kit_version"], "1.0.0")
        self.assertEqual(record["published_state"], "published_not_installed_not_activated_not_operational_not_institutionally_authorized")
        self.assertEqual(record["readiness"], "not_operational_build_required")
        self.assertEqual(record["bytes"], EXPECTED_BYTES)
        self.assertEqual(record["sha256"], EXPECTED_SHA256)
        self.assertEqual(record["build_kit_member_count"], 16)
        self.assertEqual(record["build_kit_root"], KIT_ROOT)
        self.assertEqual(record["build_kit_verifier_sha256"], EXPECTED_VERIFIER_SHA256)
        self.assertEqual(record["source_zip_sha256"], "1b5bcc016f56735f7d33b8ada746d971ec9ac313e5ef5339fb05382e44c0f4d8")
        self.assertEqual(record["target_product_id"], "NAIO-NL-COMPLETE-LEAD-1.0")
        self.assertEqual(record["target_namespace"], "nl_lead.*")
        self.assertEqual(record["target_route_assignment"], "activation_card_required_no_route_preassigned")
        self.assertNotIn("target_route", record)
        self.assertEqual(record["build_kit_counts"]["canonical_total_checks"], 113)
        self.assertEqual(record["ci_validation"], "tracked_source_builder_and_tracked_verifier_package_and_outer_zip")
        ledger = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{EXPECTED_SHA256}  {ZIP.name}", ledger)
        self.assertNotIn(OLD_ZIP.name, ledger)
        with zipfile.ZipFile(ZIP) as archive:
            names = archive.namelist()
            prefix = KIT_ROOT + "/"
            self.assertEqual(len(names), 16)
            self.assertEqual(len(names), len(set(names)))
            for required in (
                "README-FIRST.md",
                "GIVE-THIS-PACKAGE-TO-HERMES.md",
                "IMPLEMENTATION-ACTIVATION-CARD.md",
                "LICENSE",
                "FINAL-HANDOFF-REPORT.md",
                "RELEASE-MANIFEST.json",
                "SOURCE-INVENTORY.json",
                "SOURCE-PROVENANCE.json",
                "SHA256SUMS.txt",
                "tools/verify-build-kit.py",
            ):
                self.assertIn(prefix + required, names)
            kit_manifest = json.loads(archive.read(prefix + "RELEASE-MANIFEST.json"))
            self.assertEqual(kit_manifest["target"]["readiness"], "not_operational_build_required")
            self.assertEqual(kit_manifest["target"]["route_assignment"], "activation_card_required_no_route_preassigned")
            self.assertEqual(kit_manifest["counts"]["canonical_total_checks"], 113)
            self.assertEqual(kit_manifest["defaults"]["agents"], "PERM-P0 Disabled")
            self.assertEqual(kit_manifest["defaults"]["powers"], "Available Inactive")
            source_prefix = prefix + "source/03-Nurse-Leader-and-Manager/"
            for path in PACKAGE.iterdir():
                if path.is_file():
                    self.assertIn(source_prefix + path.name, names)
                    self.assertEqual(archive.read(source_prefix + path.name), path.read_bytes())

    def test_builder_is_deterministic_and_executes_tracked_verifier(self):
        before = (ZIP.stat().st_size, sha256(ZIP))
        completed = subprocess.run(
            [sys.executable, str(BUILDER)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("LEAD_BUILD_KIT_VERIFICATION=passed", completed.stdout)
        self.assertIn("outer_zip=verified", completed.stdout)
        self.assertEqual((ZIP.stat().st_size, sha256(ZIP)), before)

    def test_standalone_builder_rejects_role_manifest_and_ledger_drift(self):
        namespace = runpy.run_path(str(BUILDER))
        verify = namespace["verify_role_package"]
        provenance = self.kit_provenance
        with tempfile.TemporaryDirectory() as temporary:
            role_copy = Path(temporary) / PACKAGE.name
            shutil.copytree(PACKAGE, role_copy)
            verify.__globals__["SOURCE"] = role_copy
            manifest_path = role_copy / "ROLE-PACK.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["automatic_memory"] = True
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "safe default changed"):
                verify(provenance)

            shutil.rmtree(role_copy)
            shutil.copytree(PACKAGE, role_copy)
            verify.__globals__["SOURCE"] = role_copy
            wrapper = role_copy / "00-READ-FIRST.md"
            with wrapper.open("a", encoding="utf-8") as handle:
                handle.write("\nunauthorized wrapper drift\n")
            ledger_path = role_copy / "PACKAGE-CHECKSUMS.sha256"
            ledger_lines = [
                f"{sha256(wrapper)}  00-READ-FIRST.md" if line.endswith("  00-READ-FIRST.md") else line
                for line in ledger_path.read_text(encoding="utf-8").splitlines()
            ]
            ledger_path.write_text("\n".join(ledger_lines) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "trusted wrapper checksum mismatch"):
                verify(provenance)

    def test_standalone_builder_rejects_supplied_source_hash_drift(self):
        namespace = runpy.run_path(str(BUILDER))
        verify = namespace["verify_role_package"]
        provenance = json.loads(json.dumps(self.kit_provenance))
        provenance["source_files"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "provenance hashes changed"):
            verify(provenance)

    def test_tracked_verifier_rejects_tampered_package(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with zipfile.ZipFile(ZIP) as archive:
                archive.extractall(root)
            package = root / KIT_ROOT
            good = subprocess.run(
                [sys.executable, str(VERIFIER), "--package", str(package), "--zip", str(ZIP)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertEqual(good.returncode, 0, good.stdout)
            with (package / "README-FIRST.md").open("a", encoding="utf-8") as handle:
                handle.write("\nunauthorized change\n")
            bad = subprocess.run(
                [sys.executable, str(VERIFIER), "--package", str(package)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertNotEqual(bad.returncode, 0, bad.stdout)
            self.assertIn("verification=failed", bad.stdout.lower())

            (package / "UNDECLARED.txt").write_text("unexpected", encoding="utf-8")
            extra = subprocess.run(
                [sys.executable, str(VERIFIER), "--package", str(package)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertNotEqual(extra.returncode, 0, extra.stdout)
            self.assertIn("unexpected package files", extra.stdout)

    def test_outer_verifier_rejects_size_mismatch_before_reading_member(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            package = root / KIT_ROOT
            forged = root / "forged.zip"
            with zipfile.ZipFile(ZIP) as source:
                source.extractall(root)
                with zipfile.ZipFile(forged, "w") as target:
                    for info in source.infolist():
                        payload = source.read(info)
                        if info.filename.endswith("/README-FIRST.md"):
                            payload += b"oversized"
                        target.writestr(info, payload)
            blocked = subprocess.run(
                [sys.executable, str(VERIFIER), "--package", str(package), "--zip", str(forged)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertNotEqual(blocked.returncode, 0, blocked.stdout)
            self.assertIn("outer ZIP size mismatch", blocked.stdout)

    def test_public_scanner_handles_direct_archives_and_textlike_files(self):
        clean = subprocess.run(
            [sys.executable, str(SCANNER), str(ZIP), "--label", "LEAD-DIRECT"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(clean.returncode, 0, clean.stdout)
        self.assertIn("files=1 compressed=recursive", clean.stdout)
        with tempfile.TemporaryDirectory() as temporary:
            probe = Path(temporary) / "unsafe.zip"
            with zipfile.ZipFile(probe, "w") as archive:
                archive.writestr(".env", "API_KEY=abcdefghijklmnop")
            blocked = subprocess.run(
                [sys.executable, str(SCANNER), str(probe), "--label", "PROBE"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            self.assertNotEqual(blocked.returncode, 0, blocked.stdout)
            self.assertIn("public-safety scan failed", blocked.stdout)

    def test_public_scanner_cannot_skip_key_extensions_or_corrupt_utf8(self):
        scanner = runpy.run_path(str(SCANNER))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            pem = root / "server.pem"
            key = root / "private.key"
            env = root / "corrupt.env"
            pem.write_bytes(b"-----BEGIN PRIVATE KEY-----\nredacted\n")
            key.write_bytes(b"\xff-----BEGIN PRIVATE KEY-----\nredacted\n")
            env.write_bytes(b"\xffTOKEN=abcdefghijklmnop")
            findings = scanner["scan_paths"]([pem, key, env])
        labels = [label for label, _ in findings]
        self.assertEqual(labels.count("private key"), 2)
        self.assertEqual(labels.count("generic api key"), 1)

    def test_switchboard_guard_accepts_post_merge_steady_state(self):
        workflow = (ROOT / ".github" / "workflows" / "switchboard.yml").read_text(encoding="utf-8")
        marker = "python3 - <<'PY'\n"
        self.assertIn(marker, workflow)
        embedded = workflow.split(marker, 1)[1].split("\n          PY", 1)[0]
        script = textwrap.dedent(embedded)
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env={**os.environ, "BASE_SHA": head},
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout)
        self.assertIn("ROLE_DOWNLOAD_MIGRATION_GUARD=passed mode=steady-state", completed.stdout)

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
                elif role["label"] != "Nurse Leader and Manager":
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
