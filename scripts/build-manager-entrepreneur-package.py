#!/usr/bin/env python3
"""Build downloads/manager-entrepreneur-mission-control.zip.

The package is assembled from files that already live in this repo, so it
cannot drift from them:

- managers-entrepreneurs/starter/*          (README, handoff prompt, cheatsheet, board)
- mission-control/packets/leader/**         (the real leader Mission Control packet)
- assets/nurse-ai-side-gig-starter-kit.zip  (the venture kit, re-packed under venture/)

The archive is deterministic (fixed timestamps, sorted entries) and carries a
CHECKSUMS.sha256 covering every file. That is a checksum, not a signature.

    python3 scripts/build-manager-entrepreneur-package.py          # build
    python3 scripts/build-manager-entrepreneur-package.py --check  # exit 1 if stale
"""
from __future__ import annotations

import hashlib
import io
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "downloads" / "manager-entrepreneur-mission-control.zip"
TOP = "manager-entrepreneur-mission-control"
STAMP = (2026, 10, 13, 0, 0, 0)


def collect() -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    starter = ROOT / "managers-entrepreneurs" / "starter"
    for p in sorted(starter.iterdir()):
        if p.is_file():
            files[p.name] = p.read_bytes()
    packet = ROOT / "mission-control" / "packets" / "leader"
    for p in sorted(packet.rglob("*")):
        if p.is_file():
            files[f"mission-control-packet/leader/{p.relative_to(packet).as_posix()}"] = p.read_bytes()
    kit = ROOT / "assets" / "nurse-ai-side-gig-starter-kit.zip"
    with zipfile.ZipFile(kit) as z:
        for name in sorted(z.namelist()):
            if name.endswith("/"):
                continue
            files[f"venture/{Path(name).name}"] = z.read(name)
    sums = "".join(
        f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items())
    )
    files["CHECKSUMS.sha256"] = sums.encode()
    return files


def build() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in sorted(collect().items()):
            info = zipfile.ZipInfo(f"{TOP}/{name}", STAMP)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, data)
    return buf.getvalue()


def main() -> int:
    data = build()
    if "--check" in sys.argv:
        if not OUT.is_file() or OUT.read_bytes() != data:
            print(f"{OUT.relative_to(ROOT)} is stale; rebuild it", file=sys.stderr)
            return 1
        print("package is current")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)
    print(f"wrote {OUT.relative_to(ROOT)} ({len(data)} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
