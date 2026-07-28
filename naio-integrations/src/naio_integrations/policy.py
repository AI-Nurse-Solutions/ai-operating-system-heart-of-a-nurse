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
import logging
from pathlib import Path
from typing import Any

from .contract import (
    ActionMode,
    DataClass,
    DataZone,
    Decision,
    GatewayRequest,
    PolicyDecision,
    PolicyDecisionInterface,
    RiskTier,
)

DEFAULT_POLICY_PATH = Path(__file__).resolve().parents[2] / "config" / "edena-gateway-policy.json"

logger = logging.getLogger(__name__)


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
            # Application log only — the audit ledger stays metadata-only.
            logger.exception("EDENA policy evaluation failed; failing closed")
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

        zone_rules = self.policy["zone_rules"]
        audience = str(request.metadata.get("audience", "")).lower()
        if request.data_zone is DataZone.PRIVATE and audience in zone_rules[
            "private_zone_denied_audiences"
        ]:
            return self._deny("EDENA-PRIVATE-REFLECTION")
        target_zone = request.metadata.get("target_zone")
        if target_zone and target_zone not in zone_rules["allowed_target_zones"]:
            return self._deny("EDENA-INVALID-ZONE")
        if (
            target_zone
            and target_zone != request.data_zone.value
            and zone_rules["migration_requires_approval"]
            and not request.metadata.get("zone_migration_approval")
        ):
            return PolicyDecision(
                decision=Decision.REQUIRE_APPROVAL,
                reason_codes=("EDENA-ZONE-MIGRATION",),
                obligations=("record_zone_migration_approval",),
                policy_version=self.version,
            )

        # Packet role ids resolve to their policy archetype before rule
        # lookup, so "pre-licensure-student" carries the student gates.
        policy_role = self.policy["role_aliases"].get(actor.role, actor.role)
        role_rules = self.policy["role_rules"].get(policy_role)
        if role_rules:
            if request.intent in role_rules.get("denied_intents", ()):
                return self._deny(role_rules["reason_code"])
            ceiling = role_rules.get("max_action_mode")
            if ceiling and mode.rank > ActionMode(ceiling).rank:
                return self._deny(role_rules["reason_code"])

        # Research governance gates (Phase 4): executing research —
        # collecting data, recruiting, submitting to an IRB, sharing a
        # dataset — is gated by activity class, independent of action
        # mode. Drafting a protocol or question is ordinary draft work.
        research_rules = self.policy.get("research_rules", {})
        research_gated = request.intent in research_rules.get("execution_intents", ())
        if research_gated:
            if request.data_zone.value != research_rules["required_zone"]:
                return self._deny("EDENA-RESEARCH-ZONE")
            if research_rules.get("requires_institutional_authentication") and (
                not actor.authenticated_org
                or actor.authenticated_org != actor.tenant
            ):
                return self._deny("EDENA-RESEARCH-UNAFFILIATED")
            if research_rules.get("requires_recorded_approval") and not actor.approvals:
                return PolicyDecision(
                    decision=Decision.REQUIRE_APPROVAL,
                    reason_codes=("EDENA-RESEARCH-APPROVAL",),
                    obligations=("record_research_governance_approval",),
                    policy_version=self.version,
                )

        data_ceiling = self.policy["tier_data_ceilings"].get(tier.value)
        if data_ceiling is None or data.rank > DataClass(data_ceiling).rank:
            return self._deny("EDENA-DATA-CLASS-CEILING")

        action_ceiling = self.policy["tier_action_ceilings"].get(tier.value)
        if action_ceiling is None or mode.rank > ActionMode(action_ceiling).rank:
            return self._deny("EDENA-ACTION-MODE-CEILING")

        obligations: list[str] = []
        reasons: list[str] = []
        if target_zone and target_zone != request.data_zone.value:
            obligations.append("log_zone_migration")
        if research_gated:
            obligations.append("research_governance_audit")

        if tier in (RiskTier.ORANGE, RiskTier.RED_E):
            requirements = self.policy[
                "orange_requirements" if tier is RiskTier.ORANGE else "red_e_requirements"
            ]
            if requirements.get("authenticated_org") and (
                not actor.authenticated_org
                or actor.authenticated_org != actor.tenant
            ):
                # The organizational context must BE the current workspace —
                # an org login carried into a personal or foreign workspace
                # grants nothing.
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
            if mode_rule.get("requires_approval_id"):
                approval_id = request.metadata.get("approval_id")
                if not approval_id:
                    return PolicyDecision(
                        decision=Decision.REQUIRE_APPROVAL,
                        reason_codes=("EDENA-SIDE-EFFECT-GATE",),
                        obligations=("record_approval_id",),
                        policy_version=self.version,
                    )
                if approval_id not in actor.approvals:
                    # A fabricated or unrecorded approval is worse than a
                    # missing one: fail closed instead of re-prompting.
                    return self._deny("EDENA-APPROVAL-UNRECOGNIZED")
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
