import dataclasses
import unittest

import _bootstrap  # noqa: F401

from naio_integrations.privacy import PrivacyScreen


class PrivacyScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.screen = PrivacyScreen()

    def test_clean_educational_text_passes_untouched(self):
        text = "Sepsis bundles emphasize early recognition and timely escalation."
        result = self.screen.transform(text)
        self.assertEqual(result.action, "pass")
        self.assertEqual(result.transformed_text, text)
        self.assertTrue(result.clean)

    def test_detects_healthcare_identifiers(self):
        cases = {
            "MRN: A123456 was updated": "MRN",
            "SSN 123-45-6789 on file": "US_SSN",
            "DOB: 04/12/1985 confirmed": "DOB",
            "moved to room 412, bed B overnight": "ROOM_BED",
            "admitted 06/02/2026 for observation": "ENCOUNTER_DATE",
            "provider id: 884213 signed the note": "PROVIDER_ID",
            "call me at (555) 123-4567": "PHONE_NUMBER",
            "email nurse.jane@example.org today": "EMAIL_ADDRESS",
            "token sk_live_abcdefghijklmnopqrstuv leaked": "CREDENTIAL",
        }
        for text, entity_type in cases.items():
            findings = self.screen.analyze(text)
            self.assertTrue(findings, text)
            self.assertIn(entity_type, {f.entity_type for f in findings}, text)

    def test_redaction_removes_the_identifier_from_the_text(self):
        result = self.screen.transform("Patient MRN: A123456 admitted 06/02/2026.")
        self.assertEqual(result.action, "redact")
        self.assertNotIn("A123456", result.transformed_text)
        self.assertNotIn("06/02/2026", result.transformed_text)
        self.assertIn("<MRN>", result.transformed_text)
        self.assertIn("<ENCOUNTER_DATE>", result.transformed_text)

    def test_findings_never_carry_the_raw_value(self):
        secret = "123-45-6789"
        findings = self.screen.analyze(f"SSN {secret} noted")
        for finding in findings:
            for value in dataclasses.asdict(finding).values():
                self.assertNotIn(secret, str(value))

    def test_block_mode_returns_empty_text(self):
        result = self.screen.transform("MRN: A123456", mode="block")
        self.assertEqual(result.action, "block")
        self.assertEqual(result.transformed_text, "")
        self.assertFalse(result.clean)

    def test_overlapping_findings_do_not_duplicate_text(self):
        text = "SSN: 123-45-6789"
        result = self.screen.transform(text)
        self.assertNotIn("123-45-6789", result.transformed_text)
        self.assertLessEqual(result.transformed_text.count("US_SSN"), 2)

    def test_multiple_identifiers_all_redacted(self):
        text = (
            "Reach charge nurse at 555-867-5309 or nurse@example.org "
            "about MRN: Z99887."
        )
        result = self.screen.transform(text)
        for raw in ("555-867-5309", "nurse@example.org", "Z99887"):
            self.assertNotIn(raw, result.transformed_text)


if __name__ == "__main__":
    unittest.main()
