"""Governed action boundary (NM-006).

Implements the plan's governed action lifecycle for the local workspace:

1. Capture under the workspace's data rules (``services``).
2. Local access and data checks before anything else.
3. (Optional) an assistant proposes — evaluated by the authoritative
   EDENA engine at ``recommend`` mode: agents propose, humans judge.
4. Record the proposal: effect, purpose, payload hash, destination,
   cost limit, expected effect.
5. Evaluate the proposal against the Personal Manager effect table.
6. Collect human approval bound to the exact payload, destination,
   actor, workspace, and revision.
7. Immediately before acting, recheck policy and approval; any change
   makes the approval stale and nothing happens.
8. Record a receipt, a failure, or an effect-unknown state.

Denied and stale actions have no effects. A succeeded action is never
executed twice. An interrupted execution is reconciled on restart by
verifying the effect, never by blindly retrying it.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ._naio import (
    ActionMode,
    Actor,
    DataClass,
    DataZone,
    Decision,
    EdenaPolicyEngine,
    GatewayRequest,
    edena_engine,
    RiskTier,
)
from . import resources
from .brief import BriefService
from .services import ManagerError, ManagerWorkspace
from .store import new_id

DEFAULT_PROFILE_POLICY = resources.manager_root() / "config" / "manager-profile-policy.json"


class ActionError(ManagerError):
    pass


class StaleApproval(ActionError):
    """Something the approval was bound to changed; the action did not run."""


class EffectUncertain(Exception):
    """An effect handler cannot tell whether its effect happened."""


@dataclass(frozen=True)
class ActionRecord:
    id: str
    origin: str
    proposed_by: str
    effect: str
    purpose: str
    artifact_revision_id: str | None
    payload_sha256: str
    destination: str
    cost_limit_cents: int
    expected_effect: str
    tier: str
    policy_decision: str
    policy_reasons: tuple[str, ...]
    status: str


EffectHandler = Callable[[Path, str], str]


def write_markdown_export(path: Path, text: str) -> str:
    """Atomic local write. Returns the sha256 of the bytes on disk.

    Raises ``FileExistsError`` if a different file already occupies the
    destination: an export never silently overwrites earlier work.
    """
    data = text.encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    if path.exists():
        if hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            return digest
        raise FileExistsError(f"{path.name} already exists with different content")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".export-", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
    try:
        os.replace(tmp, path)
    except OSError as exc:
        # The one step whose failure leaves the effect genuinely uncertain;
        # everything before it provably wrote nothing at the destination.
        raise EffectUncertain(f"effect not confirmed: {exc}") from exc
    return digest


class ActionBoundary:
    def __init__(
        self,
        ws: ManagerWorkspace,
        *,
        profile_policy: Path | None = None,
        edena: EdenaPolicyEngine | None = None,
        handlers: dict[str, EffectHandler] | None = None,
    ):
        self.ws = ws
        self.briefs = BriefService(ws)
        self.profile_path = profile_policy or DEFAULT_PROFILE_POLICY
        self.edena = edena or edena_engine()
        self.handlers = handlers or {"export_markdown": write_markdown_export}

    @property
    def exports_dir(self) -> Path:
        return self.ws.root / "exports"

    def _profile(self) -> dict[str, Any]:
        # Re-read on every evaluation: a policy change between approval and
        # execution must be seen by the executor's recheck.
        return json.loads(self.profile_path.read_text(encoding="utf-8"))

    # -- evaluation -------------------------------------------------------

    def _evaluate(
        self, effect: str, origin: str, proposed_by: str, purpose: str,
        revision_id: str | None, destination: str, profile: dict[str, Any] | None = None,
    ) -> tuple[str, str, tuple[str, ...], dict[str, Any] | None]:
        """Return (tier, decision, reasons, effect_rule)."""
        profile = profile or self._profile()
        if effect in profile["blocked_effects"]:
            return "red", "deny", ("MGR-EFFECT-BLOCKED",), None
        rule = profile["effects"].get(effect)
        if rule is None:
            return "red", "deny", ("MGR-EFFECT-UNKNOWN",), None
        tier = rule["tier"]
        if origin not in rule["allowed_origins"]:
            return tier, "deny", ("MGR-ORIGIN-NOT-ADMITTED",), rule
        if not _destination_ok(destination, rule):
            return tier, "deny", ("MGR-DESTINATION-SCOPE",), rule
        if revision_id is None:
            return tier, "deny", ("MGR-NO-PAYLOAD",), rule
        revision = self.briefs.revision(revision_id)
        if rule.get("requires_accepted_revision") and revision.status != "accepted":
            return tier, "deny", ("MGR-NOT-ACCEPTED",), rule
        if origin == "assistant":
            decision = self._edena_decide(profile, effect, proposed_by, purpose)
            if decision.decision is not Decision.ALLOW:
                return tier, "deny", decision.reason_codes, rule
        if rule.get("requires_approval", True):
            return tier, "require_approval", ("MGR-HUMAN-REVIEW",), rule
        return tier, "allow", ("MGR-WITHIN-SCOPE",), rule

    def _edena_decide(self, profile: dict[str, Any], effect: str, agent_id: str, purpose: str):
        spec = profile["assistant_evaluation"]
        tenant = f"personal:{self.ws.info.id}"
        request = GatewayRequest(
            request_id=new_id("req"),
            actor=Actor(actor_id=agent_id, role=spec["role"], tenant=tenant),
            intent=f"propose_{effect}",
            content=purpose,
            risk_tier=RiskTier(spec["risk_tier"]),
            data_class=DataClass(spec["data_class"]),
            action_mode=ActionMode(spec["action_mode"]),
            target_tenant=tenant,
            data_zone=DataZone(spec["data_zone"]),
        )
        return self.edena.decide(request)

    def _policy_version(self, profile: dict[str, Any], origin: str) -> str:
        """The policy that decides an action: the profile, and for an
        assistant's proposal the EDENA gateway policy as well."""
        version = f"{profile['policy_id']}@{profile['version']}"
        if origin == "assistant":
            version += f"+edena-gateway-policy@{self.edena.version}"
        return version

    # -- lifecycle --------------------------------------------------------

    def propose(
        self,
        effect: str,
        *,
        revision_id: str | None,
        destination: str,
        purpose: str,
        proposed_by: str,
        origin: str = "human",
        cost_limit_cents: int = 0,
    ) -> ActionRecord:
        if origin not in ("human", "assistant"):
            raise ActionError(f"unknown origin: {origin}")
        if origin == "human" and proposed_by != self.ws.info.owner:
            raise ActionError("human actions in this workspace come from its owner")
        if origin == "assistant" and proposed_by == self.ws.info.owner:
            raise ActionError("an assistant cannot propose under the manager's identity")
        if cost_limit_cents < 0:
            raise ActionError("cost limit cannot be negative")
        self.ws._screen(purpose=purpose, destination=destination)
        payload_sha = ""
        if revision_id is not None:
            payload_sha = self.briefs.revision(revision_id).body_sha256
        profile = self._profile()
        tier, decision, reasons, _ = self._evaluate(
            effect, origin, proposed_by, purpose, revision_id, destination, profile
        )
        status = {"deny": "denied", "require_approval": "awaiting_approval",
                  "allow": "approved"}[decision]
        action_id = new_id("act")
        now = self.ws.clock()
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO actions (id, workspace_id, origin, proposed_by, effect, purpose,"
                " artifact_revision_id, payload_sha256, destination, cost_limit_cents,"
                " expected_effect, tier, policy_decision, policy_reasons, status,"
                " created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (action_id, self.ws.info.id, origin, proposed_by, effect, purpose,
                 revision_id, payload_sha, destination, cost_limit_cents,
                 _expected_effect(effect, destination), tier, decision,
                 json.dumps(list(reasons)), status, now, now),
            )
            db.execute(
                "INSERT INTO action_policy_versions (action_id, policy_version) VALUES (?, ?)",
                (action_id, self._policy_version(profile, origin)),
            )
            self.ws.store.log(proposed_by, f"propose:{decision}", "action", action_id)
        return self.get(action_id)

    def approve(
        self, action_id: str, approver: str, *, seen_sha256: str, seen_destination: str
    ) -> ActionRecord:
        action = self.get(action_id)
        if action.status != "awaiting_approval":
            raise ActionError(f"action is {action.status}; nothing to approve")
        if approver != self.ws.info.owner:
            raise ActionError("only this workspace's accountable manager can approve")
        rule = self._profile()["effects"].get(action.effect) or {}
        if rule.get("requires_independent_review") and approver == action.proposed_by:
            raise ActionError(
                "this effect needs independent review; one person confirming twice"
                " is not independent"
            )
        if seen_sha256 != action.payload_sha256 or seen_destination != action.destination:
            raise StaleApproval("the approval does not match the proposal as recorded")
        revision = self.briefs.revision(action.artifact_revision_id)
        if revision.body_sha256 != action.payload_sha256:
            raise StaleApproval("the content changed after it was proposed")
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO approvals (id, action_id, approver, workspace_id,"
                " artifact_revision_id, payload_sha256, destination, approved_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (new_id("apr"), action_id, approver, self.ws.info.id,
                 action.artifact_revision_id, seen_sha256, seen_destination, self.ws.clock()),
            )
            self._set_status(action_id, "approved", approver, "approve")
        return self.get(action_id)

    def execute(self, action_id: str, actor: str) -> dict[str, Any]:
        action = self.get(action_id)
        if action.status == "succeeded":
            # Retry never duplicates an effect.
            return self.receipt(action_id)
        if action.status != "approved":
            raise ActionError(f"action is {action.status}; it cannot run")
        if actor != self.ws.info.owner:
            raise ActionError("only this workspace's manager can run its actions")

        problem = self._recheck(action)
        if problem:
            with self.ws.store.transaction():
                self._set_status(action_id, "stale", actor, "stale")
            raise StaleApproval(problem)

        revision = self.briefs.revision(action.artifact_revision_id)
        text = self.briefs.render(revision)
        target = self.exports_dir / action.destination
        with self.ws.store.transaction():
            self._set_status(action_id, "executing", actor, "execute")
        try:
            handler = self.handlers[action.effect]
            digest = handler(target, text)
        except EffectUncertain as exc:
            return self._finish(action_id, actor, "effect_unknown", str(exc))
        except Exception as exc:  # noqa: BLE001 — a failed effect is recorded, not raised
            return self._finish(action_id, actor, "failed", f"{type(exc).__name__}: {exc}")
        return self._finish(
            action_id, actor, "succeeded",
            f"wrote exports/{action.destination} (sha256 {digest})",
        )

    def reconcile(self) -> list[dict[str, Any]]:
        """After a restart: settle any execution that was interrupted mid-flight."""
        settled = []
        for row in self.ws.store.conn.execute(
            "SELECT id FROM actions WHERE workspace_id = ? AND status = 'executing'",
            (self.ws.info.id,),
        ).fetchall():
            action = self.get(row["id"])
            target = self.exports_dir / action.destination
            expected = self.approved_export_sha256(action)
            if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == expected:
                settled.append(self._finish(
                    action.id, "system", "succeeded",
                    "confirmed after restart: file on disk matches the approved content"
                    f" (sha256 {expected})",
                ))
            else:
                settled.append(self._finish(
                    action.id, "system", "effect_unknown",
                    "interrupted before the effect could be confirmed; not retried",
                ))
        return settled

    def approved_export_sha256(self, action: ActionRecord) -> str:
        """The sha256 of the export the manager approved: what reconcile()
        requires the file on disk to match before calling it a success."""
        return hashlib.sha256(
            self.briefs.render(self.briefs.revision(action.artifact_revision_id)).encode("utf-8")
        ).hexdigest()

    def _recheck(self, action: ActionRecord) -> str:
        approval = self.ws.store.conn.execute(
            "SELECT * FROM approvals WHERE action_id = ?", (action.id,)
        ).fetchone()
        if approval is None:
            return "no recorded approval"
        if (
            approval["workspace_id"] != self.ws.info.id
            or approval["payload_sha256"] != action.payload_sha256
            or approval["destination"] != action.destination
            or approval["artifact_revision_id"] != action.artifact_revision_id
            or approval["approver"] != self.ws.info.owner
        ):
            return "the approval is bound to a different payload, destination, or actor"
        revision = self.briefs.revision(action.artifact_revision_id)
        if revision.body_sha256 != action.payload_sha256:
            return "the approved content has changed"
        tier, decision, reasons, _ = self._evaluate(
            action.effect, action.origin, action.proposed_by, action.purpose,
            action.artifact_revision_id, action.destination,
        )
        if decision == "deny":
            return "policy no longer admits this action: " + ", ".join(reasons)
        return ""

    def _finish(self, action_id: str, actor: str, outcome: str, detail: str) -> dict[str, Any]:
        with self.ws.store.transaction() as db:
            db.execute(
                "INSERT INTO receipts (id, action_id, outcome, detail, recorded_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (new_id("rcp"), action_id, outcome, detail, self.ws.clock()),
            )
            self._set_status(action_id, outcome, actor, outcome)
        return self.receipt(action_id)

    def _set_status(self, action_id: str, status: str, actor: str, kind: str) -> None:
        self.ws.store.conn.execute(
            "UPDATE actions SET status = ?, updated_at = ? WHERE id = ?",
            (status, self.ws.clock(), action_id),
        )
        self.ws.store.log(actor, kind, "action", action_id)

    # -- reads ------------------------------------------------------------

    def get(self, action_id: str) -> ActionRecord:
        row = self.ws.store.conn.execute(
            "SELECT * FROM actions WHERE id = ? AND workspace_id = ?",
            (action_id, self.ws.info.id),
        ).fetchone()
        if row is None:
            raise ActionError(f"action {action_id} is not in this workspace")
        return ActionRecord(
            id=row["id"], origin=row["origin"], proposed_by=row["proposed_by"],
            effect=row["effect"], purpose=row["purpose"],
            artifact_revision_id=row["artifact_revision_id"],
            payload_sha256=row["payload_sha256"], destination=row["destination"],
            cost_limit_cents=row["cost_limit_cents"], expected_effect=row["expected_effect"],
            tier=row["tier"], policy_decision=row["policy_decision"],
            policy_reasons=tuple(json.loads(row["policy_reasons"])), status=row["status"],
        )

    def policy_version(self, action_id: str) -> str | None:
        """The policy that decided the action, as it was then. None for an
        action recorded before versions were kept: unknown, not guessed."""
        row = self.ws.store.conn.execute(
            "SELECT v.policy_version FROM action_policy_versions v"
            " JOIN actions a ON a.id = v.action_id"
            " WHERE v.action_id = ? AND a.workspace_id = ?",
            (action_id, self.ws.info.id),
        ).fetchone()
        return row["policy_version"] if row else None

    def receipt(self, action_id: str) -> dict[str, Any]:
        row = self.ws.store.conn.execute(
            "SELECT * FROM receipts WHERE action_id = ? ORDER BY recorded_at DESC, rowid DESC"
            " LIMIT 1",
            (action_id,),
        ).fetchone()
        if row is None:
            raise ActionError(f"action {action_id} has no receipt")
        return {"action_id": action_id, "outcome": row["outcome"], "detail": row["detail"],
                "recorded_at": row["recorded_at"]}


def _destination_ok(destination: str, rule: dict[str, Any]) -> bool:
    if rule.get("destination_scope") != "workspace_exports":
        return False
    name = Path(destination)
    return (
        destination == name.name
        and not destination.startswith(".")
        and destination.endswith(rule.get("destination_suffix", ""))
        and len(destination) <= 120
    )


def _expected_effect(effect: str, destination: str) -> str:
    if effect == "export_markdown":
        return f"create exports/{destination} containing the accepted brief"
    return f"{effect} → {destination}"
