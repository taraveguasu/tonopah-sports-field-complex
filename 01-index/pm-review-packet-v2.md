# Attachment A Index — PM Review Packet (v2)

Generated 2026-07-31 from `01-index/package-index-v2.json` and companions. Everything below is pulled from the artifacts, not retyped.

**How to use:** Part A gates everything else and takes minutes. Part B is decisions only you can make. Part C is a content spot-check to confirm the parse is faithful. Stop wherever you like — the parts are ordered by leverage.

---

## Part A — Three structural decisions (answer these first)

These decide the shape of all 33 exhibits. Every option below is worked out using **RFP-030 Concrete**
so you are comparing like with like, not choosing from a description.

---

### A1. How scope items are stored

RFP-030's scope doc contains **72 items** across three sub-scopes (Site Concrete, Cast-in-Place
Structural, General Requirements).

#### Option 1 — Verbatim (what the index does today)

Every sentence stored exactly as written, unedited. Sample of 5 of the 72:

> Supply and install slot drain / trench drains and concrete curb along track perimeter and as indicated per detail D/L1.03, including all excavation, trenching, bedding, and backfill.
>
> Dowel all exterior sidewalks to the building slab at entrances and doorways, whether or not detailed on drawings.
>
> Provide and install 5/8" diameter x 18" long slick dowels at 18-inches on center (minimum) at all cold joints, whether shown or not.
>
> Athletic Equipment footings (including football goal posts, high jump posts, etc.) Coordinate with Track & Field Athletic Equipment Subcontractor for requirements.
>
> Includes sacking exposed concrete surfaces, drypack under light pole base plates, and installing anchor bolts furnished by others. Anchor bolt templates will be supplied by Electrical.

**Length:** 72 lines. **Traceability:** every line quotable back to the scope doc verbatim.

#### Option 2 — Summarized

Same scope, condensed to prose. This is what RFP-030's Site Concrete sub-scope would look like —
I wrote this from the 24 verbatim items, losing nothing material:

> **Site Concrete.** Supply and place concrete and reinforcement for all site flatwork, athletic
> equipment pads, curbs, take-off boards, turndown edges, and associated concrete items, including
> layout. Concrete curbs at the Synthetic Turf Sports Field and Running Track. Slot/trench drains and
> concrete curb along the track perimeter per detail D/L1.03, including excavation, trenching, bedding,
> backfill, all piping, radius slot drains, storm drain collector pipe, concrete encasements, cleanouts,
> and storm water drainage structures — connection to the site storm drainage system by others.
> Equipment pads including transformer pad. Keyed, saw-cut, control and expansion joints with filler,
> sealants, and white cap; control joint layout shop drawings for architectural approval. Dowel exterior
> sidewalks to the building slab at all entrances and doorways whether or not detailed, and provide
> 5/8" x 18" slick dowels at 18" o.c. minimum at all cold joints whether shown or not. Cast-in-place
> footings for site items including overexcavation per the Geotechnical Report: scoreboard, pressbox,
> ticket booth slab-on-grade and footings, bleacher footings and grade beams, athletic equipment
> footings (football goal posts, high jump posts), and sports field light pole bases — coordinating
> requirements with each respective subcontractor. Sacking of exposed surfaces, drypack under light pole
> base plates, and installation of anchor bolts furnished by others (templates by Electrical). Install
> steel embeds and bollards supplied by others, with footings, concrete infill and domed tops. Supply
> Type II, prepare sub-base, place and compact.

**Length:** ~1 paragraph per sub-scope, so roughly 3 paragraphs for RFP-030 instead of 72 lines.

**What you give up:** you can no longer cite one sentence and point at it in the scope doc. Merging
sentences also blurs boundaries — note how "whether or not detailed on drawings" and "whether shown or
not" now sit mid-paragraph, when verbatim they stand out as the deliberate catch-all provisions they are.

#### Option 3 — Both

Verbatim retained in the index as the source of record; condensed prose generated into the exhibit.
Costs nothing but a generation step, and the exhibit reads cleaner while the index stays quotable.

**Decide:** ☐ Verbatim only  ☐ Summarized only  ☐ Both (verbatim in index, condensed in exhibit)

---

### A2. What gap/overlap QA is built on

#### Option 1 — Coordination clauses (what I proposed)

RFP-030's scope doc names **14 coordination clauses**. Each one names a counterparty, so each becomes
a specific checkable question:

