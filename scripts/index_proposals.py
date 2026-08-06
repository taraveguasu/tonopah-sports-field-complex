#!/usr/bin/env python3
"""
Index the CONTENT of every subcontractor proposal, descope, homework response and
scope-review agenda.

The previous inventory recorded a filename and status flags parsed from that
filename. It never opened a proposal. This reads the extracted text of all 221
documents and pulls out what the bidders actually wrote.

Per PM direction:
  - Every bidder informs the scope, not just the awarded sub. A losing bidder's
    clarification often names the thing the drawings left ambiguous.
  - Descopes and homework live in different folders under different names than
    their base proposal, so they are matched by FIRM, not by filename.
  - Document date governs. The latest revision is current; earlier ones are
    retained as history. Undated documents are flagged, never guessed at.
  - Boilerplate general exclusions are noise; scope-specific ones are signal.

Usage:  python3 scripts/index_proposals.py
Writes: 01-index/proposal-content.json
"""

import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / "01-index" / "document-text" / "SUBCONTRACTOR FILES"
INDEX = ROOT / "01-index"

NUM_TO_PACKAGE = {
    "002": "RFP-002", "008": "RFP-008", "016": "RFP-016", "021": "RFP-021",
    "022": "RFP-022", "023": "RFP-023", "030": "RFP-030", "031": "RFP-031",
    "033": "RFP-033", "045": "RFP-045", "061": "RFP-060", "094": "RFP-094",
    "098": "RFP-098", "100": "RFP-100", "103": "RFP-103", "109": "RFP-109",
    "007": "ITB-008", "018": "ITB-018", "019": "ITB-019", "040": "ITB-040",
    "044": "ITB-044", "054": "ITB-054", "056": "ITB-056", "062": "ITB-062",
    "066": "ITB-066", "067": "ITB-067", "071": "ITB-071", "072": "ITB-072",
    "074": "ITB-074", "077": "ITB-077", "078": "ITB-078", "085": "ITB-085",
    "089": "ITB-089", "102": "RFP-100",
    # Sealed concrete carries no bid-package number of its own. PM ruling 08.04.26
    # moved the Resinous/Epoxy locations to Sealed Concrete under ITB-067.
    "065": "ITB-067",
}

# Trade numbers that appear on proposals but match no bid package. These are real
# bid scope with nowhere to land, not filing errors — they need a PM decision on
# which subcontract carries them.
UNASSIGNED_TRADES = {"070": "Final Cleaning"}

# Section headings a subcontractor's proposal uses for scope language.
SECTION_HEADS = [
    ("inclusions", r"^\s*(?:INCLUSIONS?|INCLUDED|INCLUDES|SCOPE INCLUDED|WE INCLUDE|"
                   r"SCOPE OF WORK|THIS (?:SYSTEM|PROPOSAL|QUOTE) INCLUDES?)\b.{0,40}$"),
    ("exclusions", r"^\s*(?:EXCLUSIONS?|EXCLUDED|EXCLUDES|NOT INCLUDED|WE EXCLUDE)\b.{0,40}$"),
    ("clarifications", r"^\s*(?:CLARIFICATIONS?|QUALIFICATIONS?|ASSUMPTIONS?|"
                       r"PROPOSAL NOTES?|(?:CLARIFICATIONS?|QUALIFICATIONS?) (?:&|AND) "
                       r"EXCLUSIONS?)\b.{0,40}$"),
    ("alternates", r"^\s*(?:ALTERNATES?|ALTERNATE LISTING|VOLUNTARY ALTERNATES?)\b.{0,40}$"),
    ("notes", r"^\s*(?:NOTES?|GENERAL NOTES?)\s*:?\s*$"),
]

# Scope statements that carry their own verb and need no heading above them.
# SI Legacy writes "Excludes Any Metal Flashing, Underslab Vapor Barrier..." as a
# free-standing bullet; heading-scoped harvesting saw a 17,000-character proposal
# and captured nothing from it.
STANDALONE = [
    ("exclusions", re.compile(
        r"^\s*[-•*]?\s*\**\s*(?:excludes?|excluding|does not include|not included)\b\s+\S", re.I)),
    ("inclusions", re.compile(
        r"^\s*[-•*]?\s*\**\s*(?:includes?|including|furnish(?:\s*(?:&|and)\s*install)?|"
        r"(?:provide|supply)\s*(?:&|and)\s*install)\b\s+\S", re.I)),
]
STOP = re.compile(r"^\s*(?:[A-Z][A-Z &/'\-]{5,}|PAGE \d|={3,}|===== PAGE)\s*:?\s*$")

INLINE_HEAD = re.compile(
    r"^\s*(EXCLUSIONS?|INCLUSIONS?|CLARIFICATIONS?|QUALIFICATIONS?|ALTERNATES?)\s*:\s*(\S.{5,})$",
    re.I)
INLINE_NAMES = {"exclusion": "exclusions", "inclusion": "inclusions",
                "clarification": "clarifications", "qualification": "clarifications",
                "alternate": "alternates"}

