"""Florence-X adapter honors the Florence-X contract (build steps 2.11 and 2.12).

Always: adapter output validates against the pinned Florence-X JSON
Schemas (stdlib validator in ``_schema.py``).

When Florence-X is importable (the CI ``florence-x-contract`` job): the
output also validates against Florence-X's own Pydantic models, and the
pinned schemas must match the upstream checkout byte-for-byte.
"""

import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path

import _bootstrap
from _bootstrap import fixed_clock
from _schema import check as _check

from nurse_manager.actions import ActionBoundary
from nurse_manager.brief import BriefService
from nurse_manager.florence_adapter import (
    AdapterError,
    evidence_bundles,
    to_candidate_action,
    to_edena_decision,
    to_evidence_bundle,
)
from nurse_manager.sample import load_sample

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts" / "florence-x"
PINNED = {
    "candidate_action.schema.json": "97c728a00fe0917dd985ce2e2412bdf9499dea8246448f82db4887f494c46699",
    "edena_decision.schema.json": "1d68ae7b790231bb551c9bc202aba540c2d04625f86b5522d1407c5b6d2bc8b2",
}
OWNER = "Sample Manager"
WEEK, TODAY = "2026-09-28", "2026-09-30"

try:  # present only in the florence-x-contract CI job
    from florence_core.schemas import CandidateAction, EDENADecision, EvidenceBundle
    from florence_core.schemas import HumanReview, ToolCallRecord
except ImportError:  # pragma: no cover
    CandidateAction = EDENADecision = EvidenceBundle = HumanReview = ToolCallRecord = None

# Florence-X publishes no JSON Schema for EvidenceBundle, so these tables
# describe its fields for the offline check. They are not a copy of the
# contract: the CI job holds them equal to the Pydantic models' own fields.
_STR, _OPT = (str,), (str, type(None))
EVIDENCE_FIELDS = {
    "bundle_id": _STR, "workflow_run_id": _STR, "signal_id": _STR, "context_hash": _OPT,
    "model_used": _OPT, "model_version": _OPT, "prompt_template_version": _OPT,
    "agent_versions": (dict,), "tool_calls": (list,), "edena_decisions": (list,),
    "human_reviews": (list,), "final_action": _OPT, "source_citations": (list,),
    "signal_received_at": _OPT, "executed_at": _OPT, "reviewed_at": _OPT,
    "completed_at": _OPT, "overrides": (list,), "deviations_from_edena": (list,),
    "incident_flags": (list,), "outcome_feedback": _OPT, "created_at": _STR,
}
TOOL_CALL_FIELDS = {"tool_id": _STR, "action_id": _STR, "proposed": (bool,),
                    "executed": (bool,), "output_hash": _OPT, "error": _OPT}
REVIEW_FIELDS = {"review_id": _STR, "action_id": _STR, "decision_id": _STR,
                 "reviewer_role": _STR, "reviewer_ref": _STR, "outcome": _STR,
                 "edited_payload_hash": _OPT, "note": _OPT, "reviewed_at": _STR}


def _schema(name):
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


class _Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.ws, _ = load_sample(Path(self._tmp.name) / "ws", clock=fixed_clock())
        self.boundary = ActionBoundary(self.ws)
        briefs = BriefService(self.ws)
        draft = briefs.draft_weekly_brief(WEEK, TODAY)
        self.accepted = briefs.accept(draft.id, OWNER, draft.body_sha256)

    def tearDown(self):
        self.ws.close()
        self._tmp.cleanup()

    def actions(self):
        """One action for every decision and origin the manager core produces."""
        propose = self.boundary.propose
        rid = self.accepted.id
        return {
            "awaiting": propose("export_markdown", revision_id=rid, destination="brief.md",
                                purpose="Save my brief", proposed_by=OWNER),
            "assistant": propose("export_markdown", revision_id=rid, destination="a.md",
                                 purpose="Save the brief", origin="assistant",
                                 proposed_by="assistant:planning-partner"),
            "blocked": propose("send_email", revision_id=rid, destination="team-list",
                               purpose="Send it", proposed_by=OWNER),
            "scope": propose("export_markdown", revision_id=rid, destination="../x.md",
                             purpose="Save", proposed_by=OWNER),
        }

    def assertValid(self, obj, schema_name):
        schema = _schema(schema_name)
        self.assertEqual(_check(obj, schema, schema), "")


