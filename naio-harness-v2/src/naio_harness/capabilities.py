from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .models import AutonomyLevel, CapabilityLayer, CapabilityManifest, CompilationContext, CompilationResult, RiskTier

MANIFEST_FIELDS = {
    "capability_id", "version", "capability_type", "source", "content_hash",
    "owner", "reviewer", "audiences", "risk_tier", "autonomy_ceiling",
    "data_classes", "tool_classes", "side_effects", "allowed_targets",
    "human_gate", "isolation", "budgets", "dependencies", "review_expires", "status",
}
REQUIRED_BUDGETS = {"max_calls", "timeout_seconds", "max_output_bytes"}


class ManifestError(ValueError):
    pass


def canonical_hash(payload: dict[str, Any]) -> str:
    unsigned = {key: value for key, value in payload.items() if key != "content_hash"}
    raw = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_manifest(path: Path) -> CapabilityManifest:
    payload = json.loads(path.read_text(encoding="utf-8"))
    unknown = set(payload) - MANIFEST_FIELDS
    missing = MANIFEST_FIELDS - set(payload)
    if unknown or missing:
        raise ManifestError(f"{path.name}: unknown={sorted(unknown)} missing={sorted(missing)}")
    if set(payload["budgets"]) != REQUIRED_BUDGETS:
        raise ManifestError(f"{path.name}: budgets must be exactly {sorted(REQUIRED_BUDGETS)}")
    if payload["content_hash"] != canonical_hash(payload):
        raise ManifestError(f"{path.name}: content_hash mismatch")
    try:
        return CapabilityManifest(
            capability_id=payload["capability_id"],
            version=payload["version"],
            capability_type=payload["capability_type"],
            source=payload["source"],
            content_hash=payload["content_hash"],
            owner=payload["owner"],
            reviewer=payload["reviewer"],
            audiences=tuple(payload["audiences"]),
            risk_tier=RiskTier(payload["risk_tier"]),
            autonomy_ceiling=AutonomyLevel(payload["autonomy_ceiling"]),
            data_classes=tuple(payload["data_classes"]),
            tool_classes=tuple(payload["tool_classes"]),
            side_effects=bool(payload["side_effects"]),
            allowed_targets=tuple(payload["allowed_targets"]),
            human_gate=payload["human_gate"],
            isolation=payload["isolation"],
            budgets={key: int(value) for key, value in payload["budgets"].items()},
            dependencies=tuple(payload["dependencies"]),
            review_expires=payload["review_expires"],
            status=payload["status"],
        )
    except (TypeError, ValueError) as exc:
        raise ManifestError(f"{path.name}: invalid value: {exc}") from exc


def load_manifests(directory: Path) -> dict[str, CapabilityManifest]:
    manifests: dict[str, CapabilityManifest] = {}
    for path in sorted(directory.glob("*.json")):
        manifest = load_manifest(path)
        if manifest.capability_id in manifests:
            raise ManifestError(f"duplicate capability_id: {manifest.capability_id}")
        manifests[manifest.capability_id] = manifest
    if not manifests:
        raise ManifestError("no capability manifests found")
    return manifests


def compile_capabilities(
    manifests: dict[str, CapabilityManifest],
    enabled: set[str],
    layers: list[CapabilityLayer],
    context: CompilationContext,
) -> CompilationResult:
    unknown = enabled - set(manifests)
    if unknown:
        return CompilationResult(set(), errors=[f"unmanifested capabilities: {sorted(unknown)}"])

    effective = set(enabled)
    removed: dict[str, list[str]] = {}
    trace: list[dict[str, Any]] = []

    def narrow(reason: str, identifiers: set[str]) -> None:
        actual = effective.intersection(identifiers)
        if actual:
            effective.difference_update(actual)
            removed.setdefault(reason, []).extend(sorted(actual))

    for layer in layers:
        before = set(effective)
        if layer.allow is not None:
            effective.intersection_update(layer.allow)
        effective.difference_update(layer.deny)
        trace.append({
            "layer": layer.name,
            "before": sorted(before),
            "after": sorted(effective),
            "removed": sorted(before - effective),
        })

    narrow("inactive_or_expired", {key for key, item in manifests.items() if item.status != "active"})
    narrow("audience_mismatch", {key for key, item in manifests.items() if context.audience not in item.audiences})
    narrow("red_risk", {key for key, item in manifests.items() if item.risk_tier is RiskTier.RED})
    if context.self_service:
        narrow("self_service_autonomy_ceiling", {key for key, item in manifests.items() if item.autonomy_ceiling.rank > 2})
    if context.no_phi:
        narrow("phi_data_class", {key for key, item in manifests.items() if "phi" in item.data_classes})
    if not context.gate_attested:
        narrow("gate_not_attested", {key for key, item in manifests.items() if item.side_effects})

    trace.append({"layer": "edena_runtime", "after": sorted(effective), "removed_by_reason": removed})
    return CompilationResult(effective=effective, removed=removed, trace=trace)