# Artifacts of the PDF and of CORE's blank proposal form, not subcontractor text.
# The form carries its own CLARIFICATIONS heading above empty fill-in lines, which
# would otherwise be harvested as if a bidder had written them.
JUNK = re.compile(
    r"^\s*(?:=====\s*PAGE|\s*Page \d+ of \d+|_{4,}|\.{4,}|"
    r"(?:No\.|Date|Name|Title|Signature|Firm|Address|Phone|Email|By)\s*[:.]?\s*_{2,}|"
    r"\$?\s*_{2,}|\(?\s*\)?\s*$)", re.I)
FORM_FIELD = re.compile(r"_{3,}")

# Boilerplate exclusions carry no scope signal. PM: ignore the general ones.
BOILERPLATE = re.compile(
    r"^\s*(?:permits?|bonds?|sales tax|taxes?|testing|inspections?|special inspection|"
    r"engineering|surveying|layout by others|temporary (?:power|water|heat|facilities|toilets?)|"
    r"overtime|premium time|winter|dewatering|builder'?s risk|insurance|"
    r"as-?built|record drawings?|warranty beyond|liquidated damages|"
    r"trash|dumpsters?|clean ?up|final clean|scaffolding|barricades?|traffic control)\b",
    re.I)

DATE_PATTERNS = [
    (re.compile(r"Submitted\s+([A-Z][a-z]+ \d{1,2}, \d{4})"), "%B %d, %Y"),
    (re.compile(r"\b([A-Z][a-z]+ \d{1,2}, \d{4})\b"), "%B %d, %Y"),
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b"), "%m/%d/%Y"),
    (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2})\b"), "%m/%d/%y"),
]
# Price, most authoritative first. The Building Connected header is the number the
# bidder actually transmitted; the letter's own base-bid line is next. Both are the
# BIDDER's statement of its price, which is what a tabulation is supposed to record
# and what must be reconciled against it.
PRICE_PATTERNS = [
    ("building_connected_header", re.compile(r"Sent proposal:\s*\$\s*([\d,]+(?:\.\d\d)?)")),
    ("base_bid_line", re.compile(
        r"(?:Base\s*Bid(?:\s*Proposal)?|Total\s*Base\s*Bid|Bid\s*Proposal)\s*"
        r"[-–—:]?\s*\$\s*([\d,]+(?:\.\d\d)?)", re.I)),
]
REV = re.compile(r"\bR(\d)\b")


def price_of(text):
    for src, rx in PRICE_PATTERNS:
        m = rx.search(text)
        if m:
            try:
                return round(float(m.group(1).replace(",", ""))), src
            except ValueError:
                continue
    return None, None


def doc_date(text):
    """Earliest confident date wins — that is the document's own date, not a
    referenced one. Returns (iso, source_string) or (None, None)."""
    head = text[:4000]
    for rx, fmt in DATE_PATTERNS:
        m = rx.search(head)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt).date().isoformat(), m.group(1)
            except ValueError:
                continue
    return None, None


# Everything from the document-type marker to the end of the string goes. Removing
# only the marker leaves the tail behind: "TAB  Homework Response Additional Info"
# becomes "TAB Additional Info", whose key can never match TAB Contractors.
DOCTYPE_WORDS = re.compile(
    r"\s*(?:R\d\b|scope review meeting agenda|homework|homeowork|descope|"
    r"\(|ALT\b|additional info).*", re.I)

# Field labels on a blank agenda template. "Subcontractor:" followed by nothing
# must not silently capture the next label down the form.
FORM_LABEL = re.compile(r"^(?:Scopes?|Project|Date|Attendees|Print Name|Company|Role)\s*:?\s*$", re.I)


def firm_of(text, fallback):
    """Firm name, in order of reliability.

    Scope-review agendas and homework responses state the firm outright on their
    first line; that beats anything inferred. Otherwise take the Building Connected
    header. The filename is last resort, with the document-type words stripped —
    otherwise "Bombard  Scope Review Meeting Agenda" normalises to a key that can
    never match Bombard Mechanical's proposal.

    The colon must be followed by spaces or tabs, never \\s — on Tahoe Fence's
    unfilled agenda \\s* crosses the newline and captures the next label, giving
    the firm name "Scopes:".
    """
    m = re.search(r"^[ \t]*Subcontractor[ \t]*:[ \t]*([^\n]{3,70})", text, re.M | re.I)
    if m and not FORM_LABEL.match(m.group(1).strip()):
        return m.group(1).strip()
    m = re.search(r"Sent proposal:.*?\n(?:Submitted[^\n]*\n)?([^\n]{3,60})", text)
    if m:
        cand = m.group(1).strip()
        if not re.match(r"^\$|^\d", cand):
            return cand
    return DOCTYPE_WORDS.sub("", fallback).strip() or fallback


