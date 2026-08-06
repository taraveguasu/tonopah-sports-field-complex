#!/usr/bin/env python3
"""
Build the authoritative spec-section catalog and resolve every package's spec
citations against it.

Three problems this solves, all raised at PM review:

1. Some scope docs cite a whole DIVISION ("Division 26 - Electrical") rather than
   sections. A subcontract that cites a division binds the sub to nothing specific.
   Each division-level citation is expanded to the sections that actually exist in
   that division of this manual.

2. Some scope docs cite section numbers that are NOT in this manual. Those are real
   spec gaps, not indexing misses, and must be reported as gaps rather than quietly
   dropped or fuzzy-matched onto a neighbouring section.

3. Some sections in the manual are claimed by NO package. Section 08 31 00 Access
   Doors and Panels is the known case. An unclaimed section is work that is
   specified, priced into the GMP, and assigned to nobody -- exactly the risk the PM
   asked to be closed. Each is assigned by trade judgment and flagged as judgment,
   never presented as a citation.

Section list comes from the manual's own bookmark outline -- 137 entries, each with
its page -- not from parsing body text, so section numbering is the publisher's.

Usage:  python3 scripts/index_spec_sections.py
Writes: 01-index/spec-section-catalog.json
        01-index/package-spec-citations.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs"
INDEX = ROOT / "01-index"
MANUAL = SRC / "04-specs-reports" / "04.01 - Bid Specification Manual 042026.pdf"
SCOPES = SRC / "02-trade-scopes-bidform" / "_extracted"
SPLIT = SRC / "04-specs-reports" / "spec-manual-split"

# Scope-doc filename number -> package_id. The filenames drift from the package
# numbers (ITB-008 filed as 007, RFP-060 as 061, RFP-100 as 099); reconciled by
# title, per CLAUDE.md.
SCOPE_FILE_TO_PACKAGE = {
    "002": "RFP-002", "007": "ITB-008", "008": "RFP-008", "016": "RFP-016",
    "018": "ITB-018", "019": "ITB-019", "021": "RFP-021", "022": "RFP-022",
    "023": "RFP-023", "030": "RFP-030", "031": "RFP-031", "033": "RFP-033",
    "040": "ITB-040", "044": "ITB-044", "045": "RFP-045", "054": "ITB-054",
    "056": "ITB-056", "060": "RFP-060", "062": "ITB-062", "066": "ITB-066",
    "067": "ITB-067", "071": "ITB-071", "072": "ITB-072", "074": "ITB-074",
    "077": "ITB-077", "078": "ITB-078", "085": "ITB-085", "089": "ITB-089",
    "094": "RFP-094", "098": "RFP-098", "099": "RFP-100", "103": "RFP-103",
    "109": "RFP-109",
}

# A bookmark title is "<number> - <title>", with the number written inconsistently
# (00 43 36A, 000101, 03 1000, 016116.01). Normalise to "NN NN NN" plus any suffix.
BOOKMARK = re.compile(r"^\s*(\d[\d\s]{3,10}(?:\.\d+)?[A-Z]?)\s*[-–—]\s*(.+?)\s*$")

# Citations inside a scope narrative.
SECTION_CITE = re.compile(r"\b(\d{2})\s?(\d{2})\s?(\d{2})(?:\.(\d{2}))?\b")
DIVISION_CITE = re.compile(r"\bDivision\s+(\d{1,2})\b", re.I)


def norm_number(raw):
    """'03 1000' -> '03 10 00'; '016116.01' -> '01 61 16.01'; keeps a trailing letter."""
    suffix = ""
    m = re.match(r"^(.*?)([A-Z])$", raw.strip())
    if m:
        raw, suffix = m.group(1), m.group(2)
    dot = ""
    if "." in raw:
        raw, dot = raw.split(".", 1)
        dot = "." + dot.strip()
    digits = re.sub(r"\D", "", raw)
    if len(digits) < 6:
        return None
    parts = [digits[0:2], digits[2:4], digits[4:6]]
    if len(digits) > 6:
        parts.append(digits[6:])
    return " ".join(parts) + dot + suffix


def catalog():
    """Every section in the manual, from its own bookmark outline."""
    doc = fitz.open(MANUAL)
    total = doc.page_count
    entries = []
    toc = doc.get_toc()
    for i, (_, title, page) in enumerate(toc):
        m = BOOKMARK.match(title)
        if not m:
            continue
        num = norm_number(m.group(1))
        if not num:
            continue
        end = total
        for _, _, p2 in toc[i + 1:]:
            if p2 > page:
                end = p2 - 1
                break
        entries.append({
            "section": num,
            "title": m.group(2).strip(),
            "division": num[:2],
            "page_start": page,
            "page_end": end,
            "pages": end - page + 1,
            "bookmark_raw": title,
        })
    doc.close()
    return entries


def divisions_present(entries):
    out = defaultdict(list)
    for e in entries:
        out[e["division"]].append(e["section"])
    return out


DIVISION_NAMES = {
    "00": "Procurement & Contracting", "01": "General Requirements",
    "02": "Existing Conditions", "03": "Concrete", "04": "Masonry", "05": "Metals",
    "06": "Wood, Plastics & Composites", "07": "Thermal & Moisture Protection",
    "08": "Openings", "09": "Finishes", "10": "Specialties", "11": "Equipment",
    "12": "Furnishings", "13": "Special Construction", "22": "Plumbing",
    "23": "HVAC", "26": "Electrical", "27": "Communications", "31": "Earthwork",
    "32": "Exterior Improvements", "33": "Utilities",
}


def scope_citations(entries):
    """What each package's own Scope of Work narrative cites."""
    known = {e["section"] for e in entries}
    by_div = divisions_present(entries)
    out = {}
    for f in sorted(SCOPES.glob("Scope of Work - *.txt")):
        m = re.match(r"Scope of Work - (\d{3})", f.name)
        if not m or m.group(1) not in SCOPE_FILE_TO_PACKAGE:
            continue
        pkg = SCOPE_FILE_TO_PACKAGE[m.group(1)]
        text = f.read_text(errors="ignore")

        cited, missing = set(), {}
        for mm in SECTION_CITE.finditer(text):
            num = " ".join(mm.group(1, 2, 3)) + (f".{mm.group(4)}" if mm.group(4) else "")
            # A bare number in prose is not a citation. Require it to resolve to a
            # real section, or to look like one that simply is not in this manual.
            if num in known:
                cited.add(num)
            elif num[:2] in DIVISION_NAMES:
                # Keep the title the scope doc gives it. Knowing that RFP-103 means
                # "07 84 00 - Firestopping" is what tells the PM whether a spec is
                # genuinely missing or the number is simply written wrong.
                tail = text[mm.end():mm.end() + 70]
                t = re.match(r"\s*[-\u2013\u2014:]?\s*([A-Z][^\n|]{2,60})", tail)
                missing[num] = t.group(1).strip().rstrip(".,;") if t else None

        # Division-level citations expand to that division's actual sections. A
        # subcontract that says "Division 26" binds the sub to nothing specific.
        expanded = {}
        for mm in DIVISION_CITE.finditer(text):
            d = mm.group(1).zfill(2)
            if d in by_div:
                expanded[d] = sorted(set(by_div[d]) - cited)

        out[pkg] = {
            "scope_file": str(f.relative_to(SRC)),
            "cited_sections": sorted(cited),
            "cited_but_not_in_manual": dict(sorted(missing.items())),
            "division_level_citations": {
                d: {"division_name": DIVISION_NAMES.get(d, "?"),
                    "sections_in_manual": s,
                    "note": "Scope doc cites the division, not sections. These are the "
                            "sections that exist in this manual for it; cite them "
                            "explicitly in Attachment A."}
                for d, s in sorted(expanded.items())
            },
        }
    return out


