#!/usr/bin/env python3
"""Contracts for the personal Data Analysis Engine pilot (personal-agi/data-engine)."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE_DIR = ROOT / "personal-agi" / "data-engine"
ANALYZER = ENGINE_DIR / "analyze.py"
REFERENCE = ENGINE_DIR / "analyses" / "study-sessions-sample"

spec_loader = importlib.util.spec_from_file_location("analyze", ANALYZER)
analyze = importlib.util.module_from_spec(spec_loader)
spec_loader.loader.exec_module(analyze)


def build_analysis(root: Path, mutate_spec=None, csv_text: str | None = None) -> Path:
    """Write a minimal valid analysis under root, optionally mutated before saving."""
    analysis_dir = root / "test-analysis"
    analysis_dir.mkdir(parents=True)
    spec = {
        "title": "Test analysis",
        "question": "How many rows are there?",
        "edena_tier": "green",
        "data_class": "D0",
        "columns": [
            {"name": "topic", "type": "string"},
            {"name": "minutes", "type": "number"},
        ],
        "analyses": [{"op": "count"}, {"op": "sum", "column": "minutes"}],
        "provenance": {"source": "synthetic fixture", "no_phi_attested": True},
        "boundaries": {
            "intended_use": ["testing"],
            "not_claims": ["no claims of any kind"],
        },
    }
    if mutate_spec:
        mutate_spec(spec)
    (analysis_dir / "spec.json").write_text(
        json.dumps(spec, indent=2) + "\n", encoding="utf-8"
    )
    if csv_text is None:
        csv_text = "topic,minutes\nreading,30\npractice,45\n"
    (analysis_dir / "data.csv").write_text(csv_text, encoding="utf-8")
    return analysis_dir


class DataEnginePilotTests(unittest.TestCase):
    def refusals(self, mutate_spec=None, csv_text: str | None = None) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            analysis_dir = build_analysis(Path(tmp), mutate_spec, csv_text)
            return analyze.render(analysis_dir, out_path=Path(tmp) / "report.md")

    def test_fixture_analysis_renders_cleanly(self) -> None:
        self.assertEqual(self.refusals(), [])

    def test_reference_report_is_fresh(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ANALYZER), "--check"],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_rendering_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = Path(tmp) / "first.md"
            second = Path(tmp) / "second.md"
            self.assertEqual(analyze.render(REFERENCE, out_path=first), [])
            self.assertEqual(analyze.render(REFERENCE, out_path=second), [])
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_report_carries_provenance_and_boundary_language(self) -> None:
        report = (REFERENCE / "report.md").read_text(encoding="utf-8")
        self.assertIn("sha256", report)
        self.assertIn("adoption signals and learning evidence", report)
        self.assertIn("edit those, not this file", report)
        self.assertIn("Agents propose. Humans judge. Nurses steward.", report)

    def test_reference_data_is_declared_synthetic(self) -> None:
        spec = json.loads((REFERENCE / "spec.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["data_class"], "D0")
        self.assertIn("Synthetic", spec["provenance"]["source"])

    def test_unknown_op_is_refused(self) -> None:
        def mutate(spec):
            spec["analyses"].append({"op": "regression", "column": "minutes"})

        problems = self.refusals(mutate)
        self.assertTrue(any("closed vocabulary" in p for p in problems), problems)

    def test_undeclared_column_is_refused(self) -> None:
        def mutate(spec):
            spec["analyses"].append({"op": "count_by", "column": "mood"})

        problems = self.refusals(mutate)
        self.assertTrue(any("not declared" in p for p in problems), problems)

    def test_number_op_on_string_column_is_refused(self) -> None:
        def mutate(spec):
            spec["analyses"].append({"op": "mean", "column": "topic"})

        problems = self.refusals(mutate)
        self.assertTrue(any("requires a number column" in p for p in problems), problems)

    def test_header_mismatch_is_refused(self) -> None:
        problems = self.refusals(csv_text="topic,minutes,extra\nreading,30,x\n")
        self.assertTrue(any("closed" in p for p in problems), problems)

    def test_non_numeric_cell_is_refused(self) -> None:
        problems = self.refusals(csv_text="topic,minutes\nreading,lots\n")
        self.assertTrue(any("not a number" in p for p in problems), problems)

    def test_empty_cell_is_refused(self) -> None:
        problems = self.refusals(csv_text="topic,minutes\nreading,\n")
        self.assertTrue(any("empty" in p for p in problems), problems)

    def test_phi_marker_in_data_is_refused(self) -> None:
        problems = self.refusals(csv_text="topic,minutes\npatient 123-45-6789,30\n")
        self.assertTrue(any("PHI" in p for p in problems), problems)

    def test_secret_in_data_is_refused(self) -> None:
        problems = self.refusals(csv_text="topic,minutes\napi_key: abc123secret,30\n")
        self.assertTrue(any("secret" in p for p in problems), problems)

    def test_overclaim_in_spec_is_refused(self) -> None:
        def mutate(spec):
            spec["question"] = "Is my study plan clinically validated yet?"

        problems = self.refusals(mutate)
        self.assertTrue(any("overclaim" in p for p in problems), problems)

    def test_orange_tier_is_refused(self) -> None:
        def mutate(spec):
            spec["edena_tier"] = "orange"

        problems = self.refusals(mutate)
        self.assertTrue(any("edena_tier" in p for p in problems), problems)

    def test_data_class_above_d1_is_refused(self) -> None:
        def mutate(spec):
            spec["data_class"] = "D3"

        problems = self.refusals(mutate)
        self.assertTrue(any("data_class" in p for p in problems), problems)

    def test_missing_phi_attestation_is_refused(self) -> None:
        def mutate(spec):
            spec["provenance"]["no_phi_attested"] = False

        problems = self.refusals(mutate)
        self.assertTrue(any("no_phi_attested" in p for p in problems), problems)

    def test_row_cap_is_enforced(self) -> None:
        original = analyze.MAX_ROWS
        analyze.MAX_ROWS = 3
        try:
            rows = "\n".join(f"topic{i},10" for i in range(5))
            problems = self.refusals(csv_text=f"topic,minutes\n{rows}\n")
            self.assertTrue(any("caps at" in p for p in problems), problems)
        finally:
            analyze.MAX_ROWS = original


if __name__ == "__main__":
    unittest.main()
