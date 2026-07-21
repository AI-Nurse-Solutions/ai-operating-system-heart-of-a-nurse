#!/usr/bin/env python3
"""Scan public healthcare artifacts for likely secrets or realistic PHI examples."""

from __future__ import annotations

import argparse
import io
import re
import sys
import zipfile
from pathlib import Path, PurePosixPath

TEXT_SUFFIXES = {
    ".bat", ".command", ".css", ".csv", ".env", ".example", ".html",
    ".js", ".json", ".md", ".mjs", ".py", ".rels", ".sh", ".toml",
    ".txt", ".xml", ".yaml", ".yml",
}
TEXT_FILENAMES = {".env", ".env.example", "LICENSE", "NOTICE", "VERSION"}
ARCHIVE_SUFFIXES = {".docx", ".zip"}
MAX_DEPTH = 3
MAX_MEMBER_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024
PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "generic api key": re.compile(
        r"(?:api[_-]?key|token|password)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,}",
        re.IGNORECASE,
    ),
    "patient or mrn example": re.compile(
        r"(?:patient\s*(?:name)?|mrn\s*(?:number)?)\s*[:=]\s*[A-Za-z0-9][A-Za-z0-9_-]*",
        re.IGNORECASE,
    ),
}


class ScanError(RuntimeError):
    """Raised when an archive cannot be scanned safely."""


def _safe_member_name(name: str) -> str:
    normalized = name.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ScanError(f"unsafe archive member path: {name!r}")
    return normalized


def extract_text(name: str, data: bytes, *, depth: int = 0) -> list[tuple[str, str]]:
    """Return textual payloads from a file, recursively unpacking ZIP/DOCX."""
    path = Path(name)
    suffix = path.suffix.lower()
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
        with archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                member = _safe_member_name(info.filename)
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
    if suffix in TEXT_SUFFIXES or path.name in TEXT_FILENAMES or (not suffix and _looks_like_text(data)):
        return [(name, data.decode("utf-8", errors="ignore"))]
    return []


def _looks_like_text(data: bytes) -> bool:
    """Return true for extensionless UTF-8-ish config/scripts while skipping binary blobs."""
    if b"\x00" in data:
        return False
    if not data:
        return True
    sample = data[:4096]
    try:
        sample.decode("utf-8")
    except UnicodeDecodeError:
        return False
    control = sum(1 for byte in sample if byte < 32 and byte not in (9, 10, 13))
    return control / len(sample) < 0.02


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
        (".env", b"API_KEY=abcdefghijklmnop"),
        (".env.example", b"Patient: John"),
        ("VERSION", b"MRN: A1B2C3"),
        ("start-discover.sh", b"TOKEN=abcdefghijklmnop"),
        ("Start-DISCOVER.command", b"MRN number=A1B2C3"),
        ("Start-DISCOVER.bat", b"Patient: John"),
        ("probe.zip", zip_payload),
        ("probe.docx", docx_payload),
        ("nested.zip", nested_payload),
    ):
        texts = extract_text(name, payload)
        if not any(phi.search(text) or PATTERNS["generic api key"].search(text) for _, text in texts):
            raise ScanError(f"text extraction probe failed: {name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--label", default="PUBLIC")
    args = parser.parse_args()
    if not args.root.exists():
        parser.error(f"root does not exist: {args.root}")
    run_self_probes()
    paths = sorted(path for path in args.root.rglob("*") if path.is_file())
    findings = scan_paths(paths)
    if findings:
        summary = ", ".join(f"{label} in {source}" for label, source in findings)
        raise SystemExit(f"{args.label} public-safety scan failed: {summary}")
    print(f"{args.label}_PUBLIC_SAFETY_SCAN=passed files={len(paths)} compressed=recursive")
    return 0


if __name__ == "__main__":
    sys.exit(main())
