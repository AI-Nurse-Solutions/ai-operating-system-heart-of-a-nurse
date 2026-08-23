#!/usr/bin/env python3
"""Contracts for the proposed nursing fundamentals research record.

Three kinds of contract live here, and the third is the unusual one.

  * Structure — the documents exist, are discoverable from the root README, and
    state their own limits.
  * Vocabulary — every governance term the codification register leans on is a
    term the runtime actually enforces. A register that graded concepts into
    policy language `edena-policy.yaml` does not define would be the phantom
    control the fine-tuning plan §3 warns about, one layer up.
  * Claims about the repository — the register's proposals rest on three facts
    about files it does not own. Those facts are asserted here, so that fixing
    one fails this test and forces the document to be updated rather than
    quietly going stale. A research record whose findings decay silently is
    worse than none.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "nursing-fundamentals"
INDEX = DOCS / "README.md"
FUNDAMENTALS = DOCS / "FUNDAMENTALS.md"
CODIFICATION = DOCS / "CODIFICATION.md"
CORPUS = DOCS / "CORPUS.md"
RECORDS = DOCS / "examples" / "illustrative-records.jsonl"

POLICY = ROOT / "naio-os" / "config" / "edena-policy.yaml"
SCHEMA = ROOT / "naio-os" / "models" / "schema" / "training-example.schema.json"
LINT = ROOT / "naio-os" / "models" / "lint_dataset.py"
PREFLIGHT = ROOT / "governance-kit" / "prompts" / "five-rights-preflight.md"

MARKDOWN = (INDEX, FUNDAMENTALS, CODIFICATION, CORPUS)


def flat(text: str) -> str:
    """Prose pins compare against collapsed whitespace so a reflow cannot break them.

    Blockquote markers are stripped first: a maxim is the same claim whether or
    not it is quoted, and a pin that broke on '>' would pin the formatting.
    """
    return re.sub(r"\s+", " ", re.sub(r"(?m)^\s*>\s?", "", text))


class DocumentStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = {path.name: path.read_text(encoding="utf-8") for path in MARKDOWN}
        cls.flat = {name: flat(body) for name, body in cls.text.items()}

    def test_documents_are_discoverable_from_the_root_readme(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("Nursing fundamentals", root_readme)
        self.assertIn("[`nursing-fundamentals/`](nursing-fundamentals/)", root_readme)
        self.assertTrue(DOCS.is_dir(), "root README links a missing directory")

    def test_every_document_declares_a_proposed_status(self) -> None:
        self.assertIn("Status: proposed research record", self.text["README.md"])
        for name in ("FUNDAMENTALS.md", "CODIFICATION.md", "CORPUS.md"):
            self.assertIn('status: "Proposed research record"', self.text[name], name)

    def test_every_document_disclaims_the_authority_it_could_be_read_as_creating(self) -> None:
        for name in ("FUNDAMENTALS.md", "CODIFICATION.md", "CORPUS.md", "README.md"):
            body = self.flat[name]
            for disclaimed in ("curriculum", "institutional authority", "PHI"):
                self.assertIn(disclaimed, body, f"{name} does not disclaim {disclaimed}")

    def test_the_corpus_spec_keeps_gate_zero(self) -> None:
        """The plan's cheapest outcome must survive being given content to author."""
        body = self.flat["CORPUS.md"]
        self.assertIn("Gate zero still governs", body)
        self.assertIn("no corpus is authored", body)

    def test_relative_links_between_these_documents_resolve(self) -> None:
        broken = []
        for path in MARKDOWN:
            for target in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if urlparse(target).scheme or target.startswith("#"):
                    continue
                resolved = (path.parent / unquote(target.split("#", 1)[0])).resolve()
                if not resolved.exists():
                    broken.append(f"{path.name} → {target}")
        self.assertEqual(broken, [], "relative links point at files that do not exist")


class EnforcedVocabularyTests(unittest.TestCase):
    """The register may only grade concepts into language the runtime enforces."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.register = CODIFICATION.read_text(encoding="utf-8")
        cls.policy = POLICY.read_text(encoding="utf-8")

    def test_every_hard_boundary_the_register_cites_exists_in_policy(self) -> None:
        for boundary in re.findall(r"hard_boundaries\.([a-z_]+)", self.register):
            self.assertIn(f"  {boundary}:", self.policy, f"{boundary} is not a declared boundary")

    def test_every_tool_class_the_register_cites_exists_in_policy(self) -> None:
        for tool_class in re.findall(r"tool_classes\.([a-z_]+)", self.register):
            self.assertIn(f"    {tool_class}:", self.policy, f"{tool_class} is not a declared tool class")

    def test_the_structural_claims_about_policy_are_true(self) -> None:
        """The register says these keys already encode nursing's delegation doctrine."""
        for key in (
            "oversight_follows_delegation: true",
            "inherit_ceiling: true",
            "may_exceed_parent_tier: false",
            "leaf_default_tier: green",
            "provenance_required: true",
        ):
            self.assertIn(key, self.policy, f"the register cites {key!r}, which policy no longer sets")

    def test_the_register_names_the_prohibited_practices_it_relies_on(self) -> None:
        for practice in ("surveillance_emotion_inference", "social_scoring"):
            self.assertIn(practice, self.register)
            self.assertIn(f"id: {practice}", self.policy)

    def test_the_attachment_test_is_stated_in_both_places(self) -> None:
        """The sorting rule is the record's load-bearing claim; it may not drift."""
        for path in (INDEX, CODIFICATION):
            body = flat(path.read_text(encoding="utf-8"))
            self.assertIn("attachment test", body.lower(), path.name)
            self.assertIn("requires naming a patient, it is refused", body, path.name)


