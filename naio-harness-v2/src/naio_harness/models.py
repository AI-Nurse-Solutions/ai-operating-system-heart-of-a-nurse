from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class RiskTier(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"


class AutonomyLevel(str, Enum):
    A0 = "A0"
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"

    @property
    def rank(self) -> int:
        return int(self.value[1:])


@dataclass(frozen=True)
class CapabilityManifest:
    capability_id: str
    version: str
    capability_type: str
    source: str
    content_hash: str
    owner: str
    reviewer: str
    audiences: tuple[str, ...]
    risk_tier: RiskTier
    autonomy_ceiling: AutonomyLevel
    data_classes: tuple[str, ...]
    tool_classes: tuple[str, ...]
    side_effects: bool
    allowed_targets: tuple[str, ...]
    human_gate: str
    isolation: str
    budgets: dict[str, int]
    dependencies: tuple[str, ...]
    review_expires: str
    status: str


@dataclass(frozen=True)
class CapabilityLayer:
    name: str
    allow: frozenset[str] | None = None
    deny: frozenset[str] = frozenset()


@dataclass(frozen=True)
class CompilationContext:
    profile: str
    audience: str
    channel_trust: str
    provider: str
    sandbox: str
    no_phi: bool = True
    self_service: bool = True
    gate_attested: bool = False


@dataclass
class CompilationResult:
    effective: set[str]
    removed: dict[str, list[str]] = field(default_factory=dict)
    trace: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "effective": sorted(self.effective),
            "removed": {key: sorted(value) for key, value in sorted(self.removed.items())},
            "trace": self.trace,
            "errors": self.errors,
        }
