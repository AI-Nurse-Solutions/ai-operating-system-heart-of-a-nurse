import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Stage0SemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy = json.loads((ROOT / "config" / "edena-semantics.json").read_text())
        cls.schema = json.loads((ROOT / "schema" / "edena-decision.schema.json").read_text())

    def test_risk_and_autonomy_are_separate_dimensions(self):
        self.assertEqual(set(self.policy["risk_tiers"]), {"green", "yellow", "orange", "red"})
        self.assertEqual(set(self.policy["autonomy_levels"]), {"A0", "A1", "A2", "A3", "A4"})

    def test_red_is_stop_not_high_autonomy(self):
        red = self.policy["risk_tiers"]["red"]
        self.assertEqual(red["default_disposition"], "block")
        self.assertEqual(self.policy["invariants"]["red_max_autonomy"], "A0")

    def test_self_service_excludes_high_autonomy(self):
        self.assertEqual(self.policy["invariants"]["self_service_max_autonomy"], "A2")
        self.assertFalse(self.policy["invariants"]["downstream_may_regrant"])

    def test_hard_redlines_are_explicit(self):
        required = {
            "phi_or_patient_identifier",
            "patient_specific_clinical_decision",
            "named_personnel_decision",
            "payment_or_financial_execution",
            "credential_or_secret_handling",
            "unmanifested_capability",
        }
        self.assertTrue(required.issubset(set(self.policy["hard_redlines"])))

    def test_decision_schema_rejects_unknown_fields(self):
        self.assertFalse(self.schema["additionalProperties"])
        self.assertIn("risk_tier", self.schema["required"])
        self.assertIn("autonomy_level", self.schema["required"])


if __name__ == "__main__":
    unittest.main()
