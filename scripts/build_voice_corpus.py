#!/usr/bin/env python3
"""
Build the voice corpus: every line of Attachment A scope language someone
actually authored, separated from the template boilerplate it sits in.

A voice profile is only as good as the corpus under it, and there are two
separate corpus problems here.

The first is boilerplate. Most of an Attachment A is not written by anyone -- it
is the template's fixed contract prose, identical on every exhibit. Counting it
teaches nothing except that the template exists. So every line is tagged
`authored` or `boilerplate` and the statistics only ever run on the authored
half.

The second is authorship, and it is the one that decides whose voice this
profile actually describes. Every line carries an `author`:

  self    Written by this repo's PM. THE authority -- this is the voice the
          profile exists to capture. Read from 00-source-docs/voice-corpus/mine/.
  core    Written by someone else at CORE: an executed exhibit from another PM's
          job, or the example bullets inside a CORE template. Evidence of HOUSE
          style, which is a different thing from personal voice. Useful for
          settling what the company expects; not evidence of how the PM writes.
  claude  This project's generated drafts. Never defines a rule -- present only
          so drift is measurable rather than a matter of opinion.

Nothing in this repo as staged was authored by its PM, so a profile built from
it alone is a house profile wearing a personal profile's name. Where `self`
lines exist they outrank `core` on every authored-layer question; where they do
not, the profile must say so instead of quietly substituting someone else's
voice.

Drop exhibits into 00-source-docs/voice-corpus/, and put the ones the PM wrote
in the mine/ subfolder -- that subfolder is the whole authorship signal.

Usage:
  python3 scripts/build_voice_corpus.py            # build + print the report
  python3 scripts/build_voice_corpus.py --quiet    # build only

Writes:
  01-index/voice-corpus.jsonl        one record per line of scope language
  01-index/voice-corpus-stats.md     the measured report
"""

import argparse
import collections
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DROP = ROOT / "00-source-docs" / "voice-corpus"
MINE = DROP / "mine"          # exhibits this repo's PM wrote -- the authority
PROCESS = ROOT / "00-source-docs" / "05-supplemental" / "attachment-a-process"
TEMPLATE_DIR = ROOT / "00-source-docs" / "SUBCONTRACTOR FILES" / "0 - ATTACHMENT A - Scope of Work"
CONTENT = ROOT / "01-index" / "attachment-a-content"
OUT_JSONL = ROOT / "01-index" / "voice-corpus.jsonl"
OUT_STATS = ROOT / "01-index" / "voice-corpus-stats.md"

# Known reference exhibits that live outside the drop folder.
SEEDS = [PROCESS / "1.01 Final Attachment A Review Log PDF Example 2.23.26.pdf"]

P_RE = re.compile(r"<w:p(?: [^>]*)?>(?:(?!</w:p>).)*?</w:p>", re.S)
R_RE = re.compile(r"<w:r(?: [^>]*)?>(?:(?!</w:r>).)*?</w:r>", re.S)
# The space before [^>]* is load-bearing: "<w:t[^>]*>" also matches "<w:tabs>",
# and since the close tag is a literal "</w:t>" the match then ran on through
# the paragraph properties and dumped raw XML into the corpus as scope language.
# The other Word scripts in this repo already spell it this way.
T_RE = re.compile(r"<w:t(?: [^>]*)?>(.*?)</w:t>", re.S)

# Outline markers CORE's template uses: 1. / A. / i. / a.
MARKER = re.compile(
    r"^\s*(?:(?P<num>\d{1,2})\.|(?P<alpha>[A-Z])\.|"
    r"(?P<roman>[ivxl]{1,7})\.|(?P<lower>[a-h])\.)\s+(?P<body>.+)$"
)

# The same markers appearing mid-line. Word sets them at their own tab stop, so
# PyMuPDF sometimes returns a marker and the item that follows it on one line --
# which silently glued four separate exclusions into a single record and made
# the exclusion-length statistics meaningless. Split those back apart. Only
# markers followed by a capitalised word count, so "Section 07 9200 - Joint
# Sealants" and "ASI #01" survive intact.
MID_MARKER = re.compile(r"(?<=[\w.,)]) (?=(?:[A-Z]|[ivxl]{2,7}|[a-h])\.\s+[A-Z])")

