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

Output: `01-index/package-index.json` — see schema below.

Run once. Invoke the `doc-indexer` agent (`.claude/agents/doc-indexer.md`) with the project root path.

### Index schema (`01-index/package-index.json`)

```json
{
  "_generated": "ISO date",
  "_source_note": "one line on what was indexed and against what CLAUDE.md decision",
  "packages": {
    "<package_id>": {
      "title": "string",
      "source_list": "RFP | ITB",
      "csi_divisions": ["03", "30"],
      "scope_of_work_doc": "path relative to 00-source-docs/",
      "bid_form_line_items": ["string, ..."],
      "spec_sections": [
        {"division": "03", "section_number": "03 3000", "section_title": "Cast-In-Place Concrete",
         "source_file": "04-specs-reports/spec-manual-split/div-03-concrete.pdf"}
      ],
      "drawing_sheets": [
        {"sheet_number": "S-201", "sheet_title": "string", "source_file": "path"}
      ],
      "addenda_refs": [
        {"addendum": "Addendum #1 (05.06.26)", "item": "string", "source_file": "path"}
      ],
      "awarded_sub": {
        "name": "string or null",
        "status": "awarded | not-yet-awarded",
        "proposal_file": "path relative to 00-source-docs/SUBCONTRACTOR FILES/ or null",
        "descope_files": ["path", "..."],
        "flags": ["from 01-index/awarded-sub-mapping.json flags_for_pm_review, if any"]
      },
      "gap_zone_flags": ["temp power", "roof curbs/equipment pads", "fire caulking", "final grade/seed", "access panels"]
    }
  }
}
```

If a project has an `01-index/awarded-sub-mapping.json` (built separately — it requires cross-referencing
a subcontractor listing against a bid tabulation, which is judgment-heavy enough to do directly rather
than delegate), `doc-indexer` merges it in under `awarded_sub`. Packages with no mapping entry get
`"status": "not-yet-awarded"` and draft from generic scope only (see Stage 2).

**Human Checkpoint #1**: the PM reviews `package-index.json` by hand before any drafting starts. This is
the highest-leverage review point in the pipeline — every draft downstream inherits whatever's wrong here.

## Stage 2 — Draft (`scope-drafter` subagent, run once per package)

Input: one package's index entry (`01-index/package-index.json#packages.<package_id>`) plus the specific
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
- If a package's `awarded_sub.flags` includes a PM-review flag (e.g. "awarded sub was not low bidder," "no
  signed Bid Form on file"), carry it forward as a visible note at the top of the draft, not silently.

Run 33 times (or however many packages the project has), one Task/Agent invocation per package_id.
Can be parallelized freely — each run is independent by design.

## Stage 3 — QA (`scope-qa` subagent, run once)

Input: all drafts in `02-drafts/`, the full `01-index/package-index.json`, and the bid form.

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
