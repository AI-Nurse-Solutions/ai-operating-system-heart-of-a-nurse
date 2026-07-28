import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.deliverables import DRAFT_BANNER
from naio_integrations.packet_builder import PHASE_2_ROLES, PacketBundleBuilder
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
        cls.builder.build_phase2(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_phase2_covers_the_three_spec_roles(self):
        self.assertEqual(
            set(PHASE_2_ROLES), {"pre-licensure-student", "staff-nurse", "educator"}
        )

    def test_every_bundle_has_manifest_readme_boundary_and_templates(self):
        for role in PHASE_2_ROLES:
            bundle = self.root / role
            self.assertTrue((bundle / "manifest.json").is_file(), role)
            self.assertTrue((bundle / "README.md").is_file(), role)
            self.assertTrue((bundle / "DATA-BOUNDARY.md").is_file(), role)
            templates = list((bundle / "templates").glob("*.md"))
            self.assertGreaterEqual(len(templates), 4, role)

    def test_bundle_manifests_verify(self):
        for role in PHASE_2_ROLES:
            manifest = json.loads(
                (self.root / role / "manifest.json").read_text(encoding="utf-8")
            )
            verify_manifest(manifest)

    def test_readme_carries_the_section_19_recognitions(self):
        for role in PHASE_2_ROLES:
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
        for role in PHASE_2_ROLES:
            boundary = (self.root / role / "DATA-BOUNDARY.md").read_text(
                encoding="utf-8"
            )
            self.assertIn("Read this before first use.", boundary)
            self.assertIn("D3, D4", boundary)
            self.assertIn("never proves", boundary)
            self.assertIn("stop control", boundary)

    def test_starter_templates_match_the_catalog_and_are_drafts(self):
        catalog = PacketCatalog()
        for role in PHASE_2_ROLES:
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
            PacketBundleBuilder().build_phase2(again)
            for role in PHASE_2_ROLES:
                for path in sorted((self.root / role).rglob("*")):
                    if path.is_file():
                        twin = again / path.relative_to(self.root)
                        self.assertEqual(
                            twin.read_text(encoding="utf-8"),
                            path.read_text(encoding="utf-8"),
                            path,
                        )

    def test_unknown_role_fails_closed(self):
        from naio_integrations.packets import PacketIntegrityError

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(PacketIntegrityError):
                self.builder.build("shadow-admin", Path(tmp) / "x")


class CommittedBundleTests(unittest.TestCase):
    """The committed bundles must exactly match a fresh deterministic build."""

    def test_committed_phase2_bundles_match_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh = Path(tmp) / "packets"
            PacketBundleBuilder().build_phase2(fresh)
            for path in sorted(fresh.rglob("*")):
                if path.is_file():
                    committed = COMMITTED_ROOT / path.relative_to(fresh)
                    self.assertTrue(committed.is_file(), committed)
                    self.assertEqual(
                        committed.read_text(encoding="utf-8"),
                        path.read_text(encoding="utf-8"),
                        committed,
                    )

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

    def test_phase3_and_phase4_packets_remain_manifest_only(self):
        for role in ("leader", "licensed-clinician"):
            files = sorted(
                path.name
                for path in (COMMITTED_ROOT / role).rglob("*")
                if path.is_file()
            )
            self.assertEqual(files, ["manifest.json"], role)


if __name__ == "__main__":
    unittest.main()
