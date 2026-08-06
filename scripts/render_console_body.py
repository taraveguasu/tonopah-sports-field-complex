#!/usr/bin/env python3
"""
Render the Buy-Out Console body as STATIC HTML.

The first cut of this console generated everything from JavaScript at runtime.
That renders fine in a browser, but any viewer that sandboxes scripts — the
claude.ai file preview, an email client, a print-to-PDF — shows a header and
nothing else. The data has to live in the markup.

So: everything below is server-rendered at build time. Tabs use radio inputs and
`:checked ~` selectors, package detail uses `<details>`, so navigation works with
scripts fully disabled. JavaScript only adds the filter box and the Feel controls.
"""

from html import escape as e


def money(n):
    return "—" if n is None else "$" + f"{round(n/1000):,}" + "K"


FLAGMETA = {
    "NOSPEC": ("#FBEAE9", "#B3261E",
               "No spec section in the manual covers this package"),
    "SPECGAP": ("#FBEAE9", "#B3261E",
                "Scope doc cites a section absent from the manual, still open"),
    "CONFLICT": ("#FBEAE9", "#B3261E",
                 "A spec section here is also claimed by another package's scope doc"),
    "DECISION": ("#FFF4DB", "#8A6100",
                 "A high-severity PM decision is open on this package"),
    "UNAWARDED": ("#FFF4DB", "#8A6100",
                  "No awarded subcontractor — drafts from generic scope only"),
    "JUDGED": ("#EEF1F6", "#3A4A5E",
               "Carries a spec section assigned by trade judgment, not by citation"),
    # Retained so an older payload still renders rather than raising.
    "REV": ("#FFF4DB", "#8A6100", "Cites a sheet Addendum #1 superseded — needs re-read"),
    "PROC": ("#FBEAE9", "#B3261E", "Procurement flag on the award"),
    "RULED": ("#E6F4EC", "#004E2B", "PM ruling applied to this package"),
}
PROCLABEL = {
    "late_submission": "Late",
    "backup_but_no_signed_bid_form": "No signed Bid Form",
    "not_submitted_via_building_connected": "Bypassed Building Connected",
    "marked_do_not_use": "Marked do-not-use",
    "value_only_no_scope_detail": "Value only, no scope",
}


def status_pill(p):
    s = (p.get("status") or "").lower()
    if s == "awarded":
        return "Awarded", "#E6F4EC", "#004E2B"
    if "not yet awarded" in s or s == "not-yet-awarded":
        return "Not yet awarded", "#FFF4DB", "#8A6100"
    return ("ITB — no award tracked" if p["source"] == "ITB" else "No award on file",
            "var(--core-concrete)", "var(--core-asphalt)")


def kpis(d):
    all_ = d["packages"]
    aw = [p for p in all_ if (p.get("status") or "").lower() == "awarded"]
    committed = sum(p.get("price") or 0 for p in aw)
    nospec = sum(1 for p in all_ if "NOSPEC" in p["flags"])
    high = sum(1 for l in d["leveling"] if str(l["sev"]).lower() == "high")
    # Judgment assignments are the reviewable surface: they are my calls, not
    # citations, and every draft inherits them. That is the number a PM should
    # see on the dashboard, not a procurement-flag count with no live source.
    judged = sum(1 for r in d["specCoverage"] if r.get("basis") == "trade_judgment")
    gaps_open = sum(1 for r in d["specCoverage"] if r.get("state") == "gap")
    rows = [
        ("Packages", len(all_), "16 RFP (1%) · 17 ITB", "var(--core-black)"),
        ("Awarded", f"{len(aw)} / 16", money(committed) + " committed", "var(--core-green)"),
        ("Open high-severity", high, "in the leveling register",
         "var(--status-danger)" if high else "var(--core-green)"),
        ("No spec source", nospec, "packages with no primary spec",
         "var(--status-danger)" if nospec else "var(--core-green)"),
        ("Spec gaps open", gaps_open, "cited by a scope doc, absent from the manual",
         "var(--status-danger)" if gaps_open else "var(--core-green)"),
        ("Assigned by judgment", judged, "sections assigned by trade judgment, not citation",
         "var(--status-warning)"),
    ]
    return '<div class="kpis">' + "".join(
        f'<div class="kpi"><div class="k">{e(str(l))}</div>'
        f'<div class="v" style="color:{c}">{e(str(v))}</div>'
        f'<div class="s">{e(str(s))}</div></div>' for l, v, s, c in rows) + "</div>"


