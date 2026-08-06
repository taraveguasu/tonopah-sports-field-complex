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
    # PM rulings 08.05.26 closing four gaps. Each must show as closed AND put the
    # replacement section into the package's list -- a ruling that does not reach
    # the package's sections has had no effect.
    ("closed", "03 35 00", "03 30 00", "ITB-067 references cast-in-place concrete instead"),
    ("closed", "07 13 00", "07 25 00", "ITB-040 uses weather barriers"),
    ("closed", "32 11 23", "31 20 00", "aggregate base is covered by earth moving"),
    ("closed", "07 84 00", "", "firestopping needs no action -- no rated assemblies"),
    ("has_section", "ITB-067", "03 30 00", "the ruling reached ITB-067's section list"),
    ("has_section", "ITB-040", "07 25 00", "the ruling reached ITB-040's section list"),
    ("has_section", "RFP-030", "31 20 00", "the ruling reached RFP-030's section list"),
    ("no_rated_walls", "", "", "the partition schedule publishes no rated assembly"),
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
    if kind == "closed":
        g = d["cited_but_absent_from_manual"].get(a)
        if not (g and g["status"] == "CLOSED BY PM RULING"):
            return False
        return (g["pm_resolution"]["resolved_to"] or "") == b
    if kind == "has_section":
        return b in d["sections_by_package"].get(a, [])
    if kind == "no_rated_walls":
        # Read the partition schedule itself rather than trusting the catalog.
        # The mark's third character is the fire-rating code; 0 is NO RATING.
        sp = ROOT / "01-index" / "sheet-structured.json"
        if not sp.exists():
            return False
        r = {x["sheet"]: x for x in json.loads(sp.read_text())["sheets"]}.get("A2-40")
        if not r:
            return False
        body = (ROOT / r["layout_file"]).read_text(errors="ignore")
        # Match the mark's own shape rather than the label above it: title-block
        # text on this sheet is drawn twice for weight, so the extraction reads
        # "PARTITION PARTITION TYPE TYPE - - 3F0 3F0" and an anchored pattern misses.
        # Mark = core-type digit, height letter, fire-rating digit.
        marks = set(re.findall(r"\b([1-9][BCFL][0-4])\b", body))
        return bool(marks) and all(m[2] == "0" for m in marks)
    if kind == "unassigned":
        return sum(1 for s in d["sections"] if s.get("primary_package") is None
                   and s.get("basis") != "not_a_technical_section") == int(b)
    return False


# Sheet-assignment probes. Each fact was confirmed by opening the sheet earlier:
# A1-20's Site Equipment Matrix lists five CFCI items, A10-30 carries the locker
# keynote, RFP-023's scope doc names A1-20 outright, LS1-10 is life-safety.
ASSIGN_PROBES = [
    ("draft", "A1-20", "RFP-094", "bleachers, from the Site Equipment Matrix"),
    ("draft", "A1-20", "RFP-109", "ticket booth, same matrix"),
    ("draft", "A1-20", "ITB-089", "scoreboard, same matrix (DAKTRONICS FB-2021)"),
    ("draft", "A1-20", "ITB-018", "trash receptacle, same matrix"),
    ("cited", "A1-20", "RFP-023", "RFP-023's scope doc names A1-20 for the Gate Schedule"),
    ("draft", "A10-30", "ITB-077", "lockers, from the 9-08 keynote"),
    ("draft", "A2-40", "RFP-060", "partition schedule belongs to the framer"),
    ("draft", "M0-05", "RFP-100", "mechanical schedules"),
    ("not", "M0-05", "ITB-056", "a passing mention of doors in a mechanical schedule "
                                "must not assign the door package"),
    ("not", "M0-05", "ITB-062", "nor the ceilings package"),
    ("all_pkgs", "LS1-10", "", "life-safety sheet binds every package, assigned to no trade"),
    ("revision", "A10-30", "ADDENDUM", "reissued sheets are read at the addendum revision"),
    ("coverage", "", "", "every sheet reaches a package and every package reaches a sheet"),
]


# Package-record probes. The drafting record is what 33 drafter runs consume, so
# it must carry the rulings and corrections made along the way rather than
# silently reverting to what the source documents said.
PACKAGE_PROBES = [
    ("count", "", "34", "every package has a drafting record, including ITB-070 "
                        "Final Cleaning added by ruling 08.06.26"),
    ("spec", "RFP-031", "04 20 16", "the mason's record carries the masonry section his "
                                    "scope doc never cited"),
    ("spec", "RFP-103", "26 56 00", "electrical carries exterior/sports-field lighting"),
    ("spec", "ITB-067", "03 30 00", "the 08.05.26 ruling reached the record"),
    ("spec", "ITB-040", "07 25 00", "same for weather barriers"),
    ("price", "RFP-008", "1924851", "TAB's corrected price, not the tab's transposition"),
    ("title", "RFP-094", "Bleachers & Press Box", "canonical title, not the mapping's "
                                                  "'Bleacher & Press Box (SUPPLY)'"),
    ("bidders", "RFP-031", "6", "Henderson's two name forms merged into one chain"),
    ("all_bidders", "RFP-030", "Cheek", "losing bidders are present, not just the awarded sub"),
    ("no_dupe_firm", "", "", "no package lists the same firm twice"),
    ("scope_file", "RFP-100", "099 HVAC", "the scope narrative path survives the number drift"),
    ("sheets", "ITB-077", "A10-30", "lockers point at the sheet carrying their keynote"),
    ("authority", "RFP-060", "", "every record states the authority hierarchy"),
    # 08.06.26 rulings. Each must reach the record a drafter reads, or the ruling
    # exists only in a log and has no effect on any exhibit.
    ("spec", "RFP-002", "02 41 00", "A4 — demolition section is in BOTH RFP-002 and RFP-008"),
    ("spec", "ITB-019", "12 93 00", "A2 — site furnishings section is in both, 019 installs"),
    ("no_scope_doc", "ITB-070", "", "E1 — Final Cleaning is a package with no scope narrative"),
    ("removed", "ITB-066", "", "E2 — records that the Owner removed the scope in VE"),
    ("gap_titled", "RFP-045", "07 41 13", "D — the absent section is carried by title, not cited"),
    ("combined", "ITB-077", "RFP-060", "lockers head into RFP-060's subcontract but keep "
                                       "their own exhibit"),
    ("own_scope", "ITB-044", "", "a combined member still drafts from its own scope narrative"),
]


