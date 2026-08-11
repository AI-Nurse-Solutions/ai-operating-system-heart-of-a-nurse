#!/usr/bin/env python3
"""
tools/check-links.py — find local links that point at nothing.

Run from the site root:

    python3 tools/check-links.py            # report
    python3 tools/check-links.py --strict   # exit 1 if anything is broken

Why this exists: documents get checked for honesty; buttons often do not. A page
can be true in every sentence and still hand a nurse a download that 404s.

A note on this tool's own history, since it is a tool about unverified claims.
It was written on 11 August 2026 against a working copy that turned out to be a
stale partial snapshot of the site, and its first docstring reported fifteen
broken links, including the Starter Kit download. Run against the actual
published tree, the count is zero — those links were broken only in the copy.
The tool was right; the tree it was pointed at was not. Kept, with the number
removed, because the check is worth having and the anecdote is worth more as a
caution than as a statistic.

Three things it is careful about, because earlier versions reported false alarms:

  * HTML comments are stripped first. An authoring template inside <!-- --> that
    contains href="URL" is not a broken link; it is a comment.
  * <script> and <style> bodies are stripped too. A JS template literal that
    builds `<a href="${esc(u)}">` at runtime is not a static link, and reporting
    it as broken trains people to ignore the report.
  * Root-relative links (/foo.html) resolve against the site root, not against
    the folder of the page that contains them.

It checks that link targets exist. It does not check that pages render, that
anchors resolve, or that external URLs are alive.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {"_to_delete", ".git", "node_modules", "__pycache__"}
EXTERNAL = ("http://", "https://", "mailto:", "tel:", "data:", "javascript:", "//")

COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)
SCRIPT = re.compile(r"<(script|style)\b.*?</\1\s*>", re.DOTALL | re.IGNORECASE)
LINK = re.compile(r'(?:href|src)\s*=\s*"([^"]*)"', re.IGNORECASE)
# A target the page computes at runtime — "${u}", "{{ path }}", "<%= x %>" — is
# not a file this check can resolve, and guessing produces noise.
TEMPLATED = re.compile(r"\$\{|\{\{|<%")


def pages() -> list[Path]:
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith((".html", ".htm")):
                out.append(Path(dirpath) / name)
    return sorted(out)


def broken() -> list[tuple[str, str]]:
    found = []
    for page in pages():
        html = page.read_text(encoding="utf-8", errors="replace")
        html = SCRIPT.sub("", COMMENT.sub("", html))
        for raw in LINK.findall(html):
            if not raw or raw.startswith("#") or raw.lower().startswith(EXTERNAL):
                continue
            if TEMPLATED.search(raw):
                continue
            target = urllib.parse.unquote(raw.split("#")[0].split("?")[0])
            if not target:
                continue
            base = ROOT if target.startswith("/") else page.parent
            resolved = (base / target.lstrip("/")).resolve()
            if not resolved.exists():
                found.append((str(page.relative_to(ROOT)), raw))
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description="Find local links that point at nothing")
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if anything is broken (use before publishing)")
    args = ap.parse_args()

    print("\ncheck-links\n")
    found = broken()
    print(f"  {len(pages())} page(s) checked")

    if not found:
        print("  \033[32m✓\033[0m every local link resolves\n")
        return 0

    by_target: dict[str, list[str]] = {}
    for src, link in found:
        by_target.setdefault(link, []).append(src)

    print(f"  \033[31m✗\033[0m {len(found)} broken link(s), {len(by_target)} distinct target(s)\n")
    for target, srcs in sorted(by_target.items(), key=lambda kv: -len(kv[1])):
        print(f"      {target}")
        for src in sorted(set(srcs)):
            print(f"        ← {src}")
    print()
    return 1 if args.strict else 0


if __name__ == "__main__":
    sys.exit(main())
