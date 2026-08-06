---
name: attachment-a-generator
description: Generates subcontract scope-of-work exhibits (Attachment A) for CMAR/GMP bid packages from RFP/ITB/spec/drawing/bid-form source documents, reconciled against awarded subcontractor proposals where available. Use when indexing bid package source docs, drafting per-package Attachment A scope exhibits, or QA'ing a set of drafted exhibits for gaps/overlaps before subcontract issuance.
---

# Attachment A Generator

Orchestrates a 4-stage pipeline that turns a CMAR project's bid documents into subcontract
scope-of-work exhibits (Attachment A), one per bid package: **index → draft → QA → final exhibit**.

Full architectural rationale: `Tonopah-Attachment-A-System-Master-Plan.md` at the project repo root
(or the equivalent master plan doc for whatever project invokes this skill).

This skill is project-agnostic. Everything project-specific (package list, key dates, folder layout,
drafting-source-of-truth decision) lives in that project's `CLAUDE.md` — read it first.

## Why this is 3 subagents, not 1 loop

A single pass holding the RFP, every package's spec sections, the full drawing set, and the bid form
in context at once produces shallow output — it'll miss spec section references or hallucinate
exclusions because it's spread too thin. Each package also needs to stay grounded in its own slice of
the index; batching all packages in one drafting context risks cross-contamination (Package #030
Concrete language bleeding into #031 Masonry exclusions). So:

- **`doc-indexer`** runs once, builds the full per-package index
- **`scope-drafter`** runs once *per package* (parallelizable), drafts from its own index slice only
- **`scope-qa`** runs once at the end, holding everything, specifically to catch what the narrow
  per-package view can't

## Stage 1 — Index (`doc-indexer` subagent)

Input: the project's `00-source-docs/` tree (read directly via Read/Glob — no Files API upload needed
when running inside Claude Code; that indirection is only for standalone-script use).

Output: one drafting record per package, plus a manifest.

```
01-index/packages/<package_id>.json   what a drafter reads — one package, nothing else
01-index/package-index.json           manifest only: title, award status, counts, file pointer
```

ONE FILE PER PACKAGE is deliberate. A single merged index gets read in full by every drafter run for the
few percent of it that run needs, and it puts all 33 packages' scope in one context — which is the
cross-contamination this pipeline is built to avoid.

### What each package record carries

| Key | Purpose |
|---|---|
| `document_authority_hierarchy` | Restated in every record, because it is the rule the drafter is most likely to invert |
| `scope_narrative.file` | The trade-boundary authority. Read in full, first |
| `spec_sections.primary` | With `basis` (`scope_doc` / `pm_ruling` / `trade_judgment`) and the rationale for each |
| `spec_sections.added_by_pm_ruling` | Sections granted by ruling that the scope doc never cited |
| `spec_sections.flow_down_from_other_packages` | Sections this package complies with but does not carry |
| `spec_sections.cited_but_absent_from_manual` | Real spec gaps, with status and any PM resolution |
| `drawings.draft_from` | Sheets at their current revision. **Retrieval only — never reproduced in the exhibit** |
| `drawings.leads_to_verify` | Weak matches. Open before relying on one; never draft from it unverified |
| `bidders[]` | **Every** bidder's inclusions, exclusions, clarifications and priced line items, with the supersession chain per firm |
| `gmp_basis_exhibit_b` | Scope assumptions, exclusions, prevailing wage and sales tax |
| `open_pm_items` | Unresolved decisions touching this package, carried into the draft as visible notes |

On this project the records are built by `scripts/build_package_index.py`, which merges the outputs of
`index_proposals.py`, `index_spec_sections.py` and `assign_sheets.py`. The `doc-indexer` agent and the
legacy single-file schema it writes are superseded by those scripts — deterministic extraction beats an
agent re-reading 343 documents, and it is re-runnable when an addendum lands.

**Human Checkpoint #1**: the PM reviews the per-package records in `01-index/packages/` by hand
before any drafting starts. This is
the highest-leverage review point in the pipeline — every draft downstream inherits whatever's wrong here.

## Stage 2 — Draft (`scope-drafter` subagent, run once per package)

Input: one package's record (`01-index/packages/<package_id>.json`) plus the specific
source files it cites. Never the full index — that's the cross-contamination risk.

Output: `02-drafts/package-{package_id}-attachment-a.md`

### Drafting rules

- **Two citation classes, not one:**
  - Spec/drawing citations: `"per Spec Section 03 30 00" `/ `"per Sheet S-201"` / `"per Addendum #1 (05.06.26)"`
  - Awarded-sub citations (only when `awarded_sub.status == "awarded"`): `"per [Sub Name]'s proposal dated [x]"` /
    `"excluded per descope agreement [x]"` — pull these from the sub's proposal PDF and any descope files,
    not just the generic RFP scope-of-work doc.