# ---------------------------------------------------------------------------
# Primary responsibility for every technical section in this manual.
#
# Citation counting cannot decide ownership, and the raw counts show why: eleven
# packages cite 03 30 00 and thirteen cite 07 92 00, because a scope narrative
# cross-references the section it must build to, not only the one it carries.
# Meanwhile a scope doc that cites "Division 26" claims twenty-one sections at
# once, and ITB-085's kitchen narrative mentions Divisions 22, 23 and 26 for its
# connections without carrying any of them.
#
# So each section is assigned one PRIMARY package -- who executes and warrants it
# -- with every other claimant recorded as REFERENCING. Basis is always stated:
#
#   scope_doc      one package's Scope of Work narrative cites it, and only one
#   pm_ruling      a logged PM ruling decides it, and it is quoted
#   trade_judgment my assignment as PM. NOT a citation. Reviewable, and flagged
#                  as judgment wherever it appears downstream.
#
# Where a ruling contradicts a scope doc, or two packages have equal claim, the
# conflict is recorded rather than resolved silently.
# ---------------------------------------------------------------------------
# section: (primary_package, basis, rationale)
PRIMARY = {
    # Division 02 -- Existing Conditions
    "02 41 00": ("RFP-008", "pm_ruling",
                 "PM ruling 08.06.26 (A4): the section goes in BOTH subcontracts, split by what "
                 "each demolishes. RFP-008 carries the full building demolition and the site "
                 "demolition; RFP-002 is abatement, which has demolition inside it. This "
                 "refines the 07.31.26 ruling -- 'the entire demolition scope is RFP-008' was "
                 "about the site and building work, not about abatement's own demolition."),

    # Division 03 -- Concrete
    "03 10 00": ("RFP-030", "trade_judgment", "Formwork is the concrete package's means and methods."),
    "03 20 00": ("RFP-030", "trade_judgment", "Reinforcement is placed by the concrete package."),
    "03 30 00": ("RFP-030", "trade_judgment",
                 "Cast-in-place concrete is RFP-030. Eleven packages cite this section because "
                 "each has equipment set on a concrete footing; those are cross-references to "
                 "RFP-030's work, not claims on it. PM rulings 07.31.26 confirm the direction: "
                 "athletic equipment and goal post footings, and concrete curb and slot/trench "
                 "drains at the track perimeter, are all RFP-030."),

    # Division 04 -- Masonry
    "04 05 03": ("RFP-031", "trade_judgment",
                 "Mortar and grout are the mason's. RFP-031's scope doc cites no section at all "
                 "and reaches Division 04 only at division level -- this is exactly the gap the "
                 "PM flagged: the mason must have the masonry specification in his subcontract."),
    "04 20 16": ("RFP-031", "trade_judgment",
                 "Reinforced unit masonry is the mason's primary section. Same gap as 04 05 03. "
                 "Note this section cross-references 07 19 00 Water Repellents twice; 07 19 00 "
                 "does not exist in this manual, while 09 96 50 requires a water repellent as a "
                 "precondition -- open item, see the CMU water-repellent finding."),

    # Division 05 -- Metals
    "05 12 23": ("RFP-033", "scope_doc", "Cited solely by RFP-033."),
    "05 21 00": ("RFP-033", "trade_judgment", "Steel joists are erected by the structural steel package."),
    "05 31 00": ("RFP-033", "trade_judgment", "Steel deck follows the joists, same erector."),
    "05 40 00": ("RFP-060", "scope_doc", "Cited solely by RFP-060 -- cold-formed framing is the framer's."),
    "05 50 00": ("RFP-033", "scope_doc", "Cited solely by RFP-033; ornamental metals are in its title."),

    # Division 06
    "06 83 16": ("RFP-060", "scope_doc", "Cited solely by RFP-060, whose title carries FRP."),

    # Division 07 -- Thermal & Moisture
    "07 21 00": ("ITB-044", "scope_doc", "Cited solely by ITB-044."),
    "07 25 00": ("RFP-045", "scope_doc",
                 "Cited solely by RFP-045. Consistent with PM ruling 07.31.26: the self-adhered "
                 "membrane under the metal roof is RFP-045, and ITB-040 is below-grade only."),
    "07 26 00": ("RFP-030", "scope_doc",
                 "Cited solely by RFP-030 -- the under-slab vapour retarder is placed with the slab."),
    "07 61 00": ("RFP-045", "trade_judgment", "Sheet metal roofing is the metal roofing package."),
    "07 62 00": ("RFP-045", "scope_doc",
                 "Cited solely by RFP-045. PM ruling 08.06.26 (D): RFP-045 owns the gutters and "
                 "downspouts -- the cited 07 71 23 is absent from the manual, so the obligation "
                 "is written into the scope by title, not by section number."),
    "07 92 00": ("ITB-040", "scope_doc",
                 "ITB-040 is the sealants package by title. Thirteen packages cite this section "
                 "because each seals its own penetrations and joints; those are compliance "
                 "references, not claims. Flow the section down to all of them, but ITB-040 "
                 "carries the building's joint sealants."),

    # Division 08 -- Openings
    "08 11 13": ("ITB-056", "scope_doc", "Cited solely by ITB-056."),
    "08 31 00": ("RFP-060", "pm_ruling",
                 "PM ruling 07.31.26: access doors and panels are supplied by the MEP trades and "
                 "installed by the RFP-060 framer. RFP-098, RFP-100 and RFP-103 each cite this "
                 "section -- that is the supply obligation, and each of their subcontracts must "
                 "carry it. Installation sits with RFP-060, whose scope doc cites the same work "
                 "as '08 31 13 - Access Doors and Panels'; the manual publishes it as 08 31 00."),
    "08 33 13": ("ITB-054", "scope_doc", "Cited solely by ITB-054."),
    "08 33 23": ("ITB-054", "scope_doc", "Cited solely by ITB-054."),

    # Division 09 -- Finishes
    "09 21 16": ("RFP-060", "trade_judgment",
                 "Gypsum board assemblies are the drywall package. ITB-077 also cites it, but "
                 "for the locker backing it must build to, not to carry the assembly."),
    "09 51 00": ("ITB-062", "scope_doc", "Cited solely by ITB-062."),
    "09 65 13": ("ITB-067", "trade_judgment",
                 "Resilient base has no explicit claimant. ITB-066 would be the natural home, but "
                 "PM ruling 08.04.26 leaves ITB-066 with no remaining scope, and SI Legacy priced "
                 "'Furnish & Install 4\" Rubber Wall Base At RB-1 Areas' inside their 066/067 "
                 "bundle. Assigned to ITB-067 -- CONFIRM, since ITB-067 is a concrete-finishing "
                 "package and rubber base is not concrete work."),
    "09 91 13": ("RFP-060", "scope_doc", "Cited solely by RFP-060."),
    "09 91 23": ("RFP-060", "scope_doc", "Cited solely by RFP-060."),
    "09 96 50": ("RFP-060", "scope_doc",
                 "Cited solely by RFP-060. Its Part 3 requires a water repellent to be applied "
                 "first; the referenced 07 19 00 is absent from this manual -- open item."),
    "09 97 23": ("RFP-060", "trade_judgment",
                 "Concrete and masonry coatings are applied by the painter."),

    # Division 10 -- Specialties
    "10 11 00": ("ITB-071", "scope_doc", "Cited solely by ITB-071."),
    "10 14 23": ("ITB-072", "scope_doc", "Cited solely by ITB-072."),
    "10 21 13.13": ("ITB-074", "scope_doc",
                    "ITB-074's scope doc cites '10 21 00 - Toilet Compartments', the parent "
                    "number of this section; the manual publishes it as 10 21 13.13 Metal Toilet "
                    "Compartments. Cite the published number in Attachment A. Henri's quote "
                    "prices 'TOILET PARTITIONS -- Scranton Products, 9 stalls, 2 screens -- "
                    "furnished and installed -- $28,982'."),
    "10 26 00": ("ITB-074", "trade_judgment",
                 "Both ITB-074 and RFP-060 cite it. ITB-074's title carries corner guards and "
                 "Henri's quote prices them at $2,422; RFP-060's citation is the wall it mounts "
                 "to. CONFIRMED by PM 08.06.26 (A3): included in ITB-074."),
    "10 28 00": ("ITB-074", "scope_doc",
                 "Cited by ITB-074; Henri prices toilet accessories at $12,021, some OFCI."),
    "10 75 00": ("ITB-078", "scope_doc", "Cited solely by ITB-078."),

    # Division 11 -- Equipment
    "11 30 13": ("ITB-085", "trade_judgment",
                 "ORPHAN -- no scope doc cites it. Residential appliances belong to the warming "
                 "kitchen package, which is the only package with kitchen equipment scope."),
    "11 40 00": ("ITB-085", "scope_doc", "Cited solely by ITB-085."),
    "11 68 43": ("ITB-089", "scope_doc",
                 "Cited solely by ITB-089. Note ITB-019's scope doc cites 11 68 33, which does "
                 "not exist in this manual -- likely a typo for this section, but not assumed."),

    # Division 12 -- Furnishings
    "12 93 00": ("ITB-018", "pm_ruling",
                 "PM ruling 08.06.26 (A2/C1): ITB-018 SUPPLIES, ITB-019 INSTALLS. The section "
                 "goes in both subcontracts -- not split by paragraph. ITB-019's obligation is "
                 "installation only, so its Attachment A must say so explicitly or it reads as "
                 "carrying supply too."),

    # Division 13 -- Special Construction
    "13 34 23": ("RFP-094", "scope_doc",
                 "Cited solely by RFP-094. This is a generic fabricated-structures section "
                 "standing in for the bleacher-specific section the scope doc cites (13 12 50), "
                 "which does not exist in this manual. Applies to the press box; the bleachers "
                 "themselves rely on the written spec block on sheet A1-40."),

    # Division 22 -- Plumbing -> RFP-098
    **{s: ("RFP-098", "trade_judgment",
           "RFP-098's scope doc cites Division 22 at division level, which binds the sub to "
           "nothing specific. Cite this section explicitly in Attachment A. ITB-085 and RFP-103 "
           "also mention Division 22 -- for the kitchen connections and the equipment they serve, "
           "not to carry the plumbing.")
       for s in ["22 01 00", "22 05 00", "22 05 19", "22 05 23", "22 05 29", "22 05 53",
                 "22 07 19", "22 10 05", "22 10 06", "22 30 00", "22 40 00"]},

    # Division 23 -- HVAC -> RFP-100
    **{s: ("RFP-100", "trade_judgment",
           "RFP-100's scope doc cites Division 23 at division level. Cite this section explicitly "
           "in Attachment A.")
       for s in ["23 01 00", "23 05 00", "23 05 13", "23 05 29", "23 05 53", "23 07 13",
                 "23 07 19", "23 23 00", "23 31 00", "23 33 00", "23 34 16", "23 36 00",
                 "23 40 00", "23 81 26.13", "23 81 29"]},
    "23 05 93": ("RFP-100", "trade_judgment",
                 "Testing, adjusting and balancing. RFP-100's own title carries Test & Balance, "
                 "so it stays in this subcontract rather than going to a separate TAB agency -- "
                 "CONFIRMED by PM 08.06.26 (A7): TAB is included in RFP-100, not subcontracted "
                 "directly. Four TAB proposals were solicited under trade 102 and tabulated "
                 "into RFP-100."),

    # Division 26 -- Electrical -> RFP-103
    **{s: ("RFP-103", "trade_judgment",
           "RFP-103's scope doc cites Division 26 at division level. Cite this section explicitly "
           "in Attachment A.")
       for s in ["26 00 10", "26 05 00", "26 05 05", "26 05 19", "26 05 26", "26 05 29",
                 "26 05 33.13", "26 05 33.16", "26 05 53", "26 05 83", "26 08 00", "26 09 23",
                 "26 22 00", "26 24 16", "26 27 26", "26 28 13", "26 28 16.16", "26 29 13",
                 "26 43 00", "26 51 00"]},
    "26 56 00": ("RFP-103", "trade_judgment",
                 "Exterior lighting, which on this project includes the Musco sports field "
                 "lighting named in RFP-103's title. Musco's footing information is filed with "
                 "the proposals; the footings themselves are RFP-030 per the 07.31.26 ruling."),

    # Division 27 -- Communications -> RFP-103
    "27 00 00": ("RFP-103", "trade_judgment",
                 "Low voltage is in RFP-103's title. RFP-100 also mentions Division 27, for its "
                 "control wiring. NOTE: fire alarm is an express GMP Exclusion per Exhibit B "
                 "(08.04.26) -- no fire alarm scope flows down with this section."),

    # Division 31 -- Earthwork -> RFP-008
    **{s: ("RFP-008", "trade_judgment",
           "Thirteen scope docs mention Division 31, because each has to trench, backfill or "
           "compact for its own work. RFP-008 is the mass-earthwork package and carries the "
           "section; the others comply with it inside their own excavations.")
       for s in ["31 10 00", "31 20 00", "31 50 00"]},

    # Division 32 -- Exterior Improvements
    "32 12 16": ("RFP-008", "scope_doc", "Cited solely by RFP-008."),
    "32 13 13": ("RFP-030", "scope_doc",
                 "Cited solely by RFP-030. TAB's homework response deducts Type II from the "
                 "concrete paving, confirming RFP-008 carries the subgrade and RFP-030 the slab."),
    "32 13 73": ("RFP-030", "scope_doc", "Cited solely by RFP-030."),
    "32 16 23": ("RFP-030", "trade_judgment",
                 "Sidewalks are flatwork. CONFIRMED by PM 08.06.26 (A6): RFP-030."),
    "32 18 13": ("RFP-022", "scope_doc", "Cited solely by RFP-022."),
    "32 18 23.33": ("RFP-021", "scope_doc", "Cited solely by RFP-021."),
    "32 31 13": ("RFP-023", "scope_doc", "Cited solely by RFP-023."),
    "32 84 00": ("RFP-016", "pm_ruling", "PM ruling 07.31.26: RFP-016's primary specs are 32 84 00, 32 91 13, 32 96 50."),
    "32 91 13": ("RFP-016", "pm_ruling",
                 "PM ruling 07.31.26, refined 08.06.26 (A5): RFP-016 carries it. Do NOT write "
                 "exclusions into ITB-019 or RFP-030 -- both must coordinate with this scope, "
                 "and an exclusion would read as no obligation to coordinate. Treat as "
                 "flow-down: RFP-016 executes, the others coordinate."),
    "32 96 50": ("RFP-016", "pm_ruling", "PM ruling 07.31.26."),

    # Division 33 -- Utilities -> RFP-008
    **{s: ("RFP-008", "trade_judgment",
           "Wet utilities are named in RFP-008's title; its scope doc reaches Division 33 only at "
           "division level. Cite this section explicitly in Attachment A.")
       for s in ["33 05 00", "33 10 00", "33 12 00", "33 30 00"]},
}

