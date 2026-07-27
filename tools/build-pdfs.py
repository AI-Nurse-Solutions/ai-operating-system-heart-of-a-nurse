#!/usr/bin/env python3
"""Regenerate the downloadable PDFs from their markdown sources.

Usage:
    python3 tools/build-pdfs.py            # rebuild every PDF and accessible HTML target
    python3 tools/build-pdfs.py media       # rebuild one target

PDF builds require pinned `markdown` and `pypdf` packages. Release/CI builds set
MEDIA_PDF_RENDERER to the digest-pinned offline Playwright wrapper; ad hoc builds
may use CHROME_BIN or a locally discovered Chrome. Keep DOCS and HTML_DOCS in sync
with publication links, and rebuild whenever a Markdown source changes.
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
    "essentials": ("assets/hermes-essentials-guide.md", "assets/hermes-essentials-guide.pdf",
                   "Hermes Essentials Guide — Directive v1.1 Community Edition"),
    "founding": ("assets/founding-year-guide.md", "assets/founding-year-guide.pdf",
                 "Nurse AI OS Founding Year Guide — Directive v1.1"),
    "make-yours": ("assets/make-it-yours-six-workflows.md", "assets/make-it-yours-six-workflows.pdf",
                   "Make Nurse AI OS Yours — Six Public-Safe Workflows"),
    "power": ("assets/hermes-power-guide.md", "assets/hermes-power-guide.pdf",
              "The Hermes Power Guide — Directive v1.1 Advanced Community Edition"),
    "cheat": ("assets/hermes-cheat-sheet.md", "assets/hermes-cheat-sheet.pdf",
              "The Pre-Procedure Checklist & Hermes Cheat Sheet"),
    "roadmap": ("assets/30-day-roadmap.md", "assets/30-day-roadmap.pdf",
                "The 30-Day Nurse AI OS Roadmap"),
    "workbook": ("assets/nurse-ai-os-workbook.md", "assets/nurse-ai-os-workbook.pdf",
                 "Nurse AI OS Workbook"),
    "safety": ("assets/safety-rules-edena.md", "assets/safety-rules-edena.pdf",
               "The Plain-Language Safety Rules (EDENA)"),
    "lamp": ("assets/lamp-huddle.md", "assets/lamp-huddle.pdf",
             "The Lamp Huddle"),
    "architecture": ("assets/nurse-ai-os-architecture-report.md", "assets/nurse-ai-os-architecture-report.pdf",
                     "Nurse AI OS Pre-Directive Architecture Evidence"),
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
    "media-ar": ("assets/nurse-ai-os-media-packet-ar.md", "media-ar.html",
                 "Nurse AI OS — موجز إعلامي بالعربية"),
    "media-hi": ("assets/nurse-ai-os-media-packet-hi.md", "media-hi.html",
                 "Nurse AI OS — हिंदी मीडिया संक्षेप"),
}

HTML_META = {
    "media-ar": {
        "lang": "ar", "dir": "rtl", "description": "موجز إعلامي عربي متاح لنظام Nurse AI OS.",
        "about_href": "ar/about.html", "about_label": "المؤسس",
        "source_label": "أُنشئ هذا الموجز المتاح من ملف Markdown المرجعي.",
        "source_link": "عرض المصدر", "center_label": "المركز الإعلامي",
        "footer": "🕯️ احملوا المصباح. احفظوا السجل. Agents propose. Humans judge. Nurses steward.",
    },
    "media-hi": {
        "lang": "hi", "dir": "ltr", "description": "Nurse AI OS का सुलभ हिंदी मीडिया संक्षेप।",
        "about_href": "hi/about.html", "about_label": "संस्थापक",
        "source_label": "यह accessible web brief canonical Markdown से बनाया गया है।",
        "source_link": "स्रोत देखें", "center_label": "मीडिया केंद्र",
        "footer": "🕯️ दीपक लेकर चलें। लेखा सुरक्षित रखें। Agents propose. Humans judge. Nurses steward.",
    },
}

# Per-language rendering config for translated documents. PDF builds are
# network-isolated: all fonts come from the digest-pinned renderer image or the
# repository's licensed Chinese subset.
LANG_META = {
    "media": {
        "lang": "en", "dir": "ltr",
        "css": "thead{display:table-header-group;}tr{break-inside:avoid;page-break-inside:avoid;}",
    },
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

    "media-ru": {
        "lang": "ru", "dir": "ltr",
        "css": "h1,h2,h3,h4{font-family:'DejaVu Serif',serif;}",
    },
    "media-zh": {
        "lang": "zh-Hans", "dir": "ltr",
        "css": "body,h1,h2,h3,h4{font-family:'Noto Sans SC Media',sans-serif;}",
    },

    "media-fr": {"lang": "fr", "dir": "ltr"},
    "media-es": {"lang": "es", "dir": "ltr"},
    "media-tl": {"lang": "tl", "dir": "ltr"},
    "media-vi": {
        "lang": "vi", "dir": "ltr",
        "font_links": "",
        "css": "body,h1,h2,h3,h4{font-family:'DejaVu Sans',sans-serif;}",
    },
}

CSS = """
@page { size: letter; margin: 0.85in 0.8in; }
@font-face { font-family: 'Noto Sans SC Media';
             src: url('fonts/NotoSansSC-Media.woff2') format('woff2');
             font-style: normal; font-weight: 100 900; }

