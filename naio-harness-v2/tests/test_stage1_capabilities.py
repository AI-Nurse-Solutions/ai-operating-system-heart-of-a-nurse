import json
import tempfile
import unittest
from pathlib import Path

from naio_harness.capabilities import ManifestError, compile_capabilities, load_manifest, load_manifests
from naio_harness.config_store import ConfigError, StrictConfigStore, load_runtime_config
from naio_harness.doctor import run_doctor
from naio_harness.models import CapabilityLayer, CompilationContext

ROOT = Path(__file__).resolve().parents[1]


class Stage1CapabilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifests = load_manifests(ROOT / "manifests")
        cls.context = CompilationContext(
            profile="test", audience="student", channel_trust="local",
            provider="test", sandbox="readonly", no_phi=True,
            self_service=True, gate_attested=False,
        )

    def test_all_sample_manifests_are_hash_verified(self):
        self.assertEqual(len(self.manifests), 4)
        for manifest in self.manifests.values():
            self.assertEqual(len(manifest.content_hash), 64)

    def test_unknown_manifest_field_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = json.loads((ROOT / "manifests" / "local.read.json").read_text())
            source["surprise"] = True
            path = Path(tmp) / "bad.json"
            path.write_text(json.dumps(source))
            with self.assertRaises(ManifestError):
                load_manifest(path)

    def test_later_layer_cannot_regrant(self):
        layers = [
            CapabilityLayer("narrow", allow=frozenset({"local.read"})),
            CapabilityLayer("attempted_regrant", allow=frozenset({"local.read", "web.research"})),
        ]
        result = compile_capabilities(self.manifests, {"local.read", "web.research"}, layers, self.context)
        self.assertEqual(result.effective, {"local.read"})
        self.assertEqual(result.trace[1]["before"], ["local.read"])

    def test_unmanifested_capability_blocks_compilation(self):
        result = compile_capabilities(self.manifests, {"unknown.tool"}, [], self.context)
        self.assertFalse(result.ok)
        self.assertEqual(result.effective, set())

    def test_red_and_high_autonomy_are_removed(self):
        modified = dict(self.manifests)
        original = modified["local.read"]
        from dataclasses import replace
        from naio_harness.models import AutonomyLevel, RiskTier
        modified["red.test"] = replace(original, capability_id="red.test", risk_tier=RiskTier.RED)
        modified["a3.test"] = replace(original, capability_id="a3.test", autonomy_ceiling=AutonomyLevel.A3)
        result = compile_capabilities(modified, {"red.test", "a3.test"}, [], self.context)
        self.assertEqual(result.effective, set())
        self.assertIn("red.test", result.removed["red_risk"])
        self.assertIn("a3.test", result.removed["self_service_autonomy_ceiling"])

    def test_side_effect_capability_requires_attested_gate(self):
        builder_context = CompilationContext(
            profile="test", audience="builder", channel_trust="local",
            provider="test", sandbox="governed", no_phi=True,
            self_service=False, gate_attested=False,
        )
        result = compile_capabilities(self.manifests, {"external.publish"}, [], builder_context)
        self.assertEqual(result.effective, set())
        self.assertIn("external.publish", result.removed["gate_not_attested"])

    def test_doctor_is_read_only_and_explainable(self):
        report = run_doctor(ROOT)
        self.assertEqual(report["status"], "ready")
        self.assertTrue(report["no_mutation"])
        self.assertEqual(report["compilation"]["effective"], ["local.draft", "local.read", "web.research"])
        self.assertNotIn("external.publish", report["compilation"]["effective"])

    def test_strict_config_preserves_last_good_and_rejected_candidate(self):
        valid = load_runtime_config(ROOT / "config" / "runtime-profile.json")
        with tempfile.TemporaryDirectory() as tmp:
            active = Path(tmp) / "runtime.json"
            store = StrictConfigStore(active)
            store.apply(valid)
            first = active.read_text()
            updated = dict(valid)
            updated["profile"] = "second"
            store.apply(updated)
            self.assertEqual(json.loads(store.last_good.read_text())["profile"], valid["profile"])
            bad = dict(updated)
            bad["unknown_security_field"] = True
            with self.assertRaises(ConfigError):
                store.apply(bad)
            self.assertEqual(active.read_text(), json.dumps(updated, indent=2, sort_keys=True) + "\n")
            self.assertEqual(len(list(store.rejected_dir.glob("candidate-*.json"))), 1)
            self.assertNotEqual(first, active.read_text())


if __name__ == "__main__":
    unittest.main()
