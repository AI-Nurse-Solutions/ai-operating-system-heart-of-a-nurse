from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ROLE_LANDING_PAGES = (
    "student-nurse.html",
    "staff-nurse.html",
    "nurse-practitioner.html",
    "medical-resident.html",
    "pathways.html",
    "post-setup/index.html",
    "medical-residents/index.html",
    "respiratory-care/index.html",
    "healthcare-research-innovation-leaders/index.html",
    "hospital-clinic-administrators/index.html",
    "wellness-services-marketing-managers/index.html",
)


class OurIntentTests(unittest.TestCase):
    def test_every_role_landing_page_contains_the_full_intent(self):
        required = (
            "Our Intent",
            "Nurse AI OS is not a replacement for anything you already belong to.",
            "We are not here to compete with existing nursing programs",
            "We are not here to make you rich.",
            "Your clinical practice is the source of your authority.",
            "steward the arrival of AI into nursing practice",
            "Stewardship, not disruption. Influence, not extraction.",
        )
        for relative_path in ROLE_LANDING_PAGES:
            page = ROOT / relative_path
            with self.subTest(page=relative_path):
                self.assertTrue(page.is_file())
                html = page.read_text(encoding="utf-8")
                self.assertEqual(html.count('class="our-intent"'), 1)
                for phrase in required:
                    self.assertIn(phrase, html)

    def test_shared_intent_styles_are_present(self):
        css = (ROOT / "assets/nurse-ai.css").read_text(encoding="utf-8")
        self.assertIn("/* ---------- Our Intent ---------- */", css)
        self.assertIn(".our-intent-lead", css)


if __name__ == "__main__":
    unittest.main()
