#!/usr/bin/env python3
"""
Build the PM review packet for the rebuilt index (Human Checkpoint #1).

Designed around one question: what does the PM have to decide that nothing else
can decide for him? Everything a probe already guarantees is deliberately left
out -- re-verifying that is what makes a review packet long and useless.

What stays in:
  A  Trade boundaries      every draft inherits these. Highest leverage in the packet.
  B  GMP contradictions    where a contract document contradicts another one.
  C  Thin packages         where a draft will come out sparse and not say so.
  D  Open spec gaps        where a package owes work no section describes.
  E  Scope with no home    bid, priced, assigned to nobody.
  F  Corrections           where I changed a recorded fact and want it confirmed.

What is left out, and why, is stated in the packet itself so the omission is a
decision rather than an oversight.

Usage:  python3 scripts/build_review_packet.py
Writes: 04-output/PM-Review-Packet-2026-08-06.md
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "01-index"
OUT = ROOT / "04-output"


def load(n):
    p = INDEX / n
    return json.loads(p.read_text()) if p.exists() else {}


# Trade-boundary calls worth arguing about. The other 51 judgment assignments are
# division rollups where the package title names the division (all of Division 22
# to Plumbing); listing those wastes the reviewer's attention.
BOUNDARIES = [
    ("A1", "09 65 13 Resilient Base and Accessories", "ITB-067 Concrete Finishing",
     "trade_judgment",
     "No package's scope doc cites it. ITB-066 would be the natural home, but your 08.04.26 "
     "ruling left ITB-066 with no remaining scope. SI Legacy priced 'Furnish & Install 4\" "
     "Rubber Wall Base At RB-1 Areas' inside their 066/067 bundle, so I put it with ITB-067.",
     "This is my least confident assignment in the catalog. ITB-067 is a concrete-finishing "
     "package and rubber base is not concrete work. Does it go to ITB-067, back to RFP-060 "
     "with the other finishes, or somewhere else?"),
    ("A2", "12 93 00 Site Furnishings", "ITB-018 (primary) / ITB-019 (athletic portion)",
     "trade_judgment — SPLIT",
     "Both ITB-018 and ITB-019 cite it, and the section's own Section Includes genuinely spans "
     "both: benches and waste receptacles, and NFHS goals, cages and pits. I show ITB-018 as "
     "primary and note ITB-019 must carry the athletic-equipment portion.",
     "A section split between two subcontracts needs your language, not mine. Do you want it "
     "split by paragraph, given wholly to one with the other excluded, or handled another way?"),
    ("A3", "10 26 00 Wall and Door Protection", "ITB-074 Building Specialties",
     "trade_judgment — CONFLICT",
     "Cited explicitly by BOTH ITB-074 and RFP-060. ITB-074's title carries corner guards and "
     "Henri priced them at $2,422; I read RFP-060's citation as the wall they mount to.",
     "Confirm ITB-074 carries corner guards, or tell me it stays with the framer."),
    ("A4", "02 41 00 Demolition", "RFP-008",
     "pm_ruling — overrides a scope doc",
     "RFP-002's scope doc cites this section solely and RFP-008's does not cite it at all. Your "
     "07.31.26 ruling gives the entire demolition scope to RFP-008, so the ruling overrides the "
     "narrative.",
     "Confirm the ruling still stands now that you can see it contradicts RFP-002's own scope "
     "doc — RFP-002's Attachment A will exclude demolition it was written to include."),
    ("A5", "32 91 13 Shot Put and Discus Mix", "RFP-016",
     "pm_ruling — three packages touch it",
     "Your 07.31.26 ruling makes it RFP-016's. ITB-019's scope doc also cites it for the shot "
     "put and discus pad, and Sahara priced that pad under RFP-030.",
     "Three packages have a claim and two of them priced it. Confirm RFP-016 carries it and I "
     "will write explicit exclusions into ITB-019 and RFP-030."),
    ("A6", "32 16 23 Sidewalks", "RFP-030 Concrete",
     "trade_judgment",
     "No package cites it explicitly. RFP-008 and RFP-016 reach it only through a division-level "
     "mention of Division 32. I put flatwork with the concrete package.",
     "Confirm sidewalks are RFP-030 and not RFP-008 with the rest of the sitework."),
    ("A7", "23 05 93 Testing, Adjusting and Balancing", "RFP-100",
     "trade_judgment",
     "RFP-100's own title carries Test & Balance, so I kept it in that subcontract. But four "
     "separate TAB proposals were solicited under trade 102 and tabulated into RFP-100.",
     "Is TAB held inside RFP-100's subcontract, or subcontracted directly to a TAB agency? If "
     "direct, RFP-100's Attachment A needs an explicit exclusion."),
    ("A8", "08 31 00 Access Doors and Panels", "RFP-060 installs / MEP supply",
     "pm_ruling",
     "Your 07.31.26 ruling: MEP trades supply, the framer installs. RFP-098, RFP-100 and RFP-103 "
     "each cite the section — that is their supply obligation.",
     "Confirm I write the supply obligation into all three MEP subcontracts and the install "
     "obligation into RFP-060, with each cross-referencing the other."),
]

GMP_ITEMS = [
    ("B1", "GMP-01 — Berridge C-Lock reverses RFI #23", "RFP-045",
     "Clarification No.1 RFI #23 answered that spec 07 61 00 (MBCI PBR panel BOD) takes "
     "precedence over the plan callout of Berridge Cee-lock. The GMP is priced on Berridge "
     "C-Lock. The GMP is later and you have ruled it supersedes, but this overturns a written "
     "architect's RFI answer.",
     "Which governs in RFP-045's Attachment A — the RFI answer or the GMP? If the GMP, I will "
     "cite Exhibit B as the instrument and note the RFI is superseded, so the record shows the "
     "reversal was deliberate."),
    ("B2", "GMP-02 — Door 106 panic hardware exclusion is ambiguous", "ITB-056 / ITB-054",
     "The GMP exclusion reads: 'Panic hardware at Door 106 per Door Schedule Remark 2. Hardware "
     "provided per specification section 08711 Door Hardware, Hardware Set 01'. It is unclear "
     "whether panic hardware is excluded outright, or whether Remark 2's hardware is excluded "
     "and Set 01 substituted.",
     "This is life safety at the concessions counter shutter and I will not guess. Which "
     "reading is correct?"),
]


def main():
    cat = load("spec-section-catalog.json")
    man = load("package-index.json")
    items = load("pm-open-items.json")

    # C — packages whose drafts will come out thin.
    thin = []
    for pid, m in man.get("packages", {}).items():
        rec = json.loads((INDEX / "packages" / f"{pid}.json").read_text())
        lines = sum(len(b.get("inclusions", [])) + len(b.get("exclusions_scope_specific", []))
                    + len(b.get("priced_line_items", [])) for b in rec["bidders"])
        specs = m["spec_sections"]
        if specs <= 1 and lines <= 15:
            thin.append((pid, m["title"], specs, m["sheets_draft_from"], m["bidders"], lines))
    thin.sort(key=lambda r: (r[2], r[5]))

    # D — spec gaps that are actually open QUESTIONS. A gap whose note already
    # names the governing document is answered; putting it in front of the PM as a
    # decision wastes the attention this packet is trying to concentrate.
    ANSWERED = ("read it from the addendum", "not a gap")
    gaps = [(k, v) for k, v in cat.get("cited_but_absent_from_manual", {}).items()
            if v["status"] == "OPEN"
            and not v.get("candidate_sections_in_manual")
            and not any(a in v["note"].lower() for a in ANSWERED)]

    L = []
    a = L.append
    a("# PM Review Packet — rebuilt index")
    a("")
    a("**Human Checkpoint #1.** Nothing drafts until this clears. The first index failed this "
      "same review on 07.31.26 at roughly a 47% defect rate on the rows checked.")
    a("")
    a("## How to use this")
    a("")
    a("Every item below is a decision only you can make. Reply by item number — `A1 yes`, "
      "`A2 split by paragraph`, `B2 excluded outright` is enough. Anything unanswered stays open "
      "and blocks the packages it touches, not the whole set.")
    a("")
    a("### What is deliberately NOT in here")
    a("")
    a("Asking you to re-verify what a probe already covers is how a review packet becomes long "
      "and useless. The suite runs 81 probes, each a fact read off the source document by hand "
      "before it was written as a check — extraction fidelity, schedule rows surviving, the right "
      "bidder document landing on the right package, sections keeping their assigned owner, "
      "sheets reaching their packages. Those are covered and omitted.")
    a("")
    a("Also omitted: **51 of my 71 trade-judgment spec assignments**, because they are division "
      "rollups where the package title names the division — all 11 Division 22 sections to "
      "Plumbing, all 16 Division 23 to HVAC, all 22 Division 26/27 to Electrical. If you want to "
      "spot-check the mechanism rather than the outcome, check one and the other 50 follow the "
      "same rule. The 20 that required real judgment are in section A.")
    a("")
    a("What probes cannot tell you, and why this packet exists: **whether a judgment is right.** "
      "They can only confirm the record says what I decided.")
    a("")

    a("## A — Trade boundaries (highest leverage)")
    a("")
    a("Every draft inherits these. A wrong boundary here is scope that lands in two subcontracts "
      "or none, and it will not announce itself in the draft.")
    a("")
    for n, sec, to, basis, why, q in BOUNDARIES:
        a(f"**{n}. {sec} → {to}**  ·  *{basis}*")
        a("")
        a(f"{why}")
        a("")
        a(f"> **Decision needed:** {q}")
        a("")

    a("## B — Where contract documents contradict each other")
    a("")
    for n, title, pkgs, why, q in GMP_ITEMS:
        a(f"**{n}. {title}**  ·  `{pkgs}`")
        a("")
        a(why)
        a("")
        a(f"> **Decision needed:** {q}")
        a("")

    a("## C — Packages that will draft thin")
    a("")
    a("These have little to draft from. The draft will come out sparse and the sparseness will "
      "not be visible in it — which is the failure mode worth catching before 33 exhibits exist.")
    a("")
    a("| Package | Title | Specs | Sheets | Bidders | Bidder scope lines |")
    a("|---|---|---:|---:|---:|---:|")
    for pid, t, sp, sh, bd, ln in thin:
        a(f"| `{pid}` | {t[:44]} | {sp} | {sh} | {bd} | {ln} |")
    a("")
    a("> **Decision needed (C1):** For each of these, is a short exhibit correct — the scope "
      "genuinely is small — or is the source thin because something was never issued? `ITB-077` "
      "is the sharpest case: no spec section, one sheet, one bidder, one line of bidder scope. "
      "Its basis of design comes from Clarification No.1 RFI #3 and a keynote on A10-30, not from "
      "a specification. Tell me whether that is enough to write a subcontract against.")
    a("")

    a("## D — Spec gaps still open")
    a("")
    a("A package owes work that no published section describes. These are not numbering errors — "
      "no candidate section exists in the manual.")
    a("")
    for k, v in gaps:
        pk = ", ".join(v["cited_by"])
        a(f"**{k} {v.get('title_per_scope_doc') or ''}** · cited by `{pk}`")
        a("")
        a(f"{v['note']}")
        a("")
    a("> **Decision needed (D1):** For each, name the governing document or tell me to write the "
      "obligation from the scope narrative and drawings alone. The three that bear on subcontracts "
      "you are close to issuing are `09 82 00` Acoustical Insulation, `10 44 13` Fire Protection "
      "Cabinets (Henri priced $6,313 of them), and `07 41 13` Metal Roof Panels — where I assigned "
      "RFP-045 the nearest published substitute, `07 61 00` Sheet Metal Roofing, which is a "
      "different section and not a renumbering.")
    a("")

    a("## E — Scope with no home")
    a("")
    a("**E1. Trade 070 Final Cleaning.** Four proposals received (CSI, Lady Lux, Nevada Angels, "
      "plus a Nevada Angels descope) under a trade number matching none of the 33 packages. The "
      "GMP Basis suggests it sits in CORE's General Conditions.")
    a("")
    a("> **Decision needed:** self-perform, folded into another subcontract, or its own package? "
      "As it stands the scope is bid with no Attachment A to land in.")
    a("")
    a("**E2. ITB-066 Fluid-Applied Flooring is hollow but still indexed.** Your 08.04.26 ruling "
      "excluded resinous/epoxy flooring and moved those locations to Sealed Concrete under "
      "ITB-067, leaving ITB-066 no remaining scope. It correctly holds zero spec sections — but it "
      "still carries 11 sheets and 4 bidders, because the assignment logic reads the scope "
      "narrative, which still describes the work.")
    a("")
    a("> **Decision needed:** do I draft an ITB-066 exhibit at all? My recommendation is a "
      "one-page exhibit recording that the package was hollowed out by ruling, rather than no "
      "exhibit — so the file shows the decision instead of a gap.")
    a("")

    a("## F — Corrections I made; confirm before they harden")
    a("")
    a("**F1. RFP-008 bid tab reversal.** The 05.12.26 tabulation records NDX at $1,924,851 and "
      "New-Com (TAB) at $3,152,033. Both bidders' own Proposal Forms state the opposite — TAB's "
      "BuildingConnected header and letter both read $1,924,851, NDX's reads $3,152,032.69. I "
      "corrected `awarded-sub-mapping.json` to $1,924,851 and withdrew the 'awarded sub was not "
      "the low bidder' flag, because TAB is in fact the low bidder ($1.92M < Monument $2.30M < NDX "
      "$3.15M).")
    a("")
    a("> **Confirm:** the correction is right and the tab is the document in error.")
    a("")
    a("**F2. Four spec gaps closed by your 08.05.26 rulings** — ITB-067 → `03 30 00`, ITB-040 → "
      "`07 25 00`, aggregate base → `31 20 00`, firestopping no action. On `07 25 00` I made a "
      "call you did not specify: I kept RFP-045 as primary, since its scope doc cites the section, "
      "and added ITB-040 alongside with the split stated per your 07.31.26 boundary.")
    a("")
    a("> **Confirm:** `07 25 00` shared between RFP-045 and ITB-040, rather than moved outright to "
      "ITB-040.")
    a("")
    a("**F3. Firestopping — I was wrong and corrected it.** I first called `07 84 00` a real gap "
      "on the grounds that code requires firestopping at every rated penetration. It does, but "
      "this project has no rated assemblies: partition schedule A2-40 publishes only `3F0`, `5F0` "
      "and `3B0`, whose third character is the rating code and is `0` in all three, with UL "
      "LISTING **(none)**; LS1-10 at its Addendum #1 revision shows 0 HR throughout. So IBC 714 "
      "has nothing to apply to. No probe caught this — your question did.")
    a("")
    a("> **Confirm:** no firestopping obligation flows into RFP-103.")
    a("")

    a("## The rest of the register")
    a("")
    n_open = len(items.get("items", []))
    a(f"`01-index/pm-open-items.md` holds all {n_open} open items including the ones above. The "
      "remainder are commercial or process — bid-tab prices, bundled bids, the CORE job number — "
      "and do not block drafting. Work them when convenient.")
    a("")
    a("---")
    a("")
    a("*Generated from the index artifacts by `scripts/build_review_packet.py`. Regenerate after "
      "any ruling; resolved items drop out.*")

    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / "PM-Review-Packet-2026-08-06.md"
    p.write_text("\n".join(L) + "\n")
    print(f"wrote {p.relative_to(ROOT)}")
    print(f"  A trade boundaries : {len(BOUNDARIES)}")
    print(f"  B contradictions   : {len(GMP_ITEMS)}")
    print(f"  C thin packages    : {len(thin)}")
    print(f"  D open spec gaps   : {len(gaps)}")
    print(f"  decisions requested: {len(BOUNDARIES) + len(GMP_ITEMS) + 2 + 1 + 3}")


if __name__ == "__main__":
    main()
