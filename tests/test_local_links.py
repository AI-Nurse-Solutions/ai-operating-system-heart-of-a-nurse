"""Every local link on the site must point at a file that exists.

A page can be true in every sentence and still hand a nurse a download that
404s. Honesty review reads prose; nobody was reading the hrefs. tools/
check-links.py existed as a manual script — this runs it in CI, so a broken
button fails a pull request instead of waiting to be noticed.
"""
from __future__ import annotations

import runpy
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "check-links.py"


class LocalLinkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(CHECKER.is_file(), f"missing {CHECKER}")
        self.checker = runpy.run_path(str(CHECKER))

    def test_every_local_link_resolves(self) -> None:
        broken = self.checker["broken"]()
        self.assertEqual(
            broken, [],
            "local links point at files that do not exist:\n"
            + "\n".join(f"  {link}  ← {src}" for src, link in broken),
        )

    def test_the_checker_actually_looks_at_pages(self) -> None:
        # A checker that silently scanned nothing would pass the test above
        # forever. Assert it found the site before trusting that it found no
        # breakage — a green light on an empty search is not a green light.
        pages = self.checker["pages"]()
        self.assertGreater(len(pages), 50, f"only {len(pages)} page(s) scanned")

    def test_a_broken_link_would_be_caught(self) -> None:
        # Prove the detector detects, rather than trusting that it does.
        page = ROOT / "index.html"
        original = page.read_text(encoding="utf-8")
        marker = 'href="explore-ecosystem.html"'
        self.assertIn(marker, original, "test needs a known-good link to break")
        try:
            page.write_text(
                original.replace(marker, 'href="no-such-page-xyz.html"', 1),
                encoding="utf-8",
            )
            found = self.checker["broken"]()
            self.assertTrue(
                any(link == "no-such-page-xyz.html" for _, link in found),
                "the checker did not notice a deliberately broken link",
            )
        finally:
            page.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