class RepositoryClaimTests(unittest.TestCase):
    """Facts the register's proposals rest on. Fixing one should fail this test."""

    def test_the_five_rights_preflight_still_speaks_the_retired_vocabulary(self) -> None:
        preflight = PREFLIGHT.read_text(encoding="utf-8")
        stale = [token for token in ("D0", "D2", "Red-P", "Red-E") if token in preflight]
        self.assertTrue(
            stale,
            "five-rights-preflight.md no longer uses the retired vocabulary — "
            "proposal 1 in nursing-fundamentals/CODIFICATION.md §5 is done and "
            "the document should be updated to say so",
        )

    def test_the_policy_still_omits_the_nursing_delegation_source(self) -> None:
        policy = POLICY.read_text(encoding="utf-8")
        review_basis = policy.split("review_basis:", 1)[1].split("\n\n", 1)[0]
        self.assertNotIn(
            "National Guidelines for Nursing Delegation",
            review_basis,
            "edena-policy now cites the nursing delegation guidelines — proposal 2 "
            "in nursing-fundamentals/CODIFICATION.md §5 is done and the document "
            "should be updated to say so",
        )

    def test_the_ncjmm_pedagogy_skill_the_survey_credits_still_exists(self) -> None:
        skill = ROOT / "starter-kit" / "My-Nurse-AI-OS" / "15-Student-Study-OS" / "Sim-Case-NCJMM-Tanner.SKILL.md"
        self.assertTrue(skill.is_file(), "the survey credits a skill that has moved")
        self.assertIn("no_phi: true", skill.read_text(encoding="utf-8"))


class IllustrativeRecordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.records = [
            json.loads(line)
            for line in RECORDS.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_the_records_pass_the_shipped_dataset_gate(self) -> None:
        """Not a re-implementation of the gate — the gate itself, on these records."""
        result = subprocess.run(
            [sys.executable, str(LINT), str(RECORDS)],
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_records_are_marked_as_not_a_corpus(self) -> None:
        for record in self.records:
            identifier = record["example_id"]
            self.assertTrue(identifier.startswith("illus-"), identifier)
            self.assertEqual(record["dataset_version"], "0.0.0", identifier)
            self.assertEqual(record["review_status"], "draft", identifier)
            self.assertNotIn("split", record, f"{identifier} claims a training split")

    def test_every_declared_task_has_a_worked_record(self) -> None:
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(record["task"] for record in self.records),
            sorted(schema["properties"]["task"]["enum"]),
            "the corpus spec maps every task to a nursing ancestor; each needs an example",
        )

    def test_the_triage_record_proposes_rather_than_decides(self) -> None:
        triage = next(r for r in self.records if r["task"] == "triage_justification")
        self.assertIn("expected_classification", triage)
        self.assertIn("expected_gate", triage)
        self.assertIn(
            "the policy engine, not I, computes",
            triage["ideal_response"],
            "the model must not present itself as the authority on the gate",
        )

    def test_the_refusal_record_does_not_claim_to_be_the_control(self) -> None:
        refusal = next(r for r in self.records if r["task"] == "refusal_redirect")
        boundaries = refusal["expected_classification"]["hard_boundaries_implicated"]
        self.assertIn("no_phi", boundaries)
        self.assertIn("no_clinical_decisions", boundaries)
        self.assertIn(
            "What I can do",
            refusal["ideal_response"],
            "a refusal without a redirect is the failure mode, not the example",
        )

    def test_no_record_speaks_a_patient_attached_nursing_vocabulary(self) -> None:
        """The corpus exclusion, enforced on the examples that demonstrate it."""
        blob = RECORDS.read_text(encoding="utf-8")
        for term in ("NANDA", "NIC ", "NOC ", "ICNP", "PNDS", "nursing diagnosis"):
            self.assertNotIn(term, blob, f"an illustrative record uses {term!r}")


if __name__ == "__main__":
    unittest.main()
