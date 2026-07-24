#!/usr/bin/env python3
"""Generate language-locked entry pages docs/en/ and docs/zh/ from docs/index.html.

The bilingual root (docs/index.html) is the single source of truth. This script
derives two sub-pages that open locked to one language (no flash) and whose
toggle navigates to the sibling path. Re-run after editing docs/index.html:

    python3 gen_lang_pages.py
"""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "docs" / "index.html"

def build(lang: str) -> str:
    html = SRC.read_text(encoding="utf-8")

    # Assets live one directory up now.
    html = html.replace('"assets/', '"../assets/')

    # Lock the language: pre-set the <html> so there is no flash of the other
    # language before JS runs, and expose __FORCE_LANG__ for the toggle script.
    if lang == "zh":
        html = html.replace('<html lang="en">', '<html lang="zh" class="zh">', 1)
    force = f'<head>\n    <script>window.__FORCE_LANG__="{lang}";</script>'
    html = html.replace("<head>", force, 1)

    # Canonical + hreflang alternates for the two locked pages and the root.
    links = (
        '\n    <link rel="canonical" href="https://robo-harness.com/{lang}/">'
        '\n    <link rel="alternate" hreflang="en" href="https://robo-harness.com/en/">'
        '\n    <link rel="alternate" hreflang="zh" href="https://robo-harness.com/zh/">'
        '\n    <link rel="alternate" hreflang="x-default" href="https://robo-harness.com/">'
    ).format(lang=lang)
    html = html.replace("</head>", links + "\n</head>", 1)
    return html

for lang in ("en", "zh"):
    out_dir = ROOT / "docs" / lang
    out_dir.mkdir(exist_ok=True)
    (out_dir / "index.html").write_text(build(lang), encoding="utf-8")
    print(f"wrote docs/{lang}/index.html")
