import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.contract import (
    ActionMode,
    Actor,
    DataClass,
    DataZone,
    Decision,
    GatewayRequest,
    RiskTier,
)
from naio_integrations.gateway import EdenaPolicyGateway
from naio_integrations.policy import EdenaPolicyEngine

NURSE = Actor(actor_id="rn-1", role="nurse", tenant="personal:rn-1")


def make_request(**overrides) -> GatewayRequest:
    defaults = dict(
        request_id="req-1",
        actor=NURSE,
        intent="summarize_reflection",
        content="Private end-of-shift reflection about workload and recovery.",
        risk_tier=RiskTier.GREEN,
        data_class=DataClass.D0,
        action_mode=ActionMode.DRAFT,
    )
    defaults.update(overrides)
    return GatewayRequest(**defaults)


class DataZoneTaxonomyTests(unittest.TestCase):
    def test_zones_match_the_mission_control_specification(self):
        self.assertEqual(
            [zone.value for zone in DataZone],
            [
                "private",
                "shared_professional",
                "educational_record",
                "institutional",
                "restricted",
            ],
        )

    def test_requests_default_to_the_private_zone(self):
        self.assertIs(make_request().data_zone, DataZone.PRIVATE)


class PrivateReflectionProtectionTests(unittest.TestCase):
    def setUp(self):
        self.engine = EdenaPolicyEngine()

    def test_private_content_never_reaches_oversight_audiences(self):
        for audience in ("manager", "faculty", "cohort", "executive", "organization"):
            decision = self.engine.decide(
                make_request(metadata={"audience": audience})
            )
            self.assertIs(decision.decision, Decision.DENY, audience)
            self.assertIn("EDENA-PRIVATE-REFLECTION", decision.reason_codes)

    def test_private_content_for_the_user_themselves_is_allowed(self):
        for audience in ("", "self", "mentee"):
            decision = self.engine.decide(
                make_request(metadata={"audience": audience})
            )
            self.assertIs(decision.decision, Decision.ALLOW, audience)

    def test_shared_professional_content_may_reach_a_manager(self):
        decision = self.engine.decide(
            make_request(
                data_zone=DataZone.SHARED_PROFESSIONAL,
                intent="project_status_summary",
                content="Milestone summary for the falls project.",
                metadata={"audience": "manager"},
            )
        )
        self.assertIs(decision.decision, Decision.ALLOW)


class ZoneMigrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = EdenaPolicyEngine()

    def test_zone_migration_requires_explicit_approval(self):
        decision = self.engine.decide(
            make_request(metadata={"target_zone": "shared_professional"})
        )
        self.assertIs(decision.decision, Decision.REQUIRE_APPROVAL)
        self.assertIn("EDENA-ZONE-MIGRATION", decision.reason_codes)
        self.assertIn("record_zone_migration_approval", decision.obligations)

    def test_approved_zone_migration_is_allowed_and_logged(self):
        decision = self.engine.decide(
            make_request(
                metadata={
                    "target_zone": "shared_professional",
                    "zone_migration_approval": "appr-12",
                }
            )
        )
        self.assertIs(decision.decision, Decision.ALLOW)
        self.assertIn("log_zone_migration", decision.obligations)

    def test_same_zone_target_is_not_a_migration(self):
        decision = self.engine.decide(
            make_request(metadata={"target_zone": "private"})
        )
        self.assertIs(decision.decision, Decision.ALLOW)
        self.assertNotIn("log_zone_migration", decision.obligations)

    def test_unknown_target_zones_are_denied_not_approved(self):
        for bogus in ("external", "public-internet", "Institutional"):
            decision = self.engine.decide(
                make_request(
                    metadata={
                        "target_zone": bogus,
                        "zone_migration_approval": "appr-12",
                    }
                )
            )
            self.assertIs(decision.decision, Decision.DENY, bogus)
            self.assertIn("EDENA-INVALID-ZONE", decision.reason_codes, bogus)


class GatewayZoneTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.gateway = EdenaPolicyGateway(trace_root=Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_private_reflection_cannot_be_summarized_for_an_executive_view(self):
        result = self.gateway.submit(
            make_request(metadata={"audience": "executive"})
        )
        self.assertIs(result.decision, Decision.DENY)
        self.assertIn("EDENA-PRIVATE-REFLECTION", result.reason_codes)

    def test_traces_record_the_data_zone(self):
        self.gateway.submit(make_request())
        records = self.gateway.tracer.read("personal:rn-1")
        start = next(r for r in records if r["kind"] == "trace_start")
        self.assertEqual(start["data_zone"], "private")


if __name__ == "__main__":
    unittest.main()
