# Attachment A Index — PM Review Packet (v2)

Generated 2026-07-31 from `01-index/package-index-v2.json` and companions. Everything below is pulled from the artifacts, not retyped.

**How to use:** Part A gates everything else and takes minutes. Part B is decisions only you can make. Part C is a content spot-check to confirm the parse is faithful. Stop wherever you like — the parts are ordered by leverage.

---

## Part A — Three structural decisions (answer these first)

These decide the shape of all 33 exhibits. If any is wrong, everything downstream is rework, so they're worth your time before you look at content.

### A1. Verbatim scope items vs. summarized

The index stores each scope doc's own sentences, unedited — 1,139 of them across 33 packages. Nothing is paraphrased, so nothing can drift from the contract language. The cost is bulk: RFP-103 alone carries 134 lines.

Sample, RFP-030 Concrete, exactly as stored:

> Supply and install concrete curbs at Synthetic Turf Sports Field and Running Track.

> Supply and install slot drain / trench drains and concrete curb along track perimeter and as indicated per detail D/L1.03, including all excavation, trenching, bedding, and backfill.

> Includes all piping, radius slot drains, storm drain collector pipe, concrete encasements as required, cleanouts, and all storm water drainage structures as indicated and required for a complete slot drain storm drainage system.

**Decide:** keep verbatim, or have me condense to a shorter scope statement per package?

- ☐ Keep verbatim  ☐ Condense  ☐ Both (verbatim retained, condensed summary added)

### A2. Coordination clauses as the gap-check spine

I pulled every sentence where a scope doc tells a sub to coordinate with another trade — 134 of them. These are the documented seams between packages, and my plan is to build the gap/overlap QA around them rather than around CSI divisions.

Sample, RFP-030 (14 clauses total):

> Scoreboard footings. Coordinate with Scoreboard Subcontractor for requirements.

> Pressbox footings. Coordinate with Pressbox Subcontractor for requirements.

> Prefabricated Ticket Booth slab-on-grade and footings. Coordinate with Ticket Booth Subcontractor for requirements.

**Decide:** are these the right seams to check gaps against?

- ☐ Yes, build QA on these  ☐ No, use a different basis  ☐ Use these plus something else

### A3. Drawings as candidates, not assignments

Only **6** drawing citations are treated as authoritative — the sheets a scope narrative names outright. The other **148** sheet associations from the old vision pass are carried as *candidates*, flagged as not corroborated by any scope doc, because assignment-from-drawings is what you rejected. A candidate only becomes a citation if a scope doc, spec, or your ruling backs it.

This is deliberately conservative. It may mean a package's exhibit cites fewer sheets than you'd expect.

**Decide:** right level of caution, or should candidates be promoted where the content is obvious?

- ☐ Keep conservative  ☐ Promote obvious ones  ☐ Promote all, flag the doubtful

---

## Part B — Open decisions (only you can settle these)

### B1. [HIGH] Three packages have no specification from any source

ITB-008 Surveying, ITB-066 Fluid-Applied Flooring, RFP-109 Ticket Booth have no 'Primary Specifications' section in their scope docs — verified against source text. ITB-066 also has no matching CSI section in the spec manual, so it has no execution standard anywhere. RFP-109's substitute is the written spec block on sheet A1-40.

**Decision needed:** What governs execution for each?

> 

### B2. [HIGH] '070 Final Cleaning' — four proposals, no package

CSI, Lady Lux, and Nevada Angels (plus a descope) bid a package numbered 070 Final Cleaning. No such package exists on either the 1% or ITB list.

**Decision needed:** Is this a 34th package, a CORE general-conditions scope, or folded into another package?

> 

### B3. [HIGH] Prevailing wage — Clark County vs Nye County

Clarification No. 2 replaced the prevailing wage section entirely and directs bidders to CLARK County rates. The project is in Nye County; CLAUDE.md records Southern Nevada Rural Region. Affects all 33 subcontracts as a direct cost and compliance item.

**Decision needed:** Which rate schedule governs?

> 

### B4. [MEDIUM] '065 Sealed Concrete' straddles ITB-066 and ITB-067

