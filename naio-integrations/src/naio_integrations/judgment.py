"""Judgment support layer — the runtime companion to "Humans judge."

EDENA decides whether a request may proceed. This layer shapes how an
answer is allowed to arrive, because the middle clause of the doctrine
is load-bearing: humans can only judge what reaches them in judgeable
form. Like EDENA, it is embedded at the gateway and driven by reviewed
configuration (``config/judgment-frames.json``) — a feature of the
runtime, not advice in a prompt pack.

Three mechanics, all deterministic:

* **Frames** — every request is matched to a named thinking frame
  (clinical judgment, systems lens, design studio, evidence appraisal,
  or general judgment) so the discipline in use is visible and
  learnable, never silent.
* **Probes** — each frame carries commit-then-compare questions. The
  gateway attaches one deterministic probe per request so the host can
  elicit the user's own read before or alongside the answer. Coach-first
  roles (students by default) are always probed.
* **Reasoning ledger** — outputs are scanned for visible judgment
  material: stated assumptions, alternatives, and change conditions.
  Decision-shaped output at consequential tiers (Yellow and above, in
  Recommend mode) that carries none of them is refused at the gateway
  with ``EDENA-JUDGMENT-VISIBILITY`` — a consequential recommendation
  may not leave the gateway as a naked verdict.

The ledger detects wording, not wisdom: a visible assumption can still
be a bad assumption. The layer makes judgment material present; the
human remains the judge.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .contract import ActionMode, GatewayRequest, RiskTier

DEFAULT_FRAMES_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "judgment-frames.json"
)


@dataclass(frozen=True)
class ReasoningLedger:
    """What judgment material an output visibly carries."""

    decision_shaped: bool
    assumptions_stated: bool
    alternatives_stated: bool
    change_conditions_stated: bool

    @property
    def visible_reasoning(self) -> bool:
        return (
            self.assumptions_stated
            or self.alternatives_stated
            or self.change_conditions_stated
        )

    @property
    def missing(self) -> tuple[str, ...]:
        gaps = []
        if not self.assumptions_stated:
            gaps.append("assumptions")
        if not self.alternatives_stated:
            gaps.append("alternatives")
        if not self.change_conditions_stated:
            gaps.append("change_conditions")
        return tuple(gaps)


@dataclass(frozen=True)
class JudgmentGuidance:
    """The frame, probe, and notice attached to one request."""

    frame: str
    frame_label: str
    probe: str
    coach_first: bool
    notice: str


class JudgmentGuide:
    """Deterministic, config-driven judgment support for the gateway."""

    def __init__(
        self,
        frames_path: Path | None = None,
        role_aliases: dict[str, str] | None = None,
    ):
        path = frames_path or DEFAULT_FRAMES_PATH
        self.config: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        # Packet role ids resolve to their policy archetype exactly as the
        # policy engine resolves them, so coach-first follows one alias table.
        self.role_aliases: dict[str, str] = dict(role_aliases or {})
        self._intent_to_frame: dict[str, str] = {}
        for name, frame in self.config["frames"].items():
            for intent in frame.get("intents", ()):
                self._intent_to_frame[intent] = name

    # ------------------------------------------------------------------
    # Frames and probes (before the answer)

    def frame_for(self, request: GatewayRequest) -> str:
        override = request.metadata.get("thinking_frame")
        if override in self.config["frames"]:
            return str(override)
        return self._intent_to_frame.get(
            request.intent, self.config["default_frame"]
        )

    def guidance(self, request: GatewayRequest) -> JudgmentGuidance:
        frame_name = self.frame_for(request)
        frame = self.config["frames"][frame_name]
        probes = frame["probes"]
        # Deterministic probe selection: stable for a given request,
        # varied across requests, no randomness (rebuildable audits).
        seed = hashlib.sha256(
            f"{request.request_id}:{request.intent}".encode("utf-8")
        ).digest()
        probe = probes[seed[0] % len(probes)]
        role = self.role_aliases.get(request.actor.role, request.actor.role)
        coach_first = role in self.config["coach_first_roles"] or (
            request.metadata.get("thinking_posture") == "coach_first"
        )
        return JudgmentGuidance(
            frame=frame_name,
            frame_label=frame["label"],
            probe=probe,
            coach_first=coach_first,
            notice=self.config["notice"],
        )

    # ------------------------------------------------------------------
    # Reasoning ledger (over the answer)

    def ledger(self, output: str) -> ReasoningLedger:
        folded = output.casefold()
        markers = self.config["reasoning_markers"]

        def any_marker(kind: str) -> bool:
            return any(marker in folded for marker in markers[kind])

        return ReasoningLedger(
            decision_shaped=any(
                marker in folded for marker in self.config["decision_markers"]
            ),
            assumptions_stated=any_marker("assumptions"),
            alternatives_stated=any_marker("alternatives"),
            change_conditions_stated=any_marker("change_conditions"),
        )

    def refuses(self, request: GatewayRequest, ledger: ReasoningLedger) -> bool:
        """True when a consequential recommendation arrives as a naked verdict."""
        enforcement = self.config["enforcement"]
        floor = RiskTier(enforcement["minimum_risk_tier"]).rank
        return (
            request.risk_tier.rank >= floor
            and request.action_mode.value in enforcement["action_modes"]
            and request.action_mode.rank <= ActionMode.CONSTRAINED_AUTONOMY.rank
            and ledger.decision_shaped
            and not ledger.visible_reasoning
        )

    @property
    def reason_code(self) -> str:
        return str(self.config["enforcement"]["reason_code"])
