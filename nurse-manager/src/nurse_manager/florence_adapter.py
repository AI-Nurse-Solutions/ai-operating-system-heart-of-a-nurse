"""Florence-X adapter (build steps 2.11 and 2.12, ADR 0001 point 3).

Projects manager action records onto Florence-X's contract objects:
``CandidateAction`` and ``EDENADecision`` (2.11), and each action's
approval, receipts, and event-log entries onto an ``EvidenceBundle`` (2.12). Florence-X consumes the output
as plain JSON-compatible dicts, so this module needs no Pydantic, and
neither schema is forked or redefined here. The contract is checked in
tests against the published JSON Schemas and, when Florence-X is
installed, against its own Pydantic models.

Rules (docs/02-contract-map.md):

* The payload travels as a hash, never as content.
* No personal names cross the boundary. Florence-X references are opaque:
  a human manager becomes ``human:workspace-owner:<workspace id>``.
* Unknown effects and unknown decisions raise an error; nothing is
  guessed into a Florence-X enum.
* The manager core keeps only three decisions (allow, require approval,
  deny), so it never emits contain/stop/throttle/escalate.
* Evidence follows Florence-X's own runtime conventions: a denial ends as
  ``blocked:deny`` with an ``edena_deny:<action>`` incident flag, an
  executed effect is a ``ToolCallRecord``, and an approval is a
  ``HumanReview``. Errors cross as the exception type only, since their
  text can carry file paths (and so a user name).
"""

from __future__ import annotations

import re
from typing import Any

from .actions import ActionBoundary, ActionRecord

CONTRACT_SOURCE = "AI-Nurse-Solutions/florence-x@09675bf61062534e21e1e4aded2f6a14e48f6b8e"
REQUESTER_ROLE = "nurse_manager"


class AdapterError(ValueError):
    """A manager record cannot be expressed faithfully in the Florence-X contract."""


# effect -> (ActionType, reversible, external_boundary_crossed)
_EFFECTS: dict[str, tuple[str, bool, bool]] = {
    # Writes a new file inside the workspace; never overwrites, so deleting it undoes it.
    "export_markdown": ("write_record", True, False),
    # Blocked in the Personal profile; mapped so denials remain representable.
    "send_email": ("send_message", False, True),
    "post_message": ("send_message", False, True),
    "publish": ("call_api", False, True),
    "upload": ("call_api", False, True),
    "delete_external": ("call_api", False, True),
}

# Manager presentation tier -> Florence-X RiskTier. Manager "red" means
# blocked in this profile, which is Florence-X's red_blocked, not red.
_TIERS = {"green": "green", "yellow": "yellow", "red": "red_blocked"}

# Manager decision -> Florence-X EdenaDecisionType.
_DECISIONS = {"allow": "allow", "require_approval": "require_human", "deny": "deny"}

# Personal Manager workspaces admit D0/D1 only; a brief mixes both, so the
# conservative (higher) classification is used.
_DATA_CLASSIFICATION = "internal"

_APPROVAL_CONSTRAINTS = [
    "approval_bound_to_payload_hash",
    "approval_bound_to_destination",
    "approval_bound_to_revision",
    "recheck_policy_and_approval_before_execute",
]


def _agent_ref(boundary: ActionBoundary, action: ActionRecord) -> str:
    if action.origin == "human":
        return f"human:workspace-owner:{boundary.ws.info.id}"
    if action.origin == "assistant":
        if not action.proposed_by.startswith("assistant:"):
            raise AdapterError("assistant ids must be opaque 'assistant:<role>' references")
        return action.proposed_by
    raise AdapterError(f"unknown origin: {action.origin}")


def _created_at(boundary: ActionBoundary, action_id: str) -> str:
    return boundary.ws.store.conn.execute(
        "SELECT created_at FROM actions WHERE id = ?", (action_id,)
    ).fetchone()["created_at"]


