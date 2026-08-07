#!/usr/bin/env python3
"""Write the readable release priority list from 01-index/buyout-log.json."""

import json
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOG = ROOT / "01-index" / "buyout-log.json"
OUT = ROOT / "04-output" / "Subcontract Release Priority.md"

d = json.loads(LOG.read_text())
pk = d["packages"]
active = [r for r in pk if r["priority_rank"]]
removed = [r for r in pk if not r["priority_rank"]]

tiers = {}
for r in active:
    tiers.setdefault(r["tier"], []).append(r)

L = []
w = L.append

w("# Subcontract release priority — Tonopah THS Sports Complex")
w("")
w(f"CORE Project No. 26-01-019 · generated {d['_generated']} · "
  f"**{len(active)} packages, ${d['_total_carried']:,.0f} carried**")
w("")
w("Ranked soonest to last. The order is a backward pass through the 04.21.26 "
  "schedule, not a scoring rubric: for each package, the latest date its "
  "subcontract can be issued for signature without pushing the field activity "
  "that needs it. Cost, delegated design, coordination and risk are recorded "
  "against each package and move it up a tier — they never invent urgency the "
  "schedule does not support.")
w("")

# ---- the headline ------------------------------------------------------
w("## The single most urgent package")
w("")
top = active[0]
w(f"**{top['package_id']} — {top['title']}**, {top['carried_sub']}, "
  f"${top['carried_value']:,.0f}.")
w("")
w(f"Release by **{top['latest_release_date']}**, which means the Attachment A "
  f"has to be drafted and through your review by **{top['draft_by']}** — "
  f"{top['draft_slack']} working days from today.")
w("")
w(f"The driver is not the steel. It is the **{top['binding_chain']}**: "
  f"{top['submit_days']} d to prepare + {top['review_days']} d to review + "
  f"{top['procure_days']} d to fabricate + {top['exec_days']} d to execute = "
  f"**{top['chain_days']} working days** back from "
  f"{top['first_field_activity']} on {top['field_need_date']}. That is the "
  "longest single chain on the job, and it is a deferred submittal, so the "
  "review runs through the building official rather than stopping at the "
  "engineer of record.")
w("")
w("A second, earlier obligation sits inside the same package and is easy to "
  "miss: **anchor bolts are needed 2/15/27 for foundations**, two and a half "
  "months before steel erection, and they are embedded in RFP-030's concrete. "
  "Buying this package against the 5/3/27 erection date misses the anchor "
  "bolts entirely.")
w("")

# ---- the schedule reality ---------------------------------------------
w("## Where the buy-out actually stands")
w("")
w("The 04.21.26 schedule allots five days to buy out the whole job — "
  "**ID 19, \"Procure Subcontractor Contracts,\" Tue 7/21/26 to Mon 7/27/26** — "
  "and starts every submittal on 7/28/26. That window closed nine working days "
  "ago with nothing issued, so all 33 packages are behind the plan by the same "
  "nine days.")
w("")
w("What separates them is float. The schedule front-loads submittals so most "
  "packages still have slack against their true field need, which is why the "
  "table below shows working days *remaining*, not days late. Three packages "
  "have already spent most of theirs.")
w("")
w("The binding constraint on recovery is not any one subcontractor's lead "
  "time — it is exhibit throughput. Thirty-two Attachment A's remain to be "
  "written, and the first three have to clear review inside eleven, seventeen "
  "and twenty-seven working days.")
w("")

# ---- tiers -------------------------------------------------------------
for t in sorted(tiers):
    grp = tiers[t]
    w(f"## Tier {t.split(chr(8212))[0].strip()} — {t.split(chr(8212))[1].strip()}"
      f"  ·  {len(grp)} packages, ${sum(r['carried_value'] for r in grp):,.0f}")
    w("")
    w("| # | Package | Subcontractor | Value | Draft by | Release by | Slack | What sets the date |")
    w("|---|---|---|---|---|---|---|---|")
    for r in grp:
        w(f"| {r['priority_rank']} | **{r['package_id']}** {r['title'][:42]} "
          f"| {r['carried_sub']} | ${r['carried_value']:,.0f} "
          f"| {r['draft_by']} | {r['latest_release_date']} | {r['working_days_slack']} d "
          f"| {r['binding_chain']} → {r['first_field_activity']} {r['field_need_date']} |")
    w("")
    for r in grp:
        if not r["other_factors"]:
            continue
        w(f"**{r['package_id']} — {r['title']}**")
        w("")
        w(r["schedule_note"])
        w("")
        for f in r["other_factors"]:
            w(f"- {f}")
        w("")

# ---- things the ranking depends on ------------------------------------
w("## What this ranking depends on, and where it is soft")
w("")
w("### Schedule gaps — $2.6M with no procurement activity at all")
w("")
w("The 04.21.26 schedule procures rebar, CMU, steel, roofing, doors and MEP "
  "equipment. It procures **none of the sports-field products**, which is the "
  "reason this project exists:")
