# Tonopah THS Sports Complex

## Project Basics
- Owner: Nye County School District (NCSD)
- Delivery method: CMAR/GMP
- Jurisdiction / applicable statutes: Nevada public works — NRS 338.16995 (1% list), NRS 338.0117 (bidder preference), SB 82 (Apprenticeship Utilization Act), Southern Nevada Rural Region prevailing wage
- Total budget: $12,000,000 (includes THS Sports Complex + Tonopah Elementary School Demolition)
- CORE job number: likely **25-10-003** (per `00-source-docs/GMP/25-10-003 - NCSD - Tonopah HS Sports Field Ph's Replacement GMP_EOD.pdf`) — CONFIRM

## Key Dates
- Notice dated: April 21, 2026
- Bid due date: May 12, 2026, 1:00 PM PDT (via Building Connected) — PAST
- Administrative NTP (anticipated): ~July 20, 2026 (shop drawings/submittals)
- Construction NTP (anticipated): ~November 23, 2026 (end of 2026 football season)
- Sport field completion (anticipated): ~July 26, 2027
- Buy-out target: 30 days from Precon/Ops handoff (handoff date TBD — confirm)

## Bid Package List

### 1% List (RFP — NRS 338.16995) — 16 packages
| package_id | Title |
|---|---|
| RFP-002 | Abatement & Building Wrecking |
| RFP-008 | Site Demolition, Salvage, Earthwork, Asphalt Paving, Wet Utilities, & Site Signage & Striping |
| RFP-016 | Landscaping & Irrigation |
| RFP-021 | Running Track Surfacing |
| RFP-022 | Synthetic Turf Sports Field |
| RFP-023 | Fencing & Gates |
| RFP-030 | Concrete |
| RFP-031 | Masonry |
| RFP-033 | Structural Steel & Ornamental Metals |
| RFP-045 | Metal Roofing, Fascia & Soffit Panels |
| RFP-060 | Framing, Drywall & Painting (incl. FRP) |
| RFP-094 | Bleachers & Press Box |
| RFP-098 | Plumbing Systems |
| RFP-100 | HVAC & Building Control Systems (incl. Test & Balance) |
| RFP-103 | Electrical & Low Voltage Systems (incl. Sports Field Lighting) |
| RFP-109 | Prefabricated Ticket Booth |

### Non-1% List (ITB) — 18 packages
| package_id | Title |
|---|---|
| ITB-008 | Surveying, Layout & Staking |
| ITB-018 | Site Furnishings |
| ITB-019 | Track & Field Athletic Equipment |
| ITB-040 | Moisture Protection & Sealants (incl. Acoustical Caulking) |
| ITB-044 | Insulation |
| ITB-054 | Special Doors |
| ITB-056 | Doors, Frames & Hardware |
| ITB-062 | Acoustical Ceiling Treatments |
| ITB-066 | Fluid-Applied Flooring — ⛔ **scope removed by Owner (VE), 08.06.26** |
| ITB-067 | Concrete Finishing |
| ITB-070 | Final Cleaning — added 08.06.26; no scope narrative was issued, draft from the four proposals on hand |
| ITB-071 | Visual Display Boards & Menu Display Case |
| ITB-072 | Building Signage |
| ITB-074 | Building & Fire Protection Specialties (incl. corner guards, cabinets, mirrors) |
| ITB-077 | Lockers |
| ITB-078 | Flagpoles |
| ITB-085 | Warming Kitchen Food Service Equipment |
| ITB-089 | Scoreboards |

**Known collisions:** Package #008 appears on BOTH lists with different scope (RFP-008 = Site Demolition/Earthwork/Utilities; ITB-008 = Surveying/Layout/Staking). Always key by package_id (source + number), never by number alone.

## Source Documents
- Location: https://core.egnyte.com/fl/dBBYFXhTDtQc/Bid_Documents_(THS_Sports_Complex)_04.21.26_
- Staged locally at: `00-source-docs/` (334 files, fully populated — see structure below)
- Authoritative revision: **post-award / post-GMP**, not just the bid set. Docs on hand include Addendum #1 (05.06.26), Clarification No. 1 (05.06.26), Clarification No. 2 (05.07.26), a negotiated **GMP R2 (07.01.26)**, a full bid tabulation (as of 05.12.26), and real subcontractor proposals/descopes/scope-review agendas for the 1% packages. This is well past bid opening — buyout is actively underway.

