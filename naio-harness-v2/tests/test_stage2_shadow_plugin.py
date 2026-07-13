import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from naio_harness.runtime_gate import ShadowGate

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "hermes-plugin" / "naio-edena-runtime" / "__init__.py"


class FakePluginContext:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, name, callback):
        self.hooks[name] = callback


def load_plugin_module():
    spec = importlib.util.spec_from_file_location("naio_edena_runtime_test", PLUGIN)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage2ShadowGateTests(unittest.TestCase):
    def test_shadow_decisions_are_non_mutating(self):
        with tempfile.TemporaryDirectory() as tmp:
            gate = ShadowGate(ROOT, Path(tmp) / "events.jsonl")
            self.assertEqual(gate.evaluate("read_file", {"path": "safe.md"})["decision"], "allow")
            self.assertEqual(gate.evaluate("write_file", {"path": "draft.md"})["decision"], "draft_only")
            self.assertEqual(gate.evaluate("unknown_power", {})["decision"], "block")
            self.assertEqual(gate.evaluate("send_message", {"text": "hello"})["decision"], "block")

    def test_shadow_log_never_contains_argument_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "events.jsonl"
            gate = ShadowGate(ROOT, log)
            secret_value = "patient-name-should-never-be-logged"
            gate.observe("read_file", {"path": secret_value, "token": "secret-token-value"})
            raw = log.read_text()
            event = json.loads(raw)
            self.assertNotIn(secret_value, raw)
            self.assertNotIn("secret-token-value", raw)
            self.assertEqual(event["argument_names"], ["path", "token"])
            self.assertFalse(event["payload_captured"])
            self.assertEqual(event["mode"], "shadow")
            self.assertEqual(event["observed_decision"], "allow")

    def test_plugin_registers_real_hermes_hook_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            old_root = os.environ.get("NAIO_HARNESS_ROOT")
            old_log = os.environ.get("NAIO_SHADOW_LOG")
            os.environ["NAIO_HARNESS_ROOT"] = str(ROOT)
            os.environ["NAIO_SHADOW_LOG"] = str(Path(tmp) / "plugin-events.jsonl")
            try:
                module = load_plugin_module()
                context = FakePluginContext()
                module.register(context)
                self.assertIn("pre_tool_call", context.hooks)
                result = context.hooks["pre_tool_call"](
                    tool_name="read_file", args={"path": "private-value"}, task_id="ignored"
                )
                self.assertIsNone(result)
                raw = Path(os.environ["NAIO_SHADOW_LOG"]).read_text()
                self.assertNotIn("private-value", raw)
                self.assertEqual(json.loads(raw)["observed_decision"], "allow")
            finally:
                if old_root is None:
                    os.environ.pop("NAIO_HARNESS_ROOT", None)
                else:
                    os.environ["NAIO_HARNESS_ROOT"] = old_root
                if old_log is None:
                    os.environ.pop("NAIO_SHADOW_LOG", None)
                else:
                    os.environ["NAIO_SHADOW_LOG"] = old_log


if __name__ == "__main__":
    unittest.main()