# Trade words are not identity. Matching on them pairs "Tahoe Fence Co." with
# "Golden Bay Fence Plus Iron Works" and "U.S. Mechanical" with "Bombard Mechanical".
TRADE_WORDS = {
    "concrete", "masonry", "mechanical", "electric", "electrical", "plumbing",
    "heating", "fence", "fencing", "steel", "roofing", "landscape", "landscaping",
    "turf", "glass", "paint", "painting", "insulation", "acoustics", "specialties",
    "builders", "building", "products", "solutions", "industries", "sports",
    "demolition", "excavating", "supply", "install", "installations", "west",
    "nevada", "vegas", "southern", "national", "american",
}
LEGAL_WORDS = re.compile(
    r"\b(inc|llc|l\.l\.c|co|corp|corporation|company|group|enterprises?|"
    r"construction|contracting|contractors?|systems?|services?|the|dba|d\.b\.a)\b", re.I)


def firm_tokens(s):
    """Identifying words in a company name, for order-independent matching.

    Substring matching fails on reordered names: the tab writes "California
    Bleachers (Nata Construction)" and the proposal writes "Nata Construction, Inc.
    DBA California Bleachers". Neither normalises to a substring of the other, but
    they share the tokens that actually identify the firm.
    """
    s = LEGAL_WORDS.sub(" ", s)
    return {t for t in re.findall(r"[a-z0-9]+", s.lower())
            if len(t) > 2 and t not in TRADE_WORDS}


def distinctive_tokens(name, peers):
    """Tokens of `name` that no other firm bidding the same package also uses.

    Even after trade words are removed, a token shared with a competitor cannot
    decide between them. Only a token unique within the package identifies a firm.
    """
    mine = firm_tokens(name)
    shared = set()
    for p in peers:
        if p != name:
            shared |= firm_tokens(p)
    return mine - shared


def firms_match(a, b, peers=()):
    ka, kb = norm_firm(a), norm_firm(b)
    if ka and kb and (ka == kb or ka in kb or kb in ka):
        return True
    da = distinctive_tokens(a, peers) if peers else firm_tokens(a)
    return bool(da and firm_tokens(b) & da)


def norm_firm(s):
    s = re.sub(r"\b(inc|llc|l\.l\.c|co|corp|corporation|company|group|enterprises?|"
               r"construction|contracting|contractors?|systems?|services?|the)\b", "", s, flags=re.I)
    return re.sub(r"[^a-z0-9]", "", s.lower())


CORE_FORM_PAGE = re.compile(r"Subcontractor Proposal Form|SUBCONTRACTOR PROPOSAL\s*\(.BID.\)\s*FORM", re.I)


def strip_core_form(text):
    """Drop CORE's blank proposal-form pages.

    Every 1% submittal bundles CORE's 4-page form ahead of the bidder's own
    proposal. The form carries its own CLARIFICATIONS and NAMING OF LOWER TIER
    SUBCONTRACTORS headings above empty fields, so harvesting it attributes CORE's
    template language to the subcontractor. Only the bidder's own pages are scope.
    """
    pages = re.split(r"(?m)^===== PAGE \d+ =====$", text)
    return "\n".join(pg for pg in pages if not CORE_FORM_PAGE.search(pg))


def sections_of(text):
    """Pull bullet items under each scope-language heading."""
    lines = strip_core_form(text).splitlines()
    out = defaultdict(list)
    cur, count = None, 0
    for ln in lines:
        s = ln.strip()
        if not s:
            continue
        hit = None
        for name, rx in SECTION_HEADS:
            if re.match(rx, s, re.I):
                hit = name
                break
        if hit:
            cur, count = hit, 0
            continue
        # Inline heading: "EXCLUSIONS:  Backing, Caulking, Fillers, ...". Henri's
        # ITB-074 quote puts its only exclusions on the heading line itself, which
        # the heading-only patterns above skip because the line runs past them.
        m = INLINE_HEAD.match(s)
        if m:
            name = INLINE_NAMES[m.group(1).lower().rstrip("s")]
            cur, count = name, 1
            out[name].append(m.group(2).strip())
            continue
        if cur:
            if STOP.match(s) and count > 0:
                cur = None
                continue
            if JUNK.match(s) or FORM_FIELD.search(s):
                continue
            # A word-count floor of three was rejecting the shortest and most
            # consequential exclusions on the job: Sahara's "Over excavation",
            # "Multiple mobilizations", "Water proofing" and "De watering" are all
            # two words. Accept two words, or one substantial word ("Dewatering"),
            # and let BOILERPLATE decide what is generic. Form noise is already
            # removed by JUNK, FORM_FIELD and STOP above.
            words = re.findall(r"[A-Za-z]{2,}", s)
            if not (len(words) >= 2 or (words and len(words[0]) >= 6)):
                continue
            if 3 < len(s) < 300:
                # The line's own verb outranks the heading above it. SI Legacy
                # groups its work under product subheadings (Caulking, Rubber Base,
                # Sealed Concrete) that never reset the section, so heading state
                # drifts and "Furnish & Install Sika HY 100 Caulking" — plainly an
                # inclusion — files itself under Exclusions.
                label = next((n for n, rx in STANDALONE if rx.match(s)), cur)
                out[label].append(s)
                count += 1
            if count > 60:
                cur = None

    # Second pass, heading-independent. A line that states its own inclusion or
    # exclusion is scope wherever it sits on the page.
    seen = {v.lower() for vs in out.values() for v in vs}
    for ln in lines:
        s = ln.strip()
        if not (3 < len(s) < 300) or s.lower() in seen:
            continue
        if JUNK.match(s) or FORM_FIELD.search(s):
            continue
        for name, rx in STANDALONE:
            if rx.match(s):
                out[name].append(s)
                seen.add(s.lower())
                break
    return {k: v for k, v in out.items() if v}


