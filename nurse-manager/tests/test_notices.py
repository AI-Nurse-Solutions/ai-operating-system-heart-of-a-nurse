"""Hermes notices and naming stay truthful (build step 0.8)."""

import hashlib
import re
from html.parser import HTMLParser
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
NOTICES = REPO / "THIRD_PARTY_NOTICES.md"
REVIEW = REPO / "nurse-manager" / "docs" / "05-hermes-review.md"
# SHA-256 of `LICENSE` (stripped) in NousResearch/hermes-agent at tag
# v2026.9.24 (f97608f) and main ee5f49b, read 2026-09-29. Any edit to the
# reproduced notice, including the grant or the disclaimer, fails this pin.
HERMES_MIT_SHA256 = "547925cbc7510811a7fd35eb72e8eee3d5381ae9527e8d4e1bd0fe74057e511c"
# Every public page whose <title> names Hermes must carry the independence
# note, marked so the test finds it in any language. Pages that make the same
# statement in their own words are listed here with the phrase that does it.
ATTRIBUTION_MARKER = 'data-attribution="hermes-independence"'
EQUIVALENT_ATTRIBUTION = {
    "hermes-downloads/index.html": "separate, free, open-source desktop runtime from Nous Research",
}
# The clause that says Nous Research does not endorse Nurse AI OS, by page
# language. Each one names Nous Research (or refers back to it) as the party
# that does not endorse, so a translation cannot flip the direction.
NON_ENDORSEMENT_CLAUSE = {
    "en": "not affiliated with or endorsed by Nous Research",
    "ar": "ولا يحظى بتأييدها",
    "es": "ni cuenta con su respaldo",
    "fr": "ni approuvé par elle",
    "hi": "न ही उसके द्वारा समर्थित",
    "ru": "не одобрен ею",
    "tl": "hindi rin ito ineendorso ng Nous Research",
    "vi": "không được Nous Research chứng thực",
    "zh": "也未获其认可",
}
SKIP_DIRS = {".git", "node_modules"}
ATTRIBUTION_NOTE = re.compile(r'<p data-attribution="hermes-independence">(.*?)</p>', re.S)


