"""Weekly brief journey and the governed action boundary (G2 exit evidence).

G2: create → review → save → close → reopen → export; denied actions have
no effects. Plus the plan's verification list: approval bound to payload,
destination, actor, workspace, and revision; stale approval fails; retry
does not duplicate effects; uncertain effects stay effect-unknown.
"""

import hashlib
import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import _bootstrap
from _bootstrap import fixed_clock

from nurse_manager import cli
from nurse_manager.actions import (
    DEFAULT_PROFILE_POLICY,
    ActionBoundary,
    ActionError,
    EffectUncertain,
    StaleApproval,
)
from nurse_manager.brief import BRIEF_DRAFT_BANNER, BriefService, StaleRevision, compose_weekly_brief
from nurse_manager.sample import load_sample
from nurse_manager.services import CaptureRefused, ManagerError, ManagerWorkspace
from nurse_manager.views import mission_control

WEEK = "2026-09-28"
TODAY = "2026-09-30"
OWNER = "Sample Manager"


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.ws, _ = load_sample(self.tmp / "ws", clock=fixed_clock())
        self.briefs = BriefService(self.ws)

    def tearDown(self):
        self.ws.close()
        self._tmp.cleanup()

    def accepted_brief(self):
        draft = self.briefs.draft_weekly_brief(WEEK, TODAY)
        return self.briefs.accept(draft.id, OWNER, draft.body_sha256)

    def reopen(self):
        self.ws.close()
        self.ws = ManagerWorkspace(self.tmp / "ws", clock=fixed_clock("2026-10-01T09:00:00+00:00"))
        self.briefs = BriefService(self.ws)


class BriefTests(_Case):
    def test_composition_is_deterministic_for_fixed_records(self):
        first, refs_a = compose_weekly_brief(self.ws, WEEK, TODAY)
        second, refs_b = compose_weekly_brief(self.ws, WEEK, TODAY)
        self.assertEqual(first, second)
        self.assertEqual(refs_a, refs_b)

    def test_every_cited_record_exists_in_this_workspace(self):
        draft = self.briefs.draft_weekly_brief(WEEK, TODAY)
        db = self.ws.store.conn
        tables = {"prj": "projects", "tsk": "tasks", "dec": "decisions", "src": "sources"}
        self.assertTrue(draft.source_refs)
        for ref in draft.source_refs:
            with self.subTest(ref=ref):
                table = tables[ref.split("-")[0]]
                row = db.execute(
                    f"SELECT workspace_id FROM {table} WHERE id = ?", (ref,)
                ).fetchone()
                self.assertEqual(row[0], self.ws.info.id)
                self.assertIn(ref, draft.body_markdown)

    def test_a_draft_says_what_it_is_and_never_claims_ai(self):
        draft = self.briefs.draft_weekly_brief(WEEK, TODAY)
        text = self.briefs.render(draft)
        self.assertIn(BRIEF_DRAFT_BANNER, text)
        self.assertIn("SYNTHETIC EXAMPLE", text)
        self.assertNotIn("AI-generated", text)
        self.assertIn("no AI model was used", text)

    def test_create_review_save_close_reopen(self):
        accepted = self.accepted_brief()
        rendered = self.briefs.render(accepted)
        self.reopen()
        again = self.briefs.accepted(accepted.artifact_id)
        self.assertEqual(again.id, accepted.id)
        self.assertEqual(again.body_sha256, accepted.body_sha256)
        self.assertEqual(self.briefs.render(again), rendered)
        self.assertIn(f"Reviewed and accepted by {OWNER}", rendered)
        mc = mission_control(self.ws, today=TODAY, week_of=WEEK)
        self.assertEqual(mc["recent_accepted_outputs"]["items"][0]["id"], accepted.id)

    def test_acceptance_is_bound_to_the_text_that_was_reviewed(self):
        draft = self.briefs.draft_weekly_brief(WEEK, TODAY)
        with self.assertRaises(StaleRevision):
            self.briefs.accept(draft.id, OWNER, "0" * 64)
        with self.assertRaises(ManagerError):
            self.briefs.accept(draft.id, "Someone Else", draft.body_sha256)

    def test_an_older_draft_cannot_be_accepted_once_a_newer_exists(self):
        first = self.briefs.draft_weekly_brief(WEEK, TODAY)
        self.briefs.revise(first.artifact_id, first.body_markdown + "\nOne more line.\n", OWNER)
        with self.assertRaises(ManagerError):
            self.briefs.accept(first.id, OWNER, first.body_sha256)

    def test_editing_after_acceptance_starts_a_new_draft(self):
        accepted = self.accepted_brief()
        edited = self.briefs.revise(
            accepted.artifact_id, accepted.body_markdown + "\nAdded after review.\n", OWNER
        )
        self.assertEqual(edited.status, "draft")
        self.assertEqual(self.briefs.accepted(accepted.artifact_id).id, accepted.id)
        self.briefs.accept(edited.id, OWNER, edited.body_sha256)
        statuses = [r.status for r in self.briefs.history(accepted.artifact_id)]
        self.assertEqual(statuses, ["superseded", "accepted"])

    def test_edits_obey_the_same_capture_rules(self):
        draft = self.briefs.draft_weekly_brief(WEEK, TODAY)
        with self.assertRaises(CaptureRefused):
            self.briefs.revise(draft.artifact_id, draft.body_markdown + "\nCall 555-201-7788\n",
                               OWNER)


