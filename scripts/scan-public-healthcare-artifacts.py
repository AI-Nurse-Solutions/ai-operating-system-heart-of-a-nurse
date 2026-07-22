#!/usr/bin/env python3
"""Scan public healthcare artifacts for likely secrets or realistic PHI examples."""

from __future__ import annotations

import argparse
import io
import re
import stat
import sys
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath

TEXT_SUFFIXES = {
    ".bash", ".bat", ".cfg", ".cmd", ".command", ".css", ".csv", ".env",
    ".fish", ".html", ".ini", ".js", ".json", ".md", ".mjs", ".ps1",
    ".py", ".rels", ".sh", ".toml", ".txt", ".xml", ".yaml", ".yml",
    ".zsh",
}
TEXT_BASENAMES = {".env", ".env.example", "LICENSE", "NOTICE", "VERSION"}
ARCHIVE_SUFFIXES = {".docx", ".zip"}
MAX_DEPTH = 3
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "generic api key": re.compile(
        r"(?:api[_-]?key|access[_-]?key|client[_-]?secret|secret|token|password)"
        r"[ \t]*[:=][ \t]*['\"]?[A-Za-z0-9_./+\-=]{16,}",
        re.IGNORECASE,
    ),
    "patient or mrn example": re.compile(
        r"(?:patient[ \t]*(?:name)?|mrn[ \t]*(?:number)?)[ \t]*[:=][ \t]*[A-Za-z0-9][A-Za-z0-9_-]*",
        re.IGNORECASE,
    ),
}


class ScanError(RuntimeError):
    """Raised when an archive cannot be scanned safely."""


def _safe_member_name(name: str) -> str:
    if not name or "\x00" in name:
        raise ScanError(f"unsafe archive member path: {name!r}")
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.parts or any(":" in part for part in path.parts):
        raise ScanError(f"unsafe archive member path: {name!r}")
    canonical = path.as_posix()
    if normalized.rstrip("/") != canonical:
        raise ScanError(f"noncanonical archive member path: {name!r}")
    return canonical


def extract_text(name: str, data: bytes, *, depth: int = 0) -> list[tuple[str, str]]:
    """Return textual payloads from a file, recursively unpacking ZIP/DOCX."""
    suffix = Path(name).suffix.lower()
    if suffix in ARCHIVE_SUFFIXES:
        if depth >= MAX_DEPTH:
            raise ScanError(f"archive nesting exceeds {MAX_DEPTH}: {name}")
        if len(data) > MAX_ARCHIVE_BYTES:
            raise ScanError(f"archive exceeds byte limit: {name}")
        try:
            archive = zipfile.ZipFile(io.BytesIO(data))
        except zipfile.BadZipFile as exc:
            raise ScanError(f"invalid compressed artifact: {name}") from exc
        payloads: list[tuple[str, str]] = []
        total = 0
        normalized_members: set[str] = set()
        with archive:
            for info in archive.infolist():
                member = _safe_member_name(info.filename)
                folded = unicodedata.normalize("NFC", member.rstrip("/")).casefold()
                if folded in normalized_members:
                    raise ScanError(f"duplicate or case-colliding archive member: {name}!{member}")
                normalized_members.add(folded)
                mode = (info.external_attr >> 16) & 0o177777
                if mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR):
                    raise ScanError(f"symlink or special archive member: {name}!{member}")
                if info.is_dir():
                    continue
                if info.flag_bits & 1:
                    raise ScanError(f"encrypted archive member: {name}!{member}")
                if info.file_size > MAX_MEMBER_BYTES:
                    raise ScanError(f"archive member exceeds byte limit: {name}!{member}")
                total += info.file_size
                if total > MAX_ARCHIVE_BYTES:
                    raise ScanError(f"expanded archive exceeds byte limit: {name}")
                member_data = archive.read(info)
                payloads.extend(extract_text(f"{name}!{member}", member_data, depth=depth + 1))
        return payloads
    basename = Path(name).name
    extensionless_text = not suffix and b"\x00" not in data
    if suffix in TEXT_SUFFIXES or basename in TEXT_BASENAMES or extensionless_text:
        try:
            return [(name, data.decode("utf-8"))]
        except UnicodeDecodeError:
            return []
    return []


