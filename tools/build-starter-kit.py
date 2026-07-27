#!/usr/bin/env python3
"""Build the public Nurse AI OS starter-kit ZIP deterministically and fail closed."""

from __future__ import annotations

import os
import stat
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "starter-kit" / "My-Nurse-AI-OS"
OUTPUT = ROOT / "assets" / "nurse-ai-os-starter-kit.zip"
PREFIX = "My-Nurse-AI-OS"
SIDE_GIG_SOURCE = SOURCE / "03-Community-Entrepreneurship" / "Nurse-AI-Side-Gig-Starter-Kit"
SIDE_GIG_OUTPUT = ROOT / "assets" / "nurse-ai-side-gig-starter-kit.zip"
SIDE_GIG_PREFIX = "Nurse-AI-Side-Gig-Starter-Kit"
FIXED_TIME = (2026, 7, 25, 0, 0, 0)


def source_files(source: Path | None = None) -> list[Path]:
    source = SOURCE if source is None else source
    source_mode = source.lstat().st_mode
    if stat.S_ISLNK(source_mode) or not stat.S_ISDIR(source_mode):
        raise RuntimeError(f"starter-kit source root must be a real directory: {source}")
    files: list[Path] = []
    for path in sorted(source.rglob("*"), key=lambda item: item.relative_to(source).as_posix()):
        relative = path.relative_to(source)
        if any(part.startswith(".") for part in relative.parts):
            raise RuntimeError(f"hidden starter-kit source entry refused: {relative.as_posix()}")
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise RuntimeError(f"starter-kit source symlink refused: {relative.as_posix()}")
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            raise RuntimeError(f"starter-kit special source entry refused: {relative.as_posix()}")
        files.append(path)
    if not files:
        raise RuntimeError("starter-kit source tree is empty")
    return files


def read_source(path: Path, source: Path | None = None) -> bytes:
    source = SOURCE if source is None else source
    relative = path.relative_to(source)
    cursor = source
    for part in relative.parts:
        cursor = cursor / part
        if stat.S_ISLNK(cursor.lstat().st_mode):
            raise RuntimeError(f"starter-kit source symlink refused: {relative.as_posix()}")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise RuntimeError(f"starter-kit source is not a regular file: {relative.as_posix()}")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            return handle.read()
    finally:
        os.close(descriptor)


def build_tree(source: Path, output: Path, prefix: str) -> int:
    files = source_files(source)
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in files:
                relative = path.relative_to(source).as_posix()
                info = zipfile.ZipInfo(f"{prefix}/{relative}", FIXED_TIME)
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(
                    info,
                    read_source(path, source),
                    compress_type=zipfile.ZIP_DEFLATED,
                    compresslevel=9,
                )
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()
    return len(files)


def build(output: Path = OUTPUT) -> None:
    count = build_tree(SOURCE, output, PREFIX)
    print(f"STARTER_KIT_BUILT files={count} output={output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")


def build_side_gig(output: Path = SIDE_GIG_OUTPUT) -> None:
    count = build_tree(SIDE_GIG_SOURCE, output, SIDE_GIG_PREFIX)
    print(f"SIDE_GIG_KIT_BUILT files={count} output={output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")


if __name__ == "__main__":
    build()
    build_side_gig()
