#!/usr/bin/env python3
"""
Pull the Attachment A exhibit out of a Bluebeam packet's extracted text.

The exhibits in OneDrive cannot be downloaded as PDFs from this session -- the
Graph search returns no downloadUrl, and read_resource hands back extracted
text instead of bytes. That text is enough: the page footers survive, so the
exhibit body can still be located inside the packet, and Word's line breaks
survive as runs of two or more spaces.

Input is whatever the connector wrote to disk, in either shape:
  - a JSON array [{"type": "text", "text": "..."}]   (persisted tool output)
  - plain text                                       (large-output spill file)

Output is one .txt per exhibit in 00-source-docs/voice-corpus/mine/text/,
named for the subcontractor, which build_voice_corpus.py reads as `self`.

Usage:
  python3 scripts/ingest_packet_text.py <dir-with-dumps> [--dry-run]
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEST = ROOT / "00-source-docs" / "voice-corpus" / "mine" / "text"

FOOTER = re.compile(r"Page (\d+) of (\d+)")
HEADING = "ATTACHMENT A SCOPE OF WORK"
# Both registers appear: a Subcontract names a Subcontractor, a professional
# services Agreement names a Consultant.
PARTY = re.compile(r"(?:Subcontractor|Consultant|Supplier)\s*:\s+([^\n]{3,60}?)\s{2,}")


def load(path):
    raw = path.read_text(encoding="utf-8", errors="replace")
    try:
        obj = json.loads(raw)
    except ValueError:
        return raw
    if isinstance(obj, list):
        return "".join(x.get("text", "") for x in obj if isinstance(x, dict))
    return raw


def exhibit_pages(text):
    """The packet's Attachment A body, as a list of page strings.

    A FINAL packet is the exhibit plus the Bid Form, the subcontractor's own
    proposal, and the descope emails -- and several of those carry their own
    "Page 1 of N" footers. The exhibit is the one whose first page also holds
    the ATTACHMENT A SCOPE OF WORK heading.
    """
    pages = text.split("\n")
    for i, page in enumerate(pages):
        m = FOOTER.search(page)
        if m and m.group(1) == "1" and HEADING in page:
            span = int(m.group(2))
            return pages[i:i + span]
    return []


def lines_of(page):
    """Recover the original lines. Word's breaks come back as 2+ spaces."""
    return [ln.strip() for ln in re.split(r"\s{2,}", page) if ln.strip()]


def party_of(text):
    m = PARTY.search(text)
    if not m:
        return None
    name = re.sub(r"[^\w &.'-]", " ", m.group(1)).strip()
    return re.sub(r"\s+", " ", name)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="directory holding the connector's text dumps")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.is_dir():
        sys.exit(f"not a directory: {src}")

    DEST.mkdir(parents=True, exist_ok=True)
    written = skipped = 0

    for path in sorted(src.iterdir()):
        if not path.is_file():
            continue
        text = load(path)
        if HEADING not in text:
            continue
        pages = exhibit_pages(text)
        if not pages:
            print(f"  ! {path.name}: heading present but no page-1 footer found")
            skipped += 1
            continue

        name = party_of(pages[0]) or path.stem
        body = "\n".join(ln for page in pages for ln in lines_of(page))
        out = DEST / f"{name}.txt"
        print(f"  {name:34} {len(pages)} pages, {len(body.splitlines())} lines"
              f"{'  (dry run)' if args.dry_run else ''}")
        if not args.dry_run:
            out.write_text(body)
        written += 1

    print(f"\n{written} exhibit(s) written to {DEST.relative_to(ROOT)}"
          + (f", {skipped} skipped" if skipped else ""))


if __name__ == "__main__":
    main()
