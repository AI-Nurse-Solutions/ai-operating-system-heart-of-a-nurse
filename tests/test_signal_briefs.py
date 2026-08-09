#!/usr/bin/env python3
"""Contracts for the Market Signal Engine v0.1 (personal-agi/signals)."""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SIGNALS = ROOT / "personal-agi" / "signals"
RENDERER = SIGNALS / "render_briefs.py"
BRIEF_FIELDS = ("what_happened", "why_it_matters_to_you", "do_now", "dont_do", "watch")


class SignalBriefTests(unittest.TestCase):
    def records(self):
        for path in sorted(SIGNALS.glob("*.json")):
            with path.open(encoding="utf-8") as handle:
                yield path, json.load(handle)

    def test_role_briefs_are_complete_where_present(self) -> None:
        found_any = False
        for path, record in self.records():
            role_briefs = record.get("role_briefs")
            if role_briefs is None:
                continue
            found_any = True
            self.assertIsInstance(role_briefs, dict, path.name)
            self.assertTrue(role_briefs, f"{path.name}: role_briefs is empty")
            for role, fields in role_briefs.items():
                for key in BRIEF_FIELDS:
                    value = fields.get(key, "")
                    self.assertTrue(
                        isinstance(value, str) and value.strip(),
                        f"{path.name}: role_briefs[{role}].{key} missing or empty",
                    )
        self.assertTrue(found_any, "no signal record carries role_briefs")

    def test_rendered_briefs_match_records(self) -> None:
        result = subprocess.run(
            [sys.executable, str(RENDERER), "--check"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_briefs_carry_the_boundary_language(self) -> None:
        briefs = sorted((SIGNALS / "briefs").rglob("*.md"))
        self.assertTrue(briefs, "no rendered briefs found")
        for path in briefs:
            text = path.read_text(encoding="utf-8")
            if path.name == "README.md":
                self.assertIn("Do not hand-edit", text, path.name)
                continue
            self.assertIn("hypothesis", text, path.name)
            self.assertIn("Source record:", text, path.name)
            self.assertIn(
                "Agents propose. Humans judge. Nurses steward.", text, path.name
            )


if __name__ == "__main__":
    unittest.main()