def package_probe(kind, pkg, val):
    d = ROOT / "01-index" / "packages"
    if not d.exists():
        return None
    if kind == "count":
        return len(list(d.glob("*.json"))) == int(val)
    if kind == "no_dupe_firm":
        for f in d.glob("*.json"):
            names = [b["firm"] for b in json.loads(f.read_text())["bidders"]]
            norm = [re.sub(r"[^a-z0-9]", "", n.lower()) for n in names]
            for i, a in enumerate(norm):
                for b in norm[i + 1:]:
                    if a and b and (a.startswith(b) or b.startswith(a)):
                        return False
        return True
    f = d / f"{pkg}.json"
    if not f.exists():
        return False
    r = json.loads(f.read_text())
    if kind == "spec":
        got = {s["section"] for s in r["spec_sections"]["primary"]} | \
              {s["section"] for s in r["spec_sections"]["added_by_pm_ruling"]}
        return val in got
    if kind == "price":
        return str(r["awarded_sub"].get("proposal_price", "")).startswith(val)
    if kind == "title":
        return r["_title"] == val
    if kind == "bidders":
        return len(r["bidders"]) == int(val)
    if kind == "all_bidders":
        return any(val.lower() in b["firm"].lower() for b in r["bidders"])
    if kind == "scope_file":
        return val in r["scope_narrative"]["file"]
    if kind == "sheets":
        return val in [s["sheet"] for s in r["drawings"]["draft_from"]]
    if kind == "authority":
        return len(r.get("document_authority_hierarchy", [])) >= 4
    if kind == "no_scope_doc":
        return r["scope_narrative"]["file"] is None and bool(r["bidders"])
    if kind == "removed":
        return bool(r.get("removed_by_owner"))
    if kind == "combined":
        c = r.get("combined_subcontract")
        return bool(c and c["lead"] == val and pkg in c["members"])
    if kind == "own_scope":
        # The whole point of writing each scope independently: a member still has
        # its own narrative and its own sections, not the lead's.
        return bool(r["scope_narrative"]["file"]) and f"{pkg[-3:]}" in r["scope_narrative"]["file"]
    if kind == "gap_titled":
        g = r["spec_sections"]["cited_by_this_scope_doc_but_absent_from_manual"].get(val)
        return bool(g and "GLOBAL RULE" in g["status"])
    return False


def assign_probe(kind, sheet, pkg):
    p = ROOT / "01-index" / "sheet-package-assignments.json"
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    rows = {r["sheet"]: r for r in d["sheets"]}
    if kind == "coverage":
        return not d["sheets_with_no_package"] and not d["packages_with_no_sheet"]
    r = rows.get(sheet)
    if not r:
        return False
    if kind == "all_pkgs":
        return bool(r.get("applies_to_all_packages"))
    if kind == "revision":
        return r["revision"].startswith(pkg)
    got = r["packages"].get(pkg)
    if kind == "not":
        return not got or got["confidence"] in ("weak", "discipline_only")
    if kind == "cited":
        return bool(got and got["confidence"] == "cited")
    return bool(got and got["confidence"] in ("cited", "strong", "moderate"))


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

    print("\nSHEET-ASSIGNMENT PROBES (packages derived from the scope docs)")
    for kind, sheet, pkg, label in ASSIGN_PROBES:
        ok = assign_probe(kind, sheet, pkg)
        if ok is None:
            print("  [SKIP] sheet-package-assignments.json not built yet"); break
        print(("  [PASS] " if ok else "  [FAIL] ") + f"{sheet or kind} {pkg}: {label}")
        if not ok:
            fails += 1

    print("\nPACKAGE-RECORD PROBES (what the drafter actually consumes)")
    for kind, pkg, val, label in PACKAGE_PROBES:
        ok = package_probe(kind, pkg, val)
        if ok is None:
            print("  [SKIP] 01-index/packages/ not built yet"); break
        print(("  [PASS] " if ok else "  [FAIL] ") + f"{pkg or kind}: {label}")
        if not ok:
            fails += 1

    total = (len(PROBES) + len(SHEET_PROBES) + len(PROPOSAL_PROBES) + len(SPEC_PROBES)
             + len(ASSIGN_PROBES) + len(PACKAGE_PROBES))
    print(f"\nprobe failures: {fails}/{total}")
    t = man["_totals"]
    print(f"corpus: {t['chars']:,} chars across {t['documents']} documents, "
          f"{t['ocr_pages']} pages recovered by OCR, {t['thin']} flagged THIN")
    return 1 if (fails or missing) else 0


if __name__ == "__main__":
    sys.exit(main())