class _TitleParser(HTMLParser):
    """Collects the text of the first <title>, whatever its attributes or case."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth, self.done, self.parts = 0, False, []

    def handle_starttag(self, tag, attrs):
        if tag == "title" and not self.done:
            self.depth += 1

    def handle_endtag(self, tag):
        if tag == "title" and self.depth:
            self.depth, self.done = 0, True

    def handle_data(self, data):
        if self.depth:
            self.parts.append(data)


def page_title(html: str) -> str:
    parser = _TitleParser()
    parser.feed(html)
    parser.close()
    return " ".join("".join(parser.parts).split())


def hermes_pages() -> list[str]:
    """Repository-relative paths of HTML pages whose title mentions Hermes."""
    pages = []
    for path in REPO.rglob("*.html"):
        rel = path.relative_to(REPO)
        if SKIP_DIRS & set(rel.parts):
            continue
        if "hermes" in page_title(path.read_text(encoding="utf-8", errors="replace")).lower():
            pages.append(rel.as_posix())
    return sorted(pages)


def _github_glob(pattern: str) -> re.Pattern:
    """GitHub Actions path-filter semantics: `*` stays within a directory, `**` crosses them."""
    out, i = "", 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif pattern.startswith("**", i):
            out, i = out + ".*", i + 2
        elif pattern[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif pattern[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(pattern[i]), i + 1
    return re.compile(out + r"\Z")


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

    def test_github_glob_semantics(self):
        self.assertTrue(_github_glob("*hermes*.html").match("remote-hermes-safely.html"))
        self.assertFalse(_github_glob("*hermes*.html").match("fr/hermes.html"))
        self.assertTrue(_github_glob("**/cheat-sheet.html").match("cheat-sheet.html"))
        self.assertTrue(_github_glob("**/cheat-sheet.html").match("zh/cheat-sheet.html"))
        self.assertTrue(_github_glob("**/*.html").match("setup-guide.html"))
        self.assertTrue(_github_glob("**/*.html").match("a/b/page.html"))

    def test_notice_workflow_triggers_on_guarded_and_future_pages(self):
        workflow = (REPO / ".github" / "workflows" / "hermes-notices.yml").read_text(encoding="utf-8")
        self.assertIn("nurse-manager/tests/test_notices.py", workflow)
        # Any HTML page can become guarded by naming Hermes in its title, so
        # the filter must cover pages of any name, not today's names only.
        guarded = {"THIRD_PARTY_NOTICES.md", "nurse-manager/tests/test_notices.py",
                   "setup-guide.html", "new-section/any-page.html", *hermes_pages()}
        for event in ("pull_request", "push"):
            with self.subTest(event=event):
                patterns = [_github_glob(p) for p in _workflow_paths(workflow, event)]
                missed = sorted(f for f in guarded if not any(p.match(f) for p in patterns))
                self.assertEqual([], missed)


class HermesReviewTests(unittest.TestCase):
    def test_review_records_sources_with_commits_and_dates(self):
        text = REVIEW.read_text(encoding="utf-8")
        self.assertIn("f97608f", text)
        self.assertIn("ee5f49b", text)
        self.assertRegex(text, r"\| 2026-\d\d-\d\d \|")
        self.assertIn("unverified", text)
        self.assertIn("## 3. Obligations checklist for step 1.11", text)


class HermesPageAttributionTests(unittest.TestCase):
    def test_title_parsing_ignores_attributes_case_and_whitespace(self):
        self.assertEqual("Hermes Setup", page_title('<title lang="en">Hermes Setup</title>'))
        self.assertEqual("Hermes Setup", page_title("<TITLE>\n  Hermes\n  Setup </TITLE>"))
        self.assertEqual("Q&A — Hermes", page_title("<title data-x='1'>Q&amp;A &mdash; Hermes</title>"))
        self.assertEqual("", page_title("<p>Hermes</p>"))

    def test_discovery_finds_the_known_pages(self):
        pages = hermes_pages()
        for page in ("hermes-masterclass.html", "hermes-downloads/index.html",
                     "cheat-sheet.html", "when-things-go-wrong.html", "zh/cheat-sheet.html"):
            self.assertIn(page, pages)

    def test_hermes_titled_pages_state_independence(self):
        for page in hermes_pages():
            with self.subTest(page=page):
                text = (REPO / page).read_text(encoding="utf-8")
                if page in EQUIVALENT_ATTRIBUTION:
                    self.assertIn(EQUIVALENT_ATTRIBUTION[page], text)
                    continue
                notes = ATTRIBUTION_NOTE.findall(text)
                self.assertEqual(1, len(notes), f"expected one {ATTRIBUTION_MARKER} note")
                self.assertIn("Nous Research", notes[0])
                self.assertIn("Nurse AI OS", notes[0])

    def test_note_says_nous_research_does_not_endorse_us(self):
        for page in hermes_pages():
            if page in EQUIVALENT_ATTRIBUTION:
                continue
            with self.subTest(page=page):
                first = page.split("/", 1)[0]
                lang = first if "/" in page and first in NON_ENDORSEMENT_CLAUSE else "en"
                notes = ATTRIBUTION_NOTE.findall((REPO / page).read_text(encoding="utf-8"))
                self.assertEqual(1, len(notes))
                self.assertIn(NON_ENDORSEMENT_CLAUSE[lang], notes[0])

    def test_equivalent_attributions_are_still_hermes_pages(self):
        self.assertEqual([], sorted(set(EQUIVALENT_ATTRIBUTION) - set(hermes_pages())))

    def test_pages_do_not_claim_endorsement(self):
        pattern = re.compile(r"(official|certified|endorsed|approved) (nurse ai os|partner)"
                             r"|(endorsed|certified|approved) by (hermes|nous)", re.I)
        for page in hermes_pages():
            with self.subTest(page=page):
                text = (REPO / page).read_text(encoding="utf-8")
                text = text.replace("not affiliated with or endorsed by", "")
                self.assertIsNone(pattern.search(text))


if __name__ == "__main__":
    unittest.main()
