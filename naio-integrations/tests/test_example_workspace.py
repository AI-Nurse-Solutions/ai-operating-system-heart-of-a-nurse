import json
import tempfile
import unittest
from pathlib import Path

import _bootstrap  # noqa: F401

from naio_integrations.deliverables import DRAFT_BANNER
from naio_integrations.orchestration import AdpieWorkflow
from naio_integrations.privacy import PrivacyScreen
from naio_integrations.workspace import (
    FIRST_RUN_CHOICES,
    ExampleWorkspace,
    WorkspaceError,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMITTED_ROOT = REPO_ROOT / "mission-control" / "example-workspace"

SPEC_FIRST_RUN_CHOICES = {
    "learning-plan",
    "structured-question",
    "project-one-pager",
    "lesson-plan",
    "executive-brief",
    "evidence-question",
    "research-question",
}


class ExampleWorkspaceBuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "workspace"
        self.workspace = ExampleWorkspace(self.root)
        self.manifest = self.workspace.build()

    def tearDown(self):
        self.tmp.cleanup()

    def test_every_json_record_is_labeled_synthetic(self):
        for path in self.root.rglob("*.json"):
            if path.name.endswith(".tmp"):
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            if path.parent.name == "project":
                self.assertTrue(payload["context"]["synthetic"], path)
            else:
                self.assertTrue(payload.get("synthetic"), path)

    def test_sample_project_is_a_genuine_completed_adpie_checkpoint(self):
        runtime = AdpieWorkflow(self.root / "project")
        state = runtime.state("sample-improvement-project")
        self.assertEqual(state["stage"], "complete")
        self.assertEqual(state["status"], "complete")
        self.assertTrue(state["authorization"]["approved"])
        self.assertIn("fictional", state["authorization"]["approver"].casefold())
        stages_recorded = set(state["stage_outputs"])
        self.assertEqual(
            stages_recorded,
            {"assess", "diagnose", "plan", "implement", "evaluate", "learn"},
        )

    def test_evidence_library_uses_the_five_spec_labels_correctly(self):
        library = json.loads(
            (self.root / "evidence" / "evidence-library.json").read_text(encoding="utf-8")
        )
        labels = {item["evidence_label"] for item in library["items"]}
        self.assertLessEqual(
            labels,
            {
                "verified_source",
                "local_policy",
                "user_provided_context",
                "ai_synthesis",
                "assumption_requiring_confirmation",
            },
        )
        self.assertIn("local_policy", labels)
        self.assertIn("ai_synthesis", labels)

    def test_sample_deliverable_completed_the_review_lifecycle(self):
        rendered = (
            self.root / "deliverables" / "sample-project-charter.md"
        ).read_text(encoding="utf-8")
        self.assertIn("SYNTHETIC EXAMPLE", rendered)
        self.assertIn("Approved by Example Reviewer (fictional)", rendered)
        self.assertNotIn(DRAFT_BANNER, rendered)

    def test_workspace_content_passes_the_privacy_screen(self):
        screen = PrivacyScreen()
        for path in sorted(self.root.rglob("*")):
            if path.is_file():
                findings = screen.analyze(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    [f.entity_type for f in findings], [], f"{path} tripped the screen"
                )

    def test_build_refuses_to_clobber_and_reset_rebuilds(self):
        with self.assertRaises(WorkspaceError):
            self.workspace.build()
        manifest = self.workspace.reset()
        self.assertTrue(manifest["synthetic"])
        self.assertTrue((self.root / "workspace.json").is_file())

    def test_remove_deletes_the_workspace(self):
        self.assertTrue(self.workspace.remove())
        self.assertFalse(self.root.exists())
        self.assertFalse(self.workspace.remove())


class FirstRunPathwayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = ExampleWorkspace(Path(self.tmp.name) / "ws")

    def tearDown(self):
        self.tmp.cleanup()

    def test_choices_match_the_onboarding_specification(self):
        self.assertEqual(set(FIRST_RUN_CHOICES), SPEC_FIRST_RUN_CHOICES)

    def test_every_choice_yields_a_real_artifact_in_one_call(self):
        for choice in FIRST_RUN_CHOICES:
            artifact = self.workspace.first_run(choice)
            self.assertEqual(artifact.status, "draft", choice)
            self.assertIn(DRAFT_BANNER, artifact.body_markdown, choice)
            self.assertGreaterEqual(artifact.body_markdown.count("## "), 3, choice)

    def test_answers_flow_into_the_artifact(self):
        artifact = self.workspace.first_run(
            "structured-question",
            answers={"the_question": "How does our fictional unit escalate a pump alarm?"},
        )
        self.assertIn("pump alarm", artifact.body_markdown)

    def test_unknown_choice_fails_closed(self):
        with self.assertRaises(WorkspaceError):
            self.workspace.first_run("autopilot-mode")


class CommittedWorkspaceTests(unittest.TestCase):
    """The committed example workspace must match a fresh deterministic build."""

    def test_committed_workspace_matches_fresh_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            fresh_root = Path(tmp) / "workspace"
            ExampleWorkspace(fresh_root).build()
            fresh_files = {
                p.relative_to(fresh_root).as_posix(): p.read_text(encoding="utf-8")
                for p in fresh_root.rglob("*")
                if p.is_file()
            }
        for name, content in fresh_files.items():
            committed = COMMITTED_ROOT / name
            self.assertTrue(committed.is_file(), name)
            self.assertEqual(
                committed.read_text(encoding="utf-8"), content, name
            )

    def test_committed_checksums_are_current(self):
        import hashlib

        checksum_file = COMMITTED_ROOT / "CHECKSUMS.sha256"
        self.assertTrue(checksum_file.is_file())
        for line in checksum_file.read_text(encoding="utf-8").splitlines():
            digest, _, name = line.partition("  ")
            actual = hashlib.sha256((COMMITTED_ROOT / name).read_bytes()).hexdigest()
            self.assertEqual(digest, actual, name)


if __name__ == "__main__":
    unittest.main()
