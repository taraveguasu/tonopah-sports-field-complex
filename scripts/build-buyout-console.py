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
    """Read the CURRENT per-package records, not the superseded v2 index.

    This console was built on 08.04 against package-index-v2.json and
    proposal-inventory.json. Both are superseded: v2 predates all extraction work,
    and the inventory recorded filenames without opening the documents behind
    them. A dashboard reporting from those is a dashboard reporting pre-rebuild
    numbers, which is worse than no dashboard.
    """
    man = load("package-index.json")
    spec = load("spec-section-catalog.json")
    sheets = load("sheet-package-assignments.json")
    items = load("pm-open-items.json")

    by_pkg_items = {}
    for it in items.get("items", []):
        for pid in it["packages"]:
            by_pkg_items.setdefault(pid, []).append(it)

    pkgs = []
    for pid in sorted(man["packages"]):
        rec = json.loads((INDEX / "packages" / f"{pid}.json").read_text())
        primary = rec["spec_sections"]["primary"] + rec["spec_sections"]["added_by_pm_ruling"]
        specs = [f'{s["section"]}|{s["title"]}' for s in primary]

        # Division for grouping: modal division across the primary sections. Taking
        # the first is wrong -- RFP-030's list opens at 07 26 00 (vapour retarders)
        # while the package is Division 03.
        divs = [s["section"][:2] for s in primary]
        dv = max(sorted(set(divs), key=divs.index), key=divs.count) if divs else "--"

        a = rec["awarded_sub"]
        sh = sheets["sheets_by_package"].get(pid, {})
        gaps = rec["spec_sections"]["cited_by_this_scope_doc_but_absent_from_manual"]
        open_items = by_pkg_items.get(pid, [])

        flags = []
        if not primary:
            flags.append("NOSPEC")
        if any(s["basis"] == "trade_judgment" for s in primary):
            flags.append("JUDGED")
        if any(s.get("conflict") for s in primary):
            flags.append("CONFLICT")
        if any(g["status"] == "OPEN" for g in gaps.values()):
            flags.append("SPECGAP")
        if a.get("status") != "awarded":
            flags.append("UNAWARDED")
        if any(i["severity"] == "high" for i in open_items):
            flags.append("DECISION")

        scope_lines = sum(len(b.get("inclusions", []))
                          + len(b.get("exclusions_scope_specific", []))
                          + len(b.get("priced_line_items", [])) for b in rec["bidders"])

        pkgs.append({
            "id": pid,
            "title": rec["_title"],
            "source": pid[:3],
            "div": dv,
            "divName": DIV_NAMES.get(dv, "—"),
            "specs": specs,
            "specBasis": [s["basis"] for s in primary],
            "flowDown": [f'{s["section"]}|{s["title"]}'
                         for s in rec["spec_sections"]["flow_down_from_other_packages"]],
            "specGaps": [[k, (v.get("title_per_scope_doc") or ""), v["status"]]
                         for k, v in gaps.items()],
            "scopeItems": scope_lines,
            "coordCount": len(rec["spec_sections"]["flow_down_from_other_packages"]),
            "coord": [s["note"] for s in rec["spec_sections"]["flow_down_from_other_packages"]],
            "alts": sum(len(b.get("priced_line_items", [])) for b in rec["bidders"]),
            "sub": a.get("awarded_sub"),
            "price": a.get("proposal_price"),
            "status": a.get("status", "not-yet-awarded"),
            "bidders": [b["firm"] for b in rec["bidders"]],
            "bidderCount": len(rec["bidders"]),
            "flags": flags,
            "procflags": [],
            "rulings": [s["rationale"] for s in primary if s["basis"] == "pm_ruling"],
            "awardNotes": ([a["note"]] if a.get("note") else []),
            "sheets": [d["sheet"] for d in rec["drawings"]["draft_from"]],
            "candidates": [{"n": s, "t": "", "warn": True}
                           for s in sh.get("leads_to_verify", [])],
            "openItems": [{"n": i["n"], "id": i["id"], "sev": i["severity"],
                           "title": i["title"]} for i in open_items],
        })
    return pkgs


def build_spec_coverage(pkgs):
    """Every technical section in the manual with its owner and the basis for it.

    The earlier version derived coverage from the packages' own spec lists, so a
    section owned by nobody was invisible by construction -- the two known gaps had
    to be hand-appended. The catalog assigns all 106 technical sections, so
    coverage can be read rather than reconstructed.
    """
    cat = load("spec-section-catalog.json")
    rows = []
    for sec in cat["sections"]:
        if sec.get("basis") in ("general_conditions", "not_a_technical_section"):
            continue
        by = [sec["primary_package"]] + sec.get("also_assigned_by_pm_ruling", [])
        rows.append({
            "section": sec["section"], "title": sec["title"], "by": by,
            "state": ("conflict" if sec.get("conflict")
                      else "flow" if sec.get("flow_down")
                      else "claimed"),
            "basis": sec["basis"],
            "note": (sec.get("flow_down") or sec["rationale"])[:300],
            "alsoCited": sec.get("also_cited_by", []),
        })
    for num, g in cat.get("cited_but_absent_from_manual", {}).items():
        rows.append({
            "section": num, "title": (g.get("title_per_scope_doc") or "") + " — NOT IN MANUAL",
            "by": g["cited_by"],
            "state": "closed" if g["status"] != "OPEN" else "gap",
            "basis": "absent",
            "note": g["note"][:300],
            "alsoCited": [],
        })
    rows.sort(key=lambda r: r["section"])
    return rows


