#!/usr/bin/env python3
"""
Verify the extraction by searching it for facts we already know are true.

Coverage counts are not evidence. The previous audits all passed while the work
was undone, because each measured its own artifact. This one asks a different
question: can the extracted corpus answer questions whose answers were confirmed
by reading the source directly?

Every probe below was verified by hand against the original document. If a probe
fails, the extraction is incomplete regardless of what the manifest reports.

Usage:  python3 scripts/verify_extraction.py
Exit:   non-zero if any probe fails or any document is missing an extraction.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs"
TEXT = ROOT / "01-index" / "document-text"
MANIFEST = ROOT / "01-index" / "extraction-manifest.json"

# (label, path-substring the fact should live in, regex that must match)
PROBES = [
    ("FCU-5 restroom unit model (M0-05 schedule)",
     "Bid Plans Vol 2", r"FXSA18AAVJU"),
    ("FCU-5 Daikin manufacturer on the schedule",
     "Bid Plans Vol 2", r"DAIKIN"),
    ("CMU spec has no integral water repellent — ASTM C90 text present",
     "div-04-masonry", r"ASTM\s*C90"),
    ("CMU 'Type I-Moisture Controlled' language",
     "div-04-masonry", r"Moisture\s*Controlled"),
    ("07 19 00 Water Repellents cross-reference from masonry",
     "div-04-masonry", r"07\s?19\s?00"),
    ("Anti-graffiti requires water repellent first coat",
     "div-09-finishes", r"water repellent has been applied"),
    ("Running track spec section exists",
     "div-32-exterior", r"32\s?18\s?23\.33"),
    ("Landscape irrigation section (PM ruling)",
     "div-32-exterior", r"32\s?84\s?00"),
    ("Addendum #1 change list names five sheets",
     "00 91 11 - Addendum", r"C1,\s*GD,\s*G0-00,\s*LS1-10,\s*A1-20"),
    ("RFI #3 locker basis of design",
     "Responses to RFIs", r"Pro Collection"),
    ("RFI #4 fire alarm answer",
     "Responses to RFIs", r"Fire Alarm requir"),
    ("Clarification No.2 prevailing wage — Clark County",
     "Clarification No. 2", r"Clark County"),
    ("Scoreboard revised BOD in addendum sheets",
     "Revised Architectural Sheets", r"DAKTRONICS|FB-2021"),
    ("Geotech report readable",
     "Geotech Report", r"(?i)compaction|bearing|subgrade"),
    ("Asbestos survey readable (OCR)",
     "Asbestos Survey", r"(?i)asbestos"),
    ("Bid form line items readable",
     "Subcontractor Proposal (Bid) Form", r"(?i)alternate|base bid|proposal"),
]


def find_text(substr):
    hits = [p for p in TEXT.rglob("*.txt") if substr.lower() in str(p).lower()]
    return hits


def main():
    if not MANIFEST.exists():
        print("extraction-manifest.json missing — extraction has not finished")
        return 1
    man = json.loads(MANIFEST.read_text())
    docs = {d["file"]: d for d in man["documents"]}

    # 1. every source document has an extraction with content
    missing, thin = [], []
    for p in sorted(SRC.rglob("*")):
        if not p.is_file() or p.name == ".gitkeep" or "/_extracted/" in str(p):
            continue
        rel = str(p.relative_to(SRC))
        d = docs.get(rel)
        if not d:
            missing.append(rel); continue
        if d.get("method") in ("skip", "xls-unsupported", "ERROR"):
            thin.append((rel, d.get("method"))); continue
        f = TEXT / (rel + ".txt")
        if not f.exists() or f.stat().st_size < 200:
            thin.append((rel, f"{f.stat().st_size if f.exists() else 0} bytes"))

    print(f"documents in manifest : {len(docs)}")
    print(f"missing extraction    : {len(missing)}")
    print(f"empty / unextractable : {len(thin)}")
    for r, why in thin[:15]:
        print(f"    {why:>18}  {r[:80]}")

    # 2. probes — facts confirmed by hand against the source
    print("\nPROBES (each verified by hand against the original document)")
    fails = 0
    for label, where, rx in PROBES:
        files = find_text(where)
        if not files:
            print(f"  [NO FILE] {label}  (no extraction matching '{where}')"); fails += 1; continue
        ok = False
        for f in files:
            if re.search(rx, f.read_text(errors="ignore"), re.I):
                ok = True; break
        print(("  [PASS] " if ok else "  [FAIL] ") + label)
        if not ok:
            fails += 1

    print(f"\nprobe failures: {fails}/{len(PROBES)}")
    t = man["_totals"]
    print(f"corpus: {t['chars']:,} chars across {t['documents']} documents, "
          f"{t['ocr_pages']} pages recovered by OCR, {t['thin']} flagged THIN")
    return 1 if (fails or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
