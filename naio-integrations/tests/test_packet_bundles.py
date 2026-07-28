import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.deliverables import DRAFT_BANNER
from naio_integrations.packet_builder import (
    INSTALLABLE_ROLES,
    PHASE_2_ROLES,
    PHASE_3_ROLES,
    PacketBundleBuilder,
)
from naio_integrations.packets import PacketCatalog, verify_manifest
from naio_integrations.privacy import PrivacyScreen

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_ROOT = REPO_ROOT / "mission-control" / "packets"

SECTION_19_RECOGNITIONS = (
    "Who this workspace is for",
    "What it helps you accomplish",
    "What it will never do on its own",
    "What to do next",
    "How your work and data are protected",
    "How progress is measured",
)


class PacketBundleBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = PacketBundleBuilder()
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name) / "packets"
        cls.builder.build_roles(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_phase2_covers_the_three_spec_roles(self):
        self.assertEqual(
            set(PHASE_2_ROLES), {"pre-licensure-student", "staff-nurse", "educator"}
        )

    def test_phase3_unlocks_the_leader_packet(self):
        self.assertEqual(PHASE_3_ROLES, ("leader",))
        self.assertEqual(set(INSTALLABLE_ROLES), set(PHASE_2_ROLES) | {"leader"})

    def test_every_bundle_has_manifest_readme_boundary_and_templates(self):
        for role in INSTALLABLE_ROLES:
            bundle = self.root / role
            self.assertTrue((bundle / "manifest.json").is_file(), role)
            self.assertTrue((bundle / "README.md").is_file(), role)
            self.assertTrue((bundle / "DATA-BOUNDARY.md").is_file(), role)
            templates = list((bundle / "templates").glob("*.md"))
            self.assertGreaterEqual(len(templates), 4, role)

    def test_bundle_manifests_verify(self):
        for role in INSTALLABLE_ROLES:
            manifest = json.loads(
                (self.root / role / "manifest.json").read_text(encoding="utf-8")
            )
            verify_manifest(manifest)

    def test_readme_carries_the_section_19_recognitions(self):
        for role in INSTALLABLE_ROLES:
            readme = (self.root / role / "README.md").read_text(encoding="utf-8")
            for recognition in SECTION_19_RECOGNITIONS:
                self.assertIn(recognition, readme, f"{role}: {recognition}")
            self.assertIn("Agents propose; humans judge; nurses steward.", readme)
            self.assertIn(
                "Installation does not imply employer, school, regulatory,"
                " IRB, privacy, or security approval.",
                readme,
            )

    def test_data_boundary_states_prohibitions_before_first_use(self):
        for role in INSTALLABLE_ROLES:
            boundary = (self.root / role / "DATA-BOUNDARY.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Read this before first use.", boundary)
            self.assertIn("D3, D4", boundary)
            self.assertIn("never proves", boundary)
            self.assertIn("stop control", boundary)

    def test_starter_templates_match_the_catalog_and_are_drafts(self):
        catalog = PacketCatalog()
        for role in INSTALLABLE_ROLES:
            configured = catalog.catalog["packets"][role]["starter_templates"]
            files = sorted(
                path.stem for path in (self.root / role / "templates").glob("*.md")
            )
            self.assertEqual(files, sorted(configured), role)
            for path in (self.root / role / "templates").glob("*.md"):
                self.assertIn(DRAFT_BANNER, path.read_text(encoding="utf-8"), path)

    def test_bundle_content_passes_the_privacy_screen(self):
        screen = PrivacyScreen()
        for path in sorted(self.root.rglob("*.md")):
            findings = screen.analyze(path.read_text(encoding="utf-8"))
            self.assertEqual(
                [f.entity_type for f in findings], [], f"{path} tripped the screen"
            )

    def test_bundles_are_deterministic(self):
        with tempfile.TemporaryDirectory() as tmp:
            again = Path(tmp) / "packets"
            PacketBundleBuilder().build_roles(again)
            for role in INSTALLABLE_ROLES:
                for path in sorted((self.root / role).rglob("*")):
                    if path.is_file():
                        twin = again / path.relative_to(self.root)
                        self.assertEqual(
                            twin.read_text(encoding="utf-8"),
                            path.read_text(encoding="utf-8"),
                            path,
                        )

    def test_rebuild_removes_templates_that_left_the_catalog(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "staff-nurse"
            builder = PacketBundleBuilder()
            builder.build("staff-nurse", bundle)
            stale = bundle / "templates" / "retired-template.md"
            stale.write_text("renamed out of the catalog", encoding="utf-8")
            stale_dir = bundle / "templates" / "old"
            stale_dir.mkdir()
            (stale_dir / "nested.md").write_text("stale", encoding="utf-8")
            builder.build("staff-nurse", bundle)
            self.assertFalse(stale.exists())
            self.assertFalse(stale_dir.exists())

    def test_unknown_role_fails_closed(self):
        from naio_integrations.packets import PacketIntegrityError

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PacketIntegrityError):
                self.builder.build("shadow-admin", Path(tmp) / "x")


class CommittedBundleTests(unittest.TestCase):
    """The committed bundles must exactly match a fresh deterministic build."""

    def test_committed_bundles_match_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "packets"
            PacketBundleBuilder().build_roles(fresh)
            for path in sorted(fresh.rglob("*")):
                if path.is_file():
                    committed = COMMITTED_ROOT / path.relative_to(fresh)
                    self.assertTrue(committed.is_file(), committed)
                    self.assertEqual(
                        committed.read_text(encoding="utf-8"),
                        path.read_text(encoding="utf-8"),
                        committed,
                    )

    def test_committed_bundles_carry_no_files_beyond_the_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "packets"
            PacketBundleBuilder().build_roles(fresh)
            for role in INSTALLABLE_ROLES:
                fresh_files = {
                    path.relative_to(fresh).as_posix()
                    for path in (fresh / role).rglob("*")
                    if path.is_file()
                }
                committed_files = {
                    path.relative_to(COMMITTED_ROOT).as_posix()
                    for path in (COMMITTED_ROOT / role).rglob("*")
                    if path.is_file()
                }
                self.assertEqual(committed_files, fresh_files, role)

    def test_committed_checksums_cover_the_whole_packets_tree(self):
        checksum_file = COMMITTED_ROOT / "CHECKSUMS.sha256"
        listed = {}
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            listed[name] = digest
        on_disk = {
            path.relative_to(COMMITTED_ROOT).as_posix()
            for path in COMMITTED_ROOT.rglob("*")
            if path.is_file() and path != checksum_file
        }
        self.assertEqual(set(listed), on_disk)
        for name, digest in listed.items():
            actual = hashlib.sha256((COMMITTED_ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(digest, actual, name)

    def test_phase4_packet_remains_manifest_only(self):
        for role in ("licensed-clinician",):
            files = sorted(
                path.name
                for path in (COMMITTED_ROOT / role).rglob("*")
                if path.is_file()
            )
            self.assertEqual(files, ["manifest.json"], role)


if __name__ == "__main__":
    unittest.main()
