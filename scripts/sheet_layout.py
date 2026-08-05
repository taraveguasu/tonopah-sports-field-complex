#!/usr/bin/env python3
"""
Re-extract every drawing sheet with LAYOUT PRESERVED, and pull out its structured
blocks — keynote legends, schedules, and general notes.

Why this exists: PyMuPDF's plain text extraction returns a drawing's words in
storage order, so a keynote tag and its definition end up many lines apart and a
schedule row is scattered. The content is all present — A11-10's text layer does
contain all 19 door numbers — but the spatial relationships that make it *mean*
something are gone. Coordinates restore them deterministically, which is better
than asking vision to re-read what the PDF already knows.

Three outputs per sheet:
  layout   words grouped into baselines, ordered left to right, wide gaps become
           tabs — schedules read as rows
  keynotes tag -> definition, resolved by picking the instance whose same-baseline
           right-hand text is the most word-like (the legend, not a plan bubble)
  notes    numbered/lettered general and sheet notes

Usage:  python3 scripts/sheet_layout.py
Writes: 01-index/sheets/<SHEET>.layout.txt
        01-index/sheet-structured.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs"
INDEX = ROOT / "01-index"
OUT = INDEX / "sheets"

BASELINE_TOL = 3.0     # points; words within this y-distance share a line
TAB_GAP = 12.0         # points of horizontal gap that becomes a column break

KEYNOTE_RE = re.compile(r"^\d{1,2}-\d{2}$")
NOTE_RE = re.compile(r"^(?:[A-Z]|\d{1,2})[.)]$")
WORDY = re.compile(r"[A-Za-z]{3,}")


def lines_from(page):
    """Group words into baselines, ordered left to right."""
    rows = defaultdict(list)
    for w in page.get_text("words"):
        x0, y0, x1, y1, txt = w[0], w[1], w[2], w[3], w[4]
        rows[round(((y0 + y1) / 2) / BASELINE_TOL)].append((x0, x1, txt))
    out = []
    for key in sorted(rows):
        ws = sorted(rows[key], key=lambda t: t[0])
        parts, prev_x1 = [], None
        for x0, x1, txt in ws:
            if prev_x1 is not None and (x0 - prev_x1) > TAB_GAP:
                parts.append("\t")
            parts.append(txt)
            prev_x1 = x1
        out.append((key * BASELINE_TOL, " ".join(parts).replace(" \t ", "\t")))
    return out


def keynotes_from(page):
    """tag -> definition, choosing the legend instance over plan callout bubbles."""
    words = page.get_text("words")
    tags = [w for w in words if KEYNOTE_RE.fullmatch(w[4])]
    best = {}
    for t in tags:
        y = (t[1] + t[3]) / 2
        same = [w for w in words
                if abs(((w[1] + w[3]) / 2) - y) < BASELINE_TOL
                and w[0] > t[2] and (w[0] - t[2]) < 500]
        txt = " ".join(w[4] for w in sorted(same, key=lambda w: w[0])).strip()
        # A legend entry reads like prose; a plan bubble sits next to other tags.
        score = len(WORDY.findall(txt))
        if score and score > best.get(t[4], (0, ""))[0]:
            best[t[4]] = (score, txt)
    return {k: v[1] for k, v in sorted(best.items())}


def notes_from(lines):
    """Numbered/lettered notes under a NOTES-style heading."""
    out, capturing = [], False
    for _, ln in lines:
        s = ln.strip()
        if re.search(r"\b(GENERAL|SHEET|DEMOLITION|CONSTRUCTION)?\s*NOTES\b", s, re.I) and len(s) < 60:
            capturing = True
            continue
        if capturing:
            if re.match(r"^(?:[A-Z]|\d{1,2})[.)]\s+\S", s) and len(s) > 12:
                out.append(s)
            elif len(s) > 90:
                out.append(s)
            elif not s:
                continue
            elif len(out) > 2 and re.match(r"^[A-Z ]{6,}$", s):
                capturing = False
    return out[:80]


def tables_from(page):
    """Real table reconstruction.

    Baseline grouping cannot recover a two-line cell: on M0-05 the manufacturer
    reads DAIKIN on one line and FXSA18AAVJU on the next, so the model breaks away
    from its row and FCU-5's restroom unit loses its model number. PyMuPDF's table
    finder resolves the grid properly and merges those cells.
    """
    out = []
    try:
        found = page.find_tables()
    except Exception:
        return out
    for t in found.tables:
        try:
            rows = t.extract()
        except Exception:
            continue
        clean = []
        for r in rows:
            cells = [(c or "").replace("\n", " ").strip() for c in r]
            if any(cells):
                clean.append(cells)
        if len(clean) < 2:
            continue
        # Name the table from the first row that looks like a title.
        name = None
        for r in clean[:3]:
            joined = " ".join(c for c in r if c)
            m = re.search(r"([A-Z][A-Z0-9 &/,\-]*(?:SCHEDULE|MATRIX|LEGEND|INDEX))", joined)
            if m:
                name = m.group(1).strip()
                break
        out.append({
            "table": name or f"table ({clean[0][0][:28] if clean[0] and clean[0][0] else 'untitled'})",
            "rows": clean[:80],
            "row_count": len(clean),
            "col_count": max(len(r) for r in clean),
        })
    return out


def main():
    corpus = json.loads((INDEX / "sheet-corpus.json").read_text())
    docs = {}
    recs = []
    for r in corpus["sheets"]:
        doc = r["source"]
        if doc not in docs:
            docs[doc] = fitz.open(SRC / doc)
        page = docs[doc][r["page"] - 1]

        lines = lines_from(page)
        kn = keynotes_from(page)
        notes = notes_from(lines)
        scheds = tables_from(page)

        header = (f"SHEET: {r['sheet']}\nTITLE: {r['title']}\nREVISION: {r['revision']}\n"
                  f"SOURCE: {doc} (page {r['page']})\n"
                  f"LAYOUT-PRESERVED EXTRACTION — baselines grouped, columns tab-separated\n"
                  + "=" * 74 + "\n")
        body = "\n".join(ln for _, ln in lines)
        (OUT / f"{r['sheet']}.layout.txt").write_text(header + body)

        recs.append({
            "sheet": r["sheet"], "title": r["title"], "revision": r["revision"],
            "layout_file": f"01-index/sheets/{r['sheet']}.layout.txt",
            "chars": len(body), "lines": len(lines),
            "keynotes": kn, "keynote_count": len(kn),
            "tables": [s["table"] for s in scheds],
            "table_rows": sum(s["row_count"] for s in scheds),
            "table_detail": scheds,
            "notes_captured": len(notes), "notes": notes,
        })

    for d in docs.values():
        d.close()

    out = {
        "_generated": "2026-08-04",
        "_method": ("Words extracted with coordinates, grouped into baselines, ordered left to "
                    "right, with wide horizontal gaps rendered as tabs. Keynote tags paired to "
                    "definitions by same-baseline proximity, choosing the most word-like instance "
                    "so legend entries win over plan callout bubbles."),
        "_totals": {
            "sheets": len(recs),
            "chars": sum(r["chars"] for r in recs),
            "keynote_definitions": sum(r["keynote_count"] for r in recs),
            "sheets_with_keynotes": sum(1 for r in recs if r["keynote_count"]),
            "tables": sum(len(r["tables"]) for r in recs),
            "table_rows": sum(r["table_rows"] for r in recs),
            "notes": sum(r["notes_captured"] for r in recs),
        },
        "sheets": recs,
    }
    (INDEX / "sheet-structured.json").write_text(json.dumps(out, indent=2) + "\n")
    t = out["_totals"]
    for k, v in t.items():
        print(f"  {k:24} {v:,}")


if __name__ == "__main__":
    main()
