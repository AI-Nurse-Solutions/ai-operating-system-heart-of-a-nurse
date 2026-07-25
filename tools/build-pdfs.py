#!/usr/bin/env python3
"""Regenerate the downloadable PDFs from their markdown sources.

Usage:
    python3 tools/build-pdfs.py            # rebuilds every target in DOCS
    python3 tools/build-pdfs.py roadmap    # rebuilds one (any key in DOCS below)

Requires pinned `markdown` and `pypdf` packages plus a Chromium/Chrome binary
(set CHROME_BIN, otherwise common locations are tried). Keep this script in sync with DOCS
below when a new markdown-sourced PDF is added, and re-run it whenever a
source .md changes so the PDF downloads never drift from the web copy again.
"""
import hashlib
import html as html_lib
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown
from pypdf import PdfReader, PdfWriter

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
    "architecture-2026-07-13": (
        "assets/2026-07-13-nurse-ai-os-updated-architecture-report.md",
        "assets/2026-07-13-nurse-ai-os-updated-architecture-report.pdf",
        "Nurse AI OS Architecture Report — July 13, 2026 Evidence Snapshot",
    ),
    "media": ("assets/nurse-ai-os-media-packet.md", "assets/nurse-ai-os-media-packet.pdf",
              "Nurse AI OS™ Media Kit"),
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
    "media-tl": ("assets/nurse-ai-os-media-packet-tl.md", "assets/nurse-ai-os-media-packet-tl.pdf",
                 "Nurse AI OS — Media brief sa Tagalog"),
    "media-vi": ("assets/nurse-ai-os-media-packet-vi.md", "assets/nurse-ai-os-media-packet-vi.pdf",
                 "Nurse AI OS — Tóm tắt truyền thông tiếng Việt"),
}