class ActionBoundaryTests(_Case):
    def boundary(self, **kwargs):
        return ActionBoundary(self.ws, **kwargs)

    def exports(self):
        root = self.tmp / "ws" / "exports"
        return sorted(p.name for p in root.iterdir()) if root.exists() else []

    def approved_export(self, boundary=None, name="brief.md"):
        boundary = boundary or self.boundary()
        accepted = self.accepted_brief()
        action = boundary.propose("export_markdown", revision_id=accepted.id,
                                  destination=name, purpose="Save my brief", proposed_by=OWNER)
        self.assertEqual(action.status, "awaiting_approval")
        self.assertEqual(action.tier, "yellow")
        boundary.approve(action.id, OWNER, seen_sha256=action.payload_sha256,
                         seen_destination=name)
        return boundary, action, accepted

    def test_export_journey_writes_exactly_the_accepted_text(self):
        boundary, action, accepted = self.approved_export()
        receipt = boundary.execute(action.id, OWNER)
        self.assertEqual(receipt["outcome"], "succeeded")
        written = (self.tmp / "ws" / "exports" / "brief.md").read_text(encoding="utf-8")
        self.assertEqual(written, self.briefs.render(accepted))
        self.assertIn(hashlib.sha256(written.encode()).hexdigest(), receipt["detail"])

    def test_retry_never_duplicates_the_effect(self):
        boundary, action, _ = self.approved_export()
        first = boundary.execute(action.id, OWNER)
        second = boundary.execute(action.id, OWNER)
        self.assertEqual(first, second)
        receipts = self.ws.store.conn.execute(
            "SELECT count(*) FROM receipts WHERE action_id = ?", (action.id,)
        ).fetchone()[0]
        self.assertEqual(receipts, 1)
        self.assertEqual(self.exports(), ["brief.md"])

    def test_approval_survives_restart(self):
        _, action, _ = self.approved_export()
        self.reopen()
        self.assertEqual(self.boundary().execute(action.id, OWNER)["outcome"], "succeeded")

    def test_denied_actions_have_no_effects(self):
        boundary = self.boundary()
        accepted = self.accepted_brief()
        draft = self.briefs.revise(accepted.artifact_id, accepted.body_markdown + "\nx\n", OWNER)
        cases = [
            ("export_markdown", draft.id, "brief.md", "MGR-NOT-ACCEPTED", "yellow"),
            ("send_email", accepted.id, "team@list", "MGR-EFFECT-BLOCKED", "red"),
            ("launch_rocket", accepted.id, "x.md", "MGR-EFFECT-UNKNOWN", "red"),
            ("export_markdown", accepted.id, "../escape.md", "MGR-DESTINATION-SCOPE", "yellow"),
            ("export_markdown", accepted.id, "/tmp/escape.md", "MGR-DESTINATION-SCOPE", "yellow"),
            ("export_markdown", accepted.id, "sub/escape.md", "MGR-DESTINATION-SCOPE", "yellow"),
            ("export_markdown", accepted.id, ".hidden.md", "MGR-DESTINATION-SCOPE", "yellow"),
            ("export_markdown", accepted.id, "brief.exe", "MGR-DESTINATION-SCOPE", "yellow"),
        ]
        for effect, revision_id, destination, reason, tier in cases:
            with self.subTest(effect=effect, destination=destination):
                action = boundary.propose(effect, revision_id=revision_id,
                                          destination=destination, purpose="try",
                                          proposed_by=OWNER)
                self.assertEqual(action.status, "denied")
                self.assertEqual(action.policy_reasons, (reason,))
                self.assertEqual(action.tier, tier)
                with self.assertRaises(ActionError):
                    boundary.approve(action.id, OWNER, seen_sha256=action.payload_sha256,
                                     seen_destination=destination)
                with self.assertRaises(ActionError):
                    boundary.execute(action.id, OWNER)
        self.assertEqual(self.exports(), [])
        self.assertFalse((self.tmp / "escape.md").exists())

    def test_approval_must_match_what_was_proposed(self):
        boundary = self.boundary()
        accepted = self.accepted_brief()
        action = boundary.propose("export_markdown", revision_id=accepted.id,
                                  destination="brief.md", purpose="Save", proposed_by=OWNER)
        with self.assertRaises(StaleApproval):
            boundary.approve(action.id, OWNER, seen_sha256="f" * 64, seen_destination="brief.md")
        with self.assertRaises(StaleApproval):
            boundary.approve(action.id, OWNER, seen_sha256=action.payload_sha256,
                             seen_destination="other.md")
        with self.assertRaises(ActionError):
            boundary.approve(action.id, "Someone Else", seen_sha256=action.payload_sha256,
                             seen_destination="brief.md")

    def test_approval_goes_stale_when_a_newer_revision_is_accepted(self):
        boundary, action, accepted = self.approved_export()
        edited = self.briefs.revise(accepted.artifact_id, accepted.body_markdown + "\nz\n", OWNER)
        self.briefs.accept(edited.id, OWNER, edited.body_sha256)
        with self.assertRaises(StaleApproval):
            boundary.execute(action.id, OWNER)
        self.assertEqual(boundary.get(action.id).status, "stale")
        self.assertEqual(self.exports(), [])

    def test_policy_change_between_approval_and_execution_is_seen(self):
        policy = json.loads(DEFAULT_PROFILE_POLICY.read_text(encoding="utf-8"))
        path = self.tmp / "policy.json"
        path.write_text(json.dumps(policy), encoding="utf-8")
        boundary, action, _ = self.approved_export(self.boundary(profile_policy=path))
        policy["blocked_effects"]["export_markdown"] = "Exports paused by the steward."
        del policy["effects"]["export_markdown"]
        path.write_text(json.dumps(policy), encoding="utf-8")
        with self.assertRaises(StaleApproval):
            boundary.execute(action.id, OWNER)
        self.assertEqual(self.exports(), [])

    def test_an_existing_different_file_is_never_overwritten(self):
        boundary, action, _ = self.approved_export()
        target = self.tmp / "ws" / "exports" / "brief.md"
        target.parent.mkdir(parents=True)
        target.write_text("earlier work", encoding="utf-8")
        receipt = boundary.execute(action.id, OWNER)
        self.assertEqual(receipt["outcome"], "failed")
        self.assertEqual(target.read_text(encoding="utf-8"), "earlier work")

    def test_uncertain_effect_is_recorded_and_not_retried(self):
        def uncertain(path, text):
            raise EffectUncertain("disk went away mid-write")

        boundary, action, _ = self.approved_export(
            self.boundary(handlers={"export_markdown": uncertain})
        )
        receipt = boundary.execute(action.id, OWNER)
        self.assertEqual(receipt["outcome"], "effect_unknown")
        with self.assertRaises(ActionError):
            boundary.execute(action.id, OWNER)

    def test_interrupted_execution_is_verified_on_restart_never_rerun(self):
        _, action, _ = self.approved_export()
        self.ws.store.conn.execute(
            "UPDATE actions SET status = 'executing' WHERE id = ?", (action.id,)
        )
        self.reopen()
        settled = self.boundary().reconcile()
        self.assertEqual([s["outcome"] for s in settled], ["effect_unknown"])
        self.assertEqual(self.exports(), [])

    def test_interrupted_execution_confirmed_by_content_hash(self):
        boundary, action, accepted = self.approved_export()
        (self.tmp / "ws" / "exports").mkdir()
        (self.tmp / "ws" / "exports" / "brief.md").write_text(
            self.briefs.render(accepted), encoding="utf-8"
        )
        self.ws.store.conn.execute(
            "UPDATE actions SET status = 'executing' WHERE id = ?", (action.id,)
        )
        settled = boundary.reconcile()
        self.assertEqual([s["outcome"] for s in settled], ["succeeded"])


