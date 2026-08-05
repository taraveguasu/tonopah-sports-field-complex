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


# Sheet-level probes run against the structured drawing corpus, not the flat text.
# Each was confirmed by reading the sheet directly first.
SHEET_PROBES = [
    ("M0-05", "table", r"FCU\s*\|?\s*5.*FXSA18AAVJU.*RESTROOMS",
     "FCU-5 restroom unit keeps its model on the same row"),
    ("M0-05", "table", r"DAIKIN FXSA30AAVJU", "FCU-3/4 team-room units resolve"),
    ("A10-30", "keynote", r"FILLER, PAINT COLOR TO MATCH METAL LOCKERS",
     "Addendum #1's new 9-07 filler keynote paired to its tag"),
    ("A10-30", "keynote", r"METAL LOCKERS, CFCI", "9-08 paired, BOD deleted by addendum"),
    ("A11-10", "table", r"\b106A\b", "door schedule reaches door 106A"),
    ("A11-10", "table", r"\b113\b", "door schedule reaches the last door"),
    ("A1-20", "table", r"DAKTRONICS|FB-2021", "Site Equipment Matrix at ADD-1 revision"),
    ("GD", "any", r"4\"? ?TYPE II|TYPE II", "grading details carry the revised paving section"),
    ("L1.03", "any", r"(?i)track|curb", "landscape detail sheet content present"),
]


# Proposal-corpus probes. Each fact below was read off the source document by hand
# before being written here. They guard the two things filename-based indexing got
# wrong: that a document is matched to the right package, and that the scope text
# harvested is the bidder's own rather than CORE's blank form.
PROPOSAL_PROBES = [
    ("Sahara", "RFP-030", "exclusions_scope_specific", r"(?i)over ?excavation",
     "Sahara's own exclusion survives, not CORE form boilerplate"),
    ("Sahara", "RFP-030", "exclusions_scope_specific", r"(?i)caliche|hard rock",
     "Sahara excludes caliche/hard rock — contradicts the RFP-030 scope doc"),
    ("NewCom TAB", "RFP-008", "price", r"^1924851$",
     "TAB's price is their own $1,924,851, not the tab's transposed $3,152,033"),
    ("TAB Homework Response.pdf", "RFP-008", "date", r"^2026-05-22$",
     "TAB homework response dated ten days after bid opening"),
    ("TAB Homework Response.pdf", "RFP-008", "any", r"(?i)delete trench drain",
     "TAB's deduct for deleting the trench drain — bears on the RFP-030 ruling"),
    ("Elite Sports - Track Asphalt", "RFP-021", "matched", r".",
     "a homework file whose name says neither 'homework' nor its package still lands"),
    ("Henderson ALT block Pricing", "RFP-031", "matched", r".",
     "Henderson's alternate block pricing matched by firm, not filename"),
    ("Tahoe Fence Scope Review", "RFP-023", "matched", r".",
     "an unfilled agenda template still matches its package"),
]


# Spec-catalog probes. Each was confirmed against the manual or a scope doc first.
# They guard the assignment layer: that every technical section has an owner, that
# the owner is the right trade, and that a missing spec is reported as missing
# rather than fuzzy-matched onto a neighbour.
SPEC_PROBES = [
    ("assigned", "04 05 03", "RFP-031",
     "the mason has the masonry mortar/grout section, which his scope doc never cited"),
    ("assigned", "04 20 16", "RFP-031", "and reinforced unit masonry"),
    ("assigned", "26 56 00", "RFP-103", "exterior/sports-field lighting sits with electrical"),
    ("assigned", "23 05 93", "RFP-100", "test & balance stays in the HVAC package per its title"),
    ("assigned", "08 31 00", "RFP-060", "access panels install with the framer per PM ruling"),
    ("assigned", "32 18 23.33", "RFP-021", "running track surfacing"),
    ("assigned", "02 41 00", "RFP-008", "demolition, per ruling, against RFP-002's own citation"),
    ("count", "RFP-103", "21", "all twenty-one Division 26 sections plus Division 27"),
    ("count", "RFP-098", "11", "all eleven Division 22 sections"),
    ("no_section", "ITB-066", "", "fluid-applied flooring correctly holds none after the ruling"),
    ("gap", "07 84 00", "RFP-103", "firestopping cited but absent from the manual"),
    ("gap", "03 35 00", "ITB-067", "concrete finishing's own section is absent"),
    ("correction", "04 43 36C", "00 43 36C", "the mis-numbered procurement form is corrected"),
    ("unassigned", "", "0", "no technical section is left without an owner"),
]


