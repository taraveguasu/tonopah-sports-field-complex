#!/usr/bin/env python3
"""
Build the per-package drafting index the scope-drafter consumes.

Stage 2 produced five separate artifacts, each answering one question well and
none of them answering "what does the drafter need in front of it for RFP-030".
This merges them into one self-contained record per package:

    01-index/packages/<package_id>.json     one per package, drafter reads one
    01-index/package-index.json             manifest only, points at the above

ONE FILE PER PACKAGE, deliberately. The skill's rule is that a drafter never sees
the whole index -- cross-contamination between packages is how scope migrates
from one subcontract into another. A single merged file would also be read in
full 33 times, once per drafter run, for the ~3% of it that run needs.

The record carries POINTERS to primary sources plus enough content to know what
to open. It is not a substitute for reading the source: the drafter opens the
scope narrative, the spec sections and the sheets. What it does supply directly
is the bidder scope language, because that is scattered across 246 documents in
four folders and no drafter could reasonably assemble it.

Every bidder is included, not just the awarded sub -- PM direction: a losing
bidder's clarification is often the clearest signal of what the documents left
ambiguous, and that is a primary source of Attachment A inclusions.

Usage:  python3 scripts/build_package_index.py
"""

import json
import re
import shutil
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "01-index"
OUT = INDEX / "packages"
SRC = ROOT / "00-source-docs"

SCOPE_DOC_DIR = "00-source-docs/02-trade-scopes-bidform/_extracted"
SPLIT_DIR = "00-source-docs/04-specs-reports/spec-manual-split"

# package_id -> the Scope of Work narrative filename. The filenames drift from
# the package numbers (ITB-008 filed as 007, RFP-060 as 061, RFP-100 as 099).
SCOPE_DOC = {
    "RFP-002": "Scope of Work - 002 Abatement & Building Wrecking.txt",
    "ITB-008": "Scope of Work - 007 Surveying & Staking.txt",
    "RFP-008": "Scope of Work - 008 Demo, Earthwork, Paving, Utilities, & Striping.txt",
    "RFP-016": "Scope of Work - 016 Landscaping & Irrigation.txt",
    "ITB-018": "Scope of Work - 018 Site Furnishings.txt",
    "ITB-019": "Scope of Work - 019 Track & Field Athletic Equipment.txt",
    "RFP-021": "Scope of Work - 021 Running Track Surfacing.txt",
    "RFP-022": "Scope of Work - 022 Synthetic Turf Sports Field.txt",
    "RFP-023": "Scope of Work - 023 Fencing & Gates.txt",
    "RFP-030": "Scope of Work - 030 Concrete.txt",
    "RFP-031": "Scope of Work - 031 Masonry.txt",
    "RFP-033": "Scope of Work - 033 Structural Steel & Ornamental Metals.txt",
    "ITB-040": "Scope of Work - 040 Moisture Protection & Sealants.txt",
    "ITB-044": "Scope of Work - 044 Insulation.txt",
    "RFP-045": "Scope of Work - 045 Metal Roofing, Fascia & Soffit Panels.txt",
    "ITB-054": "Scope of Work - 054 Special Doors.txt",
    "ITB-056": "Scope of Work - 056 Doors, Frames & Hardware.txt",
    "RFP-060": "Scope of Work - 060 Metal Stud Framing, Drywall & Painting.txt",
    "ITB-062": "Scope of Work - 062 Acoustical Ceilings Treatments.txt",
    "ITB-066": "Scope of Work - 066 Fluid-Applied Floors.txt",
    "ITB-067": "Scope of Work - 067 Concrete Finishing.txt",
    "ITB-071": "Scope of Work - 071 Visual Display Boards & Menu Display Case.txt",
    "ITB-072": "Scope of Work - 072 Building Signage.txt",
    "ITB-074": "Scope of Work - 074 Building & Fire Protection Specialties.txt",
    "ITB-077": "Scope of Work - 077 Lockers.txt",
    "ITB-078": "Scope of Work - 078 Flagpoles.txt",
    "ITB-085": "Scope of Work - 085 Warming Kitchen Food Service Equipment.txt",
    "ITB-089": "Scope of Work - 089 Scoreboards.txt",
    "RFP-094": "Scope of Work - 094 Bleachers & Press Box.txt",
    "RFP-098": "Scope of Work - 098 Plumbing Systems.txt",
    "RFP-100": "Scope of Work - 099 HVAC & Building Controls Systems.txt",
    "RFP-103": "Scope of Work - 103 Electrical & Low Voltage Systems.txt",
    "RFP-109": "Scope of Work - 109 Prefabricated Ticket Booth.txt",
    # PM ruling 08.06.26 (E1). No Scope of Work narrative was ever issued for final
    # cleaning -- proposals were solicited under trade 070 and four came back. Its
    # exhibit is drafted from those proposals and the documents on hand.
    "ITB-070": None,
}

