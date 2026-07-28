#!/usr/bin/env python3
"""Build the committed Mission Control role-packet manifests.

Deterministic: running this twice produces byte-identical output, and CI
rebuilds twice and diffs. Manifests land in mission-control/packets/ with
a CHECKSUMS.sha256 covering every generated file.
"""

from __future__ import annotations

import hashlib
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
    written: list[Path] = []
    for role, manifest in sorted(catalog.build_all().items()):
        verify_manifest(manifest)
        target = OUTPUT_ROOT / role / "manifest.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_manifest(manifest), encoding="utf-8")
        written.append(target)
        print(f"built {target.relative_to(ROOT)} ({manifest['integrity_checksum']})")
    checksum_lines = []
    for path in written:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        checksum_lines.append(f"{digest}  {path.relative_to(OUTPUT_ROOT).as_posix()}")
    checksum_file = OUTPUT_ROOT / "CHECKSUMS.sha256"
    checksum_file.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")
    print(f"built {checksum_file.relative_to(ROOT)} ({len(written)} manifests)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