- **Not-yet-awarded packages**: draft strictly from generic RFP/ITB/spec/scope-of-work language, and add a
  visible header note: `> Awarded subcontractor TBD as of [index date] — draft based on generic RFP scope.`
- **Structure**: Package Title & ID → Inclusions → Exclusions → Coordination with Adjacent Trades → Citations list.
- **Every inclusion/exclusion needs a citation.** No uncited scope language — that's the "plausible-sounding
  filler" failure mode this whole pipeline exists to avoid.
- **Never put a drawing roster in the exhibit.** The sheet→package index is a retrieval tool that tells the
  drafter what to read; it is not exhibit content. Do not emit an "Applicable Drawings" or "Sheets Included"
  list, and do not enumerate a package's sheets anywhere in the draft. An enumerated sheet list in a
  subcontract works against the GC: it creates the negative implication that unlisted sheets do not apply,
  which narrows a broad "complete scope per plans and specifications" obligation into a bounded one and
  hands the subcontractor an argument in the first change-order dispute. It also goes stale the moment an
  addendum reissues a sheet. Cite a sheet only where it does work a citation should do — fixing a trade
  boundary, resolving an ambiguity, or pinning a basis of design — exactly as the Scope of Work narratives
  themselves do ("See A1-20 for Gate Schedule and details").
- **Write to the schedule and the specification, not to a model number.** A subcontract naming a specific
  model buys that model and nothing else; when a submittal returns a superseded part number the sub has an
  argument it was not in scope. Write *"all fan coil units and heat pumps as indicated on the mechanical
  schedule, including any additional parts and accessories for a complete installation"*, not *"one Daikin
  FXSA18AAVJU at the restrooms"*. Name a product only where a contract document establishes it as basis of
  design — an RFI answer, an addendum, a GMP Basis assumption, a drawn BOD keynote — then cite that
  instrument and still require a complete installation around it.
- **Think past what the documents happen to say.** This is a subcontract, not an RFP summary. If the manual
  has a masonry section and this is the masonry package, it belongs in the subcontract whether or not the
  scope narrative cited it — as do the ordinary obligations of a complete trade scope (layout from
  established control, protection of adjacent work, receiving and offloading, cleanup of own debris,
  warranty, submittal coordination). Assignments made by trade judgment are marked as such in the record;
  they belong in the subcontract, but only citation-backed items may be written as citations.
- If a package's `awarded_sub.flags` includes a PM-review flag (e.g. "awarded sub was not low bidder," "no
  signed Bid Form on file"), carry it forward as a visible note at the top of the draft, not silently.

Run 33 times (or however many packages the project has), one Task/Agent invocation per package_id.
Can be parallelized freely — each run is independent by design.

## Stage 3 — QA (`scope-qa` subagent, run once)

Input: all drafts in `02-drafts/`, every record in `01-index/packages/`, and the bid form.

Output: `03-qa/scope-leveling-register.xlsx` (or `.csv`/`.md` table if no xlsx writer is available —
columns: gap/overlap description, packages involved, severity, recommended resolution).

Checks:
1. **Gaps** — work documented somewhere in the source docs with no home in any Attachment A. Specifically
   check known gap zones: temp power, roof curbs/equipment pads, fire caulking, final grade/seed, access panels.
2. **Overlaps** — two packages both claiming the same scope.
3. **Proposal-vs-RFP contradictions** — for reconciled packages, does the awarded sub's proposal exclude
   something the RFP scope-of-work assumed was included (or vice versa)? This is the check unique to the
   "reconciled to awarded sub" drafting mode — flag every contradiction found, don't silently resolve it.

This step needs to hold the full leveling matrix in mind at once and catch what's missing rather than
generate forward from a template — use Opus-class reasoning (see `.claude/agents/scope-qa.md` model setting).

**Human Checkpoint #2**: PM resolves every flagged gap/overlap/contradiction — this is judgment the PM has
to own, not something to auto-resolve. Decide negotiable-vs-non-negotiable language per project norms.

## Stage 4 — Final Exhibit

Convert PM-approved drafts into the project's branded Attachment A exhibit format (docx), one per package,
landing in `04-output/`, ready to attach to the subcontract agreement template. This step is manual/PM-driven
once drafts are approved — no subagent needed unless the project has a docx-templating skill available.

## Reference

- `references/csi-divisions.md` — CSI MasterFormat division numbers, used to tag `csi_divisions` in the index
  and to map spec-manual-split filenames (`div-XX-*.pdf`) to package scope.