def build_leveling():
    """The leveling register is now the open-items register.

    It is assembled from the indexes by build_open_items.py, so an item closed by
    a ruling disappears on the next run instead of lingering in a dashboard.
    """
    items = load("pm-open-items.json")
    kind = {"SPEC-C": "OVL", "SPEC-G": "GAP", "SPEC-N": "GAP", "BID-B": "OVL",
            "BID-T": "GAP", "BID-L": "GAP", "BID-P": "GAP", "BID-U": "GAP",
            "GMP-0": "OVL", "AWD-0": "GAP", "PROC-": "GAP"}
    reg = []
    for it in items.get("items", []):
        pre = it["id"][:5]
        reg.append({
            "kind": kind.get(pre, "GAP"),
            "sev": it["severity"],
            "title": f'[{it["id"]}] {it["title"]}',
            "src": "pm-open-items",
            "pkgs": it["packages"],
            "detail": it["detail"],
            "cites": [["item", str(it["n"])]],
        })
    order = {"high": 0, "medium": 1, "low": 2}
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
            "bidSet": "Addendum #1 (05.06.26) · Clarifications 1 & 2 · GMP R2 Exhibit B (07.01.26)",
            "totals": load("package-index.json")["_totals"],
            "coverage": load("file-coverage-audit.json")["_totals"],
        },
    }
    import sys
    sys.path.insert(0, str(ROOT / "scripts"))
    from render_console_body import render

    shell = (ROOT / "scripts" / "buyout-console.shell.html").read_text()
    body = render(payload)
    # JS is enhancement only: the filter box and the Feel controls. Everything
    # else is already in the markup and works with scripts disabled.
    js = """
<script>
(function(){
  var f=document.getElementById('filter'); if(f){ f.hidden=false;
    f.addEventListener('input',function(){
      var q=f.value.trim().toLowerCase();
      document.querySelectorAll('details.pkg').forEach(function(d){
        d.style.display = !q || d.textContent.toLowerCase().indexOf(q)>-1 ? '' : 'none';
      });
    });
  }
  var TH={density:{'Command center':{rowPad:'6px 14px',fs:'12px',kpiPad:'9px 16px',kpiNum:'20px'},
    'Standard':{rowPad:'11px 16px',fs:'13px',kpiPad:'14px 20px',kpiNum:'26px'},
    'Briefing':{rowPad:'17px 22px',fs:'14.5px',kpiPad:'22px 24px',kpiNum:'34px'}},
   chrome:{'Night bar':{bar:'var(--core-black)',barFg:'#fff',barSub:'var(--core-cement)',barEdge:'var(--core-bright-green)',barAccent:'var(--core-bright-green)',sect:'var(--core-asphalt)',sectFg:'#fff',sectSub:'var(--core-cement)',page:'var(--core-concrete)'},
     'Field green':{bar:'var(--core-deep-green)',barFg:'#fff',barSub:'#BCD8C4',barEdge:'var(--core-bright-green)',barAccent:'var(--core-bright-green)',sect:'var(--core-green)',sectFg:'#fff',sectSub:'#CFE5D4',page:'#EEF2ED'},
     'Paper':{bar:'#fff',barFg:'var(--core-black)',barSub:'var(--core-asphalt)',barEdge:'var(--core-black)',barAccent:'var(--core-deep-green)',sect:'var(--core-concrete)',sectFg:'var(--core-black)',sectSub:'var(--core-asphalt)',page:'#F6F5F2'}},
   risk:{'Calm':'2px','Standard':'4px','Alarm':'6px'}};
  function apply(){
    var r=document.documentElement.style, d=document.getElementById('density'),
        c=document.getElementById('chrome'), k=document.getElementById('risk');
    var a=TH.density[d.value]; for(var x in a) r.setProperty('--'+x,a[x]);
    var b=TH.chrome[c.value];  for(var y in b) r.setProperty('--'+y,b[y]);
    r.setProperty('--railW',TH.risk[k.value]);
  }
  ['density','chrome','risk'].forEach(function(id){
    var el=document.getElementById(id); if(el) el.addEventListener('change',apply);
  });
  apply();
})();
</script>"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(shell.replace("<!--__BODY__-->", body + js))
    kb = OUT.stat().st_size / 1024
    print(f"packages:      {len(pkgs)}")
    print(f"spec rows:     {len(payload['specCoverage'])}")
    print(f"leveling rows: {len(payload['leveling'])}")
    print(f"-> {OUT.relative_to(ROOT)} ({kb:.0f} KB)")


if __name__ == "__main__":
    main()
