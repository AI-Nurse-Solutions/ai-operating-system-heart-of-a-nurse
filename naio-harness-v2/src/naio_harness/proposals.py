from __future__ import annotations

import hashlib
import json
import os
import secrets
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .ledger import ProvenanceLedger


class ProposalError(RuntimeError):
    pass


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat()


def action_digest(capability_id: str, target: str, arguments: dict[str, Any]) -> str:
    envelope = {"capability_id": capability_id, "target": target, "arguments": arguments}
    raw = json.dumps(envelope, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def approval_digest(proposal: dict[str, Any], reviewer_role: str, approved_at: str) -> str:
    binding = {
        "proposal_id": proposal["proposal_id"],
        "manifest_hash": proposal["manifest_hash"],
        "action_digest": proposal["action_digest"],
        "target": proposal["target"],
        "reviewer_role": reviewer_role,
        "approved_at": approved_at,
    }
    return hashlib.sha256(json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ProposalStore:
    """Durable proposal store. Action payloads are never persisted, only hashes."""

    def __init__(self, directory: Path, ledger_path: Path | None = None):
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.ledger = ProvenanceLedger(ledger_path or directory / "proposal-events.jsonl")

    def create(
        self,
        *,
        capability_id: str,
        manifest_hash: str,
        policy_version: str,
        dataset_version: str,
        risk_tier: str,
        autonomy_level: str,
        side_effecting: bool,
        idempotent: bool,
        target: str,
        arguments: dict[str, Any],
        expires_in_seconds: int = 3600,
        max_attempts: int = 3,
    ) -> dict[str, Any]:
        if risk_tier == "red":
            raise ProposalError("red-risk work cannot become an executable proposal")
        if side_effecting and not target:
            raise ProposalError("side-effecting proposals require an explicit target")
        created = _now()
        proposal = {
            "schema_version": "2.0.0",
            "proposal_id": secrets.token_hex(16),
            "created_at": _iso(created),
            "expires_at": _iso(created + timedelta(seconds=expires_in_seconds)),
            "status": "pending_review",
            "capability_id": capability_id,
            "manifest_hash": manifest_hash,
            "policy_version": policy_version,
            "dataset_version": dataset_version,
            "risk_tier": risk_tier,
            "autonomy_level": autonomy_level,
            "side_effecting": bool(side_effecting),
            "idempotent": bool(idempotent),
            "target": target,
            "action_digest": action_digest(capability_id, target, arguments),
            "idempotency_key": secrets.token_hex(16),
            "attempt_count": 0,
            "max_attempts": int(max_attempts),
            "approval": None,
            "lease": None,
            "tombstone_reason": None,
        }
        self._save(proposal)
        self._event(proposal, "proposal_created")
        return proposal

    def approve(self, proposal_id: str, reviewer_role: str, arguments: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
        proposal = self.load(proposal_id)
        now = now or _now()
        self._expire_if_needed(proposal, now)
        if proposal["status"] not in {"pending_review", "needs_review"}:
            raise ProposalError(f"proposal is not reviewable: {proposal['status']}")
        self._assert_action(proposal, arguments)
        approved_at = _iso(now)
        proposal["approval"] = {
            "reviewer_role": reviewer_role,
            "approved_at": approved_at,
            "approval_digest": approval_digest(proposal, reviewer_role, approved_at),
        }
        proposal["status"] = "approved"
        proposal["lease"] = None
        self._save(proposal)
        self._event(proposal, "proposal_approved")
        return proposal

    def acquire(self, proposal_id: str, worker_id: str, arguments: dict[str, Any], lease_seconds: int = 120) -> dict[str, Any]:
        proposal = self.load(proposal_id)
        now = _now()
        self._expire_if_needed(proposal, now)
        if proposal["status"] != "approved" or proposal["approval"] is None:
            raise ProposalError(f"proposal is not executable: {proposal['status']}")
        self._assert_action(proposal, arguments)
        if proposal["attempt_count"] >= proposal["max_attempts"]:
            proposal["status"] = "tombstoned"
            proposal["tombstone_reason"] = "retry_ceiling_reached"
            self._save(proposal)
            self._event(proposal, "proposal_tombstoned")
            raise ProposalError("retry ceiling reached")
        proposal["attempt_count"] += 1
        proposal["status"] = "executing"
        proposal["lease"] = {
            "worker_hash": hashlib.sha256(worker_id.encode()).hexdigest(),
            "acquired_at": _iso(now),
            "expires_at": _iso(now + timedelta(seconds=lease_seconds)),
        }
        self._save(proposal)
        self._event(proposal, "proposal_acquired")
        return proposal

    def complete(self, proposal_id: str, result_metadata: dict[str, Any]) -> dict[str, Any]:
        proposal = self.load(proposal_id)
        if proposal["status"] != "executing":
            raise ProposalError("only executing proposals can complete")
        proposal["status"] = "executed"
        proposal["lease"] = None
        proposal["result_digest"] = hashlib.sha256(
            json.dumps(result_metadata, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        self._save(proposal)
        self._event(proposal, "proposal_completed")
        return proposal

    def reconcile_restart(self) -> list[dict[str, Any]]:
        reconciled = []
        for path in sorted(self.directory.glob("proposal-*.json")):
            proposal = json.loads(path.read_text(encoding="utf-8"))
            if proposal["status"] != "executing":
                continue
            proposal["lease"] = None
            if proposal["attempt_count"] >= proposal["max_attempts"]:
                proposal["status"] = "tombstoned"
                proposal["tombstone_reason"] = "retry_ceiling_reached_after_restart"
            elif proposal["side_effecting"] or not proposal["idempotent"]:
                proposal["status"] = "needs_review"
                proposal["approval"] = None
            else:
                proposal["status"] = "approved"
            self._save(proposal)
            self._event(proposal, "proposal_reconciled")
            reconciled.append(proposal)
        return reconciled

    def load(self, proposal_id: str) -> dict[str, Any]:
        path = self.directory / f"proposal-{proposal_id}.json"
        if not path.exists():
            raise ProposalError("proposal not found")
        return json.loads(path.read_text(encoding="utf-8"))

    def kanban_card(self, proposal_id: str) -> dict[str, Any]:
        proposal = self.load(proposal_id)
        return {
            "title": f"EDENA review: {proposal['capability_id']}",
            "status": proposal["status"],
            "proposal_id": proposal["proposal_id"],
            "risk_tier": proposal["risk_tier"],
            "target": proposal["target"],
            "expires_at": proposal["expires_at"],
            "action_digest": proposal["action_digest"],
            "contains_payload": False,
        }

    def _assert_action(self, proposal: dict[str, Any], arguments: dict[str, Any]) -> None:
        digest = action_digest(proposal["capability_id"], proposal["target"], arguments)
        if digest != proposal["action_digest"]:
            raise ProposalError("action changed after proposal creation")

    def _expire_if_needed(self, proposal: dict[str, Any], now: datetime) -> None:
        if now >= datetime.fromisoformat(proposal["expires_at"]):
            proposal["status"] = "expired"
            self._save(proposal)
            self._event(proposal, "proposal_expired")
            raise ProposalError("proposal expired")

    def _path(self, proposal: dict[str, Any]) -> Path:
        return self.directory / f"proposal-{proposal['proposal_id']}.json"

    def _save(self, proposal: dict[str, Any]) -> None:
        path = self._path(proposal)
        fd, temporary = tempfile.mkstemp(prefix=path.name + ".", dir=self.directory)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(proposal, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _event(self, proposal: dict[str, Any], event_type: str) -> None:
        self.ledger.append({
            "schema_version": "2.0.0-proposal",
            "event_type": event_type,
            "proposal_id": proposal["proposal_id"],
            "capability_id": proposal["capability_id"],
            "status": proposal["status"],
            "action_digest": proposal["action_digest"],
            "payload_captured": False,
        })
