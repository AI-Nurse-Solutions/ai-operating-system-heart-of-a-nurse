#!/usr/bin/env python3
"""Acceptance and packaging tests for the USA-only Nurse Practitioner lane."""

from __future__ import annotations

import ast
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
PACKAGE = ROOT / "post-setup" / "packages" / "06-Nurse-Practitioner-USA"
DOWNLOADS = ROOT / "post-setup" / "downloads"
PROGRAM = PACKAGE / "NP-Complete-AI-OS-with-Wings-Hermes-Program.md"
GUIDE = PACKAGE / "NP-Complete-AI-OS-with-Wings-Setup-Guide.md"
DOCX = PACKAGE / "NP-Complete-AI-OS-with-Wings-Setup-Guide.docx"
ROLE_MANIFEST = PACKAGE / "ROLE-PACK.json"
ZIP = DOWNLOADS / "WINGS-Nurse-Practitioner-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0.zip"
BUILD_KIT_ROOT = "WINGS-Nurse-Practitioner-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0"
BUILD_KIT_BYTES = 7697078
BUILD_KIT_SHA256 = "48461f307d1c2639d35467f803d1fd8e5e1da16e69d57b88eb9dbf987bf652fc"
BUILD_KIT_MEMBER_COUNT = 131
BUILD_KIT_VERIFIER_SHA256 = "72d1b4628c9ad578e9579ce3eec86de9e4b1637b21fd3f6415115250333f6b1c"
SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE = "7a7ec1b59d1fd31a37aa28b5cc346f78bdb4e516164a91a9c28383fc77b65501"
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

    def test_public_surfaces_do_not_overclaim_wings_class_or_tracked_build_source(self):
        resources = (ROOT / "resources.html").read_text(encoding="utf-8")
        post_setup = (ROOT / "post-setup" / "index.html").read_text(encoding="utf-8")
        self.assertIn("USA-only Nurse Practitioner self-install build kit", resources)
        self.assertNotIn("USA-only Nurse Practitioner Complete Edition", resources)
        self.assertIn("Governed build-kit ZIPs are checksum-pinned", post_setup)
        self.assertNotIn(
            "Every role package and build-kit wrapper remains visible and inspectable",
            post_setup,
        )

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
        self.assertEqual(
            record["activation"],
            "user_initiated_read_only_preflight_with_exact_wings_implementation_activation_card",
        )
        self.assertEqual(record["legacy_source_activation_contract"], "user_initiated_guided_complete_setup_with_combined_activation_card")
        self.assertEqual(record["legacy_source_package_version"], "2026.07.14.2")
        self.assertEqual(record["package_version"], "1.0.0")
        self.assertEqual(record["build_kit_version"], "1.0.0")
        self.assertEqual(record["acceptance_tests"]["total"], 145)
        self.assertEqual(record["download_type"], "self_install_hermes_build_kit")
        self.assertEqual(record["readiness"], "not_operational_build_required")
        self.assertEqual(record["published_state"], "published_not_installed_not_activated_not_operational_not_institutionally_authorized")
        self.assertEqual(record["target_product"], "NP WINGS — Nurse Practitioner Life, Practice & Purpose Mission Control")
        self.assertEqual(record["target_route"], "/nurse-practitioners/dashboard")
        self.assertEqual(record["build_kit_member_count"], BUILD_KIT_MEMBER_COUNT)
        self.assertEqual(record["build_kit_root"], BUILD_KIT_ROOT)
        self.assertEqual(record["build_kit_verifier_sha256"], BUILD_KIT_VERIFIER_SHA256)
        self.assertEqual(record["source_zip_sha256_before_derivative"], SOURCE_ZIP_SHA256_BEFORE_DERIVATIVE)
        self.assertEqual(record["bytes"], BUILD_KIT_BYTES)
        self.assertEqual(record["sha256"], BUILD_KIT_SHA256)
        self.assertEqual(record["sha256"], sha256(ZIP))
        ledger = (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8")
        self.assertIn(f"{sha256(ZIP)}  {ZIP.name}", ledger)
        with zipfile.ZipFile(ZIP) as archive:
            self.assertEqual(len(archive.infolist()), BUILD_KIT_MEMBER_COUNT)
            names = set(archive.namelist())
            self.assertIn(f"{BUILD_KIT_ROOT}/README-FIRST.md", names)
            self.assertIn(f"{BUILD_KIT_ROOT}/GIVE-THIS-PACKAGE-TO-HERMES.md", names)
            self.assertIn(f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json", names)
            self.assertIn(f"{BUILD_KIT_ROOT}/SHA256SUMS.txt", names)
            release = json.loads(archive.read(f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json"))
            self.assertEqual(release["target"]["readiness"], "not_operational_build_required")
            self.assertEqual(release["target"]["country_availability"], ["United States"])
            self.assertEqual(release["counts"]["total_required_execution_records"], 410)
            self.assertEqual(release["counts"]["superpowers"], 15)
            verifier_sha = hashlib.sha256(archive.read(f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py")).hexdigest()
            self.assertEqual(verifier_sha, BUILD_KIT_VERIFIER_SHA256)

    def test_public_checksum_ledger_is_complete_and_matches_every_archive(self):
        ledger = {}
        for line in (DOWNLOADS / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+\.zip)", line)
            if match is None:
                self.fail(f"Invalid checksum-ledger line: {line!r}")
            filename = match.group(2)
            self.assertNotIn(filename, ledger)
            ledger[filename] = match.group(1)
        archives = {path.name for path in DOWNLOADS.glob("*.zip")}
        self.assertEqual(set(ledger), archives)
        for filename, expected in ledger.items():
            self.assertEqual(sha256(DOWNLOADS / filename), expected, filename)

    def test_shared_builder_keeps_shift_and_wings_configs(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        configs = namespace["BUILD_KIT_DOWNLOADS"]
        self.assertIn("staff-nurse", configs)
        self.assertIn("nurse-practitioner-usa", configs)
        wings_config = configs["nurse-practitioner-usa"]
        self.assertEqual(wings_config["country_availability"], ["United States"])
        self.assertEqual(wings_config["target"]["country_availability"], ["United States"])

    def test_shared_builder_rejects_unsafe_metadata_before_crc_or_payload_reads(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "build-post-setup-role-packs.py"))
        validate = namespace["validate_build_kit_zip"]
        config = dict(namespace["BUILD_KIT_DOWNLOADS"]["nurse-practitioner-usa"])
        role = next(item for item in namespace["ROLES"] if item["slug"] == "nurse-practitioner-usa")
        with zipfile.ZipFile(ZIP) as archive:
            baseline = archive.infolist()

        ordinary_index = next(
            index
            for index, item in enumerate(baseline)
            if not item.filename.endswith("/tools/verify-build-kit.py")
        )

        def mutated(change):
            infos = [copy.copy(item) for item in baseline]
            change(infos[ordinary_index])
            return infos

        def raw_nul(item):
            item.orig_filename = item.filename + "\x00alias"

        def raw_alias(item):
            item.orig_filename = item.filename + ".alias"

        def noncanonical(item):
            item.filename = f"{BUILD_KIT_ROOT}/a//b.txt"
            item.orig_filename = item.filename

        def encrypted(item):
            item.flag_bits |= 0x1

        def unsupported_compression(item):
            item.compress_type = zipfile.ZIP_BZIP2

        def unexpected_executable(item):
            item.external_attr = 0o100755 << 16

        def symlink(item):
            item.external_attr = 0o120777 << 16

        def oversized(item):
            item.file_size = namespace["MAX_BUILD_KIT_MEMBER_BYTES"] + 1

        cases = {
            "raw-nul": mutated(raw_nul),
            "raw-alias": mutated(raw_alias),
            "noncanonical": mutated(noncanonical),
            "encrypted": mutated(encrypted),
            "unsupported-compression": mutated(unsupported_compression),
            "unexpected-executable": mutated(unexpected_executable),
            "symlink": mutated(symlink),
            "oversized": mutated(oversized),
        }

        for label, infos in cases.items():
            fake = mock.MagicMock()
            fake.__enter__.return_value = fake
            fake.__exit__.return_value = False
            fake.infolist.return_value = infos
            fake.testzip.side_effect = AssertionError("CRC/payload touched")
            fake.read.side_effect = AssertionError("payload touched")
            with self.subTest(label=label), mock.patch.object(zipfile, "ZipFile", return_value=fake):
                with self.assertRaises(ValueError):
                    validate(role, config)
                fake.testzip.assert_not_called()
                fake.read.assert_not_called()

    def test_wings_country_boundary_is_archive_native_and_verified(self):
        with zipfile.ZipFile(ZIP) as archive:
            manifest = json.loads(archive.read(f"{BUILD_KIT_ROOT}/RELEASE-MANIFEST.json"))
            self.assertEqual(manifest["target"]["country_availability"], ["United States"])
            for name in ("README-FIRST.md", "GIVE-THIS-PACKAGE-TO-HERMES.md"):
                text = archive.read(f"{BUILD_KIT_ROOT}/{name}").decode("utf-8")
                self.assertIn("available only in the United States", text)
                self.assertIn("stop before build mutation", text)
            verifier = archive.read(f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py").decode("utf-8")
            self.assertIn("USA-only availability is embedded in both Hermes entrypoints", verifier)

    def test_country_boundary_rotation_is_byte_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / ZIP.name
            shutil.copy2(ZIP, candidate)
            subprocess.run(
                [sys.executable, str(ROOT / "scripts" / "rotate-wings-country-boundary.py"), "--zip", str(candidate)],
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertEqual(candidate.stat().st_size, BUILD_KIT_BYTES)
            self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), BUILD_KIT_SHA256)

    def test_rotation_utility_rejects_unsafe_metadata_before_payload_reads(self):
        namespace = runpy.run_path(str(ROOT / "scripts" / "rotate-wings-country-boundary.py"))
        validate_infos = namespace["validate_infos"]
        max_member = namespace["MAX_MEMBER_BYTES"]
        max_expanded = namespace["MAX_EXPANDED_BYTES"]
        verifier_name = f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py"

        def info(
            name: str,
            *,
            mode: int = 0o100644,
            size: int = 1,
            encrypted: bool = False,
            compression: int = zipfile.ZIP_DEFLATED,
        ) -> zipfile.ZipInfo:
            item = zipfile.ZipInfo(name)
            item.external_attr = mode << 16
            item.file_size = size
            item.compress_size = 1
            item.flag_bits = 0x1 if encrypted else 0
            item.compress_type = compression
            return item

        with self.assertRaisesRegex(ValueError, "member count mismatch"):
            validate_infos([info(verifier_name)])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            safe_name = f"{BUILD_KIT_ROOT}/safe.txt"
            validate_infos([info(safe_name), info(safe_name)], expected_count=2)
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
        for unsafe, message in (
            (f"{BUILD_KIT_ROOT}/a//b.txt", "Unsafe WINGS ZIP path"),
            (f"{BUILD_KIT_ROOT}/a/./b.txt", "Unsafe WINGS ZIP path"),
            (f"{BUILD_KIT_ROOT}/drive:C.txt", "Unsafe WINGS ZIP path"),
            (f"{BUILD_KIT_ROOT}/../escape.txt", "Unsafe WINGS ZIP path"),
            (f"{BUILD_KIT_ROOT}/nul\x00suffix.txt", "raw/normalized path mismatch"),
        ):
            with self.subTest(unsafe=unsafe), self.assertRaisesRegex(ValueError, message):
                validate_infos([info(unsafe)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "Encrypted"):
            validate_infos([info(verifier_name, encrypted=True)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "Unsupported.*compression"):
            validate_infos([info(verifier_name, compression=zipfile.ZIP_BZIP2)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "mode mismatch"):
            validate_infos([info(f"{BUILD_KIT_ROOT}/unexpected.sh", mode=0o100755)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "mode mismatch"):
            validate_infos([info(verifier_name, mode=0o120777)], expected_count=1)
        with self.assertRaisesRegex(ValueError, "member exceeds byte limit"):
            validate_infos([info(verifier_name, mode=0o100755, size=max_member + 1)], expected_count=1)
        expanded = [
            info(f"{BUILD_KIT_ROOT}/{index}.bin", size=max_member)
            for index in range((max_expanded // max_member) + 1)
        ]
        with self.assertRaisesRegex(ValueError, "expanded bytes exceed limit"):
            validate_infos(expanded, expected_count=len(expanded))
        with self.assertRaisesRegex(ValueError, "file/directory collision"):
            validate_infos(
                [info(f"{BUILD_KIT_ROOT}/node"), info(f"{BUILD_KIT_ROOT}/node/child.txt")],
                expected_count=2,
            )

        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / ZIP.name
            shutil.copy2(ZIP, candidate)
            with zipfile.ZipFile(candidate, "a") as archive:
                archive.writestr(f"{BUILD_KIT_ROOT}/unexpected.txt", b"unsafe inventory")
            before = candidate.read_bytes()
            with mock.patch.object(
                zipfile.ZipFile, "testzip", side_effect=AssertionError("CRC/payload touched")
            ), mock.patch.object(
                zipfile.ZipFile, "read", side_effect=AssertionError("payload touched")
            ):
                with self.assertRaisesRegex(ValueError, "member count mismatch"):
                    namespace["load_entries"](candidate)
            self.assertEqual(candidate.read_bytes(), before)

    def test_bundled_verifier_documentation_and_portability_contract_are_archive_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            extracted = Path(tmp) / "package"
            namespace = runpy.run_path(str(ROOT / "scripts" / "rotate-wings-country-boundary.py"))
            with zipfile.ZipFile(ZIP) as archive:
                namespace["validate_infos"](archive.infolist())
                self.assertIsNone(archive.testzip())
                archive.extractall(extracted)
                governed_command = (
                    "python3 tools/verify-build-kit.py --package . "
                    f"--zip ../{ZIP.name}"
                )
                for document in ("INSTALL.md", "README.md", "START_HERE.md"):
                    text = archive.read(f"{BUILD_KIT_ROOT}/{document}").decode("utf-8")
                    self.assertIn(governed_command, text)
                    self.assertNotIn(
                        "`python3 tools/verify-build-kit.py --package .`",
                        text,
                    )
                install = archive.read(f"{BUILD_KIT_ROOT}/INSTALL.md").decode("utf-8")
                self.assertIn("Require the trusted `CHECKSUMS.sha256` sidecar", install)
                self.assertIn("authenticated publisher channel", install)
                self.assertIn("before extraction", install)
                self.assertIn("Stop if the sidecar is missing", install)
                self.assertNotIn("before extraction when available", install)
                verifier_path = f"{BUILD_KIT_ROOT}/tools/verify-build-kit.py"
                verifier_source = archive.read(verifier_path).decode("utf-8")
                ast.parse(verifier_source)
                self.assertIn('parser.add_argument("--zip", dest="zip_path", type=Path)', verifier_source)
                self.assertIn(
                    'enforce_modes=args.zip_path is None and os.name != "nt"',
                    verifier_source,
                )
                self.assertIn(
                    "check_outer_zip(c, package, args.zip_path.resolve(), args.require_release_companions)",
                    verifier_source,
                )
                verifier_mode = (archive.getinfo(verifier_path).external_attr >> 16) & 0o777
                self.assertEqual(verifier_mode, 0o755)
            self.assertTrue((extracted / BUILD_KIT_ROOT / "tools" / "verify-build-kit.py").is_file())

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
                if not role.get("prebuilt"):
                    (source_root / role["source"]).mkdir()
                elif role["label"] != "Nurse Practitioner (USA)":
                    shutil.copytree(
                        ROOT / "post-setup" / "packages" / role["folder"],
                        source_root / role["folder"],
                    )
            build.__globals__["PACKAGES"] = root / "packages"
            build.__globals__["DOWNLOADS"] = root / "downloads"
            with self.assertRaisesRegex(FileNotFoundError, "06-Nurse-Practitioner-USA"):
                build(source_root)
            self.assertEqual(list((root / "packages").iterdir()), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