# Canonical package titles, from CLAUDE.md's bid package list. Derived titles are
# not good enough here: this string becomes the exhibit's own heading, and the
# other sources disagree with each other -- the awarded-sub mapping calls RFP-094
# "Bleacher & Press Box (SUPPLY)", the GMP calls ITB-074 "Building & Fire
# Protection Accessories", and a filename slice yields "07 Surveying & Staking".
TITLES = {
    "RFP-002": "Abatement & Building Wrecking",
    "RFP-008": "Site Demolition, Salvage, Earthwork, Asphalt Paving, Wet Utilities, "
               "& Site Signage & Striping",
    "RFP-016": "Landscaping & Irrigation",
    "RFP-021": "Running Track Surfacing",
    "RFP-022": "Synthetic Turf Sports Field",
    "RFP-023": "Fencing & Gates",
    "RFP-030": "Concrete",
    "RFP-031": "Masonry",
    "RFP-033": "Structural Steel & Ornamental Metals",
    "RFP-045": "Metal Roofing, Fascia & Soffit Panels",
    "RFP-060": "Framing, Drywall & Painting (incl. FRP)",
    "RFP-094": "Bleachers & Press Box",
    "RFP-098": "Plumbing Systems",
    "RFP-100": "HVAC & Building Control Systems (incl. Test & Balance)",
    "RFP-103": "Electrical & Low Voltage Systems (incl. Sports Field Lighting)",
    "RFP-109": "Prefabricated Ticket Booth",
    "ITB-008": "Surveying, Layout & Staking",
    "ITB-018": "Site Furnishings",
    "ITB-019": "Track & Field Athletic Equipment",
    "ITB-040": "Moisture Protection & Sealants (incl. Acoustical Caulking)",
    "ITB-044": "Insulation",
    "ITB-054": "Special Doors",
    "ITB-056": "Doors, Frames & Hardware",
    "ITB-062": "Acoustical Ceiling Treatments",
    "ITB-066": "Fluid-Applied Flooring",
    "ITB-067": "Concrete Finishing",
    "ITB-071": "Visual Display Boards & Menu Display Case",
    "ITB-072": "Building Signage",
    "ITB-074": "Building & Fire Protection Specialties (incl. corner guards, cabinets, mirrors)",
    "ITB-077": "Lockers",
    "ITB-078": "Flagpoles",
    "ITB-085": "Warming Kitchen Food Service Equipment",
    "ITB-089": "Scoreboards",
    "ITB-070": "Final Cleaning",
}

# Packages whose scope was removed after bid. They keep a record and an exhibit so
# the file shows the decision rather than a hole.
REMOVED_BY_OWNER = {
    "ITB-066": {
        "ruling_date": "2026-08-06",
        "ruling": "This scope was removed by the Owner in a value engineering exercise.",
        "consequence": "Resinous/epoxy flooring is not built. Those locations become Sealed "
                       "Concrete under ITB-067 (PM ruling 08.04.26). ITB-066 has no remaining "
                       "scope; its exhibit records the removal.",
    },
}

