#!/usr/bin/env python3
"""Contracts for the proposed NAIO fine-tuning plan, schema, and dataset gate."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "naio-os" / "models"
INDEX = MODELS / "README.md"
PLAN = MODELS / "FINE-TUNING-PLAN.md"
SCHEMA = MODELS / "schema" / "training-example.schema.json"
LINT = MODELS / "lint_dataset.py"
POLICY = ROOT / "naio-os" / "config" / "edena-policy.yaml"

GOOD_RECORD = {
    "example_id": "spec-committee-digest-001",
    "dataset_version": "0.1.0",
    "trained_against": "edena-policy@2.0.0",
    "task": "workflow_spec",
    "origin": "nurse_authored",
    "role_id": "leader",
    "sphere": "professional",
    "input": "Our committee spends hours every month consolidating team updates.",
    "ideal_response": "problem: committee consolidation burden",
    "review_status": "approved",
    "reviewers": ["rn-01", "rn-02"],
    "split": "train",
}


def run_lint(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class FineTuningPlanDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.plan = PLAN.read_text(encoding="utf-8")

    def test_documents_are_discoverable_and_honest_about_status(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("NAIO fine-tuning plan", root_readme)
        self.assertIn("[`naio-os/models/`](naio-os/models/)", root_readme)
        self.assertIn('status: "Proposed engineering plan"', self.plan)
        self.assertIn("Status: **proposed engineering plan.**", self.index)
        for disclaimed in ("no training run", "no hosted service", "no PHI processing"):
            self.assertIn(disclaimed, self.plan)

    def test_plan_keeps_the_decision_with_the_policy_engine(self) -> None:
        for required in (
            "the model does not classify. The policy engine classifies",
            "Agents propose. Humans judge. Nurses steward.",
            "phantom control",
            "Refusal is not a model safety control",
        ):
            self.assertIn(required, self.plan)

    def test_plan_gates_the_program_behind_a_prompted_baseline(self) -> None:
        self.assertIn("Gate zero", self.plan)
        self.assertIn("ship the prompted baseline and stop", self.plan)

    def test_relative_markdown_links_resolve(self) -> None:
        for source in (INDEX, PLAN):
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative = unquote(target.split("#", 1)[0])
                self.assertFalse(
                    Path(relative).is_absolute(),
                    f"{source.relative_to(ROOT)} has a non-relative link to {target}",
                )
                resolved = (source.parent / relative).resolve()
                self.assertTrue(
                    resolved.is_relative_to(ROOT.resolve()),
                    f"{source.relative_to(ROOT)} links outside the repository: {target}",
                )
                self.assertTrue(
                    resolved.exists(),
                    f"{source.relative_to(ROOT)} has a broken link to {target}",
                )


class TrainingExampleSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        cls.policy = POLICY.read_text(encoding="utf-8")

    def test_schema_is_closed(self) -> None:
        self.assertFalse(self.schema["additionalProperties"])

    def test_governance_enums_match_the_enforced_policy(self) -> None:
        properties = self.schema["properties"]
        self.assertEqual(
            properties["sphere"]["enum"],
            ["personal", "professional", "community", "sidegig", "interest"],
        )
        for gate in properties["expected_gate"]["enum"]:
            self.assertIn(f"  {gate}:", self.policy, f"{gate} is not a gate the runtime defines")
        classification = properties["expected_classification"]["properties"]
        for tool_class in classification["tool_classes"]["items"]["enum"]:
            self.assertIn(f"    {tool_class}:", self.policy)
        for boundary in classification["hard_boundaries_implicated"]["items"]["enum"]:
            self.assertIn(f"  {boundary}:", self.policy)

    def test_role_ids_match_the_shipped_presets(self) -> None:
        presets = sorted(
            path.stem for path in (ROOT / "naio-os" / "mission-control" / "roles").glob("*.json")
        )
        self.assertEqual(sorted(self.schema["properties"]["role_id"]["enum"]), presets)

    def test_schema_carries_no_vocabulary_the_runtime_cannot_enforce(self) -> None:
        text = SCHEMA.read_text(encoding="utf-8")
        for invented in ("Red-P", "Red-E", "D0", "D4", "data_class"):
            self.assertNotIn(invented, text, f"{invented} is not enforced anywhere in NAIO")


class DatasetGateTests(unittest.TestCase):
    def lint_record(self, record: dict) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.jsonl"
            corpus.write_text(json.dumps(record) + "\n", encoding="utf-8")
            return run_lint(str(corpus))

    def test_schema_only_run_succeeds(self) -> None:
        result = run_lint("--schema-only")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_a_governed_record_passes(self) -> None:
        result = self.lint_record(GOOD_RECORD)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_phi_shaped_text_is_refused(self) -> None:
        record = dict(GOOD_RECORD, input="Patient in room 412, MRN 88213, DOB 03/14/1958.")
        result = self.lint_record(record)
        self.assertEqual(result.returncode, 1)
        for label in ("medical record number", "room or bed number", "date of birth format"):
            self.assertIn(label, result.stdout)

    def test_the_gate_shares_the_runtime_phi_list(self) -> None:
        source = LINT.read_text(encoding="utf-8")
        self.assertIn("from adapters.phi import PHI_PATTERNS", source)
        self.assertNotIn("MRN[:#_", source, "the gate is carrying its own copy of the patterns")

    def test_unenforceable_governance_vocabulary_is_refused(self) -> None:
        result = self.lint_record(dict(GOOD_RECORD, expected_gate="Red-P"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("which the runtime cannot enforce", result.stdout)

    def test_approval_without_a_reviewer_is_refused(self) -> None:
        record = dict(GOOD_RECORD)
        record.pop("reviewers")
        result = self.lint_record(record)
        self.assertEqual(result.returncode, 1)
        self.assertIn("approved with no named reviewer", result.stdout)

    def test_an_authored_preference_pair_is_refused(self) -> None:
        result = self.lint_record(dict(GOOD_RECORD, rejected_response="That sounds excellent!"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("not from an authored strawman", result.stdout)

    def test_duplicate_example_ids_are_refused(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            corpus = Path(directory) / "corpus.jsonl"
            line = json.dumps(GOOD_RECORD) + "\n"
            corpus.write_text(line + line, encoding="utf-8")
            result = run_lint(str(corpus))
        self.assertEqual(result.returncode, 1)
        self.assertIn("already used at", result.stdout)


if __name__ == "__main__":
    unittest.main()
