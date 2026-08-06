#!/usr/bin/env python3
"""
Assign every drawing sheet to the packages that build from it, deriving the
assignment from the SCOPE DOCS rather than from reading the drawing.

This redoes work the PM rejected on 07.31.26. The first index assigned sheets by
reading each drawing and judging what trade it looked like -- which inverts the
authority hierarchy. The drawings show extent and location; the Scope of Work
narrative decides whose work it is. So the narrative supplies the vocabulary and
the sheets are matched against it, not the other way round.

Four signals, strongest first, and every assignment carries its evidence:

  sheet_citation   the scope doc names the sheet outright ("See A1-20 for Gate
                   Schedule and details"). Only 8 packages do this, but where it
                   exists it is decisive.
  spec_section     the sheet cites a spec section whose primary package is known
                   from spec-section-catalog.json.
  scope_terms      distinctive trade vocabulary from the scope doc found on the
                   sheet. Distinctive is computed, not hand-listed: the 33 scope
                   docs share a long boilerplate preamble, so any term appearing
                   in more than a few of them carries no trade signal and is
                   dropped.
  discipline       the sheet's discipline prefix, used only to catch sheets no
                   other signal reached, and always marked as the weak signal it
                   is.

Sheets are read at their CURRENT revision -- sheet-corpus.json already resolves
the seven sheets Addendum #1 reissued.

Usage:  python3 scripts/assign_sheets.py
Writes: 01-index/sheet-package-assignments.json
"""

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs"
INDEX = ROOT / "01-index"
SCOPES = SRC / "02-trade-scopes-bidform" / "_extracted"

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

# Discipline prefix -> packages that plausibly build from that discipline. Used
# ONLY as a last-resort net for sheets no stronger signal reached, and recorded
# as "discipline" so a reviewer can see it was never more than that.
DISCIPLINE = {
    "G": None, "LS": None,                       # general/life-safety: all packages
    "C": ["RFP-008"], "MG": ["RFP-008"], "GD": ["RFP-008"], "UT": ["RFP-008"],
    "L": ["RFP-016", "RFP-021", "RFP-022", "ITB-019"],
    "A": ["RFP-060"], "AD": ["RFP-002", "RFP-008"],
    "S": ["RFP-033", "RFP-030"],
    "M": ["RFP-100"], "P": ["RFP-098"], "E": ["RFP-103"], "ED": ["RFP-103"],
}

STOP = set("""the a an and or of for to in on at by with from as is are be shall will all any
each per this that these those which not no non other others such same than then there here
work works provide provides provided providing include includes including included complete
completed required require requires requirement requirements specified specify specifies
contractor subcontractor proposer contract documents plans specifications section sections
division divisions scope proposal package base bid value date shall may must new existing
installation install installed installing material materials labor equipment supervision
coordinate coordination related primary refer reference see also if when where prior after
before during upon out into over under above below between within without through per
system systems necessary applicable general typical standard standards code codes""".split())

TOKEN = re.compile(r"[A-Za-z][A-Za-z\-']{2,}")

# Tables that assign responsibility for a product, as opposed to listing one
# discipline's own equipment. Detected from CONTENT, not from the table's parsed
# name: on A1-20 the table finder names the Site Equipment Matrix
# "table (MANUFACTURER)" because it never recovers the title, so a name-based
# test misses the one table on the project that states who furnishes what.
RESPONSIBILITY_CONTENT = re.compile(r"\bRESPONSIBIL|\bCFCI\b|\bOFCI\b|\bOFOI\b|\bCFOI\b", re.I)
RESPONSIBILITY_NAME = re.compile(r"MATRIX|LEGEND|INDEX", re.I)


def is_responsibility_table(t):
    blob = " ".join([t.get("table") or ""]
                    + [" ".join(c for c in row if c) for row in t.get("rows", [])]
                    + t.get("raw_lines", []))
    return bool(RESPONSIBILITY_CONTENT.search(blob)
                or RESPONSIBILITY_NAME.search(t.get("table") or ""))


