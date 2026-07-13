"""Hermes adapter for the NAIO EDENA runtime gate."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_GATE = None


def _mode() -> str:
    return os.environ.get("NAIO_EDENA_MODE", "shadow").strip().lower()


def _gate():
    global _GATE
    if _GATE is not None:
        return _GATE
    root = Path(os.environ["NAIO_HARNESS_ROOT"]).expanduser().resolve()
    source = root / "src"
    if str(source) not in sys.path:
        sys.path.insert(0, str(source))
    from naio_harness.runtime_gate import RuntimeGate
    _GATE = RuntimeGate(root, mode=_mode())
    return _GATE


def _on_pre_tool_call(tool_name: str = "", args=None, **kwargs):
    mode = _mode()
    if mode == "shadow":
        try:
            _gate().observe(tool_name=tool_name, args=args, **kwargs)
        except Exception:
            return None
        return None
    if mode != "enforce":
        return {
            "action": "block",
            "message": "Nurse AI OS blocked this action because NAIO_EDENA_MODE is invalid.",
        }
    try:
        return _gate().enforce(tool_name=tool_name, args=args, **kwargs)
    except Exception:
        return {
            "action": "block",
            "message": "Nurse AI OS blocked this action because the EDENA gate failed closed.",
        }


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
