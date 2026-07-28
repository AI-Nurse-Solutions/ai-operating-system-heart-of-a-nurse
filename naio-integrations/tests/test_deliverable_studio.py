import unittest

import _bootstrap  # noqa: F401

from naio_integrations.deliverables import (
    DRAFT_BANNER,
    SYNTHETIC_BANNER,
    DeliverableError,
    DeliverableStudio,
)

SPEC_3_6_TEMPLATES = {
    "project-charter",
    "aim-statement-driver-diagram",
    "evidence-summary",
    "policy-procedure-draft",
    "education-plan",
    "competency-checklist",
    "case-study",
    "meeting-pack",
    "executive-brief",
    "presentation-poster-outline",
    "abstract-manuscript-scaffold",
    "communication-plan",
    "message-draft",
    "dashboard-summary",
    "personal-development-plan",
}


class TemplateCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.studio = DeliverableStudio()

    def test_catalog_covers_every_spec_3_6_deliverable(self):
        self.assertEqual(set(self.studio.templates(group="spec_3_6")), SPEC_3_6_TEMPLATES)

    def test_first_run_templates_exist(self):
        first_run = set(self.studio.templates(group="first_run"))
        self.assertEqual(
            first_run,
            {
                "structured-question",
                "project-one-pager",
                "evidence-question",
                "research-question",
            },
        )

    def test_every_template_has_titled_guided_sections(self):
        for template_id in self.studio.templates():
            template = self.studio.describe(template_id)
            self.assertTrue(template["title"], template_id)
            self.assertGreaterEqual(len(template["sections"]), 3, template_id)
            for section in template["sections"]:
                self.assertTrue(section["heading"], template_id)
                self.assertTrue(section["guidance"], template_id)

    def test_unknown_template_fails_closed(self):
        with self.assertRaises(DeliverableError):
            self.studio.describe("final-approved-report")


class NeverFinalRuleTests(unittest.TestCase):
    def setUp(self):
        self.studio = DeliverableStudio()

    def test_every_scaffold_is_born_a_draft_with_the_banner(self):
        for template_id in self.studio.templates():
            deliverable = self.studio.scaffold(template_id)
            self.assertEqual(deliverable.status, "draft", template_id)
            self.assertFalse(deliverable.approved, template_id)
            self.assertIn(DRAFT_BANNER, self.studio.render(deliverable), template_id)

    def test_review_requires_a_named_human_and_valid_disposition(self):
        draft = self.studio.scaffold("executive-brief")
        with self.assertRaises(DeliverableError):
            self.studio.record_review(draft, reviewer="  ", disposition="approved", reviewed_on="2026-07-28")
        with self.assertRaises(DeliverableError):
            self.studio.record_review(draft, reviewer="A. Leader", disposition="finalized", reviewed_on="2026-07-28")
        with self.assertRaises(DeliverableError):
            self.studio.record_review(draft, reviewer="A. Leader", disposition="approved", reviewed_on="")

    def test_approved_render_carries_the_human_attestation(self):
        draft = self.studio.scaffold("executive-brief")
        approved = self.studio.record_review(
            draft, reviewer="A. Leader", disposition="approved", reviewed_on="2026-07-28"
        )
        rendered = self.studio.render(approved)
        self.assertNotIn(DRAFT_BANNER, rendered)
        self.assertIn("Approved by A. Leader on 2026-07-28", rendered)
        self.assertIn("generation alone never makes content final", rendered)

    def test_review_records_are_immutable_once_written(self):
        import dataclasses

        draft = self.studio.scaffold("executive-brief")
        rejected = self.studio.record_review(
            draft, reviewer="A. Leader", disposition="rejected", reviewed_on="2026-07-28"
        )
        with self.assertRaises(dataclasses.FrozenInstanceError):
            rejected.review.disposition = "approved"
        self.assertFalse(rejected.approved)

    def test_non_approved_review_still_reads_as_not_usable(self):
        draft = self.studio.scaffold("executive-brief")
        rejected = self.studio.record_review(
            draft, reviewer="A. Leader", disposition="needs_changes", reviewed_on="2026-07-28"
        )
        rendered = self.studio.render(rejected)
        self.assertIn("not approved for use", rendered)
        self.assertFalse(rejected.approved)

    def test_synthetic_deliverables_always_carry_the_synthetic_banner(self):
        deliverable = self.studio.scaffold("case-study", synthetic=True)
        self.assertIn(SYNTHETIC_BANNER, self.studio.render(deliverable))
        approved = self.studio.record_review(
            deliverable, reviewer="Reviewer", disposition="approved", reviewed_on="2026-07-28"
        )
        self.assertIn(SYNTHETIC_BANNER, self.studio.render(approved))


class ScaffoldContentTests(unittest.TestCase):
    def setUp(self):
        self.studio = DeliverableStudio()

    def test_context_fills_matching_sections(self):
        deliverable = self.studio.scaffold(
            "project-charter",
            context={"aim": "Reduce huddle overruns to 2 of 10 days within two weeks."},
        )
        self.assertIn("Reduce huddle overruns", deliverable.body_markdown)

    def test_context_is_privacy_screened_before_embedding(self):
        deliverable = self.studio.scaffold(
            "project-charter",
            context={"aim": "Improve follow-up for MRN: A123456 next month."},
        )
        self.assertNotIn("A123456", deliverable.body_markdown)
        self.assertIn("Privacy screen", deliverable.body_markdown)

    def test_provenance_is_rendered_or_explicitly_absent(self):
        sourced = self.studio.scaffold(
            "evidence-summary", provenance=("evidence/library.json#example-1",)
        )
        self.assertIn("evidence/library.json#example-1", sourced.body_markdown)
        unsourced = self.studio.scaffold("evidence-summary")
        self.assertIn("none recorded", unsourced.body_markdown)

    def test_scaffolds_are_deterministic(self):
        first = self.studio.scaffold("executive-brief", context={"situation": "Stable."})
        second = DeliverableStudio().scaffold(
            "executive-brief", context={"situation": "Stable."}
        )
        self.assertEqual(first.deliverable_id, second.deliverable_id)
        self.assertEqual(first.body_markdown, second.body_markdown)


if __name__ == "__main__":
    unittest.main()
