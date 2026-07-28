"""EDENA Policy Gateway — the first Integration Contract prototype.

Composes the Phase 1 layers between every Nurse AI OS user, agent, model,
memory store, and external tool:

    Request -> Identity and role -> Privacy screen (Presidio pattern) ->
    EDENA policy decision (OPA pattern) -> Validation (Guardrails pattern) ->
    Allow / deny / require approval -> Execute -> Validate output -> Audit
    (Langfuse pattern, hash-chained, tenant-separated)

Most platforms begin with what the agent can do. Nurse AI OS begins with
what it is authorized to do, what data it may use, what must remain
human-controlled, and how the entire decision can be audited.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from .contract import (
    Decision,
    GatewayRequest,
    PolicyDecision,
    RiskTier,
    ValidationIssue,
)
from .observability import GatewayTracer
from .policy import EdenaPolicyEngine
from .privacy import PrivacyScreen
from .validation import TrafficValidator


@dataclass
class GatewayResult:
    """Everything a caller and an auditor need to know about one request."""

    decision: Decision
    reason_codes: tuple[str, ...]
    obligations: tuple[str, ...]
    trace_id: str
    screened_content: str
    privacy_entity_types: tuple[str, ...] = ()
    output: str | None = None
    validation_issues: tuple[ValidationIssue, ...] = ()
    stage: str = "complete"
    detail: dict[str, Any] = field(default_factory=dict)

    @property
    def allowed(self) -> bool:
        return self.decision is Decision.ALLOW


class EdenaPolicyGateway:
    """The governed front door for every meaningful Nurse AI OS action."""

    def __init__(
        self,
        trace_root: Path,
        policy: EdenaPolicyEngine | None = None,
        privacy: PrivacyScreen | None = None,
        validator: TrafficValidator | None = None,
        tracer: GatewayTracer | None = None,
    ):
        self.policy = policy or EdenaPolicyEngine()
        self.privacy = privacy or PrivacyScreen()
        self.validator = validator or TrafficValidator()
        self.tracer = tracer or GatewayTracer(trace_root)

    def submit(
        self,
        request: GatewayRequest,
        executor: Callable[[GatewayRequest], str] | None = None,
    ) -> GatewayResult:
        trace_id = self.tracer.start_trace(request)

        input_check = self.validator.validate_input(request)
        self.tracer.record_span(
            trace_id,
            "validate_input",
            {"ok": input_check.ok, "issues": [issue.check for issue in input_check.issues]},
        )
        if not input_check.ok:
            return self._finish(
                trace_id,
                request,
                Decision.DENY,
                ("EDENA-INPUT-VALIDATION",),
                stage="validate_input",
                screened="",
                issues=input_check.issues,
            )

        privacy_result = self.privacy.transform(request.content)
        entity_types = tuple(sorted({f.entity_type for f in privacy_result.findings}))
        self.tracer.record_span(
            trace_id,
            "privacy_screen",
            {
                "action": privacy_result.action,
                "finding_count": len(privacy_result.findings),
                "entity_types": list(entity_types),
            },
        )
        if privacy_result.findings and request.risk_tier is RiskTier.GREEN:
            # Green cannot accept identifying content at all — not even redacted.
            return self._finish(
                trace_id,
                request,
                Decision.DENY,
                ("EDENA-PRIVACY-REDLINE",),
                stage="privacy_screen",
                screened="",
                entity_types=entity_types,
            )
        screened_request = GatewayRequest(
            request_id=request.request_id,
            actor=request.actor,
            intent=request.intent,
            content=privacy_result.transformed_text,
            risk_tier=request.risk_tier,
            data_class=request.data_class,
            action_mode=request.action_mode,
            target_tenant=request.target_tenant,
            metadata=request.metadata,
        )

        policy_decision: PolicyDecision = self.policy.decide(screened_request)
        self.tracer.record_span(
            trace_id,
            "policy_decision",
            {
                "decision": policy_decision.decision.value,
                "reason_codes": list(policy_decision.reason_codes),
                "obligations": list(policy_decision.obligations),
            },
        )
        if policy_decision.decision is not Decision.ALLOW:
            return self._finish(
                trace_id,
                request,
                policy_decision.decision,
                policy_decision.reason_codes,
                stage="policy_decision",
                screened=privacy_result.transformed_text,
                obligations=policy_decision.obligations,
                entity_types=entity_types,
            )

        output: str | None = None
        issues: tuple[ValidationIssue, ...] = ()
        if executor is not None:
            raw_output = executor(screened_request)
            output_check = self.validator.validate_output(screened_request, raw_output)
            self.tracer.record_span(
                trace_id,
                "validate_output",
                {"ok": output_check.ok, "issues": [issue.check for issue in output_check.issues]},
            )
            if not output_check.ok:
                return self._finish(
                    trace_id,
                    request,
                    Decision.DENY,
                    ("EDENA-OUTPUT-VALIDATION",),
                    stage="validate_output",
                    screened=privacy_result.transformed_text,
                    issues=output_check.issues,
                    entity_types=entity_types,
                )
            output_privacy = self.privacy.transform(raw_output)
            self.tracer.record_span(
                trace_id,
                "privacy_screen_output",
                {
                    "action": output_privacy.action,
                    "finding_count": len(output_privacy.findings),
                },
            )
            output = output_privacy.transformed_text
            issues = output_check.issues

        self.tracer.end_trace(trace_id, "allow")
        return GatewayResult(
            decision=Decision.ALLOW,
            reason_codes=policy_decision.reason_codes,
            obligations=policy_decision.obligations,
            trace_id=trace_id,
            screened_content=privacy_result.transformed_text,
            privacy_entity_types=entity_types,
            output=output,
            validation_issues=issues,
        )

    def _finish(
        self,
        trace_id: str,
        request: GatewayRequest,
        decision: Decision,
        reasons: tuple[str, ...],
        stage: str,
        screened: str,
        obligations: tuple[str, ...] = (),
        issues: tuple[ValidationIssue, ...] = (),
        entity_types: tuple[str, ...] = (),
    ) -> GatewayResult:
        outcome = decision.value if decision is not Decision.ALLOW else "allow"
        self.tracer.end_trace(trace_id, outcome)
        return GatewayResult(
            decision=decision,
            reason_codes=reasons,
            obligations=obligations,
            trace_id=trace_id,
            screened_content=screened,
            privacy_entity_types=entity_types,
            validation_issues=issues,
            stage=stage,
        )
