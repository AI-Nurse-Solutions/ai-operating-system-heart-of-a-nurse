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

    def test_span_payload_screening_is_recursive_and_case_insensitive(self):
        trace_id = self.tracer.start_trace(make_request())
        for payload in (
            {"Content": "raw"},
            {"detail": {"RAW": "raw"}},
            {"items": [{"text": "raw"}]},
            {"deep": [{"inner": {"Payload": "raw"}}]},
        ):
            with self.assertRaises(ValueError, msg=payload):
                self.tracer.record_span(trace_id, "leaky", payload)

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

    def test_sanitization_collisions_still_get_distinct_streams(self):
        colliding_a = self.tracer.start_trace(make_request("org:a/b"))
        colliding_b = self.tracer.start_trace(make_request("org:a?b"))
        self.tracer.end_trace(colliding_a, "allow")
        self.tracer.end_trace(colliding_b, "deny")
        records_a = self.tracer.read("org:a/b")
        records_b = self.tracer.read("org:a?b")
        self.assertTrue(all(r["tenant"] == "org:a/b" for r in records_a))
        self.assertTrue(all(r["tenant"] == "org:a?b" for r in records_b))
        self.assertEqual(len(records_a), 2)
        self.assertEqual(len(records_b), 2)
        files = list(Path(self.tmp.name).glob("traces-*.jsonl"))
        self.assertEqual(len(files), 2)

    def test_concurrent_readers_never_see_partial_records(self):
        import threading

        trace_id = self.tracer.start_trace(make_request())
        errors: list[Exception] = []
        reader_active = threading.Event()
        done = threading.Event()

        def write() -> None:
            try:
                # Handshake: no appends until the reader has completed at
                # least one read, so the loops genuinely overlap and the
                # read path is exercised against in-flight writes.
                if not reader_active.wait(timeout=10):
                    raise RuntimeError("reader never started")
                for i in range(15):
                    self.tracer.record_span(trace_id, f"span-{i}", {"i": i})
            except Exception as exc:  # noqa: BLE001 - forwarded for assertion
                errors.append(exc)
            finally:
                done.set()

        def read_repeatedly() -> None:
            try:
                while not done.is_set():
                    records = self.tracer.read("personal:rn-1")
                    self.assertTrue(all("record_hash" in r for r in records))
                    self.tracer.verify("personal:rn-1")
                    reader_active.set()
            except Exception as exc:  # noqa: BLE001 - forwarded for assertion
                errors.append(exc)

        writer = threading.Thread(target=write)
        reader = threading.Thread(target=read_repeatedly)
        reader.start()
        writer.start()
        writer.join()
        reader.join()
        self.assertEqual(errors, [])
        self.assertTrue(reader_active.is_set())
        self.assertEqual(self.tracer.verify("personal:rn-1")["count"], 16)

    def test_concurrent_appends_keep_the_chain_intact(self):
        import threading

        trace_id = self.tracer.start_trace(make_request())
        errors: list[Exception] = []

        def spam(worker: int) -> None:
            try:
                for i in range(5):
                    self.tracer.record_span(
                        trace_id, f"span-{worker}-{i}", {"worker": worker, "i": i}
                    )
            except Exception as exc:  # noqa: BLE001 - forwarded for assertion
                errors.append(exc)

        threads = [threading.Thread(target=spam, args=(w,)) for w in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        verification = self.tracer.verify("personal:rn-1")
        self.assertTrue(verification["ok"])
        self.assertEqual(verification["count"], 21)


if __name__ == "__main__":
    unittest.main()
