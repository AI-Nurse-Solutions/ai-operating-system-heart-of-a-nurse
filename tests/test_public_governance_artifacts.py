import importlib
import importlib.util
import re
import runpy
import shutil
import stat
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

PYPDF_AVAILABLE = importlib.util.find_spec("pypdf") is not None


ROOT = Path(__file__).resolve().parents[1]
GOVERNANCE_SOURCE = ROOT / "governance-kit"
GOVERNANCE_ZIP = ROOT / "assets" / "governance-kit.zip"
STARTER_SOURCE = ROOT / "starter-kit" / "My-Nurse-AI-OS"
STARTER_ZIP = ROOT / "assets" / "nurse-ai-os-starter-kit.zip"
SIDE_GIG_SOURCE = STARTER_SOURCE / "03-Community-Entrepreneurship" / "Nurse-AI-Side-Gig-Starter-Kit"
SIDE_GIG_ZIP = ROOT / "assets" / "nurse-ai-side-gig-starter-kit.zip"
PUBLIC_DOCUMENT_SOURCES = (
    ROOT / "assets" / "30-day-roadmap.md",
    ROOT / "assets" / "founding-year-guide.md",
    ROOT / "assets" / "hermes-cheat-sheet.md",
    ROOT / "assets" / "hermes-essentials-guide.md",
    ROOT / "assets" / "hermes-power-guide.md",
    ROOT / "assets" / "lamp-huddle.md",
    ROOT / "assets" / "make-it-yours-six-workflows.md",
    ROOT / "assets" / "nurse-ai-os-workbook.md",
    ROOT / "assets" / "safety-rules-edena.md",
)
PUBLIC_DOCUMENT_PDFS = tuple(path.with_suffix(".pdf") for path in PUBLIC_DOCUMENT_SOURCES)
RESOURCE_PAGES = (ROOT / "resources.html",) + tuple(
    ROOT / locale / "resources.html"
    for locale in ("es", "tl", "zh", "ar", "vi", "ru", "hi", "fr")
)


