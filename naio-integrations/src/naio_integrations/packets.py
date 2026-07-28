"""Mission Control packet manifest generator (dashboard spec section 14).

Every role packet ships with a machine-readable manifest: packet name and
version, role modules enabled, required and optional dependencies,
default agents, default permissions, prohibited data classes, supported
exports, migration version, and an integrity checksum.

Roles are configuration plus modules, never a forked application: the
catalog in ``config/mission-control-packets.json`` is the single source
of truth, and every packet embeds the same shared core.

Safe-by-default invariants are enforced at generation AND at
verification, so a hand-edited manifest that weakens them fails closed:

* default permissions start empty ("start with none");
* every starter agent ships tools-disabled, propose-only, Green tier;
* D3 and D4 data are prohibited in the personal edition;
* installation never implies institutional approval.

Manifests are deterministic: identical catalog in, byte-identical
manifest out. No timestamps, no randomness.

Trust model: the integrity checksum detects corruption and accidental
drift; it is not an authenticity proof, since anyone who edits a
manifest can recompute it. Authenticity comes from git provenance plus
the CI determinism gate (manifests are rebuilt from the reviewed
catalog and any diff fails), and the safe-by-default invariants below
are verified independently of the checksum, so even a re-checksummed
manifest cannot smuggle unsafe defaults past ``verify_manifest``.
Detached release signing (the naio-os release-key pattern) is the
institutional-distribution path and deliberately out of scope here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contract import DataClass, DataZone, RiskTier

DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parents[2] / "config" / "mission-control-packets.json"
)

MANIFEST_SCHEMA_VERSION = "1.0.0"

REQUIRED_MANIFEST_FIELDS = (
    "manifest_schema",
    "packet_name",
    "display_name",
    "packet_version",
    "role",
    "role_modules",
    "required_dependencies",
    "optional_dependencies",
    "default_agents",
    "default_permissions",
    "integrations_enabled_by_default",
    "prohibited_data_classes",
    "prohibited_data_note",
    "supported_exports",
    "migration_version",
    "governance",
    "integrity_checksum",
)


class PacketIntegrityError(ValueError):
    """A manifest is missing, malformed, tampered with, or unsafe."""


def _canonical(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_checksum(manifest: dict[str, Any]) -> str:
    unsigned = {k: v for k, v in manifest.items() if k != "integrity_checksum"}
    return "sha256:" + hashlib.sha256(_canonical(unsigned)).hexdigest()


class PacketCatalog:
    """Loads the packet catalog and generates verified role manifests."""

    def __init__(self, catalog_path: Path | None = None):
        path = catalog_path or DEFAULT_CATALOG_PATH
        self.catalog: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))

    def roles(self) -> tuple[str, ...]:
        return tuple(sorted(self.catalog["packets"]))

    def build_manifest(self, role: str) -> dict[str, Any]:
        packets = self.catalog["packets"]
        if role not in packets:
            raise PacketIntegrityError(f"unknown role packet: {role}")
        packet = packets[role]
        agent_roster = self.catalog["agents"]
        default_agents = []
        for agent_id in packet["default_agents"]:
            if agent_id not in agent_roster:
                raise PacketIntegrityError(f"unknown agent in catalog: {agent_id}")
            default_agents.append(
                {
                    "agent_id": agent_id,
                    "purpose": agent_roster[agent_id],
                    "edena_tier": RiskTier.GREEN.value,
                    "tools_enabled": False,
                    "actions_may_execute": [],
                    "required_review": "every_output",
                }
            )
        manifest: dict[str, Any] = {
            "manifest_schema": MANIFEST_SCHEMA_VERSION,
            "packet_name": f"nurse-ai-os-mission-control-{role}",
            "display_name": packet["display_name"],
            "packet_version": self.catalog["packet_version"],
            "role": role,
            "role_modules": list(self.catalog["shared_modules"])
            + list(packet["role_modules"]),
            "required_dependencies": list(self.catalog["required_dependencies"]),
            "optional_dependencies": list(self.catalog["optional_dependencies"]),
            "default_agents": default_agents,
            "default_permissions": [],
            "integrations_enabled_by_default": False,
            "prohibited_data_classes": list(self.catalog["prohibited_data_classes"]),
            "prohibited_data_note": self.catalog["prohibited_data_note"],
            "supported_exports": list(self.catalog["supported_exports"]),
            "migration_version": self.catalog["migration_version"],
            "governance": {
                "directive": self.catalog["directive"],
                "default_risk_tier": RiskTier.GREEN.value,
                "default_data_zone": DataZone.PRIVATE.value,
                "institutional_approval_granted": False,
                "install_note": self.catalog["install_note"],
            },
        }
        manifest["integrity_checksum"] = compute_checksum(manifest)
        verify_manifest(manifest)
        return manifest

    def build_all(self) -> dict[str, dict[str, Any]]:
        return {role: self.build_manifest(role) for role in self.roles()}


def render_manifest(manifest: dict[str, Any]) -> str:
    """Stable on-disk form: sorted keys, two-space indent, trailing newline."""
    return json.dumps(manifest, sort_keys=True, indent=2) + "\n"


def verify_manifest(manifest: dict[str, Any]) -> None:
    """Fail closed on any missing field, checksum mismatch, or unsafe default."""
    missing = [f for f in REQUIRED_MANIFEST_FIELDS if f not in manifest]
    if missing:
        raise PacketIntegrityError(f"manifest missing required fields: {missing}")
    if manifest["integrity_checksum"] != compute_checksum(manifest):
        raise PacketIntegrityError("integrity checksum mismatch")
    if manifest["default_permissions"] != []:
        raise PacketIntegrityError("packets must start with no default permissions")
    if manifest["integrations_enabled_by_default"] is not False:
        raise PacketIntegrityError("integrations must be off by default")
    for data_class in (DataClass.D3.value, DataClass.D4.value):
        if data_class not in manifest["prohibited_data_classes"]:
            raise PacketIntegrityError(
                f"personal edition must prohibit {data_class} data"
            )
    for module in ("edena-guardrails", "data-boundary-notice", "mission-control-core"):
        if module not in manifest["role_modules"]:
            raise PacketIntegrityError(f"packet is missing the shared core module {module}")
    if not manifest["default_agents"]:
        raise PacketIntegrityError("a packet must ship at least one starter agent")
    for agent in manifest["default_agents"]:
        if agent.get("tools_enabled") is not False:
            raise PacketIntegrityError(
                f"starter agent {agent.get('agent_id')} must ship tools-disabled"
            )
        if agent.get("actions_may_execute") != []:
            raise PacketIntegrityError(
                f"starter agent {agent.get('agent_id')} must be propose-only"
            )
        if agent.get("edena_tier") != RiskTier.GREEN.value:
            raise PacketIntegrityError(
                f"starter agent {agent.get('agent_id')} must start at Green"
            )
    governance = manifest["governance"]
    if governance.get("default_risk_tier") != RiskTier.GREEN.value:
        raise PacketIntegrityError("packets must default to the Green tier")
    if governance.get("default_data_zone") != DataZone.PRIVATE.value:
        raise PacketIntegrityError("packets must default to the private data zone")
    if governance.get("institutional_approval_granted") is not False:
        raise PacketIntegrityError(
            "packets must declare institutional_approval_granted: false"
        )
    if not governance.get("install_note", "").strip():
        raise PacketIntegrityError(
            "the install note explaining that installation is not approval is required"
        )
