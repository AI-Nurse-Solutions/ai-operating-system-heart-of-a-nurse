#!/usr/bin/env python3
"""Regenerate the downloadable PDFs from their markdown sources.

Usage:
    python3 tools/build-pdfs.py            # rebuilds all three
    python3 tools/build-pdfs.py roadmap    # rebuilds one (cheat|roadmap|workbook)

Requires: `pip install markdown` and a Chromium/Chrome binary (set CHROME_BIN,
otherwise common locations are tried). Keep this script in sync with DOCS
below when a new markdown-sourced PDF is added, and re-run it whenever a
source .md changes so the PDF downloads never drift from the web copy again.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent

DOCS = {
    "cheat": ("assets/hermes-cheat-sheet.md", "assets/hermes-cheat-sheet.pdf",
              "The Pre-Procedure Checklist & Hermes Cheat Sheet"),
    "roadmap": ("assets/30-day-roadmap.md", "assets/30-day-roadmap.pdf",
                "The 30-Day Nurse AI OS Roadmap"),
    "workbook": ("assets/nurse-ai-os-workbook.md", "assets/nurse-ai-os-workbook.pdf",
                 "Nurse AI OS Workbook"),
}

CSS = """
@page { size: letter; margin: 0.85in 0.8in; }
:root { --navy:#10233a; --teal:#1f6f6f; --gold:#c9942f; --ink:#2c3540; --muted:#5b6570; }
* { box-sizing: border-box; }
body { font-family: 'Source Sans 3', 'Source Sans Pro', -apple-system, 'Segoe UI', sans-serif;
       color: var(--ink); font-size: 10.5pt; line-height: 1.55; margin: 0; }
h1, h2, h3, h4 { font-family: 'Fraunces', Georgia, 'Times New Roman', serif;
                 color: var(--navy); line-height: 1.25; page-break-after: avoid; }
h1 { font-size: 21pt; border-bottom: 3px solid var(--gold); padding-bottom: 6px; }
h2 { font-size: 15pt; margin-top: 1.6em; border-bottom: 1px solid #d8dee5; padding-bottom: 3px; }
h3 { font-size: 12pt; margin-top: 1.3em; }
a { color: var(--teal); text-decoration: none; }
blockquote { border-left: 4px solid var(--gold); background: #faf6ee; color: var(--muted);
             margin: 1em 0; padding: .6em 1em; page-break-inside: avoid; }
code { font-family: 'SF Mono', Consolas, Menlo, monospace; font-size: .9em;
       background: #eef1f4; padding: 1px 4px; border-radius: 3px; }
pre { background: var(--navy); color: #dbe6ef; padding: .8em 1em; border-radius: 6px;
      white-space: pre-wrap; page-break-inside: avoid; }
pre code { background: none; color: inherit; padding: 0; }
table { border-collapse: collapse; width: 100%; margin: 1em 0; page-break-inside: avoid; font-size: .95em; }
th { background: var(--navy); color: #fff; text-align: left; }
th, td { border: 1px solid #c9d2da; padding: 5px 9px; vertical-align: top; }
tr:nth-child(even) td { background: #f4f6f8; }
ul, ol { padding-left: 1.4em; }
li { margin: .25em 0; }
hr { border: none; border-top: 1px solid #d8dee5; margin: 1.6em 0; }
.doc-footer { margin-top: 2.5em; padding-top: .8em; border-top: 2px solid var(--gold);
              color: var(--muted); font-size: 9pt; }
"""

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,700'
         '&family=Source+Sans+3:wght@400;600;700&display=swap" rel="stylesheet">')


def find_chrome() -> str:
    for cand in [os.environ.get("CHROME_BIN"),
                 "/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell",
                 shutil.which("chromium"), shutil.which("google-chrome"), shutil.which("chrome"),
                 "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]:
        if cand and Path(cand).exists():
            return cand
    sys.exit("No Chromium/Chrome found — set CHROME_BIN to your browser binary.")


def build(key: str, chrome: str) -> None:
    src_rel, out_rel, title = DOCS[key]
    src, out = ROOT / src_rel, ROOT / out_rel
    body = markdown.markdown(src.read_text(encoding="utf-8"),
                             extensions=["tables", "fenced_code", "sane_lists", "smarty"])
    html = (f'<!DOCTYPE html><html><head><meta charset="utf-8"><title>{title}</title>'
            f'{FONTS}<style>{CSS}</style></head><body>{body}'
            f'<div class="doc-footer">nurse-ai-os.org · No PHI, ever · AI drafts, humans judge, '
            f'nurses steward · This PDF is generated from {src_rel} — the web copy is canonical.'
            f'</div></body></html>')
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
        tf.write(html)
        tmp = tf.name
    try:
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--virtual-time-budget=15000", "--no-pdf-header-footer",
                        f"--print-to-pdf={out}", f"file://{tmp}"],
                       check=True, capture_output=True, timeout=180)
    finally:
        os.unlink(tmp)
    print(f"built {out_rel} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    targets = sys.argv[1:] or list(DOCS)
    chrome = find_chrome()
    for t in targets:
        if t not in DOCS:
            sys.exit(f"unknown target {t!r} — choose from {', '.join(DOCS)}")
        build(t, chrome)