# Priced add/deduct/alternate lines. On TAB's letter these sit under "Price
# Includes:" rather than any Alternates heading, so heading-scoped harvesting
# misses them entirely -- and they are precisely the scope-shifting items buyout
# has to see ("Deduct — Delete trench drain for the bid - $125,000.00").
LINE_ITEM = re.compile(
    r"^\s*(?:ADD|ADDS?|DEDUCT|ALT(?:ERNATE)?|ALT\s*#?\s*\d+|VE|OPTION|CREDIT|"
    r"BASE\s*BID|UNIT\s*RATE)\b[^\n]{0,200}?"
    r"(?:\$\s*[\d,]+(?:\.\d\d)?|NO\s*BID|N/?A|TBD|INCLUDED)", re.I)


# An itemised quote prices scope by product group: an ALL-CAPS group heading, a
# few detail lines, then a delivery term and a price. Henri's ITB-074 quote is
# entirely in this form and yielded nothing to heading-scoped harvesting.
GROUP_HEAD = re.compile(r"^[A-Z][A-Z0-9 ,&/'\"\-\.]{4,60}$")
GROUP_PRICE = re.compile(
    r"^\s*(FURNISHED AND INSTALLED|FURNISHED ONLY|SUPPLY ONLY|INSTALLED ONLY)[^\n]*$", re.I)
DOLLARS = re.compile(r"^\s*\$\s*([\d,]+(?:\.\d\d)?)\s*$")
# Catalogue codes from the detail rows: OFCI-PT, KB310-SSRE, 5806X36.
PRODUCT_CODE = re.compile(r"[A-Z]{1,6}[-]?[A-Z0-9]{0,6}(?:[-X][A-Z0-9]{1,6})+|\d[A-Z0-9\-]+")


def priced_groups_of(text):
    """ALL-CAPS product groups that carry their own delivery term and price."""
    lines = [l.strip() for l in strip_core_form(text).splitlines()]
    out, head = [], None
    for i, s in enumerate(lines):
        if GROUP_HEAD.fullmatch(s) and not GROUP_PRICE.match(s):
            # Nearest heading above the price wins, but product codes in the detail
            # rows are shaped like headings too — without rejecting them "TOILET
            # ACCESSORIES" becomes "OFCI-PT". Taking the first heading instead is
            # not the fix: that picks up the document's own "PROPOSAL" banner.
            if not PRODUCT_CODE.fullmatch(s):
                head = s
            continue
        if head and GROUP_PRICE.match(s):
            amt = next((DOLLARS.match(lines[j]).group(1)
                        for j in range(i + 1, min(i + 4, len(lines)))
                        if DOLLARS.match(lines[j])), None)
            out.append(f"{head} — {s.strip()}" + (f" — ${amt}" if amt else ""))
            head = None
    return out[:40]


def line_items_of(text):
    """Priced alternates, adds and deducts anywhere in the document."""
    out, seen = [], set()
    for ln in strip_core_form(text).splitlines():
        s = ln.strip()
        if not (4 < len(s) < 220) or FORM_FIELD.search(s):
            continue
        if LINE_ITEM.match(s) and s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out[:40]


def classify(path):
    """Document type, from the folder first and the filename second.

    The folder is the stronger signal. "Elite Sports - Track Asphalt Info.pdf" and
    "Henderson ALT block Pricing.pdf" are both homework responses — they sit in the
    Homework Responses folder — but neither filename says so. Reading the name alone
    classified them as proposals, which then took the wrong side of the dash for the
    firm name and left them unmatched to any package.
    """
    n = path.name.lower()
    folder = str(path.parent).lower()
    if "cut sheets" in folder:
        return "cut_sheet"
    if "homework" in folder:
        return "homework_response"
    if "agenda" in n:
        return "scope_review_agenda"
    if "homework" in n or "homeowork" in n:
        return "homework_response"
    if "descope" in n:
        return "descope"
    return "proposal"


LEADING_NUMS = re.compile(r"^\s*((?:\d{3}\s*,\s*)*\d{3})\b")


def packages_of(name):
    m = LEADING_NUMS.match(name)
    if not m:
        return []
    return [NUM_TO_PACKAGE[n] for n in re.findall(r"\d{3}", m.group(1)) if n in NUM_TO_PACKAGE]


