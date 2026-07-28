"""Validation reference adapter (pattern: guardrails-ai/guardrails).

Sits beneath EDENA and answers a different question than policy does:
EDENA + OPA ask "is this actor permitted to do this?"; this layer asks
"does this input or output satisfy the required quality and safety
constraints?".

Input guards: prompt-injection indicators, unsafe tool requests.
Output guards: unsupported clinical claims, overconfident recommendations,
missing citations, missing educational limitation statements.
"""

from __future__ import annotations

import json
import re

from .contract import (
    GatewayRequest,
    ValidationInterface,
    ValidationIssue,
    ValidationResult,
)

INJECTION_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
        r"disregard\s+(?:your|the)\s+(?:system\s+prompt|rules|guardrails)",
        r"you\s+are\s+now\s+(?:dan|unrestricted|jailbroken)",
        r"reveal\s+(?:your|the)\s+system\s+prompt",
        r"</?(?:system|assistant)>",
    )
]

UNSAFE_TOOL_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\brm\s+-rf\b",
        r"\bdrop\s+table\b",
        r"\bcurl\b[^\n]*\|\s*(?:ba)?sh\b",
    )
]

CLINICAL_CLAIM_PATTERN = re.compile(
    r"\b(?:administer|prescribe|titrate|increase|decrease|hold|give)\b[^.\n]{0,80}"
    r"\b(?:dose|dosage|mg|mcg|units?|mL|drip|infusion)\b",
    re.IGNORECASE,
)

OVERCONFIDENCE_PATTERN = re.compile(
    r"\b(?:guaranteed|always works|cannot fail|100%\s*(?:safe|effective)|no risk)\b",
    re.IGNORECASE,
)

CITATION_PATTERN = re.compile(
    r"\[(?:source|ref)[^\]]*\]|\bdoi:\s*\S+|\bPMID:?\s*\d+|\bhttps?://\S+",
    re.IGNORECASE,
)

EDUCATIONAL_LIMITATION_PATTERN = re.compile(
    r"educational\s+(?:purposes?|use|support)|not\s+(?:a\s+substitute|medical\s+advice)"
    r"|verify\s+with\s+(?:your\s+)?(?:institution|provider|policy)",
    re.IGNORECASE,
)


class TrafficValidator(ValidationInterface):
    """Deterministic input/output guard suite."""

    def validate_input(self, request: GatewayRequest) -> ValidationResult:
        issues: list[ValidationIssue] = []
        for pattern in INJECTION_PATTERNS:
            if pattern.search(request.content):
                issues.append(
                    ValidationIssue(
                        check="prompt_injection",
                        severity="fail",
                        message="Prompt-injection indicator detected in input.",
                    )
                )
                break
        for pattern in UNSAFE_TOOL_PATTERNS:
            if pattern.search(request.content):
                issues.append(
                    ValidationIssue(
                        check="unsafe_tool_request",
                        severity="fail",
                        message="Input requests an unsafe tool invocation.",
                    )
                )
                break
        return ValidationResult(ok=not any(i.severity == "fail" for i in issues), issues=tuple(issues))

    def validate_output(self, request: GatewayRequest, output: str) -> ValidationResult:
        issues: list[ValidationIssue] = []
        clinical = CLINICAL_CLAIM_PATTERN.search(output)
        cited = bool(CITATION_PATTERN.search(output))
        limited = bool(EDUCATIONAL_LIMITATION_PATTERN.search(output))
        if clinical and not cited:
            issues.append(
                ValidationIssue(
                    check="unsupported_clinical_claim",
                    severity="fail",
                    message="Clinical dosing language without any citation.",
                )
            )
        if clinical and not limited:
            issues.append(
                ValidationIssue(
                    check="missing_educational_limitation",
                    severity="fail",
                    message="Clinical content must state its educational limitation.",
                )
            )
        if OVERCONFIDENCE_PATTERN.search(output):
            issues.append(
                ValidationIssue(
                    check="overconfident_recommendation",
                    severity="fail",
                    message="Overconfident language is not permitted in recommendations.",
                )
            )
        if request.intent.endswith("_json"):
            try:
                json.loads(output)
            except (ValueError, TypeError):
                issues.append(
                    ValidationIssue(
                        check="output_schema",
                        severity="fail",
                        message="Output is not the valid JSON this intent requires.",
                    )
                )
        return ValidationResult(ok=not any(i.severity == "fail" for i in issues), issues=tuple(issues))