### `00-source-docs/` structure
| Folder | Contents |
|---|---|
| `01-rfp-itb/` | Notice of RFP (1%), Invitation to Bid (Non-1%) |
| `02-trade-scopes-bidform/` | Subcontractor Proposal (Bid) Form + all 33 Scope of Work docs (one per package) |
| `03-drawings/` | Bid Plans Vol 1/2 (FIELD), Bid Plans (ES DEMO) |
| `04-specs-reports/` | Bid Specification Manual (single 40MB PDF, **not yet split**), Geotech Report, Asbestos Survey, Asbestos Mgmt Plan |
| `05-supplemental/` | CORE Subcontract Agreement template, insurance reqs, billing procedures, Preliminary Construction Schedule (04.21.26), logistics plan template, non-collusive affidavit, compliance affidavit |
| `06-addenda/` | Addendum #1 folder (table of contents, door hardware, revised architectural/civil sheets), Clarifications 1 & 2, RFI responses, contour map |
| `GMP/` (not in original 01-06 scheme) | Negotiated GMP R2 (pdf + xlsm), GMP EOD (25-10-003), GC's & GR's, bid-leveling workbook, GMP schedule, 1% subcontractor listing, Basis of Proposal |
| `SUBCONTRACTOR FILES/` (not in original 01-06 scheme) | Attachment A/B templates, **actual submitted subcontractor proposals** (1% packages — GGG, Northstar, NDX, Black Canyon, BrightView, AstroTurf, CG&B, etc.), 1% Descopes (scope-review meeting agendas, homework responses, cut sheets), Bid Tabulation Sheet, Bid RFIs, Other Proposals |

## System Architecture (Attachment A Generation Pipeline)
Full design doc: `Tonopah-Attachment-A-System-Master-Plan.md` (repo root). Summary:

- **Reusable skill** `attachment-a-generator` (lives in user skill library, works on future CMAR projects too) orchestrates a 4-stage pipeline: index → draft → QA → final exhibit.
- **Three subagents**, each bounded to its own context: `doc-indexer` (runs once, builds `01-index/package-index.json`), `scope-drafter` (runs once per package — 33x — drafts `02-drafts/package-{n}-attachment-a.md`), `scope-qa` (runs once against all 33 drafts, catches gaps/overlaps, needs Opus-class reasoning).
- **Memory layer**: this `CLAUDE.md` + `01-index/` outputs — lets any session resume without re-explaining the project.

