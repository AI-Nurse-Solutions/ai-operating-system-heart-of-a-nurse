#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

HARNESS_ROOT = Path(__file__).resolve().parents[1]
SITE_ROOT = Path(__file__).resolve().parents[2]
PUBLIC_FILES = [
    SITE_ROOT / "governed-harness.html",
    SITE_ROOT / "assets" / "governed-harness-2-architecture.md",
    HARNESS_ROOT / "evidence" / "release-evidence.json",
]


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links: list[str] = []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "a":
            href = values.get("href")
            if href:
                self.links.append(href)
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def main() -> int:
    errors: list[str] = []
    page = (SITE_ROOT / "governed-harness.html").read_text(encoding="utf-8")
    parser = LinkParser()
    parser.feed(page)
    if not parser.title.strip():
        errors.append("missing HTML title")
    required = ["CNO", "CIO", "CTO", "46/46", "8/8", "Existing-anchor signed", "Primary sources"]
    for value in required:
        if value not in page:
            errors.append(f"missing required public statement: {value}")
    external = [link for link in parser.links if urlparse(link).scheme in {"http", "https"}]
    if len(external) < 25:
        errors.append(f"expected at least 25 external citations, found {len(external)}")
    for link in parser.links:
        parsed = urlparse(link)
        if parsed.scheme or link.startswith(("#", "mailto:")):
            continue
        target = (SITE_ROOT / parsed.path).resolve()
        if not target.exists():
            errors.append(f"broken internal link: {link}")

    combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_FILES)
    forbidden = {
        "local user path": r"/Users/[^/\s]+",
        "private key": r"BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY",
        "GitHub token": r"gh[opusr]_[A-Za-z0-9]{20,}",
        "API key": r"\bsk_[A-Za-z0-9_-]{20,}",
        "authorization bearer": r"Authorization:\s*Bearer",
        "patient-like MRN": r"\bMRN\s*[:#-]\s*(?!TEST)(?=[A-Z0-9]*\d)[A-Z0-9]{4,}\b",
    }
    for label, pattern in forbidden.items():
        if re.search(pattern, combined, re.IGNORECASE):
            errors.append(f"forbidden public pattern: {label}")

    evidence = json.loads(PUBLIC_FILES[2].read_text(encoding="utf-8"))
    signing = evidence.get("signing", {})
    verification = evidence.get("verification", {})
    if evidence.get("release_status") != "signed_implementation_candidate":
        errors.append("release status is not the approved signed candidate label")
    if signing.get("signed") is not True:
        errors.append("signed candidate must declare its detached signature")
    if signing.get("trust_anchor_rotated") is not False:
        errors.append("existing-anchor release must not claim key rotation")
    unit_tests = verification.get("unit_tests", {})
    if unit_tests.get("count") != 46 or unit_tests.get("ok") is not True:
        errors.append("unit-test evidence mismatch")
    if verification.get("trajectory_evaluations", {}).get("passed") != 8:
        errors.append("trajectory evidence mismatch")

    signature_name = signing.get("signature")
    signature = HARNESS_ROOT / "evidence" / signature_name if isinstance(signature_name, str) else None
    public_key = SITE_ROOT / "naio-os" / "config" / "naio-os-release-public.pem"
    if signature is None or not signature.is_file():
        errors.append("detached release-evidence signature missing")
    elif not public_key.is_file():
        errors.append("trusted release public key missing")
    else:
        verified = subprocess.run(
            ["openssl", "dgst", "-sha256", "-verify", str(public_key), "-signature", str(signature), str(PUBLIC_FILES[2])],
            capture_output=True,
            text=True,
        )
        if verified.returncode != 0 or "Verified OK" not in verified.stdout:
            errors.append("detached release-evidence signature failed verification")

    output = {"ok": not errors, "errors": errors, "internal_links_checked": len(parser.links) - len(external), "external_citations": len(external), "public_files_scanned": len(PUBLIC_FILES)}
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
