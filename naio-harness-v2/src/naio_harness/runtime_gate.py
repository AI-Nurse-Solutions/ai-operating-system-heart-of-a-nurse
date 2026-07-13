from __future__ import annotations

import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .capabilities import compile_capabilities, load_manifests
from .config_store import load_runtime_config
from .ledger import ProvenanceLedger
from .models import CapabilityLayer, CompilationContext, RiskTier

SENSITIVE_KEYS = {
    "mrn", "patient", "patient_name", "date_of_birth", "dob", "medical_record",
    "chart", "diagnosis", "room_number", "ssn", "password", "passwd", "secret",
    "api_key", "apikey", "access_token", "refresh_token", "card_number", "cvv",
}
SENSITIVE_PATTERNS = [
    re.compile(r"\bMRN\s*[:#-]?\s*[A-Z0-9]{4,}\b", re.IGNORECASE),
    re.compile(r"\bDOB\s*[:#-]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b", re.IGNORECASE),
    re.compile(r"\b(?:SSN|social security)\s*[:#-]?\s*\d{3}-?\d{2}-?\d{4}\b", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"\b(?:sk|gh[opusr])_[A-Za-z0-9_-]{20,}\b"),
]


class RuntimeGate:
    """Evaluate Hermes tool calls while minimizing logged data."""

    def __init__(
        self,
        root: Path,
        log_path: Path | None = None,
        runtime_config_path: Path | None = None,
        mode: str = "shadow",
    ):
        self.root = root
        configured = runtime_config_path or Path(os.environ.get("NAIO_RUNTIME_CONFIG", root / "config" / "runtime-profile.json"))
        self.config = load_runtime_config(configured)
        self.manifests = load_manifests(root / "manifests")
        self.tool_map = json.loads((root / "config" / "tool-map.json").read_text(encoding="utf-8"))
        self.log_path = log_path or Path(os.environ.get("NAIO_SHADOW_LOG", root / "state" / "runtime-events.jsonl"))
        self.mode = mode

    def evaluate(self, tool_name: str, args: Any = None) -> dict[str, Any]:
        redline = self._detect_redline(args)
        if redline:
            return self._event(tool_name, self.tool_map.get(tool_name), "block", redline, args)
        capability_id = self.tool_map.get(tool_name)
        if not capability_id:
            return self._event(tool_name, None, "block", "EDENA-UNMANIFESTED-TOOL", args)
        layers = [
            CapabilityLayer(
                name=item["name"],
                allow=None if item["allow"] is None else frozenset(item["allow"]),
                deny=frozenset(item["deny"]),
            )
            for item in self.config["layers"]
        ]
        context = CompilationContext(
            profile=self.config["profile"], audience=self.config["audience"],
            channel_trust=self.config["channel_trust"], provider=self.config["provider"],
            sandbox=self.config["sandbox"], no_phi=self.config["no_phi"],
            self_service=self.config["self_service"], gate_attested=self.config["gate_attested"],
        )
        result = compile_capabilities(self.manifests, {capability_id}, layers, context)
        if not result.ok or capability_id not in result.effective:
            reason = next((key for key, values in result.removed.items() if capability_id in values), "layer_restriction")
            return self._event(tool_name, capability_id, "block", f"EDENA-{reason.upper().replace('_', '-')}", args)
        manifest = self.manifests[capability_id]
        if manifest.side_effects:
            decision = "require_approval"
            reason = "EDENA-SIDE-EFFECT-APPROVAL"
        elif manifest.risk_tier is RiskTier.YELLOW:
            decision = "draft_only"
            reason = "EDENA-YELLOW-DRAFT"
        else:
            decision = "allow"
            reason = "EDENA-WITHIN-SCOPE"
        return self._event(tool_name, capability_id, decision, reason, args)

    def observe(self, tool_name: str = "", args: Any = None, **_: Any) -> None:
        try:
            event = self.evaluate(tool_name, args)
        except Exception as exc:
            event = self._event(tool_name, None, "block", "EDENA-EVALUATOR-ERROR", args)
            event["error_class"] = type(exc).__name__
        event["observed_decision"] = event.pop("decision")
        self._append(event)
        return None

    def enforce(self, tool_name: str = "", args: Any = None, **_: Any) -> dict[str, str] | None:
        try:
            event = self.evaluate(tool_name, args)
        except Exception as exc:
            event = self._event(tool_name, None, "block", "EDENA-EVALUATOR-ERROR", args)
            event["error_class"] = type(exc).__name__
        self._append(event)
        decision = event["decision"]
        if decision in {"allow", "draft_only"}:
            return None
        if decision == "require_approval":
            return {
                "action": "approve",
                "message": "EDENA requires meaningful human approval before this external side effect.",
                "rule_key": f"naio:{event['capability_id']}",
            }
        return {
            "action": "block",
            "message": f"Nurse AI OS blocked this action ({event['reason_code']}). No data was sent or changed.",
        }

    def _detect_redline(self, value: Any) -> str | None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).lower() in SENSITIVE_KEYS:
                    return "EDENA-REDLINE-SENSITIVE-FIELD"
                found = self._detect_redline(item)
                if found:
                    return found
        elif isinstance(value, (list, tuple)):
            for item in value:
                found = self._detect_redline(item)
                if found:
                    return found
        elif isinstance(value, str):
            if any(pattern.search(value) for pattern in SENSITIVE_PATTERNS):
                return "EDENA-REDLINE-SENSITIVE-CONTENT"
        return None

    def _event(self, tool_name: str, capability_id: str | None, decision: str, reason: str, args: Any) -> dict[str, Any]:
        return {
            "schema_version": "2.0.0",
            "event_id": secrets.token_hex(16),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": self.mode,
            "profile": self.config.get("profile", "unknown") if hasattr(self, "config") else "unknown",
            "tool_name": tool_name,
            "capability_id": capability_id,
            "decision": decision,
            "reason_code": reason,
            "argument_names": sorted(args) if isinstance(args, dict) else [],
            "payload_captured": False,
        }

    def _append(self, event: dict[str, Any]) -> None:
        ProvenanceLedger(self.log_path).append(event)


ShadowGate = RuntimeGate