def unassigned_of(name):
    """Trade numbers on the proposal that map to no bid package."""
    m = LEADING_NUMS.match(name)
    if not m:
        return []
    return [n for n in re.findall(r"\d{3}", m.group(1)) if n in UNASSIGNED_TRADES]


# Firms whose descope/homework/agenda filenames cannot be resolved to their
# proposal by normalisation alone. Each verified by opening the document.
# "TAB" is the trap: in this folder it is TAB Contractors on RFP-008 (their
# homework letter reads "Re: Site Demo / Clearing, Earthwork, Paving, Wet
# Utilities"), NOT the Test-And-Balance scope on RFP-100.
FIRM_ALIASES = {
    "cgb": ["RFP-022"],                    # CG&B Enterprises
    "gti": ["RFP-016"],                    # GTI 1 Inc. = BrightView, per PM
    "calibleachers": ["RFP-094"],
    "elitesports": ["RFP-021"],
    "henderson": ["RFP-031"],
    "mh": ["RFP-060"],                     # M&H
    "quantumelectric": ["RFP-103"],
    "tab": ["RFP-008"],                    # TAB Contractors, verified by letter
    "wheelerseletric": ["RFP-103"],        # misspelling of Wheelers Electric
    "wheelerselectric": ["RFP-103"],
    "tahoefence": ["RFP-023"],
}

# Product cut sheets belong to the package that installs the product.
CUT_SHEET_PACKAGES = {
    "aco sport": ["RFP-030"],              # trench drain, PM-assigned to concrete
    "discuss cage": ["ITB-019"],
    "discus cage": ["ITB-019"],
    "pole vault": ["ITB-019"],
    "goal post": ["ITB-019", "RFP-030"],   # equipment ITB-019, footings RFP-030
}


# Documents that belong to the project rather than to any one package. These are
# supposed to be unmatched; separating them keeps the unmatched list meaningful.
PROJECT_LEVEL = re.compile(
    r"ATTACHMENT A - Scope of Work/|ATTACHMENT B - Gen Prov|Bid Tabulation Sheet/|"
    r"Bid RFIs/(?!RFI #1-2)|Homework Tracker", re.I)


BID_TAB = (ROOT / "01-index" / "document-text" / "SUBCONTRACTOR FILES" /
           "21.0 - Subcontractor Proposals" / "Bid Tabulation Sheet" /
           "NCSD THS Field & TES Demo - Bid Tab Sheet - (05.12.2026).xlsx.txt")


# The tab's trade headings, in sheet order, are the 16 1% packages. ITB packages
# are not tabulated at all, so a firm missing from the tab is only notable if its
# package is one of these.
TAB_TRADES = {
    "Abatement & Building Wrecking": "RFP-002",
    "Site Demo/Clearing, Salvage, Earthwork, Asphalt Pavement, & Wet Utilities": "RFP-008",
    "Landscaping & Irrigation": "RFP-016",
    "Running Track Surfacing": "RFP-021",
    "Synthetic Turf Sports Field": "RFP-022",
    "Fencing & Gates": "RFP-023",
    "Concrete": "RFP-030",
    "Masonry": "RFP-031",
    "Structural Steel & Ornamental Metals": "RFP-033",
    "Metal Roofing, Fascia & Soffit Panels": "RFP-045",
    "Framing, Drywall & Painting": "RFP-060",
    "Bleachers & Pressbox": "RFP-094",
    "Plumbing Systems": "RFP-098",
    "HVAC & Building Controls Systems": "RFP-100",
    "Electrical & Low Voltage Systems": "RFP-103",
    "Prefabricated Ticket Booth": "RFP-109",
}


def bid_tab_prices():
    """(package, firm_key) -> (firm as tabulated, price) from the 05.12.26 bid tab.

    The tabulation is a transcription, not a source. Reconciling it against each
    bidder's own submitted price is the only way to catch a transcription error,
    and on this project it catches one: the tab reverses NDX and TAB on RFP-008.

    Keyed by package as well as firm. The Monument Company bid five packages; a
    firm-only key collapses those to one row and reports four false mismatches.

    Only the first worksheet is this project. The workbook carries a second sheet
    from an unrelated job (a Phase 2 youth development complex), whose rows would
    otherwise be read in as Tonopah bids.
    """
    if not BID_TAB.exists():
        return {}
    out, trade, pkg = {}, None, None
    in_sheet = False
    for ln in BID_TAB.read_text(errors="ignore").splitlines():
        if ln.startswith("=== SHEET:"):
            in_sheet = "Bid Tab (" in ln
            continue
        if not in_sheet or not ln.startswith("\t"):
            continue
        vals = [c.strip() for c in ln.split("\t") if c.strip()]
        if not vals:
            continue
        if len(vals) == 1 and not ln.startswith("\t\t"):
            trade = vals[0]
            pkg = TAB_TRADES.get(trade)
            continue
        if pkg and len(vals) > 2 and re.fullmatch(r"[\d,]+(?:\.\d+)?", vals[-1].replace("$", "")):
            out[(pkg, vals[0])] = round(float(vals[-1].replace(",", "")))
    return out