Sealed concrete appears under filename numbers 065, 066, 067 and combined '066, 067'. Both packages currently show the identical four bidders (FW Specialties, NRC, Ryerson, SI Legacy).

**Decision needed:** Which package carries sealed concrete?

> 

### B5. [MEDIUM] Supply-only vs install-only bids split several packages

ITB-019: Exerplay and SportsEdge bid SUPPLY, Great Western bid INSTALL. ITB-056: Hallgren SUPPLY, SNV Specialties INSTALL. RFP-094 and RFP-109 received SUPPLY-only proposals — but sheet A1-20's Site Equipment Matrix designates Bleachers, Press Box and Ticket Booth as CFCI (contractor furnished, contractor installed).

**Decision needed:** For each split package, which package carries installation?

> 

### B6. [MEDIUM] Procurement flags on proposals

15 proposals have no signed Bid Form, 5 are late, 2 bypassed Building Connected, 2 are marked DO NOT USE, 1 is value-only with no scope detail (Conti, RFP-103). RFP-045's awarded sub Foursquare carries both the no-Form and bypassed-BC flags. NRS 338.16995 governs the 1% list.

**Decision needed:** Any of these block subcontract execution?

> 

### B7. [MEDIUM] 32 91 13 leveling exposure on RFP-016

Your ruling put Section 32 91 13 Track & Field Event Inorganic Material Mix (the discus/shot put material) in RFP-016. BrightView/GTI's scope review explicitly EXCLUDED 'discuss and shot put pads'. Awarded sub is Black Canyon.

**Decision needed:** Confirm Black Canyon carries 32 91 13.

> 

### B8. [LOW] Addendum #1 change list disagrees with the revised drawing index

The addendum's narrative §5.01 names five reissued sheets. The revised G0-00 drawing index marks seven, adding A2-10 and A10-30 — both of which carry real scope changes.

**Decision needed:** Worth raising with KNIT? Should the subcontract state that G0-00's index governs current revisions?

> 

### B9. [LOW] Two project facts still unconfirmed

CORE job number recorded as 'likely 25-10-003'. Precon→Ops handoff date, which starts the 30-day buyout clock, is still TBD.

**Decision needed:** Confirm both.

> 

---

## Part C — Content spot-check (confirm the parse is faithful)

Four packages, chosen because they carry the most boundary surface or your recent rulings. For each, open the scope doc listed and confirm the index didn't lose or distort anything.

### RFP-030 — Concrete

- **Open:** `00-source-docs/02-trade-scopes-bidform/Scope of Work - 030 Concrete.docx`
- Scope items captured: **72** · coordination clauses: **14** · alternates: **1**
- Primary specs: 07 26 00 Vapor Retarders, 32 13 13 Concrete Paving, 32 13 73 Concrete Paving Joint Sealants
- Primary divisions: Div 03 Concrete
- Bidders on file: 4 (Cheek Construction, Monument Co, Sahara Concrete, XL Concrete Masonry)

| Check | Verdict |
|---|---|
| Scope items complete and undistorted | ☐ OK ☐ Missing items ☐ Distorted |
| Primary specs correct | ☐ OK ☐ Wrong ☐ Incomplete |
| Alternates complete | ☐ OK ☐ Missing |

### RFP-008 — Site Clearing, Demo, Earthwork, Asphalt Paving, &

- **Open:** `00-source-docs/02-trade-scopes-bidform/Scope of Work - 008 Demo, Earthwork, Paving, Utilities, & Striping.docx`
- Scope items captured: **102** · coordination clauses: **8** · alternates: **3**
- Primary specs: 02 41 13 Selective Site Demolition, 32 12 16 Asphalt Paving
- Primary divisions: Div 31 Earthwork, Div 33 Utilities
- Bidders on file: 3 (Monument Co, NDX, NewCom TAB)

| Check | Verdict |
|---|---|
| Scope items complete and undistorted | ☐ OK ☐ Missing items ☐ Distorted |
| Primary specs correct | ☐ OK ☐ Wrong ☐ Incomplete |
| Alternates complete | ☐ OK ☐ Missing |

