from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .capabilities import compile_capabilities, load_manifests
from .config_store import load_runtime_config
from .models import CapabilityLayer, CompilationContext, RiskTier


class ShadowGate:
    """Evaluate tool calls without changing Hermes behavior or storing payloads."""

    def __init__(self, root: Path, log_path: Path | None = None):
        self.root = root
        self.config = load_runtime_config(root / "config" / "runtime-profile.json")
        self.manifests = load_manifests(root / "manifests")
        self.tool_map = json.loads((root / "config" / "tool-map.json").read_text(encoding="utf-8"))
        self.log_path = log_path or Path(os.environ.get("NAIO_SHADOW_LOG", root / "state" / "shadow-events.jsonl"))

    def evaluate(self, tool_name: str, args: Any = None) -> dict[str, Any]:
        capability_id = self.tool_map.get(tool_name)
        if not capability_id:
            return self._event(tool_name, None, "would_block", "EDENA-UNMANIFESTED_TOOL", args)
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
            return self._event(tool_name, capability_id, "would_block", f"EDENA-{reason.upper()}", args)
        manifest = self.manifests[capability_id]
        if manifest.risk_tier is RiskTier.YELLOW:
            decision = "would_draft_only"
            reason = "EDENA-YELLOW-DRAFT"
        elif manifest.side_effects:
            decision = "would_require_approval"
            reason = "EDENA-SIDE-EFFECT-APPROVAL"
        else:
            decision = "would_allow"
            reason = "EDENA-WITHIN-SCOPE"
        return self._event(tool_name, capability_id, decision, reason, args)

    def observe(self, tool_name: str = "", args: Any = None, **_: Any) -> None:
        try:
            event = self.evaluate(tool_name, args)
        except Exception as exc:
            event = self._event(tool_name, None, "would_block", "EDENA-EVALUATOR-ERROR", args)
            event["error_class"] = type(exc).__name__
        self._append(event)
        return None

    def _event(self, tool_name: str, capability_id: str | None, decision: str, reason: str, args: Any) -> dict[str, Any]:
        return {
            "schema_version": "2.0.0-shadow",
            "event_id": secrets.token_hex(16),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "mode": "shadow",
            "profile": self.config.get("profile", "unknown") if hasattr(self, "config") else "unknown",
            "tool_name": tool_name,
            "capability_id": capability_id,
            "would_decide": decision,
            "reason_code": reason,
            "argument_names": sorted(args) if isinstance(args, dict) else [],
            "payload_captured": False,
        }

    def _append(self, event: dict[str, Any]) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True, separators=(",", ":")) + "\n")
