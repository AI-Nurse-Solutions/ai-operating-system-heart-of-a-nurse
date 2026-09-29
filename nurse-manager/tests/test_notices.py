"""Hermes notices and naming stay truthful (build step 0.8)."""

import hashlib
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NOTICES = REPO / "THIRD_PARTY_NOTICES.md"
REVIEW = REPO / "nurse-manager" / "docs" / "05-hermes-review.md"
# SHA-256 of `LICENSE` (stripped) in NousResearch/hermes-agent at tag
# v2026.9.24 (f97608f) and main ee5f49b, read 2026-09-29. Any edit to the
# reproduced notice, including the grant or the disclaimer, fails this pin.
HERMES_MIT_SHA256 = "547925cbc7510811a7fd35eb72e8eee3d5381ae9527e8d4e1bd0fe74057e511c"
HERMES_PAGES = (
    "hermes-masterclass.html",
    "hermes-configuration-handbook.html",
    "remote-hermes-safely.html",
    "hermes-downloads/index.html",
)


def _inventory_row(text: str, component: str) -> list[str]:
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and cells[0].startswith(component):
            return cells
    raise AssertionError(f"no inventory row for {component!r}")


class HermesNoticeTests(unittest.TestCase):
    def setUp(self):
        self.notices = NOTICES.read_text(encoding="utf-8")

    def test_hermes_desktop_row_has_required_fields(self):
        cells = _inventory_row(self.notices, "Hermes Desktop")
        self.assertEqual(5, len(cells), cells)
        _, upstream, license_, status, modified = cells
        self.assertIn("github.com/NousResearch/hermes-agent", upstream)
        self.assertRegex(upstream, r"`v\d{4}\.\d+\.\d+` \(`[0-9a-f]{7,}`\)")
        self.assertTrue(license_.startswith("MIT"), license_)
        self.assertIn("Referenced, not bundled", status)
        self.assertIn("1.11", status)
        self.assertEqual("No", modified)

    def test_status_never_claims_hermes_is_shipped(self):
        cells = _inventory_row(self.notices, "Hermes Desktop")
        self.assertNotRegex(cells[3].lower(), r"\b(bundled inside|vendored in|ships with)\b")

    def test_step_1_11_obligations_are_recorded(self):
        match = re.search(r"### 2\.1 Hermes Desktop.*?(?=\n## )", self.notices, re.S)
        self.assertIsNotNone(match, "§2.1 missing")
        section = match.group(0)
        for needle in ("referenced, not bundled", "MIT notice", "NOTICE",
                       "python-build-standalone", "`uv`", "GPL", "logos", "endorsement"):
            self.assertIn(needle, section)

    def test_mit_notice_is_intact(self):
        match = re.search(r"## 2\. Hermes\n.*?```text\n(.*?)```", self.notices, re.S)
        self.assertIsNotNone(match, "Hermes MIT notice block missing")
        digest = hashlib.sha256(match.group(1).strip().encode("utf-8")).hexdigest()
        self.assertEqual(HERMES_MIT_SHA256, digest)

    def test_no_affiliation_names_nous_research(self):
        section = self.notices.split("## 5. No Affiliation", 1)[1]
        self.assertIn("Hermes Desktop", section)
        self.assertIn("Nous Research", section)


def _workflow_paths(workflow: str, event: str) -> set[str]:
    """Path filters under `on.<event>.paths` in a workflow file (no YAML dependency)."""
    paths, in_event, in_paths = set(), False, False
    for line in workflow.splitlines():
        if re.match(r"^  \S", line):
            in_event, in_paths = line.strip() == f"{event}:", False
        elif in_event and re.match(r"^    paths:\s*$", line):
            in_paths = True
        elif in_event and re.match(r"^    \S", line):
            in_paths = False
        elif in_paths:
            match = re.match(r'^\s+- "([^"]+)"', line)
            if match:
                paths.add(match.group(1))
        if re.match(r"^\S", line) and not line.startswith("on:"):
            in_event = in_paths = False
    return paths


class NoticeWorkflowTriggerTests(unittest.TestCase):
    """A PR that touches only a guarded file must still run this suite."""

    def test_manager_workflow_triggers_on_guarded_files(self):
        workflow = (REPO / ".github" / "workflows" / "nurse-manager.yml").read_text(encoding="utf-8")
        guarded = {"THIRD_PARTY_NOTICES.md", *HERMES_PAGES}
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                paths = _workflow_paths(workflow, event)
                self.assertIn("nurse-manager/**", paths)
                self.assertEqual(set(), guarded - paths)


class HermesReviewTests(unittest.TestCase):
    def test_review_records_sources_with_commits_and_dates(self):
        text = REVIEW.read_text(encoding="utf-8")
        self.assertIn("f97608f", text)
        self.assertIn("ee5f49b", text)
        self.assertRegex(text, r"\| 2026-\d\d-\d\d \|")
        self.assertIn("unverified", text)
        self.assertIn("## 3. Obligations checklist for step 1.11", text)


class HermesPageAttributionTests(unittest.TestCase):
    def test_hermes_titled_pages_state_independence(self):
        for page in HERMES_PAGES:
            with self.subTest(page=page):
                text = (REPO / page).read_text(encoding="utf-8")
                self.assertIn("Nous Research", text)
                self.assertRegex(text, r"(not affiliated with or endorsed by Nous Research"
                                       r"|separate, free, open-source desktop runtime from Nous Research)")

    def test_pages_do_not_claim_endorsement(self):
        pattern = re.compile(r"(official|certified|endorsed|approved) (nurse ai os|partner)"
                             r"|(endorsed|certified|approved) by (hermes|nous)", re.I)
        for page in HERMES_PAGES:
            with self.subTest(page=page):
                text = (REPO / page).read_text(encoding="utf-8")
                text = text.replace("not affiliated with or endorsed by", "")
                self.assertIsNone(pattern.search(text))


if __name__ == "__main__":
    unittest.main()
