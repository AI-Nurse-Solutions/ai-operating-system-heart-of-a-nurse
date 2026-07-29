#!/usr/bin/env python3
"""Contracts for the proposed NIN Knowledge Commons doctrine and playbook."""

from __future__ import annotations

import re
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
COMMONS = ROOT / "knowledge-commons"
INDEX = COMMONS / "README.md"
DOCTRINE = COMMONS / "DOCTRINE.md"
PLAYBOOK = COMMONS / "PLAYBOOK.md"


class KnowledgeCommonsDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.doctrine = DOCTRINE.read_text(encoding="utf-8")
        cls.playbook = PLAYBOOK.read_text(encoding="utf-8")

    def test_documents_are_discoverable_and_honest_about_status(self) -> None:
        root_readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("NIN Knowledge Commons doctrine and playbook", root_readme)
        self.assertIn("[`knowledge-commons/`](knowledge-commons/)", root_readme)
        self.assertIn("Status: proposed architecture and operating doctrine", self.index)
        self.assertIn("does not establish an operating service", self.index)
        self.assertIn('status: "Proposed architecture doctrine"', self.doctrine)
        self.assertIn('status: "Proposed operating playbook"', self.playbook)
        self.assertIn("capabilities remain inactive until built and verified", self.playbook)

    def test_relative_markdown_links_resolve(self) -> None:
        for source in (INDEX, DOCTRINE, PLAYBOOK):
            text = source.read_text(encoding="utf-8")
            for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
                if target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                relative_target = unquote(target.split("#", 1)[0])
                self.assertFalse(
                    Path(relative_target).is_absolute(),
                    f"{source.relative_to(ROOT)} has a non-relative link to {target}",
                )
                resolved = (source.parent / relative_target).resolve()
                self.assertTrue(
                    resolved.is_relative_to(ROOT.resolve()),
                    f"{source.relative_to(ROOT)} links outside the repository: {target}",
                )
                self.assertTrue(
                    resolved.exists(),
                    f"{source.relative_to(ROOT)} has a broken link to {target}",
                )

    def test_doctrine_preserves_source_authority_and_scoped_authority(self) -> None:
        for required in (
            "Content packages are the source of truth",
            "Search, vector, and graph indexes are disposable derivatives",
            "Contributors propose. Reviewers verify. Institutions authorize. Nurses steward.",
            "Inclusion means available for governed use—not endorsement",
            "No creator may be the sole approver of their own pack",
            "Creator ownership is the default",
            "Repository documentation licensing does not automatically license future Knowledge Packs",
            "A private contributor address, phone number, identity-verification record",
            "must not enter the pack manifest, catalog, retrieval indexes, graph, public review record, or analytics",
        ):
            self.assertIn(required, self.doctrine)

    def test_doctrine_preserves_edena_and_no_phi_boundaries(self) -> None:
        for required in (
            "Green, Yellow, Orange, Red-P (prohibited), and Red-E",
            "D0 public, formally deidentified, or synthetic",
            "D3 PHI or other sensitive regulated material",
            "D4 credentials, secrets, signing material",
            "Observe, Draft, Recommend, Prepare Action, Act With Approval, and Constrained Autonomy",
            "Unrestricted autonomy is prohibited",
            "D3 or D4 material",
            "A future Orange lane requires",
            "Red-P remains prohibited",
        ):
            self.assertIn(required, self.doctrine)

    def test_hybrid_retrieval_is_authorization_first_and_rebuildable(self) -> None:
        for required in (
            "graph-ready hybrid RAG",
            "Indexes are derivatives and must be rebuildable from authorized source packages",
            "Unauthorized content must never become a semantic-ranking candidate",
            "Retrieved content is data, never instructions",
            "remove the pack's chunks, vectors, and graph edges from active retrieval",
        ):
            self.assertIn(required, self.doctrine)
        for required in (
            "must all run before similarity search or graph expansion",
            "Intent classification must occur before the query-level EDENA and permitted-use filter",
            "optional local vector index",
            "registry graph",
            "optional curated concept graph",
            "controlled claim-evidence graph",
            "The target for unauthorized retrieval is zero",
        ):
            self.assertIn(required, self.playbook)

    def test_reference_implementation_evidence_stays_bounded(self) -> None:
        self.assertIn("reference implementation evidence", self.index)
        self.assertIn(
            "it is not the Commons, a catalog, or a hosted retrieval service",
            self.index,
        )
        self.assertIn(
            "That evidence supports the direction and activates nothing.",
            self.doctrine,
        )
        self.assertIn("NIN–NAIO Master Directive v1.1", self.doctrine)
        self.assertIn(
            "one person must never be presented as two independent reviewers",
            self.playbook,
        )

    def test_playbook_preserves_manual_review_lifecycle_and_deferrals(self) -> None:
        for required in (
            "No step automatically grants the next state",
            "A passed scan means only that automated checks did not find a listed defect. It is not approval",
            "No review or approval may silently follow changing bytes",
            "does not install, authorize, or activate a pack",
            "open active content only in an approved sandbox",
            "Public Orange submissions remain held or refused",
            "The proposed 85/15 split is not final policy",
            "Explicit MVP deferrals",
            "native marketplace or platform-held funds",
            "PHI or D3/D4 processing",
            "Designed, documented, implemented, tested, committed, merged, deployed, and live-verified are distinct states",
        ):
            self.assertIn(required, self.playbook)


if __name__ == "__main__":
    unittest.main()