def main():
    docs = []
    for f in sorted(TEXT.rglob("*.txt")):
        rel = str(f.relative_to(ROOT / "01-index" / "document-text"))
        text = f.read_text(errors="ignore")
        # Strip BOTH extensions: files are named "<original>.pdf.txt". Leaving the
        # ".pdf" on turns Bombard's key into "bombardpdf", which can never match
        # "bombardmechanical" from their proposal.
        stem = re.sub(r"\.(pdf|docx|xlsx|xlsm|xls)$", "", f.name[:-4], flags=re.I)
        kind = classify(f)
        pkgs = packages_of(stem)
        iso, raw = doc_date(text)
        sect = sections_of(text)

        excl = sect.get("exclusions", [])
        scope_excl = [e for e in excl if not BOILERPLATE.match(e)]

        price, price_src = price_of(text)
        line_items = line_items_of(text)
        groups = priced_groups_of(text)
        rv = REV.search(stem)

        # Which side of the dash holds the firm is decided by the filename's own
        # shape, not by document kind. A name that opens with a package number is
        # "<pkg> <trade> - <Firm>", so the firm follows the dash — that holds even
        # for "065 Sealed Concrete - SI Legacy (descope)", which is a descope. A
        # name that does not ("Elite Sports - Track Asphalt Info") leads with the
        # firm, and taking the part after the dash yields a subject line instead.
        if LEADING_NUMS.match(stem) and " - " in stem:
            fb = stem.split(" - ", 1)[1]
        else:
            fb = stem.split(" - ")[0]
        fb = re.sub(r"\(.*", "", fb).strip()
        firm = firm_of(text, fb)

        docs.append({
            "file": rel,
            "kind": kind,
            "packages": pkgs,
            "unassigned_trades": [f"{n} {UNASSIGNED_TRADES[n]}" for n in unassigned_of(stem)],
            "firm": firm,
            "firm_key": norm_firm(firm),
            "date": iso,
            "date_raw": raw,
            "date_missing": iso is None,
            "revision": int(rv.group(1)) if rv else None,
            "price": price,
            "price_source": price_src,
            "chars": len(text),
            "inclusions": sect.get("inclusions", []),
            "exclusions_all": excl,
            "exclusions_scope_specific": scope_excl,
            "clarifications": sect.get("clarifications", []),
            "alternates": sect.get("alternates", []),
            "priced_line_items": line_items,
            "priced_scope_groups": groups,
            "notes": sect.get("notes", []),
            "has_scope_language": bool(sect) or bool(line_items) or bool(groups),
        })

    # ---- link documents by firm, then order by date within each package ----
    by_pkg = defaultdict(list)
    for d in docs:
        for p in d["packages"]:
            by_pkg[p].append(d)

    # documents with no package number: attach by firm to packages that firm bid
    firm_pkgs = defaultdict(set)
    for d in docs:
        if d["packages"] and d["firm_key"]:
            firm_pkgs[d["firm_key"]].update(d["packages"])
    orphans = []
    for d in docs:
        if d["packages"]:
            continue
        hits = set()
        dk = d["firm_key"]
        # Aliases match on prefix, not equality. Normalisation does not converge:
        # the agenda says "GTI 1 Inc." (gti1) while the proposal says "GTI" (gti),
        # and "CG&B Enterprise Inc" keeps the singular that the plural strips.
        for a, ps in FIRM_ALIASES.items():
            if dk == a or dk.startswith(a):
                hits |= set(ps)
        low = d["file"].lower()
        for frag, ps in CUT_SHEET_PACKAGES.items():
            if frag in low:
                hits |= set(ps)
        for k, ps in firm_pkgs.items():
            if not k or not dk:
                continue
            # Short keys like "cgb" are real firms. Requiring exact equality for them
            # loses the agenda whose key is "cgbenterprise"; allowing bare substring
            # would let a 2-3 letter key collide with an unrelated company. Anchor
            # short keys to the start of the string instead.
            if len(k) <= 4 or len(dk) <= 4:
                if k == dk or dk.startswith(k) or k.startswith(dk):
                    hits |= ps
            elif k in dk or dk in k:
                hits |= ps
        if hits:
            d["packages_by_firm_match"] = sorted(hits)
            for p in hits:
                by_pkg[p].append(d)
        else:
            orphans.append(d)

    packages, price_moves = {}, []
    for p, ds in sorted(by_pkg.items()):
        ds_sorted = sorted(ds, key=lambda d: (d["date"] or "0000-00-00", d["revision"] or 0))

        # Supersession chain per firm: every document that firm filed on this
        # package, oldest first. The last dated one governs; anything undated is
        # called out rather than assumed to be either newest or oldest.
        chains = {}
        for d in ds_sorted:
            chains.setdefault(d["firm_key"], []).append(d)

        # Merge keys that are the same firm written two ways. On RFP-031 the
        # proposal and agenda key as "hendersonmasonry" while the ALT block pricing
        # keys as "henderson", splitting one bidder into two chains -- so "latest
        # date governs" runs on two half-chains and can report a stale document as
        # current. Within a single package, one key being a prefix of another is a
        # naming variant, not two firms.
        merged = {}
        for key in sorted(chains, key=len, reverse=True):
            target = next((m for m in merged
                           if m.startswith(key) or key.startswith(m)), None)
            if target:
                merged[target] += chains[key]
            else:
                merged[key] = list(chains[key])
        chains = {k: sorted(v, key=lambda d: (d["date"] or "0000-00-00", d["revision"] or 0))
                  for k, v in merged.items()}
        current = {}
        for key, chain in chains.items():
            dated = [c for c in chain if c["date"]]
            cur = dated[-1] if dated else None
            current[key] = {
                # Most complete form of the name in the chain, not whichever
                # document happened to be latest -- after merging, that would label
                # Henderson Masonry as plain "Henderson".
                "firm": max((c["firm"] for c in chain), key=len),
                "current_document": cur["file"] if cur else None,
                "current_date": cur["date"] if cur else None,
                "superseded": [c["file"] for c in dated[:-1]],
                "undated_not_sequenced": [c["file"] for c in chain if not c["date"]],
            }
            # A price that moves along the chain is the thing buyout has to catch:
            # the later document governs, so a number carried forward from the bid
            # tab may no longer be the number the sub is standing behind.
            priced = [c for c in dated if c["price"]]
            if len(priced) > 1 and len({c["price"] for c in priced}) > 1:
                price_moves.append({
                    "package": p,
                    "firm": max((c["firm"] for c in chain), key=len),
                    "sequence": [{"date": c["date"], "price": c["price"],
                                  "kind": c["kind"], "file": c["file"]} for c in priced],
                    "governing_price": priced[-1]["price"],
                    "governing_date": priced[-1]["date"],
                })

        packages[p] = {
            "document_count": len(ds),
            "firms": sorted({d["firm"] for d in ds}),
            "current_per_firm": current,
            "documents": [d["file"] for d in ds_sorted],
            "scope_language_docs": [d["file"] for d in ds if d["has_scope_language"]],
        }

    # ---- bundled proposals: one document doing duty for several packages ----
    # SI Legacy filed near-identical documents under 040, 065, 066 and 067; each
    # carries all four trades' scope. Sprinturf did the same across 016 and 022.
    # Drafting a package's Attachment A from a document that also describes three
    # other packages is how scope gets double-carried or dropped between them.
    bundled = []
    by_firm = defaultdict(list)
    for d in docs:
        if d["kind"] == "proposal" and d["packages"] and d["firm_key"]:
            by_firm[d["firm_key"]].append(d)
    for key, group in by_firm.items():
        pkgs_seen = {p for g in group for p in g["packages"]}
        if len(pkgs_seen) < 2 or len(group) < 2:
            continue
        pairs = []
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                if set(a["packages"]) == set(b["packages"]):
                    continue
                sa = {x.lower() for x in a["exclusions_all"] + a["inclusions"]}
                sb = {x.lower() for x in b["exclusions_all"] + b["inclusions"]}
                if not sa or not sb:
                    continue
                overlap = len(sa & sb) / min(len(sa), len(sb))
                if overlap >= 0.7:
                    pairs.append({
                        "packages": sorted(set(a["packages"]) | set(b["packages"])),
                        "overlap": round(overlap, 2),
                        "files": [a["file"], b["file"]],
                    })
        if pairs:
            bundled.append({
                "firm": group[0]["firm"],
                "packages_bid": sorted(pkgs_seen),
                "near_identical_pairs": pairs,
                "reading": ("This bidder submitted one bundled scope across several packages. "
                            "Each package's file also describes the others, so neither the "
                            "price nor the scope splits cleanly by package without a descope."),
            })

    # ---- reconcile each bidder's own stated price against the tabulation ----
    tab = bid_tab_prices()
    tab_mismatches, tab_unmatched_firms = [], []
    for d in docs:
        if d["kind"] != "proposal" or not d["price"] or not d["packages"]:
            continue
        pkg = d["packages"][0]
        if pkg not in TAB_TRADES.values():
            continue                      # ITB packages are not tabulated
        peers = [f for (p, f) in tab if p == pkg]
        hit = next(((f, v) for (p, f), v in tab.items()
                    if p == pkg and firms_match(f, d["firm"], peers)), None)
        if not hit:
            # The firm is absent from this package's tab row. Before calling it a
            # gap, look for the same firm and the same amount under another trade —
            # that is a bidder whose combined-scope number was tabulated once, so
            # this package's row never sees it.
            elsewhere = [{"tabulated_under": p, "tabulated_as": f, "price": v}
                         for (p, f), v in tab.items()
                         if abs(v - d["price"]) <= 1
                         and firms_match(f, d["firm"], [x for (q, x) in tab if q == p])]
            tab_unmatched_firms.append({
                "package": pkg, "firm": d["firm"], "file": d["file"],
                "same_price_under_other_trade": elsewhere or None,
                "reading": ("This bidder's price is tabulated under a different package, so "
                            "this package's row omits them and the other package's row carries "
                            "a number that is not comparable to its single-scope bidders."
                            if elsewhere else
                            "Bidder submitted on this package but appears on no tab row for it."),
            })
            continue
        tab_firm, tab_price = hit
        # Allow a dollar of rounding; the tab stores whole dollars.
        if abs(tab_price - d["price"]) > 1:
            swap = [f for (p, f), v in tab.items()
                    if p == pkg and abs(v - d["price"]) <= 1
                    and not firms_match(f, d["firm"], peers)]
            tab_mismatches.append({
                "package": pkg,
                "firm": d["firm"],
                "price_per_own_proposal": d["price"],
                "price_source": d["price_source"],
                "price_per_bid_tab": tab_price,
                "tabulated_as": tab_firm,
                "proposal_file": d["file"],
                "tab_row_carrying_this_price": swap or None,
                "reading": ("The tabulation appears to have swapped these two bidders' prices — "
                            "the amount on this proposal is tabulated against another firm on "
                            "the same package."
                            if swap else
                            "The tabulated price does not appear on the bidder's own proposal."),
            })

    out = {
        "_generated": "2026-08-04",
        "_purpose": ("Content of every proposal, descope, homework response and scope-review "
                     "agenda. Replaces the filename-only inventory."),
        "_rules": {
            "all_bidders": "Every bidder informs the scope, including losing and disqualified ones.",
            "matching": "Descopes and homework are matched to packages by FIRM, since they are "
                        "filed separately from the base proposal under different names.",
            "supersession": "Latest date, then highest revision, is current per firm. Earlier "
                            "documents are retained as history.",
            "undated": "Flagged via date_missing, never inferred from a filename.",
            "boilerplate": "General exclusions are separated from scope-specific ones; only the "
                           "latter carry signal.",
            "verb_over_heading": "A line stating its own inclusion or exclusion is classified by "
                                 "that verb, not by the heading above it. Bidders who organise by "
                                 "product subheading would otherwise have their scope mis-filed.",
            "line_items": "Priced alternates, adds and deducts are captured wherever they appear, "
                          "including outside any Alternates heading.",
            "tab_is_not_a_source": "The bid tabulation is a transcription. Each bidder's own "
                                   "stated price is reconciled against it; the proposal governs.",
            "bundled_bids": "A firm whose documents for different packages are near-identical "
                            "submitted one bundled scope. Neither price nor scope splits by "
                            "package without a descope.",
        },
        "_totals": {
            "documents": len(docs),
            "with_scope_language": sum(1 for d in docs if d["has_scope_language"]),
            "dated": sum(1 for d in docs if d["date"]),
            "undated": sum(1 for d in docs if d["date_missing"]),
            "inclusions": sum(len(d["inclusions"]) for d in docs),
            "exclusions_total": sum(len(d["exclusions_all"]) for d in docs),
            "exclusions_scope_specific": sum(len(d["exclusions_scope_specific"]) for d in docs),
            "clarifications": sum(len(d["clarifications"]) for d in docs),
            "priced_line_items": sum(len(d["priced_line_items"]) for d in docs),
            "priced_scope_groups": sum(len(d["priced_scope_groups"]) for d in docs),
            "packages_covered": len(packages),
            "unmatched_documents": len(orphans),
            "project_level_documents": sum(1 for d in orphans if PROJECT_LEVEL.search(d["file"])),
            "price_movements": len(price_moves),
            "unassigned_trade_documents": sum(1 for d in docs if d["unassigned_trades"]),
            "bid_tab_price_mismatches": len(tab_mismatches),
            "bundled_multi_package_bidders": len(bundled),
        },
        "_bundled_proposals": bundled,
        "_bid_tab_reconciliation": {
            "_note": ("Each bidder's own stated price checked against the 05.12.26 bid "
                      "tabulation. The tabulation is a transcription; the proposal governs."),
            "firms_not_found_on_tab": tab_unmatched_firms,
            "mismatches": tab_mismatches,
        },
        "packages": packages,
        "documents": docs,
        # Split the leftovers. A bid tab or an Attachment B template belongs to no
        # package by design; anything else in this list is an unresolved match.
        "_project_level": sorted(d["file"] for d in orphans if PROJECT_LEVEL.search(d["file"])),
        "_unmatched": sorted(d["file"] for d in orphans if not PROJECT_LEVEL.search(d["file"])),
        "_unassigned_trades": sorted(
            {f"{t} — {d['firm']} — {d['file']}" for d in docs for t in d["unassigned_trades"]}),
        "_price_movements": price_moves,
    }
    (INDEX / "proposal-content.json").write_text(json.dumps(out, indent=2) + "\n")
    for k, v in out["_totals"].items():
        print(f"  {k:28} {v:,}")


if __name__ == "__main__":
    main()
