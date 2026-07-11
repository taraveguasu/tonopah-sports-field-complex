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

### Non-1% List (ITB) — 17 packages
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
| ITB-066 | Fluid-Applied Flooring |
| ITB-067 | Concrete Finishing |
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
| `01-index/package-index.json` | ✅ Generated (07.10.26), drawings vision-verified (07.11.26) — all 33 packages (16 RFP + 17 ITB), all cited source paths verified to resolve on disk, 81 PM-review flags. See summary below. |
| Drawing sheet indexing | ✅ Done — all 91 sheets across both Bid Plans volumes + ES Demo set cataloged from PDF bookmarks (`01-index/drawing-sheet-catalog.json`), then vision-verified sheet-by-sheet (actually opened and read, not just title-matched) via 3 background agents. Raw output in `01-index/drawing-vision-{vol1,vol2,esdemo}.json`, merged into each package's `drawing_sheets` with rationale/confidence preserved. Only ITB-008 (Surveying/Staking) still has zero drawing sheets — confirmed inherent to that scope, not a gap. |

## Current Pipeline Stage
- [x] Stage 0: Repo setup complete
- [x] Stage 1: Source docs staged, spec manual split, awarded-sub mapping built (Files API step dropped as unnecessary — see build status)
- [x] Stage 2: Index generated (`01-index/package-index.json`)
- [ ] Stage 3: **Index reviewed/corrected by PM — YOU ARE HERE.** Do not start Stage 4 drafting until this is done; every draft inherits whatever's wrong in the index.
- [ ] Stage 4: Drafts generated (`02-drafts/`)
- [ ] Stage 5: QA leveling register generated (`03-qa/`)
- [ ] Stage 6: Gaps/overlaps resolved by PM
- [ ] Stage 7: Final exhibits generated (`04-output/`)
- [ ] Stage 8: Subcontracts issued

### `package-index.json` summary — needs PM review before drafting starts
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
  - Non-1% (ITB) packages have no awarded-sub proposal on hand yet in `SUBCONTRACTOR FILES/` — those still draft from generic RFP/ITB/spec scope until awarded-sub docs show up
  - `scope-drafter` prompts need a second citation class beyond spec-section/sheet-number: "per [Sub Name]'s proposal dated [x]" / "excluded per descope agreement [x]"
  - `scope-qa` should flag any package where the awarded-sub's proposal contradicts the RFP scope, not just gaps/overlaps between packages
- Need: confirm CORE job number is 25-10-003
- ~~Need: "02 – Subcontractor Trade Scopes of Work" narrative and Bid Form~~ — RESOLVED, present in `02-trade-scopes-bidform/`
- Need: confirm whether any addenda/clarifications were issued after Clarification No. 2 (05.07.26) and before bid opening (05.12.26), or since