def to_candidate_action(boundary: ActionBoundary, action_id: str) -> dict[str, Any]:
    action = boundary.get(action_id)
    if action.effect not in _EFFECTS:
        raise AdapterError(f"no Florence-X action type is defined for effect '{action.effect}'")
    action_type, reversible, external = _EFFECTS[action.effect]
    if action.tier not in _TIERS:
        raise AdapterError(f"unknown tier: {action.tier}")
    evidence: list[str] = []
    artifact_ref = "none"
    if action.artifact_revision_id:
        revision = boundary.briefs.revision(action.artifact_revision_id)
        evidence = [revision.id, *revision.source_refs]
        artifact_ref = revision.artifact_id
    return {
        "action_id": action.id,
        "workflow_run_id": f"nurse-manager:{boundary.ws.info.id}:{artifact_ref}",
        "agent_id": _agent_ref(boundary, action),
        "requester_role": REQUESTER_ROLE,
        "action_type": action_type,
        "intended_target": f"workspace-exports:{action.destination}"
        if action.effect == "export_markdown" else f"{action.effect}:{action.destination}",
        "tool_requested": None,
        "data_classification": _DATA_CLASSIFICATION,
        "reversible": reversible,
        "external_boundary_crossed": external,
        "clinical_impact": None,
        "financial_impact": None,
        "legal_or_compliance_impact": None,
        "proposed_payload_hash": f"sha256:{action.payload_sha256}" if action.payload_sha256 else "none",
        "evidence_refs": evidence,
        "risk_hint": _TIERS[action.tier],
        "blast_radius_estimate": action.expected_effect,
        "created_at": _created_at(boundary, action.id),
    }


def to_edena_decision(boundary: ActionBoundary, action_id: str) -> dict[str, Any]:
    action = boundary.get(action_id)
    if action.policy_decision not in _DECISIONS:
        raise AdapterError(f"unknown decision: {action.policy_decision}")
    decision = _DECISIONS[action.policy_decision]
    return {
        "decision_id": f"{action.id}:decision",
        "action_id": action.id,
        "decision": decision,
        "risk_tier": _TIERS[action.tier],
        "required_human_role": REQUESTER_ROLE if decision == "require_human" else None,
        "constraints": list(_APPROVAL_CONSTRAINTS) if decision == "require_human" else [],
        "rationale": "reason codes: " + ", ".join(action.policy_reasons),
        "evidence_required": [],
        # As recorded when the action was decided, never today's policy.
        "policy_pack_version": boundary.policy_version(action.id),
        "decided_at": _created_at(boundary, action.id),
        "expires_at": None,
    }


# Where each action stands, as the ``final_action`` of its evidence. The
# first two follow Florence-X's runtime; the rest are the manager's own
# states, named so none can be mistaken for a completed effect.
_FINAL = {
    "denied": "blocked:deny",
    "awaiting_approval": "awaiting_human_review",
    "approved": "awaiting_execution",
    "executing": "executing",
    "stale": "blocked:stale_approval",
}
_OUTPUT_SHA = re.compile(r"sha256 ([0-9a-f]{64})")


def _events(boundary: ActionBoundary, action_id: str) -> list[Any]:
    return list(boundary.ws.store.conn.execute(
        "SELECT * FROM event_log WHERE record_type = 'action' AND record_id = ? ORDER BY seq",
        (action_id,)))