| RFP-030 says | Seam to check | Counterparty |
|---|---|---|
| "Scoreboard footings. Coordinate with Scoreboard Subcontractor" | Does ITB-089 exclude its own footings? | ITB-089 |
| "Pressbox footings… Bleacher footings / grade beams" | Does RFP-094 exclude footings? | RFP-094 |
| "Prefabricated Ticket Booth slab-on-grade and footings" | Does RFP-109 exclude slab and footings? | RFP-109 |
| "Athletic Equipment footings (football goal posts, high jump posts)" | Does ITB-019 exclude footings? | ITB-019 |
| "installing anchor bolts furnished by others… templates supplied by Electrical" | Who furnishes vs installs? | RFP-103 |
| "Install all steel embeds (supplied by others)… all bollards (supplied by others)" | Who supplies? | RFP-033 |
| "Coordinate required masonry laps… rebar safety caps until Masonry assumes responsibility" | Handoff point | RFP-031 |
| "sleeves in slab-on-grade" / "layout requirements" | Sleeve and layout responsibility | RFP-098, RFP-100, RFP-103 |

→ **8 distinct counterparties, 8 concrete questions**, each traceable to a sentence in the contract.

#### Option 2 — CSI divisions

RFP-030 is Division 03 Concrete. Checking overlaps by division finds packages that also claim Div 03:

| Package | Div 03 relationship |
|---|---|
| ITB-067 Concrete Finishing | claims Division 03 |
| RFP-031 Masonry | lists Division 03 as related |

→ **2 hits.** And note what it *misses*: every footing seam above. Scoreboard, bleachers, press box,
ticket booth and athletic equipment are Division 11/13 items — their **footings** are Division 03, but a
division-level check never pairs RFP-030 with ITB-089 or ITB-019, because those packages aren't Div 03.
Those footing seams are exactly where your rulings have already been needed twice this week.

#### Option 3 — Both

Coordination clauses as the primary spine, CSI divisions as a secondary sweep to catch packages that
share a division but never mention each other (which is how ITB-066 vs ITB-067 sealed concrete surfaced).

**Decide:** ☐ Coordination clauses  ☐ CSI divisions  ☐ Both (clauses primary, divisions as backstop)

---

### A3. How drawings get cited

RFP-030 today: **1 authoritative citation**, **12 candidates**.

#### Option 1 — Conservative (what the index does today)

Only sheets the scope narrative names outright become citations.

**Cited (1):** `L1.03` — the scope doc says "per detail D/L1.03".

**Held as candidates (12):** L1.00, L1.01, L1.06, A1-12, A1-20 ⚠, S0-00, S0-01, S1-30, S1-40, S2-10,
S3-00, S3-01

**Risk:** RFP-030's exhibit would cite one landscape detail sheet and **none of the structural foundation
sheets** — no S1-30 Scoreboard Foundation, no S1-40 Home Grand Stands, no S3-00/S3-01 Typical Foundation
Sections. For a concrete package that is obviously too thin.

#### Option 2 — Promote where the scope doc corroborates the content

Promote a candidate when the scope doc describes that work even without naming the sheet.

**Would become citations (7):**

| Sheet | Scope doc language that corroborates it |
|---|---|
| `S1-30` Foundation Plan – Scoreboard | "Scoreboard footings" |
| `S1-40` Foundation Plan – Home Grand Stands | "Bleacher footings / grade beams" |
| `S2-10` Foundation & Roof Framing – Concessions | "continuous footings, slab-on-grade, turned-down edges" |
| `S3-00`, `S3-01` Typical Foundation Sections | "cast-in-place footings", "stepped footings at utility entrances" |
| `S0-00` General Notes | "Class D Seismic Design Category; Importance Factor 1.0" |
| `A1-20` Site Details ⚠ | "expansion joints… control joints" (**must be re-read at ADD 1 revision**) |

**Would stay candidates (5):** L1.00, L1.01, L1.06 (landscape sheets, more likely RFP-016/RFP-022
territory), A1-12, S0-01

#### Option 3 — Promote all, flag the doubtful

All 12 become citations; the landscape sheets carry a "verify ownership" flag.

**Risk:** RFP-030's exhibit would cite three landscape construction sheets. If those belong to RFP-016 or
RFP-022, you've handed the concrete sub drawings for someone else's work — the exact
assignment-from-drawings failure that got v1 rejected.

**Decide:** ☐ Conservative  ☐ Promote where scope doc corroborates  ☐ Promote all, flag doubtful

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