# Lines that are page furniture rather than contract text.
FURNITURE = re.compile(
    r"^(page \d+ of \d+|example|attachment a|scope of work|"
    r"core project no|project name|phone:|email:|contact person:|"
    r"subcontractor:|supplier:|password:|invite to be sent|procore|"
    r"lump sum base bid|no bond included|www\.)", re.I
)

# Template placeholders -- highlighted, but carrying no authored prose.
PLACEHOLDER = re.compile(
    r"^(text\.?|none\.?|\?+|n/?a|company name|address|city, st, zip|"
    r"tbd|xx-xx-xxx|name of project)$", re.I
)

# The template's own fixed contract sentences. These appear verbatim on every
# exhibit, so they are boilerplate no matter which source they were read from.
BOILERPLATE_CUES = [
    "has accounted for, as part of this lump sum",
    "shall adhere to all",
    "can be downloaded from the following location",
    "must go to the procore software",
    "to go to the procore software",
    "shall perform the scope of work generally described as",
    "shall provide a complete turnkey",
    "shall provide a complete scope of work in accordance",
    "the following items are specifically excluded",
    "provide all labor, material, equipment, and services required to furnish",
    "provide all material, equipment, and services required to deliver",
    "provide all material, equipment, and services as required to furnish",
    "web-based software on this project",
    "foreman, at a minimum, shall attend",
    "pricing is based on tariff",
]

GROUP_HEADER_CUE = "provide all materials, labor, equipment, and supervision"


def norm(s):
    """Collapse whitespace and normalise the typography Word emits."""
    s = (s.replace("’", "'").replace("‘", "'")
          .replace("“", '"').replace("”", '"')
          .replace("–", "-").replace("—", "-")
          .replace("\xa0", " "))
    return re.sub(r"\s+", " ", s).strip()


def is_boilerplate(text):
    low = text.lower()
    return any(cue in low for cue in BOILERPLATE_CUES)


def classify(text, section):
    """What kind of line this is, for per-kind statistics."""
    if section == "exclusions":
        return "exclusion"
    if re.match(r"^(Section|Division)\s", text):
        return "spec_section"
    if GROUP_HEADER_CUE in text.lower():
        return "group_header"
    if section == "provisions":
        return "provision"
    return "scope_item"


# --------------------------------------------------------------------------
# PDF: an executed exhibit
# --------------------------------------------------------------------------

PAGE_FOOTER = re.compile(r"Page (\d+) of (\d+)")


def pdf_lines(path):
    """Body text of the Attachment A exhibit inside a Bluebeam review packet.

    Two things have to be filtered out or the corpus fills with prose nobody
    wrote as scope language:

    1. The 72pt red "Example" callouts laid over the reference exhibit. They
       extract as ordinary text, so spans are restricted to normal-size black
       body text.
    2. The rest of the packet. A FINAL packet is the exhibit plus a review
       cover sheet, a price build-up, the signed Bid Form and the descope
       notes -- seven documents, only one of which is the exhibit. Reading all
       fifteen pages put "CMU" and "DIV. 4" into the corpus off a pricing
       summary and would have produced an abbreviation rule that the exhibit
       body contradicts. The exhibit is located by its own "Page 1 of N"
       footer next to the ATTACHMENT A heading, and exactly those N pages are
       read.
    """
    try:
        import pymupdf
    except ImportError:
        print(f"  ! skipped {path.name} (pip install pymupdf to read it)", file=sys.stderr)
        return []

    with pymupdf.open(path) as doc:
        pages = []
        for page in doc:
            lines = []
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines", []):
                    txt = "".join(
                        s["text"] for s in line["spans"]
                        if s["size"] <= 14 and s["color"] == 0
                    )
                    if txt.strip():
                        lines.append(txt)
            pages.append(lines)

    start, span = None, None
    for i, lines in enumerate(pages):
        joined = " ".join(lines)
        m = PAGE_FOOTER.search(joined)
        if m and m.group(1) == "1" and "ATTACHMENT A" in joined.upper():
            start, span = i, int(m.group(2))
            break

    if start is None:                       # a bare exhibit, not a packet
        return [ln for lines in pages for ln in lines]

    print(f"  exhibit body: pages {start + 1}-{start + span} of {len(pages)}")
    return [ln for lines in pages[start:start + span] for ln in lines]


