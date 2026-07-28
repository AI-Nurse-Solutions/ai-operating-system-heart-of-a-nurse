#!/usr/bin/env python3
"""Build the committed Mission Control role-packet manifests.

Deterministic: running this twice produces byte-identical output, and CI
rebuilds twice and diffs. Manifests land in mission-control/packets/ with
a CHECKSUMS.sha256 covering every generated file.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "naio-integrations" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from naio_integrations.packets import PacketCatalog, render_manifest, verify_manifest  # noqa: E402

OUTPUT_ROOT = ROOT / "mission-control" / "packets"


def main() -> int:
    catalog = PacketCatalog()
    for role, manifest in sorted(catalog.build_all().items()):
        verify_manifest(manifest)
        target = OUTPUT_ROOT / role / "manifest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_manifest(manifest), encoding="utf-8")
        print(f"built {target.relative_to(ROOT)} ({manifest['integrity_checksum']})")
    # CHECKSUMS.sha256 for the packets tree is owned by
    # build-mission-control-packet-bundles.py, which runs after this
    # script and covers manifests and bundle contents alike.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
