#!/usr/bin/env python3
"""
Check a package's scope language against the Attachment A voice profile.

Run this before build_attachment_a.py. It reads the content record rather than
the built .docx, so a violation is fixed at its source instead of being retyped
into a generated file that the next build overwrites.

Only the mechanical rules are checked here -- the ones a regex can decide
without judgment. The profile's substantive rules (say who has the adjacent
work, one obligation per item) are drafting instructions for `scope-drafter`,
and rule 7 gets a soft coverage warning at the end rather than a per-line error,
because whether a given item has an adjacent responsibility is not something a
pattern can know. Item length is likewise reported once for the package, since
a wordy register is one finding rather than twenty-five.

Rules and the evidence behind them:
  .claude/skills/attachment-a-generator/references/voice-profile.md

Calibrated 08.08.26 against the PM's own 40 executed exhibits across two jobs
(1,554 scope items). Before that the thresholds came from a different CORE
author's masonry exhibit and the blank template, and several contradicted his
writing outright -- the abbreviation list banned CMU, MEP and FRP, which he
uses, and the count rule recommended "six (6)" where he writes "6".

Usage:
  python3 scripts/voice_check.py ITB-072
  python3 scripts/voice_check.py --all
  python3 scripts/voice_check.py --all --strict    # warnings fail too

Exit status: 1 if any error (or, with --strict, any warning) was reported.
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "01-index" / "attachment-a-content"

GROUP_HEADER = (
    "Provide all materials, labor, equipment, and supervision for a complete "
    "Scope of Work per plans and specifications. This Scope of Work shall "
    "include, but not be limited to:"
)

# The catch-all group that closes a package. On a 1-exhibit corpus this looked
# like an invention and was warned about; across 40 of the PM's exhibits it
# appears 25 times, so the GROUP is established practice.
#
# What is not his is the sentence the drafts append to it. He writes the title
# bare -- "General Scope Requirements" on its own line, items underneath -- with
# no formula at all. "The following requirements shall apply to all work under
# this Scope of Work package:" appears nowhere in his writing or the template.
# A bare title with no formula and no trailing sentence -- "General Scope
# Requirements", "Submittals, Permits, Testing & General Scope Requirements".
# Matching only the literal phrase would reject a descriptive variant that is
# otherwise in his form.
CATCH_ALL_HEADER = re.compile(r"^[A-Z][^.:]{3,70}?\s*[-–—]?\s*$")
INVENTED_HEADER = "The following requirements shall apply to all work under this Scope of Work"

# Profile rule 3. Deliberately a denylist, not an allowlist of verbs: the first
# cut enumerated the verbs seen in the corpus and flagged Salvage, Perform,
# Abandon, Camera, Relocate and Ensure as defects, which they are not. A voice
# check that cries wolf gets switched off, so this only fires on openers that
# are weak on their face. The executed exhibit itself opens some items with a
# noun ("Excess mortar on the backside of all masonry joints is to be
# troweled..."), so a noun opener is a warning, never an error.
BAD_OPENERS = [
    ("error", re.compile(r"^(The )?Subcontractor (is|will|shall be) responsible", re.I),
     "opens with a responsibility clause; use an imperative verb or "
     "'Subcontractor shall …' (rule 3)"),
    ("error", re.compile(r"^(It is|It shall be|There (is|are)|This includes|"
                         r"Work includes|The work (includes|shall))", re.I),
     "opens with an expletive construction; use an imperative verb (rule 3)"),
    ("warn", re.compile(r"^(Any|Some|Various|Certain|As needed|If required)\b", re.I),
     "opens with a vague quantifier (rule 3)"),
    ("warn", re.compile(r"^(The|A|An)\s+[a-z]", re.I),
     "opens with a noun phrase rather than a verb (rule 3)"),
]

# Profile rule 6. Abbreviations that must be written out in an exhibit.
#
# This list used to hold CMU, MEP, FRP, SOW, T&B and a dozen more, on the
# strength of one executed exhibit in which a different CORE PM wrote "Concrete
# Masonry Unit" five times. Measured against this PM's own three exhibits that
# was simply wrong -- he writes CMU, MEP, FRP, HSS, RTU, E.I.F.S., F.O.B., AHJ
# and LLV without expansion, so the check was flagging his writing as defective.
#
# What survives is the short list where the abbreviation is genuinely ambiguous
# in a contract: a role that has a defined-term equivalent, or a two-letter unit
# that reads as a word.
BANNED_ABBREV = {
    "GC": "Contractor",
    "A/E": "Architect",
    "SOW": "Scope of Work",
    "TYP": "typical",
    "EA": "each",
    "LF": "linear foot",
    "SF": "square foot",
}

# Rule 6, allowed without expansion. Trade abbreviations plus standards bodies.
ALLOWED_ABBREV = {
    "FOB", "AFF", "OSHA", "RFI", "ASI", "ADA", "IBC", "ICC", "ANSI", "NFHS",
    "SWPPP", "NRS", "CSI", "PR", "BIM", "NTP", "GMP", "CMAR", "UL", "ASTM",
    "NEC", "NFPA", "HVAC", "PVC", "HDPE", "II", "III", "IV", "PDF", "CORE",
    "GPS", "EPDM", "TPO", "PSI", "ACI", "AWS", "AISC", "NDS", "IECC",
    # Trade abbreviations measured in the PM's own exhibits.
    "CMU", "MEP", "FRP", "HSS", "RTU", "AHJ", "FAA", "LLV", "NRC", "VIN",
    "CDL", "WF", "MF", "EIFS", "DG", "OFCI", "CFCI",
    # Measured across the mechanical, electrical and low-voltage exhibits.
    "BMS", "AHU", "FFE", "PV", "VAV", "RPDA", "RPPA", "FDC", "PIV", "RCP",
    "DMV", "BACnet", "VFD", "ATS", "UPS", "IDF", "MDF", "CAT6", "EMT",
}

# Two or more capitalised tokens in a row are sign copy, a project name or a
# heading -- "TONOPAH HIGH SCHOOL", "HOME OF THE MUCKERS" -- not abbreviations.
# Flagging their words individually produced five warnings on one correct line.
CAPS_RUN = re.compile(r"\b[A-Z][A-Z0-9&/'-]{1,}(?:\s+[A-Z][A-Z0-9&/'-]{1,})+\b")
QUOTED = re.compile(r"[\"'“‘][^\"'”’]{2,}[\"'”’]")

# Profile rule 8. Longhand dimensions, which match neither source. The negative
# lookahead is what keeps the house's own form legal: "five foot (5') boundary"
# and "five feet (5') outside the building" are correct per rule 8 -- the word
# carries the numeral right behind it -- and an earlier cut flagged both.
SPELLED_DIMENSION = re.compile(
    r"\b(one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"sixteen|eighteen|twenty|twenty-four|thirty|thirty-two|thirty-six|forty|"
    r"forty-eight|sixty|seventy-two|ninety|one hundred|"
    r"one eighth|one quarter|one half|three quarters|one thirty-second|"
    r"one sixteenth)\s+"
    r"(inch|inches|foot|feet|degree|degrees|gauge|mil|mils|ounce|ounces|pound|pounds)"
    r"\b(?!\s*\()",
    re.I,
)

# Profile rule 9. A count written as a word: "six physical hard copies".
#
# The fix used to be "write six (6)", copying the blank template's habit. The
# PM's own exhibits use bare numerals -- "Includes 40 additional manhours",
# "Include an additional 35 steel pipe bollards" -- and the word-plus-paren form
# appears in 1% of his items against 24% of the template's. So the same pattern
# is kept, and the advice it gives is inverted.
SPELLED_COUNT = re.compile(
    r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"fifteen|twenty|thirty|forty|fifty)\s+(?!\()"
    r"(?!hundred|thousand|percent|inch|inches|foot|feet|degree|degrees|gauge|"
    r"mil|mils|ounce|ounces|pound|pounds|days?|weeks?|months?|years?|"
    r"business|calendar|hours?)"
    r"([a-z]+)",
    re.I,
)

DIGITS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
          "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
          "fifteen": 15, "twenty": 20, "thirty": 30, "forty": 40, "fifty": 50}

# Profile rule 12. Exclusions name what is out, not who has it instead. 2 of his
# 192 exclusion lines route (1.0%); the current drafts route 27%. Routing puts a
# representation about another subcontract's contents into this one, and on this
# project it would have been false -- RFP-008 and ITB-072 both excluded track
# signage, so neither could truthfully point at the other.
ROUTED_EXCLUSION = re.compile(
    r"\bwhich (are|is) (included in|provided by|performed by)\b|"
    r"\bincluded in the .{3,60}? Scope of Work\b|"
    r"\b(are|is) (provided|furnished|performed) by (the )?[A-Z]",
)

# His exclusions run median 5 words, p90 11, p99 24.
LONG_EXCLUSION_WORDS = 24

# Profile rule 5. The blank template's install verb, not the PM's -- 25 of his
# 1,554 scope items (1.6%), less even than the other CORE author's 3.4%, while
# "Supply and install" opens 11.8% of his.
HOUSE_VERB = re.compile(r"^Provide and install\b")

# Profile rule 4. Signals that an item names who has the adjacent work. Note
# that bare "Coordinate" does not count -- coordinating with nobody in
# particular is the vagueness this rule exists to catch, so the pattern
# requires a named party after "with".
RESPONSIBILITY = re.compile(
    r"\bby (others|the Owner|the Architect|the Contractor|Contractor|Owner)\b|"
    r"\b[A-Z][a-zA-Z]+ [Ss]ubcontractor\b|"
    r"\bfurnished by\b|\binstalled by\b|\bprovided by\b|\bestablished by\b|"
    r"\blaid out by\b|\bunder the .+ Scope of Work\b|"
    r"\bCoordinate\b[^.]{0,80}\bwith (the )?[A-Z]",
)

# Profile rule 3, and the highest-value check in this file.
#
# Calibrated against the PM's own 1,554 scope items across 40 exhibits and two
# jobs: median 13 words, p90 32, p95 40, p99 57, longest 119.
#
# This threshold has moved three times and the history is the point. It started
# at 55, from a different author's masonry exhibit. Three of the PM's exhibits
# showed a maximum of 46, so it was tightened to 45 -- which turned out to flag
# 2.6% of his own writing once more exhibits arrived. At 8 exhibits 55 looked
# right; at 40 his p99 is 57. It now sits at 60, just past that, where an item
# is almost certainly two obligations rather than one long one.
#
# The lesson worth keeping: each tightening was a small sample masquerading as a
# limit. The package-median check below is the load-bearing one -- his median is
# half the other author's, and that gap is stable across both jobs, while the
# tails are nearly identical (his p90 32, the other author's 34).
LONG_ITEM_WORDS = 60

# The PM's 90th percentile and median, for the package-level register check
# rather than per-item warnings.
VERBOSE_ITEM_WORDS = 32
PM_MEDIAN_WORDS = 13

# Contract terms that carry meaning and are capitalised in the corpus. Checked
# only for the unambiguous ones -- "project" and "owner" appear too often as
# ordinary words for a flag to be worth the noise.
DEFINED_TERMS = {
    "scope of work": "Scope of Work",
    "subcontract amount": "Subcontract Amount",
    "contract documents": "Contract Documents",
    "project manual": "Project Manual",
    "substantial completion": "Substantial Completion",
}


class Report:
    def __init__(self, pkg):
        self.pkg = pkg
        self.rows = []

    def add(self, level, where, msg, text):
        self.rows.append((level, where, msg, text))

    @property
    def errors(self):
        return [r for r in self.rows if r[0] == "error"]

    @property
    def warnings(self):
        return [r for r in self.rows if r[0] == "warn"]

    def print(self):
        if not self.rows:
            print(f"{self.pkg}: clean")
            return
        print(f"\n{self.pkg}: {len(self.errors)} error(s), {len(self.warnings)} warning(s)")
        for level, where, msg, text in self.rows:
            mark = "ERROR" if level == "error" else "warn "
            print(f"  {mark} {where}: {msg}")
            if text:
                snippet = text if len(text) <= 110 else text[:107] + "..."
                print(f"        {snippet}")


def check_line(rep, where, text, is_exclusion=False):
    for abbr, expansion in BANNED_ABBREV.items():
        pattern = r"(?<![A-Za-z0-9])" + re.escape(abbr) + r"(?![A-Za-z0-9])"
        if re.search(pattern, text):
            rep.add("error", where,
                    f"abbreviation '{abbr}' — write '{expansion}' (rule 6)", text)

    scan = QUOTED.sub(" ", CAPS_RUN.sub(" ", text))
    for abbr in set(re.findall(r"(?<![A-Za-z0-9])([A-Z]{2,6})(?![A-Za-z0-9])", scan)):
        if abbr not in ALLOWED_ABBREV and abbr not in BANNED_ABBREV:
            rep.add("warn", where,
                    f"abbreviation '{abbr}' is not on the terms-of-art list — "
                    f"expand it, or add it to ALLOWED_ABBREV (rule 6)", text)

    m = SPELLED_DIMENSION.search(text)
    if m:
        rep.add("error", where,
                f"dimension spelled longhand: '{m.group(0)}' — use numerals and marks (rule 8)",
                text)

    for low, proper in DEFINED_TERMS.items():
        if re.search(r"(?<![A-Za-z])" + low + r"(?![A-Za-z])", text):
            rep.add("warn", where,
                    f"defined term lowercased — write '{proper}' (rule 7)", text)

    if is_exclusion:
        m = ROUTED_EXCLUSION.search(text)
        if m:
            rep.add("error", where,
                    f"routes the work to another package (\"{m.group(0)}\") — the PM's "
                    f"exclusions state what is out and stop, 2 of 192 (rule 12)", text)
        n = len(text.split())
        if n > LONG_EXCLUSION_WORDS:
            rep.add("warn", where,
                    f"{n} words — his exclusions run median 5, p99 {LONG_EXCLUSION_WORDS} "
                    f"(rule 12)", text)
        return

    m = SPELLED_COUNT.search(text)
    if m:
        digit = DIGITS.get(m.group(1).lower(), m.group(1))
        rep.add("warn", where,
                f"count spelled out: '{m.group(0).strip()}' — the PM writes bare "
                f"numerals, '{digit} {m.group(2)}' (rule 9)", text)

    if HOUSE_VERB.match(text):
        rep.add("warn", where,
                "'Provide and install' is the blank template's verb; the PM writes "
                "'Supply and install' (11.8% vs 1.6%) (rule 5)", text)

    if len(text.split()) > LONG_ITEM_WORDS:
        rep.add("error", where,
                f"{len(text.split())} words — past the 99th percentile of the "
                f"PM's own items (median {PM_MEDIAN_WORDS}); split it (rule 3)",
                text)

    for level, pattern, msg in BAD_OPENERS:
        if pattern.match(text):
            rep.add(level, where, msg, text)


def check(pkg, quiet=False):
    path = CONTENT / f"{pkg}.json"
    if not path.exists():
        print(f"{pkg}: no content record at {path.relative_to(ROOT)}", file=sys.stderr)
        return None

    spec = json.loads(path.read_text())
    rep = Report(pkg)
    items_total = responsibility_hits = 0
    lengths = []

    for gi, grp in enumerate(spec.get("scope_groups", []), 1):
        header = grp["header"]
        if GROUP_HEADER in header:
            if header.strip().startswith(("Provide", "Supply")):
                rep.add("error", f"group {gi} header",
                        "missing the trade name before the formula (rule 2)", header)
        elif CATCH_ALL_HEADER.match(header.strip()):
            pass                          # his own closing group, written bare
        elif INVENTED_HEADER in header:
            rep.add("error", f"group {gi} header",
                    "the trailing sentence is invented — the PM writes this group's "
                    "title bare, e.g. 'General Scope Requirements' with the items "
                    "underneath and no formula (rule 11)", header)
        else:
            rep.add("error", f"group {gi} header",
                    "does not carry the template's group-header formula (rule 2)", header)

        for ii, item in enumerate(grp["items"], 1):
            where = f"group {gi} item {ii}"
            check_line(rep, where, item)
            items_total += 1
            lengths.append(len(item.split()))
            if RESPONSIBILITY.search(item):
                responsibility_hits += 1

    for ei, exc in enumerate(spec.get("exclusions", []), 1):
        check_line(rep, f"exclusion {ei}", exc, is_exclusion=True)

    # Rule 3, reported once for the package rather than per item. Warning on
    # every item above the PM's 90th percentile produced 25 warnings on one
    # package, which is how a check gets ignored -- and it misrepresents the
    # finding, because item length here is a property of the package's whole
    # drafting register, not a defect in 25 separate places.
    if lengths:
        lengths.sort()
        median = lengths[len(lengths) // 2]
        verbose = sum(1 for n in lengths if n > VERBOSE_ITEM_WORDS)
        if median > PM_MEDIAN_WORDS * 1.5:
            rep.add("warn", "package",
                    f"median item {median} words against the PM's {PM_MEDIAN_WORDS}; "
                    f"{verbose} of {len(lengths)} items exceed his 90th percentile "
                    f"({VERBOSE_ITEM_WORDS}). The register is wordier than his "
                    f"exhibits throughout (rule 3)", "")

    # Rule 7 as a coverage check. The PM names a counterparty in 11% of his
    # scope items; a package well under that is usually leaving adjacent
    # responsibility implied rather than genuinely having none.
    if items_total:
        share = responsibility_hits / items_total
        if share < 0.08:
            rep.add("warn", "package",
                    f"only {responsibility_hits} of {items_total} items "
                    f"({share:.0%}) name a counterparty or coordination partner; "
                    f"the PM's own exhibits run 11.4% (rule 7)", "")

    if not quiet:
        rep.print()
    return rep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("package", nargs="?", help="package_id, e.g. ITB-072")
    ap.add_argument("--all", action="store_true", help="check every content record")
    ap.add_argument("--strict", action="store_true", help="warnings fail too")
    args = ap.parse_args()

    if args.all:
        pkgs = [p.stem for p in sorted(CONTENT.glob("*.json"))]
    elif args.package:
        pkgs = [args.package]
    else:
        ap.error("give a package_id or --all")

    reports = [r for r in (check(p) for p in pkgs) if r]
    errors = sum(len(r.errors) for r in reports)
    warnings = sum(len(r.warnings) for r in reports)
    print(f"\n{len(reports)} package(s): {errors} error(s), {warnings} warning(s)")
    sys.exit(1 if errors or (args.strict and warnings) else 0)


if __name__ == "__main__":
    main()
