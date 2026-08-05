#!/usr/bin/env python3
"""
Split the drawing extractions into one text file per sheet, at its current revision.

The whole-document extractions are page-delimited; drawing-sheet-catalog.json maps
sheet number to page index. This produces the per-sheet corpus every downstream
query needs — "what does A11-10 say" has to be answerable without opening a 93 MB
PDF and counting pages.

Sheets reissued by Addendum #1 are taken from the revised PDF, and the superseded
base version is written alongside with a .SUPERSEDED suffix so the change is still
inspectable.

Also scores each sheet for what its text layer actually yielded, so the vision pass
that follows can be aimed at the sheets that need it rather than run blind.

Usage:  python3 scripts/split_sheets.py
Writes: 01-index/sheets/<SHEET>.txt  (+ .SUPERSEDED.txt where applicable)
        01-index/sheet-corpus.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "01-index" / "document-text"
INDEX = ROOT / "01-index"
OUT = INDEX / "sheets"

# Sheets Addendum #1 reissued -> (revised source doc, page index within it)
REVISED = {
    "G0-00": ("06-addenda/Addendum #1 (05.06.26)/Revised Architectural Sheets (ADD 1).pdf", 0),
    "LS1-10": ("06-addenda/Addendum #1 (05.06.26)/Revised Architectural Sheets (ADD 1).pdf", 1),
    "A1-20": ("06-addenda/Addendum #1 (05.06.26)/Revised Architectural Sheets (ADD 1).pdf", 2),
    "A2-10": ("06-addenda/Addendum #1 (05.06.26)/Revised Architectural Sheets (ADD 1).pdf", 3),
    "A10-30": ("06-addenda/Addendum #1 (05.06.26)/Revised Architectural Sheets (ADD 1).pdf", 4),
    "C1": ("06-addenda/Addendum #1 (05.06.26)/Revised Civil Sheets (ADD 1).pdf", 0),
    "GD": ("06-addenda/Addendum #1 (05.06.26)/Revised Civil Sheets (ADD 1).pdf", 1),
}

PAGE_RE = re.compile(r"^===== PAGE (\d+) =====$", re.M)

# Signals that tell us what a sheet's text layer actually delivered.
SIGNALS = {
    "schedule": re.compile(r"\bSCHEDULE\b", re.I),
    "keynotes": re.compile(r"\bKEY ?NOTES?\b", re.I),
    "general_notes": re.compile(r"\bGENERAL NOTES\b|\bSHEET NOTES\b", re.I),
    "legend": re.compile(r"\bLEGEND\b", re.I),
    "detail_callouts": re.compile(r"\b(?:SEE|REFER TO)\s+(?:SHEET|DETAIL|DWG)", re.I),
    "revision_block": re.compile(r"\bADDENDUM\b|\bREV\b\s+\bDATE\b", re.I),
    "equipment_tags": re.compile(r"\b(?:FCU|EF|DH|CU|BS|RTU|WH|AHU|P-\d|EM-\d)\b"),
    "dimensions": re.compile(r"\d+'\s*-\s*\d+\"|\b\d+\"\s*O\.?C\.?"),
}


def pages_of(doc_rel):
    f = TEXT / (doc_rel + ".txt")
    if not f.exists():
        return None
    body = f.read_text(errors="ignore")
    parts = PAGE_RE.split(body)
    # parts = [pre, '1', text1, '2', text2, ...]
    out = {}
    for i in range(1, len(parts) - 1, 2):
        out[int(parts[i]) - 1] = parts[i + 1]
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    catalog = json.loads((INDEX / "drawing-sheet-catalog.json").read_text())["sheets"]

    cache = {}
    def get(doc):
        if doc not in cache:
            cache[doc] = pages_of(doc)
        return cache[doc]

    recs, missing = [], []
    for e in catalog:
        sheet = e["sheet_number"].split()[0]
        base_doc, base_pg = e["source_file"], e["page_0idx"]

        # current revision
        if sheet in REVISED:
            cur_doc, cur_pg = REVISED[sheet]
            revision = "ADDENDUM #1 (05.06.26)"
        else:
            cur_doc, cur_pg = base_doc, base_pg
            revision = "BID DOCS (04.20.26)"

        pg = get(cur_doc)
        if pg is None or cur_pg not in pg:
            missing.append((sheet, cur_doc, cur_pg)); continue
        text = pg[cur_pg].strip()

        header = (f"SHEET: {sheet}\nTITLE: {e['sheet_title']}\nREVISION: {revision}\n"
                  f"SOURCE: {cur_doc} (page {cur_pg+1})\n" + "=" * 70 + "\n")
        (OUT / f"{sheet}.txt").write_text(header + text)

        rec = {"sheet": sheet, "title": e["sheet_title"], "revision": revision,
               "source": cur_doc, "page": cur_pg + 1, "chars": len(text),
               "file": f"01-index/sheets/{sheet}.txt"}

        found = [k for k, rx in SIGNALS.items() if rx.search(text)]
        rec["signals"] = found
        # A sheet whose text layer is thin, or which has a schedule/keynote block we
        # can see referenced but little text, is a vision candidate.
        rec["needs_vision"] = len(text) < 900 or (
            ("keynotes" in found or "schedule" in found) and len(text) < 2500)
        recs.append(rec)

        if sheet in REVISED:
            bp = get(base_doc)
            if bp and base_pg in bp:
                (OUT / f"{sheet}.SUPERSEDED.txt").write_text(
                    f"SHEET: {sheet} — SUPERSEDED BASE-BID VERSION\n"
                    f"Superseded by ADDENDUM #1 (05.06.26). Retained for diffing only.\n"
                    f"SOURCE: {base_doc} (page {base_pg+1})\n" + "=" * 70 + "\n"
                    + bp[base_pg].strip())
                rec["superseded_file"] = f"01-index/sheets/{sheet}.SUPERSEDED.txt"

    corpus = {
        "_generated": "2026-08-04",
        "_purpose": "One text file per drawing sheet at its current revision. Downstream "
                    "queries read these, not the source PDFs.",
        "_revision_policy": "Sheets reissued by Addendum #1 are taken from the revised PDF. "
                            "The base version is kept as <SHEET>.SUPERSEDED.txt for diffing.",
        "_totals": {
            "sheets": len(recs),
            "at_addendum_revision": sum(1 for r in recs if r["revision"].startswith("ADDENDUM")),
            "chars": sum(r["chars"] for r in recs),
            "needing_vision": sum(1 for r in recs if r["needs_vision"]),
            "missing": len(missing),
        },
        "sheets": recs,
        "_missing": [{"sheet": s, "doc": d, "page": p + 1} for s, d, p in missing],
    }
    (INDEX / "sheet-corpus.json").write_text(json.dumps(corpus, indent=2) + "\n")

    t = corpus["_totals"]
    print(f"sheets written        : {t['sheets']}")
    print(f"at addendum revision  : {t['at_addendum_revision']}")
    print(f"total chars           : {t['chars']:,}")
    print(f"flagged needs_vision  : {t['needing_vision']}")
    print(f"missing               : {t['missing']}")
    if missing:
        for s, d, p in missing[:10]:
            print(f"    {s}  {d} p{p+1}")
    print("\nthinnest sheets (vision candidates):")
    for r in sorted(recs, key=lambda x: x["chars"])[:14]:
        print(f"  {r['chars']:>6}  {r['sheet']:<9} {r['title'][:44]:<44} {','.join(r['signals'][:3])}")


if __name__ == "__main__":
    main()
