#!/usr/bin/env python3
"""
Assemble every open item needing a PM decision into one numbered register.

Built from the index artifacts rather than hand-maintained, so an item cannot
drift out of sync with the evidence behind it, and an item closed by a ruling
disappears from the register on the next run instead of lingering.

Sources:
  01-index/spec-section-catalog.json   spec gaps, section conflicts, empty packages
  01-index/proposal-content.json       bid-tab reconciliation, bundled bids, price moves
  01-index/awarded-sub-mapping.json    award anomalies
  01-index/gmp-basis-exhibit-b.json    GMP Basis flags (GMP-01..07)

Items carry a stable ID so a decision can be recorded against it later.

Usage:  python3 scripts/build_open_items.py
Writes: 01-index/pm-open-items.md
        01-index/pm-open-items.json
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "01-index"


def load(name):
    p = INDEX / name
    return json.loads(p.read_text()) if p.exists() else {}


# Items that live in no index because they are questions about process or about
# documents outside the corpus. Kept short and explicit.
MANUAL_ITEMS = [
    ("PROC-01", "medium", "Confirm CORE job number is 25-10-003",
     "Taken from the GMP EOD filename. Never confirmed against a CORE system of record.",
     ["ALL"]),
    ("PROC-02", "medium", "Confirm no addenda or clarifications issued after Clarification No.2",
     "Clarification No.2 is dated 05.07.26 and bid opening was 05.12.26. The GMP R2 (07.01.26) "
     "is treated as an addendum per ruling 08.04.26. Confirm nothing else was issued between "
     "those dates or since, because anything issued supersedes what is indexed.",
     ["ALL"]),
    ("PROC-03", "low", "Precon to Ops handoff date, for the 30-day buy-out target",
     "CLAUDE.md records the buy-out target as 30 days from handoff, with the handoff date TBD.",
     ["ALL"]),
]

SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def spec_items(cat):
    out = []
    n = 0
    for s, v in cat.get("cited_but_absent_from_manual", {}).items():
        if v.get("status") != "OPEN":
            continue
        n += 1
        cand = v.get("candidate_sections_in_manual") or []
        # A near-miss number the PM need only confirm is not the same problem as a
        # section that is simply not in the manual.
        sev = "low" if cand else "high"
        out.append((f"SPEC-G{n:02d}", sev,
                    f"{s} {v.get('title_per_scope_doc') or ''} — cited but absent from the manual",
                    (v.get("note") or "") +
                    (f"  CANDIDATE(S) in manual: {', '.join(cand)} — confirm or reject."
                     if cand else "  No candidate section exists; this needs a source."),
                    sorted(v.get("cited_by", []))))
    for i, c in enumerate(cat.get("conflicts_needing_pm_ruling", []), 1):
        out.append((f"SPEC-C{i:02d}", "high",
                    f"{c['section']} {c['title']} — claimed by more than one scope doc",
                    f"Assigned to {c['assigned_to']} ({c['basis']}); also cited by "
                    f"{', '.join(c['also_cited_by'])}. {c['rationale']}",
                    sorted(set([c["assigned_to"]] + c["also_cited_by"]))))
    for i, (p, v) in enumerate(sorted(cat.get("packages_with_no_primary_section", {}).items()), 1):
        out.append((f"SPEC-N{i:02d}", "medium",
                    f"{p} holds no spec section of its own",
                    v["reason"], [p]))
    return out


def bid_items(prop, awarded):
    out = []
    rec = prop.get("_bid_tab_reconciliation", {})
    for i, m in enumerate(rec.get("mismatches", []), 1):
        out.append((f"BID-T{i:02d}", "high",
                    f"{m['package']} — {m['firm']} tabulated at a price the proposal does not state",
                    f"Proposal states ${m['price_per_own_proposal']:,} "
                    f"({m['price_source']}); bid tab states ${m['price_per_bid_tab']:,} as "
                    f"'{m['tabulated_as']}'. {m['reading']} "
                    f"Correction already applied to awarded-sub-mapping.json — confirm.",
                    [m["package"]]))
    for i, f in enumerate(rec.get("firms_not_found_on_tab", []), 1):
        out.append((f"BID-L{i:02d}", "high",
                    f"{f['package']} — {f['firm']} bid this package but appears on no tab row for it",
                    f["reading"] + (f"  Tabulated instead under "
                                    f"{f['same_price_under_other_trade'][0]['tabulated_under']} at "
                                    f"${f['same_price_under_other_trade'][0]['price']:,}."
                                    if f.get("same_price_under_other_trade") else ""),
                    [f["package"]]))
    for i, b in enumerate(prop.get("_bundled_proposals", []), 1):
        out.append((f"BID-B{i:02d}", "medium",
                    f"{b['firm']} bid {', '.join(b['packages_bid'])} as one bundled scope",
                    b["reading"], b["packages_bid"]))
    for i, m in enumerate(prop.get("_price_movements", []), 1):
        seq = " -> ".join(f"${x['price']:,} ({x['date']})" for x in m["sequence"])
        out.append((f"BID-P{i:02d}", "medium",
                    f"{m['package']} — {m['firm']}'s price moves between documents",
                    f"{seq}. The later document governs by date; confirm which figure is intended "
                    f"before the subcontract value is set.",
                    [m["package"]]))
    seen = set()
    for i, t in enumerate(prop.get("_unassigned_trades", []), 1):
        trade = t.split(" — ")[0]
        if trade in seen:
            continue
        seen.add(trade)
        out.append((f"BID-U{len(seen):02d}", "high",
                    f"Trade {trade} was bid but maps to no bid package",
                    "Proposals were solicited and received under this trade number, which matches "
                    "none of the 33 packages. Confirm whether it is CORE self-perform, folded "
                    "into another subcontract, or needs its own package — as it stands the scope "
                    "is bid with no Attachment A to land in.",
                    ["UNASSIGNED"]))
    for i, f in enumerate(awarded.get("flags_for_pm_review", []), 1):
        if "WITHDRAWN" in f or "UNRELIABLE" in f or f.startswith(("RFP-016 /", "RFP-002 PRICE",
                                                                  "070 FINAL")):
            continue     # already carried as its own item above
        out.append((f"AWD-{i:02d}", "medium", f[:90].rstrip(" ,.-") + "...", f, ["see text"]))
    return out


def gmp_items(gmp):
    return [(f["id"], f["severity"], f["title"], f["detail"], f["packages"])
            for f in gmp.get("_new_flags_for_pm", [])]


def main():
    cat = load("spec-section-catalog.json")
    prop = load("proposal-content.json")
    awarded = load("awarded-sub-mapping.json")
    gmp = load("gmp-basis-exhibit-b.json")

    items = (gmp_items(gmp) + spec_items(cat) + bid_items(prop, awarded) + MANUAL_ITEMS)
    items.sort(key=lambda x: (SEVERITY_ORDER.get(x[1], 3), x[0]))

    recs = [{"n": i, "id": a, "severity": b, "title": c, "detail": d, "packages": e,
             "decision": None}
            for i, (a, b, c, d, e) in enumerate(items, 1)]

    lines = [
        "# Open items for PM decision",
        "",
        f"Generated {cat.get('_generated', '')} from the index artifacts, not maintained by hand — "
        "rebuild with `python3 scripts/build_open_items.py` after any ruling, and items closed by "
        "a ruling drop off automatically.",
        "",
        f"**{len(recs)} open** — "
        + ", ".join(f"{sum(1 for r in recs if r['severity'] == s)} {s}"
                    for s in ("high", "medium", "low")),
        "",
        "Reply by number. Anything not answered stays open.",
        "",
    ]
    for sev in ("high", "medium", "low"):
        group = [r for r in recs if r["severity"] == sev]
        if not group:
            continue
        lines += [f"## {sev.upper()} ({len(group)})", ""]
        for r in group:
            pk = ", ".join(r["packages"][:8]) + (" ..." if len(r["packages"]) > 8 else "")
            lines += [f"**{r['n']}. [{r['id']}] {r['title']}**",
                      f"  <sub>{pk}</sub>", "",
                      f"  {r['detail']}", ""]
    (INDEX / "pm-open-items.md").write_text("\n".join(lines) + "\n")
    (INDEX / "pm-open-items.json").write_text(json.dumps({
        "_generated": cat.get("_generated", ""),
        "_purpose": "Numbered register of every open PM decision, assembled from the indexes.",
        "_totals": {s: sum(1 for r in recs if r["severity"] == s)
                    for s in ("high", "medium", "low")},
        "items": recs,
    }, indent=2) + "\n")

    print(f"{len(recs)} open items")
    for sev in ("high", "medium", "low"):
        print(f"  {sev:<7} {sum(1 for r in recs if r['severity'] == sev)}")


if __name__ == "__main__":
    main()
