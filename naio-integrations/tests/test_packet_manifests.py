import copy
import hashlib
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.packets import (
    PacketCatalog,
    PacketIntegrityError,
    compute_checksum,
    render_manifest,
    verify_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_ROOT = REPO_ROOT / "mission-control" / "packets"

SPEC_ROLES = {
    "pre-licensure-student",
    "staff-nurse",
    "leader",
    "educator",
    "licensed-clinician",
}

SPEC_ROLE_MODULES = {
    "pre-licensure-student": {
        "theory-to-practice-bridge",
        "clinical-reasoning-cases",
        "clinical-day-planner",
        "skills-competency-passport",
        "five-minute-debrief",
        "nclex-and-study-templates",
    },
    "staff-nurse": {
        "workflow-friction-log",
        "evidence-question-queue",
        "quality-project-launchpad",
        "certification-clinical-ladder-plan",
        "professional-portfolio",
    },
    "leader": {
        "strategy-and-portfolio-map",
        "decision-room",
        "operational-metric-dictionary",
        "ai-governance-register",
        "executive-communication-templates",
    },
    "educator": {
        "curriculum-builder",
        "simulation-studio",
        "competency-and-observation-tools",
        "feedback-coach",
        "deidentified-cohort-dashboard",
    },
    "licensed-clinician": {
        "evidence-to-practice-workspace",
        "guideline-comparison",
        "clinical-innovation-toolkit",
        "research-protocol-workspace",
        "research-governance-gates",
    },
}


class PacketCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = PacketCatalog()
        cls.manifests = cls.catalog.build_all()

    def test_catalog_covers_the_five_spec_roles(self):
        self.assertEqual(set(self.catalog.roles()), SPEC_ROLES)

    def test_every_packet_embeds_the_shared_core(self):
        for role, manifest in self.manifests.items():
            for module in (
                "mission-control-core",
                "edena-guardrails",
                "data-boundary-notice",
                "example-workspace-synthetic",
                "starter-agents-tools-disabled",
            ):
                self.assertIn(module, manifest["role_modules"], f"{role}: {module}")

    def test_role_modules_match_the_specification(self):
        for role, expected in SPEC_ROLE_MODULES.items():
            modules = set(self.manifests[role]["role_modules"])
            self.assertTrue(
                expected <= modules,
                f"{role} missing {expected - modules}",
            )

    def test_manifests_are_deterministic(self):
        again = PacketCatalog().build_all()
        for role in SPEC_ROLES:
            self.assertEqual(
                render_manifest(self.manifests[role]),
                render_manifest(again[role]),
                role,
            )

    def test_every_manifest_passes_verification(self):
        for role, manifest in self.manifests.items():
            verify_manifest(manifest)
            self.assertEqual(
                manifest["integrity_checksum"], compute_checksum(manifest), role
            )

    def test_unknown_role_fails_closed(self):
        with self.assertRaises(PacketIntegrityError):
            self.catalog.build_manifest("shadow-admin")


class ManifestVerificationTests(unittest.TestCase):
    def setUp(self):
        self.manifest = PacketCatalog().build_manifest("staff-nurse")

    def reseal(self, manifest):
        manifest["integrity_checksum"] = compute_checksum(manifest)
        return manifest

    def test_tampered_manifest_fails_checksum(self):
        tampered = copy.deepcopy(self.manifest)
        tampered["packet_version"] = "9.9.9"
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(tampered)

    def test_default_permissions_must_start_empty(self):
        unsafe = self.reseal(
            {**copy.deepcopy(self.manifest), "default_permissions": ["email_send"]}
        )
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(unsafe)

    def test_integrations_must_be_off_by_default(self):
        unsafe = self.reseal(
            {**copy.deepcopy(self.manifest), "integrations_enabled_by_default": True}
        )
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(unsafe)

    def test_personal_edition_must_prohibit_d3_and_d4(self):
        unsafe = self.reseal(
            {**copy.deepcopy(self.manifest), "prohibited_data_classes": ["D4"]}
        )
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(unsafe)

    def test_starter_agents_must_ship_tools_disabled_and_propose_only(self):
        armed = copy.deepcopy(self.manifest)
        armed["default_agents"][0]["tools_enabled"] = True
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(self.reseal(armed))
        executing = copy.deepcopy(self.manifest)
        executing["default_agents"][0]["actions_may_execute"] = ["send_email"]
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(self.reseal(executing))

    def test_missing_shared_core_module_fails(self):
        stripped = copy.deepcopy(self.manifest)
        stripped["role_modules"] = [
            m for m in stripped["role_modules"] if m != "edena-guardrails"
        ]
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(self.reseal(stripped))

    def test_institutional_approval_must_be_structurally_false(self):
        granted = copy.deepcopy(self.manifest)
        granted["governance"]["institutional_approval_granted"] = True
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(self.reseal(granted))
        missing = copy.deepcopy(self.manifest)
        del missing["governance"]["institutional_approval_granted"]
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(self.reseal(missing))

    def test_governance_defaults_are_green_and_private(self):
        escalated = copy.deepcopy(self.manifest)
        escalated["governance"]["default_risk_tier"] = "orange"
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(self.reseal(escalated))
        exposed = copy.deepcopy(self.manifest)
        exposed["governance"]["default_data_zone"] = "institutional"
        with self.assertRaises(PacketIntegrityError):
            verify_manifest(self.reseal(exposed))


class CommittedArtifactTests(unittest.TestCase):
    """The committed manifests must exactly match a fresh rebuild."""

    def test_committed_manifests_match_fresh_build(self):
        manifests = PacketCatalog().build_all()
        for role, manifest in manifests.items():
            committed = COMMITTED_ROOT / role / "manifest.json"
            self.assertTrue(committed.is_file(), role)
            self.assertEqual(
                committed.read_text(encoding="utf-8"), render_manifest(manifest), role
            )

    def test_committed_checksums_cover_every_manifest(self):
        checksum_file = COMMITTED_ROOT / "CHECKSUMS.sha256"
        self.assertTrue(checksum_file.is_file())
        entries = {}
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            entries[name] = digest
        for role in SPEC_ROLES:
            name = f"{role}/manifest.json"
            self.assertIn(name, entries)
            actual = hashlib.sha256((COMMITTED_ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(entries[name], actual, name)

    def test_committed_manifests_verify_after_json_round_trip(self):
        import json

        for role in SPEC_ROLES:
            manifest = json.loads(
                (COMMITTED_ROOT / role / "manifest.json").read_text(encoding="utf-8")
            )
            verify_manifest(manifest)


if __name__ == "__main__":
    unittest.main()
