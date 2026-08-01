#!/usr/bin/env python3
"""
Prove that every project document has actually been processed -- or say plainly
which ones have not.

Walks every file under 00-source-docs/ and checks whether it is referenced by any
index artifact in 01-index/. Files that are deliberately out of scope are
classified as such with a reason, so "unaccounted for" means exactly that and
nothing else.

Usage:  python3 scripts/audit-file-coverage.py
Writes: 01-index/file-coverage-audit.json
        01-index/file-coverage-audit.md
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs"
INDEX = ROOT / "01-index"

# Files that are derived artifacts we produced, not source documents to index.
DERIVED = [
    (re.compile(r"02-trade-scopes-bidform/_extracted/.*\.txt$"),
     "derived", "Plain-text extraction of a Scope of Work .docx, produced by scripts/extract-scope-docs.py"),
    (re.compile(r"04-specs-reports/spec-manual-split/.*\.pdf$"),
     "derived", "Per-division split of the Bid Specification Manual, produced from its bookmark outline"),
    (re.compile(r"04-specs-reports/spec-manual-split/_manifest\.json$"),
     "derived", "Manifest for the spec-manual split"),
]

# Source categories whose processing is proven by a specific artifact rather than
# by a literal path string appearing in an index file.
CATEGORY_RULES = [
    (re.compile(r"^03-drawings/.*\.pdf$"), "drawings",
     "Sheet-level catalog in drawing-sheet-catalog.json (91 sheets) plus vision reads"),
    (re.compile(r"^04-specs-reports/.*Specification Manual.*\.pdf$"), "spec_manual",
     "Split into 22 per-division PDFs under spec-manual-split/"),
    (re.compile(r"^02-trade-scopes-bidform/Scope of Work - .*\.docx$"), "scope_docs",
     "Extracted to _extracted/*.txt and parsed verbatim into package-index-v2.json"),
]


# Severity of an unprocessed file, judged by what it blocks. Ordered -- first match wins.
GAP_SEVERITY = [
    (re.compile(r"Subcontractor Proposal \(Bid\) Form", re.I), "HIGH",
     "Defines the bid line items and alternate structure every exhibit must mirror. "
     "package-index-v2.json currently has NO bid_form_line_items field -- the v1 index had one."),
    (re.compile(r"Geotech", re.I), "HIGH",
     "Scope narratives reference the Geotechnical Report 25 times (backfill, hard dig, caliche, "
     "compaction). Drives RFP-008 earthwork and RFP-030 foundations. Never opened."),
    (re.compile(r"Asbestos", re.I), "HIGH",
     "Defines the actual abatement scope for RFP-002. Never opened."),
    (re.compile(r"Cut Sheets/", re.I), "HIGH",
     "Product basis-of-design cut sheets tied to specific packages: ACO Sport trench drain "
     "(RFP-030), discus cage / pole vault / goal post (ITB-019, RFP-030 footings)."),
    (re.compile(r"ATTACHMENT [AB]", re.I), "HIGH",
     "The Attachment A and B templates -- the output format for Stage 7. Never opened."),
    (re.compile(r"Preliminary Construction Schedule|Logistics Plan", re.I), "HIGH",
     "Scope docs bind subs to these by reference ('multiple mobilizations per the Preliminary "
     "Construction Schedule and Logistics Plan'). Never opened."),
    (re.compile(r"Bid RFIs/", re.I), "MEDIUM",
     "RFI log may contain responses beyond the 25 carried in Clarification No. 1."),
    (re.compile(r"1% Subcontractor Listing|Bid Tab|Bid Summary|Bid Commitments", re.I), "MEDIUM",
     "Basis of award. Used to build awarded-sub-mapping.json but not re-verified in this pass."),
    (re.compile(r"GMP R2|Basis of Proposal|GMP_EOD|GMP-R2", re.I), "MEDIUM",
     "The negotiated GMP -- the money the exhibits must reconcile to."),
    (re.compile(r"01-rfp-itb/", re.I), "LOW",
     "PDF of the RFP notice / ITB. Same content extracted from the .docx equivalents in "
     "02-trade-scopes-bidform/_extracted/."),
    (re.compile(r"Subcontract Agreement|Insurance|Billing|Textura|Affidavit", re.I), "LOW",
     "Flow-down commercial terms. Belong to Attachment B, not the Attachment A scope exhibit."),
    (re.compile(r"1213PC - Bid Tab Sheet - 2-28-13", re.I), "LOW",
     "Dated 2013 -- appears to be a stale template carried into the folder, not this project."),
    (re.compile(r"GC's|GR's|BidLeveling|GMP Schedule", re.I), "LOW",
     "CORE-internal cost and schedule workbooks; not scope sources for subcontract exhibits."),
    (re.compile(r"Copy of .*GMP.*DRAFT", re.I), "LOW",
     "Superseded working draft of the GMP (05.26.26); GMP R2 (07.01.26) is current."),
    (re.compile(r"Table of Contents \(ADD 1\)", re.I), "LOW",
     "Addendum #1 spec table of contents; its substantive change (adding 08 71 00) is already "
     "captured in the supersession map."),
]


def classify_gap(rel):
    for rx, level, why in GAP_SEVERITY:
        if rx.search(rel):
            return level, why
    return "UNCLASSIFIED", "Not matched by any severity rule -- review manually."


# Artifacts that must NOT be counted as evidence of coverage.
#   package-index.json      -- v1, rejected at PM review 07.31.26. Crediting a file
#                              because the REJECTED index cited it proves nothing.
#   file-coverage-audit.json -- this script's own output. It lists every path in the
#                              project, so scanning it makes the audit validate itself
#                              and report a false all-clear on the second run.
REJECTED = {"package-index.json", "file-coverage-audit.json"}


def collect_referenced_paths():
    """Every source-relative path mentioned anywhere in the index artifacts."""
    refs = set()
    pat = re.compile(r"(?:0[0-9]-[a-z-]+|GMP|SUBCONTRACTOR FILES)/[^\"\\]+")
    for f in sorted(INDEX.glob("*.json")):
        if f.name in REJECTED:
            continue
        text = f.read_text()
        for m in pat.finditer(text):
            r = m.group(0).strip()
            # Citations often append a locator: "...pdf p.3", "...pdf (backup)".
            r = re.sub(r"\s+(?:p\.?\s*\d+|pp?\.\s*[\d-]+)$", "", r)
            refs.add(r)
            m2 = re.search(r"^(.*?\.(?:pdf|docx|xlsx|xlsm|xls|txt|json))\b", r, re.I)
            if m2:
                refs.add(m2.group(1))
    return refs


def main():
    files = sorted(
        p for p in SRC.rglob("*")
        if p.is_file() and p.name != ".gitkeep"
    )
    refs = collect_referenced_paths()
    # Index references by basename too -- some artifacts cite bare filenames.
    ref_basenames = {Path(r).name for r in refs}
    # Artifacts sometimes cite a bare filename (e.g. supersession map's
    # "narrative_file": "00 91 11 - Addendum #1 (ADD 1).pdf"). Credit those.
    bare = re.compile(r"\"([^\"/]+\.(?:pdf|docx|xlsx|xlsm|xls))\"", re.I)
    for f in sorted(INDEX.glob("*.json")):
        if f.name in REJECTED:
            continue
        ref_basenames.update(m.group(1) for m in bare.finditer(f.read_text()))

    rows, buckets = [], defaultdict(list)
    for p in files:
        rel = str(p.relative_to(SRC))
        status, category, reason = None, None, None

        for rx, cat, why in DERIVED:
            if rx.search(rel):
                status, category, reason = "derived_artifact", cat, why
                break

        if status is None:
            for rx, cat, why in CATEGORY_RULES:
                if rx.match(rel):
                    status, category, reason = "processed", cat, why
                    break

        if status is None:
            if rel in refs or p.name in ref_basenames:
                status, category = "processed", "referenced_by_index"
                reason = "Path or filename cited in an 01-index artifact"
            else:
                status, category = "NOT_PROCESSED", "unreferenced"
                reason = "No index artifact references this file"

        row = {"file": rel, "status": status, "category": category, "reason": reason}
        if status == "NOT_PROCESSED":
            row["severity"], row["blocks"] = classify_gap(rel)
        rows.append(row)
        buckets[status].append(rel)

    # Group the gaps by folder so the report is actionable rather than a flat list.
    gaps = defaultdict(list)
    for r in rows:
        if r["status"] == "NOT_PROCESSED":
            top = r["file"].split("/")[0]
            gaps[top].append(r["file"])

    by_sev = defaultdict(list)
    for r in rows:
        if r["status"] == "NOT_PROCESSED":
            by_sev[r["severity"]].append(r)

    audit = {
        "_generated": "2026-07-31",
        "_purpose": "Confirm every project document is processed and indexed, or name the ones that are not.",
        "_totals": {
            "files_total": len(rows),
            "processed": len(buckets["processed"]),
            "derived_artifacts": len(buckets["derived_artifact"]),
            "NOT_PROCESSED": len(buckets["NOT_PROCESSED"]),
        },
        "gaps_by_severity": {k: [{"file": x["file"], "blocks": x["blocks"]} for x in v]
                             for k, v in sorted(by_sev.items())},
        "gaps_by_folder": {k: sorted(v) for k, v in sorted(gaps.items())},
        "files": rows,
    }
    (INDEX / "file-coverage-audit.json").write_text(json.dumps(audit, indent=2) + "\n")

    # Markdown summary
    md = ["# File Coverage Audit\n",
          f"**{audit['_totals']['files_total']} files** under `00-source-docs/`.\n",
          "| Status | Count |", "|---|---|",
          f"| Processed / indexed | {audit['_totals']['processed']} |",
          f"| Derived artifacts (produced by this pipeline) | {audit['_totals']['derived_artifacts']} |",
          f"| **Not processed** | **{audit['_totals']['NOT_PROCESSED']}** |", ""]
    if gaps:
        md.append("## Unprocessed files by folder\n")
        for folder, items in sorted(gaps.items()):
            md.append(f"### `{folder}/` — {len(items)} file(s)\n")
            for i in items:
                md.append(f"- `{i}`")
            md.append("")
    else:
        md.append("No unprocessed files.\n")
    (INDEX / "file-coverage-audit.md").write_text("\n".join(md))

    print(f"files:            {audit['_totals']['files_total']}")
    print(f"processed:        {audit['_totals']['processed']}")
    print(f"derived:          {audit['_totals']['derived_artifacts']}")
    print(f"NOT PROCESSED:    {audit['_totals']['NOT_PROCESSED']}")
    for lvl in ("HIGH", "MEDIUM", "LOW", "UNCLASSIFIED"):
        if by_sev.get(lvl):
            print(f"   {lvl}: {len(by_sev[lvl])}")


if __name__ == "__main__":
    main()
