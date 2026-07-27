"""Verified public-manifest records for governed Hermes MCP role profiles."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from pathlib import Path


def _read_regular_within(root: Path, relative: Path) -> bytes:
    if relative.is_absolute() or not relative.parts or any(part in {"", ".", ".."} for part in relative.parts):
        raise ValueError(f"Unsafe governed Hermes role profile path: {relative}")
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise RuntimeError("Descriptor-relative no-follow artifact reads are unavailable")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    descriptors: list[int] = []
    try:
        try:
            descriptors.append(os.open(root, directory_flags))
            for part in relative.parts[:-1]:
                descriptors.append(os.open(part, directory_flags, dir_fd=descriptors[-1]))
                if not stat.S_ISDIR(os.fstat(descriptors[-1]).st_mode):
                    raise ValueError(f"Non-directory governed artifact path component: {relative}")
            descriptors.append(os.open(relative.parts[-1], file_flags, dir_fd=descriptors[-1]))
        except OSError as exc:
            raise ValueError(f"Unable to open governed artifact beneath its root: {relative}") from exc
        descriptor = descriptors[-1]
        mode = os.fstat(descriptor).st_mode
        if not stat.S_ISREG(mode):
            raise ValueError(f"Governed Hermes role profile artifact is not a regular file: {relative}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            return handle.read()
    finally:
        for opened in reversed(descriptors):
            os.close(opened)


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
    try:
        artifact_bytes = _read_regular_within(root, relative)
    except FileNotFoundError as exc:
        raise FileNotFoundError(root / relative) from exc
    if len(artifact_bytes) != source["bytes"] or hashlib.sha256(artifact_bytes).hexdigest() != source["sha256"]:
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
