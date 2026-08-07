#!/usr/bin/env python3
"""
Build a package's Attachment A by editing CORE's Word template in place.

The process document is explicit: "Only modify items that are highlighted."  So
this does not regenerate the document from scratch -- it opens the template's
XML, replaces the text inside HIGHLIGHTED runs, and leaves every other run
untouched byte for byte.  The contract language, the numbering definitions, the
styles and the unhighlighted boilerplate come out identical to the template.

Where a section needs more (or fewer) bullets than the template provides, the
template's own paragraph is cloned as the prototype so the new bullets inherit
its numbering level and formatting rather than being invented.

Two things this deliberately does NOT do:
  - Put a price breakout anywhere in the Attachment A. PM direction: the only
    place to break out pricing is the Bluebeam cover sheet. The exhibit carries
    one LUMP SUM. (SCOPE OPTIONS carry their own dollar figure because the
    template provides that field for them -- that is an option price, not a
    breakout of the lump sum.)
  - Cite a specification section absent from the Project Manual. PM ruling
    08.06.26 (D): the obligation goes in by TITLE instead.

Usage:  python3 scripts/build_attachment_a.py RFP-008
Writes: 02-drafts/<package_id>/<Subcontractor> Draft Att A.docx
"""

import json
import re
import shutil
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = (ROOT / "00-source-docs" / "05-supplemental" / "attachment-a-process" /
            "2601019 NV 002 Attach A Subcontract DS Template 050925.docx")
CONTENT = ROOT / "01-index" / "attachment-a-content"
OUT = ROOT / "02-drafts"

P_RE = re.compile(r'<w:p(?: [^>]*)?>(?:(?!</w:p>).)*?</w:p>', re.S)
R_RE = re.compile(r'<w:r(?: [^>]*)?>(?:(?!</w:r>).)*?</w:r>', re.S)
T_RE = re.compile(r'(<w:t(?: [^>]*)?>)(.*?)(</w:t>)', re.S)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


def para_text(p):
    return "".join(re.findall(r'<w:t[^>]*>(.*?)</w:t>', p, re.S))


def is_highlighted(run):
    return "<w:highlight" in run


def set_para_text(p, new):
    """Put `new` into the paragraph's highlighted runs, leaving the rest alone.

    `new` may be a string (all text into the first highlighted run, any further
    highlighted runs emptied) or a list of strings, one per highlighted run --
    which is what the address block needs, since "Address" and "City, ST, Zip"
    are two highlighted runs separated by a line break in one paragraph.

    Unhighlighted runs are never touched. That is what keeps "Phone:",
    "Contact Person:" and every contract sentence exactly as the template has
    them, which is the rule the process document states.
    """
    runs = list(R_RE.finditer(p))
    hi = [m for m in runs if is_highlighted(m.group(0))]
    if not hi:
        return p
    vals = list(new) if isinstance(new, (list, tuple)) else [new]

    def fill(run, text):
        seen = [0]

        def sub(mm):
            seen[0] += 1
            if seen[0] == 1:
                return f'<w:t xml:space="preserve">{esc(text)}</w:t>'
            return f"{mm.group(1)}{mm.group(3)}"       # blank the extras
        return T_RE.sub(sub, run)

    out, last, n = [], 0, 0
    for m in runs:
        out.append(p[last:m.start()])
        r = m.group(0)
        if is_highlighted(r):
            r = fill(r, vals[n] if n < len(vals) else "")
            n += 1
        out.append(r)
        last = m.end()
    out.append(p[last:])
    return "".join(out)


def clone(prototype, texts):
    """One paragraph per string, each a copy of the prototype's formatting."""
    return "".join(set_para_text(prototype, t) for t in texts)


def build(pkg):
    spec = json.loads((CONTENT / f"{pkg}.json").read_text())

    with zipfile.ZipFile(TEMPLATE) as z:
        parts = {n: z.read(n) for n in z.namelist()}
    xml = parts["word/document.xml"].decode("utf-8")

    paras = [m.group(0) for m in P_RE.finditer(xml)]
    idx = {i: p for i, p in enumerate(paras)}

    # Prototypes cloned for repeated content, taken from the template itself so
    # cloned bullets inherit real numbering levels rather than invented ones.
    proto_group = idx[29]      # ilvl=1 -- "A./B./C." scope group header
    proto_bullet = idx[30]     # ilvl=2 -- "i./ii./iii." bullet
    proto_section = idx[63]    # spec section line
    proto_directive = idx[82]  # Addendum/Clarification/RFI line
    proto_option = idx[51]     # SCOPE OPTIONS line with its own $ field
    proto_excl = idx[107]      # exclusion line

    repl = {}                                  # paragraph index -> new XML
    for i, t in spec["simple"].items():
        repl[int(i)] = set_para_text(idx[int(i)], t)

    # --- SCOPE OF WORK body: template paragraphs 29-43 ---------------------
    body = []
    for grp in spec["scope_groups"]:
        body.append(set_para_text(proto_group, grp["header"]))
        body.append(clone(proto_bullet, grp["items"]))
    repl[29] = "".join(body)
    for i in range(30, 44):
        repl[i] = ""                           # consumed by the block above

    # --- SCOPE OPTIONS ------------------------------------------------------
    if spec["scope_options"]:
        # Two highlighted runs on this line: the scope text, then the amount that
        # follows the template's own "for a total amount of $".
        opts = [set_para_text(proto_option, [o["scope"], o["amount"]])
                for o in spec["scope_options"]]
        repl[49] = ""                          # drop the "None." line
        repl[51] = "".join(opts)
    else:
        repl[51] = ""

    # --- CONSTRUCTION DOCUMENTS: spec sections ------------------------------
    repl[62] = ""                              # "None"
    repl[63] = clone(proto_section, spec["spec_sections"])
    repl[64] = ""

    # --- Directives ---------------------------------------------------------
    repl[78] = ""                              # "None."
    repl[80] = ""                              # BIM line (no BIM on this job)
    repl[82] = clone(proto_directive, spec["directives"])
    for i in (84, 86, 88, 90):
        repl[i] = ""

    # --- EXCLUSIONS ---------------------------------------------------------
    repl[107] = clone(proto_excl, spec["exclusions"])
    repl[108] = ""

    # Optional standard clauses the template highlights so they can be kept or cut
    for i, keep in spec["standard_clauses"].items():
        if not keep:
            repl[int(i)] = ""

    # --- reassemble ---------------------------------------------------------
    out, last = [], 0
    for i, m in enumerate(P_RE.finditer(xml)):
        out.append(xml[last:m.start()])
        out.append(repl.get(i, m.group(0)))
        last = m.end()
    out.append(xml[last:])
    new_xml = "".join(out)

    dest = OUT / pkg
    dest.mkdir(parents=True, exist_ok=True)
    f = dest / f"{spec['file_stem']} Draft Att A.docx"
    with zipfile.ZipFile(f, "w", zipfile.ZIP_DEFLATED) as z:
        for n, data in parts.items():
            z.writestr(n, new_xml.encode("utf-8") if n == "word/document.xml" else data)

    print(f"wrote {f.relative_to(ROOT)}")
    n_items = sum(len(g["items"]) for g in spec["scope_groups"])
    print(f"  scope groups {len(spec['scope_groups'])}, items {n_items}, "
          f"sections {len(spec['spec_sections'])}, "
          f"directives {len(spec['directives'])}, exclusions {len(spec['exclusions'])}")
    return f


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "RFP-008")
