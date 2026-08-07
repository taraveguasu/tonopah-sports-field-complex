#!/usr/bin/env python3
"""
Inventory EVERY subcontractor proposal by package -- all bidders, not just the
awarded sub.

Per PM direction 07.31.26: losing bidders routinely itemize something the
drawings left ambiguous, and those line items are the clearest signal of what
must be spelled out explicitly in the subcontract. Proposals are NOT an
authority tier; they are read diagnostically.

Filenames encode package number, sub name, and status flags. Scope-review
agendas and homework responses are filed by SUB name rather than package, so
they are joined back through the sub names discovered in the proposals.

Usage:  python3 scripts/build-proposal-inventory.py
Writes: 01-index/proposal-inventory.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUBS = ROOT / "00-source-docs" / "SUBCONTRACTOR FILES" / "21.0 - Subcontractor Proposals"
OUT = ROOT / "01-index" / "proposal-inventory.json"

# Filename package numbers -> package_id. The bid documents drift between the
# RFP/ITB list numbering and the numbers used on scope docs and proposals.
NUM_TO_PACKAGE = {
    "002": "RFP-002", "008": "RFP-008", "016": "RFP-016", "021": "RFP-021",
    "022": "RFP-022", "023": "RFP-023", "030": "RFP-030", "031": "RFP-031",
    "033": "RFP-033", "045": "RFP-045", "061": "RFP-060", "094": "RFP-094",
    "098": "RFP-098", "100": "RFP-100", "103": "RFP-103", "109": "RFP-109",
    "007": "ITB-008", "018": "ITB-018", "019": "ITB-019", "040": "ITB-040",
    "044": "ITB-044", "054": "ITB-054", "056": "ITB-056", "062": "ITB-062",
    "066": "ITB-066", "067": "ITB-067", "071": "ITB-071", "072": "ITB-072",
    "074": "ITB-074", "077": "ITB-077", "078": "ITB-078", "085": "ITB-085",
    "089": "ITB-089",
    # Test & Balance is inside RFP-100's title per CLAUDE.md, but was solicited
    # under its own number.
    "102": "RFP-100",
}

# Numbers that appear on proposals but match no package in the RFP/ITB lists.
UNMAPPED_NUMBERS = {
    "065": "'Sealed Concrete' -- overlaps ITB-066 (Fluid-Applied Flooring) and ITB-067 "
           "(Concrete Finishing); the same scope also appears under 066 and 067 filenames. "
           "Which package carries sealed concrete is unresolved.",
    "070": "'Final Cleaning' -- NO corresponding package exists in either the 1% list or the "
           "ITB list in CLAUDE.md. Four proposals were solicited and received. Either a "
           "package is missing from the project's package list, or this scope is being "
           "carried directly by CORE.",
}

FLAG_PATTERNS = [
    (r"\(w backup\)", "has_backup"),
    (r"\(backup, no Form\)", "backup_but_no_signed_bid_form"),
    (r"\(no backup,? no Form\)", "no_backup_no_form"),
    (r"\(Form\)", "signed_form_only"),
    (r"\(value only\)", "value_only_no_scope_detail"),
    (r"\bLATE\b", "late_submission"),
    (r"DO NOT USE", "marked_do_not_use"),
    (r"not submitted to BC", "not_submitted_via_building_connected"),
    (r"\(SUPPLY[^)]*\)", "supply_only"),
    (r"\(INSTALL\)", "install_only"),
    (r"descope", "descope_document"),
    (r"Descope Qs", "descope_questions"),
    (r"\bALT\b|\(ALT", "alternate_pricing"),
    (r"\bR[1-9]\b", "revised_submission"),
    (r"Substitution Comparison", "substitution_request"),
    (r"Images\+Video", "supplemental_media"),
]


def parse_flags(name: str):
    return sorted({tag for pat, tag in FLAG_PATTERNS if re.search(pat, name, re.I)})


def parse_numbers(name: str):
    """Leading package numbers; a proposal may span several ('066, 067 ...')."""
    m = re.match(r"^\s*((?:\d{3}\s*,\s*)*\d{3})\b", name)
    if not m:
        return []
    return re.findall(r"\d{3}", m.group(1))


def sub_name(name: str) -> str:
    """Everything after the trade description, before the status parens."""
    stem = Path(name).stem
    parts = stem.split(" - ")
    if len(parts) >= 2:
        cand = parts[1]
    else:
        cand = parts[0]
    cand = re.sub(r"\(.*", "", cand).strip()
    return cand or "UNKNOWN"


def norm_sub(s: str) -> str:
    """Loose key for joining agendas/homework to proposals."""
    s = s.lower()
    s = re.sub(r"\b(inc|llc|co|corp|corporation|company|enterprises|construction|"
               r"mechanical|electric|electrical|fence|sports|builders|international)\b", "", s)
    s = re.sub(r"[^a-z0-9]", "", s)
    return s


# Agendas and homework responses are filed under short or misspelled sub names that
# fuzzy matching either misses or, worse, mis-joins. Resolved by hand against the
# proposal list. "TAB" is the trap: it means Test-And-Balance (RFP-100) here, but it
# is also part of "NewCom TAB", the demolition contractor on RFP-008.
SUPPORT_ALIASES = {
    "cg&b": ["RFP-022"],                 # CG & B Enterprises
    "cali.bleachers": ["RFP-094"],       # California Bleachers NATA
    "calibleachers": ["RFP-094"],
    "cheeck": ["RFP-030"],               # misspelling of Cheek Construction
    "m&h": ["RFP-060"],                  # M & H
    "ndx": ["RFP-008"],
    "tab": ["RFP-100"],                  # Test & Balance -- NOT NewCom TAB on RFP-008
    "usmechanical": ["RFP-098", "RFP-100"],
    "universalmech.": ["RFP-098"],       # Universal Plumbing & Heating
    "universalmech": ["RFP-098"],
    "jwelectric": ["RFP-103"],
    # GTI 1 Inc. IS BrightView (same entity, two names) -- confirmed by PM 07.31.26.
    # Their scope review agenda and homework response are filed under "GTI" while their
    # proposals are filed under "BrightView". Do not count them as two bidders.
    "gti": ["RFP-016"],
}

# Subcontractors that appear under more than one name across the bid documents.
ENTITY_ALIASES = {
    "GTI 1 Inc.": {
        "same_as": "BrightView",
        "confirmed_by": "PM, 2026-07-31",
        "appears_as_gti_in": [
            "1% Descopes/GTI  Scope Review Meeting Agenda.docx",
            "1% Descopes/Homework Responses/GTI Homework Response.pdf",
        ],
        "appears_as_brightview_in": [
            "Other/1% proposals for RFP-016 (Irrigation) and RFP-022 (Synthetic Turf)",
        ],
        "note": "Bidder counts must not double-count these as separate firms.",
    }
}

# Support files that are not subcontractor-specific at all.
NON_SUB_SUPPORT = {"tonopahhsfield-homeworktracker"}


def main():
    proposals = defaultdict(list)      # package_id -> [record]
    unmapped = []
    all_subs = {}                      # norm key -> {display, packages}

    for folder, listing in [
        ("1% Subcontractor Proposals", SUBS / "1% Subcontractor Proposals"),
        ("Other Proposals", SUBS / "Other Proposals"),
    ]:
        for f in sorted(listing.glob("*.pdf")):
            nums = parse_numbers(f.name)
            sub = sub_name(f.name)
            rec_base = {
                "file": str(f.relative_to(ROOT / "00-source-docs")),
                "subcontractor": sub,
                "source_folder": folder,
                "flags": parse_flags(f.name),
            }
            if not nums:
                unmapped.append({**rec_base, "reason": "no leading package number"})
                continue
            if len(nums) > 1:
                rec_base["spans_multiple_packages"] = [NUM_TO_PACKAGE.get(n, f"UNMAPPED-{n}") for n in nums]
            for n in nums:
                pid = NUM_TO_PACKAGE.get(n)
                if not pid:
                    unmapped.append({**rec_base, "filename_number": n,
                                     "reason": UNMAPPED_NUMBERS.get(n, "number not in package list")})
                    continue
                proposals[pid].append(rec_base)
                k = norm_sub(sub)
                all_subs.setdefault(k, {"display": sub, "packages": set()})
                all_subs[k]["packages"].add(pid)

    # Join scope-review agendas and homework responses (filed by sub, not package)
    desc_dir = SUBS / "1% Subcontractor Proposals" / "1% Descopes"
    support = defaultdict(list)
    for f in sorted(list(desc_dir.glob("*.*")) + list((desc_dir / "Homework Responses").glob("*.*"))):
        if f.is_dir():
            continue
        stem = f.stem
        nums = parse_numbers(f.name)
        matched = set()
        if nums:
            matched = {NUM_TO_PACKAGE[n] for n in nums if n in NUM_TO_PACKAGE}
        else:
            raw = re.sub(r"(Scope Review Meeting Agenda|Homework Response\w*|Homeowork Response|"
                         r"Descope\w*|\(.*?\)|\bR\d\b).*", "", stem).strip()
            flat = re.sub(r"\s+", "", raw.lower())
            if flat in NON_SUB_SUPPORT:
                rec_extra = "project-level tracker, not subcontractor-specific"
                support["_NON_SUB"].append({"file": str(f.relative_to(ROOT / "00-source-docs")),
                                            "note": rec_extra})
                continue
            if flat in SUPPORT_ALIASES:
                matched = set(SUPPORT_ALIASES[flat])
            else:
                key = norm_sub(raw)
                for k, v in all_subs.items():
                    if key and k and (key == k or (len(key) > 3 and (key in k or k in key))):
                        matched |= v["packages"]
        rec = {
            "file": str(f.relative_to(ROOT / "00-source-docs")),
            "kind": ("scope_review_agenda" if "Agenda" in stem
                     else "homework_response" if "omework" in stem
                     else "descope"),
            "matched_by": "package_number" if nums else "subcontractor_name",
        }
        if matched:
            for pid in matched:
                support[pid].append(rec)
        else:
            support["_UNMATCHED"].append({**rec, "stem": stem})

    packages = {}
    for pid in sorted(set(list(proposals) + [p for p in support if not p.startswith("_")])):
        recs = proposals.get(pid, [])
        bidders = sorted({r["subcontractor"] for r in recs})
        packages[pid] = {
            "bidder_count": len(bidders),
            "bidders": bidders,
            "proposals": recs,
            "supporting_docs": support.get(pid, []),
        }

    inventory = {
        "_generated": "2026-07-31",
        "_purpose": (
            "Every bidder's proposal per package, not just the awarded sub's. Proposals are NOT "
            "an authority tier -- they never override the contract documents. They are read to "
            "surface the assumptions bidders made where the documents were ambiguous, and to "
            "expose scope gaps. Boilerplate general exclusions are ignored. Any proposal that "
            "contradicts a contract document is flagged for PM, never silently adopted."
        ),
        "_totals": {
            "packages_with_proposals": len(packages),
            "proposal_files": sum(len(v["proposals"]) for v in packages.values()),
            "supporting_files": sum(len(v["supporting_docs"]) for v in packages.values()),
        },
        "packages": packages,
        "_entity_aliases": ENTITY_ALIASES,
        "_findings_for_pm": [
            {
                "id": "PI-01",
                "severity": "resolved",
                "title": "GTI 1 Inc. is BrightView -- same entity, two filing names",
                "detail": (
                    "'GTI  Scope Review Meeting Agenda.docx' records a 5/15/2026 scope review, scopes "
                    "'Landscape, Irrigation'. No proposal is filed under GTI. PM confirmed 07.31.26 that "
                    "GTI 1 Inc. and BrightView are the same firm; BrightView's proposals cover RFP-016 "
                    "(Irrigation) and RFP-022 (Synthetic Turf, marked LATE - DO NOT USE). Recorded in "
                    "_entity_aliases so bidder counts do not treat them as two firms."
                ),
                "why_it_still_matters": (
                    "BrightView/GTI did NOT win RFP-016 -- Black Canyon did. Per PM direction, a losing "
                    "bidder's scope review is the most valuable kind, and this one is unusually explicit "
                    "about what the documents left ambiguous. GTI stated these EXCLUSIONS: tree demo, "
                    "ground treatment, pole vault, discus and shot put pads, trench drains, concrete pads. "
                    "And these INCLUSIONS/ASSUMPTIONS: temporary irrigation (assumed surface-mounted), site "
                    "amenities, prevailing wage. Every one of those is a boundary RFP-016's Attachment A "
                    "should state explicitly. Note the exclusions corroborate PM rulings already made -- "
                    "trench drains and concrete pads to RFP-030, tree demo to RFP-008 (SOW-008 includes "
                    "'tree removal, including stump grinding'), pole vault and shot put to ITB-019/RFP-030."
                ),
                "pm_action": "None outstanding. Feed GTI's exclusion list into RFP-016 drafting.",
            },
            {
                "id": "PI-02",
                "severity": "high",
                "title": "'070 Final Cleaning' has four proposals but no package in the project package list",
                "detail": (
                    "Proposals from CSI, Lady Lux, and Nevada Angels (plus a Nevada Angels descope) are "
                    "filed under number 070 'Final Cleaning'. Neither the 1% list nor the ITB list in "
                    "CLAUDE.md contains a Final Cleaning package."
                ),
                "why_it_matters": (
                    "Either the 33-package list is incomplete, or final cleaning is being self-performed by "
                    "CORE. Final cleaning is commonly assumed by every trade to be someone else's -- if it "
                    "is neither a package nor an explicit CORE scope, it is an uncovered cost."
                ),
                "pm_action": "Confirm whether Final Cleaning is a 34th package, a CORE general-conditions scope, or folded into another package.",
            },
            {
                "id": "PI-03",
                "severity": "medium",
                "title": "'065 Sealed Concrete' overlaps ITB-066 and ITB-067 with the same bidders",
                "detail": (
                    "SI Legacy's sealed-concrete descope is filed under 065, while the same scope also "
                    "appears under 066 (Sealed Concrete), 067 (Fluid Applied Floor) and combined "
                    "'066, 067' filenames from NRC, Ryerson and FW Specialties. ITB-066 is Fluid-Applied "
                    "Flooring and ITB-067 is Concrete Finishing."
                ),
                "why_it_matters": (
                    "ITB-066 and ITB-067 currently show the identical four bidders. The boundary between "
                    "fluid-applied flooring, sealed concrete and concrete finishing is not established by "
                    "the numbering, and ITB-066 has no spec section in the manual."
                ),
                "pm_action": "Rule on which package carries sealed concrete before either exhibit is drafted.",
            },
            {
                "id": "PI-04",
                "severity": "medium",
                "title": "Bidders priced across package boundaries -- relevant to planned package combinations",
                "detail": (
                    "Combined proposals on file: '016, 022' (Sprinturf, irrigation + synthetic turf), "
                    "'040, 044' (Gleeson Powers, sealants + insulation), '066, 067' (NRC, Ryerson, FW "
                    "Specialties), '072, 089' (Image360, Y C Signs, signage + scoreboards)."
                ),
                "why_it_matters": (
                    "These are the seams where the market itself combines scope. Worth weighing against the "
                    "package combinations the PM intends, since a combination the bidders already priced "
                    "together carries less leveling risk."
                ),
                "pm_action": "Cross-check against the forthcoming package combination list.",
            },
            {
                "id": "PI-05",
                "severity": "medium",
                "title": "Supply/install splits appear inside single packages",
                "detail": (
                    "ITB-019: Exerplay and SportsEdge bid SUPPLY, Great Western bid INSTALL. ITB-056: "
                    "Hallgren bid SUPPLY, SNV Specialties bid INSTALL. ITB-018 and ITB-078 also carry "
                    "SUPPLY-only bids from Exerplay. RFP-094 and RFP-109 received SUPPLY-only proposals."
                ),
                "why_it_matters": (
                    "A package awarded to a supply-only bidder leaves installation uncovered unless the "
                    "exhibit names who installs. Sheet A1-20's Site Equipment Matrix designates Scoreboard, "
                    "Bleachers, Press Box, Trash Receptacle and Ticket Booth as CFCI (contractor furnished, "
                    "contractor installed), so those cannot be left supply-only."
                ),
                "pm_action": "For each split package, confirm the install side is carried by a named package.",
            },
            {
                "id": "PI-06",
                "severity": "medium",
                "title": "Proposals with no signed Bid Form, late submissions, and value-only bids",
                "detail": (
                    "Flags parsed from filenames across all packages: 'backup, no Form' (no signed bid "
                    "form), 'LATE', 'not submitted to BC' (bypassed Building Connected), 'DO NOT USE', and "
                    "'value only' (RFP-103 Conti -- a price with no scope detail). Per-file flags are in "
                    "each package's proposals array."
                ),
                "why_it_matters": (
                    "NRS 338.16995 governs the 1% list. A proposal that never came through Building "
                    "Connected or lacks a signed bid form is a procurement-process exposure, not just a "
                    "paperwork gap. RFP-045's awarded sub, Foursquare, is flagged both 'no Form' and "
                    "'LATE - not submitted to BC'."
                ),
                "pm_action": "Review the flagged proposals for procurement compliance before those subcontracts issue.",
            },
            {
                "id": "PI-07",
                "severity": "low",
                "title": "CLAUDE.md's claim that ITB packages have no proposals on hand is wrong",
                "detail": (
                    "CLAUDE.md states 'Non-1% (ITB) packages have no awarded-sub proposal on hand yet in "
                    "SUBCONTRACTOR FILES -- those still draft from generic RFP/ITB/spec scope.' In fact all "
                    "17 ITB packages have proposals in 'Other Proposals', 86 files total."
                ),
                "why_it_matters": "Every ITB exhibit can be informed by real bidder assumptions, not generic scope language.",
                "pm_action": "None -- CLAUDE.md corrected as part of this pass.",
            },
        ],
        "_unmapped_files": unmapped,
        "_unmatched_supporting_docs": support.get("_UNMATCHED", []),
        "_non_subcontractor_support_files": support.get("_NON_SUB", []),
    }
    OUT.write_text(json.dumps(inventory, indent=2) + "\n")

    print(f"packages with proposals: {len(packages)}")
    print(f"proposal files:          {inventory['_totals']['proposal_files']}")
    print(f"supporting files:        {inventory['_totals']['supporting_files']}")
    print(f"unmapped proposal files: {len(unmapped)}")
    print(f"unmatched support docs:  {len(support.get('_UNMATCHED', []))}")
    print(f"\n-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