:root { --navy:#10233a; --teal:#1f6f6f; --gold:#c9942f; --ink:#2c3540; --muted:#5b6570; }
* { box-sizing: border-box; }
body { font-family: 'DejaVu Sans', sans-serif;
       color: var(--ink); font-size: 10.5pt; line-height: 1.55; margin: 0; }
h1, h2, h3, h4 { font-family: 'DejaVu Serif', serif;
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

FONTS = ""


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


def build(key: str, chrome: str | None, renderer: str | None = None) -> None:
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
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", dir=out.parent, delete=False, encoding="utf-8"
    ) as tf:
        tf.write(html)
        tmp = tf.name
    with tempfile.NamedTemporaryFile(
        "wb", suffix=".raw.pdf", dir=out.parent, delete=False
    ) as pf:
        raw_pdf = Path(pf.name)
    try:
        if renderer:
            command = [renderer, tmp, str(raw_pdf)]
        else:
            command = [chrome, "--headless", "--no-sandbox", "--disable-gpu",
                       "--virtual-time-budget=15000", "--no-pdf-header-footer",
                       f"--print-to-pdf={raw_pdf}", f"file://{tmp}"]
        try:
            subprocess.run(command, check=True, capture_output=True, timeout=300)
        except subprocess.CalledProcessError as exc:
            if exc.stdout:
                sys.stderr.write(exc.stdout.decode("utf-8", errors="replace"))
            if exc.stderr:
                sys.stderr.write(exc.stderr.decode("utf-8", errors="replace"))
            raise
        canonicalize_pdf(raw_pdf, out, title, source_digest)
    finally:
        os.unlink(tmp)
        raw_pdf.unlink(missing_ok=True)
    print(f"built {out_rel} ({out.stat().st_size} bytes)")


def build_html(key: str) -> None:
    """Build accessible web text when the PDF engine cannot preserve logical text."""
    src_rel, out_rel, title = HTML_DOCS[key]
    meta = HTML_META[key]
    src, out = ROOT / src_rel, ROOT / out_rel
    source_bytes = src.read_bytes()
    source_digest = hashlib.sha256(source_bytes).hexdigest()
    body = markdown.markdown(source_bytes.decode("utf-8"),
                             extensions=["tables", "fenced_code", "sane_lists", "smarty"])
    if key == "media-ar":
        body = body.replace("Nurse AI OS™", '<bdi dir="ltr">Nurse AI OS™</bdi>', 1)
        source_heading = "<h2>Directive v1.1 canonical status</h2>"
        if body.count(source_heading) != 1:
            raise RuntimeError("Arabic media source-control heading missing or duplicated")
        before_source, source_block = body.split(source_heading, 1)
        if "</ul>" not in source_block:
            raise RuntimeError("Arabic media source-control list missing")
        source_block = source_block.replace("</ul>", "</ul></section>", 1)
        body = before_source + '<section lang="en" dir="ltr">' + source_heading + source_block
    page = f'''<!DOCTYPE html>
<html lang="{meta["lang"]}" dir="{meta["dir"]}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html_lib.escape(title)}</title><meta name="description" content="{html_lib.escape(meta["description"], quote=True)}">
<meta name="source-sha256" content="{source_digest}"><link rel="stylesheet" href="assets/nurse-ai.css">
<style>html,body{{max-width:100%;overflow-x:hidden}}.media-brief{{box-sizing:border-box;width:100%;max-width:820px;margin:0 auto;padding:3rem 1.25rem;overflow-wrap:anywhere}}.media-brief *{{box-sizing:border-box;max-width:100%}}.media-brief h1{{font-size:clamp(2rem,6vw,3.6rem);overflow-wrap:anywhere}}.media-brief blockquote{{margin:1rem 0;border-left:4px solid var(--gold-500);padding:1rem 1.2rem;background:var(--linen-50);overflow-wrap:anywhere}}html[dir="rtl"] .media-brief blockquote{{border-left:0;border-right:4px solid var(--gold-500)}}.media-brief li{{margin:.55rem 0}}.source-note{{background:var(--navy-900);color:var(--white);padding:1rem 1.25rem;overflow-wrap:anywhere}}.source-note a{{color:var(--gold-300)}}@media(max-width:640px){{.nav-bar{{flex-wrap:wrap;gap:.65rem}}.nav-links{{width:100%;display:flex;flex-wrap:wrap;justify-content:flex-start;gap:.55rem}}.media-brief{{padding:2rem 1.25rem}}.media-brief h1{{font-size:clamp(2rem,10vw,2.8rem)}}}}</style></head>
<body><header class="site-header"><nav class="nav-bar"><a class="brand" href="index.html"><span class="lamp">🕯️</span> Nurse AI OS</a><div class="nav-links"><a href="media.html">{html_lib.escape(meta["center_label"])}</a><a href="{meta["about_href"]}">{html_lib.escape(meta["about_label"])}</a><a class="nav-cta" href="soul-quiz.html">SOUL Quiz</a></div></nav></header>
<main id="main-content" class="media-brief"><div class="source-note">{html_lib.escape(meta["source_label"])} <a href="{src_rel}">{html_lib.escape(meta["source_link"])}</a> · <a href="media.html">{html_lib.escape(meta["center_label"])}</a></div>{body}</main>
<footer class="site-footer"><div class="container"><p class="footer-motto">{html_lib.escape(meta["footer"])}</p></div></footer><script src="assets/site-shell.js" defer></script></body></html>'''
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
    renderer = os.environ.get("MEDIA_PDF_RENDERER")
    if renderer and not Path(renderer).is_file():
        sys.exit(f"MEDIA_PDF_RENDERER does not exist: {renderer}")
    chrome = None
    for t in targets:
        if t in DOCS:
            if not renderer:
                chrome = chrome or find_chrome()
            build(t, chrome, renderer)
        elif t in HTML_DOCS:
            build_html(t)
        else:
            choices = ", ".join([*DOCS, *HTML_DOCS])
            sys.exit(f"unknown target {t!r} — choose from {choices}")
