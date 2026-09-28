"""Florence-X adapter honors the Florence-X contract (build step 2.11).

Always: adapter output validates against the pinned Florence-X JSON
Schemas (stdlib subset validator: types, required, enums, anyOf,
additionalProperties=false, date-time).

When Florence-X is importable (the CI ``florence-x-contract`` job): the
output also validates against Florence-X's own Pydantic models, and the
pinned schemas must match the upstream checkout byte-for-byte.
"""

import hashlib
import json
import os
import re
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

import _bootstrap
from _bootstrap import fixed_clock

from nurse_manager.actions import ActionBoundary
from nurse_manager.brief import BriefService
from nurse_manager.florence_adapter import (
    AdapterError,
    to_candidate_action,
    to_edena_decision,
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
    from florence_core.schemas import CandidateAction, EDENADecision
except ImportError:  # pragma: no cover
    CandidateAction = EDENADecision = None


def _check(value, schema, root, path="$"):
    """Minimal JSON Schema validator for the constructs these schemas use."""
    if "$ref" in schema:
        name = schema["$ref"].split("/")[-1]
        return _check(value, root["$defs"][name], root, path)
    if "anyOf" in schema:
        errors = [_check(value, option, root, path) for option in schema["anyOf"]]
        if all(errors):
            return f"{path}: matches no anyOf option ({errors})"
        return ""
    if "enum" in schema and value not in schema["enum"]:
        return f"{path}: {value!r} not in {schema['enum']}"
    kind = schema.get("type")
    checks = {
        "string": lambda v: isinstance(v, str),
        "boolean": lambda v: isinstance(v, bool),
        "array": lambda v: isinstance(v, list),
        "object": lambda v: isinstance(v, dict),
        "null": lambda v: v is None,
    }
    if kind and not checks[kind](value):
        return f"{path}: expected {kind}, got {type(value).__name__}"
    if schema.get("format") == "date-time":
        try:
            datetime.fromisoformat(value)
        except (TypeError, ValueError):
            return f"{path}: not a date-time"
    if kind == "array":
        for i, item in enumerate(value):
            err = _check(item, schema.get("items", {}), root, f"{path}[{i}]")
            if err:
                return err
    if kind == "object":
        props = schema.get("properties", {})
        missing = [k for k in schema.get("required", []) if k not in value]
        if missing:
            return f"{path}: missing {missing}"
        if schema.get("additionalProperties") is False:
            extra = sorted(set(value) - set(props))
            if extra:
                return f"{path}: unexpected {extra}"
        for key, sub in props.items():
            if key in value:
                err = _check(value[key], sub, root, f"{path}.{key}")
                if err:
                    return err
    return ""


def _schema(name):
    return json.loads((CONTRACTS / name).read_text(encoding="utf-8"))


class AdapterTests(unittest.TestCase):
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
