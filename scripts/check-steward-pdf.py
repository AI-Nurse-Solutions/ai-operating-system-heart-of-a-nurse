#!/usr/bin/env python3
# pyright: reportMissingImports=false
"""Fail-closed semantic and active-content checks for the public STEWARD PDF."""

from __future__ import annotations

import hashlib
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

from pypdf import PdfReader
from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "hospital-clinic-administrators" / "preview" / "STEWARD-Governance-Specification.pdf"
SOURCE = ROOT / "hospital-clinic-administrators" / "preview" / "STEWARD-Governance-Specification.md"
EXPECTED_TEXT_SHA256 = "960a616b214a4a4823e7168dcfea62617cb7afeb6763f87539a17b87673ecec5"
EXPECTED_TITLE = "STEWARD Governance Specification — Hospital & Clinic Administration Preview"
EXPECTED_AUTHOR = "NAIO Institute"
EXPECTED_SUBJECT = "Non-executable governance preview for hospital and clinic administration"
FORBIDDEN_PDF_NAMES = (
    b"/AA",
    b"/AcroForm",
    b"/EmbeddedFiles",
    b"/ImportData",
    b"/JavaScript",
    b"/JS",
    b"/Launch",
    b"/OpenAction",
    b"/RichMedia",
    b"/SubmitForm",
)
REQUIRED_NONCLAIMS = (
    "This document is a governance specification, not software.",
    "Non-executable",
    "Not institution-approved",
    "No runtime tier assigned",
    "AI may prepare. Authorized humans judge, approve, act, record, and remain accountable.",
    "A future STEWARD runtime must never become or impersonate",
    "not third-party certification",
)
FORBIDDEN_POSITIVE_CLAIMS = (
    "activate steward now",
    "complete ai os is available",
    "install steward now",
    "runtime status: implemented",
    "steward is institution-ready",
    "steward is institution-approved",
)


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).split())


def plain_heading(line: str) -> str:
    text = re.sub(r"^#{2,4}\s+", "", line).strip()
    text = re.sub(r"\[([^]]+)]\([^)]*\)", r"\1", text)
    return normalize(text.replace("`", "").replace("**", "").replace("__", ""))


def outline_count(items: list[object]) -> int:
    return sum(outline_count(item) if isinstance(item, list) else 1 for item in items)


def fail(message: str) -> None:
    raise SystemExit(f"STEWARD_PDF_CHECK=failed: {message}")


def assert_inert_object_graph(reader: PdfReader) -> None:
    forbidden = {name.decode() for name in FORBIDDEN_PDF_NAMES}
    seen: set[tuple[int, int]] = set()

    def walk(value: Any, path: str) -> None:
        if isinstance(value, IndirectObject):
            identity = (value.idnum, value.generation)
            if identity in seen:
                return
            seen.add(identity)
            value = value.get_object()
        if isinstance(value, DictionaryObject):
            for key, child in value.items():
                key_text = str(key)
                if key_text in forbidden:
                    fail(f"forbidden active-content name present at {path}: {key_text}")
                walk(child, f"{path}/{key_text}")
        elif isinstance(value, ArrayObject):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")

    walk(reader.trailer, "trailer")


def main() -> None:
    pdf_path = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else PDF
    if len(sys.argv) > 2:
        fail("usage: check-steward-pdf.py [pdf-path]")

    reader = PdfReader(str(pdf_path))
    assert_inert_object_graph(reader)
    root = reader.trailer["/Root"]
    mark_info = root.get("/MarkInfo")
    if not root.get("/StructTreeRoot"):
        fail("missing tagged structure tree")
    if root.get("/Lang") != "en":
        fail("document language is not en")
    if not mark_info or not mark_info.get("/Marked"):
        fail("marked-content metadata is absent")
    if len(reader.pages) != 15:
        fail(f"unexpected page count: {len(reader.pages)}")
    if outline_count(reader.outline) != 42:
        fail(f"unexpected outline count: {outline_count(reader.outline)}")
    if reader.attachments:
        fail("attachments are prohibited")
    if reader.get_fields():
        fail("interactive form fields are prohibited")

    metadata = reader.metadata
    expected_metadata = {
        "title": EXPECTED_TITLE,
        "author": EXPECTED_AUTHOR,
        "subject": EXPECTED_SUBJECT,
    }
    for field, expected in expected_metadata.items():
        if getattr(metadata, field) != expected:
            fail(f"unexpected {field} metadata")

    extracted = normalize(" ".join(page.extract_text() or "" for page in reader.pages))
    extracted_casefold = extracted.casefold()
    text_digest = hashlib.sha256(extracted.encode("utf-8")).hexdigest()
    if text_digest != EXPECTED_TEXT_SHA256:
        fail(f"normalized text digest mismatch: {text_digest}")

    for phrase in REQUIRED_NONCLAIMS:
        if normalize(phrase).casefold() not in extracted_casefold:
            fail(f"required nonclaim missing: {phrase}")
    for phrase in FORBIDDEN_POSITIVE_CLAIMS:
        if normalize(phrase).casefold() in extracted_casefold:
            fail(f"forbidden positive claim present: {phrase}")

    source = SOURCE.read_text(encoding="utf-8")
    headings = [plain_heading(line) for line in source.splitlines() if re.match(r"^#{2,4}\s+", line)]
    missing = [heading for heading in headings if heading.casefold() not in extracted_casefold]
    if missing:
        fail(f"canonical Markdown headings missing from PDF: {missing}")

    print(
        "STEWARD_PDF_CHECK=passed "
        f"pages={len(reader.pages)} outline={outline_count(reader.outline)} "
        f"headings={len(headings)} text_sha256={text_digest}"
    )


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError) as exc:
        fail(str(exc))