# Packages the PM intends to award under ONE subcontract, each keeping its own
# Attachment A. PM ruling 08.06.26 (D), scope confirmed 08.06.26: write each scope
# independently.
#
# The exhibits stay separate on purpose. Each trade's scope remains independently
# reviewable and independently descopeable, and if the combination does not hold at
# award, the exhibits survive it. What the grouping does change is what counts as an
# overlap: scope-qa must not flag RFP-060 and ITB-044 sharing a boundary as a
# leveling defect when they are heading into the same agreement.
COMBINED_SUBCONTRACTS = {
    "RFP-060": {
        "lead": "RFP-060",
        "members": ["RFP-060", "ITB-044", "ITB-062", "ITB-077"],
        "ruling_date": "2026-08-06",
        "ruling": "RFP-060 will include ITB-044 Insulation, ITB-062 Acoustical Ceiling "
                  "Treatments and ITB-077 Lockers. Each scope is written independently -- "
                  "one Attachment A per package, all attached to the one subcontract.",
        "drafting": "Draft this package's exhibit on its own scope only. Do not absorb the "
                    "other members' scope into it and do not exclude their scope from it; "
                    "they are separate exhibits under the same agreement.",
    },
}
COMBINED_LOOKUP = {m: g for g in COMBINED_SUBCONTRACTS.values() for m in g["members"]}

DIVISION_PDF = {
    "02": "div-02-existing-conditions", "03": "div-03-concrete", "04": "div-04-masonry",
    "05": "div-05-metals", "06": "div-06-wood-plastics-composites",
    "07": "div-07-thermal-moisture", "08": "div-08-openings", "09": "div-09-finishes",
    "10": "div-10-specialties", "11": "div-11-equipment", "12": "div-12-furnishings",
    "13": "div-13-special-construction", "22": "div-22-plumbing", "23": "div-23-hvac",
    "26": "div-26-electrical", "27": "div-27-communications", "31": "div-31-earthwork",
    "32": "div-32-exterior-improvements", "33": "div-33-utilities",
}

AUTHORITY = [
    "1. Addenda & Clarifications supersede everything they touch. Addendum #1 (05.06.26) "
    "reissued G0-00, LS1-10, A1-20, A2-10, A10-30, C1 and GD. Exhibit B Basis of GMP "
    "(07.01.26) is a contract document treated as an addendum (PM ruling 08.04.26).",
    "2. The Scope of Work narrative decides WHICH PACKAGE carries an item. It is the "
    "trade-boundary authority.",
    "3. Specifications decide HOW the work is executed.",
    "4. Drawings show extent and location. Weakest authority for assignment.",
    "Subcontractor proposals are NOT in this hierarchy. They surface the assumptions a "
    "bidder made and expose gaps. Where a proposal contradicts a contract document, FLAG "
    "it -- never silently adopt the proposal's position or narrow the subcontract to match "
    "it. Ignore general/boilerplate exclusions.",
]


def load(name):
    p = INDEX / name
    return json.loads(p.read_text()) if p.exists() else {}


