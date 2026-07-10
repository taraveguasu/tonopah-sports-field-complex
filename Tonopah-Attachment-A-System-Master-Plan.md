# Tonopah THS Sports Complex — Attachment A Generation System
## Master Implementation Plan

---

## 1. Big Picture — What This System Actually Is

You're building two separate things that work together:

**A reusable capability** (`attachment-a-generator` skill) — the methodology for turning RFP/ITB/spec/drawing/bid-form documents into subcontract scope exhibits. This lives in your skill library and works on any future CMAR buyout, not just Tonopah.

**A project instance** (the `tonopah-ths-sports-complex` repo) — the actual data, source documents, and work product for this specific project. This is disposable in the sense that it's project-scoped, but durable in the sense that it needs to persist and be resumable across weeks of Claude Code sessions.

Think of it like this: the skill is the recipe, the repo is the kitchen with this specific project's ingredients and half-finished dishes in it. You'll reuse the recipe on the next CMAR project; you won't reuse this kitchen.

**Four architectural layers, bottom to top:**

| Layer | What it is | Why it exists |
|---|---|---|
| **Data layer** | Source docs on disk + Files API `file_id`s | Documents get uploaded once, referenced many times — no re-sending a 40MB spec manual on every one of 33 drafting calls |
| **Logic layer** | Skills — `attachment-a-generator`, `senior-pm` orchestration, `csi-divisions`, `public-works-context` references | Encodes *how* to index, draft, and QA — separated from any specific project's data so it's reusable |
| **Execution layer** | Subagents — doc-indexer, scope-drafter, scope-qa | Each is a bounded task with its own context window. A drafting pass for Package #030 (Concrete) never sees the noise from Package #103 (Electrical) — it stays grounded in its own slice of the index |
| **Memory layer** | `CLAUDE.md` at repo root + `01-index/` outputs | Lets any Claude Code session — today, next week, three weeks from now — pick up exactly where the last one left off, without you re-explaining the project |

The reason this isn't one giant prompt: a single pass holding the RFP, all 33 packages' worth of spec sections, the full drawing set, and the bid form in context at once produces shallow output — it'll miss spec section references or hallucinate exclusions because it's spread too thin. Breaking it into indexed retrieval + focused per-package drafting is what gets you output with real citations instead of plausible-sounding filler.

---

## 2. Skills to Build or Use

| Skill | Status | Role |
|---|---|---|
| `attachment-a-generator` | **Build new** | Orchestrates the 4-stage pipeline below. Defines index schema, drafting prompt structure, QA leveling logic. Lives in your user skill library. |
| `senior-pm` | Existing | Parent orchestrator — invokes `subcontract-management` and `preconstruction` sub-skills for scope leveling logic and the 30-day buy-out framework |
| `subcontract-management` (sub-skill) | Existing | Scope leveling matrix format, common gap zones (temp power, roof curbs, fire caulking, etc.), scope-of-work exhibit checklist |
| `preconstruction` (sub-skill) | Existing | GMP scope definition, constructability lens |
| `references/csi-divisions.md` | Existing | Scope assignment logic for indexing |
| `references/public-works-context.md` | Existing | NV/NRS 338 flow-down language, prevailing wage, SB 82 apprenticeship requirements — all confirmed applicable per the RFP you uploaded |
| `pdf-reading` | Existing | Source document ingestion — spec manual, drawings, geotech/asbestos reports |
| `xlsx` | Existing | Bid form restructuring, QA leveling register |
| `docx` | Existing | Final Attachment A exhibit output |
| `core-brand-guidelines` | Existing | Applies CORE branding to final docx exhibits |
| `api` | Existing | Scaffolding for the Files API upload/batch script |

Nothing else needs to be built from scratch — `attachment-a-generator` is the one new asset, and it's mostly configuration (index schema, prompt templates) rather than novel logic, since the subcontract-management sub-skill already encodes the scope-leveling judgment.

---

## 3. Subagents

Three subagents, each a distinct Claude Code Task invocation with its own bounded context:

**`doc-indexer`** (runs once)
- Input: RFP, ITB, spec manual sections, drawing set, bid form, addenda/clarifications, geotech/asbestos reports
- Job: build the structured per-package index — spec sections, drawing sheets, addenda references, bid form line items, mapped against both the 1% and non-1% package lists
- Output: `01-index/package-index.json`
- Model: Sonnet 5

**`scope-drafter`** (runs 33x, once per bid package)
- Input: one package's index entry + relevant `file_id`s
- Job: draft the Attachment A narrative — inclusions, exclusions, coordination-with-adjacent-trades language, cited to spec section/sheet number
- Output: `02-drafts/package-{number}-attachment-a.md`
- Model: Sonnet 5
- Why 33 separate runs and not one loop in a single context: each draft needs to stay grounded in its own package's index slice. Batching them in one context risks cross-contamination — Package #030 (Concrete) language bleeding into #031 (Masonry) exclusions.