def scope_bodies():
    """Trade-specific portion of each scope doc, keyed by package."""
    out = {}
    for f in sorted(SCOPES.glob("Scope of Work - *.txt")):
        m = re.match(r"Scope of Work - (\d{3})", f.name)
        if not m or m.group(1) not in SCOPE_FILE_TO_PACKAGE:
            continue
        text = f.read_text(errors="ignore")
        # The preamble down to "Primary Specifications" is identical in all 33.
        i = text.find("Primary Specifications")
        out[SCOPE_FILE_TO_PACKAGE[m.group(1)]] = (text[i:] if i > 0 else text, text)
    return out


def distinctive_terms(bodies, haystacks, max_docs=4, max_sheet_fraction=0.25):
    """Terms and phrases that identify a trade, computed rather than hand-listed.

    Calibrated on BOTH corpora, because each removes a different kind of noise:

    Scope-doc frequency removes shared contract language. Even after the preamble
    is cut, the 33 narratives repeat a great deal of it -- "provide all tests and
    certifications", "receive, offload, handle, store". A term carried by more
    than a handful of them cannot distinguish between them.

    Sheet frequency removes drawing boilerplate, and this is the one that matters
    for precision. "Architect", "las vegas", "adjacent", "minimum", "record" all
    survive the scope-doc filter -- each appears in only a few narratives -- but
    every sheet in the set carries them in its title block or general notes, so
    they say nothing about which package builds from a given sheet. Without this
    second axis the assignment produced fourteen packages per sheet, with the
    right one on top and a long tail of nonsense under it.
    """
    per_doc = {}
    for pkg, (body, _) in bodies.items():
        words = [w.lower() for w in TOKEN.findall(body)]
        uni = {w for w in words if w not in STOP}
        bi = {f"{a} {b}" for a, b in zip(words, words[1:])
              if a not in STOP and b not in STOP}
        per_doc[pkg] = uni | bi

    df = Counter()
    for terms in per_doc.values():
        df.update(terms)
    candidates = {t for t, n in df.items() if n <= max_docs and len(t) > 5}

    sheet_df = Counter()
    for hay in haystacks.values():
        sheet_df.update(t for t in candidates if t in hay)
    ceiling = max_sheet_fraction * len(haystacks)
    keep = {t for t in candidates if sheet_df[t] <= ceiling}

    return ({pkg: terms & keep for pkg, terms in per_doc.items()},
            sorted(candidates - keep))


# The package title names the product. For a small equipment package -- lockers,
# scoreboards, flagpoles -- the scope doc is short and accumulates too little
# vocabulary to score, but the sheet names the product outright in a keynote or a
# schedule row. Sheet-frequency filtering then removes any of these that turn out
# to be ubiquitous, so the list can stay generous.
PACKAGE_TITLES = {
    "RFP-002": "abatement building wrecking asbestos", "RFP-008": "site demolition earthwork asphalt paving utilities signage striping",
    "RFP-016": "landscaping irrigation", "RFP-021": "running track surfacing",
    "RFP-022": "synthetic turf sports field", "RFP-023": "fencing gates",
    "RFP-030": "concrete", "RFP-031": "masonry",
    "RFP-033": "structural steel ornamental metals", "RFP-045": "metal roofing fascia soffit panels",
    "RFP-060": "framing drywall painting", "RFP-094": "bleachers press box",
    "RFP-098": "plumbing", "RFP-100": "hvac building control",
    "RFP-103": "electrical low voltage sports field lighting",
    "RFP-109": "prefabricated ticket booth",
    "ITB-008": "surveying layout staking", "ITB-018": "site furnishings bench receptacle",
    "ITB-019": "track field athletic equipment goal post",
    "ITB-040": "moisture protection sealants caulking", "ITB-044": "insulation",
    "ITB-054": "special doors coiling overhead", "ITB-056": "doors frames hardware",
    "ITB-062": "acoustical ceilings", "ITB-066": "fluid-applied flooring epoxy",
    "ITB-067": "concrete finishing sealed", "ITB-071": "visual display boards menu display case",
    "ITB-072": "building signage", "ITB-074": "fire protection specialties corner guards cabinets mirrors",
    "ITB-077": "lockers", "ITB-078": "flagpoles", "ITB-085": "warming kitchen food service",
    "ITB-089": "scoreboards",
}
TITLE_GENERIC = {"building", "site", "sports", "field", "special", "protection", "service",
                 "control", "low", "press", "post", "case", "box"}