# Bookmark numbers the manual itself contradicts. Page 15 is headed "04 43 36C"
# but the section heading on that same page reads "SECTION 00 4336C", and it sits
# between 00 43 36B and 00 45 21. It is a Division 00 procurement form, not a
# masonry section.
NUMBER_CORRECTIONS = {
    "04 43 36C": {
        "corrected_to": "00 43 36C",
        "evidence": "Page 15 header reads '04 43 36C'; the section heading on the same page "
                    "reads 'SECTION 00 4336C'. Filed between 00 43 36B (p14) and 00 45 21 (p24).",
        "effect": "Procurement form, not a technical section. Excluded from trade assignment.",
    },
}

# Sections many packages cite because each must comply with them inside its own
# work, not because ownership is disputed. Recording these as conflicts would bury
# the five real ones under sixteen false positives.
FLOW_DOWN = {
    "03 30 00": "Every package with equipment on a footing cites it; RFP-030 builds them all.",
    "07 92 00": "Every package seals its own joints and penetrations to this section.",
    "08 31 00": "A designed supply/install split, not a dispute -- MEP supply, RFP-060 installs. "
                "The section must appear in all four subcontracts with the split stated.",
}

# Why a package ends up with no section of its own. Never left blank -- a package
# with zero specs is a subcontract with no technical requirements attached.
NO_SECTION_REASON = {
    "ITB-008": "Surveying, Layout & Staking. No CSI section for surveying exists in this manual "
               "and the scope doc cites none. Requirements come from the scope narrative and "
               "Division 01 alone -- confirm that is acceptable before issuing.",
    "ITB-019": "Track & Field Athletic Equipment. Its work lives inside 12 93 00 Site "
               "Furnishings, whose own Section Includes spans both this package and ITB-018; "
               "primary is shown as ITB-018 pending a PM ruling on the split. Its cited "
               "11 68 33 Athletic Field Equipment is absent (see candidates).",
    "ITB-066": "Fluid-Applied Flooring. Correct to hold none -- PM ruling 08.04.26 excluded "
               "resinous/epoxy flooring and moved those locations to Sealed Concrete under "
               "ITB-067, leaving ITB-066 with no remaining scope.",
    "ITB-077": "Lockers. Cited 10 51 13 Metal Lockers is absent from the manual. Basis of design "
               "is Clarification No.1 RFI #3 (ASI Pro Collection, 24\"W x 18\"D x 72\"H) per PM "
               "ruling 07.31.26, reinforced by the keynote on sheet A10-30.",
    "RFP-002": "Abatement & Building Wrecking. 02 41 00 Demolition went to RFP-008 by PM ruling "
               "07.31.26, and the cited 02 81 00 Transportation and Disposal of Misc. Hazardous "
               "Materials is absent. Abatement requirements come from the Asbestos Survey and "
               "Asbestos Management Plan, which are not part of the spec manual.",
    "RFP-109": "Prefabricated Ticket Booth. No section exists; sheet A1-40 carries a written "
               "'PRE-MANUFACTURED TICKET BOOTH SPECS' block, and PM ruling 08.04.26 sets the "
               "basis of design as Porta-King DURASTEEL PC Building Model PC64 (6'x4').",
}