### Build status
| Component | Status |
|---|---|
| Repo skeleton + `CLAUDE.md` | ✅ Done |
| Source docs staged | ✅ Done — and then some (GMP + actual sub proposals in hand, beyond original scope) |
| Bid Spec Manual split into per-division sections | ✅ Done — 22 division PDFs in `04-specs-reports/spec-manual-split/`, built from the manual's own bookmark outline (exact page boundaries, manifest at `spec-manual-split/_manifest.json`) |
| `01-index/awarded-sub-mapping.json` | ✅ Done — 14 of 16 1% packages have a confirmed awarded sub; RFP-094 (Bleachers & Press Box) and RFP-109 (Prefabricated Ticket Booth) not yet awarded. Several PM-review flags recorded (awarded sub not low bidder on 5 packages, one missing signed Bid Form, one late/out-of-process proposal) |
| Files API upload script | 🗑️ Superseded — running inside Claude Code, subagents read `00-source-docs/` directly via Read/Glob, no file_id upload needed. `scripts/upload-files.py` left in place but noted as not part of this pipeline |
| `attachment-a-generator` skill | ✅ Built — `.claude/skills/attachment-a-generator/SKILL.md` (+ `references/csi-divisions.md`) |
| `doc-indexer` / `scope-drafter` / `scope-qa` subagent definitions | ✅ Built — `.claude/agents/{doc-indexer,scope-drafter,scope-qa}.md` |
| `01-index/package-index.json` | ❌ **REJECTED by PM (07.31.26) — do not draft from this.** ~47% defect rate on the 17 highest-stakes rows the PM checked. Three root causes, all confirmed: the 33 Scope of Work narratives were never read (stored as filenames only); Addendum #1's 7 revised sheets were never applied as supersession, so 16 of 33 packages cite dead base-bid drawings; awarded-sub proposals were mapped but never read. Full record: `01-index/pm-review-2026-07-31.md`. |
| Scope of Work narratives extracted | ✅ Done (07.31.26) — all 35 `.docx` (33 SOW + ITB + RFP notice) extracted to `02-trade-scopes-bidform/_extracted/*.txt`, 362,376 chars, article offsets in `01-index/scope-doc-extraction-manifest.json`. Built by `scripts/extract-scope-docs.py`. **These are the primary scope authority for the re-index** — they resolve boundaries the drawings leave ambiguous. |
| Proposal / descope / homework content indexed | ✅ Done (08.05.26) — `01-index/proposal-content.json`, built by `scripts/index_proposals.py`. All 246 bidder documents read, not just filenames: 2,246 inclusions, 2,041 scope-specific exclusions, 645 clarifications, 138 priced add/deduct line items, 14 priced product groups. **All 33 packages now have at least one scope-bearing document.** Supersession chain per firm per package (latest date governs; 47 undated documents are flagged, never sequenced by guess). Bid tabulation reconciled against every bidder's own stated price. 8 proposal probes added to `scripts/verify_extraction.py`; **33/33 probes pass.** |
| Spec sections cataloged & assigned | ✅ Done (08.05.26) — `01-index/spec-section-catalog.json` + `package-spec-citations.json`, built by `scripts/index_spec_sections.py`. 131 sections from the manual's own bookmark outline; **all 106 technical sections have a primary package** — 30 by scope-doc citation, 5 by PM ruling, 71 by trade judgment (flagged as judgment, never as citation). Division-level citations expanded to real sections: RFP-031 now has 04 05 03 / 04 20 16, RFP-098 all 11 Div-22, RFP-100 all 16 Div-23, RFP-103 all 22 Div-26/27. 3 flow-down sections separated from 5 genuine conflicts. 19 cited-but-absent sections written up individually. 14 spec probes added; **47/47 probes pass.** |
| Sheet → package assignments | ✅ Done (08.06.26) — `01-index/sheet-package-assignments.json`, built by `scripts/assign_sheets.py`. **Re-derived from the scope docs, not from reading the drawings** — closing the third root cause of the 07.31.26 rejection. 91 sheets, 783 assignments, each carrying its evidence. Four signals: scope doc naming the sheet (12), spec section whose owner is known, distinctive scope vocabulary, discipline prefix (last resort, marked weak). Output splits `draft_from` from `leads_to_verify`. **Every sheet reaches a package and every package reaches a sheet.** 13 assignment probes added; **68/68 probes pass.** |
| Drawing sheet indexing | ⚠️ Partially valid — 91 base-bid sheets cataloged (`01-index/drawing-sheet-catalog.json`) and vision-read (`drawing-vision-{vol1,vol2,esdemo}.json`). Independent spot-check confirmed the readings are verbatim-accurate **for the revision they read**, but the pass consumed the base bid set only. The 7 sheets revised by Addendum #1 (G0-00, LS1-10, A1-20, A2-10, A10-30, C1, GD) were never opened. Sheet content is reusable; package assignments are not, having been made from drawings rather than from scope docs. |

### Open items raised by the proposal index (08.05.26) — need PM decisions
All confirmed by reading the source document, not inferred from a count.

1. **RFP-008 bid tab is reversed — CORRECTED.** The 05.12.26 tabulation records NDX at
   $1,924,851 and New-Com (TAB) at $3,152,033. Both bidders' own Proposal Forms state the
   opposite: TAB's BuildingConnected header and letter both read **$1,924,851**, NDX's reads
   **$3,152,032.69**. TAB is therefore the **low** bidder (TAB $1.92M < Monument $2.30M < NDX
   $3.15M), not the high one. `awarded-sub-mapping.json` has been corrected and the "awarded sub
   was not the low bidder" flag on RFP-008 withdrawn. **The tab is a transcription, not a source
   — treat any price taken from it as unverified.** Reconciliation of all 16 tabulated packages
   now runs automatically; RFP-008 is the only reversal.
2. **Sprinturf's bid does not split (RFP-016 / RFP-022).** One combined $1,022,155 number for
   Landscaping + Irrigation + Synthetic Turf. Their Proposal Form is headed "Bid Proposal:
   Landscaping & Irrigation"; their descope file is named "016, 022". The tab enters it once,
   under 016 only — so RFP-022's row omits them entirely and RFP-016's row compares a combined
   bid against landscaping-only bids (BrightView $131,300, Black Canyon $111,275).
