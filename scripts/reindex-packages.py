#!/usr/bin/env python3
"""
Rebuild package-index.json with the Scope of Work narrative as primary authority.

The rejected index stored scope_of_work_doc as a filename and derived package
assignments from drawing titles. This build inverts that, per the document
authority hierarchy established at PM review 07.31.26:

  1. Addenda / Clarifications supersede everything they touch
  2. Scope of Work narrative decides WHICH package carries an item
  3. Specifications decide HOW work is executed
  4. Drawings show extent and location (weakest authority for assignment)
  Proposals are NOT an authority tier -- diagnostic only.

Scope content is PARSED VERBATIM from the narratives rather than summarized, so
nothing in the index is a paraphrase. Each package's own "Primary Specifications"
list is used instead of CSI-division guessing, and drawing references are taken
from the scope text itself.

Usage:  python3 scripts/reindex-packages.py
Writes: 01-index/package-index-v2.json
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXTRACTED = ROOT / "00-source-docs" / "02-trade-scopes-bidform" / "_extracted"
INDEX = ROOT / "01-index"
OUT = INDEX / "package-index-v2.json"

# Scope-doc filename number -> package_id (numbering drifts between lists)
NUM_TO_PACKAGE = {
    "002": "RFP-002", "008": "RFP-008", "016": "RFP-016", "021": "RFP-021",
    "022": "RFP-022", "023": "RFP-023", "030": "RFP-030", "031": "RFP-031",
    "033": "RFP-033", "045": "RFP-045", "060": "RFP-060", "094": "RFP-094",
    "098": "RFP-098", "099": "RFP-100", "103": "RFP-103", "109": "RFP-109",
    "007": "ITB-008", "018": "ITB-018", "019": "ITB-019", "040": "ITB-040",
    "044": "ITB-044", "054": "ITB-054", "056": "ITB-056", "062": "ITB-062",
    "066": "ITB-066", "067": "ITB-067", "071": "ITB-071", "072": "ITB-072",
    "074": "ITB-074", "077": "ITB-077", "078": "ITB-078", "085": "ITB-085",
    "089": "ITB-089",
}

# Section headings that mark boilerplate, not scope.
BOILERPLATE_HEADS = {
    "PRECEDENCE", "SCHEDULE", "REASONABLE INFERENCE", "EXISTING CONDITIONS",
    "CONSTRUCTION DOCUMENTS", "TRADE PARTNER VOLUNTARY ALTERNATES", "DISCLAIMER",
    "END OF SCOPE OF WORK",
}

SHEET_RE = re.compile(
    r"\b((?:[A-Z]{1,3}\d{1,2}[-.]\d{2})|(?:GD|MG|C\d)|(?:[A-Z]{1,2}\d\.\d{2}))\b"
)
SPEC_RE = re.compile(r"\bSection\s+(\d{2}(?:\s?\d{2}\s?\d{2}(?:\.\d+)?)?)\s*[–\-—]\s*([^\n]+)")
DIV_RE = re.compile(r"\bDivision\s+(\d{2})\s*[–\-—]\s*([^\n]+)")
ALT_RE = re.compile(r"^Alternate\s+([\d]{3}\.[\d]{2}(?:-[A-Z])?)\s*[–\-—]\s*\(?(ADD|DEDUCT)\)?\s*[–\-—]?\s*(.*)$", re.I)


def load_lines(p: Path):
    return [l.strip() for l in p.read_text().splitlines() if l.strip()]


def parse_doc(path: Path):
    lines = load_lines(path)
    out = {
        "primary_specifications": [],
        "primary_divisions": [],
        "related_specifications": [],
        "related_divisions": [],
        "scope_items": [],
        "coordination_clauses": [],
        "drawing_references": [],
        "alternates": [],
    }

    # Header: "PROPOSAL PACKAGE #023 Fencing & Gates"
    num, title = None, None
    for l in lines[:6]:
        m = re.search(r"(?:PROPOSAL\s+)?PACKAGE\s*#?\s*(\d{3})\s*(.*)", l, re.I)
        if m:
            num, title = m.group(1), m.group(2).strip()
            break

    mode = None
    for l in lines:
        head = l.upper().rstrip(":")
        if head.startswith("PRIMARY SPECIFICATION"):
            mode = "primary"; continue
        if head.startswith("RELATED SPECIFICATION"):
            mode = "related"; continue
        if head.startswith("ALTERNATES"):
            mode = "alternates"; continue
        if re.match(r"^Scope of Work\s*[–\-—]", l, re.I):
            mode = "scope"
            out["scope_items"].append(l)   # keep the lead-in, it names the trade
            continue
        if any(head.startswith(b) for b in BOILERPLATE_HEADS):
            mode = None; continue

        if mode in ("primary", "related"):
            ms, md = SPEC_RE.search(l), DIV_RE.search(l)
            if ms:
                raw = re.sub(r"\s+", " ", ms.group(1)).strip()
                if len(raw.replace(" ", "")) <= 2:
                    # "Section 32 - Exterior Improvements": division-level, mislabeled.
                    rec = {"division": raw, "title": ms.group(2).strip(),
                           "note": "scope doc writes this as 'Section %s'; it is a division-level "
                                   "reference, not a CSI section number" % raw}
                    dkey = "primary_divisions" if mode == "primary" else "related_divisions"
                    if rec not in out[dkey]:
                        out[dkey].append(rec)
                else:
                    rec = {"section": raw, "title": ms.group(2).strip()}
                    key = "primary_specifications" if mode == "primary" else "related_specifications"
                    if rec not in out[key]:
                        out[key].append(rec)
            elif md:
                rec = {"division": md.group(1), "title": md.group(2).strip()}
                dkey = "primary_divisions" if mode == "primary" else "related_divisions"
                if rec not in out[dkey]:
                    out[dkey].append(rec)
        elif mode == "scope":
            out["scope_items"].append(l)
            if re.search(r"coordinat", l, re.I):
                out["coordination_clauses"].append(l)
        elif mode == "alternates":
            m = ALT_RE.match(l)
            if m:
                out["alternates"].append({
                    "alternate_id": m.group(1),
                    "type": m.group(2).upper(),
                    "description": m.group(3).strip(),
                    "detail": "",
                })
            elif out["alternates"] and l and not l.upper().startswith("THE FOLLOWING"):
                out["alternates"][-1]["detail"] += (" " + l).strip()

    # Drawing sheets named anywhere in the scope narrative
    body = "\n".join(out["scope_items"])
    seen = []
    for m in SHEET_RE.finditer(body):
        s = m.group(1)
        if s not in seen:
            seen.append(s)
    out["drawing_references"] = seen
    return num, title, out


def main():
    superseded = {}
    smap = json.loads((INDEX / "addendum-supersession-map.json").read_text())
    for sh in smap["addendum_1"]["sheets_reissued"]:
        superseded[sh["sheet"]] = {
            "current_revision": "ADDENDUM #1 (05.06.26)",
            "revised_location": sh.get("revised_location"),
            "announced_in_addendum": sh.get("announced_in_addendum"),
        }

    # Vision-read sheet content from the base-bid pass. Reusable as EVIDENCE of what a
    # sheet contains, but NOT as package assignment -- those were made from drawings
    # rather than scope docs, which is what PM review rejected. Carried as candidates.
    vision = {}
    for tag in ("vol1", "vol2", "esdemo"):
        for e in json.loads((INDEX / f"drawing-vision-{tag}.json").read_text())["sheet_assignments"]:
            sn = e["sheet_number"].split()[0]
            vision.setdefault(sn, e)

    inventory = json.loads((INDEX / "proposal-inventory.json").read_text())
    awarded = json.loads((INDEX / "awarded-sub-mapping.json").read_text())

    def awarded_for(pid):
        def walk(o):
            if isinstance(o, dict):
                if pid in o and isinstance(o[pid], dict):
                    return o[pid]
                for v in o.values():
                    r = walk(v)
                    if r:
                        return r
            return None
        return walk(awarded)

    packages, problems = {}, []
    for f in sorted(EXTRACTED.glob("Scope of Work - *.txt")):
        m = re.search(r"Scope of Work - (\d{3})", f.name)
        if not m:
            problems.append(f"no number in filename: {f.name}")
            continue
        fnum = m.group(1)
        pid = NUM_TO_PACKAGE.get(fnum)
        if not pid:
            problems.append(f"filename number {fnum} maps to no package: {f.name}")
            continue

        num, title, parsed = parse_doc(f)
        if num and num != fnum:
            problems.append(f"{pid}: filename says {fnum}, document header says #{num}")

        # Tag every drawing reference with its current revision
        drawings = []
        for s in parsed["drawing_references"]:
            rec = {"sheet_number": s, "cited_by": "scope of work narrative"}
            if s in superseded:
                rec["revision"] = superseded[s]["current_revision"]
                rec["read_from"] = superseded[s]["revised_location"]
                rec["base_bid_version_superseded"] = True
            else:
                rec["revision"] = "BID DOCS (04.20.26)"
                rec["base_bid_version_superseded"] = False
            drawings.append(rec)

        # Candidate sheets: what the base-bid vision pass associated with this package.
        cited = {d["sheet_number"] for d in drawings}
        candidates = []
        for sn, e in vision.items():
            if pid in e.get("package_ids", []) and sn not in cited:
                rec = {
                    "sheet_number": sn,
                    "sheet_title": e.get("sheet_title"),
                    "vision_rationale": e.get("rationale"),
                    "vision_confidence": e.get("confidence"),
                    "status": "CANDIDATE -- not corroborated by the scope narrative",
                }
                if sn in superseded:
                    rec["revision"] = superseded[sn]["current_revision"]
                    rec["read_from"] = superseded[sn]["revised_location"]
                    rec["WARNING"] = ("Vision pass read the BASE BID sheet. This sheet was reissued by "
                                      "Addendum #1 and must be re-read at the current revision before use.")
                else:
                    rec["revision"] = "BID DOCS (04.20.26)"
                candidates.append(rec)

        inv = inventory["packages"].get(pid, {})
        packages[pid] = {
            "title": title,
            "source_list": "1% (RFP)" if pid.startswith("RFP") else "Non-1% (ITB)",
            "scope_of_work_doc": {
                "file": f"02-trade-scopes-bidform/{f.stem}.docx",
                "extracted_text": f"02-trade-scopes-bidform/_extracted/{f.name}",
                "document_header": f"PROPOSAL PACKAGE #{num} {title}" if num else None,
                "filename_number": fnum,
                "authority": "PRIMARY -- decides which package carries a given item",
            },
            "primary_specifications": parsed["primary_specifications"],
            "primary_divisions": parsed["primary_divisions"],
            "related_specifications": parsed["related_specifications"],
            "related_divisions": parsed["related_divisions"],
            "scope_items_verbatim": parsed["scope_items"],
            "coordination_clauses": parsed["coordination_clauses"],
            "drawing_sheets": drawings,
            "drawing_sheet_candidates": candidates,
            "alternates": parsed["alternates"],
            "proposals": {
                "bidder_count": inv.get("bidder_count", 0),
                "bidders": inv.get("bidders", []),
                "files": inv.get("proposals", []),
                "supporting_docs": inv.get("supporting_docs", []),
                "authority": "NOT an authority tier -- diagnostic only. Never overrides contract "
                             "documents. Ignore boilerplate general exclusions. Contradictions are "
                             "flagged for PM, never silently adopted.",
            },
            "awarded_sub": awarded_for(pid),
        }

    idx = {
        "_generated": "2026-07-31",
        "_supersedes": "01-index/package-index.json (REJECTED at PM review 07.31.26)",
        "_authority_hierarchy": [
            "1. Addenda & Clarifications supersede everything they touch",
            "2. Scope of Work narrative decides WHICH package carries an item",
            "3. Specifications decide HOW the work is executed",
            "4. Drawings show extent and location (weakest authority for assignment)",
            "Proposals are NOT in the hierarchy -- diagnostic only",
        ],
        "_method": (
            "Scope content is parsed VERBATIM from the narratives, never paraphrased. Spec "
            "citations come from each package's own 'Primary Specifications' list rather than "
            "CSI-division inference. Every drawing citation carries the revision actually "
            "governing, resolved through addendum-supersession-map.json."
        ),
        "_totals": {},
        "packages": packages,
        "_parse_problems": problems,
    }
    idx["_totals"] = {
        "packages": len(packages),
        "scope_items_captured": sum(len(p["scope_items_verbatim"]) for p in packages.values()),
        "primary_spec_citations": sum(len(p["primary_specifications"]) for p in packages.values()),
        "primary_division_citations": sum(len(p["primary_divisions"]) for p in packages.values()),
        "alternates": sum(len(p["alternates"]) for p in packages.values()),
        "coordination_clauses": sum(len(p["coordination_clauses"]) for p in packages.values()),
        "drawing_citations": sum(len(p["drawing_sheets"]) for p in packages.values()),
        "drawing_candidates": sum(len(p["drawing_sheet_candidates"]) for p in packages.values()),
        "candidates_needing_reread_at_current_revision": sum(
            1 for p in packages.values() for c in p["drawing_sheet_candidates"] if "WARNING" in c),
    }
    OUT.write_text(json.dumps(idx, indent=2) + "\n")

    print(f"packages:              {idx['_totals']['packages']}")
    print(f"verbatim scope items:  {idx['_totals']['scope_items_captured']}")
    print(f"primary spec cites:    {idx['_totals']['primary_spec_citations']}")
    print(f"primary div cites:     {idx['_totals']['primary_division_citations']}")
    print(f"alternates:            {idx['_totals']['alternates']}")
    print(f"coordination clauses:  {idx['_totals']['coordination_clauses']}")
    print(f"drawing citations:     {idx['_totals']['drawing_citations']}")
    print(f"parse problems:        {len(problems)}")
    for p in problems:
        print(f"   ! {p}")
    print(f"\n-> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