**`scope-qa`** (runs once, after all 33 drafts exist)
- Input: all 33 drafts + the full index + bid form
- Job: cross-check for gaps (documented work with no home in any Attachment A) and overlaps (two packages claiming the same scope), specifically checking the known gap zones — temp power, roof curbs/equipment pads, fire caulking, final grade/seed, access panels
- Output: `03-qa/scope-leveling-register.xlsx`
- Model: **Opus 4.8** — this is the one step that benefits from the extra reasoning depth, since it has to hold the full leveling matrix and catch what's missing rather than generate forward from a template

---

## 4. Workflow — Full Sequence

**Stage 0 — Repo & Environment Setup** *(you're basically here now)*
1. `git init` the `tonopah-ths-sports-complex` repo, build the folder skeleton
2. Write `CLAUDE.md` — package list (both sources), the #008 collision flag, key dates, current stage
3. Pull the Egnyte bid docs folder into `00-source-docs/`, matching the 01–06 structure
4. **Resolve the #008 collision** — decide on a disambiguation scheme (e.g., prefix with source: `RFP-008` vs `ITB-008`) before anything downstream references package numbers
5. Confirm authoritative document revision — bid set vs. any post-award update — and pull the current Clarifications & Addenda folder in full (you're past bid opening; more may have been issued since Addendum #1/Clarifications 1–2)
6. Get the two missing pieces: "02 – Subcontractor Trade Scopes of Work" narrative and the Bid Form itself

**Stage 1 — Document Preparation**
1. Split the 40MB Bid Specification Manual into per-division sections (keeps each Files API upload targeted and keeps individual drafting calls from pulling in irrelevant divisions)
2. Spot-check the drawing set and scanned reports (Asbestos Survey, Asbestos Mgmt Plan) for OCR/scan quality before trusting vision extraction on them
3. Run the upload script (`scripts/upload-files.py` or similar, using the `api` skill scaffolding) — every source doc gets uploaded once via the Files API, `file_id`s written to `01-index/file_ids.json`

**Stage 2 — Indexing**
1. Run `doc-indexer` against all uploaded `file_id`s
2. Output lands in `01-index/package-index.json`

**Stage 3 — Human Checkpoint #1** *(you)*
- Review the index against your own knowledge of the project. This is the highest-leverage review point in the whole pipeline — every drafting pass downstream inherits whatever's wrong here. Correct by hand, don't just skim.

**Stage 4 — Drafting**
1. Run `scope-drafter` once per package — 33 runs, can batch/parallelize
2. Output: 33 files in `02-drafts/`

**Stage 5 — QA / Leveling**
1. Run `scope-qa` against all 33 drafts
2. Output: `03-qa/scope-leveling-register.xlsx` — flagged gaps, overlaps, and unresolved package boundary questions

**Stage 6 — Human Checkpoint #2** *(you)*
- Resolve every flagged gap/overlap — this is judgment CORE has to own, not something to auto-resolve
- Decide on any negotiable-vs-non-negotiable language per the subcontract-management checklist

**Stage 7 — Final Output**
1. `docx` skill converts approved drafts into CORE-branded Attachment A exhibits, one per package
2. Land in `04-output/`, ready to attach to the CORE Subcontract Agreement template (already sitting in your `05-Supplemental Documents` folder)

**Stage 8 — Buy-Out Execution**
- Attachment A exhibits feed into subcontract issuance per the standard 30-day buy-out timeline (scope leveling calls → draft subcontracts issued → negotiate exceptions → execute). This is where the system hands off to your normal process — the AI pipeline's job ends at Stage 7.

---

## 5. Timing Against Your Actual Clock

Per the RFP: Administrative NTP (shop drawings/submittals) is anticipated **~July 20, 2026** — that's about two weeks out from today. Construction NTP is **~November 23, 2026**. That gives you a real runway before the 30-day subcontract execution clock starts in earnest, but Stage 0–3 (setup through index correction) is worth finishing before Administrative NTP hits, since that's when submittal and RFI volume typically starts pulling your attention away from buy-out prep.

---

## 6. What I'd Build First

If you want to sequence the actual build work with me:
1. Repo skeleton + `CLAUDE.md` (fast, unblocks everything else)
2. `attachment-a-generator` skill file (defines the index schema and prompt structure the subagents will use)
3. Files API upload script
4. `doc-indexer` subagent definition — this is the one worth getting right before touching the other two, since everything downstream depends on it working correctly the first time