def pkg_detail(p):
    """Inline detail body — the drawer content, rendered statically."""
    out = []
    t, bg, fg = status_pill(p)
    out.append('<div class="dsec" style="margin-top:0">Award</div><dl class="kv">')
    out.append(f'<dt>Status</dt><dd><span class="pill" style="background:{bg};color:{fg}">{e(t)}</span></dd>')
    out.append(f'<dt>Awarded sub</dt><dd>{e(p["sub"] or "— not awarded")}</dd>')
    out.append(f'<dt>Proposal value</dt><dd>{money(p.get("price"))}</dd>')
    out.append(f'<dt>Bidders on file</dt><dd>{p["bidderCount"]} — {e(", ".join(p["bidders"]) or "none")}</dd></dl>')

    if p["procflags"]:
        out.append('<div class="dsec">Procurement flags</div><ul class="tight">')
        out += [f'<li style="color:var(--status-danger)">{e(PROCLABEL.get(f, f))}</li>' for f in p["procflags"]]
        out.append("</ul>")
    if p["awardNotes"]:
        out.append('<div class="dsec">Award notes</div>')
        out += [f'<div class="cite">{e(n)}</div>' for n in p["awardNotes"]]
    if p["rulings"]:
        out.append('<div class="dsec">PM rulings applied</div>')
        out += [f'<div class="cite" style="border-left-color:var(--core-deep-green)">{e(r)}</div>'
                for r in p["rulings"]]

    out.append('<div class="dsec">Primary specifications</div>')
    if p["specs"]:
        out.append('<ul class="tight">')
        for s in p["specs"]:
            n, ti = s.split("|", 1)
            out.append(f"<li><b>{e(n)}</b> — {e(ti)}</li>")
        out.append("</ul>")
    else:
        out.append('<div class="cite" style="border-left-color:var(--status-danger)">'
                   "No primary specification cited by the scope narrative, and none matched in the "
                   "spec manual. Execution standard undecided.</div>")

    out.append(f'<div class="dsec">Coordination clauses ({p["coordCount"]})</div>')
    if p["coord"]:
        out.append('<ul class="tight">' + "".join(f"<li>{e(c)}</li>" for c in p["coord"]) + "</ul>")
    else:
        out.append("<em>None.</em>")

    out.append('<div class="dsec">Drawings</div><dl class="kv">'
               f'<dt>Cited by scope doc</dt><dd>{e(", ".join(p["sheets"]) or "—")}</dd>'
               f'<dt>Scope items</dt><dd>{p["scopeItems"]} (verbatim)</dd>'
               f'<dt>Alternates</dt><dd>{p["alts"]}</dd></dl>')
    if p["candidates"]:
        out.append('<div class="mut" style="margin-top:10px">Candidate sheets '
                   "(not corroborated by the scope narrative):</div><ul class=\"tight\">")
        for c in p["candidates"]:
            warn = (' <span class="flag" style="background:#FFF4DB;color:#8A6100">'
                    "SUPERSEDED — RE-READ</span>") if c["warn"] else ""
            out.append(f'<li>{e(c["n"])} — {e(c["t"] or "")}{warn}</li>')
        out.append("</ul>")
    return "".join(out)


def pkg_row(p):
    t, bg, fg = status_pill(p)
    flags = "".join(
        f'<span class="flag" title="{e(FLAGMETA.get(f, ("#EEE","#333",f))[2])}" '
        f'style="background:{FLAGMETA.get(f, ("#EEE","#333",f))[0]};color:{FLAGMETA.get(f, ("#EEE","#333",f))[1]}">{f}</span>' for f in p["flags"])
    pct = min(100, round(p["scopeItems"] / 135 * 100))
    subcol = "var(--core-black)" if p["sub"] else "var(--core-cement)"
    return f"""<details class="pkg" data-pkg="{e(p['id'])}">
<summary><div class="row cols">
  <div class="id">{e(p['id'])}</div>
  <div style="display:flex;align-items:center;gap:8px;padding-right:14px;flex-wrap:wrap">
    <span class="ti">{e(p['title'])}</span>{flags}</div>
  <div class="mut">Div {e(p['div'])} · {e(p['divName'])}</div>
  <div style="padding-right:16px"><div class="mut" style="margin-bottom:4px">{p['scopeItems']} scope items</div>
    <div class="meter"><i style="width:{pct}%;background:var(--core-green)"></i></div></div>
  <div style="font-size:12.5px;color:{subcol}">{e(p['sub'] or '— not awarded')}</div>
  <div class="rt">{money(p.get('price'))}</div>
  <div class="rt" style="font-weight:600;color:var(--core-asphalt);padding-right:14px">{p['bidderCount']} bid{'' if p['bidderCount']==1 else 's'}</div>
  <div><span class="pill" style="background:{bg};color:{fg}">{e(t)}</span></div>
</div></summary>
<div class="pkgbody">{pkg_detail(p)}</div>
</details>"""