def title_nouns():
    """Product nouns from each package title, singular and plural."""
    out = {}
    for pkg, title in PACKAGE_TITLES.items():
        words = {w for w in title.split() if len(w) > 3 and w not in TITLE_GENERIC}
        forms = set()
        for w in words:
            forms.add(w)
            forms.add(w[:-1] if w.endswith("s") else w + "s")
        out[pkg] = forms
    return out


def structured_text(rec, structured):
    """Two tiers, because WHERE a product noun sits decides what it means.

    A keynote or sheet title naming the product ("METAL LOCKERS, CFCI" on A10-30)
    says the sheet carries that work -- this is the whole reason small equipment
    packages get found at all, since their scope docs are too short to accumulate
    vocabulary. The same noun in a row of some other discipline's schedule says
    nothing: M0-05's mechanical schedule mentions doors and ceilings in passing
    and would otherwise pull in ITB-054, ITB-056 and ITB-062.

    Returns (named, mentioned): named is the strong location, mentioned the weak.
    """
    st = structured.get(rec["sheet"]) or {}
    named = [rec["title"]] + list(st.get("keynotes", {}).values())
    mentioned = list(st.get("notes", []))
    for t in st.get("table_detail", []):
        title = t.get("table") or ""
        named.append(title)
        rows = [" ".join(c for c in row if c) for row in t.get("rows", [])] + \
               t.get("raw_lines", [])
        # A MATRIX or LEGEND assigns responsibility for a product -- A1-20's Site
        # Equipment Matrix is what tells us the bleachers, ticket booth and
        # scoreboard are Contractor-furnished and whose they are, so its rows name
        # the work. A discipline SCHEDULE lists that discipline's own equipment,
        # and its passing mention of a door or a ceiling names nothing.
        (named if is_responsibility_table(t) else mentioned).extend(rows)
    return "\n".join(named).lower(), "\n".join(mentioned).lower()


def cited_sheets(bodies, known):
    pat = re.compile(r"\b([A-Z]{1,2}\d{1,2}[-.]\d{1,2}|MG|GD|C\d)\b")
    return {pkg: sorted({h for h in pat.findall(body) if h in known})
            for pkg, (body, _) in bodies.items()}


def sheet_haystack(rec, structured):
    """Everything readable on the sheet: title, keynotes, notes, table rows."""
    parts = [rec["title"]]
    st = structured.get(rec["sheet"])
    if st:
        parts += list(st.get("keynotes", {}).values())
        parts += st.get("notes", [])
        for t in st.get("table_detail", []):
            for row in t.get("rows", []):
                parts.append(" ".join(c for c in row if c))
            parts += t.get("raw_lines", [])
    f = ROOT / "01-index" / "sheets" / f"{rec['sheet']}.layout.txt"
    if f.exists():
        parts.append(f.read_text(errors="ignore"))
    return "\n".join(parts).lower()


