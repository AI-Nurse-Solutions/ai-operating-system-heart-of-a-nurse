#!/usr/bin/env python3
"""Idempotently rotate TEACH verifier portability and documented verification paths.

The governed TEACH ZIP is treated as data. This utility never executes bundled
artifact-controlled code and never installs or activates the package.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = REPO / "post-setup" / "downloads" / (
    "TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-"
    "Build-Kit-v1.0.0.zip"
)
ROOT = "TEACH-Nurse-Educator-Instructional-Designer-Mission-Control-Hermes-Build-Kit-v1.0.0"
OUTER_ZIP_ARGUMENT = f"../{DEFAULT_ZIP.name}"
BARE_COMMAND = "python3 tools/verify-build-kit.py --package ."
GOVERNED_COMMAND = f"{BARE_COMMAND} --zip {OUTER_ZIP_ARGUMENT}"
EXPECTED_MEMBER_COUNT = 121
MAX_MEMBER_BYTES = 32 * 1024 * 1024
MAX_EXPANDED_BYTES = 256 * 1024 * 1024
EXPECTED_ROTATED_BYTES = 6_820_684
EXPECTED_ROTATED_SHA256 = "39d7a83a79b6137d50b6b5da639cd44d0427e4e06e30fc9d7f3b19805b4080f3"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_infos(
    infos: list[zipfile.ZipInfo], *, expected_count: int = EXPECTED_MEMBER_COUNT
) -> None:
    """Reject unsafe archive metadata before any member payload is read."""
    names = [item.filename for item in infos]
    if len(infos) != expected_count:
        raise ValueError(f"TEACH ZIP member count mismatch: {len(infos)} != {expected_count}")
    if len(names) != len(set(names)):
        raise ValueError("TEACH ZIP contains duplicate entry names")
    if not names or {name.split("/", 1)[0] for name in names if name} != {ROOT}:
        raise ValueError("TEACH ZIP root is unexpected")
    normalized = {unicodedata.normalize("NFC", name).casefold() for name in names}
    if len(normalized) != len(names):
        raise ValueError("TEACH ZIP contains case/Unicode-colliding entry names")

    expanded_bytes = 0
    for item in infos:
        name = item.filename
        pure = PurePosixPath(name)
        mode = (item.external_attr >> 16) & 0o777777
        if (
            not name
            or name.startswith("/")
            or "\\" in name
            or "\x00" in name
            or ".." in pure.parts
            or any(":" in part for part in pure.parts)
            or name.rstrip("/") != pure.as_posix()
        ):
            raise ValueError(f"Unsafe TEACH ZIP path: {name!r}")
        if item.flag_bits & 0x1:
            raise ValueError(f"Encrypted TEACH ZIP member rejected: {name}")
        if (mode & 0o170000) == 0o120000:
            raise ValueError(f"TEACH ZIP symlink member rejected: {name}")
        if (mode & 0o170000) not in (0, 0o100000, 0o040000):
            raise ValueError(f"TEACH ZIP special-file member rejected: {name}")
        if item.file_size > MAX_MEMBER_BYTES:
            raise ValueError(f"TEACH ZIP member exceeds byte limit: {name}")
        expanded_bytes += item.file_size
        if expanded_bytes > MAX_EXPANDED_BYTES:
            raise ValueError("TEACH ZIP expanded bytes exceed limit")


def validate_archive(path: Path, *, require_rotated_identity: bool = False) -> None:
    """Run complete archive-as-data checks without executing bundled code."""
    with zipfile.ZipFile(path) as archive:
        validate_infos(archive.infolist())
        bad_crc = archive.testzip()
        if bad_crc is not None:
            raise ValueError(f"TEACH ZIP CRC failure: {bad_crc}")
    if require_rotated_identity:
        actual_bytes = path.stat().st_size
        actual_sha256 = sha256(path.read_bytes())
        if (actual_bytes, actual_sha256) != (
            EXPECTED_ROTATED_BYTES,
            EXPECTED_ROTATED_SHA256,
        ):
            raise ValueError(
                "Rotated TEACH ZIP identity mismatch: "
                f"bytes={actual_bytes} sha256={actual_sha256}"
            )


def load_entries(path: Path) -> tuple[list[zipfile.ZipInfo], dict[str, bytes], bytes]:
    validate_archive(path)
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        data = {item.filename: archive.read(item) for item in infos if not item.is_dir()}
        return infos, data, archive.comment


def replace_exact(text: str, old: str, new: str, label: str) -> str:
    if new in text and old not in text:
        return text
    if old not in text:
        raise ValueError(f"Required {label} anchor is missing")
    return text.replace(old, new, 1)


def rotate(path: Path) -> None:
    infos, data, comment = load_entries(path)
    prefix = ROOT + "/"
    manifest_path = prefix + "RELEASE-MANIFEST.json"
    checksum_path = prefix + "SHA256SUMS.txt"
    verifier_path = prefix + "tools/verify-build-kit.py"
    read_first_path = prefix + "README-FIRST.md"
    install_path = prefix + "INSTALL.md"
    start_here_path = prefix + "START_HERE.md"
    user_guide_path = prefix + "implementation/EDUCATOR-User-Installation-Guide.md"

    for required in (
        manifest_path,
        checksum_path,
        verifier_path,
        read_first_path,
        install_path,
        start_here_path,
        user_guide_path,
    ):
        if required not in data:
            raise ValueError(f"Required TEACH entry is missing: {required}")

    read_first = data[read_first_path].decode("utf-8")
    read_first = replace_exact(
        read_first,
        "2. Extract a working copy.\n3. From the extracted package root, run:\n\n"
        f"   ```text\n   {BARE_COMMAND}\n   ```",
        "2. Extract a working copy immediately beside the unchanged original ZIP.\n"
        "3. From the extracted package root, run:\n\n"
        f"   ```text\n   {GOVERNED_COMMAND}\n   ```",
        "README-FIRST verification",
    )
    data[read_first_path] = read_first.encode("utf-8")

    install = data[install_path].decode("utf-8")
    install = replace_exact(
        install,
        "Keep an unchanged copy of the versioned ZIP. Extract a working copy and run from its root:\n\n"
        f"```text\n{BARE_COMMAND}\n```\n\n"
        "If the versioned ZIP is beside the extracted directory, Hermes may also verify the archive with the exact filename shown in the release handoff:\n\n"
        "```text\npython3 tools/verify-build-kit.py --package . --zip ../<versioned-build-kit>.zip\n```",
        "Keep the unchanged original ZIP immediately beside the extracted package folder. "
        "From the extracted package root, verify both the working copy and authoritative outer-ZIP metadata:\n\n"
        f"```text\n{GOVERNED_COMMAND}\n```",
        "INSTALL verification",
    )
    data[install_path] = install.encode("utf-8")

    start_here = data[start_here_path].decode("utf-8")
    start_here = replace_exact(
        start_here,
        "1. Save the original ZIP unchanged.\n"
        "2. Do not add learner, patient, employee, or confidential institutional information.\n"
        "3. Extract a working copy and verify it:\n\n"
        f"   ```text\n   {BARE_COMMAND}\n   ```",
        "1. Save the original ZIP unchanged.\n"
        "2. Do not add learner, patient, employee, or confidential institutional information.\n"
        "3. Extract a working copy immediately beside the unchanged ZIP and verify it:\n\n"
        f"   ```text\n   {GOVERNED_COMMAND}\n   ```",
        "START_HERE verification",
    )
    data[start_here_path] = start_here.encode("utf-8")

    user_guide = data[user_guide_path].decode("utf-8")
    user_guide = replace_exact(
        user_guide,
        "1. Keep the original versioned ZIP unchanged.\n"
        "2. Extract a working copy in a private folder.\n"
        "3. Open a terminal in the extracted package root and run:\n\n"
        f"   ```text\n   {BARE_COMMAND}\n   ```",
        "1. Keep the original versioned ZIP unchanged.\n"
        "2. Extract a working copy immediately beside the unchanged ZIP in a private folder.\n"
        "3. Open a terminal in the extracted package root and run:\n\n"
        f"   ```text\n   {GOVERNED_COMMAND}\n   ```",
        "educator user-guide verification",
    )
    data[user_guide_path] = user_guide.encode("utf-8")

    verifier = data[verifier_path].decode("utf-8")
    if "import os\n" not in verifier:
        verifier = replace_exact(verifier, "import json\n", "import json\nimport os\n", "verifier os import")

    old_mode_function = "def check_modes(c: Checks, package: Path) -> None:"
    new_mode_function = "def check_modes(c: Checks, package: Path, enforce_modes: bool) -> None:"
    if new_mode_function not in verifier:
        verifier = replace_exact(verifier, old_mode_function, new_mode_function, "mode function")

    old_mode_result = '    c.check(not bad, "Package modes are normalized and not group/world writable", bad[:30])'
    new_mode_result = (
        '    if enforce_modes:\n'
        '        c.check(not bad, "Package modes are normalized and not group/world writable", bad[:30])\n'
        '    elif bad:\n'
        '        c.warn("Extracted filesystem modes are non-authoritative; outer-ZIP modes remain mandatory", bad[:30])\n'
        '    else:\n'
        '        c.check(True, "Package modes are normalized and not group/world writable")'
    )
    if new_mode_result not in verifier:
        verifier = replace_exact(verifier, old_mode_result, new_mode_result, "mode result")

    old_mode_call = "    check_modes(c, package)"
    new_mode_call = '    check_modes(c, package, enforce_modes=args.zip_path is None and os.name != "nt")'
    if new_mode_call not in verifier:
        verifier = replace_exact(verifier, old_mode_call, new_mode_call, "mode call")
    data[verifier_path] = verifier.encode("utf-8")

    manifest = json.loads(data[manifest_path])
    excluded = {manifest_path, checksum_path}
    files = []
    for full_name in sorted(name for name in data if name not in excluded):
        relative = full_name.removeprefix(prefix)
        if relative == full_name:
            raise ValueError(f"Entry escaped TEACH root: {full_name}")
        payload = data[full_name]
        files.append({"bytes": len(payload), "path": relative, "sha256": sha256(payload)})
    manifest["files_excluding_manifest_and_checksums"] = files
    data[manifest_path] = (
        json.dumps(manifest, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")

    checksum_lines = []
    for full_name in sorted(name for name in data if name != checksum_path):
        relative = full_name.removeprefix(prefix)
        checksum_lines.append(f"{sha256(data[full_name])}  {relative}")
    data[checksum_path] = ("\n".join(checksum_lines) + "\n").encode("utf-8")

    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    os.close(fd)
    temp = Path(temp_name)
    try:
        with zipfile.ZipFile(temp, "w", allowZip64=True) as output:
            output.comment = comment
            for original in infos:
                info = copy.copy(original)
                payload = b"" if original.is_dir() else data[original.filename]
                kwargs = {"compresslevel": 9} if info.compress_type == zipfile.ZIP_DEFLATED else {}
                output.writestr(info, payload, compress_type=info.compress_type, **kwargs)
        validate_archive(temp, require_rotated_identity=True)
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

    print(f"TEACH_VERIFIER_PORTABILITY_ROTATED={path}")
    print(f"TEACH_ZIP_BYTES={path.stat().st_size}")
    print(f"TEACH_ZIP_SHA256={sha256(path.read_bytes())}")
    print(f"TEACH_VERIFIER_SHA256={sha256(data[verifier_path])}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args()
    rotate(args.zip.resolve())


if __name__ == "__main__":
    main()
