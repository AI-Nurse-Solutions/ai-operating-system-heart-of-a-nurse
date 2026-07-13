import json
import tempfile
import unittest
from pathlib import Path

from naio_harness.evaluations import run_evaluations
from naio_harness.ledger import GENESIS_HASH, LedgerError, ProvenanceLedger

ROOT = Path(__file__).resolve().parents[1]


class Stage4ProvenanceTests(unittest.TestCase):
    def test_hash_chain_verifies_and_has_terminal_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            ledger = ProvenanceLedger(path)
            first = ledger.append({"decision": "allow", "payload_captured": False})
            second = ledger.append({"decision": "block", "payload_captured": False})
            report = ledger.verify()
            self.assertTrue(report["ok"])
            self.assertEqual(report["count"], 2)
            self.assertEqual(first["previous_hash"], GENESIS_HASH)
            self.assertEqual(second["previous_hash"], first["event_hash"])
            self.assertEqual(report["terminal_hash"], second["event_hash"])

    def test_modification_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            ledger = ProvenanceLedger(path)
            ledger.append({"decision": "block", "payload_captured": False})
            record = json.loads(path.read_text())
            record["decision"] = "allow"
            path.write_text(json.dumps(record) + "\n")
            with self.assertRaises(LedgerError):
                ledger.verify()

    def test_deletion_or_reordering_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ledger.jsonl"
            ledger = ProvenanceLedger(path)
            ledger.append({"decision": "allow"})
            ledger.append({"decision": "block"})
            lines = path.read_text().splitlines()
            path.write_text(lines[1] + "\n" + lines[0] + "\n")
            with self.assertRaises(LedgerError):
                ledger.verify()

    def test_versioned_synthetic_evaluation_dataset_passes(self):
        report = run_evaluations(ROOT)
        self.assertTrue(report["ok"])
        self.assertTrue(report["synthetic_only"])
        self.assertEqual(report["case_count"], 8)
        self.assertEqual(report["passed"], 8)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(len(report["dataset_hash"]), 64)
        self.assertEqual(len(report["terminal_provenance_root"]), 64)
        self.assertTrue(report["dataset_version"].startswith("2026.07.13"))


if __name__ == "__main__":
    unittest.main()
