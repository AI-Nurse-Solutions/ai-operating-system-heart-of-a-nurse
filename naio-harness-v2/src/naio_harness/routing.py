from __future__ import annotations

import json
from pathlib import Path


class RoutingError(RuntimeError):
    pass


class ModelRouterPolicy:
    def __init__(self, path: Path):
        self.policy = json.loads(path.read_text(encoding="utf-8"))

    def authorize_fallback(
        self,
        *,
        data_class: str,
        current_provider: str,
        fallback_provider: str,
        fallback_index: int,
        fallback_manifested: bool,
    ) -> dict[str, str | bool]:
        rules = self.policy["rules"]
        if data_class not in rules:
            raise RoutingError("unknown data class")
        if data_class == "phi":
            raise RoutingError("PHI model routing is blocked")
        if fallback_index > int(self.policy["max_fallbacks"]):
            raise RoutingError("fallback budget exceeded")
        if not fallback_manifested:
            raise RoutingError("fallback provider is unmanifested")
        provider_changed = current_provider != fallback_provider
        if provider_changed and rules[data_class]["provider_change"] == "denied":
            raise RoutingError("provider change denied for this data class")
        return {
            "allowed": True,
            "data_class": data_class,
            "provider_changed": provider_changed,
            "privacy_floor": rules[data_class]["privacy_floor"],
        }
