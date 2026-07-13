from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


class ConfigError(ValueError):
    pass


RUNTIME_FIELDS = {
    "schema_version", "profile", "audience", "channel_trust", "provider",
    "sandbox", "no_phi", "self_service", "gate_attested", "enabled_capabilities", "layers",
}
LAYER_FIELDS = {"name", "allow", "deny"}


def validate_runtime_config(payload: dict[str, Any]) -> None:
    unknown = set(payload) - RUNTIME_FIELDS
    missing = RUNTIME_FIELDS - set(payload)
    if unknown or missing:
        raise ConfigError(f"runtime config unknown={sorted(unknown)} missing={sorted(missing)}")
    if payload["schema_version"] != "2.0.0":
        raise ConfigError("unsupported schema_version")
    if not isinstance(payload["enabled_capabilities"], list) or not payload["enabled_capabilities"]:
        raise ConfigError("enabled_capabilities must be a non-empty list")
    if not isinstance(payload["layers"], list) or not payload["layers"]:
        raise ConfigError("layers must be a non-empty list")
    for layer in payload["layers"]:
        if set(layer) != LAYER_FIELDS:
            raise ConfigError(f"layer fields must be exactly {sorted(LAYER_FIELDS)}")
        if layer["allow"] is not None and not isinstance(layer["allow"], list):
            raise ConfigError("layer allow must be null or list")
        if not isinstance(layer["deny"], list):
            raise ConfigError("layer deny must be list")


def load_runtime_config(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot load runtime config: {exc}") from exc
    validate_runtime_config(payload)
    return payload


class StrictConfigStore:
    def __init__(self, active: Path, validator: Callable[[dict[str, Any]], None] = validate_runtime_config):
        self.active = active
        self.validator = validator
        self.last_good = active.with_suffix(active.suffix + ".last-good")
        self.rejected_dir = active.parent / "rejected"

    def apply(self, candidate: dict[str, Any]) -> Path:
        try:
            self.validator(candidate)
        except Exception:
            self._preserve_rejected(candidate)
            raise
        self.active.parent.mkdir(parents=True, exist_ok=True)
        if self.active.exists():
            self.last_good.write_bytes(self.active.read_bytes())
        raw = json.dumps(candidate, indent=2, sort_keys=True).encode() + b"\n"
        fd, temporary = tempfile.mkstemp(prefix=self.active.name + ".", dir=self.active.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(raw)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.active)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return self.active

    def _preserve_rejected(self, candidate: dict[str, Any]) -> Path:
        self.rejected_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        path = self.rejected_dir / f"candidate-{stamp}.json"
        path.write_text(json.dumps(candidate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path