def panel_packages(d):
    groups = [("RFP", "1% List (NRS 338.16995) — RFP packages"),
              ("ITB", "Non-1% List — ITB packages")]
    out = ['<div class="panel panel-packages">',
           '<div class="toolbar" id="pkgtools"><div style="flex:1"></div>'
           '<input type="search" id="filter" placeholder="Filter packages, subs, spec sections…" '
           'style="width:320px" hidden></div>']
    for key, label in groups:
        rows = [p for p in d["packages"] if p["source"] == key]
        val = sum(p.get("price") or 0 for p in rows)
        out.append(f'<section class="grp"><div class="grph"><div class="t">{e(label)}</div>'
                   f'<div class="m">{len(rows)} packages · {money(val)} awarded value</div></div>'
                   '<div class="hd cols"><div>Package</div><div>Scope</div><div>CSI Div</div>'
                   '<div>Scope items</div><div>Subcontractor</div><div class="rt">Value</div>'
                   '<div class="rt" style="padding-right:14px">Bidders</div><div>Award</div></div>')
        out += [pkg_row(p) for p in rows]
        out.append("</section>")
    out.append("</div>")
    return "".join(out)


def panel_specs(d):
    style = {"claimed": ("transparent", "var(--core-green)", "Assigned"),
             "conflict": ("#EDEBFF", "#3B3480", "Conflict — two scope docs claim it"),
             "flow": ("#EEF1F6", "#3A4A5E", "Flow-down — many comply, one carries"),
             "closed": ("#E6F4EC", "#004E2B", "Absent — closed by PM ruling"),
             "overlap": ("#EDEBFF", "#3B3480", "Overlap — claimed twice"),
             "gap": ("#FBEAE9", "#B3261E", "Absent from the manual — open")}
    cols = "grid-template-columns:120px minmax(240px,1fr) minmax(240px,1fr) 200px"
    out = ['<div class="panel panel-specs">',
           '<h2 class="sec">Specification coverage</h2>',
           '<p class="secsub">All 106 technical sections in the manual with the package responsible for each, '
           "plus every section a scope doc cites that the manual does not publish. Basis is stated per section: "
           "a scope-doc citation, a PM ruling, or trade judgment. Trade judgment is an assignment, not a "
           "citation — it is reviewable and is what the PM review packet asks about.</p>",
           f'<div class="card"><div class="hd" style="{cols};background:var(--sect);color:var(--sectFg)">'
           "<div>Section</div><div>Title</div><div>Claimed by</div><div>Coverage</div></div>"]
    for r in d["specCoverage"]:
        bg, fg, lab = style.get(r["state"], ("transparent", "var(--core-green)", r["state"]))
        note = (f'<div class="mut" style="margin-top:4px;font-size:11px">{e(r["note"])}</div>'
                if r.get("note") else "")
        by = ", ".join(r["by"]) if r["by"] else "<em>nobody</em>"
        out.append(f'<div class="hd" style="{cols};background:{bg};text-transform:none;letter-spacing:0;'
                   'font-size:12.5px;font-weight:400;color:var(--core-black);font-family:var(--font-body)">'
                   f'<div style="font-family:var(--font-display);font-weight:900">{e(r["section"])}</div>'
                   f'<div>{e(r["title"])}</div><div class="mut">{by}</div>'
                   f'<div><span class="pill" style="background:#fff;color:{fg};border:1px solid {fg}">{lab}'
                   f"</span>{note}</div></div>")
    out.append("</div></div>")
    return "".join(out)