def to_evidence_bundle(boundary: ActionBoundary, action_id: str) -> dict[str, Any]:
    """The Florence-X ``EvidenceBundle`` for one action: its decision, the
    manager's approval, what ran and with what outcome, and when."""
    action = boundary.get(action_id)
    if action.effect not in _EFFECTS:
        raise AdapterError(f"no Florence-X action type is defined for effect '{action.effect}'")
    action_type = _EFFECTS[action.effect][0]
    conn = boundary.ws.store.conn
    created = _created_at(boundary, action.id)
    owner_ref = f"human:workspace-owner:{boundary.ws.info.id}"
    decision = to_edena_decision(boundary, action.id)

    approval = conn.execute("SELECT * FROM approvals WHERE action_id = ?",
                            (action.id,)).fetchone()
    reviews = []
    if approval is not None:
        if approval["approver"] != boundary.ws.info.owner:
            raise AdapterError("only the workspace owner approves; this approval is not theirs")
        reviews.append({
            "review_id": approval["id"],
            "action_id": action.id,
            "decision_id": decision["decision_id"],
            "reviewer_role": REQUESTER_ROLE,
            "reviewer_ref": owner_ref,
            "outcome": "approve",
            "edited_payload_hash": None,
            "note": None,
            "reviewed_at": approval["approved_at"],
        })

    receipt = conn.execute(
        "SELECT * FROM receipts WHERE action_id = ? ORDER BY recorded_at DESC, rowid DESC LIMIT 1",
        (action.id,)).fetchone()
    events = _events(boundary, action.id)
    executed_at = next((e["at"] for e in events if e["kind"] == "execute"), None)
    tool_calls, flags, deviations = [], [], []
    if receipt is not None:
        found = _OUTPUT_SHA.search(receipt["detail"])
        tool_calls.append({
            "tool_id": action.effect,
            "action_id": action.id,
            "proposed": True,
            "executed": receipt["outcome"] == "succeeded",
            "output_hash": f"sha256:{found.group(1)}"
            if receipt["outcome"] == "succeeded" and found else None,
            # The type or state only: a message can name a path, and a path a person.
            "error": None if receipt["outcome"] == "succeeded" else
            (receipt["outcome"] if receipt["outcome"] == "effect_unknown"
             else receipt["detail"].split(":", 1)[0]),
        })
        if action.policy_decision == "deny":
            deviations.append("an effect ran although the policy denied it")
        if action.policy_decision == "require_approval" and approval is None:
            deviations.append("an effect ran without the approval the policy required")

    status = action.status
    if status == "denied":
        flags.append(f"edena_deny:{action.id}")
    elif status == "stale":
        flags.append(f"stale_approval:{action.id}")
    elif status == "effect_unknown":
        flags.append(f"effect_unknown:{action.id}")
    final = _FINAL.get(status) or {
        "succeeded": action_type,
        "failed": f"failed:{action_type}",
        "effect_unknown": f"effect_unknown:{action_type}",
    }[status]

    evidence: list[str] = []
    artifact_ref = "none"
    if action.artifact_revision_id:
        revision = boundary.briefs.revision(action.artifact_revision_id)
        evidence = [revision.id, *revision.source_refs]
        artifact_ref = revision.artifact_id
    completed = (receipt["recorded_at"] if receipt is not None
                 else created if status == "denied"
                 else events[-1]["at"] if status == "stale" and events else None)
    return {
        "bundle_id": f"{action.id}:evidence",
        "workflow_run_id": f"nurse-manager:{boundary.ws.info.id}:{artifact_ref}",
        "signal_id": f"{action.id}:proposal",
        "context_hash": f"sha256:{action.payload_sha256}" if action.payload_sha256 else None,
        "model_used": None,
        "model_version": None,
        "prompt_template_version": None,
        "agent_versions": {},
        "tool_calls": tool_calls,
        "edena_decisions": [decision],
        "human_reviews": reviews,
        "final_action": final,
        "source_citations": list(dict.fromkeys(evidence)),
        "signal_received_at": created,
        "executed_at": executed_at,
        "reviewed_at": approval["approved_at"] if approval is not None else None,
        "completed_at": completed,
        "overrides": [],
        "deviations_from_edena": deviations,
        "incident_flags": flags,
        "outcome_feedback": None,
        # As of the last thing that happened to the action, so the same
        # records always give the same bundle.
        "created_at": events[-1]["at"] if events else created,
    }


def evidence_bundles(boundary: ActionBoundary) -> list[dict[str, Any]]:
    """Evidence for every action in the workspace whose effect Florence-X can name."""
    return [to_evidence_bundle(boundary, row["id"]) for row in boundary.ws.store.conn.execute(
        "SELECT id, effect FROM actions WHERE workspace_id = ? ORDER BY created_at, id",
        (boundary.ws.info.id,)) if row["effect"] in _EFFECTS]
