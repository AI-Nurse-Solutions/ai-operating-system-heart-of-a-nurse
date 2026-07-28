import unittest

import _bootstrap  # noqa: F401

from naio_integrations.contract import MemoryRecord
from naio_integrations.memory import GovernedMemory, MemoryGovernanceError


def make_record(**overrides) -> MemoryRecord:
    defaults = dict(
        memory_id="mem-1",
        tenant="personal:rn-1",
        role_scope="nurse",
        content="Prefers ADPIE-structured project summaries.",
        provenance="stated by user in onboarding, 2026-07-01",
        created_at="2026-07-01T12:00:00+00:00",
    )
    defaults.update(overrides)
    return MemoryRecord(**defaults)


class MemoryContractTests(unittest.TestCase):
    def setUp(self):
        self.memory = GovernedMemory()

    def test_remember_requires_known_consent_verb(self):
        with self.assertRaises(MemoryGovernanceError):
            self.memory.remember(make_record(), consent="sure")

    def test_do_not_remember_stores_nothing(self):
        with self.assertRaises(MemoryGovernanceError):
            self.memory.remember(make_record(), consent="do_not_remember")
        self.assertEqual(self.memory.recall("personal:rn-1", "nurse", "ADPIE"), ())

    def test_ask_before_remembering_defers_to_the_human(self):
        with self.assertRaises(MemoryGovernanceError) as ctx:
            self.memory.remember(make_record(), consent="ask_before_remembering")
        self.assertIn("ask the human", str(ctx.exception))

    def test_memory_without_provenance_is_rejected(self):
        with self.assertRaises(MemoryGovernanceError):
            self.memory.remember(make_record(provenance=""), consent="remember")

    def test_consented_memory_is_stored_and_recalled(self):
        self.memory.remember(make_record(), consent="remember")
        results = self.memory.recall("personal:rn-1", "nurse", "adpie")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].memory_id, "mem-1")

    def test_patient_identifiers_are_quarantined_not_remembered(self):
        stored = self.memory.remember(
            make_record(content="Follow up on MRN: A123456 tomorrow"),
            consent="remember",
        )
        self.assertTrue(stored.quarantined)
        self.assertNotIn("A123456", stored.content)
        self.assertEqual(self.memory.recall("personal:rn-1", "nurse", "follow"), ())

    def test_recall_never_crosses_tenants(self):
        self.memory.remember(make_record(), consent="remember")
        self.assertEqual(self.memory.recall("org:mercy", "nurse", "ADPIE"), ())

    def test_recall_respects_role_scope(self):
        self.memory.remember(make_record(role_scope="educator"), consent="remember")
        self.assertEqual(self.memory.recall("personal:rn-1", "student", "ADPIE"), ())
        self.assertEqual(
            len(self.memory.recall("personal:rn-1", "educator", "ADPIE")), 1
        )

    def test_expired_memories_are_not_recalled(self):
        self.memory.remember(
            make_record(expires_at="2026-01-01"), consent="remember"
        )
        self.assertEqual(self.memory.recall("personal:rn-1", "nurse", "ADPIE"), ())

    def test_forget_honors_deletion_immediately(self):
        self.memory.remember(make_record(), consent="remember")
        self.assertTrue(self.memory.forget("personal:rn-1", "mem-1"))
        self.assertEqual(self.memory.recall("personal:rn-1", "nurse", "ADPIE"), ())
        self.assertFalse(self.memory.forget("personal:rn-1", "mem-1"))

    def test_correct_replaces_content_with_new_provenance(self):
        self.memory.remember(make_record(), consent="remember")
        corrected = self.memory.correct(
            "personal:rn-1",
            "mem-1",
            content="Prefers SBAR-structured summaries.",
            provenance="corrected by user, 2026-07-15",
        )
        self.assertIn("SBAR", corrected.content)
        results = self.memory.recall("personal:rn-1", "nurse", "sbar")
        self.assertEqual(len(results), 1)
        self.assertIn("corrected by user", results[0].provenance)

    def test_correcting_a_missing_memory_fails(self):
        with self.assertRaises(MemoryGovernanceError):
            self.memory.correct("personal:rn-1", "ghost", "x", "y")

    def test_quarantine_removes_memory_from_recall(self):
        self.memory.remember(make_record(), consent="remember")
        self.assertTrue(
            self.memory.quarantine("personal:rn-1", "mem-1", "possible poisoning")
        )
        self.assertEqual(self.memory.recall("personal:rn-1", "nurse", "ADPIE"), ())

    def test_quarantine_requires_a_reason(self):
        self.memory.remember(make_record(), consent="remember")
        self.assertFalse(self.memory.quarantine("personal:rn-1", "mem-1", ""))


if __name__ == "__main__":
    unittest.main()