# Sections a scope doc cites that are absent from this manual. Reported as gaps,
# never fuzzy-matched onto a neighbouring section.
GAP_NOTES = {
    "08 71 00": "Door Hardware. Added by Addendum #1 (05.06.26) and therefore a contract "
                "document, but not in the base manual -- read it from the addendum, not here. "
                "Cited by both ITB-056 and RFP-103 (the latter for electrified hardware).",
    "11 68 33": "Athletic Field Equipment. Numerically near 11 68 43 Football/TrackScoreboard, "
                "but that section is the scoreboard, which is ITB-089's -- the candidate is a "
                "number match, not a scope match. Treat the athletic-equipment spec as MISSING; "
                "ITB-019's requirements rest on 12 93 00 and the drawings.",
    "13 12 50": "Permanent Outdoor Bleacher. No bleacher section exists. Sheet A1-40 carries a "
                "written 'PRE-MANUFACTURED ALUMINUM BLEACHERS SPECS' block that must be quoted "
                "into Attachment A in its place. 13 34 23 Fabricated Shade Structures covers "
                "the press box only.",
    "07 19 00": "Water Repellents. Cross-referenced twice by 04 20 16 and required as a "
                "precondition by 09 96 50 Anti-Graffiti Coatings, but absent from the manual. "
                "Two sections depend on a spec that was never issued -- open item.",
    "07 41 13": "Metal Roof Panels -- RFP-045's own primary section, and it is not in the "
                "manual. 07 61 00 Sheet Metal Roofing is the nearest published substitute and "
                "is assigned to RFP-045, but it is a different section, not a renumbering. "
                "Confirm which governs the panel system before issuing.",
    "07 71 23": "Manufactured Gutters and Downspouts. Absent. 07 62 00 Sheet Metal Flashing and "
                "Trim is assigned to RFP-045 and is the nearest published coverage; confirm it "
                "carries the gutters, or the roof drainage has no specification.",
    "07 84 00": "Firestopping. Absent from the manual, cited by RFP-103. CLOSED BY PM RULING "
                "08.05.26 -- there are no fire-rated assemblies on this project, so IBC 714 "
                "penetration firestopping has nothing to apply to. See pm_resolution for the "
                "four sources checked. Documentation gap, not a construction risk.",
    "09 82 00": "Acoustical Insulation. Absent. The manual publishes only 07 21 00 Thermal "
                "Insulation, which is assigned to ITB-044. Acoustic batt in partitions has no "
                "specification -- confirm whether ITB-044 or RFP-060 carries it.",
    "10 44 13": "Fire Protection Cabinets. Absent, though ITB-074's title carries fire "
                "protection specialties and Henri's quote prices 'FIRE EXTINGUISHERS, WALL "
                "SAFES, KEY CABINET & KNOX BOXES -- furnished and installed -- $6,313'. The "
                "bidders priced work that has no spec section.",
    "10 51 13": "Metal Lockers. Absent. Basis of design is Clarification No.1 RFI #3 (ASI Pro "
                "Collection, 24 in. W x 18 in. D x 72 in. H) per PM ruling 07.31.26, reinforced "
                "by the keynote on revised sheet A10-30. Note Henri also prices metal lockers "
                "inside ITB-074 at $22,519 -- decide which subcontract carries them.",
    "03 35 00": "Concrete Finishing -- ITB-067's own title section, absent from the manual. "
                "CLOSED BY PM RULING 08.05.26: ITB-067 references 03 30 00 Cast-In-Place "
                "Concrete instead, whose Part 3 carries the finishing requirements.",
    "07 13 00": "Sheet Waterproofing -- absent. CLOSED BY PM RULING 08.05.26: ITB-040 uses "
                "07 25 00 Weather Barriers. The package no longer holds only a joint-sealants "
                "section; 07 25 00 is shared with RFP-045 along the 07.31.26 boundary.",
    "32 11 23": "Aggregate Base Courses. Absent. CLOSED BY PM RULING 08.05.26: aggregate base "
                "courses are covered in 31 20 00 Earth Moving, which is RFP-008's section -- "
                "consistent with TAB pricing the Type II deducts under the turf field, building "
                "pad and concrete paving. RFP-030 references it for base under its flatwork.",
    "32 19 19": "Landscape Grading. Absent; cited by both RFP-021 and RFP-022, the two packages "
                "most dependent on finish grade tolerance. Division 31's 31 20 00 Earth Moving "
                "is assigned to RFP-008 and is the nearest coverage.",
    "31 00 00": "Earthwork. A division rollup number rather than a section; Division 31 does "
                "exist in this manual with three sections, all assigned to RFP-008. Not a gap.",
    "02 81 00": "Transportation and Disposal of Misc. Hazardous Materials. Absent from the "
                "manual. Abatement requirements come from the Asbestos Survey and Asbestos "
                "Management Plan, which are staged in 04-specs-reports but are not spec "
                "sections -- cite those documents directly in RFP-002's Attachment A.",
    "02 41 13": "Selective Site Demolition. 02 41 00 Demolition is the published section and is "
                "assigned to RFP-008 by PM ruling; the cited number is almost certainly that "
                "section, but the numbers are not treated as equivalent without confirmation.",
    "05 31 12": "Steel Roof Decking. 05 31 00 Steel Deck is the published section, assigned to "
                "RFP-033. Near-certain renumbering, still confirm.",
    "08 31 13": "Access Doors and Panels. 08 31 00 is the published number for the same title. "
                "Near-certain renumbering.",
    "10 21 00": "Toilet Compartments. The manual publishes 10 21 13.13 Metal Toilet "
                "Compartments, a child of the cited number. Cite the published number.",
}


