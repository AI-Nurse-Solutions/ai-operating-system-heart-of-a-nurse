"""Florence-X adapter (build step 2.11, ADR 0001 point 3).

Projects manager action records onto Florence-X's contract objects:
``CandidateAction`` and ``EDENADecision``. Florence-X consumes the output
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
"""

from __future__ import annotations

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
    policy = boundary._profile()
    version = f"{policy['policy_id']}@{policy['version']}"
    if action.origin == "assistant":
        version += f"+edena-gateway-policy@{boundary.edena.version}"
    return {
        "decision_id": f"{action.id}:decision",
        "action_id": action.id,
        "decision": decision,
        "risk_tier": _TIERS[action.tier],
        "required_human_role": REQUESTER_ROLE if decision == "require_human" else None,
        "constraints": list(_APPROVAL_CONSTRAINTS) if decision == "require_human" else [],
        "rationale": "reason codes: " + ", ".join(action.policy_reasons),
        "evidence_required": [],
        "policy_pack_version": version,
        "decided_at": _created_at(boundary, action.id),
        "expires_at": None,
    }