def parse_exhibit(lines, source_id, kind, author):
    """Reassemble wrapped lines into outline items and tag each one."""
    records, section, buf = [], "scope", []

    def flush():
        if not buf:
            return
        joined = norm(" ".join(buf))
        buf.clear()
        for text in MID_MARKER.split(joined):
            text = MARKER.sub(r"\g<body>", text.strip())
            if len(text) < 12 or FURNITURE.match(text):
                continue
            records.append({
                "source_id": source_id,
                "source_kind": kind,
                "author": author,
                "section": section,
                "kind": classify(text, section),
                "authored": not is_boilerplate(text),
                "text": text,
            })

    for raw in lines:
        line = norm(raw)
        if not line:
            continue
        head = line.lower().rstrip(":")
        if head in ("scope options", "construction documents", "exclusions",
                    "project specific provisions", "scope of work"):
            flush()
            section = {"exclusions": "exclusions",
                       "project specific provisions": "provisions",
                       "construction documents": "documents",
                       "scope options": "options"}.get(head, "scope")
            continue
        if FURNITURE.match(line):
            continue
        m = MARKER.match(line)
        if m:
            flush()
            buf.append(m.group("body"))
        else:
            buf.append(line)
    flush()
    return records


# --------------------------------------------------------------------------
# DOCX: a CORE template's authored example runs
# --------------------------------------------------------------------------

def docx_exhibit(path, source_id, author):
    """Every paragraph of a completed .docx exhibit, one record per paragraph.

    Two things make this a different job from both docx_highlighted and the PDF
    path.

    A template carries its authored examples in highlighted runs; a FINAL
    exhibit has had all highlighting stripped -- the process document requires
    it ("No; highlight, comments, strikeout, or other editing indicators"). So
    reading a finished exhibit for highlighted runs returns nothing at all.

    And the PDF path splits items on their printed outline markers, which a
    .docx does not have: Word's numbering lives in the paragraph's numPr
    properties, not in its text, so "i." and "A." are rendered at print time and
    never appear in a <w:t>. Routing a .docx through that splitter glued a whole
    exhibit into six records. In Word the paragraph *is* the item boundary, so
    that is what is used here.
    """
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")

    records, section = [], "scope"
    for para in P_RE.finditer(xml):
        text = norm("".join(T_RE.findall(para.group(0))))
        if not text:
            continue
        head = text.lower().rstrip(":")
        if head in ("scope options", "construction documents", "exclusions",
                    "project specific provisions", "scope of work"):
            section = {"exclusions": "exclusions",
                       "project specific provisions": "provisions",
                       "construction documents": "documents",
                       "scope options": "options"}.get(head, "scope")
            continue
        # A stray printed marker survives on some paragraphs; drop it.
        text = MARKER.sub(r"\g<body>", text)
        if len(text) < 12 or FURNITURE.match(text) or PLACEHOLDER.match(text):
            continue
        records.append({
            "source_id": source_id,
            "source_kind": "executed",
            "author": author,
            "section": section,
            "kind": classify(text, section),
            "authored": not is_boilerplate(text),
            "text": text,
        })
    return records