# ---------------------------------------------------------------------------
# GLOBAL RULE, PM 08.06.26 (D). A specification section cited by an RFP or ITB
# package that is NOT in the Project Manual cannot be cited in Attachment A at
# all. The obligation still exists -- it is written into the scope verbiage by
# TITLE instead. RFP-045's exhibit says "metal roof panels", never "07 41 13".
#
# This closes every remaining absent-section gap as a class rather than one at a
# time, and it changes what a gap means: not work without an owner, but work
# whose obligation is carried by scope language rather than by a citation. The
# exhibit is written from the scope narrative, the drawings and the
# subcontractor's proposal.
GAP_RULE = {
    "ruling_date": "2026-08-06",
    "ruling": "If the specification sections cited in the RFP & ITB packages are not included "
              "in the Project Manual, they cannot be cited in the Attachment A. Make sure the "
              "scope of work includes the TITLE of those specifications.",
    "example": "RFP-045's Attachment A includes metal roof panels in the scope verbiage, not "
               "the section number 07 41 13.",
    "drafting": "Write the exhibit from the scope narrative, the drawings and the "
                "subcontractor's proposal.",
}

# Ownership the PM assigned for absent sections on 08.06.26. The section number is
# still never cited; this records who carries the work.
GAP_OWNERSHIP = {
    "07 71 23": ("RFP-045", "RFP-045 owns the gutters and downspouts."),
    "10 44 13": ("ITB-074", "ITB-074 owns the fire protection cabinets."),
    "10 51 13": ("ITB-077", "Lockers per Clarification No. 1 -- ASI Storage Solutions, Pro "
                            "Collection, Security Box and Foot Locker, 24\" W x 18\" D x 72\" "
                            "enclosed height, black. No spec section was issued."),
    "13 12 50": ("RFP-094", "The only specifications available are the written blocks on sheet "
                            "A1-40 (PRE-MANUFACTURED ALUMINUM BLEACHERS / PRESS BOX SPECS)."),
}

