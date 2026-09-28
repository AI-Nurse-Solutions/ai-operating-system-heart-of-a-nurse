"""IPC contract between the manager core and the desktop host (build step 1.4).

Every envelope the real CLI prints must satisfy the JSON Schema, every
command must be declared, and the committed TypeScript must be exactly
what the generator produces from the schema. The Node test
(test_ipc_contract.mjs) checks the same fixtures with ajv and tsc.
"""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401
from _schema import check

from nurse_manager import cli

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gen_ipc_types  # noqa: E402
import ipc_fixtures  # noqa: E402

IPC = ROOT / "contracts" / "ipc"
SCHEMA = json.loads((IPC / "nurse-manager-ipc.schema.json").read_text(encoding="utf-8"))
COMMANDS = json.loads((IPC / "commands.json").read_text(encoding="utf-8"))


def validate(envelope):
    """Return "" if the envelope and its data satisfy the contract."""
    kind = "OkEnvelope" if envelope.get("ok") is True else "ErrorEnvelope"
    err = check(envelope, SCHEMA["$defs"][kind], SCHEMA)
    if err or kind == "ErrorEnvelope":
        return err
    type_name = COMMANDS["commands"].get(envelope["command"])
    if type_name is None:
        return f"undeclared command {envelope['command']}"
    return check(envelope["data"], SCHEMA["$defs"][type_name], SCHEMA, "$.data")


class IpcContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        cls.fixtures = ipc_fixtures.collect(Path(cls._tmp.name))

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()

    def test_every_real_envelope_satisfies_the_contract(self):
        for name, envelope in self.fixtures.items():
            with self.subTest(fixture=name):
                self.assertEqual(validate(envelope), "")

    def test_declared_commands_match_the_cli_exactly(self):
        self.assertEqual(sorted(COMMANDS["commands"]), sorted(cli.commands()))
        self.assertEqual(COMMANDS["contract"], cli.CONTRACT)
        self.assertEqual(SCHEMA["$defs"]["Contract"]["const"], cli.CONTRACT)

    def test_fixtures_exercise_every_command_and_both_outcomes(self):
        exercised = {e["command"] for e in self.fixtures.values() if e["ok"]}
        self.assertEqual(exercised, set(cli.commands()))
        self.assertTrue(any(not e["ok"] for e in self.fixtures.values()))

    def test_honest_states_reach_the_host(self):
        empty = self.fixtures["mission-empty"]["data"]
        self.assertEqual(empty["priorities"]["state"], "empty")
        self.assertEqual(empty["assistants_at_work"]["state"], "unavailable")
        denied = self.fixtures["export-denied"]
        self.assertTrue(denied["ok"])  # the proposal was recorded...
        self.assertEqual(denied["data"]["status"], "denied")  # ...and refused
        self.assertIn("SYNTHETIC EXAMPLE", self.fixtures["show-draft"]["data"]["markdown"])

    def test_ai_outcomes_reach_the_host_honestly(self):
        outcomes = {name: self.fixtures[name]["data"] for name in (
            "assistant-brief-no-model", "assistant-brief-unavailable", "assistant-brief-drafted")}
        self.assertEqual([d["outcome"] for d in outcomes.values()],
                         ["no_model", "provider_failed", "drafted"])
        self.assertEqual([d["drafted_by_model"] for d in outcomes.values()], [False, False, True])
        self.assertEqual(outcomes["assistant-brief-drafted"]["revision"]["created_by"],
                         "assistant:local")
        self.assertEqual(self.fixtures["assistant"]["data"]["provider"], "none")
        self.assertEqual(self.fixtures["assistant-off"]["data"]["provider"], "none")
        self.assertFalse(self.fixtures["assistant-preview-no-model"]["data"]["will_send"])
        preview = self.fixtures["assistant-preview"]["data"]
        self.assertTrue(preview["will_send"])
        self.assertEqual([c["gate"] for c in preview["checks"]], ["data_rules", "edena", "budget"])
        self.assertFalse(self.fixtures["error-assistant-brief-stale-preview"]["ok"])
        self.assertIn("AI DRAFT", self.fixtures["weekly-ai-draft"]["data"]["current"]["markdown"])
        self.assertIsNone(self.fixtures["weekly-empty"]["data"]["current"])
        kinds = {i["kind"] for i in
                 self.fixtures["mission-awaiting-approval"]["data"]["needs_my_judgment"]["items"]}
        self.assertIn("action", kinds)

    def test_the_contract_rejects_what_the_host_must_never_receive(self):
        run = self.fixtures["run"]
        mission = self.fixtures["mission"]
        cases = {
            "sent is not an outcome": (run, ("data", "outcome"), "sent"),
            "unknown field": (run, ("data", "payload"), "raw text"),
            "wrong contract version": (run, ("contract",), "nurse-manager-ipc@2"),
            "bad date": (mission, ("data", "today"), "30/09/2026"),
            "boolean is not a count": (mission, ("data", "task_counts", "idea"), True),
            "assistants cannot appear yet": (
                mission, ("data", "assistants_at_work", "items"), [{"id": "x"}]),
        }
        for label, (envelope, path, value) in cases.items():
            with self.subTest(case=label):
                broken = copy.deepcopy(envelope)
                target = broken
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                self.assertNotEqual(validate(broken), "")

    def test_generated_typescript_is_current(self):
        committed = (IPC / "nurse-manager-ipc.d.ts").read_text(encoding="utf-8")
        self.assertEqual(committed, gen_ipc_types.generate(),
                         "run: python3 nurse-manager/tools/gen_ipc_types.py")


if __name__ == "__main__":
    unittest.main()
