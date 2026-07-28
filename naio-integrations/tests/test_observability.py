import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.contract import (
    ActionMode,
    Actor,
    DataClass,
    GatewayRequest,
    RiskTier,
)
from naio_integrations.observability import GatewayTracer


def make_request(tenant: str = "personal:rn-1") -> GatewayRequest:
    return GatewayRequest(
        request_id="req-1",
        actor=Actor(actor_id="rn-1", role="nurse", tenant=tenant),
        intent="summarize_policy",
        content="MRN: A123456 should never appear in traces",
        risk_tier=RiskTier.YELLOW,
        data_class=DataClass.D2,
        action_mode=ActionMode.DRAFT,
    )


class GatewayTracerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tracer = GatewayTracer(Path(self.tmp.name))

    def tearDown(self):
        self.tmp.cleanup()

    def test_trace_lifecycle_records_start_spans_and_end(self):
        trace_id = self.tracer.start_trace(make_request())
        self.tracer.record_span(trace_id, "policy_decision", {"decision": "allow"})
        self.tracer.end_trace(trace_id, "allow")
        records = self.tracer.read("personal:rn-1")
        self.assertEqual(
            [record["kind"] for record in records],
            ["trace_start", "span", "trace_end"],
        )
        self.assertEqual(records[-1]["outcome"], "allow")

    def test_traces_never_store_raw_content(self):
        trace_id = self.tracer.start_trace(make_request())
        self.tracer.end_trace(trace_id, "allow")
        raw = json.dumps(self.tracer.read("personal:rn-1"))
        self.assertNotIn("A123456", raw)
        self.assertIn("content_length", raw)

    def test_span_payloads_reject_raw_content_keys(self):
        trace_id = self.tracer.start_trace(make_request())
        with self.assertRaises(ValueError):
            self.tracer.record_span(trace_id, "leaky", {"content": "MRN: A123456"})

    def test_tenants_are_separated_into_distinct_streams(self):
        personal = self.tracer.start_trace(make_request("personal:rn-1"))
        org = self.tracer.start_trace(make_request("org:mercy"))
        self.tracer.end_trace(personal, "allow")
        self.tracer.end_trace(org, "deny")
        personal_records = self.tracer.read("personal:rn-1")
        org_records = self.tracer.read("org:mercy")
        self.assertTrue(all(r["tenant"] == "personal:rn-1" for r in personal_records))
        self.assertTrue(all(r["tenant"] == "org:mercy" for r in org_records))
        files = sorted(path.name for path in Path(self.tmp.name).glob("traces-*.jsonl"))
        self.assertEqual(len(files), 2)

    def test_hash_chain_verifies_and_detects_tampering(self):
        trace_id = self.tracer.start_trace(make_request())
        self.tracer.end_trace(trace_id, "allow")
        verification = self.tracer.verify("personal:rn-1")
        self.assertTrue(verification["ok"])
        self.assertEqual(verification["count"], 2)
        path = next(Path(self.tmp.name).glob("traces-*.jsonl"))
        lines = path.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[0])
        record["intent"] = "tampered"
        lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"))
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            self.tracer.verify("personal:rn-1")

    def test_unknown_trace_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            self.tracer.record_span("missing", "span", {})
        with self.assertRaises(ValueError):
            self.tracer.end_trace("missing", "allow")


if __name__ == "__main__":
    unittest.main()