### ITB-077 — Lockers

- **Open:** `00-source-docs/02-trade-scopes-bidform/Scope of Work - 077 Lockers.docx`
- Scope items captured: **15** · coordination clauses: **3** · alternates: **0**
- Primary specs: 10 51 13 Metal Lockers
- Primary divisions: —
- Bidders on file: 1 (IISI)

| Check | Verdict |
|---|---|
| Scope items complete and undistorted | ☐ OK ☐ Missing items ☐ Distorted |
| Primary specs correct | ☐ OK ☐ Wrong ☐ Incomplete |
| Alternates complete | ☐ OK ☐ Missing |

### RFP-016 — Landscaping & Irrigation

- **Open:** `00-source-docs/02-trade-scopes-bidform/Scope of Work - 016 Landscaping & Irrigation.docx`
- Scope items captured: **26** · coordination clauses: **2** · alternates: **2**
- Primary specs: 32 84 00 Landscape Irrigation, 32 91 13 Track & Field Event Inorganic Material Mix, 32 96 50 Invasive Plant Removal
- Primary divisions: Div 32 Exterior Improvements (as pertains to this scope of work)
- Bidders on file: 3 (Black Canyon, BrightView, Tand)
- **Your rulings applied:** 1
  - RFP-016 carries primary spec sections 32 84 00, 32 91 13 and 32 96 50.

| Check | Verdict |
|---|---|
| Scope items complete and undistorted | ☐ OK ☐ Missing items ☐ Distorted |
| Primary specs correct | ☐ OK ☐ Wrong ☐ Incomplete |
| Alternates complete | ☐ OK ☐ Missing |

---

## Part D — What I know is still missing

The coverage audit found **42 files never opened**, 17 of them high impact. I recommend closing six before you review content — but you're seeing this list either way so nothing is hidden.

| File | What it blocks |
|---|---|
| `02.0 - Subcontractor Proposal (Bid) Form (1%).pdf` | Defines the bid line items and alternate structure every exhibit must mirror. package-index-v2.json currently  |
| `Subcontractor Proposal (Bid) Form (1%).pdf` | (same as above) |
| `04.02 - Geotech Report 012125.pdf` | Scope narratives reference the Geotechnical Report 25 times (backfill, hard dig, caliche, compaction). Drives  |
| `04.03 - Asbestos Survey_EICS 100323.pdf` | Defines the actual abatement scope for RFP-002. Never opened. |
| `04.04 - Asbestos Mgmt Plan & Inspection Reports_EISC 01042` | (same as above) |
| `05.7 - Preliminary Construction Schedule (04.21.26).pdf` | Scope docs bind subs to these by reference ('multiple mobilizations per the Preliminary Construction Schedule  |
| `Logistics Plan Template.pdf` | (same as above) |
| `001_Attach A_PA DS Template_04-03-25.docx` | The Attachment A and B templates -- the output format for Stage 7. Never opened. |
| `002_ Attach A_ Subcontract DS Template_05-09-25.docx` | (same as above) |
| `NV_Attach A Review Log Cover Bluebeam Template_11-14-25.xl` | (same as above) |
| `PrePreparatory Phase Checklist.docx` | (same as above) |
| `NV Attach B_Consultant DS Template  07-11-16.pdf` | (same as above) |
| `NV Attach B_Subcontract Gen Prov DS TEMPLATE_01.28.23.pdf` | (same as above) |
| `ACO Sport - System 3000 Slot Channel Trench Drain System S` | Product basis-of-design cut sheets tied to specific packages: ACO Sport trench drain (RFP-030), discus cage /  |
| `DCHS-35BN Discuss Cage.pdf` | (same as above) |
| `Pole Vault.pdf` | (same as above) |
| `SEF305P Goal Post.pdf` | (same as above) |

**My recommendation:** close the Bid Form (a regression — v1 had `bid_form_line_items`, v2 lost it) and the four cut sheets now. Defer the Attachment A/B templates (Stage 7 output format, not index input) and read geotech/asbestos while drafting the specific packages they govern.
