"""Orchestration reference adapter (pattern: langchain-ai/langgraph).

Operationalizes ADPIE as a long-running, stateful workflow:

    Assess -> Diagnose -> Plan -> Human authorization ->
    Implement -> Evaluate -> Learn -> (Reassess or Complete)

Florence-X remains the named orchestration and professional reasoning
layer; this runtime sits underneath it. Checkpoints are durable JSON on
disk, the workflow pauses at the human-authorization gate and cannot be
advanced past it programmatically, and every transition is kept in the
state history so a project is resumable after any interruption.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .contract import OrchestrationInterface

STAGES = (
    "assess",
    "diagnose",
    "plan",
    "human_authorization",
    "implement",
    "evaluate",
    "learn",
    "complete",
)


class WorkflowError(RuntimeError):
    pass


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class AdpieWorkflow(OrchestrationInterface):
    """Durable, resumable ADPIE state machine with a hard human gate."""

    def __init__(self, checkpoint_dir: Path, now=None):
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self._now = now or _utcnow

    def start(self, workflow_id: str, context: dict[str, Any]) -> dict[str, Any]:
        if self._path(workflow_id).exists():
            raise WorkflowError(f"workflow {workflow_id} already exists")
        state = {
            "workflow_id": workflow_id,
            "stage": "assess",
            "status": "running",
            "context": context,
            "stage_outputs": {},
            "authorization": None,
            "history": [
                {"at": self._now(), "event": "started", "stage": "assess"},
            ],
        }
        self._save(state)
        return state

    def advance(self, workflow_id: str, **inputs: Any) -> dict[str, Any]:
        state = self.state(workflow_id)
        stage = state["stage"]
        if state["status"] == "complete":
            raise WorkflowError("workflow already complete")
        if stage == "human_authorization":
            raise WorkflowError(
                "workflow is paused at the human-authorization gate; "
                "only authorize() can move it"
            )
        state["stage_outputs"][stage] = inputs or {"note": "no output recorded"}
        next_stage = STAGES[STAGES.index(stage) + 1]
        state["stage"] = next_stage
        if next_stage == "human_authorization":
            state["status"] = "awaiting_authorization"
        if next_stage == "complete":
            state["status"] = "complete"
        state["history"].append(
            {"at": self._now(), "event": "advanced", "from": stage, "stage": next_stage}
        )
        self._save(state)
        return state

    def authorize(self, workflow_id: str, approver: str, approved: bool) -> dict[str, Any]:
        state = self.state(workflow_id)
        if state["stage"] != "human_authorization":
            raise WorkflowError("workflow is not at the human-authorization gate")
        if not approver:
            raise WorkflowError("authorization requires a named accountable human")
        state["authorization"] = {
            "approver": approver,
            "approved": approved,
            "at": self._now(),
        }
        if approved:
            state["stage"] = "implement"
            state["status"] = "running"
            event = "authorized"
        else:
            state["stage"] = "plan"
            state["status"] = "running"
            event = "returned_to_planning"
        state["history"].append(
            {"at": self._now(), "event": event, "approver": approver, "stage": state["stage"]}
        )
        self._save(state)
        return state

    def reassess(self, workflow_id: str) -> dict[str, Any]:
        """Cyclical improvement: loop a learned workflow back to assessment."""
        state = self.state(workflow_id)
        if state["stage"] not in ("learn", "complete"):
            raise WorkflowError("reassessment starts from learn or complete")
        state["stage"] = "assess"
        state["status"] = "running"
        state["authorization"] = None
        state["history"].append({"at": self._now(), "event": "reassess", "stage": "assess"})
        self._save(state)
        return state

    def state(self, workflow_id: str) -> dict[str, Any]:
        path = self._path(workflow_id)
        if not path.exists():
            raise WorkflowError(f"unknown workflow {workflow_id}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _path(self, workflow_id: str) -> Path:
        if not workflow_id.replace("-", "").replace("_", "").isalnum():
            raise WorkflowError("workflow id must be alphanumeric with - or _")
        return self.checkpoint_dir / f"{workflow_id}.json"

    def _save(self, state: dict[str, Any]) -> None:
        path = self._path(state["workflow_id"])
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