HTML_DOCS = {
    "media-hi": ("assets/nurse-ai-os-media-packet-hi.md", "media-hi.html",
                 "Nurse AI OS — हिंदी मीडिया संक्षेप"),
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
    "architecture-2026-07-13": {
        "lang": "en", "dir": "ltr",
        "css": ".doc-footer{margin-top:.2em;padding-top:.25em;font-size:7pt;line-height:1.2;}",
    },
    "media-ar": {
        "lang": "ar", "dir": "rtl",
        "font_links": "",
        "css": ("body,h1,h2,h3,h4{font-family:Arial,sans-serif;}"
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

    "media-fr": {"lang": "fr", "dir": "ltr"},
    "media-es": {"lang": "es", "dir": "ltr"},
    "media-tl": {"lang": "tl", "dir": "ltr"},
    "media-vi": {
        "lang": "vi", "dir": "ltr",
        "font_links": "",
        "css": "body,h1,h2,h3,h4{font-family:Arial,sans-serif;}",
    },
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


def canonicalize_pdf(raw: Path, out: Path, title: str, source_digest: str) -> None:
    """Remove volatile Chrome metadata and atomically publish stable PDF bytes."""
    reader = PdfReader(raw)
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    # Replace rather than merge Chrome's volatile CreationDate/ModDate values.
    writer._info = None
    writer.add_metadata({
        "/Title": title,
        "/Author": "Robert Domondon",
        "/Subject": "Nurse AI OS media and governance information",
        "/Creator": "Nurse AI OS PDF builder",
        "/Producer": "pypdf 6.14.2",
        "/SourceSHA256": source_digest,
    })
    # Chrome emits timestamp-derived identifiers. The canonical publication
    # omits them so identical source/layout input produces identical bytes.
    writer._ID = None
    with tempfile.NamedTemporaryFile(
        "wb", suffix=".canonical.pdf", dir=out.parent, delete=False
    ) as tf:
        canonical = Path(tf.name)
        writer.write(tf)
    try:
        os.replace(canonical, out)
    finally:
        canonical.unlink(missing_ok=True)


def build(key: str, chrome: str) -> None:
    src_rel, out_rel, title = DOCS[key]
    meta = LANG_META.get(key, {})
    src, out = ROOT / src_rel, ROOT / out_rel
    source_bytes = src.read_bytes()
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    body = markdown.markdown(source_bytes.decode("utf-8"),
                             extensions=["tables", "fenced_code", "sane_lists", "smarty"])
    if key == "media-ar":
        body = body.replace("Nurse AI OS™", '<bdi dir="ltr">Nurse AI OS™</bdi>', 1)
    footer = (
        f'<div class="doc-footer">nurse-ai-os.org · No PHI · Agents propose. Humans judge. '
        f'Nurses steward. · This PDF is generated from {src_rel} — the web copy is canonical.'
        f'</div>'
    )
    html = (f'<!DOCTYPE html><html lang="{meta.get("lang", "en")}" dir="{meta.get("dir", "ltr")}">'
            f'<head><meta charset="utf-8"><title>{title}</title><meta name="author" content="Robert Domondon">'
            f'{FONTS}{meta.get("font_links", "")}<style>{CSS}{meta.get("css", "")}</style></head><body>{body}'
            f'{footer}</body></html>')
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as tf:
        tf.write(html)
        tmp = tf.name
    with tempfile.NamedTemporaryFile(
        "wb", suffix=".raw.pdf", dir=out.parent, delete=False
    ) as pf:
        raw_pdf = Path(pf.name)
    try:
        subprocess.run([chrome, "--headless", "--no-sandbox", "--disable-gpu",
                        "--virtual-time-budget=15000", "--no-pdf-header-footer",
                        f"--print-to-pdf={raw_pdf}", f"file://{tmp}"],
                       check=True, capture_output=True, timeout=180)
        canonicalize_pdf(raw_pdf, out, title, source_digest)
    finally:
        os.unlink(tmp)
        raw_pdf.unlink(missing_ok=True)
    print(f"built {out_rel} ({out.stat().st_size} bytes)")


def build_html(key: str) -> None:
    """Build accessible web text when the PDF engine cannot preserve logical text."""
    src_rel, out_rel, title = HTML_DOCS[key]
    src, out = ROOT / src_rel, ROOT / out_rel
    source_bytes = src.read_bytes()
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    body = markdown.markdown(source_bytes.decode("utf-8"),
                             extensions=["tables", "fenced_code", "sane_lists", "smarty"])
    page = f'''<!DOCTYPE html>
<html lang="hi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_lib.escape(title)}</title><meta name="description" content="Accessible Hindi Nurse AI OS media brief.">
<meta name="source-sha256" content="{source_digest}"><link rel="stylesheet" href="assets/nurse-ai.css">
<style>html,body{{max-width:100%;overflow-x:hidden}}.media-brief{{box-sizing:border-box;width:100%;max-width:820px;margin:0 auto;padding:3rem 1.25rem;overflow-wrap:anywhere}}.media-brief *{{box-sizing:border-box;max-width:100%}}.media-brief h1{{font-size:clamp(2rem,6vw,3.6rem);overflow-wrap:anywhere}}.media-brief blockquote{{margin:1rem 0;border-left:4px solid var(--gold-500);padding:1rem 1.2rem;background:var(--linen-50);overflow-wrap:anywhere}}.media-brief li{{margin:.55rem 0}}.source-note{{background:var(--navy-900);color:var(--white);padding:1rem 1.25rem;overflow-wrap:anywhere}}.source-note a{{color:var(--gold-300)}}@media(max-width:640px){{.nav-bar{{flex-wrap:wrap;gap:.65rem}}.nav-links{{width:100%;display:flex;flex-wrap:wrap;justify-content:flex-start;gap:.55rem}}.media-brief{{padding:2rem 1.25rem}}.media-brief h1{{font-size:clamp(2rem,10vw,2.8rem)}}}}</style></head>
<body><header class="site-header"><nav class="nav-bar"><a class="brand" href="index.html"><span class="lamp">🕯️</span> Nurse AI OS</a><div class="nav-links"><a href="media.html">Media center</a><a href="hi/about.html">संस्थापक</a><a class="nav-cta" href="soul-quiz.html">SOUL Quiz</a></div></nav></header>
<main id="main-content" class="media-brief"><div class="source-note">यह accessible web brief canonical Markdown से बनाया गया है। <a href="assets/nurse-ai-os-media-packet-hi.md">स्रोत देखें</a> · <a href="media.html">मीडिया केंद्र</a></div>{body}</main>
<footer class="site-footer"><div class="container"><p class="footer-motto">🕯️ दीपक लेकर चलें। लेखा सुरक्षित रखें। Agents propose. Humans judge. Nurses steward.</p></div></footer><script src="assets/site-shell.js" defer></script></body></html>'''
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=out.parent,
                                     delete=False, encoding="utf-8") as tf:
        tf.write(page)
        temporary = Path(tf.name)
    try:
        os.replace(temporary, out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"built {out_rel} ({out.stat().st_size} bytes)")


if __name__ == "__main__":
    targets = sys.argv[1:] or [*DOCS, *HTML_DOCS]
    chrome = None
    for t in targets:
        if t in DOCS:
            chrome = chrome or find_chrome()
            build(t, chrome)
        elif t in HTML_DOCS:
            build_html(t)
        else:
            choices = ", ".join([*DOCS, *HTML_DOCS])
            sys.exit(f"unknown target {t!r} — choose from {choices}")