def scan_paths(paths: list[Path]) -> list[tuple[str, str]]:
    """Return (pattern label, source path) findings without exposing matched text."""
    findings: list[tuple[str, str]] = []
    for path in paths:
        for source, text in extract_text(path.name, path.read_bytes()):
            for label, pattern in PATTERNS.items():
                if pattern.search(text):
                    findings.append((label, f"{path}:{source}"))
    return findings


def _probe_archive(member: str, payload: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member, payload)
    return buffer.getvalue()


def run_self_probes() -> None:
    examples = ("Patient: John", "MRN: 123456", "MRN number=A1B2C3")
    phi = PATTERNS["patient or mrn example"]
    for example in examples:
        if not phi.search(example):
            raise ScanError(f"plain-text PHI probe failed: {example}")
    zip_payload = _probe_archive("payload.txt", b"MRN: A1B2C3")
    docx_payload = _probe_archive("word/document.xml", b"<w:t>Patient: John</w:t>")
    nested_payload = _probe_archive("nested.zip", zip_payload)
    for name, payload in (
        ("probe.zip", zip_payload),
        ("probe.docx", docx_payload),
        ("nested.zip", nested_payload),
    ):
        texts = extract_text(name, payload)
        if not any(phi.search(text) for _, text in texts):
            raise ScanError(f"compressed PHI probe failed: {name}")
    secret = PATTERNS["generic api key"]
    for name, payload in (
        (".env", b"API_KEY=abcdefghijklmnop"),
        ("setup.sh", b"CLIENT_SECRET=abcd/efgh+ijkl=="),
        ("install.command", b"ACCESS_KEY=abcdefghijklmnop"),
        ("VERSION", b"TOKEN=abcdefghijklmnop"),
    ):
        texts = extract_text(name, payload)
        if not any(secret.search(text) for _, text in texts):
            raise ScanError(f"text-file secret probe failed: {name}")
    empty_env = "HERMES_API_KEY=\nHERMES_MODEL=\nOPENAI_COMPATIBLE_API_KEY=\n"
    if secret.search(empty_env):
        raise ScanError("empty environment assignment produced a cross-line false positive")

    collision_buffer = io.BytesIO()
    with zipfile.ZipFile(collision_buffer, "w") as archive:
        archive.writestr("Payload.txt", b"safe")
        archive.writestr("payload.txt", b"safe")
    try:
        extract_text("collision.zip", collision_buffer.getvalue())
    except ScanError as exc:
        if "case-colliding" not in str(exc):
            raise
    else:
        raise ScanError("case-colliding archive-member probe failed")

    symlink_buffer = io.BytesIO()
    symlink = zipfile.ZipInfo("linked.txt")
    symlink.create_system = 3
    symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(symlink_buffer, "w") as archive:
        archive.writestr(symlink, b"target.txt")
    try:
        extract_text("symlink.zip", symlink_buffer.getvalue())
    except ScanError as exc:
        if "symlink or special" not in str(exc):
            raise
    else:
        raise ScanError("symlink archive-member probe failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--label", default="PUBLIC")
    args = parser.parse_args()
    if not args.root.exists():
        parser.error(f"root does not exist: {args.root}")
    run_self_probes()
    paths = (
        [args.root]
        if args.root.is_file()
        else sorted(path for path in args.root.rglob("*") if path.is_file())
    )
    findings = scan_paths(paths)
    if findings:
        summary = ", ".join(f"{label} in {source}" for label, source in findings)
        raise SystemExit(f"{args.label} public-safety scan failed: {summary}")
    print(f"{args.label}_PUBLIC_SAFETY_SCAN=passed files={len(paths)} compressed=recursive")
    return 0


if __name__ == "__main__":
    sys.exit(main())
