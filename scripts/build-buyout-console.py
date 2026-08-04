#!/usr/bin/env python3
"""
Build the Buy-Out Console — a standalone, self-contained HTML app implementing the
Claude Design spec `Buyout Console.dc.html`, wired to this project's REAL index
artifacts rather than the design mock's placeholder data.

Design source: claude.ai/design project 64680ce4-1bb7-4e4e-8f1c-8659b481aad8
Design system: CORE Construction (tokens inlined so the output is standalone).

What differs from the design mock, deliberately:
  - The mock invents subcontractors, spec sections and a leveling register. This
    build reads the actual awarded subs, the actual primary specifications parsed
    verbatim from the scope narratives, and builds the leveling register from real
    PM findings plus the 134 coordination clauses the scope docs actually contain.
  - The mock's "stage" is a 0-8 pipeline position per package. Real pipeline state
    is per-project (Stage 2, reopened), so package progress is derived from award
    and document status instead of invented per-package stages.

Usage:  python3 scripts/build-buyout-console.py
Writes: 04-output/buyout-console.html
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "01-index"
OUT = ROOT / "04-output" / "buyout-console.html"

DIV_NAMES = {
    "00": "Procurement & Contracting", "01": "General Requirements",
    "02": "Existing Conditions", "03": "Concrete", "04": "Masonry", "05": "Metals",
    "06": "Wood & Plastics", "07": "Thermal & Moisture", "08": "Openings",
    "09": "Finishes", "10": "Specialties", "11": "Equipment", "12": "Furnishings",
    "13": "Special Construction", "21": "Fire Suppression", "22": "Plumbing",
    "23": "HVAC", "26": "Electrical", "27": "Communications",
    "28": "Electronic Safety & Security", "31": "Earthwork",
    "32": "Exterior Improvements", "33": "Utilities",
}


def load(name):
    return json.loads((INDEX / name).read_text())


def build_packages():
    v2 = load("package-index-v2.json")
    inv = load("proposal-inventory.json")
    aw = load("awarded-sub-mapping.json")

    awarded = {}
    def walk(o):
        if isinstance(o, dict):
            for k, val in o.items():
                if isinstance(val, dict) and "awarded_sub" in val and "title" in val:
                    awarded[k] = val
                else:
                    walk(val)
    walk(aw)

    pkgs = []
    for pid, p in sorted(v2["packages"].items()):
        specs = [f'{s["section"]}|{s["title"]}' for s in p["primary_specifications"]]
        divs = [f'Div {d["division"]}|{d["title"]}' for d in p["primary_divisions"]]
        prim = specs + divs

        # Division for grouping. An explicit "Primary Specifications: Division NN"
        # beats inference. Otherwise take the MODAL division across the primary
        # sections, not the first one -- RFP-030's list starts at 07 26 00
        # (damproofing) while the package is Division 03, and RFP-060 starts at
        # 05 40 00 while four of its six sections are Division 09.
        if p["primary_divisions"]:
            dv = str(p["primary_divisions"][0]["division"]).zfill(2)
        elif p["primary_specifications"]:
            divs = [s["section"][:2] for s in p["primary_specifications"]]
            dv = max(sorted(set(divs), key=divs.index), key=divs.count)
        else:
            dv = "--"

        a = awarded.get(pid, {})
        ipk = inv["packages"].get(pid, {})

        flags = []
        if not p["primary_specifications"] and not p["primary_divisions"]:
            flags.append("NOSPEC")
        if any("WARNING" in c for c in p["drawing_sheet_candidates"]):
            flags.append("REV")
        if p.get("_pm_rulings"):
            flags.append("RULED")
        pf = [f for f in (a.get("flags") or [])]
        if pf:
            flags.append("PROC")

        # Procurement flags carried on this package's proposals
        procflags = sorted({f for pr in ipk.get("proposals", []) for f in pr.get("flags", [])
                            if f in ("late_submission", "backup_but_no_signed_bid_form",
                                     "not_submitted_via_building_connected",
                                     "marked_do_not_use", "value_only_no_scope_detail")})

        pkgs.append({
            "id": pid,
            "title": p["title"] or pid,
            "source": pid[:3],
            "div": dv,
            "divName": DIV_NAMES.get(dv, "—"),
            "specs": prim,
            "scopeItems": len(p["scope_items_verbatim"]),
            "coordCount": len(p["coordination_clauses"]),
            "coord": p["coordination_clauses"],
            "alts": len(p["alternates"]),
            "sub": a.get("awarded_sub"),
            "price": a.get("proposal_price"),
            "status": a.get("status") or ("not-solicited" if pid.startswith("ITB") else "unknown"),
            "bidders": ipk.get("bidders", []),
            "bidderCount": ipk.get("bidder_count", 0),
            "flags": flags,
            "procflags": procflags,
            "rulings": [r["ruling"] for r in p.get("_pm_rulings", [])],
            "awardNotes": (a.get("flags") or []) + ([a["note"]] if a.get("note") else []),
            "sheets": [d["sheet_number"] for d in p["drawing_sheets"]],
            "candidates": [{"n": c["sheet_number"], "t": c.get("sheet_title"),
                            "warn": "WARNING" in c} for c in p["drawing_sheet_candidates"]],
        })
    return pkgs


def build_spec_coverage(pkgs):
    m = {}
    for p in pkgs:
        for s in p["specs"]:
            num, title = s.split("|", 1)
            m.setdefault(num, {"section": num, "title": title, "by": []})
            m[num]["by"].append(p["id"])
    rows = []
    for k in sorted(m):
        r = m[k]
        n = len(r["by"])
        r["state"] = "overlap" if n > 1 else "claimed"
        rows.append(r)
    # Known unclaimed / partially-owned sections surfaced by the index findings
    for num, title, note in [
        ("08 31 00", "Access Doors and Panels",
         "Related to RFP-098 / RFP-100 / RFP-103, primary to none — MEP supply, RFP-060 installs (PM 07.31.26)"),
        ("12 93 00", "Site Furnishings",
         "Spans ITB-018 and ITB-019 per its own Section Includes — confirm the athletic-equipment portion"),
    ]:
        rows.append({"section": num, "title": title, "by": [], "state": "gap", "note": note})
    return rows


def build_leveling():
    v2 = load("package-index-v2.json")
    inv = load("proposal-inventory.json")
    sm = load("addendum-supersession-map.json")
    reg = []

    for f in v2.get("_findings_for_pm", []):
        reg.append({
            "kind": "GAP" if f["severity"] in ("high", "HIGH") else "OVL",
            "sev": f["severity"], "title": f["title"], "src": "package-index-v2",
            "pkgs": f.get("packages", []), "detail": f.get("detail", ""),
            "cites": [[k, str(v)[:400]] for k, v in f.items()
                      if k in ("why_it_matters", "pm_action", "resolved_by_pm_2026_07_31",
                               "clarification_2026_07_31", "why_it_still_matters")],
        })
    for f in inv.get("_findings_for_pm", []):
        reg.append({
            "kind": "GAP" if f["severity"] in ("high",) else "OVL",
            "sev": f["severity"], "title": f["title"], "src": "proposal-inventory",
            "pkgs": f.get("packages", []), "detail": f.get("detail", ""),
            "cites": [[k, str(v)[:400]] for k, v in f.items()
                      if k in ("why_it_matters", "pm_action", "why_it_still_matters")],
        })

    a1 = sm["addendum_1"]
    d = a1["_CRITICAL_DISCREPANCY"]
    reg.append({
        "kind": "OVL", "sev": "medium", "title": d["finding"][:90], "src": "supersession-map",
        "pkgs": [], "detail": d["why_it_still_matters"],
        "cites": [["pm_action", d["pm_action"]], ["correction", d.get("CORRECTION_2026_07_31", "")[:400]]],
    })
    c2 = sm["clarification_2"]["changes"][0]
    reg.append({
        "kind": "GAP", "sev": "high", "title": "Prevailing wage — Clark County vs Nye County",
        "src": "supersession-map", "pkgs": ["ALL 33"], "detail": c2["_FLAG"],
        "cites": [["Clarification No. 2", c2["content"]]],
    })
    order = {"high": 0, "HIGH": 0, "medium": 1, "low": 2, "resolved": 3}
    reg.sort(key=lambda r: order.get(r["sev"], 9))
    return reg


def main():
    pkgs = build_packages()
    payload = {
        "packages": pkgs,
        "specCoverage": build_spec_coverage(pkgs),
        "leveling": build_leveling(),
        "meta": {
            "project": "Tonopah THS Sports Complex",
            "owner": "Nye County School District",
            "delivery": "CMAR / GMP",
            "bidSet": "Addendum #1 (05.06.26) · Clarification 1 & 2",
            "totals": load("package-index-v2.json")["_totals"],
            "coverage": load("file-coverage-audit.json")["_totals"],
        },
    }
    tpl = (ROOT / "scripts" / "buyout-console.template.html").read_text()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(tpl.replace("/*__DATA__*/null", json.dumps(payload, separators=(",", ":"))))
    kb = OUT.stat().st_size / 1024
    print(f"packages:      {len(pkgs)}")
    print(f"spec rows:     {len(payload['specCoverage'])}")
    print(f"leveling rows: {len(payload['leveling'])}")
    print(f"-> {OUT.relative_to(ROOT)} ({kb:.0f} KB)")


if __name__ == "__main__":
    main()