def main():
    spec = load("spec-section-catalog.json")
    cites = load("package-spec-citations.json").get("packages", {})
    sheets = load("sheet-package-assignments.json")
    props = load("proposal-content.json")
    awarded = load("awarded-sub-mapping.json")
    gmp = load("gmp-basis-exhibit-b.json")
    openitems = load("pm-open-items.json")
    corpus = {s["sheet"]: s for s in load("sheet-corpus.json").get("sheets", [])}

    sec_by_num = {s["section"]: s for s in spec["sections"]}
    sec_owner = defaultdict(list)
    sec_added = defaultdict(list)
    flow_down = defaultdict(list)
    for s in spec["sections"]:
        p = s.get("primary_package")
        if p and p != "ALL PACKAGES":
            sec_owner[p].append(s)
        for extra in s.get("also_assigned_by_pm_ruling", []):
            sec_added[extra].append(s)
        if s.get("flow_down"):
            for p2 in s.get("flows_down_to", []):
                flow_down[p2].append(s)

    docs_by_file = {d["file"]: d for d in props.get("documents", [])}
    items_by_pkg = defaultdict(list)
    for it in openitems.get("items", []):
        for p in it["packages"]:
            items_by_pkg[p].append(
                {"n": it["n"], "id": it["id"], "severity": it["severity"],
                 "title": it["title"], "detail": it["detail"]})

    def spec_entry(s):
        d = DIVISION_PDF.get(s["division"])
        return {
            "section": s["section"], "title": s["title"],
            "basis": s["basis"], "rationale": s["rationale"],
            "manual_pages": f"{s['page_start']}-{s['page_end']}",
            "division_pdf": f"{SPLIT_DIR}/{d}.pdf" if d else None,
            "conflict": s.get("conflict", False),
            "also_cited_by": [p for p in s.get("cited_explicitly_by", [])
                              if p != s.get("primary_package")],
        }

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.json"):
        old.unlink()

    manifest = {}
    for pkg, scope_file in sorted(SCOPE_DOC.items()):
        pk_sheets = sheets.get("sheets_by_package", {}).get(pkg, {})
        aw = awarded.get("packages", {}).get(pkg)
        pc = props.get("packages", {}).get(pkg, {})

        # Every bidder on this package, current document first per firm.
        bidders = []
        for key, chain in sorted(pc.get("current_per_firm", {}).items()):
            cur = docs_by_file.get(chain.get("current_document") or "")
            hist = [docs_by_file.get(f) for f in chain.get("superseded", [])]
            rec = {
                "firm": chain.get("firm"),
                "current_document": chain.get("current_document"),
                "current_date": chain.get("current_date"),
                "superseded_documents": chain.get("superseded", []),
                "undated_not_sequenced": chain.get("undated_not_sequenced", []),
            }
            if cur:
                rec.update({
                    "kind": cur["kind"], "price": cur["price"],
                    "inclusions": cur["inclusions"],
                    "exclusions_scope_specific": cur["exclusions_scope_specific"],
                    "clarifications": cur["clarifications"],
                    "priced_line_items": cur["priced_line_items"],
                    "priced_scope_groups": cur.get("priced_scope_groups", []),
                })
            # A superseded document can still hold scope language the current one
            # dropped; keep what it said rather than only that it existed.
            extra = []
            for h in hist:
                if h and (h["inclusions"] or h["exclusions_scope_specific"]
                          or h["priced_line_items"]):
                    extra.append({"file": h["file"], "date": h["date"],
                                  "inclusions": h["inclusions"][:20],
                                  "exclusions_scope_specific": h["exclusions_scope_specific"][:20],
                                  "priced_line_items": h["priced_line_items"]})
            if extra:
                rec["superseded_content"] = extra
            bidders.append(rec)

        gmp_assume = gmp.get("scope_specific_assumptions", {}).get(pkg)
        num = pkg.split("-")[1]
        gmp_excl = [x for x in gmp.get("exclusions", [])
                    if re.search(rf"\b{num}\b", x) or
                    (gmp_assume and any(w.lower() in x.lower()
                                        for w in gmp_assume["title"].split() if len(w) > 5))]

        rec = {
            "_package_id": pkg,
            "_title": TITLES[pkg],
            "_title_variants_in_source": sorted(
                {t for t in [(gmp_assume or {}).get("title"), (aw or {}).get("title")]
                 if t and t != TITLES[pkg]}) or None,
            "_list": "1% (RFP — NRS 338.16995)" if pkg.startswith("RFP") else "Non-1% (ITB)",
            "_generated": "2026-08-06",
            "_how_to_use": (
                "Pointers plus bidder scope language. OPEN the scope narrative, the spec "
                "sections and the sheets -- do not draft from this record's titles alone. "
                "Do NOT enumerate drawings in the exhibit; the sheet lists here tell you "
                "what to read, not what to write."),
            "document_authority_hierarchy": AUTHORITY,

            "scope_narrative": ({
                "file": f"{SCOPE_DOC_DIR}/{scope_file}",
                "note": "PRIMARY trade-boundary authority. Read this first and in full.",
            } if scope_file else {
                "file": None,
                "note": "NO Scope of Work narrative was issued for this package. Draft from the "
                        "bidders' proposals and the documents on hand, per PM ruling.",
            }),
            "removed_by_owner": REMOVED_BY_OWNER.get(pkg),
            "combined_subcontract": COMBINED_LOOKUP.get(pkg),
            "spec_sections": {
                "primary": [spec_entry(s) for s in sorted(sec_owner.get(pkg, []),
                                                          key=lambda x: x["section"])],
                "added_by_pm_ruling": [spec_entry(s) for s in sec_added.get(pkg, [])],
                "flow_down_from_other_packages": [
                    {"section": s["section"], "title": s["title"],
                     "primary_package": s["primary_package"], "note": s["flow_down"]}
                    for s in flow_down.get(pkg, [])],
                "cited_by_this_scope_doc_but_absent_from_manual": {
                    k: {"title_per_scope_doc": v.get("title_per_scope_doc"),
                        "status": v["status"], "note": v["note"],
                        "carried_by": v.get("carried_by"),
                        "ownership_ruling": v.get("ownership_ruling"),
                        # The drafter needs the instruction, not just the flag.
                        "how_to_write_it": v.get("how_to_write_it"),
                        "candidates": v.get("candidate_sections_in_manual")}
                    for k, v in spec.get("cited_but_absent_from_manual", {}).items()
                    if pkg in v.get("cited_by", [])},
                "division_00_01": "Bind every subcontract; not listed per package.",
            },
            "drawings": {
                "_warning": "RETRIEVAL ONLY. Never reproduce a sheet list in the exhibit.",
                "draft_from": [
                    {"sheet": sh, "title": corpus[sh]["title"],
                     "revision": corpus[sh]["revision"],
                     "file": corpus[sh]["file"]}
                    for sh in pk_sheets.get("draft_from", []) if sh in corpus],
                "leads_to_verify": pk_sheets.get("leads_to_verify", []),
            },
            "awarded_sub": aw or {"status": "not-yet-awarded"},
            "bidders": bidders,
            "bidder_note": (
                "Read EVERY bidder, not only the awarded sub. A losing bidder's "
                "clarification is often the clearest signal of what the documents left "
                "ambiguous, and is a primary source of Attachment A inclusions."),
            "gmp_basis_exhibit_b": {
                "_authority": "Contract document, treated as an addendum (PM ruling 08.04.26).",
                "scope_assumptions": (gmp_assume or {}).get("items", []),
                "possibly_relevant_exclusions": gmp_excl,
                "prevailing_wage": gmp.get("_commercial_terms", {}).get("prevailing_wage"),
                "sales_tax": gmp.get("_commercial_terms", {}).get("sales_tax"),
            },
            "open_pm_items": items_by_pkg.get(pkg, []),
        }
        (OUT / f"{pkg}.json").write_text(json.dumps(rec, indent=2) + "\n")
        manifest[pkg] = {
            "title": rec["_title"], "list": rec["_list"],
            "file": f"01-index/packages/{pkg}.json",
            "awarded_sub": (aw or {}).get("awarded_sub"),
            "status": (aw or {}).get("status", "not-yet-awarded"),
            "spec_sections": len(rec["spec_sections"]["primary"])
                             + len(rec["spec_sections"]["added_by_pm_ruling"]),
            "sheets_draft_from": len(rec["drawings"]["draft_from"]),
            "bidders": len(bidders),
            "open_pm_items": len(rec["open_pm_items"]),
            "combined_with": (COMBINED_LOOKUP[pkg]["members"] if pkg in COMBINED_LOOKUP else None),
        }

    # Preserve the rejected first index rather than overwriting it -- the PM review
    # that rejected it cites it by name.
    old = INDEX / "package-index.json"
    keep = INDEX / "package-index.REJECTED-2026-07-31.json"
    if old.exists() and not keep.exists():
        shutil.move(str(old), str(keep))

    old.write_text(json.dumps({
        "_generated": "2026-08-06",
        "_supersedes": ("package-index.json rejected by PM 07.31.26, preserved as "
                        "package-index.REJECTED-2026-07-31.json. Also supersedes "
                        "package-index-v2.json, which predates all extraction work."),
        "_structure": ("MANIFEST ONLY. Each package's drafting record is a separate file "
                       "under 01-index/packages/. A drafter reads its own package's file "
                       "and no other -- cross-contamination between packages is how scope "
                       "migrates from one subcontract into another."),
        "_totals": {
            "packages": len(manifest),
            "spec_sections_assigned": sum(m["spec_sections"] for m in manifest.values()),
            "sheets_draft_from": sum(m["sheets_draft_from"] for m in manifest.values()),
            "bidders": sum(m["bidders"] for m in manifest.values()),
            "packages_awarded": sum(1 for m in manifest.values() if m["status"] == "awarded"),
            "open_pm_items_attached": sum(m["open_pm_items"] for m in manifest.values()),
        },
        "packages": manifest,
    }, indent=2) + "\n")

    print(f"{len(manifest)} package records written to 01-index/packages/")
    for p, m in manifest.items():
        print(f"  {p:8} specs={m['spec_sections']:>2} sheets={m['sheets_draft_from']:>2} "
              f"bidders={m['bidders']:>2} items={m['open_pm_items']:>2}  {m['title'][:40]}")


if __name__ == "__main__":
    main()