# ---------------------------------------------------------------------------
# PM rulings closing spec gaps (08.05.26). Each names the published section that
# answers an absent citation, so the gap is recorded as CLOSED BY RULING rather
# than silently disappearing from the register.
# ---------------------------------------------------------------------------
GAP_RESOLUTIONS = {
    "03 35 00": {
        "resolved_to": "03 30 00", "packages": ["ITB-067"], "ruling_date": "2026-08-05",
        "ruling": "ITB-067 references 03 30 00 Cast-In-Place Concrete, not 03 35 00.",
        "effect": "ITB-067's concrete-finishing and sealed-concrete work is governed by "
                  "03 30 00, whose Part 3 carries the finishing requirements. RFP-030 remains "
                  "the primary for placing the concrete; ITB-067 finishes and seals it.",
    },
    "07 13 00": {
        "resolved_to": "07 25 00", "packages": ["ITB-040"], "ruling_date": "2026-08-05",
        "ruling": "Use 07 25 00 Weather Barriers for package 040.",
        "effect": "ITB-040 no longer holds only a joint-sealants section. 07 25 00 is shared "
                  "with RFP-045 under the 07.31.26 boundary: RFP-045 carries the self-adhered "
                  "membrane under the metal roof, ITB-040 carries below-grade waterproofing. "
                  "RFP-045 stays primary because its scope doc cites the section; ITB-040 is "
                  "added alongside. CONFIRM if the intent was to move it instead of share it.",
    },
    "32 11 23": {
        "resolved_to": "31 20 00", "packages": ["RFP-030", "RFP-008"], "ruling_date": "2026-08-05",
        "ruling": "Aggregate base courses are covered in Section 31 20 00 Earth Moving.",
        "effect": "Closes the base-course gap that TAB's three Type II deducts price against. "
                  "31 20 00 is RFP-008's section, consistent with TAB carrying the Type II "
                  "under the turf field, building pad and concrete paving. RFP-030 references "
                  "it for the base under its flatwork.",
    },
    "07 84 00": {
        "resolved_to": None, "packages": ["RFP-103"], "ruling_date": "2026-08-05",
        "ruling": "No action required -- there are no fire-rated assemblies on this project.",
        "effect": "DOWNGRADED from REAL GAP. Verified against four sources: partition schedule "
                  "A2-40 publishes only 3F0, 5F0 and 3B0, whose third character is the rating "
                  "code and is 0 (NO RATING) in all three, with UL LISTING '(none)'; LS1-10 at "
                  "Addendum #1 revision shows 0 HR for every IBC 601 element and 0 HR exterior "
                  "walls at >30 ft fire separation distance on all four sides, with opening "
                  "protection NOT REQUIRED and area separation 0 HR; the superseded base-bid "
                  "LS1-10 carries the same 0 HR values, so the addendum did not change them; "
                  "and no door in A11-10's 22-row schedule carries a rating, with no UL design "
                  "number anywhere in the 91-sheet set. IBC 714 penetration firestopping "
                  "applies only to rated assemblies, so the missing section is a documentation "
                  "gap, not a construction risk. The FRP panels' 'CLASS A/C FIRE-RATED' in the "
                  "finish schedule is ASTM E84 surface burning, not an assembly rating.",
    },
}

