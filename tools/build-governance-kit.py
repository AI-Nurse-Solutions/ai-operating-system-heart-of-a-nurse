#!/usr/bin/env python3
"""Build the public Governance Kit ZIP deterministically from reviewed sources."""

from __future__ import annotations

import os
import stat
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "governance-kit"
OUTPUT = ROOT / "assets" / "governance-kit.zip"
FIXED_ZIP_TIME = (2026, 7, 25, 0, 0, 0)


def source_files() -> list[Path]:
    if SOURCE.is_symlink():
        raise RuntimeError("governance-kit source root must not be a symlink")

    files: list[Path] = []
    for path in sorted(SOURCE.rglob("*"), key=lambda candidate: candidate.relative_to(SOURCE).as_posix()):
        relative = path.relative_to(SOURCE)
        if any(part.startswith(".") for part in relative.parts):
            raise RuntimeError(f"hidden governance-kit source entry is prohibited: {relative}")
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"governance-kit source symlink is prohibited: {relative}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise RuntimeError(f"governance-kit source must be a regular file: {relative}")
        files.append(path)
    return files


def read_regular_source(path: Path) -> bytes:
    relative = path.relative_to(SOURCE)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"unable to open regular governance-kit source: {relative}") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError(f"governance-kit source changed type before read: {relative}")
        with os.fdopen(descriptor, "rb") as source:
            descriptor = -1
            return source.read()
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def build(output: Path = OUTPUT) -> None:
    files = source_files()
    if not files:
        raise RuntimeError("governance-kit source directory is empty")

    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                member = path.relative_to(SOURCE).as_posix()
                info = zipfile.ZipInfo(member, FIXED_ZIP_TIME)
                info.create_system = 3
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(
                    info,
                    read_regular_source(path),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    build()
    print(f"GOVERNANCE_KIT_BUILT files={len(source_files())} output={OUTPUT.relative_to(ROOT)}")
