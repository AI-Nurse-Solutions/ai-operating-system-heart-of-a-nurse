#!/usr/bin/env python3
"""Load the NAIO plugin through Hermes's real plugin manager in a temporary home."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--harness-root", type=Path, required=True)
    parser.add_argument("--hermes-source", type=Path, required=True)
    args = parser.parse_args()
    root = args.harness_root.resolve()
    hermes = args.hermes_source.resolve()

    with tempfile.TemporaryDirectory() as tmp:
        home = Path(tmp) / "hermes-canary"
        plugin_target = home / "plugins" / "naio-edena-runtime"
        plugin_target.parent.mkdir(parents=True)
        shutil.copytree(root / "hermes-plugin" / "naio-edena-runtime", plugin_target)
        (home / "config.yaml").write_text(
            "plugins:\n  enabled:\n    - naio-edena-runtime\n",
            encoding="utf-8",
        )
        log = Path(tmp) / "events.jsonl"
        os.environ.update({
            "HERMES_HOME": str(home),
            "NAIO_HARNESS_ROOT": str(root),
            "NAIO_EDENA_MODE": "enforce",
            "NAIO_RUNTIME_CONFIG": str(root / "config" / "runtime-profile-enforce.json"),
            "NAIO_SHADOW_LOG": str(log),
        })
        sys.path.insert(0, str(hermes))
        sys.path.insert(0, str(root / "src"))
        from hermes_cli import plugins

        plugins.discover_plugins(force=True)
        checks = {
            "read": plugins.get_pre_tool_call_directive("read_file", {"path": "public.md"})[0],
            "unknown": plugins.get_pre_tool_call_directive("unknown_power", {})[0],
            "external": plugins.get_pre_tool_call_directive("send_message", {"text": "public"})[0],
            "phi": plugins.get_pre_tool_call_directive("write_file", {"content": "MRN: ABCD1234"})[0],
        }
        expected = {"read": None, "unknown": "block", "external": "approve", "phi": "block"}
        event_count = len(log.read_text().splitlines()) if log.exists() else 0
        output = {"ok": checks == expected and event_count == 4, "checks": checks, "expected": expected, "event_count": event_count}
        print(json.dumps(output, indent=2, sort_keys=True))
        return 0 if output["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