class AdapterTests(_Case):
    def test_every_action_maps_to_a_valid_candidate_action_and_decision(self):
        for label, action in self.actions().items():
            with self.subTest(action=label):
                self.assertValid(to_candidate_action(self.boundary, action.id),
                                 "candidate_action.schema.json")
                self.assertValid(to_edena_decision(self.boundary, action.id),
                                 "edena_decision.schema.json")

    def test_the_validator_rejects_what_florence_x_would_reject(self):
        good = to_candidate_action(self.boundary, self.actions()["awaiting"].id)
        schema = _schema("candidate_action.schema.json")
        for broken in (
            {**good, "payload": "raw text"},
            {**good, "action_type": "export_markdown"},
            {**good, "reversible": "yes"},
            {k: v for k, v in good.items() if k != "proposed_payload_hash"},
        ):
            with self.subTest(broken=sorted(set(broken) ^ set(good)) or "value"):
                self.assertNotEqual(_check(broken, schema, schema), "")

    def test_payload_travels_as_a_hash_never_as_content(self):
        action = self.actions()["awaiting"]
        candidate = to_candidate_action(self.boundary, action.id)
        self.assertEqual(candidate["proposed_payload_hash"], f"sha256:{self.accepted.body_sha256}")
        blob = json.dumps(candidate)
        self.assertNotIn("Weekly Manager Brief", blob)
        self.assertIn(self.accepted.id, candidate["evidence_refs"])
        self.assertEqual(candidate["evidence_refs"][1:], list(self.accepted.source_refs))

    def test_no_personal_names_cross_the_boundary(self):
        for label, action in self.actions().items():
            with self.subTest(action=label):
                blob = json.dumps([to_candidate_action(self.boundary, action.id),
                                   to_edena_decision(self.boundary, action.id)])
                self.assertNotIn(OWNER, blob)
        human = to_candidate_action(self.boundary, self.actions()["awaiting"].id)
        self.assertEqual(human["agent_id"], f"human:workspace-owner:{self.ws.info.id}")

    def test_decisions_and_tiers_map_faithfully(self):
        acts = self.actions()
        awaiting = to_edena_decision(self.boundary, acts["awaiting"].id)
        self.assertEqual((awaiting["decision"], awaiting["risk_tier"]), ("require_human", "yellow"))
        self.assertEqual(awaiting["required_human_role"], "nurse_manager")
        self.assertIn("approval_bound_to_payload_hash", awaiting["constraints"])
        blocked = to_edena_decision(self.boundary, acts["blocked"].id)
        self.assertEqual((blocked["decision"], blocked["risk_tier"]), ("deny", "red_blocked"))
        self.assertIn("MGR-EFFECT-BLOCKED", blocked["rationale"])
        self.assertEqual(blocked["constraints"], [])
        send = to_candidate_action(self.boundary, acts["blocked"].id)
        self.assertEqual((send["action_type"], send["external_boundary_crossed"],
                          send["reversible"]), ("send_message", True, False))
        export = to_candidate_action(self.boundary, acts["awaiting"].id)
        self.assertEqual((export["action_type"], export["external_boundary_crossed"],
                          export["reversible"]), ("write_record", False, True))

    def test_assistant_decisions_name_both_policies(self):
        decision = to_edena_decision(self.boundary, self.actions()["assistant"].id)
        self.assertRegex(decision["policy_pack_version"],
                         r"^nurse-manager-personal-profile@.+\+edena-gateway-policy@.+$")
        candidate = to_candidate_action(self.boundary, self.actions()["assistant"].id)
        self.assertEqual(candidate["agent_id"], "assistant:planning-partner")

    def test_decisions_name_the_policy_in_force_when_they_were_made(self):
        acts = self.actions()
        before = {label: to_edena_decision(self.boundary, a.id)["policy_pack_version"]
                  for label, a in acts.items()}
        profile = json.loads(self.boundary.profile_path.read_text(encoding="utf-8"))
        profile["version"] = "99.0.0"
        upgraded = Path(self._tmp.name) / "profile.json"
        upgraded.write_text(json.dumps(profile), encoding="utf-8")
        later = ActionBoundary(self.ws, profile_policy=upgraded)
        for label, action in acts.items():
            with self.subTest(action=label):
                self.assertNotIn("99.0.0", before[label])
                self.assertEqual(to_edena_decision(later, action.id)["policy_pack_version"],
                                 before[label])
                self.assertEqual(to_evidence_bundle(later, action.id)["edena_decisions"][0]
                                 ["policy_pack_version"], before[label])
        fresh = later.propose("export_markdown", revision_id=self.accepted.id,
                              destination="new.md", purpose="Save", proposed_by=OWNER)
        self.assertTrue(to_edena_decision(later, fresh.id)["policy_pack_version"]
                        .endswith("@99.0.0"))

    def test_a_decision_recorded_before_versions_were_kept_names_none(self):
        action = self.actions()["awaiting"]
        self.ws.store.conn.execute("DELETE FROM action_policy_versions WHERE action_id = ?",
                                   (action.id,))
        decision = to_edena_decision(self.boundary, action.id)
        self.assertIsNone(decision["policy_pack_version"])  # unknown, never guessed
        self.assertValid(decision, "edena_decision.schema.json")

    def test_unknown_effects_are_refused_not_guessed(self):
        action = self.boundary.propose("launch_rocket", revision_id=self.accepted.id,
                                       destination="x", purpose="?", proposed_by=OWNER)
        with self.assertRaises(AdapterError):
            to_candidate_action(self.boundary, action.id)
        # The decision (a denial) is still representable.
        self.assertEqual(to_edena_decision(self.boundary, action.id)["decision"], "deny")

    @unittest.skipIf(CandidateAction is None, "Florence-X is not installed (runs in the florence-x-contract CI job)")
    def test_florence_x_pydantic_models_accept_the_output(self):
        for label, action in self.actions().items():
            with self.subTest(action=label):
                CandidateAction.model_validate(to_candidate_action(self.boundary, action.id))
                EDENADecision.model_validate(to_edena_decision(self.boundary, action.id))