def docx_highlighted(path, source_id, author="core"):
    """Highlighted runs from a template -- where CORE writes its own examples."""
    with zipfile.ZipFile(path) as z:
        xml = z.read("word/document.xml").decode("utf-8")

    records, section = [], "scope"
    for para in P_RE.finditer(xml):
        p = para.group(0)
        full = norm("".join(T_RE.findall(p)))
        head = full.lower().rstrip(":")
        if head in ("scope options", "construction documents", "exclusions",
                    "project specific provisions"):
            section = {"exclusions": "exclusions",
                       "project specific provisions": "provisions",
                       "construction documents": "documents",
                       "scope options": "options"}.get(head, "scope")
            continue

        text = norm("".join(
            t for r in R_RE.finditer(p) if "<w:highlight" in r.group(0)
            for t in T_RE.findall(r.group(0))
        ))
        if not text or PLACEHOLDER.match(text) or len(text) < 25:
            continue
        if text.startswith("<") or "please delete this note" in text.lower():
            continue           # an instruction to the PM, not contract prose
        if FURNITURE.match(text):
            continue
        records.append({
            "source_id": source_id,
            "source_kind": "template",
            "author": author,
            "section": section,
            "kind": classify(text, section),
            "authored": not is_boilerplate(text),
            "text": text,
        })
    return records


# --------------------------------------------------------------------------
# JSON: this project's own drafts
# --------------------------------------------------------------------------

def draft_records(path):
    spec = json.loads(path.read_text())
    pkg = spec.get("_package", path.stem)
    out = []

    def add(text, kind, section):
        text = norm(text)
        if len(text) < 12:
            return
        out.append({
            "source_id": f"draft:{pkg}",
            "source_kind": "draft",
            "author": "claude",
            "section": section,
            "kind": kind,
            "authored": not is_boilerplate(text),
            "text": text,
        })

    for grp in spec.get("scope_groups", []):
        add(grp["header"], "group_header", "scope")
        for item in grp["items"]:
            add(item, "scope_item", "scope")
    for exc in spec.get("exclusions", []):
        add(exc, "exclusion", "exclusions")
    for sec in spec.get("spec_sections", []):
        add(sec, "spec_section", "documents")
    return out


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------

# Each probe is a rule candidate. A rule earns its place in the voice profile by
# showing up in the executed and template corpus, not by seeming reasonable.
PROBES = [
    ("opener: Supply and install",   r"^Supply and install\b"),
    ("opener: Provide and install",  r"^Provide and install\b"),
    ("opener: Furnish and install",  r"^(Furnish and install|Include furnishing and installing)\b"),
    ("opener: Provide",              r"^Provide (?!all materials, labor)"),
    ("opener: Coordinate",           r"^Coordinate\b"),
    ("opener: Subcontractor shall",  r"^Subcontractor shall\b"),
    ("responsibility: by others",    r"\bby others\b"),
    ("responsibility: Capitalized Subcontractor/trade",
                                     r"\b[A-Z][a-z]+ (?:S|s)ubcontractor\b"),
    ("coordination sentence",        r"(?:^|\. )Coordinat\w+ "),
    ("cite: per plans and specifications", r"per plans and specifications"),
    ("cite: specifically referencing", r"specifically referencing"),
    ("cite: as indicated/detailed",  r"\bas (indicated|detailed|shown|scheduled)\b"),
    ("cite: Section NN NNNN",        r"\bSection \d{2} \d{2,4}"),
    ("number: numeral in parens",    r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|"
                                     r"eleven|twelve|twenty[- ]?\w*|thirty[- ]?\w*|"
                                     r"[a-z]+teen)\s*\(\d+\)"),
    ("number: bare spelled-out",     r"\b(?:one|two|three|four|five|six|seven|eight|nine|ten|"
                                     r"twelve|twenty|twenty-four|thirty)\b(?!\s*\()"),
    ("number: inch/foot marks",      r"\d\s*[’”'\"]"),
    ("parenthetical: (i.e./e.g.",    r"\((?:i\.e\.|e\.g\.)"),
    ("hedge: including but not limited to", r"including,? but not limited to"),
    ("abbrev: CMU/MEP/AFF/OSHA",     r"\b(CMU|MEP|AFF|OSHA|FOB|SWPPP|ADA|IBC|NFHS|ANSI|ICC)\b"),
    ("spelled-out term: Concrete Masonry Unit", r"Concrete Masonry Unit"),
    ("spelled-out term: Mechanical, Electrical and Plumbing",
                                     r"Mechanical, Electrical and Plumbing"),
]