def panel_leveling(d):
    sev = {"high": ("#FBEAE9", "#B3261E"), "medium": ("#FFF4DB", "#8A6100"),
           "low": ("var(--core-concrete)", "var(--core-asphalt)"),
           "resolved": ("#E6F4EC", "#004E2B")}
    out = ['<div class="panel panel-leveling">', '<h2 class="sec">Leveling register</h2>',
           '<p class="secsub">Open gaps, overlaps and decisions carried by the index artifacts — every entry '
           "traced to the artifact that produced it. Resolved items stay visible so a ruling is never silently "
           "lost.</p>"]
    for l in d["leveling"]:
        bg, fg = sev.get(str(l["sev"]).lower(), sev["low"])
        pk = e(" · ".join(l["pkgs"])) if l["pkgs"] else "—"
        cites = "".join(f'<div class="cite" style="margin:0 16px 12px"><b>{e(k.replace("_"," "))}</b>{e(v)}</div>'
                        for k, v in l["cites"] if v)
        out.append(f"""<article class="card"><div class="cardh">
<span class="pill" style="background:{bg};color:{fg}">{e(str(l['sev']))}</span>
<div style="flex:1"><div style="font-family:var(--font-display);font-weight:900;font-size:14.5px">{e(l['title'])}</div>
<div class="mut" style="margin-top:3px">{pk} <span style="color:var(--core-cement)">· source: {e(l['src'])}</span></div>
</div></div><div class="cardb">{e(l['detail'])}</div>{cites}</article>""")
    out.append("</div>")
    return "".join(out)


def panel_ask(d):
    """Without JS there is no query box, so this panel ships the index it would search."""
    seams = []
    for p in d["packages"]:
        for c in p["coord"]:
            seams.append((p["id"], c))
    out = ['<div class="panel panel-ask">', '<h2 class="sec">Coordination seams</h2>',
           f'<p class="secsub">All {len(seams)} places a scope narrative tells a subcontractor to coordinate '
           "with another trade — the documented boundaries between packages, and where gaps form. With "
           "JavaScript enabled a search box filters these live; the full list is below either way.</p>",
           '<div class="card"><div class="hd" style="grid-template-columns:110px 1fr;background:var(--sect);'
           'color:var(--sectFg)"><div>Package</div><div>Coordination clause</div></div>']
    for pid, c in seams:
        out.append('<div class="hd" style="grid-template-columns:110px 1fr;text-transform:none;letter-spacing:0;'
                   'font-size:12.5px;font-weight:400;color:var(--core-black);font-family:var(--font-body);'
                   'align-items:start">'
                   f'<div style="font-family:var(--font-display);font-weight:900">{e(pid)}</div>'
                   f"<div>{e(c)}</div></div>")
    out.append("</div></div>")
    return "".join(out)


def render(d):
    m = d["meta"]
    tabs = [("packages", "Packages", len(d["packages"])),
            ("specs", "Spec coverage", len(d["specCoverage"])),
            ("leveling", "Leveling register", len(d["leveling"])),
            ("ask", "Coordination seams", sum(p["coordCount"] for p in d["packages"]))]
    radios = "".join(
        f'<input class="tabin" type="radio" name="tab" id="t-{k}"{" checked" if i == 0 else ""}>'
        for i, (k, _, _) in enumerate(tabs))
    labels = "".join(
        f'<label class="tab" for="t-{k}">{e(l)}<span class="n">{n}</span></label>' for k, l, n in tabs)
    t = m["totals"]
    prov = (f'{t["spec_sections_assigned"]} spec sections assigned · '
            f'{t["sheets_draft_from"]} sheet assignments · '
            f'{t["bidders"]} bidder records · '
            f'{t["open_pm_items_attached"]} open PM items attached to packages')
    return f"""<div class="wrap">
<header class="bar">
  <div><h1>CORE&nbsp;·&nbsp;Buy-Out Console</h1>
    <div class="sub">{e(m['project'])} · {e(m['owner'])} · {e(m['delivery'])}</div></div>
  <div style="flex:1"></div>
  <div class="clock"><b>TBD</b><span>30-day buy-out<br>handoff date not set</span></div>
  <div style="text-align:right"><div class="lbl">Bid set of record</div>
    <div style="font-size:12px;font-weight:700">{e(m['bidSet'])}</div></div>
</header>

<div class="feel">
  <span class="tglab">Feel</span>
  <label>Density <select id="density"><option>Command center</option><option selected>Standard</option><option>Briefing</option></select></label>
  <label>Chrome <select id="chrome"><option>Night bar</option><option selected>Field green</option><option>Paper</option></select></label>
  <label>Risk emphasis <select id="risk"><option>Calm</option><option selected>Standard</option><option>Alarm</option></select></label>
  <div style="flex:1"></div><span class="mut">{e(prov)}</span>
</div>

{kpis(d)}
{radios}
<nav class="tabs">{labels}</nav>
<main class="main">
{panel_packages(d)}
{panel_specs(d)}
{panel_leveling(d)}
{panel_ask(d)}
</main>
</div>"""