class EvidenceTests(_Case):
    """Receipts, approvals, and the event log as Florence-X EvidenceBundles (2.12)."""

    def lifecycle(self):
        """One action in every state the manager core can leave one in."""
        acts = self.actions()
        propose, rid = self.boundary.propose, self.accepted.id
        approve = lambda a: self.boundary.approve(  # noqa: E731
            a.id, OWNER, seen_sha256=a.payload_sha256, seen_destination=a.destination)
        out = {"awaiting": acts["awaiting"], "denied": acts["blocked"],
               "assistant": acts["assistant"]}
        approved = propose("export_markdown", revision_id=rid, destination="later.md",
                           purpose="Save it later", proposed_by=OWNER)
        approve(approved)
        out["approved"] = approved
        ran = propose("export_markdown", revision_id=rid, destination="ran.md",
                      purpose="Save it", proposed_by=OWNER)
        approve(ran)
        self.boundary.execute(ran.id, OWNER)
        out["succeeded"] = ran
        taken = propose("export_markdown", revision_id=rid, destination="taken.md",
                        purpose="Save it", proposed_by=OWNER)
        approve(taken)
        self.boundary.exports_dir.mkdir(parents=True, exist_ok=True)
        (self.boundary.exports_dir / "taken.md").write_text("someone else's file")
        self.boundary.execute(taken.id, OWNER)
        out["failed"] = taken
        stale = propose("export_markdown", revision_id=rid, destination="stale.md",
                        purpose="Save it", proposed_by=OWNER)
        approve(stale)
        self.ws.store.conn.execute("UPDATE approvals SET destination = 'elsewhere.md'"
                                   " WHERE action_id = ?", (stale.id,))
        with self.assertRaises(Exception):
            self.boundary.execute(stale.id, OWNER)
        out["stale"] = stale
        lost = propose("export_markdown", revision_id=rid, destination="lost.md",
                       purpose="Save it", proposed_by=OWNER)
        approve(lost)
        with self.ws.store.transaction():  # interrupted mid-effect, then restarted
            self.boundary._set_status(lost.id, "executing", OWNER, "execute")
        recovered = propose("export_markdown", revision_id=rid, destination="recovered.md",
                            purpose="Save it", proposed_by=OWNER)
        approve(recovered)
        (self.boundary.exports_dir / "recovered.md").write_text(  # written, then the crash
            self.boundary.briefs.render(self.accepted), encoding="utf-8")
        with self.ws.store.transaction():
            self.boundary._set_status(recovered.id, "executing", OWNER, "execute")
        self.boundary.reconcile()
        out["effect_unknown"] = lost
        out["recovered"] = recovered
        return {label: self.boundary.get(a.id) for label, a in out.items()}

    def assertShape(self, bundle):
        def fits(obj, fields, where):
            self.assertEqual(set(obj), set(fields), where)
            for key, types in fields.items():
                self.assertIsInstance(obj[key], types, f"{where}.{key}")
        fits(bundle, EVIDENCE_FIELDS, "bundle")
        for call in bundle["tool_calls"]:
            fits(call, TOOL_CALL_FIELDS, "tool_call")
        for review in bundle["human_reviews"]:
            fits(review, REVIEW_FIELDS, "review")
        for decision in bundle["edena_decisions"]:
            self.assertValid(decision, "edena_decision.schema.json")

    def test_every_state_maps_to_well_formed_evidence(self):
        for label, action in self.lifecycle().items():
            with self.subTest(state=label):
                self.assertShape(to_evidence_bundle(self.boundary, action.id))

    def test_what_happened_is_what_the_evidence_says(self):
        acts = self.lifecycle()
        get = lambda label: to_evidence_bundle(self.boundary, acts[label].id)  # noqa: E731

        denied = get("denied")
        self.assertEqual((denied["final_action"], denied["incident_flags"]),
                         ("blocked:deny", [f"edena_deny:{acts['denied'].id}"]))
        self.assertEqual((denied["tool_calls"], denied["human_reviews"]), ([], []))
        self.assertEqual(denied["completed_at"], denied["signal_received_at"])

        awaiting = get("awaiting")
        self.assertEqual((awaiting["final_action"], awaiting["completed_at"]),
                         ("awaiting_human_review", None))
        self.assertEqual(awaiting["edena_decisions"][0]["decision"], "require_human")

        approved = get("approved")
        self.assertEqual((approved["final_action"], approved["tool_calls"]),
                         ("awaiting_execution", []))
        (review,) = approved["human_reviews"]
        self.assertEqual((review["outcome"], review["reviewer_role"], review["decision_id"]),
                         ("approve", "nurse_manager", f"{acts['approved'].id}:decision"))
        self.assertEqual(approved["reviewed_at"], review["reviewed_at"])

        ran = get("succeeded")
        (call,) = ran["tool_calls"]
        on_disk = hashlib.sha256((self.boundary.exports_dir / "ran.md").read_bytes()).hexdigest()
        self.assertEqual((call["tool_id"], call["executed"], call["output_hash"], call["error"]),
                         ("export_markdown", True, f"sha256:{on_disk}", None))
        self.assertEqual(ran["final_action"], "write_record")
        self.assertTrue(ran["signal_received_at"] <= ran["reviewed_at"] <= ran["executed_at"]
                        <= ran["completed_at"])
        self.assertEqual((ran["deviations_from_edena"], ran["incident_flags"]), ([], []))
        self.assertEqual(ran["context_hash"], f"sha256:{self.accepted.body_sha256}")
        self.assertEqual(ran["source_citations"], [self.accepted.id, *self.accepted.source_refs])

        failed = get("failed")
        (call,) = failed["tool_calls"]
        self.assertEqual((call["executed"], call["output_hash"], call["error"]),
                         (False, None, "FileExistsError"))
        self.assertEqual(failed["final_action"], "failed:write_record")

        stale = get("stale")
        self.assertEqual((stale["final_action"], stale["incident_flags"], stale["tool_calls"]),
                         ("blocked:stale_approval", [f"stale_approval:{acts['stale'].id}"], []))
        self.assertIsNotNone(stale["completed_at"])

        recovered = get("recovered")  # confirmed after a restart: the digest still crosses
        (call,) = recovered["tool_calls"]
        on_disk = hashlib.sha256(
            (self.boundary.exports_dir / "recovered.md").read_bytes()).hexdigest()
        self.assertEqual((call["executed"], call["output_hash"], call["error"]),
                         (True, f"sha256:{on_disk}", None))
        self.assertEqual(recovered["final_action"], "write_record")
        # A receipt the previous release wrote, without the digest, still gives it.
        self.ws.store.conn.execute(
            "UPDATE receipts SET detail = 'confirmed after restart: file on disk matches the"
            " approved content' WHERE action_id = ?", (acts["recovered"].id,))
        (call,) = get("recovered")["tool_calls"]
        self.assertEqual((call["executed"], call["output_hash"]), (True, f"sha256:{on_disk}"))

        lost = get("effect_unknown")
        (call,) = lost["tool_calls"]
        self.assertEqual((call["executed"], call["error"]), (False, "effect_unknown"))
        self.assertEqual((lost["final_action"], lost["incident_flags"]),
                         ("effect_unknown:write_record", [f"effect_unknown:{acts['effect_unknown'].id}"]))

    def test_no_names_paths_or_content_cross_the_boundary(self):
        blob = json.dumps(evidence_bundles(self.boundary) + [
            to_evidence_bundle(self.boundary, a.id) for a in self.lifecycle().values()])
        self.assertNotIn(OWNER, blob)
        self.assertNotIn(str(self.boundary.exports_dir), blob)
        self.assertNotIn(self._tmp.name, blob)
        self.assertNotIn("Weekly Manager Brief", blob)

    def test_the_same_records_always_give_the_same_evidence(self):
        for label, action in self.lifecycle().items():
            with self.subTest(state=label):
                self.assertEqual(to_evidence_bundle(self.boundary, action.id),
                                 to_evidence_bundle(self.boundary, action.id))

    def test_unknown_effects_are_refused_and_left_out_of_the_workspace_list(self):
        action = self.boundary.propose("launch_rocket", revision_id=self.accepted.id,
                                       destination="x", purpose="?", proposed_by=OWNER)
        with self.assertRaises(AdapterError):
            to_evidence_bundle(self.boundary, action.id)
        self.assertNotIn(action.id, [b["edena_decisions"][0]["action_id"]
                                     for b in evidence_bundles(self.boundary)])

    @unittest.skipIf(EvidenceBundle is None, "Florence-X is not installed (runs in the florence-x-contract CI job)")
    def test_florence_x_pydantic_models_accept_the_evidence(self):
        for label, action in self.lifecycle().items():
            with self.subTest(state=label):
                bundle = to_evidence_bundle(self.boundary, action.id)
                EvidenceBundle.model_validate(bundle)

    @unittest.skipIf(EvidenceBundle is None, "Florence-X is not installed (runs in the florence-x-contract CI job)")
    def test_the_offline_field_tables_match_florence_x(self):
        for model, fields in ((EvidenceBundle, EVIDENCE_FIELDS), (ToolCallRecord, TOOL_CALL_FIELDS),
                              (HumanReview, REVIEW_FIELDS)):
            with self.subTest(model=model.__name__):
                self.assertEqual(set(model.model_fields), set(fields))


class PinnedSchemaTests(unittest.TestCase):
    def test_pinned_copies_are_unmodified(self):
        for name, digest in PINNED.items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((CONTRACTS / name).read_bytes()).hexdigest(), digest)

    @unittest.skipUnless(os.environ.get("FLORENCE_X_DIR"), "no upstream checkout to compare")
    def test_pinned_copies_match_the_upstream_checkout(self):
        upstream = Path(os.environ["FLORENCE_X_DIR"]) / "schemas"
        for name in PINNED:
            with self.subTest(file=name):
                self.assertEqual((CONTRACTS / name).read_bytes(), (upstream / name).read_bytes())


if __name__ == "__main__":
    unittest.main()
