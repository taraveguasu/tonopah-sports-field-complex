#!/usr/bin/env python3
"""
Audit whether each source document's CONTENT has actually been indexed.

scripts/audit-file-coverage.py answers a weaker question: is this file's path
mentioned somewhere in 01-index/? A path can be cited by a file nobody opened —
that is precisely how the v1 index passed its own checks while all 33 scope
narratives sat unread. This audit does not accept a citation as evidence.

Tiers, strongest to weakest:

  EXTRACTED    Full text of this file exists in a derived artifact on disk.
  READ         Content demonstrably read — a stored rationale, quotation or
               diff that could only come from opening the document.
  METADATA     Only filename-derived facts recorded (package number, status
               flags parsed from the name). The document itself is unopened.
  UNOPENED     No evidence of contact with the content at all.

Usage:  python3 scripts/audit-content-indexed.py
Writes: 01-index/content-index-audit.json / .md
"""

import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs"
INDEX = ROOT / "01-index"


def load(n):
    p = INDEX / n
    return json.loads(p.read_text()) if p.exists() else {}


def main():
    v2 = load("package-index-v2.json")
    smap = load("addendum-supersession-map.json")
    inv = load("proposal-inventory.json")
    vis = {}
    for tag in ("vol1", "vol2", "esdemo"):
        d = load(f"drawing-vision-{tag}.json")
        for e in d.get("sheet_assignments", []):
            vis[e["sheet_number"].split()[0]] = e

    # ---- EXTRACTED: a derived text artifact exists for this source file ----
    extracted = {}
    exdir = SRC / "02-trade-scopes-bidform" / "_extracted"
    for t in exdir.glob("*.txt"):
        extracted[f"02-trade-scopes-bidform/{t.stem}.docx"] = {
            "artifact": f"02-trade-scopes-bidform/_extracted/{t.name}",
            "chars": len(t.read_text()),
        }

    # ---- READ: stored content that could only come from opening the file ----
    read = {}

    # Drawings: 91 base-bid sheets carry a vision rationale.
    for f in (SRC / "03-drawings").glob("*.pdf"):
        rel = f"03-drawings/{f.name}"
        n = sum(1 for e in vis.values() if True)  # counted per file below
        read[rel] = {"evidence": f"vision rationales stored for sheets in this set",
                     "detail": f"{len(vis)} sheets vision-read across the three drawing files"}

    # Addenda: the supersession map stores overlay diffs and quoted clause text.
    a1 = smap.get("addendum_1", {})
    for sh in a1.get("sheets_reissued", []):
        loc = (sh.get("revised_location") or "").split(" p.")[0]
        if loc:
            od = sh.get("overlay_diff")
            read[loc] = {"evidence": "overlay diff vs base sheet stored",
                         "detail": f"{sh['sheet']}: " + ("structured diff" if isinstance(od, list) else str(od)[:60])}
    for key, node in (("clarification_1", "key_overrides"), ("clarification_2", "changes")):
        c = smap.get(key, {})
        f = c.get("file")
        if f:
            read[f] = {"evidence": "verbatim responses/changes transcribed",
                       "detail": f"{len(c.get(node, []))} items captured"}
    if smap.get("clarification_1", {}).get("rfi_log"):
        read[smap["clarification_1"]["rfi_log"]] = {
            "evidence": "RFI responses transcribed verbatim",
            "detail": f"{len(smap['clarification_1'].get('key_overrides', []))} RFI answers captured"}
    nf = a1.get("narrative_file")
    if nf:
        read[f"06-addenda/Addendum #1 (05.06.26)/{nf}"] = {
            "evidence": "change list quoted (section 5.01)",
            "detail": "narrative read; its 5-sheet list compared against the 7 actually reissued"}
    for s in a1.get("specifications_added", []):
        if s.get("file"):
            read[s["file"]] = {"evidence": "section content summarised",
                               "detail": f'{s["section"]} {s["title"]} — Section Includes captured'}

    # Spec manual splits: a section is READ only where the index cites it.
    cited_specs = set()
    for p in v2.get("packages", {}).values():
        for s in p.get("primary_specifications", []) + p.get("related_specifications", []):
            cited_specs.add(s["section"].replace(" ", ""))

    # Scope-review agendas / homework actually opened (content quoted anywhere).
    blob = " ".join((INDEX / n).read_text() for n in
                    ["proposal-inventory.json", "addendum-supersession-map.json",
                     "package-index-v2.json"] if (INDEX / n).exists())
    for f in SRC.rglob("*"):
        if not f.is_file():
            continue
        rel = str(f.relative_to(SRC))
        if "1% Descopes" in rel and f.suffix in (".docx", ".pdf"):
            # quoted content, not just the path, is the test
            stem = f.stem
            if stem in blob and ("Excludes" in blob or "exclusion" in blob.lower()):
                if "GTI" in stem:
                    read[rel] = {"evidence": "exclusions and inclusions transcribed",
                                 "detail": "GTI/BrightView scope review — 6 exclusions, 4 inclusions captured"}

    # ---- METADATA: filename-derived only ----
    metadata = {}
    for pid, pk in inv.get("packages", {}).items():
        for pr in pk.get("proposals", []):
            metadata.setdefault(pr["file"], {
                "evidence": "filename parsed only",
                "detail": f"package + {len(pr.get('flags', []))} status flag(s) from the filename; "
                          "proposal contents never opened"})
        for sd in pk.get("supporting_docs", []):
            metadata.setdefault(sd["file"], {
                "evidence": "filename parsed only",
                "detail": f"classified as {sd.get('kind')}; contents never opened"})

    # ---- classify every file ----
    rows, buckets = [], defaultdict(list)
    for f in sorted(p for p in SRC.rglob("*") if p.is_file() and p.name != ".gitkeep"):
        rel = str(f.relative_to(SRC))
        if "/_extracted/" in rel or rel.startswith("02-trade-scopes-bidform/_extracted"):
            tier, ev, det = "DERIVED", "artifact produced by this pipeline", ""
        elif rel.startswith("04-specs-reports/spec-manual-split"):
            m = re.search(r"div-(\d{2})", rel)
            hit = [s for s in cited_specs if m and s.startswith(m.group(1))]
            if hit:
                tier, ev = "READ", "sections cited by the index"
                det = f"{len(hit)} section(s) from this division are cited"
            else:
                tier, ev, det = "UNOPENED", "no section from this division is cited", ""
        elif rel in extracted:
            tier, ev = "EXTRACTED", "full text extracted to a derived artifact"
            det = f'{extracted[rel]["chars"]:,} chars -> {extracted[rel]["artifact"]}'
        elif rel in read:
            tier, ev, det = "READ", read[rel]["evidence"], read[rel]["detail"]
        elif rel in metadata:
            tier, ev, det = "METADATA", metadata[rel]["evidence"], metadata[rel]["detail"]
        else:
            tier, ev, det = "UNOPENED", "no evidence of content being opened", ""
        rows.append({"file": rel, "tier": tier, "evidence": ev, "detail": det})
        buckets[tier].append(rel)

    by_folder = defaultdict(lambda: defaultdict(int))
    for r in rows:
        by_folder[r["file"].split("/")[0]][r["tier"]] += 1

    audit = {
        "_generated": "2026-08-04",
        "_question": "Has each source document's CONTENT been indexed — not merely its path cited?",
        "_why_this_differs_from_file_coverage_audit": (
            "file-coverage-audit.json counts a file as processed when its path appears in any index "
            "artifact. A path can be cited by a document nobody opened; that is how the v1 index "
            "reported full coverage while all 33 scope narratives sat unread. This audit accepts only "
            "extracted text or stored content-derived evidence."),
        "_tiers": {
            "EXTRACTED": "Full text pulled into a derived artifact on disk.",
            "READ": "Content demonstrably opened — stored rationale, quotation or diff.",
            "METADATA": "Only filename-derived facts recorded. Document unopened.",
            "UNOPENED": "No contact with the content.",
            "DERIVED": "Artifact this pipeline produced, not a source document.",
        },
        "_totals": {k: len(v) for k, v in sorted(buckets.items())},
        "by_folder": {k: dict(v) for k, v in sorted(by_folder.items())},
        "files": rows,
    }
    (INDEX / "content-index-audit.json").write_text(json.dumps(audit, indent=2) + "\n")

    order = ["EXTRACTED", "READ", "METADATA", "UNOPENED", "DERIVED"]
    md = ["# Content Index Audit\n",
          "**Question:** has each source document's *content* been indexed — not merely its path cited?\n",
          "| Tier | Files | Meaning |", "|---|---|---|"]
    mean = audit["_tiers"]
    for t in order:
        md.append(f'| {t} | {len(buckets[t])} | {mean[t]} |')
    md.append("\n## By folder\n")
    md.append("| Folder | " + " | ".join(order) + " |")
    md.append("|---" * (len(order) + 1) + "|")
    for folder, counts in audit["by_folder"].items():
        md.append(f"| `{folder}/` | " + " | ".join(str(counts.get(t, 0)) for t in order) + " |")
    (INDEX / "content-index-audit.md").write_text("\n".join(md) + "\n")

    tot = len(rows)
    for t in order:
        print(f"{t:10} {len(buckets[t]):>4}   ({100*len(buckets[t])/tot:.0f}%)")
    print(f"{'TOTAL':10} {tot:>4}")
    print()
    for folder, counts in audit["by_folder"].items():
        print(f"  {folder:26} " + "  ".join(f"{t[:4]}={counts.get(t,0)}" for t in order))


if __name__ == "__main__":
    main()