w("")
w("| Package | Carried | Schedule has |")
w("|---|---|---|")
gaps = [("RFP-022", "Synthetic turf"), ("RFP-021", "Track surfacing"),
        ("RFP-016", "Landscape & irrigation"), ("ITB-019", "Track & field equipment"),
        ("RFP-023", "Fencing & gates"), ("ITB-089", "Scoreboard"),
        ("RFP-109", "Ticket booth")]
by_id = {r["package_id"]: r for r in pk}
tot = 0
for pid, name in gaps:
    r = by_id[pid]
    tot += r["carried_value"]
    has = ("submittal only (ID 39, Sports Field Product Data)" if pid == "RFP-022"
           else "nothing")
    w(f"| {pid} {name} | ${r['carried_value']:,.0f} | {has} |")
w(f"| | **${tot:,.0f}** | |")
w("")
w("Their release dates above are computed from trade judgment, not from the "
  "schedule, and every one is labeled `judgment` in the workbook. **The turf "
  "lead time is the one worth confirming with the manufacturer this week** — "
  "$1,139,000 of made-to-order product whose only schedule presence is a "
  "20-day product-data submittal, and a late turf order cannot be recovered by "
  "adding crews.")
w("")
w("### Two stale lines still on the procurement critical path")
w("")
w("The schedule submits and procures **fire alarm** (80 d) and **fire "
  "sprinkler** (20 d) material. Fire alarm is an express GMP Exclusion per your "
  "08.04.26 ruling and fire suppression is carried N/A at $0. Neither is a bid "
  "package. They should come off the schedule so they stop consuming attention "
  "that RFP-103 needs.")
w("")
w("### Grouping decisions that move dates")
w("")
w("**Applied** — the Jetstream agreement. Your 08.06.26 D ruling puts RFP-060, "
  "ITB-044, ITB-062 and ITB-077 under one agreement with four separate "
  "exhibits. An agreement cannot issue in pieces, so all four now carry "
  "RFP-060's date of "
  f"{by_id['RFP-060']['latest_release_date']}, pulling ITB-044 and ITB-077 "
  "forward from 2027-04-13 and ITB-062 from 2027-04-06.")
w("")
w("**Not applied, needs your call** — three vendors hold more than one package "
  "and I did not assume how you want them papered:")
w("")
w("| Vendor | Packages | Earliest member | If one agreement, all move to |")
w("|---|---|---|---|")
for kind, label, members in [("v", "Exerplay", ["ITB-018", "ITB-019"]),
                             ("v", "YESCO", ["ITB-072", "ITB-078", "ITB-089"]),
                             ("v", "US Mechanical", ["RFP-098", "RFP-100"])]:
    ms = [by_id[m] for m in members]
    e = min(m["latest_release_date"] for m in ms)
    w(f"| {label} | {', '.join(members)} | {e} | {e} |")
w("")
w("YESCO is the one that matters: ITB-089 Scoreboards is ranked 5th at "
  "2026-10-19 while ITB-072 Building Signage sits at 2027-04-12. One agreement "
  "pulls all three to October.")
w("")

# ---- excluded ----------------------------------------------------------
w("## Not in this log")
w("")
for r in removed:
    w(f"- **{r['package_id']} {r['title']}** — {r['schedule_note']}")
w("- **CORE self-perform and general conditions** — GEN1 temporary construction "
  "requirements $57,630, GEN2 equipment $58,000, GEN3 waste management and "
  "cleaning $83,545, and #104 temporary power and lighting $2,550. Together "
  "$201,725, which is exactly the difference between this log's $9,675,291 and "
  "the GMP BackSheet subtotal of $9,877,016.")
w("- Contingency, allowances, insurance and bonds.")
w("")
w("## Authority")
w("")
w("- **Subcontractor and value:** GMP R2 `BackSheet`, rows 16–146. This is "
  "where the GMP's money actually lands. It is *not* the 05.12.26 bid "
  "tabulation, which is a transcription and is known to reverse RFP-008's two "
  "low rows, and it is *not* `awarded-sub-mapping.json`, which predates the "
  "GMP. Reading the BackSheet corrected four packages: ITB-077 is Jetstream "
  "(not Henri), RFP-103 is Quantum Electric, ITB-067 is Ryerson, and RFP-094 "
  "and RFP-109 are both carried rather than unawarded.")
w("- **Dates:** 05.7 Preliminary Construction Schedule (04.21.26), read at "
  "activity level, cross-checked against the 05.29.26 GMP schedule milestones.")
w("- **Risk items:** `01-index/pm-open-items.json`.")
w("- **Working days** are Monday–Friday. Holidays are not modeled — the "
  "schedule does not publish its calendar, and adding one would be inventing "
  "precision. Every date here is therefore slightly optimistic.")

OUT.write_text("\n".join(L) + "\n")
print(f"wrote {OUT.relative_to(ROOT)}  ({len(L)} lines)")
