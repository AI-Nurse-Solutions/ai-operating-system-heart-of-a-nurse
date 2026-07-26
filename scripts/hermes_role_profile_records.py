"""Verified public-manifest records for governed Hermes MCP role profiles."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def companion_record(repo: Path, profile: str) -> dict:
    root = repo / "hermes-role-profiles"
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    matches = [record for record in manifest.get("profiles", []) if record.get("profile") == profile]
    if len(matches) != 1:
        raise ValueError(f"Expected one governed Hermes role profile record for {profile}")
    source = matches[0]
    relative = Path(source["download"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"Unsafe governed Hermes role profile path for {profile}")
    artifact = root / relative
    if not artifact.is_file():
        raise FileNotFoundError(artifact)
    if artifact.stat().st_size != source["bytes"] or _sha256(artifact) != source["sha256"]:
        raise ValueError(f"Governed Hermes role profile bytes changed for {profile}")
    if source.get("mcp_enabled_by_default") is not False or source.get("mcp_tools_exposed_by_default") != 0:
        raise ValueError(f"Unsafe governed Hermes role profile defaults for {profile}")
    return {
        "activation": "separate_explicit_post_card_approval",
        "activation_readiness": source["activation_readiness"],
        "bytes": source["bytes"],
        "download": f"/hermes-role-profiles/{source['download']}",
        "install_on_download": False,
        "mapping_classification": source["mapping_classification"],
        "mapping_condition": source["mapping_condition"],
        "mcp_enabled_by_default": False,
        "mcp_tools_exposed_by_default": 0,
        "profile": profile,
        "sha256": source["sha256"],
        "version": source["version"],
    }
