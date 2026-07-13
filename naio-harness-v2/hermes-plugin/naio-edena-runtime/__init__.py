"""Hermes adapter for the NAIO EDENA runtime gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_GATE = None


def _gate():
    global _GATE
    if _GATE is not None:
        return _GATE
    root = Path(os.environ["NAIO_HARNESS_ROOT"]).expanduser().resolve()
    source = root / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from naio_harness.runtime_gate import ShadowGate
    _GATE = ShadowGate(root)
    return _GATE


def _on_pre_tool_call(tool_name: str = "", args=None, **kwargs):
    # Shadow mode is deliberately observational. It always returns None.
    try:
        _gate().observe(tool_name=tool_name, args=args, **kwargs)
    except Exception:
        # Stage 2 must not change Hermes behavior. Stage 3 replaces this with
        # fail-closed directives after canary verification.
        return None
    return None


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
