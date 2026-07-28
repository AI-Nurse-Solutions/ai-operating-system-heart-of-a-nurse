"""Policy-decision reference adapter (pattern: open-policy-agent/opa).

Evaluates one decision document per request, exactly like an OPA policy
decision point: input document in, `{decision, reason_codes, obligations}`
out. The rules live in ``config/edena-gateway-policy.json`` so EDENA stays
declarative doctrine, not code every developer re-interprets.

Fail-closed everywhere: an unknown tier, mode, role, or a rule the engine
cannot evaluate produces DENY, never ALLOW. Ambiguity narrows capability.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .contract import (
    ActionMode,
    DataClass,
    Decision,
    GatewayRequest,
    PolicyDecision,
    PolicyDecisionInterface,
    RiskTier,
)

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[2] / "config" / "edena-gateway-policy.json"


class EdenaPolicyEngine(PolicyDecisionInterface):
    """Deterministic EDENA policy decision point."""

    def __init__(self, policy_path: Path | None = None):
        path = policy_path or DEFAULT_POLICY_PATH
        self.policy: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        self.version = self.policy.get("schema_version", "unknown")

    def decide(self, request: GatewayRequest) -> PolicyDecision:
        try:
            return self._decide(request)
        except Exception:
            return self._deny("EDENA-EVALUATOR-ERROR")

    def _decide(self, request: GatewayRequest) -> PolicyDecision:
        tier = request.risk_tier
        mode = request.action_mode
        data = request.data_class
        actor = request.actor

        prohibited = self.policy["prohibited"]
        if tier.value in prohibited["risk_tiers"]:
            return self._deny("EDENA-PROHIBITED-TIER")
        if mode.value in prohibited["action_modes"]:
            return self._deny("EDENA-UNRESTRICTED-AUTONOMY")

        if request.target_tenant and request.target_tenant != actor.tenant:
            return self._deny("EDENA-TENANT-BOUNDARY")

        role_rules = self.policy["role_rules"].get(actor.role)
        if role_rules:
            if request.intent in role_rules.get("denied_intents", ()):
                return self._deny(role_rules["reason_code"])
            ceiling = role_rules.get("max_action_mode")
            if ceiling and mode.rank > ActionMode(ceiling).rank:
                return self._deny(role_rules["reason_code"])

        data_ceiling = self.policy["tier_data_ceilings"].get(tier.value)
        if data_ceiling is None or data.rank > DataClass(data_ceiling).rank:
            return self._deny("EDENA-DATA-CLASS-CEILING")

        action_ceiling = self.policy["tier_action_ceilings"].get(tier.value)
        if action_ceiling is None or mode.rank > ActionMode(action_ceiling).rank:
            return self._deny("EDENA-ACTION-MODE-CEILING")

        obligations: list[str] = []
        reasons: list[str] = []

        if tier in (RiskTier.ORANGE, RiskTier.RED_E):
            requirements = self.policy[
                "orange_requirements" if tier is RiskTier.ORANGE else "red_e_requirements"
            ]
            if requirements.get("authenticated_org") and not actor.authenticated_org:
                return self._deny("EDENA-ORG-CONTEXT-REQUIRED")
            if requirements.get("recorded_approval") and not actor.approvals:
                return self._deny("EDENA-APPROVAL-REQUIRED")
            missing = [
                control
                for control in requirements.get("institutional_controls", ())
                if control not in request.metadata.get("institutional_controls", ())
            ]
            if missing:
                return self._deny("EDENA-INSTITUTIONAL-CONTROLS")
            obligations.append("continuous_audit")

        if mode.has_side_effects:
            side_rules = self.policy["side_effect_rules"]
            mode_rule = side_rules.get(mode.value, {})
            if mode_rule.get("tiers") and tier.value not in mode_rule["tiers"]:
                return self._deny("EDENA-ACTION-MODE-CEILING")
            if mode_rule.get("decision") == "require_approval":
                return PolicyDecision(
                    decision=Decision.REQUIRE_APPROVAL,
                    reason_codes=("EDENA-SIDE-EFFECT-GATE",),
                    obligations=("meaningful_human_approval",),
                    policy_version=self.version,
                )
            if mode_rule.get("requires_approval_id") and not request.metadata.get("approval_id"):
                return PolicyDecision(
                    decision=Decision.REQUIRE_APPROVAL,
                    reason_codes=("EDENA-SIDE-EFFECT-GATE",),
                    obligations=("record_approval_id",),
                    policy_version=self.version,
                )
            obligations.append("log_side_effect")

        reasons.append("EDENA-WITHIN-SCOPE")
        return PolicyDecision(
            decision=Decision.ALLOW,
            reason_codes=tuple(reasons),
            obligations=tuple(obligations),
            policy_version=self.version,
        )

    def _deny(self, reason_code: str) -> PolicyDecision:
        return PolicyDecision(
            decision=Decision.DENY,
            reason_codes=(reason_code,),
            policy_version=self.version,
        )
