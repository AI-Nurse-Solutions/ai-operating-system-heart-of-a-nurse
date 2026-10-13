"""The managers & entrepreneurs SOUL landing page and its Hermes package.

The page promises two downloads. These tests check that the package exists,
is current with its sources, contains what the page says it contains, and
never claims a signature it does not have.
"""
from __future__ import annotations

import hashlib
import runpy
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "managers-entrepreneurs" / "index.html"
ZIP = ROOT / "downloads" / "manager-entrepreneur-mission-control.zip"
BUILDER = ROOT / "scripts" / "build-manager-entrepreneur-package.py"
TOP = "manager-entrepreneur-mission-control/"


class ManagersEntrepreneursTests(unittest.TestCase):
    def test_page_links_the_package(self) -> None:
        html = PAGE.read_text(encoding="utf-8")
        self.assertIn('href="../downloads/manager-entrepreneur-mission-control.zip"', html)
        self.assertIn("SOUL.md", html)
        self.assertIn("naio-soul.json", html)

    def test_package_is_current(self) -> None:
        build = runpy.run_path(str(BUILDER))["build"]
        self.assertEqual(ZIP.read_bytes(), build(), "rebuild the package")

    def test_package_contents(self) -> None:
        with zipfile.ZipFile(ZIP) as z:
            names = {n[len(TOP):] for n in z.namelist()}
            for required in (
                "README.md",
                "HANDOFF-PROMPT.txt",
                "SETUP-CHEATSHEET.md",
                "mission-control.html",
                "mission-control-packet/leader/manifest.json",
                "mission-control-packet/leader/DATA-BOUNDARY.md",
                "mission-control-packet/leader/templates/meeting-pack.md",
                "venture/Side-Gig-Offer-Canvas.md",
                "venture/30-Day-Validation-Sprint.md",
                "CHECKSUMS.sha256",
            ):
                self.assertIn(required, names)
            sums = z.read(TOP + "CHECKSUMS.sha256").decode().splitlines()
            self.assertEqual(len(sums), len(names) - 1)
            for line in sums:
                digest, name = line.split("  ", 1)
                self.assertEqual(hashlib.sha256(z.read(TOP + name)).hexdigest(), digest, name)

    def test_no_signature_claim(self) -> None:
        # The package carries checksums only. "Signed" here would be false.
        with zipfile.ZipFile(ZIP) as z:
            for name in z.namelist():
                if name.endswith((".md", ".txt", ".html")) and "/venture/" not in name and "/mission-control-packet/" not in name:
                    text = z.read(name).decode().lower()
                    self.assertNotIn("signed release", text, name)
                    self.assertNotIn("is signed", text, name)

    def test_board_makes_no_network_calls(self) -> None:
        html = (ROOT / "managers-entrepreneurs" / "starter" / "mission-control.html").read_text()
        for marker in ("fetch(", "XMLHttpRequest", "localStorage", "<script src"):
            self.assertNotIn(marker, html)


if __name__ == "__main__":
    unittest.main()