class AssistantProposalTests(_Case):
    def test_assistant_may_recommend_and_only_the_manager_approves(self):
        boundary = ActionBoundary(self.ws)
        accepted = self.accepted_brief()
        action = boundary.propose("export_markdown", revision_id=accepted.id,
                                  destination="brief.md", purpose="Save the brief",
                                  proposed_by="assistant:planning-partner", origin="assistant")
        self.assertEqual(action.status, "awaiting_approval")
        with self.assertRaises(ActionError):
            boundary.approve(action.id, "assistant:planning-partner",
                             seen_sha256=action.payload_sha256, seen_destination="brief.md")
        with self.assertRaises(ActionError):
            boundary.execute(action.id, "assistant:planning-partner")

    def test_assistant_cannot_borrow_the_managers_identity(self):
        accepted = self.accepted_brief()
        with self.assertRaises(ActionError):
            ActionBoundary(self.ws).propose(
                "export_markdown", revision_id=accepted.id, destination="brief.md",
                purpose="Save", proposed_by=OWNER, origin="assistant",
            )

    def test_the_authoritative_edena_policy_still_decides_for_assistants(self):
        # Ask EDENA for a side-effecting mode in a personal tenant: the
        # gateway policy has no tier that grants it without an org context.
        policy = json.loads(DEFAULT_PROFILE_POLICY.read_text(encoding="utf-8"))
        policy["assistant_evaluation"]["action_mode"] = "act_with_approval"
        path = self.tmp / "policy.json"
        path.write_text(json.dumps(policy), encoding="utf-8")
        accepted = self.accepted_brief()
        action = ActionBoundary(self.ws, profile_policy=path).propose(
            "export_markdown", revision_id=accepted.id, destination="brief.md",
            purpose="Save", proposed_by="assistant:planning-partner", origin="assistant",
        )
        self.assertEqual(action.status, "denied")
        self.assertTrue(all(code.startswith("EDENA-") for code in action.policy_reasons))


