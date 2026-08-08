#!/usr/bin/env python3
"""
Check a package's scope language against the Attachment A voice profile.

Run this before build_attachment_a.py. It reads the content record rather than
the built .docx, so a violation is fixed at its source instead of being retyped
into a generated file that the next build overwrites.

Only the mechanical rules are checked here -- the ones a regex can decide
without judgment. The profile's substantive rules (say who has the adjacent
work, one obligation per item) are drafting instructions for `scope-drafter`,
and rule 4 gets a soft coverage warning at the end rather than a per-line error,
because whether a given item has an adjacent responsibility is not something a
pattern can know.

Rules and the evidence behind them:
  .claude/skills/attachment-a-generator/references/voice-profile.md

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

# A second header formula both current drafts use for the catch-all group that
# closes a package. It is not in the corpus -- no executed exhibit on file has
# such a group -- so it is accepted with a warning rather than treated as a
# defect, and it stays that way until an executed exhibit settles it.
ALT_GROUP_HEADER = "The following requirements shall apply to all work under this Scope of Work"

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
BANNED_ABBREV = {
    "CMU": "Concrete Masonry Unit",
    "MEP": "Mechanical, Electrical and Plumbing",
    "GC": "Contractor",
    "A/E": "Architect",
    "OFCI": "Owner Furnished, Contractor Installed",
    "CFCI": "Contractor Furnished, Contractor Installed",
    "T&B": "Test and Balance",
    "VE": "value engineering",
    "SOW": "Scope of Work",
    "FRP": "fiberglass reinforced panel",
    "DG": "decomposed granite",
    "AC": "asphalt concrete",
    "PT": "post-tensioned",
    "SS": "stainless steel",
    "TYP": "typical",
    "EA": "each",
    "LF": "linear foot",
    "SF": "square foot",
}

# Rule 6, allowed: unambiguous terms of art.
ALLOWED_ABBREV = {
    "FOB", "AFF", "OSHA", "RFI", "ASI", "ADA", "IBC", "ICC", "ANSI", "NFHS",
    "SWPPP", "NRS", "CSI", "PR", "BIM", "NTP", "GMP", "CMAR", "UL", "ASTM",
    "NEC", "NFPA", "HVAC", "PVC", "HDPE", "II", "III", "IV", "PDF", "CORE",
    "GPS", "ADA", "EPDM", "TPO", "PSI", "ACI", "AWS", "AISC", "NDS", "IECC",
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

# Profile rule 8. A bare count with no numeral: "six physical hard copies".
BARE_COUNT = re.compile(
    r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
    r"fifteen|twenty|thirty|forty|fifty)\s+(?!\()"
    r"(?!hundred|thousand|percent|inch|inches|foot|feet|degree|degrees|gauge|"
    r"mil|mils|ounce|ounces|pound|pounds|days?|weeks?|months?|years?|"
    r"business|calendar|hours?)"
    r"([a-z]+)",
    re.I,
)

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

# Profile rule 11.
LONG_ITEM_WORDS = 55

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
        return

    m = BARE_COUNT.search(text)
    if m:
        rep.add("warn", where,
                f"count without numeral: '{m.group(0).strip()}' — "
                f"write '{m.group(1)} ({m.group(1)}) …' style (rule 8)", text)

    words = len(text.split())
    if words > LONG_ITEM_WORDS:
        rep.add("warn", where,
                f"{words} words — items above {LONG_ITEM_WORDS} usually carry "
                f"two obligations; split (rules 11, 12)", text)

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

    for gi, grp in enumerate(spec.get("scope_groups", []), 1):
        header = grp["header"]
        if GROUP_HEADER in header:
            if header.strip().startswith(("Provide", "Supply")):
                rep.add("error", f"group {gi} header",
                        "missing the trade name before the formula (rule 2)", header)
        elif ALT_GROUP_HEADER in header:
            rep.add("warn", f"group {gi} header",
                    "uses the catch-all header variant, which no executed exhibit "
                    "on file uses — confirm it is house style (rule 2)", header)
        else:
            rep.add("error", f"group {gi} header",
                    "does not carry the template's group-header formula (rule 2)", header)

        for ii, item in enumerate(grp["items"], 1):
            where = f"group {gi} item {ii}"
            check_line(rep, where, item)
            items_total += 1
            if RESPONSIBILITY.search(item):
                responsibility_hits += 1

    for ei, exc in enumerate(spec.get("exclusions", []), 1):
        check_line(rep, f"exclusion {ei}", exc, is_exclusion=True)

    # Rule 4 as a coverage check. The executed exhibit names another party in
    # 14% of its lines; a package well under that is usually leaving adjacent
    # responsibility implied rather than genuinely having none.
    if items_total:
        share = responsibility_hits / items_total
        if share < 0.08:
            rep.add("warn", "package",
                    f"only {responsibility_hits} of {items_total} items "
                    f"({share:.0%}) name who has the adjacent work; the executed "
                    f"exhibit runs 14% (rule 4)", "")

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