AUTHORS = (("self", "yours"), ("core", "CORE (others)"), ("claude", "drafts"))


def measure(records):
    """Report by AUTHOR, not by document type.

    Authorship is the axis that decides whose voice a rule describes. Grouping
    by executed/template/draft hid the thing that matters most: whether any of
    the corpus was written by the person the profile is supposed to sound like.
    """
    groups = collections.OrderedDict(
        (key, [r for r in records if r.get("author") == key and r["authored"]])
        for key, _ in AUTHORS
    )
    labels = dict(AUTHORS)

    lines = ["# Voice corpus — measured", "",
             "Authored lines only; template boilerplate is excluded from every count.",
             "Grouped by who wrote the line, since that is what decides whose voice a",
             "rule describes. Built by `scripts/build_voice_corpus.py`.", ""]

    if not groups["self"]:
        lines += [
            "> ⚠️ **No lines in this corpus were written by this repo's PM.**",
            "> Every rule below therefore describes CORE *house* style as practised by",
            "> other authors — not personal voice. Put the PM's own executed exhibits in",
            "> `00-source-docs/voice-corpus/mine/` and re-run; those lines become the",
            "> authority and the rules get re-derived against them.",
            "",
        ]

    lines.append("## Corpus size")
    lines.append("")
    lines.append("| author | authored lines | boilerplate lines | documents | document types |")
    lines.append("|---|---:|---:|---:|---|")
    for key, rows in groups.items():
        mine = [r for r in records if r.get("author") == key]
        boiler = sum(1 for r in mine if not r["authored"])
        docs = len({r["source_id"] for r in mine})
        kinds = ", ".join(sorted({r["source_kind"] for r in mine})) or "--"
        lines.append(f"| {labels[key]} | {len(rows)} | {boiler} | {docs} | {kinds} |")
    lines.append("")

    header = " | ".join(labels[k] for k, _ in AUTHORS)
    lines.append("## Probe hits (share of that author's authored lines)")
    lines.append("")
    lines.append(f"| probe | {header} |")
    lines.append("|---|---:|---:|---:|")
    for name, pat in PROBES:
        rx = re.compile(pat)
        cells = []
        for rows in groups.values():
            if not rows:
                cells.append("--")
                continue
            n = sum(1 for r in rows if rx.search(r["text"]))
            cells.append(f"{n} ({100*n/len(rows):.0f}%)")
        lines.append(f"| {name} | " + " | ".join(cells) + " |")
    lines.append("")

    # The author grouping is the headline, but it pools an executed exhibit with
    # a blank template, and those carry different weight -- executed prose
    # survived a Review Session, template prose is illustrative. The profile
    # cites specific buckets, so they stay separately checkable here.
    buckets = collections.OrderedDict()
    for key, label in AUTHORS:
        for kind in ("executed", "template", "draft"):
            rows = [r for r in records if r.get("author") == key
                    and r["source_kind"] == kind and r["authored"]]
            if rows:
                buckets[f"{labels[key]} / {kind}"] = rows

    if len(buckets) > 1:
        lines.append("## Probe hits by author and document type")
        lines.append("")
        lines.append("| probe | " + " | ".join(buckets) + " |")
        lines.append("|---" + "|---:" * len(buckets) + "|")
        for name, pat in PROBES:
            rx = re.compile(pat)
            cells = [f"{sum(1 for r in rows if rx.search(r['text']))} "
                     f"({100*sum(1 for r in rows if rx.search(r['text']))/len(rows):.0f}%)"
                     for rows in buckets.values()]
            lines.append(f"| {name} | " + " | ".join(cells) + " |")
        lines.append("")
        lines.append("Denominators: " +
                     ", ".join(f"{k} {len(v)}" for k, v in buckets.items()) + ".")
        lines.append("")

    scope = [r for r in records if r["authored"] and r["kind"] == "scope_item"]
    lines.append("## Scope-item shape")
    lines.append("")
    lines.append("| author | items | median words | median sentences |")
    lines.append("|---|---:|---:|---:|")
    for key in groups:
        rows = [r for r in scope if r.get("author") == key]
        if not rows:
            lines.append(f"| {labels[key]} | 0 | -- | -- |")
            continue
        words = sorted(len(r["text"].split()) for r in rows)
        sents = sorted(len(re.findall(r"[.;]\s+[A-Z]", r["text"])) + 1 for r in rows)
        lines.append(f"| {labels[key]} | {len(rows)} | {words[len(words)//2]} | "
                     f"{sents[len(sents)//2]} |")
    lines.append("")

    # Openers come from whoever the current authority is: the PM's own lines
    # once they exist, CORE's otherwise.
    authority = "self" if groups["self"] else "core"
    openers = collections.Counter(
        " ".join(r["text"].split()[:2]) for r in scope if r.get("author") == authority
    )
    lines.append(f"## Most common openers — {labels[authority]}")
    lines.append("")
    for phrase, n in openers.most_common(12):
        lines.append(f"- `{phrase}` — {n}")
    lines.append("")

    # Where the PM's practice and CORE's differ, that difference IS the personal
    # voice -- the whole reason authorship is tracked. Surfaced only once there
    # is something to compare.
    if groups["self"] and groups["core"]:
        lines.append("## Where yours diverges from CORE's other authors")
        lines.append("")
        lines.append("| probe | yours | CORE (others) | delta |")
        lines.append("|---|---:|---:|---:|")
        deltas = []
        for name, pat in PROBES:
            rx = re.compile(pat)
            a = sum(1 for r in groups["self"] if rx.search(r["text"])) / len(groups["self"])
            b = sum(1 for r in groups["core"] if rx.search(r["text"])) / len(groups["core"])
            deltas.append((abs(a - b), name, a, b))
        for gap, name, a, b in sorted(deltas, reverse=True)[:10]:
            if gap < 0.05:
                break
            lines.append(f"| {name} | {a:.0%} | {b:.0%} | {a-b:+.0%} |")
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    records = []

    # Executed exhibits. Anything under mine/ is the PM's own writing and
    # becomes the authority; everything else is another author at CORE.
    exhibits = [(p, "core") for p in SEEDS if p.exists()]
    if DROP.exists():
        exhibits += [(p, "core") for p in sorted(DROP.glob("*.pdf"))]
        exhibits += [(p, "core") for p in sorted(DROP.glob("*.docx"))]
    if MINE.exists():
        exhibits += [(p, "self") for p in sorted(MINE.glob("*.pdf"))]
        exhibits += [(p, "self") for p in sorted(MINE.glob("*.docx"))]

    for p, author in exhibits:
        if p.suffix.lower() == ".pdf":
            recs = parse_exhibit(pdf_lines(p), p.stem, "executed", author)
        else:
            recs = docx_exhibit(p, p.stem, author)
        records += recs
        print(f"executed[{author}]  {p.name}: {len(recs)} lines")

    # CORE's blank templates, read for the example bullets in their highlighted
    # runs. Always house style, never personal.
    docx = sorted(TEMPLATE_DIR.glob("*Attach A*.docx")) if TEMPLATE_DIR.exists() else []
    docx += sorted(PROCESS.glob("*Attach A*.docx")) if PROCESS.exists() else []
    for p in docx:
        recs = docx_highlighted(p, p.stem, "core")
        records += recs
        print(f"template[core]  {p.name}: {len(recs)} lines")

    for p in sorted(CONTENT.glob("*.json")):
        recs = draft_records(p)
        records += recs
        print(f"draft[claude]   {p.stem}: {len(recs)} lines")

    OUT_JSONL.write_text("".join(json.dumps(r) + "\n" for r in records))
    report = measure(records)
    OUT_STATS.write_text(report)
    print(f"\nwrote {OUT_JSONL.relative_to(ROOT)} ({len(records)} records)")
    print(f"wrote {OUT_STATS.relative_to(ROOT)}")
    if not args.quiet:
        print()
        print(report)


if __name__ == "__main__":
    main()