class CliJourneyTests(unittest.TestCase):
    def run_cli(self, *argv):
        """Run one command; return (exit code, parsed envelope)."""
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = cli.main([str(a) for a in argv])
        envelope = json.loads(buf.getvalue())
        self.assertEqual(envelope["contract"], cli.CONTRACT)
        self.assertEqual(envelope["command"], str(argv[0]))
        self.assertEqual(envelope["ok"], code == 0)
        return code, envelope

    def data(self, *argv):
        code, envelope = self.run_cli(*argv)
        self.assertEqual(code, 0, envelope)
        return envelope["data"]

    def test_full_manager_journey_through_the_headless_surface(self):
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp)
        ws = tmp / "ws"
        self.data("sample", ws)
        mc = self.data("mission", ws, "--today", TODAY, "--week", WEEK)
        self.assertEqual(len(mc["priorities"]["items"]), 3)
        draft = self.data("brief", ws, "--week", WEEK, "--today", TODAY)
        shown = self.data("show", ws, "--revision", draft["id"])
        self.assertIn("DRAFT", shown["markdown"])
        self.assertEqual(shown["revision"], draft)
        accepted = self.data("accept", ws, "--revision", draft["id"], "--reviewer", OWNER,
                             "--sha", draft["sha256"])
        self.assertEqual(accepted["status"], "accepted")
        action = self.data("export", ws, "--revision", draft["id"], "--file", "week.md",
                           "--by", OWNER)
        self.assertEqual(action["status"], "awaiting_approval")
        self.data("approve", ws, "--action", action["id"], "--approver", OWNER,
                  "--sha", action["payload_sha256"], "--destination", "week.md")
        receipt = self.data("run", ws, "--action", action["id"], "--actor", OWNER)
        self.assertEqual(receipt["outcome"], "succeeded")
        self.assertTrue((ws / "exports" / "week.md").is_file())
        code, err = self.run_cli("accept", ws, "--revision", draft["id"], "--reviewer", OWNER,
                                 "--sha", draft["sha256"])
        self.assertEqual(code, 2)
        self.assertEqual(err["error"]["type"], "ManagerError")
        self.assertNotIn("data", err)


if __name__ == "__main__":
    unittest.main()
