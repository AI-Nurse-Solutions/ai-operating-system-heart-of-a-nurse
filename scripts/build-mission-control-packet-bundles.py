#!/usr/bin/env python3
"""Build the committed installable role-packet bundles (Phases 2 through 4).

Runs after build-mission-control-manifests.py and owns
mission-control/packets/CHECKSUMS.sha256, which covers every committed
file under the packets tree (manifests and bundle contents alike).
Deterministic: running twice produces byte-identical output; CI rebuilds
twice and diffs.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "naio-integrations" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from naio_integrations.packet_builder import PacketBundleBuilder  # noqa: E402

PACKETS_ROOT = ROOT / "mission-control" / "packets"


def main() -> int:
    builder = PacketBundleBuilder()
    for path in builder.build_roles(PACKETS_ROOT):
        print(f"built {path.relative_to(ROOT)}")
    checksum_file = PACKETS_ROOT / "CHECKSUMS.sha256"
    lines = []
    for path in sorted(PACKETS_ROOT.rglob("*")):
        if path.is_file() and path != checksum_file:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            lines.append(f"{digest}  {path.relative_to(PACKETS_ROOT).as_posix()}")
    checksum_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"built {checksum_file.relative_to(ROOT)} ({len(lines)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
