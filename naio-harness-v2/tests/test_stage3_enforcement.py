import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

from naio_harness.runtime_gate import RuntimeGate

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "hermes-plugin" / "naio-edena-runtime" / "__init__.py"
ENFORCE_CONFIG = ROOT / "config" / "runtime-profile-enforce.json"


class FakePluginContext:
    def __init__(self):
        self.hooks = {}

    def register_hook(self, name, callback):
        self.hooks[name] = callback


def load_plugin(name="naio_edena_enforce_test"):
    spec = importlib.util.spec_from_file_location(name, PLUGIN)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Stage3EnforcementTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = Path(self.tmp.name) / "events.jsonl"
        self.gate = RuntimeGate(ROOT, self.log, ENFORCE_CONFIG, mode="enforce")

    def tearDown(self):
        self.tmp.cleanup()

    def test_safe_read_and_local_draft_proceed(self):
        self.assertIsNone(self.gate.enforce("read_file", {"path": "public.md"}))
        self.assertIsNone(self.gate.enforce("write_file", {"path": "draft.md", "content": "public draft"}))

    def test_unknown_tool_fails_closed(self):
        directive = self.gate.enforce("unknown_power", {})
        self.assertEqual(directive["action"], "block")
        self.assertIn("UNMANIFESTED", directive["message"])

    def test_sensitive_field_blocks_without_logging_value(self):
        private_value = "Patient Example"
        directive = self.gate.enforce("write_file", {"path": "draft.md", "patient_name": private_value})
        self.assertEqual(directive["action"], "block")
        raw = self.log.read_text()
        self.assertNotIn(private_value, raw)
        self.assertIn("EDENA-REDLINE-SENSITIVE-FIELD", raw)

    def test_sensitive_content_pattern_blocks(self):
        private_value = "MRN: ABCD1234"
        directive = self.gate.enforce("write_file", {"path": "draft.md", "content": private_value})
        self.assertEqual(directive["action"], "block")
        self.assertNotIn(private_value, self.log.read_text())

    def test_external_side_effect_routes_to_native_approval(self):
        directive = self.gate.enforce("send_message", {"text": "Public release candidate"})
        self.assertEqual(directive["action"], "approve")
        self.assertEqual(directive["rule_key"], "naio:external.publish")

    def test_plugin_enforcement_error_fails_closed(self):
        env = {
            "NAIO_HARNESS_ROOT": str(ROOT),
            "NAIO_EDENA_MODE": "enforce",
            "NAIO_RUNTIME_CONFIG": str(ROOT / "config" / "missing.json"),
            "NAIO_SHADOW_LOG": str(self.log),
        }
        previous = {key: os.environ.get(key) for key in env}
        os.environ.update(env)
        try:
            module = load_plugin("naio_edena_missing_config_test")
            context = FakePluginContext()
            module.register(context)
            directive = context.hooks["pre_tool_call"](tool_name="send_message", args={"text": "x"})
            self.assertEqual(directive["action"], "block")
            self.assertIn("failed closed", directive["message"])
        finally:
            for key, value in previous.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_invalid_mode_fails_closed(self):
        previous = os.environ.get("NAIO_EDENA_MODE")
        os.environ["NAIO_EDENA_MODE"] = "unsafe-typo"
        try:
            module = load_plugin("naio_edena_invalid_mode_test")
            context = FakePluginContext()
            module.register(context)
            directive = context.hooks["pre_tool_call"](tool_name="read_file", args={"path": "x"})
            self.assertEqual(directive["action"], "block")
        finally:
            if previous is None:
                os.environ.pop("NAIO_EDENA_MODE", None)
            else:
                os.environ["NAIO_EDENA_MODE"] = previous

    def test_event_payload_is_metadata_only(self):
        self.gate.enforce("send_message", {"text": "public content", "destination": "external"})
        event = json.loads(self.log.read_text())
        self.assertFalse(event["payload_captured"])
        self.assertEqual(event["argument_names"], ["destination", "text"])
        self.assertNotIn("public content", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
