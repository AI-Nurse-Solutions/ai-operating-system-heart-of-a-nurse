#!/usr/bin/env python3
"""Build the committed Mission Control synthetic example workspace.

Deterministic: the builder uses a fixed example clock, so running this
twice produces byte-identical output; CI rebuilds twice and diffs.
Output lands in mission-control/example-workspace/ with a
CHECKSUMS.sha256 covering every generated file.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "naio-integrations" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from naio_integrations.workspace import ExampleWorkspace  # noqa: E402

OUTPUT_ROOT = ROOT / "mission-control" / "example-workspace"


def main() -> int:
    workspace = ExampleWorkspace(OUTPUT_ROOT)
    workspace.remove()
    workspace.build()
    checksum_file = OUTPUT_ROOT / "CHECKSUMS.sha256"
    lines = []
    for path in sorted(OUTPUT_ROOT.rglob("*")):
        if path.is_file() and path != checksum_file:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
            print(f"built {path.relative_to(ROOT)}")
    checksum_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"built {checksum_file.relative_to(ROOT)} ({len(lines)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
