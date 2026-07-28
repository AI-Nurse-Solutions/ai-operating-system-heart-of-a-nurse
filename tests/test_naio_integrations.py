"""Repo-level regression for the Nurse AI OS Integration Contract package.

Runs the package's own unittest suite in a subprocess (exactly how CI and
contributors run it) and smoke-tests the EDENA Policy Gateway end to end
from the repository root.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "naio-integrations"
SRC = PACKAGE / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class IntegrationPackageSuiteTests(unittest.TestCase):
    def test_package_suite_passes(self):
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                str(PACKAGE / "tests"),
                "-p",
                "test_*.py",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=300,
        )
        self.assertEqual(
            completed.returncode,
            0,
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}",
        )

    def test_policy_config_is_valid_json_with_required_rules(self):
        policy = json.loads(
            (PACKAGE / "config" / "edena-gateway-policy.json").read_text(encoding="utf-8")
        )
        self.assertIn("red-p", policy["prohibited"]["risk_tiers"])
        self.assertIn("unrestricted_autonomy", policy["prohibited"]["action_modes"])
        self.assertEqual(policy["tier_data_ceilings"]["green"], "D0")
        self.assertIn("student", policy["role_rules"])
        self.assertTrue(policy["zone_rules"]["migration_requires_approval"])
        for audience in ("manager", "faculty", "cohort", "executive"):
            self.assertIn(
                audience, policy["zone_rules"]["private_zone_denied_audiences"]
            )

    def test_recognizer_config_covers_healthcare_identifiers(self):
        config = json.loads(
            (PACKAGE / "config" / "privacy-recognizers.json").read_text(encoding="utf-8")
        )
        entity_types = {item["entity_type"] for item in config["recognizers"]}
        for required in ("MRN", "ROOM_BED", "ENCOUNTER_DATE", "PROVIDER_ID"):
            self.assertIn(required, entity_types)

    def test_gateway_smoke_from_repository_root(self):
        from naio_integrations.contract import (
            ActionMode,
            Actor,
            DataClass,
            Decision,
            GatewayRequest,
            RiskTier,
        )
        from naio_integrations.gateway import EdenaPolicyGateway

        with tempfile.TemporaryDirectory() as tmp:
            gateway = EdenaPolicyGateway(trace_root=Path(tmp))
            actor = Actor(actor_id="rn-1", role="nurse", tenant="personal:rn-1")
            allowed = gateway.submit(
                GatewayRequest(
                    request_id="smoke-1",
                    actor=actor,
                    intent="summarize_policy",
                    content="Draft a falls-prevention huddle outline.",
                    risk_tier=RiskTier.GREEN,
                    data_class=DataClass.D0,
                    action_mode=ActionMode.DRAFT,
                )
            )
            self.assertIs(allowed.decision, Decision.ALLOW)
            denied = gateway.submit(
                GatewayRequest(
                    request_id="smoke-2",
                    actor=actor,
                    intent="summarize_chart",
                    content="Summarize the chart for MRN: A123456.",
                    risk_tier=RiskTier.GREEN,
                    data_class=DataClass.D0,
                    action_mode=ActionMode.DRAFT,
                )
            )
            self.assertIs(denied.decision, Decision.DENY)
            self.assertIn("EDENA-PRIVACY-REDLINE", denied.reason_codes)
            self.assertTrue(gateway.tracer.verify("personal:rn-1")["ok"])

    def test_package_readme_states_scope_and_limits(self):
        readme = " ".join(
            (PACKAGE / "README.md").read_text(encoding="utf-8").casefold().split()
        )
        for phrase in (
            "not clinical decision support",
            "never proves",
            "humans retain authority",
            "edena policy gateway",
        ):
            self.assertIn(phrase, readme, phrase)


if __name__ == "__main__":
    unittest.main()