def spec_probe(kind, a, b):
    p = ROOT / "01-index" / "spec-section-catalog.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    if kind == "assigned":
        return any(s["section"] == a and s.get("primary_package") == b for s in d["sections"])
    if kind == "count":
        return len(d["sections_by_package"].get(a, [])) >= int(b)
    if kind == "no_section":
        return a in d["packages_with_no_primary_section"]
    if kind == "gap":
        g = d["cited_but_absent_from_manual"].get(a)
        return bool(g and b in g["cited_by"] and g["note"]
                    and not g["note"].startswith("No section with"))
    if kind == "correction":
        c = d["number_corrections"].get(a)
        return bool(c and c["corrected_to"] == b)
    if kind == "unassigned":
        return sum(1 for s in d["sections"] if s.get("primary_package") is None
                   and s.get("basis") != "not_a_technical_section") == int(b)
    return False


def proposal_probe(file_frag, pkg, field, rx):
    p = ROOT / "01-index" / "proposal-content.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text())
    docs = [d for d in data["documents"] if file_frag.lower() in d["file"].lower()]
    if not docs:
        return False
    for d in docs:
        pkgs = set(d["packages"]) | set(d.get("packages_by_firm_match", []))
        if pkg not in pkgs:
            continue
        if field == "matched":
            return True
        if field == "price":
            if d["price"] and re.search(rx, str(d["price"])):
                return True
            continue
        if field == "date":
            if d["date"] and re.search(rx, d["date"]):
                return True
            continue
        if field == "any":
            hay = "\n".join(d["inclusions"] + d["exclusions_all"] +
                            d["clarifications"] + d["alternates"] + d["notes"] +
                            d.get("priced_line_items", []))
        else:
            hay = "\n".join(d.get(field, []))
        if re.search(rx, hay):
            return True
    return False


def sheet_probe(sheet, kind, rx):
    import json as _j
    p = ROOT / "01-index" / "sheet-structured.json"
    if not p.exists():
        return None
    data = {r["sheet"]: r for r in _j.loads(p.read_text())["sheets"]}
    r = data.get(sheet)
    if not r:
        return False
    hay = []
    if kind in ("table", "any"):
        for t in r.get("table_detail", []):
            # Both views: the resolved grid, and the raw baseline lines. A fact is
            # captured if either holds it — that is the point of storing both.
            for row in t.get("rows", []):
                hay.append(" | ".join(c for c in row if c))
            hay += t.get("raw_lines", [])
    if kind in ("keynote", "any"):
        hay += [f"{k} {v}" for k, v in r.get("keynotes", {}).items()]
    if kind == "any":
        f = ROOT / r["layout_file"]
        if f.exists():
            hay.append(f.read_text(errors="ignore"))
    return any(re.search(rx, h, re.I) for h in hay)


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

    print("\nSHEET PROBES (structured drawing corpus)")
    sfails = 0
    for sheet, kind, rx, label in SHEET_PROBES:
        ok = sheet_probe(sheet, kind, rx)
        if ok is None:
            print("  [SKIP] sheet-structured.json not built yet"); break
        print(("  [PASS] " if ok else "  [FAIL] ") + f"{sheet}: {label}")
        if not ok:
            sfails += 1
    fails += sfails

    print("\nPROPOSAL PROBES (bidder documents, matched and read)")
    for frag, pkg, field, rx, label in PROPOSAL_PROBES:
        ok = proposal_probe(frag, pkg, field, rx)
        if ok is None:
            print("  [SKIP] proposal-content.json not built yet"); break
        print(("  [PASS] " if ok else "  [FAIL] ") + f"{pkg} {frag}: {label}")
        if not ok:
            fails += 1

    print("\nSPEC-CATALOG PROBES (section assignment and gap reporting)")
    for kind, a, b, label in SPEC_PROBES:
        ok = spec_probe(kind, a, b)
        if ok is None:
            print("  [SKIP] spec-section-catalog.json not built yet"); break
        print(("  [PASS] " if ok else "  [FAIL] ") + f"{a or kind}: {label}")
        if not ok:
            fails += 1

    total = (len(PROBES) + len(SHEET_PROBES) + len(PROPOSAL_PROBES) + len(SPEC_PROBES))
    print(f"\nprobe failures: {fails}/{total}")
    t = man["_totals"]
    print(f"corpus: {t['chars']:,} chars across {t['documents']} documents, "
          f"{t['ocr_pages']} pages recovered by OCR, {t['thin']} flagged THIN")
    return 1 if (fails or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
