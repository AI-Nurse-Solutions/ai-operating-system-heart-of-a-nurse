#!/usr/bin/env python3
"""Regenerate the downloadable PDFs from their markdown sources.

Usage:
    python3 tools/build-pdfs.py            # rebuilds every target in DOCS
    python3 tools/build-pdfs.py roadmap    # rebuilds one (any key in DOCS below)

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
    "safety": ("assets/safety-rules-edena.md", "assets/safety-rules-edena.pdf",
               "The Plain-Language Safety Rules (EDENA)"),
    "architecture": ("assets/nurse-ai-os-architecture-report.md", "assets/nurse-ai-os-architecture-report.pdf",
                     "Nurse AI OS Architecture Report"),
    "media": ("assets/nurse-ai-os-media-packet.md", "assets/nurse-ai-os-media-packet.pdf",
              "Nurse AI OS™ Media Packet"),
    "media-fr": ("assets/nurse-ai-os-media-packet-fr.md", "assets/nurse-ai-os-media-packet-fr.pdf",
                 "Nurse AI OS — Dossier de presse"),
    "media-es": ("assets/nurse-ai-os-media-packet-es.md", "assets/nurse-ai-os-media-packet-es.pdf",
                 "Nurse AI OS — Dossier de prensa"),
    "media-ar": ("assets/nurse-ai-os-media-packet-ar.md", "assets/nurse-ai-os-media-packet-ar.pdf",
                 "Nurse AI OS — الملف الإعلامي"),
    "media-ru": ("assets/nurse-ai-os-media-packet-ru.md", "assets/nurse-ai-os-media-packet-ru.pdf",
                 "Nurse AI OS — Пресс-кит"),
    "media-zh": ("assets/nurse-ai-os-media-packet-zh.md", "assets/nurse-ai-os-media-packet-zh.pdf",
                 "Nurse AI OS — 媒体资料包"),
    "media-hi": ("assets/nurse-ai-os-media-packet-hi.md", "assets/nurse-ai-os-media-packet-hi.pdf",
                 "Nurse AI OS — मीडिया किट"),
}

# Per-language rendering config for translated documents: html lang/dir, extra
# Google-Fonts stylesheets for the script, and CSS overriding the default
# Latin font stacks. Latin-script languages (fr, es) need no entry.
LANG_META = {
    "architecture": {
        "lang": "en", "dir": "ltr",
        # Keep the compact evidence appendix and generated source footer
        # together instead of creating a nearly empty trailing page.
        "css": ".doc-footer{margin-top:.2em;padding-top:.25em;font-size:7pt;line-height:1.2;}",
    },
    "media-ar": {
        "lang": "ar", "dir": "rtl",
        "font_links": '<link href="https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic:wght@400;700&display=swap" rel="stylesheet">',
        "css": ("body,h1,h2,h3,h4{font-family:'Noto Naskh Arabic',serif;}"
                "body{direction:rtl;}th,td{text-align:right;}"
                "ul,ol{padding-right:1.4em;padding-left:0;}"
                "blockquote{border-left:none;border-right:4px solid var(--gold);}"),
    },
    "media-ru": {
        "lang": "ru", "dir": "ltr",
        "font_links": '<link href="https://fonts.googleapis.com/css2?family=Noto+Serif:wght@400;700&display=swap" rel="stylesheet">',
        # Source Sans 3 covers Cyrillic for body text; Fraunces does not, so headings switch to Noto Serif.
        "css": "h1,h2,h3,h4{font-family:'Noto Serif',Georgia,serif;}",
    },
    "media-zh": {
        "lang": "zh-Hans", "dir": "ltr",
        "font_links": '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;700&family=Noto+Serif+SC:wght@700&display=swap" rel="stylesheet">',
        "css": "body{font-family:'Noto Sans SC',sans-serif;}h1,h2,h3,h4{font-family:'Noto Serif SC',Georgia,serif;}",
    },
    "media-hi": {
        "lang": "hi", "dir": "ltr",
        "font_links": '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;700&family=Noto+Serif+Devanagari:wght@700&display=swap" rel="stylesheet">',
        "css": "body{font-family:'Noto Sans Devanagari',sans-serif;}h1,h2,h3,h4{font-family:'Noto Serif Devanagari',Georgia,serif;}",
    },
    "media-fr": {"lang": "fr", "dir": "ltr"},
    "media-es": {"lang": "es", "dir": "ltr"},
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
    meta = LANG_META.get(key, {})
    src, out = ROOT / src_rel, ROOT / out_rel
    body = markdown.markdown(src.read_text(encoding="utf-8"),
                             extensions=["tables", "fenced_code", "sane_lists", "smarty"])
    footer = (
        f'<div class="doc-footer">nurse-ai-os.org · No PHI · Agents propose. Humans judge. '
        f'Nurses steward. · This PDF is generated from {src_rel} — the web copy is canonical.'
        f'</div>'
    )
    html = (f'<!DOCTYPE html><html lang="{meta.get("lang", "en")}" dir="{meta.get("dir", "ltr")}">'
            f'<head><meta charset="utf-8"><title>{title}</title>'
            f'{FONTS}{meta.get("font_links", "")}<style>{CSS}{meta.get("css", "")}</style></head><body>{body}'
            f'{footer}</body></html>')
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
