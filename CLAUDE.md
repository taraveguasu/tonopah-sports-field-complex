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
| Bid Spec Manual split into per-division sections | ❌ Not done — still one 40MB file |
| `scripts/upload-files.py` (Files API upload) | ⚠️ Stub only — `SOURCE_FILES` dict is empty, needs wiring before it can run |
| `01-index/file_ids.json` | ❌ Not generated |
| `attachment-a-generator` skill | ❌ Not built |
| `doc-indexer` / `scope-drafter` / `scope-qa` subagent definitions | ❌ Not built |
| `01-index/package-index.json` | ❌ Not generated |

## Current Pipeline Stage
- [x] Stage 0: Repo setup complete
- [~] Stage 1: Source docs staged (done — RFP/ITB/scopes/drawings/specs/addenda/GMP/sub proposals all present); spec manual split and Files API upload still outstanding
- [ ] Stage 2: Index generated (`01-index/package-index.json`)
- [ ] Stage 3: Index reviewed/corrected by PM
- [ ] Stage 4: Drafts generated (`02-drafts/`)
- [ ] Stage 5: QA leveling register generated (`03-qa/`)
- [ ] Stage 6: Gaps/overlaps resolved by PM
- [ ] Stage 7: Final exhibits generated (`04-output/`)
- [ ] Stage 8: Subcontracts issued

## Open Questions / Notes
- **Drafting source-of-truth question (needs PM decision before Stage 2 indexing):** Since actual subcontractor proposals, descopes, and scope-review agendas already exist for most 1% packages, should each package's Attachment A be drafted from (a) the generic RFP/spec/scope-of-work language only, or (b) reconciled against the specific awarded subcontractor's actual proposal + negotiated descopes? Option (b) is more accurate to what was actually bought out but requires a package→awarded-sub mapping (Bid Tabulation Sheet may already have this) and pulls the descope/homework-response docs into the index.
- Need: confirm CORE job number is 25-10-003
- ~~Need: "02 – Subcontractor Trade Scopes of Work" narrative and Bid Form~~ — RESOLVED, present in `02-trade-scopes-bidform/`
- Need: confirm whether any addenda/clarifications were issued after Clarification No. 2 (05.07.26) and before bid opening (05.12.26), or since