3. **Nine firms submitted bundled multi-package scope**, where each package's document also
   describes the others: Tand (016/022), XL Concrete Masonry (030/031), Division 09
   (044/056/062/060), Bombard (098/100), Exerplay (018/019/078), SI Legacy (040/066/067),
   NRC (066/067), Ryerson (066/067), YESCO (072/078/089). Neither price nor scope splits by
   package without a descope.
4. **Trade 070 "Final Cleaning" has four proposals and no bid package** (CSI, Lady Lux, Nevada
   Angels + a Nevada Angels descope). Confirm whether it is CORE self-perform, folded into
   another subcontract, or needs its own package.
5. **Northstar's price moves after bid (RFP-002):** proposal 05.12.26 states $718,623; homework
   response 05.15.26 states $718,263 — a digit transposition $360 apart. The later document
   governs by date; confirm which figure is intended.
6. **TAB's 05.22.26 homework response is a re-priced proposal**, ten days after bid opening. Same
   $1,924,851 base, but it carries scope-shifting deducts that bear on other packages: *Delete
   trench drain −$125,000*, *Delete Type II and geofabric from turf field −$150,000*, *Delete
   Type II from building pad and concrete paving −$46,000*, *ADD D-10 dozer for hard dig
   +$70,000*. The trench-drain deduct interacts with the 07.31.26 ruling that trench drains at
   the track perimeter are RFP-030.
7. **ITB-074 / ITB-077 locker overlap:** Henri's ITB-074 quote prices *METAL LOCKERS — ASI
   Storage, 20 frames / 20 openings — furnished and installed — $22,519* inside the Building
   Specialties package. ITB-077 is the lockers package. Decide which subcontract carries them.
8. **Tahoe Fence's scope-review agenda is a blank template** — subcontractor, scopes, date and
   attendees all unfilled. Either the meeting record was never completed or the wrong file was
   saved.

### Spec gaps (08.05.26) — 4 closed by ruling, 15 open
Nineteen sections are cited by a scope doc but absent from the manual. Five are near-certain
renumberings (02 41 13→02 41 00, 05 31 12→05 31 00, 08 31 13→08 31 00, 10 21 00→10 21 13.13,
11 68 33→? ).

**Closed by PM ruling 08.05.26** — the replacement section is now in each package's list:

| Absent | Ruling | Now references |
|---|---|---|
| 03 35 00 Concrete Finishing | ITB-067 references 03 30 00, not 03 35 00 | **ITB-067 → 03 30 00** (Part 3 carries the finishing requirements; RFP-030 still places the concrete) |
| 07 13 00 Sheet Waterproofing | Use 07 25 00 for package 040 | **ITB-040 → 07 25 00** Weather Barriers, shared with RFP-045 along the 07.31.26 boundary (RFP-045 = membrane under metal roof, ITB-040 = below-grade) |
| 32 11 23 Aggregate Base Courses | Covered in 31 20 00 Earth Moving | **RFP-030 → 31 20 00**; RFP-008 remains primary, consistent with TAB pricing the Type II deducts |
| 07 84 00 Firestopping | No action required | **No rated assemblies on this project** — see below |

**There are no fire-rated assemblies anywhere on this job.** Verified against four sources:
partition schedule A2-40 publishes only marks `3F0`, `5F0`, `3B0`, whose third character is the
fire-rating code and is `0` (NO RATING) in all three, with UL LISTING **(none)**; LS1-10 at its
Addendum #1 revision shows **0 HR** for every IBC 601 element and 0 HR exterior walls at >30 ft
fire separation distance on all four sides, opening protection NOT REQUIRED, area separation
0 HR, no sprinklers, no fire alarm, Type VB; the superseded base-bid LS1-10 carries the same
0 HR values, so the addendum did not change them; and no door in A11-10's 22-row schedule carries
a rating, with no UL design number anywhere in the 91-sheet set. IBC 714 penetration firestopping
applies only to rated assemblies, so 07 84 00 is a documentation gap, not a construction risk.
(The FRP panels' "CLASS A/C FIRE-RATED" in the finish schedule is ASTM E84 surface burning, not an
assembly rating.)

**Still open, and worth a decision:** **09 82 00 Acoustical Insulation** absent (only 07 21 00
Thermal exists — confirm whether ITB-044 or RFP-060 carries acoustic batt); **10 44 13 Fire
Protection Cabinets** absent though Henri priced $6,313 of them; **07 41 13 Metal Roof Panels**
absent — RFP-045 is assigned 07 61 00 Sheet Metal Roofing as the nearest published substitute,
which is a different section, not a renumbering.

