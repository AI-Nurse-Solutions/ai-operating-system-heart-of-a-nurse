from __future__ import annotations

import json
from pathlib import Path

from .models import CapabilityLayer


class TrustCellError(RuntimeError):
    pass


class TrustCells:
    def __init__(self, path: Path):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if set(payload) != {"schema_version", "cells", "invariants"}:
            raise TrustCellError("trust-cell configuration fields are missing or unknown")
        if payload["invariants"].get("child_may_regrant") is not False:
            raise TrustCellError("child_may_regrant must be false")
        self.cells = payload["cells"]

    def layer(self, name: str, parent_effective: set[str] | None = None) -> CapabilityLayer:
        if name not in self.cells:
            raise TrustCellError("unknown trust cell")
        cell = self.cells[name]
        allowed = set(cell["allow"])
        if parent_effective is not None:
            allowed.intersection_update(parent_effective)
        return CapabilityLayer(name=f"trust-cell:{name}", allow=frozenset(allowed), deny=frozenset(cell["deny"]))