def main():
    corpus = json.loads((INDEX / "sheet-corpus.json").read_text())["sheets"]
    structured = {r["sheet"]: r for r in
                  json.loads((INDEX / "sheet-structured.json").read_text())["sheets"]}
    cat = json.loads((INDEX / "spec-section-catalog.json").read_text())
    sec_primary = {s["section"]: s["primary_package"] for s in cat["sections"]
                   if s.get("primary_package") and s["primary_package"] != "ALL PACKAGES"}

    bodies = scope_bodies()
    haystacks = {r["sheet"]: sheet_haystack(r, structured) for r in corpus}
    keynote_text = {r["sheet"]: structured_text(r, structured) for r in corpus}
    named_text = {k: v[0] for k, v in keynote_text.items()}
    nouns = title_nouns()
    # A product noun on most sheets identifies nothing; drop it on the same basis
    # as the scope-doc vocabulary.
    noun_df = Counter()
    for txt in named_text.values():
        noun_df.update({n for forms in nouns.values() for n in forms if n in txt})
    ubiquitous = {n for n, c in noun_df.items() if c > 0.25 * len(named_text)}
    terms, boilerplate = distinctive_terms(bodies, haystacks)
    known_sheets = set(haystacks)
    citations = cited_sheets(bodies, known_sheets)

    SEC = re.compile(r"\b(\d{2})\s?(\d{2})\s?(\d{2})(?:\.(\d{2}))?\b")

    recs, unassigned = [], []
    by_pkg = defaultdict(list)
    for r in corpus:
        hay = sheet_haystack(r, structured)
        evidence = defaultdict(dict)

        for pkg, sheets in citations.items():
            if r["sheet"] in sheets:
                evidence[pkg]["sheet_citation"] = (
                    f"{pkg}'s Scope of Work names sheet {r['sheet']} directly")

        for mm in SEC.finditer(hay.upper()):
            num = " ".join(mm.group(1, 2, 3)) + (f".{mm.group(4)}" if mm.group(4) else "")
            owner = sec_primary.get(num)
            if owner:
                evidence[owner].setdefault("spec_section", []).append(num)

        # A two-word trade phrase is worth far more than a single word. "branch
        # selector", "high jump", "concrete housekeeping" name the work; "heater"
        # or "column" appear in half the trades' vocabularies.
        scores = {}
        for pkg, tset in terms.items():
            hits = sorted({t for t in tset if t in hay})
            if hits:
                scores[pkg] = (sum(2 if " " in t else 1 for t in hits), hits)
        top = max((v[0] for v in scores.values()), default=0)
        for pkg, (score, hits) in scores.items():
            # Absolute floor, and a relative one: a package scoring far below the
            # best match on a sheet is matching incidental words, not the work.
            if score >= 4 and score >= 0.3 * top:
                evidence[pkg]["scope_terms"] = [t for t in hits if " " in t][:10] or hits[:10]
                evidence[pkg]["scope_term_count"] = len(hits)
                evidence[pkg]["scope_term_score"] = score

        named, mentioned = keynote_text[r["sheet"]]
        for pkg, forms in nouns.items():
            hit = sorted({n for n in forms if n in named} - ubiquitous)
            if hit:
                evidence[pkg]["product_named_on_sheet"] = hit[:6]
            else:
                soft = sorted({n for n in forms if n in mentioned} - ubiquitous)
                if soft:
                    evidence[pkg]["product_mentioned_in_a_schedule"] = soft[:6]

        # Weak net, only where nothing stronger landed.
        prefix = re.match(r"[A-Z]+", r["sheet"]).group(0)
        if not evidence:
            for pkg in (DISCIPLINE.get(prefix) or []):
                evidence[pkg]["discipline"] = (
                    f"No scope doc reached this sheet; assigned from the '{prefix}' "
                    f"discipline prefix alone. WEAK -- verify before drafting from it.")

        def strength(e):
            if "sheet_citation" in e:
                return "cited"
            sc = e.get("scope_term_score", 0)
            if "spec_section" in e and sc >= 6:
                return "strong"
            if "product_named_on_sheet" in e and (sc or "spec_section" in e):
                return "strong"
            if "spec_section" in e or sc >= 14:
                return "strong"
            if "product_named_on_sheet" in e:
                return "moderate"
            if "product_mentioned_in_a_schedule" in e:
                return "weak"
            if sc >= 6:
                return "moderate"
            if sc:
                return "weak"
            return "discipline_only"

        packages = {p: {"confidence": strength(e), **{k: v for k, v in e.items()}}
                    for p, e in evidence.items()}
        rec = {
            "sheet": r["sheet"], "title": r["title"], "revision": r["revision"],
            "source": r["source"], "page": r["page"],
            "packages": dict(sorted(packages.items(),
                                    key=lambda kv: (-kv[1].get("scope_term_score", 0), kv[0]))),
            "package_count": len(packages),
        }
        if prefix in ("G", "LS"):
            rec["applies_to_all_packages"] = True
            rec["note"] = ("General / life-safety sheet. Binds every package; not assigned "
                           "to a trade.")
        recs.append(rec)
        for p, v in packages.items():
            by_pkg[p].append((r["sheet"], v["confidence"]))
        if not packages and prefix not in ("G", "LS"):
            unassigned.append({"sheet": r["sheet"], "title": r["title"],
                               "chars": r["chars"], "prefix": prefix})

    no_sheets = sorted(set(SCOPE_FILE_TO_PACKAGE.values()) - set(by_pkg))

    out = {
        "_generated": "2026-08-06",
        "_method": ("Assignments derived from each package's Scope of Work narrative, not from "
                    "reading the drawings. Signals, strongest first: the scope doc naming the "
                    "sheet; a spec section on the sheet whose primary package is known; "
                    "distinctive scope-doc vocabulary found on the sheet; and, only for sheets "
                    "nothing else reached, the discipline prefix. Distinctive vocabulary is "
                    "computed by document frequency across the 33 scope docs, so shared "
                    "contract boilerplate cannot generate a match."),
        "_revision_policy": ("Sheets are read at their current revision. The seven reissued by "
                            "Addendum #1 are the addendum versions."),
        "_totals": {
            "sheets": len(recs),
            "at_addendum_revision": sum(1 for r in recs if r["revision"].startswith("ADDENDUM")),
            "general_sheets_binding_all": sum(1 for r in recs if r.get("applies_to_all_packages")),
            "sheets_with_no_package": len(unassigned),
            "packages_with_no_sheet": len(no_sheets),
            "assignments": sum(r["package_count"] for r in recs),
            "by_confidence": dict(Counter(
                v["confidence"] for r in recs for v in r["packages"].values())),
        },
        "sheets": recs,
        "sheets_by_package": {
            k: {"draft_from": sorted(sh for sh, c in v
                                     if c in ("cited", "strong", "moderate")),
                "leads_to_verify": sorted(sh for sh, c in v
                                          if c in ("weak", "discipline_only")),
                "_note": ("draft_from carries a scope-doc citation, a spec section, or "
                          "enough distinctive scope vocabulary to stand behind. "
                          "leads_to_verify matched on a single incidental term and must be "
                          "opened before anything is drafted from it.")}
            for k, v in sorted(by_pkg.items())},
        "_boilerplate_terms_excluded": {
            "_why": ("Terms distinctive across the scope docs but present on more than a "
                     "quarter of the sheets -- title-block and general-note language that "
                     "cannot indicate which package builds from a sheet."),
            "count": len(boilerplate),
            "terms": boilerplate[:120],
        },
        "sheets_with_no_package": unassigned,
        "packages_with_no_sheet": no_sheets,
    }
    (INDEX / "sheet-package-assignments.json").write_text(json.dumps(out, indent=2) + "\n")
    for k, v in out["_totals"].items():
        print(f"  {k:28} {v}")
    if unassigned:
        print("\nsheets no package reached:")
        for u in unassigned:
            print(f"    {u['sheet']:<10} {u['title'][:50]}")
    if no_sheets:
        print(f"\npackages with no sheet: {', '.join(no_sheets)}")


if __name__ == "__main__":
    main()