**Five genuine conflicts** (two scope docs claiming the same section): 02 41 00 (RFP-002 cites it,
ruling gives it to RFP-008), 09 21 16 (ITB-077 vs RFP-060), 10 26 00 (ITB-074 vs RFP-060),
12 93 00 (ITB-018 vs ITB-019 — the section's own Section Includes spans both), 32 91 13
(ITB-019 vs the RFP-016 ruling). Separate from these, 03 30 00, 07 92 00 and 08 31 00 are
**flow-down** sections many packages cite by design, not disputes.

**Bookmark number correction:** the manual's outline lists "04 43 36C - Expanded Subcontractor
Listing". Page 15's own section heading reads **SECTION 00 4336C**, and it is filed between
00 43 36B and 00 45 21. It is a Division 00 procurement form, not a masonry section.

## Current Pipeline Stage
- [x] Stage 0: Repo setup complete
- [x] Stage 1: Source docs staged, spec manual split, awarded-sub mapping built (Files API step dropped as unnecessary — see build status)
- [x] Stage 2: **REBUILT (08.06.26).** All three root causes of the 07.31.26 rejection are closed: the 33 scope narratives are extracted and are the primary authority; Addendum #1 is applied as supersession and sheets are read at their current revision; all 246 bidder documents are read, not just mapped. Spec sections cataloged and every technical section assigned. Sheet→package assignments re-derived from the scope docs. **68/68 verification probes pass.** Open PM decisions collected in `01-index/pm-open-items.md`.
- [ ] Stage 3b: **YOU ARE HERE** — the rebuilt index must clear the same PM review that failed on 07.31.26 before drafting starts.
- [x] Stage 3: Index reviewed by PM — done, and it failed. Verdicts and root causes in `01-index/pm-review-2026-07-31.md`. The re-index must clear this same review before Stage 4.
- [ ] Stage 4: Drafts generated (`02-drafts/`)
- [ ] Stage 5: QA leveling register generated (`03-qa/`)
- [ ] Stage 6: Gaps/overlaps resolved by PM
- [ ] Stage 7: Final exhibits generated (`04-output/`)
- [ ] Stage 8: Subcontracts issued

### Document authority hierarchy — governs the re-index
Established by PM review 07.31.26. The first index inverted this, treating drawings as the
primary authority and never opening the scope narratives.

1. **Addenda & Clarifications** supersede everything they touch. Addendum #1 (05.06.26) revised
   7 sheets — G0-00, LS1-10, A1-20, A2-10, A10-30, C1, GD — and added spec section 08 71 00.
   Clarifications 1 & 2 carry RFI answers that override both drawings and specs. **Always index
   the revised sheet, never the base-bid sheet.** Every citation needs a revision field.
2. **Scope of Work narrative** (`02-trade-scopes-bidform/_extracted/*.txt`) decides *which
   package carries a given item*. This is the trade-boundary authority — the drawings show what
   exists, the scope doc says whose it is.
3. **Specifications** decide how the work is executed.
4. **Drawings** show extent and location. They are the weakest authority for assignment.
**Subcontractor proposals are NOT in the authority hierarchy at all.** (Corrected by PM
07.31.26 — an earlier draft wrongly listed them as a fifth tier that "reconciles" final scope.)
A proposal never relieves a sub of completing the scope per the contract documents; the
contract documents overrule the proposal. Their role is diagnostic:

- They **surface the assumptions** a bidder made where the documents were ambiguous.
- They **expose scope gaps** and level the playing field between bidders.
- Where a proposal **contradicts any contract document → FLAG for PM to clarify.** Never
  silently adopt the proposal's position, and never quietly narrow the subcontract to match it.
- **Ignore the general/boilerplate exclusions** on proposals. They are not scope decisions.
- **Read every bidder's proposal for a package, not just the awarded sub's.** Losing bidders
  routinely itemize something the drawings left ambiguous; those line items are the clearest
  available signal of what must be spelled out explicitly in the subcontract. This is a primary
  source of Attachment A inclusions.

Known trade-boundary rules from PM review: self-adhered membrane under metal roof is RFP-045,
not ITB-040 (ITB-040 is below-grade waterproofing only); concrete curb and slot/trench drains
at track perimeter are RFP-030; athletic equipment footings incl. goal posts are RFP-030; the
entire demolition scope is RFP-008.

### PM rulings log (running)
| Date | Ruling |
|---|---|
| 07.31.26 | Entire demolition scope is RFP-008 |
| 07.31.26 | Goal post / athletic equipment footings are RFP-030 |
| 07.31.26 | Concrete curb and slot/trench drains at track perimeter are RFP-030 |
| 07.31.26 | ITB-040 is below-grade waterproofing only; self-adhered membrane under metal roof is RFP-045 |
| 07.31.26 | RFI responses issued with the Addendum are contract documents and bind the subcontractor |
| 07.31.26 | ITB-077 basis of design is Clarification No.1 RFI #3 (ASI Pro Collection, 24"W x 18"D x 72"H) |
| 07.31.26 | Locker filler panels are ITB-077, delivered with lockers, field-measured before order or field-cut for tight fit |
| 07.31.26 | There is NO fire alarm system (formalizing ASI forthcoming) |
| 07.31.26 | Access doors and panels (08 31 00): MEP trades supply, RFP-060 framer installs |
| 07.31.26 | RFP-016 primary specs are 32 84 00, 32 91 13, 32 96 50 |
| 08.04.26 | **Exhibit B — Basis of GMP (07.01.26) is a contract document and supersedes the base bid set**, treated as an addendum (forthcoming revision) |
| 08.04.26 | Prevailing wage is **2025-2026 Southern Nevada Rural Region** — supersedes Clarification No.2's Clark County direction |
| 08.04.26 | GMP includes Nevada State Sales Tax |
| 08.04.26 | **Fire alarm systems are an express GMP Exclusion** — the written instrument the no-fire-alarm direction was awaiting |
| 08.04.26 | Resinous/Epoxy Flooring excluded; those locations become Sealed Concrete under ITB-067 (Owner Accepted Alternate) — ITB-066 has no remaining scope |
| 08.04.26 | RFP-109 ticket booth is Porta-King DURASTEEL PC Building Model PC64 (6'x4') |
| 08.04.26 | RFP-022 turf is Matrix Helix 46 oz, Elia Renufill/Realfill infill, SOTERIA 20mm pad |
| 08.05.26 | **ITB-067 references 03 30 00 Cast-In-Place Concrete, not 03 35 00** (absent from the manual) |
| 08.05.26 | **ITB-040 uses 07 25 00 Weather Barriers** in place of the absent 07 13 00 Sheet Waterproofing |
| 08.05.26 | **Aggregate base courses are covered in 31 20 00 Earth Moving** — closes the absent 32 11 23 |
| 08.06.26 | **A1** — 09 65 13 Resilient Base included in ITB-067 |
| 08.06.26 | **A2/C1** — 12 93 00 Site Furnishings: ITB-018 SUPPLIES, ITB-019 INSTALLS. Spec in both subcontracts; ITB-019's is installation only |
| 08.06.26 | **A3** — 10 26 00 Wall & Door Protection included in ITB-074 |
| 08.06.26 | **A4** — 02 41 00 Demolition spec in BOTH RFP-002 and RFP-008. RFP-002 is abatement, which has demo in it; RFP-008 has the full building demo and site demo |
| 08.06.26 | **A5** — 32 91 13 is RFP-016. **Do NOT exclude it in ITB-019 or RFP-030** — they must coordinate with that scope |
| 08.06.26 | **A6** — 32 16 23 Sidewalks are RFP-030 |
| 08.06.26 | **A7** — Test & Balance is included in RFP-100, not subcontracted directly |
| 08.06.26 | **A8** — Access doors confirmed: MEP supply, RFP-060 installs |
| 08.06.26 | **B1** — The GMP governs over RFI #23; RFP-045 is the Berridge C-Lock system |
| 08.06.26 | **B2** — Panic hardware at Door 106 is **excluded**; it was a bid alternate the Owner did not accept |
| 08.06.26 | **C1** — ITB-077 lockers per Clarification No. 1 (ASI Pro Collection, Security Box & Foot Locker, 24"W x 18"D x 72"H, black). No spec section was issued |
| 08.06.26 | **D — GLOBAL RULE.** A spec section cited by an RFP/ITB package that is NOT in the Project Manual **cannot be cited in Attachment A**. Put the specification's **TITLE** into the scope verbiage instead (RFP-045 says "metal roof panels", not "07 41 13"). Draft those obligations from the scope narrative, the drawings and the subcontractor's proposal |
| 08.06.26 | **D** — RFP-045 owns the gutters and downspouts |
| 08.06.26 | **D** — ITB-074 owns the fire protection cabinets |
| 08.06.26 | **D** — RFP-094's only specifications are the written blocks on sheet A1-40 |
| 08.06.26 | **D** — **RFP-060 will include ITB-044, ITB-062 and ITB-077** under one subcontract. **Each scope is written independently** — one Attachment A per package, all attached to the same agreement. Exhibits stay separately reviewable and separately descopeable; `scope-qa` must not read a shared boundary between these four as a leveling defect |
| 08.06.26 | **E1** — Final Cleaning is its own package (**ITB-070**). No scope narrative was issued; draft from the four proposals and documents on hand |
| 08.06.26 | **E2** — ITB-066 Fluid-Applied Flooring: **scope removed by the Owner in a value engineering exercise** |
| 08.06.26 | **F1/F2/F3** — RFP-008 tab reversal, 07 25 00 shared RFP-045/ITB-040, and no firestopping obligation: all confirmed |
| 08.05.26 | **07 84 00 Firestopping needs no action — there are no fire-rated assemblies on this project** (all three partition types rate 0; LS1-10 shows 0 HR throughout) |

### `package-index.json` summary — ⚠️ SUPERSEDED, describes the rejected index
Kept for provenance. Findings below that came from the vision pass are still useful as leads,
but every package assignment must be re-derived from the hierarchy above.
- 29/33 packages have real cited spec sections; 4 have none because **no matching CSI section exists in the spec manual** (not extraction misses — confirmed by cross-checking each scope doc's own citations): RFP-109 Prefabricated Ticket Booth, ITB-066 Fluid-Applied Flooring, ITB-077 Lockers, ITB-008 Surveying/Layout/Staking. **Update (07.11.26, drawing vision pass):** 3 of these 4 now have a drawn substitute for the missing spec section — RFP-109 and RFP-094 (Bleachers, whose own bleacher-specific spec section is also missing) each have full written spec blocks on sheet A1-40 ("PRE-MANUFACTURED TICKET BOOTH SPECS" / "PRE-MANUFACTURED ALUMINUM BLEACHERS SPECS" / "PRE-MANUFACTURED PRESS BOX SPECS"); ITB-077's missing locker spec is matched by a drawn Basis-of-Design keynote on sheet A10-30 ("ASI Storage Solutions Single Tier Locker Competitor Collection"), consistent with the earlier RFI. Only ITB-066 (Fluid-Applied Flooring) and ITB-008 remain genuinely unresolved.
- **Drawing sheets are now vision-verified for all 91 sheets** (all 3 drawing files) — see build status above. This surfaced real findings beyond just filling gaps:
  - **3 mislabeled citations corrected**: ITB-054's roll-up door detail was cited to the wrong sheet (A4-10 → actually A7-10/A11-10); RFP-022's L1.02 and L1.03 sheet descriptions didn't match their actual content (L1.02 is field-events equipment layout, not turf/track notes; L1.03 is track markings + turf install detail + a curb detail, not high-jump/pole-vault — those are on L1.07).
  - **A1-20's "Site Equipment Matrix"** is an authoritative CFCI (Contractor Furnished, Contractor Installed) responsibility table for 5 packages: Scoreboard (ITB-089), Bleachers & Press Box (RFP-094), Trash Receptacle (ITB-018), Ticket Booth (RFP-109) — none are Owner-furnished, worth citing directly in those drafts.
  - **New RFP-002/RFP-008 overlap found**: keynote on the on-site Site Demo Plan calls for salvaging fixtures from the existing concessions building — a third overlap between these two packages beyond the already-flagged ES-campus alternate duplicate.
  - **ES Demo drawing set (6 sheets) indexed for the first time** — all assigned to both RFP-002 and RFP-008, since the drawings mix building-wrecking and site/utility-demo content without a clean trade split. Confirms RFP-002 Alt 002.02 and RFP-008 Alt 008.04 (identically worded "ADD - Demolition & Site Clearing at Abandoned Elementary School Campus") share this same drawing set — **unresolved whether that alternate splits by trade or both packages are pricing the same combined scope**; needs to be checked against the 1% Descopes files before scope-qa runs.
  - **Ambiguous demo boundary**: landscape demolition sheets (existing track/turf/jump-pit/goal-post removal) could belong to RFP-008 (general demo) or to the respective install packages (RFP-021 track, RFP-022 turf, ITB-019 equipment) clearing their own way — no source doc resolves this, mirrors the RFI #14/#15 pattern already in the index.
  - **Deferred submittal ambiguity**: G0-00 lists "Goal Post Structural Design" as a deferred submittal alongside Pressbox/Bleachers/Scoreboard — could belong to ITB-019 (supplies goals) or RFP-033 (if treated as delegated structural steel design). Not force-assigned.
  - 81 flags total in `_flags_for_pm` now (up from 53) — includes one process note: the merge script initially dropped 3 valid citations (RFP-023 ×2, ITB-078 ×1) that a vision agent confirmed correct in its rationale text but didn't re-list explicitly; caught and restored, but worth a spot-check in case others were missed the same way.
- Older flags, key ones still open:
  - **Numbering drift** between scope-doc filenames and package_ids: ITB-008 filed as "007", RFP-060 as "061", RFP-100 as "099", ITB-040 cross-referenced elsewhere as "#038", RFP-008 alternate references a nonexistent "Bid Package #004". Reconciled by title match, not number — but worth a human sanity check.
  - **Spec sections cited by scope docs that don't exist in the manual**: 02 81 00 (RFP-002), 07 13 00 (ITB-040), 09 82 00 (ITB-044), 10 44 13 (ITB-074), 10 51 13 (ITB-077), 11 68 33 (ITB-019), 13 12 50 (RFP-094 Bleachers). Left uncited rather than guessed — these are real spec gaps, not indexing failures.
  - **Section 12 93 00 (Site Furnishings)** spans both ITB-018 (benches/waste receptacles) and ITB-019 (Track & Field Athletic Equipment — NFHS goals/cages/pits) per its own Section Includes — scope-qa needs to verify the two awarded subs don't both claim the athletic-equipment portion.
  - **Section 08 31 00 (Access Doors and Panels)** exists in the spec manual but is claimed by no package — a real gap-zone hit.
  - Duplicate "ADD Menu Display Case" alternate is worded identically in both ITB-072 (Building Signage) and ITB-085 (Warming Kitchen Food Service Equipment) — plus ITB-071's own title ("Visual Display Boards & Menu Display Case") also implies this scope, so three packages may be touching it. Needs PM resolution on which one actually carries it.
  - RFP-094 (Bleachers & Press Box) scope doc cites a bleacher-specific section that doesn't exist; only a generic Fabricated Structures section was found and tentatively assigned to the press box portion only.

## Open Questions / Notes
- ~~**Drafting source-of-truth question**~~ — **RESOLVED (07.10.26):** each 1% package's Attachment A will be drafted **reconciled to the awarded subcontractor** — i.e. cross-referenced against that package's actual submitted proposal, negotiated descopes, and scope-review agenda in `SUBCONTRACTOR FILES/`, not just the generic RFP/spec language. Consequences for the pipeline:
  - `doc-indexer` must build a **package → awarded-sub mapping** first (start from `GMP/1% Subcontractor Listing.pdf` and `SUBCONTRACTOR FILES/21.0 - Subcontractor Proposals/Bid Tabulation Sheet/`), then pull that specific sub's proposal PDF + any `1% Descopes/` files (descope Q&A, homework responses, scope-review agenda) into the index alongside the RFP/spec/drawing citations
  - ~~Non-1% (ITB) packages have no awarded-sub proposal on hand yet~~ — **WRONG, corrected 07.31.26.** All 17 ITB packages have proposals staged in `SUBCONTRACTOR FILES/21.0 - Subcontractor Proposals/Other Proposals/` (86 files). **Every one of the 33 packages has at least one bidder on file** — 154 proposal files plus 103 descope / homework-response / scope-review-agenda files. Full map: `01-index/proposal-inventory.json`
  - **Entity alias:** GTI 1 Inc. = BrightView (same firm, filed under both names — scope-review agenda and homework response say GTI, proposals say BrightView). Do not count as two bidders.
  - `scope-drafter` prompts need a second citation class beyond spec-section/sheet-number: "per [Sub Name]'s proposal dated [x]" / "excluded per descope agreement [x]"
  - `scope-qa` should flag any package where the awarded-sub's proposal contradicts the RFP scope, not just gaps/overlaps between packages
- Need: confirm CORE job number is 25-10-003
- ~~Need: "02 – Subcontractor Trade Scopes of Work" narrative and Bid Form~~ — RESOLVED, present in `02-trade-scopes-bidform/`
- Need: confirm whether any addenda/clarifications were issued after Clarification No. 2 (05.07.26) and before bid opening (05.12.26), or since
