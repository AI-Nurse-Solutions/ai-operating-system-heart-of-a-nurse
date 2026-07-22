#!/usr/bin/env python3
"""Idempotently embed and verify the WINGS United States availability boundary.

This script rotates the governed prebuilt WINGS ZIP as data. It does not execute
artifact-controlled code and does not install or activate the package.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

REPO = Path(__file__).resolve().parents[1]
DEFAULT_ZIP = REPO / "post-setup" / "downloads" / (
    "WINGS-Nurse-Practitioner-Complete-AI-OS-Mission-Control-Hermes-"
    "Build-Kit-v1.0.0.zip"
)
ROOT = "WINGS-Nurse-Practitioner-Complete-AI-OS-Mission-Control-Hermes-Build-Kit-v1.0.0"
COUNTRIES = ["United States"]
BOUNDARY = (
    "Availability boundary: this build kit is available only in the United States. "
    "If the target user or intended use is outside the United States, stop before "
    "build mutation and route to a separately governed local-jurisdiction review. "
    "This package confers no licensure, clinical authority, or institutional authorization."
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def add_after(text: str, anchor: str, addition: str) -> str:
    if addition in text:
        return text
    if anchor not in text:
        raise ValueError(f"Required patch anchor is missing: {anchor!r}")
    return text.replace(anchor, anchor + "\n\n" + addition, 1)


def load_entries(path: Path) -> tuple[list[zipfile.ZipInfo], dict[str, bytes], bytes]:
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        if len(names) != len(set(names)):
            raise ValueError("WINGS ZIP contains duplicate entry names")
        if not names or names[0].split("/", 1)[0] != ROOT:
            raise ValueError("WINGS ZIP root is unexpected")
        for name in names:
            pure = PurePosixPath(name)
            if pure.is_absolute() or ".." in pure.parts or "\\" in name:
                raise ValueError(f"Unsafe WINGS ZIP path: {name}")
        data = {item.filename: archive.read(item) for item in infos if not item.is_dir()}
        return infos, data, archive.comment


def rotate(path: Path) -> None:
    infos, data, comment = load_entries(path)
    prefix = ROOT + "/"

    read_first = prefix + "README-FIRST.md"
    give = prefix + "GIVE-THIS-PACKAGE-TO-HERMES.md"
    manifest_path = prefix + "RELEASE-MANIFEST.json"
    checksum_path = prefix + "SHA256SUMS.txt"
    verifier_path = prefix + "tools/verify-build-kit.py"

    for required in (read_first, give, manifest_path, checksum_path, verifier_path):
        if required not in data:
            raise ValueError(f"Required WINGS entry is missing: {required}")

    read_text = data[read_first].decode("utf-8")
    read_text = add_after(
        read_text,
        "# Read Me First — instruction for Hermes",
        BOUNDARY,
    )
    data[read_first] = read_text.encode("utf-8")

    give_text = data[give].decode("utf-8")
    give_text = add_after(
        give_text,
        "You are the implementation engineer for `NAIO-NP-WINGS-FUNCTIONAL-BUILD-KIT-1.0.0`.",
        BOUNDARY,
    )
    data[give] = give_text.encode("utf-8")

    verifier = data[verifier_path].decode("utf-8")
    old_target = (
        'target == {"foundation_namespace": FOUNDATION_NAMESPACE, "home": HOME, '
        '"lane": LANE, "namespace": NAMESPACE, "product": "NP WINGS — Nurse '
        'Practitioner Life, Practice & Purpose Mission Control", "product_id": '
        'PRODUCT_ID, "readiness": "not_operational_build_required", "route": ROUTE, '
        '"version": "2.0.0"}'
    )
    new_target = (
        'target == {"country_availability": ["United States"], '
        '"foundation_namespace": FOUNDATION_NAMESPACE, "home": HOME, "lane": LANE, '
        '"namespace": NAMESPACE, "product": "NP WINGS — Nurse Practitioner Life, '
        'Practice & Purpose Mission Control", "product_id": PRODUCT_ID, "readiness": '
        '"not_operational_build_required", "route": ROUTE, "version": "2.0.0"}'
    )
    if new_target not in verifier:
        if old_target not in verifier:
            raise ValueError("Bundled verifier target assertion anchor is missing")
        verifier = verifier.replace(old_target, new_target, 1)

    verifier_anchor = (
        'c.check(manifest.get("counts") == expected_counts, "Manifest counts are exact", '
        'manifest.get("counts"))'
    )
    verifier_check = (
        'c.check(all("available only in the United States" in '
        '(package / name).read_text(encoding="utf-8") for name in '
        '["README-FIRST.md", "GIVE-THIS-PACKAGE-TO-HERMES.md"]), '
        '"USA-only availability is embedded in both Hermes entrypoints")'
    )
    if verifier_check not in verifier:
        if verifier_anchor not in verifier:
            raise ValueError("Bundled verifier manifest-count anchor is missing")
        verifier = verifier.replace(
            verifier_anchor,
            verifier_anchor + "\n    " + verifier_check,
            1,
        )

    if "import os\n" not in verifier:
        import_anchor = "import json\n"
        if import_anchor not in verifier:
            raise ValueError("Bundled verifier import anchor is missing")
        verifier = verifier.replace(import_anchor, import_anchor + "import os\n", 1)

    old_mode_function = "def check_package_filesystem(c: Checks, package: Path) -> None:"
    new_mode_function = "def check_package_filesystem(c: Checks, package: Path, enforce_modes: bool) -> None:"
    if new_mode_function not in verifier:
        if old_mode_function not in verifier:
            raise ValueError("Bundled verifier filesystem-mode function anchor is missing")
        verifier = verifier.replace(old_mode_function, new_mode_function, 1)

    old_mode_result = '    c.check(not unsafe_modes, "Package modes are normalized and safe", unsafe_modes[:10])'
    new_mode_result = (
        '    if enforce_modes:\n'
        '        c.check(not unsafe_modes, "Package modes are normalized and safe", unsafe_modes[:10])\n'
        '    elif unsafe_modes:\n'
        '        c.warn("Extracted filesystem modes are non-authoritative; outer-ZIP modes remain mandatory", unsafe_modes[:10])\n'
        '    else:\n'
        '        c.check(True, "Package modes are normalized and safe")'
    )
    if new_mode_result not in verifier:
        if old_mode_result not in verifier:
            raise ValueError("Bundled verifier filesystem-mode result anchor is missing")
        verifier = verifier.replace(old_mode_result, new_mode_result, 1)

    broken_mode_call = "        check_package_filesystem(c, package, enforce_modes=args.zip is None and os.name != \"nt\")"
    old_mode_call = "        check_package_filesystem(c, package)"
    new_mode_call = "        check_package_filesystem(c, package, enforce_modes=args.zip_path is None and os.name != \"nt\")"
    if broken_mode_call in verifier:
        verifier = verifier.replace(broken_mode_call, new_mode_call, 1)
    elif new_mode_call not in verifier:
        if old_mode_call not in verifier:
            raise ValueError("Bundled verifier filesystem-mode call anchor is missing")
        verifier = verifier.replace(old_mode_call, new_mode_call, 1)
    data[verifier_path] = verifier.encode("utf-8")

    manifest = json.loads(data[manifest_path])
    if not isinstance(manifest.get("target"), dict):
        raise ValueError("WINGS release manifest target is malformed")
    manifest["target"]["country_availability"] = COUNTRIES

    excluded = {manifest_path, checksum_path}
    files = []
    for full_name in sorted(name for name in data if name not in excluded):
        relative = full_name.removeprefix(prefix)
        if relative == full_name:
            raise ValueError(f"Entry escaped WINGS root: {full_name}")
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
                kwargs = {}
                if info.compress_type == zipfile.ZIP_DEFLATED:
                    kwargs["compresslevel"] = 9
                output.writestr(info, payload, compress_type=info.compress_type, **kwargs)
        with zipfile.ZipFile(temp) as check:
            if check.testzip() is not None:
                raise ValueError("Rotated WINGS ZIP failed CRC verification")
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)

    print(f"WINGS_COUNTRY_BOUNDARY_ROTATED={path}")
    print(f"WINGS_ZIP_BYTES={path.stat().st_size}")
    print(f"WINGS_ZIP_SHA256={sha256(path.read_bytes())}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args()
    rotate(args.zip.resolve())


if __name__ == "__main__":
    main()