class PublicGovernanceArtifactsTest(unittest.TestCase):
    def test_active_governance_sources_do_not_invent_names_or_entities(self) -> None:
        sources = list(PUBLIC_DOCUMENT_SOURCES)
        sources.extend(path for path in GOVERNANCE_SOURCE.rglob("*") if path.is_file())
        sources.extend(path for path in STARTER_SOURCE.rglob("*") if path.is_file())
        prohibited = (
            "Ethical Design & Enablement for Nursing Augmentation",
            "Diseño ético y habilitación para ampliar las capacidades de enfermería",
            "© NAIO Institute",
            "$1,500–$2,999 professional program",
        )
        for path in sources:
            text = path.read_text(encoding="utf-8")
            for phrase in prohibited:
                self.assertNotIn(phrase, text, f"{path.relative_to(ROOT)} contains {phrase!r}")

    def test_public_governance_kit_uses_directive_v1_1_dimensions(self) -> None:
        governance = (GOVERNANCE_SOURCE / "GOVERNANCE.yaml").read_text(encoding="utf-8")
        for required in (
            "risk_tiers:",
            "data_classes:",
            "action_modes:",
            "Red-P:",
            "Red-E:",
            'action: "Recommend"',
            'enforcement: "advisory instructions only; no mechanical control enforcement"',
        ):
            self.assertIn(required, governance)
        self.assertIn('eligible_actions: ["Observe", "Draft"]', governance)
        self.assertNotRegex(governance, r"(?m)^automation_levels:")
        self.assertNotRegex(governance, r"(?m)^\s+L[0-5]:")
        green = re.search(r"(?ms)^  Green:\n(?P<body>.*?)(?=^  Yellow:)", governance)
        self.assertIsNotNone(green)
        assert green is not None
        self.assertNotIn("Recommend", green.group("body"))

    def test_governance_zip_exactly_matches_reviewed_sources(self) -> None:
        expected = {}
        for path in GOVERNANCE_SOURCE.rglob("*"):
            mode = path.lstat().st_mode
            self.assertFalse(stat.S_ISLNK(mode), path.relative_to(ROOT))
            if stat.S_ISDIR(mode):
                continue
            self.assertTrue(stat.S_ISREG(mode), path.relative_to(ROOT))
            expected[path.relative_to(GOVERNANCE_SOURCE).as_posix()] = path.read_bytes()
        with zipfile.ZipFile(GOVERNANCE_ZIP) as archive:
            members = archive.infolist()
            self.assertEqual([info.filename for info in members], sorted(expected))
            for info in members:
                self.assertFalse(info.is_dir())
                self.assertEqual(info.date_time, (2026, 7, 25, 0, 0, 0))
                self.assertEqual((info.external_attr >> 16) & 0o170000, 0o100000)
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)
                self.assertEqual(archive.read(info), expected[info.filename])

    def test_governance_builder_rejects_source_symlink_before_payload_read(self) -> None:
        namespace = runpy.run_path(str(ROOT / "tools" / "build-governance-kit.py"))
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            source = temporary_root / "governance-kit"
            shutil.copytree(GOVERNANCE_SOURCE, source)
            outside = temporary_root / "outside.md"
            outside.write_text("must not be packaged", encoding="utf-8")
            (source / "symlink-escape.md").symlink_to(outside)
            build = namespace["build"]
            build.__globals__["SOURCE"] = source
            output = temporary_root / "governance-kit.zip"
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                build(output)

    def test_starter_zip_exactly_matches_reviewed_sources(self) -> None:
        expected = {}
        for path in STARTER_SOURCE.rglob("*"):
            mode = path.lstat().st_mode
            self.assertFalse(stat.S_ISLNK(mode), path.relative_to(ROOT))
            if stat.S_ISDIR(mode):
                continue
            self.assertTrue(stat.S_ISREG(mode), path.relative_to(ROOT))
            member = f"My-Nurse-AI-OS/{path.relative_to(STARTER_SOURCE).as_posix()}"
            expected[member] = path.read_bytes()
        with zipfile.ZipFile(STARTER_ZIP) as archive:
            members = archive.infolist()
            self.assertEqual([info.filename for info in members], sorted(expected))
            for info in members:
                self.assertEqual(info.date_time, (2026, 7, 25, 0, 0, 0))
                self.assertEqual((info.external_attr >> 16) & 0o170000, 0o100000)
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)
                self.assertEqual(archive.read(info), expected[info.filename])

    def test_starter_builder_rejects_source_symlink_before_payload_read(self) -> None:
        namespace = runpy.run_path(str(ROOT / "tools" / "build-starter-kit.py"))
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            source = temporary_root / "My-Nurse-AI-OS"
            shutil.copytree(STARTER_SOURCE, source)
            outside = temporary_root / "outside.md"
            outside.write_text("must not be packaged", encoding="utf-8")
            (source / "symlink-escape.md").symlink_to(outside)
            build = namespace["build"]
            build.__globals__["SOURCE"] = source
            output = temporary_root / "starter-kit.zip"
            with self.assertRaisesRegex(RuntimeError, "symlink"):
                build(output)

    def test_starter_source_read_resists_parent_swap(self) -> None:
        namespace = runpy.run_path(str(ROOT / "tools" / "build-starter-kit.py"))
        with tempfile.TemporaryDirectory() as temporary:
            temporary_root = Path(temporary)
            source = temporary_root / "My-Nurse-AI-OS"
            reviewed_parent = source / "reviewed"
            reviewed_parent.mkdir(parents=True)
            artifact = reviewed_parent / "artifact.md"
            artifact.write_bytes(b"SAFE_REVIEWED_BYTES")
            outside_parent = temporary_root / "outside"
            outside_parent.mkdir()
            (outside_parent / artifact.name).write_bytes(b"UNREVIEWED_OUTSIDE_BYTES")
            displaced_parent = source / "reviewed-before-swap"
            original_open = namespace["os"].open
            swapped = False

            def swap_parent_before_file_open(path, flags, *args, **kwargs):
                nonlocal swapped
                if not swapped and Path(path).name == artifact.name:
                    reviewed_parent.rename(displaced_parent)
                    reviewed_parent.symlink_to(outside_parent, target_is_directory=True)
                    swapped = True
                return original_open(path, flags, *args, **kwargs)

            with mock.patch.object(namespace["os"], "open", side_effect=swap_parent_before_file_open):
                payload = namespace["read_source"](artifact, source)

            self.assertTrue(swapped)
            self.assertEqual(payload, b"SAFE_REVIEWED_BYTES")

    def test_side_gig_zip_exactly_matches_reviewed_sources(self) -> None:
        expected = {
            f"Nurse-AI-Side-Gig-Starter-Kit/{path.relative_to(SIDE_GIG_SOURCE).as_posix()}": path.read_bytes()
            for path in SIDE_GIG_SOURCE.rglob("*")
            if path.is_file()
        }
        with zipfile.ZipFile(SIDE_GIG_ZIP) as archive:
            members = archive.infolist()
            self.assertEqual([info.filename for info in members], sorted(expected))
            for info in members:
                self.assertEqual(info.date_time, (2026, 7, 25, 0, 0, 0))
                self.assertEqual((info.external_attr >> 16) & 0o170000, 0o100000)
                self.assertEqual((info.external_attr >> 16) & 0o777, 0o644)
                self.assertEqual(archive.read(info), expected[info.filename])

    def test_current_navigation_does_not_present_signed_legacy_snapshot_as_current(self) -> None:
        active_pages = RESOURCE_PAGES + (ROOT / "pathways.html", ROOT / "hermes-masterclass.html")
        for path in active_pages:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("naio-os/README.md", text, path.relative_to(ROOT))
            self.assertNotIn("naio-os/GOVERNANCE-RESEARCH.md", text, path.relative_to(ROOT))
            self.assertNotIn("naio-os/release.json", text, path.relative_to(ROOT))

        for path in RESOURCE_PAGES:
            text = path.read_text(encoding="utf-8")
            self.assertEqual(text.count("architecture-report.html"), 1, path.relative_to(ROOT))

    @unittest.skipUnless(PYPDF_AVAILABLE, "pypdf unavailable")
    def test_current_public_pdfs_match_corrected_governance_boundary(self) -> None:
        reader = importlib.import_module("pypdf").PdfReader
        for path in PUBLIC_DOCUMENT_PDFS:
            text = "\n".join(page.extract_text() or "" for page in reader(path).pages)
            self.assertNotIn("Ethical Design & Enablement for Nursing Augmentation", text, path.name)
            self.assertNotIn("© NAIO Institute", text, path.name)
            self.assertNotIn("$1,500–$2,999 professional program", text, path.name)
            self.assertIn("Robert Domondon", text, path.name)

    def test_workflows_cover_governance_source_and_derivative_closure(self) -> None:
        website = (ROOT / ".github" / "workflows" / "website-alignment.yml").read_text(encoding="utf-8")
        media = (ROOT / ".github" / "workflows" / "media-packet.yml").read_text(encoding="utf-8")
        for required in (
            '"governance-kit/**"',
            '"assets/governance-kit.zip"',
            '"assets/nurse-ai-os-starter-kit.zip"',
            '"assets/nurse-ai-side-gig-starter-kit.zip"',
            '"assets/safety-rules-edena.*"',
            '"tools/build-governance-kit.py"',
            '"tools/build-starter-kit.py"',
            '"starter-kit/My-Nurse-AI-OS/**"',
            '"naio-os/**"',
            '"tests/test_public_governance_artifacts.py"',
            '"GOVERNANCE.md"',
            '"README.md"',
            '"assets/governed-harness-2-architecture.md"',
            '"naio-harness-v2/README.md"',
        ):
            self.assertIn(required, website + media)
        for required in (
            '"GOVERNANCE.md"',
            '"README.md"',
            '"assets/governed-harness-2-architecture.md"',
            '"naio-harness-v2/README.md"',
            '"naio-os/**"',
        ):
            self.assertEqual(website.count(required), 2, required)
        self.assertIn("python tools/build-governance-kit.py", media)
        self.assertEqual(media.count("python tools/build-starter-kit.py"), 2)
        self.assertIn("targets=(essentials founding make-yours power cheat roadmap workbook safety lamp)", media)
        self.assertIn('python tools/build-pdfs.py "${targets[@]}"', media)
        scanner_documents = website.split("documents=(", 1)[1].split(")", 1)[0]
        for required in (
            "assets/founding-year-guide.md",
            "assets/founding-year-guide.pdf",
            "assets/make-it-yours-six-workflows.md",
            "assets/make-it-yours-six-workflows.pdf",
        ):
            self.assertIn(required, scanner_documents)

    def test_active_operator_and_proposed_council_boundaries(self) -> None:
        html_sources = [path for path in ROOT.rglob("*.html") if "node_modules" not in path.parts]
        joined = "\n".join(path.read_text(encoding="utf-8") for path in html_sources)
        for prohibited in (
            "© 2026 Nurse AI OS · NAIO Institute",
            "Published by NAIO Institute",
            "NAIO Institute publishes",
            '"@id": "https://nurse-ai-os.org/#org"',
        ):
            self.assertNotIn(prohibited, joined)
        homepages = (ROOT / "index.html",) + tuple(
            ROOT / locale / "index.html"
            for locale in ("es", "tl", "zh", "ar", "vi", "ru", "hi", "fr")
        )
        for path in homepages:
            text = path.read_text(encoding="utf-8")
            self.assertIn('"@id": "https://nurse-ai-os.org/#operator"', text, path.relative_to(ROOT))
            self.assertIn('"name": "Robert Domondon"', text, path.relative_to(ROOT))

        marketplace = (
            ROOT
            / "starter-kit"
            / "My-Nurse-AI-OS"
            / "16-Builder-OS"
            / "Template-Marketplace-Submissions.md"
        ).read_text(encoding="utf-8")
        self.assertIn("No Nurse Steward Council is currently seated or authorized", marketplace)
        self.assertIn("does not receive a trust label", marketplace)
        self.assertNotIn("Council members review", marketplace)
        self.assertNotIn("Two approvals", marketplace)


if __name__ == "__main__":
    unittest.main()
