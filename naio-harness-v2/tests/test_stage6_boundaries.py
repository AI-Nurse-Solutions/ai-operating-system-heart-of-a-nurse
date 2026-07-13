import json
import tempfile
import unittest
from pathlib import Path

from naio_harness.budgets import BudgetExceeded, BudgetManager
from naio_harness.connectors import ConnectorError, ConnectorPolicy
from naio_harness.routing import ModelRouterPolicy, RoutingError
from naio_harness.runtime_gate import RuntimeGate
from naio_harness.trust_cells import TrustCells

ROOT = Path(__file__).resolve().parents[1]
ENFORCE_CONFIG = ROOT / "config" / "runtime-profile-enforce.json"


class Stage6BoundaryTests(unittest.TestCase):
    def test_untrusted_intake_has_public_research_only(self):
        cells = TrustCells(ROOT / "config" / "trust-cells.json")
        layer = cells.layer("untrusted-intake")
        self.assertEqual(layer.allow, frozenset({"web.research"}))
        self.assertTrue({"local.read", "local.draft", "external.publish"}.issubset(layer.deny))

    def test_child_cell_cannot_regrant_parent_denial(self):
        cells = TrustCells(ROOT / "config" / "trust-cells.json")
        layer = cells.layer("governed-executor", parent_effective={"local.read", "local.draft"})
        self.assertEqual(layer.allow, frozenset({"local.read", "local.draft"}))
        self.assertNotIn("external.publish", layer.allow)

    def test_budget_exhaustion_blocks_and_run_identifier_is_hashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "budgets.json"
            budget = BudgetManager(path)
            self.assertEqual(budget.consume("private-session-id", "external.publish", 1), 1)
            with self.assertRaises(BudgetExceeded):
                budget.consume("private-session-id", "external.publish", 1)
            self.assertNotIn("private-session-id", path.read_text())

    def test_runtime_gate_blocks_second_external_call_for_same_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = RuntimeGate(ROOT, Path(tmp) / "events.jsonl", ENFORCE_CONFIG, mode="enforce")
            first = gate.enforce("send_message", {"text": "Synthetic public"}, session_id="run-1")
            second = gate.enforce("send_message", {"text": "Synthetic public"}, session_id="run-1")
            self.assertEqual(first["action"], "approve")
            self.assertEqual(second["action"], "block")
            self.assertIn("BUDGET-EXHAUSTED", second["message"])

    def test_oversized_result_is_truncated_at_manifest_budget(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = RuntimeGate(ROOT, Path(tmp) / "events.jsonl", ENFORCE_CONFIG, mode="enforce")
            maximum = gate.manifests["local.read"].budgets["max_output_bytes"]
            transformed = gate.transform_result("read_file", "x" * (maximum + 20))
            self.assertIsNotNone(transformed)
            self.assertIn("EDENA: tool result truncated", transformed)
            self.assertLess(len(transformed), maximum + 200)
            self.assertIsNone(gate.transform_result("read_file", "short"))

    def test_private_model_fallback_cannot_change_provider(self):
        router = ModelRouterPolicy(ROOT / "config" / "model-routing.json")
        with self.assertRaises(RoutingError):
            router.authorize_fallback(
                data_class="private-non-phi", current_provider="provider-a",
                fallback_provider="provider-b", fallback_index=1, fallback_manifested=True,
            )
        allowed = router.authorize_fallback(
            data_class="public", current_provider="provider-a",
            fallback_provider="provider-b", fallback_index=1, fallback_manifested=True,
        )
        self.assertTrue(allowed["allowed"])
        with self.assertRaises(RoutingError):
            router.authorize_fallback(
                data_class="phi", current_provider="provider-a",
                fallback_provider="provider-a", fallback_index=1, fallback_manifested=True,
            )

    def test_connector_requires_strict_public_https_manifest(self):
        policy = ConnectorPolicy(ROOT / "config" / "connector-policy.json")
        valid = {
            "connector_id": "mcp-docs-readonly",
            "endpoint": "https://modelcontextprotocol.io/docs",
            "auth_mode": "none",
            "token_passthrough": False,
            "data_class": "public",
            "capabilities": ["read_public_docs"],
        }
        self.assertTrue(policy.validate(valid)["allowed"])
        invalid_cases = [
            {**valid, "endpoint": "http://modelcontextprotocol.io/docs"},
            {**valid, "endpoint": "https://127.0.0.1/service"},
            {**valid, "endpoint": "https://unknown.example/service"},
            {**valid, "token_passthrough": True},
            {**valid, "data_class": "private-non-phi"},
            {**valid, "unexpected": True},
        ]
        for manifest in invalid_cases:
            with self.subTest(manifest=manifest):
                with self.assertRaises(ConnectorError):
                    policy.validate(manifest)

    def test_connector_and_routing_configs_are_fail_closed(self):
        connector = json.loads((ROOT / "config" / "connector-policy.json").read_text())
        routing = json.loads((ROOT / "config" / "model-routing.json").read_text())
        self.assertEqual(connector["unknown_host_disposition"], "block")
        self.assertFalse(connector["token_passthrough"])
        self.assertEqual(routing["unknown_provider_disposition"], "block")
        self.assertFalse(routing["quality_may_override_privacy"])


if __name__ == "__main__":
    unittest.main()