# Packages given a section by ruling that their own scope doc did not cite.
# Kept separate from PRIMARY so the primary trade is never quietly reassigned.
PM_SECTION_ADDITIONS = {
    "03 30 00": ["ITB-067"],
    "07 25 00": ["ITB-040"],
    "31 20 00": ["RFP-030"],
    # 08.06.26 rulings. Each of these puts the SAME section in two subcontracts on
    # purpose, with the split written into the scope language rather than by giving
    # the section to one and excluding it from the other.
    "02 41 00": ["RFP-002"],   # A4 — RFP-008 building + site demo, RFP-002 abatement demo
    "12 93 00": ["ITB-019"],   # A2 — ITB-018 supplies, ITB-019 installs
}

# Sections one package executes and others must coordinate with. Distinct from a
# gap and from a conflict: writing an exclusion here would read as "no obligation
# to coordinate", which is the opposite of the intent.
PM_COORDINATION = {
    "32 91 13": {
        "executes": "RFP-016",
        "coordinates": ["ITB-019", "RFP-030"],
        "ruling": "PM 08.06.26 (A5): RFP-016 carries it; do not exclude it in the others, "
                  "they need to coordinate with that scope.",
    },
}


def near_matches(num, known):
    """Manual sections that could be what an absent citation meant.

    Offered as CANDIDATES only. "05 31 12 - Steel Roof Decking" almost certainly
    means 05 31 00 Steel Deck, but silently rewriting a cited number is how the
    first index put dead drawings into sixteen packages. The PM decides.
    """
    div, mid = num[:2], num[3:5]
    out = []
    for k in known:
        if k == num or k[:2] != div:
            continue
        if k[3:5] == mid or k.startswith(num):   # same middle pair, or a child number
            out.append(k)
    return sorted(out)


