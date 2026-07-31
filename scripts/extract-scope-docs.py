#!/usr/bin/env python3
"""
Extract the text of every Scope of Work .docx (plus the RFP notice and ITB) into
plain text so the index can actually be built from what they SAY, not just from
their filenames.

The first index stored `scope_of_work_doc` as a bare path and never opened the
file. These narratives are the most authoritative statement of what each package
carries -- they resolve trade boundaries that the drawings leave ambiguous.

Usage:  python3 scripts/extract-scope-docs.py
Writes: 00-source-docs/02-trade-scopes-bidform/_extracted/*.txt
        01-index/scope-doc-extraction-manifest.json
"""

import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs" / "02-trade-scopes-bidform"
OUT = SRC / "_extracted"
MANIFEST = ROOT / "01-index" / "scope-doc-extraction-manifest.json"

# Headings the scope docs use. Capturing where each lands lets the indexer cite
# a specific article instead of the whole document.
ARTICLES = [
    "PRECEDENCE", "SCHEDULE", "REASONABLE INFERENCE", "SCOPE OF WORK",
    "INCLUSIONS", "EXCLUSIONS", "CLARIFICATIONS", "ALTERNATES",
    "UNIT PRICING", "ALLOWANCES", "SPECIFIC REQUIREMENTS", "GENERAL REQUIREMENTS",
    "SAFETY", "QUALITY", "CLOSEOUT", "SUBMITTALS", "WARRANTY",
]


def docx_text(path: Path) -> str:
    """Pull readable text out of a .docx, preserving paragraph and table-cell breaks."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    # Paragraph and table-cell boundaries become newlines, then strip all tags.
    xml = re.sub(r"</w:(p|tr)>", "\n", xml)
    xml = re.sub(r"</w:tc>", "\t", xml)
    txt = re.sub(r"<[^>]+>", "", xml)
    # Unescape the handful of entities Word emits.
    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")]:
        txt = txt.replace(a, b)
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def find_articles(txt: str):
    """Record which known articles appear, so the indexer can cite them."""
    found = []
    for art in ARTICLES:
        m = re.search(rf"^\s*{re.escape(art)}\b.*$", txt, re.M | re.I)
        if m:
            found.append({"article": art, "char_offset": m.start()})
    return sorted(found, key=lambda a: a["char_offset"])


def main():
    OUT.mkdir(exist_ok=True)
    docs = sorted(SRC.glob("*.docx"))
    if not docs:
        raise SystemExit(f"no .docx found in {SRC}")

    manifest = {
        "_generated": "2026-07-31",
        "_why": (
            "The initial package-index.json stored scope_of_work_doc as a filename only; the "
            "narratives were never read. PM review found this caused resolvable scope questions "
            "to be flagged as unresolvable. These extractions are the input for the re-index."
        ),
        "documents": [],
    }

    total = 0
    for d in docs:
        txt = docx_text(d)
        dest = OUT / (d.stem + ".txt")
        dest.write_text(txt)
        total += len(txt)
        manifest["documents"].append({
            "source": str(d.relative_to(ROOT / "00-source-docs")),
            "extracted_to": str(dest.relative_to(ROOT / "00-source-docs")),
            "chars": len(txt),
            "articles_found": find_articles(txt),
        })
        print(f"  {len(txt):>7,} chars  {d.name}")

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n")
    print(f"\n{len(docs)} documents, {total:,} chars total")
    print(f"manifest -> {MANIFEST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