def main():
    entries = catalog()
    sc = scope_citations(entries)
    titles = {e["section"]: e["title"] for e in entries}

    explicit, division = defaultdict(set), defaultdict(set)
    for p, v in sc.items():
        for s in v["cited_sections"]:
            explicit[s].add(p)
        for d, dv in v["division_level_citations"].items():
            if d in ("00", "01"):
                continue                      # every package is bound by these
            for s in dv["sections_in_manual"]:
                division[s].add(p)

    sections, conflicts = [], []
    for e in entries:
        s = e["section"]
        rec = dict(e)
        if s in NUMBER_CORRECTIONS:
            rec["number_correction"] = NUMBER_CORRECTIONS[s]
            rec["primary_package"] = None
            rec["basis"] = "not_a_technical_section"
            sections.append(rec)
            continue
        if e["division"] in ("00", "01"):
            rec["primary_package"] = "ALL PACKAGES"
            rec["basis"] = "general_conditions"
            rec["rationale"] = ("Division 00/01 binds every subcontract and flows down to all "
                                "33 packages; it is not assigned to a trade.")
            sections.append(rec)
            continue

        pkg, basis, why = PRIMARY[s]
        others = sorted((explicit[s] | division[s]) - {pkg})
        added = PM_SECTION_ADDITIONS.get(s, [])
        coord = PM_COORDINATION.get(s)
        rec.update({
            "primary_package": pkg,
            "basis": basis,
            "rationale": why,
            "also_assigned_by_pm_ruling": added,
            "coordination_required_by": (coord["coordinates"] if coord else []),
            "coordination_ruling": (coord["ruling"] if coord else None),
            "referencing_packages": sorted(set(others) - set(added)),
            "cited_explicitly_by": sorted(explicit[s]),
            "reached_by_division_citation_from": sorted(division[s]),
        })
        # A scope doc that cites a section it is not being given is a conflict the
        # PM has to close, not something to resolve silently in an index.
        rival = sorted(explicit[s] - {pkg})
        if s in FLOW_DOWN:
            rec["flow_down"] = FLOW_DOWN[s]
            rec["flows_down_to"] = rival
        elif rival:
            conflicts.append({
                "section": s, "title": titles[s], "assigned_to": pkg, "basis": basis,
                "also_cited_by": rival, "rationale": why,
            })
            rec["conflict"] = True
        sections.append(rec)

    by_pkg = defaultdict(list)
    for r in sections:
        if r.get("primary_package") and r["primary_package"] != "ALL PACKAGES":
            by_pkg[r["primary_package"]].append(r["section"])
        # A section added by ruling belongs in that package's list too, or the
        # package still reads as holding nothing and the ruling has no effect.
        for extra in r.get("also_assigned_by_pm_ruling", []):
            by_pkg[extra].append(r["section"])

    known = {e["section"] for e in entries}
    gaps, gap_titles = defaultdict(list), {}
    for p, v in sc.items():
        for s, t in v["cited_but_not_in_manual"].items():
            gaps[s].append(p)
            if t:
                gap_titles[s] = t

    # Packages that end up carrying no section of their own. Each is explainable,
    # but a package silently holding zero specs is how a subcontract goes out with
    # no technical requirements attached, so every one is named with its reason.
    no_section = {}
    for p in sorted(sc):
        if p in by_pkg:
            continue
        cited_absent = sorted(sc[p]["cited_but_not_in_manual"])
        no_section[p] = {
            "cited_sections_absent_from_manual": cited_absent,
            "reason": NO_SECTION_REASON.get(p, "No section in this manual covers this package."),
        }

    cat = {
        "_generated": "2026-08-05",
        "_source": "Bookmark outline of 04-specs-reports/04.01 - Bid Specification Manual 042026.pdf",
        "_method": ("Section numbers and page ranges come from the manual's own bookmark outline, "
                    "not from parsing body text. Primary responsibility is assigned per section "
                    "with an explicit basis: scope_doc, pm_ruling, or trade_judgment. "
                    "trade_judgment is MY assignment as PM and is not a citation."),
        "_totals": {
            "sections_in_manual": len(sections),
            "technical_sections": sum(1 for r in sections
                                      if r.get("basis") not in ("general_conditions",
                                                                "not_a_technical_section")),
            "assigned_by_scope_doc": sum(1 for r in sections if r.get("basis") == "scope_doc"),
            "assigned_by_pm_ruling": sum(1 for r in sections if r.get("basis") == "pm_ruling"),
            "assigned_by_trade_judgment": sum(1 for r in sections
                                              if r.get("basis") == "trade_judgment"),
            "conflicts": len(conflicts),
            "flow_down_sections": len(FLOW_DOWN),
            "packages_with_no_primary_section": len(no_section),
            "cited_but_absent_from_manual": len(gaps),
            "gaps_closed_by_pm_ruling": len(GAP_RESOLUTIONS),
            "gaps_closed_by_global_rule": len([g for g in gaps if g not in GAP_RESOLUTIONS]),
            "gaps_still_open": 0,
        },
        "sections": sections,
        "sections_by_package": {k: sorted(v) for k, v in sorted(by_pkg.items())},
        "conflicts_needing_pm_ruling": conflicts,
        "packages_with_no_primary_section": no_section,
        "cited_but_absent_from_manual": {
            s: {"title_per_scope_doc": gap_titles.get(s),
                "cited_by": sorted(ps),
                "candidate_sections_in_manual": near_matches(s, known),
                "status": ("CLOSED BY PM RULING" if s in GAP_RESOLUTIONS
                           else "CLOSED BY GLOBAL RULE — cite by title, never by number"),
                "pm_resolution": GAP_RESOLUTIONS.get(s),
                # Where the PM named an owner, use it. Otherwise a section cited by
                # exactly one package is that package's obligation -- it cited it.
                "carried_by": (None if s in GAP_RESOLUTIONS else
                               GAP_OWNERSHIP.get(s, (None, None))[0]
                               or (sorted(ps)[0] if len(set(ps)) == 1 else None)),
                "ownership_ruling": (GAP_OWNERSHIP.get(s, (None, None))[1]
                                     if s not in GAP_RESOLUTIONS else None),
                "how_to_write_it": (None if s in GAP_RESOLUTIONS else
                                    f"Do NOT cite {s}. Put the words "
                                    f"\"{gap_titles.get(s) or 'the specification title'}\" into "
                                    f"the scope verbiage, and draft the obligation from the "
                                    f"scope narrative, the drawings and the bidders' proposals."),
                "note": GAP_NOTES.get(s, "No section with this number is in the manual.")}
            for s, ps in sorted(gaps.items())
        },
        "absent_section_rule": GAP_RULE,
        "number_corrections": NUMBER_CORRECTIONS,
    }
    (INDEX / "spec-section-catalog.json").write_text(json.dumps(cat, indent=2) + "\n")
    (INDEX / "package-spec-citations.json").write_text(json.dumps({
        "_generated": "2026-08-05",
        "_purpose": ("What each package's Scope of Work narrative actually cites, before any "
                     "judgment is applied. Kept separate from the catalog so the assignment "
                     "layer can be reviewed against the raw citations."),
        "packages": sc,
    }, indent=2) + "\n")

    for k, v in cat["_totals"].items():
        print(f"  {k:32} {v}")
    print("\nsections per package:")
    for p, ss in cat["sections_by_package"].items():
        print(f"  {p:8} {len(ss):>3}  {', '.join(ss[:6])}{' ...' if len(ss) > 6 else ''}")


if __name__ == "__main__":
    main()
