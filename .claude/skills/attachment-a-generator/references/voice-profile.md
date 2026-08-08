# Attachment A voice profile

How this PM writes the SCOPE OF WORK section of an Attachment A, induced from three exhibits
he wrote and CORE executed — not from general contract-drafting advice, and not from the blank
template.

`scope-drafter` reads this before writing any scope group, and `scripts/voice_check.py`
enforces the mechanical half of it before an exhibit is built.

---

## Corpus and authorship

Every record in `01-index/voice-corpus.jsonl` carries an `author`:

| `author` | What it is | Lines | Weight |
|---|---|---:|---|
| `self` | **The PM's own SCOPE OF WORK sections**, from `00-source-docs/voice-corpus/mine/` | 108 | **The authority.** Outranks everything below |
| `core` | Another CORE author's executed exhibit, and the blank templates' examples | 162 | House style. Governs only where `self` is silent |
| `claude` | This project's generated drafts | 138 | Never defines a rule. Present so drift is measurable |

The `self` corpus is three FINAL exhibits from **DMV Silverado Ranch** (SPWD, PWP# NY-2022-200),
across three trades: ADI (Doors, Frames & Hardware), Adams & Smith (Structural & Ornamental
Metals), Anning-Johnson (Metal Studs & Drywall). Three trades is enough to tell voice apart
from trade vocabulary, which one exhibit could not.

**Only the SCOPE OF WORK section of those exhibits is the PM's writing** — confirmed 08.08.26.
The construction-documents list, project-specific provisions, scope options and exclusions come
from the template and the contracts department, and are attributed `core` even inside the PM's
own files (`SELF_SECTIONS` in `build_voice_corpus.py`). So this profile is authoritative about
scope items and group headers, and says nothing personal about exclusions.

| Confidence | Means |
|---|---|
| **fixed** | Boilerplate. The template supplies it verbatim; not a writing choice at all |
| **high** | Clear in the PM's own corpus, consistent across all three trades |
| **medium** | Present in the PM's corpus but thin, or trade-specific |
| **house** | No `self` evidence. CORE practice, followed by default — flag rather than rely |
| **open** | Genuinely unsettled. Listed as a decision at the bottom |

Counts cite `01-index/voice-corpus-stats.md` and name their bucket; percentages are against
that bucket's own line count.

---

## 1. What is voice here, and what is not

An Attachment A is three layers, and only one of them is written by a person:

1. **The template's contract prose** — "Subcontractor has accounted for, as part of this lump
   sum Subcontract, the fact that the Contract Documents may not contain all required
   details…". Identical on every exhibit CORE issues. `build_attachment_a.py` only edits
   highlighted runs, so this layer is byte-identical to the template and carries no voice
   decisions. Do not paraphrase it, improve it, or reason about it.
2. **The fixed formulas** — the group header, the spec-section line, the directive line. Fill
   in the blanks; do not restyle. Rule 2.
3. **The scope items** — the authored layer, and the PM's own work. Everything below is
   about this layer.

## 2. The group header is a formula — `fixed`

```
<Trade Name> - Provide all materials, labor, equipment, and supervision for a complete
Scope of Work per plans and specifications. This Scope of Work shall include, but not be
limited to:
```

7 of the PM's 9 group headers carry it verbatim. (One drifts to lowercase "scope of work",
one is truncated after "for a complete" — both are slips, not variants.) Substitute only the
trade name. Where a trade's name has a common abbreviation, define it here and use the short
form below: *"Fiber-Reinforced Plastic (FRP) Paneling - Provide all materials…"*.

## 3. Scope items are SHORT — `high`

**Median 12 words. Quartiles 9 / 12 / 22. 90th percentile 33. Longest item in the corpus: 46.**

This is the largest single divergence from everything else in the corpus, and the one most
worth enforcing:

| | median | p90 | max | items > 45 words |
|---|---:|---:|---:|---:|
| **PM (self)** | **12** | 33 | 46 | **0** |
| CORE, other author | 28 | — | — | — |
| Current drafts | 26 | 43 | 71 | 7 |

The current drafts run more than double the PM's median. `Includes all half-height doors.` is
a complete, enforceable item at five words. One obligation per item, stated once — when an
item needs a comma-spliced second clause it is usually two items.

## 4. `Includes …` is the signature construction — `high`

**28% of the PM's scope items open with `Includes`, against 1% everywhere else.** It is a
verb-initial fragment with no subject, used to pull a specific thing inside a scope the group
header already established:

> "Includes frames at kiosks, mockup, and half-height door frames."
> "Includes all gate hardware, excluding cane bolts, gate boxes, hinges, and pivots."
> "Includes compound radius trusses as required to achieve compound radius structure at DMV roof."
> "Includes 40 additional manhours to complete minor repairs due to undefinable or miscellaneous damage."
> "Includes surfaces receiving intumescent coatings."

Note the pattern in the second one: `Includes X, excluding Y` — the inclusion and its carve-out
in a single line, rather than an item here and an exclusion four pages later.

## 5. Install verbs — `high`

**`Supply and install` is the verb: 18% of the PM's items, against 1–2% for every other
author.** `Provide and install` — which the blank template uses in 24% of its examples — appears
**once** in 108 lines. Do not use it.

The working set, in the PM's own frequency order:

`Supply and install` · `Includes` · `Provide` · `Supply only, F.O.B. jobsite` · `Coordinate with` ·
`Subcontractor shall` · `Provide all` · `Reinforce` · `Prepare` · `Verify` · `Layout, supply, and install` ·
`Supply and apply` · `Install only`

`Supply only, F.O.B. jobsite` is the specific form for supply-without-install — it appears in
the structural steel exhibit for embeds and bollards and it is more precise than "furnish".

## 6. Abbreviate freely; define non-obvious ones on first use — `high`

**The PM uses `CMU`, `MEP`, `FRP`, `HSS`, `HVAC`, `RTU`, `E.I.F.S.`, `F.O.B.`, `AHJ`, `FAA`,
`LLV`, `NRC`, `VIN`, `CDL` without expansion.**

⚠️ An earlier version of this file said the opposite — spell out `Concrete Masonry Unit`, never
write `CMU` — on the strength of one masonry exhibit by a different author. That rule was wrong
for this PM and `voice_check.py` would have flagged his own writing. It is withdrawn.

The real rule is lighter: use the trade's ordinary abbreviations, and where one is not
universally read, define it once in the group header and use the short form after —
`Fiber-Reinforced Plastic (FRP) Paneling`.

## 7. Name the trade you are coordinating with — `high`

Coordination appears in 7% of the PM's items, roughly double the other author's rate, and it
always names a counterparty by its subcontract role:

> "Coordinate with Low Voltage Subcontractor to ensure that all doors and frames to receive
> door contact sensors, access controls, and card readers are properly prepped."
> "Coordinate with Fire Sprinkler, Plumbing, and HVAC Subcontractors for hanging loads."
> "Coordinate all keying requirements with Contractor and Owner, including providing keying
> schedule required to obtain Letter of Authorization."

Capitalised as a proper noun — *Low Voltage Subcontractor*, *Electrical Subcontractor*,
*Framing Subcontractor* — never "the electrician" or "the GC". Defined contract terms stay
capitalised: Scope of Work, Subcontract Amount, Contract Documents, Project Manual, Owner,
Architect, Contractor, Subcontractor.

`by others` is used, but sparingly — 3% of items, less than the other author's 6%.

## 8. Cite the detail, not the specification — `high`

**The PM cites a spec section number in a scope item exactly zero times in 108 lines**, against
13% for the other CORE author. Scope items point at drawings:

> "LLV steel angles for Kiosk Screen connection per 5/S5.44."
> "Steel angle and HSS at Mechanical Roof Curbs per sheet S5.61."
> "Tube steel and steel angle at Security Grille per detail 23/A2.16."
> "Handrail closure plate and escutcheon rings per 8/ and 12/G1.02."
> "…per architectural drawings (MF-1 and MF-2 as indicated on Finish Schedule, sheet A2.05)."

Forms used: `per <detail>/<sheet>`, `per sheet <n>`, `per detail <d>/<sheet>`. Spec sections
belong in the CONSTRUCTION DOCUMENTS section of the exhibit, which is not the PM's layer.

`as indicated` / `as scheduled` / `as specified` is the general form when no single detail
governs — 15% of items, against 1% for the other author. The blank template's
`specifically referencing` idiom appears **zero** times in the PM's writing; an earlier version
of this file recommended it, which was wrong. This does not change `SKILL.md`'s rule against
enumerating a sheet roster — a pinpoint citation that does work is exactly what that rule asks
for.

## 9. Numbers are bare numerals — `high`

`40 additional manhours`, `35 steel pipe bollards`, `1/4" Bent plate`, `24" and 42" AFF`.

The word-plus-parenthesis form (`thirty-four (34)`) is the blank template's habit — 24% of its
examples — and appears in **1%** of the PM's items. Do not use it, and never spell a dimension
longhand: `4" x 6"`, not "four inches by six inches".

## 10. Write scope-expanding language deliberately — `medium`

Where a quantity or extent is uncertain, the PM closes the gap in the item rather than leaving
it to be argued:

> "Provide tube steel support posts at half walls, **whether shown or not**."
> "Provide all blocking under parapet caps, **whether wood or metal**."
> "**Include an additional 35** steel pipe bollards in addition to those shown on plans."
> "Joist design shall include **all additional live and dead loads as indicated on drawings**."

## 11. Standing obligations get one line each — `medium`

Testing, layout, protection and cleanup appear as their own short items, not as a paragraph:

> "Provide all tests and certifications required for complete and operational systems."
> "Provide all layout related to this scope of work."
> "All templates shall arrive to jobsite preassembled with bolts attached to templates."
> "Exterior structural members shall be sealed watertight."

An obligation that constrains *how* rather than *what* is written `<Noun> shall <verb>` rather
than as an imperative — that is the one place the PM drops the imperative opener.

---

## Open decisions

**D1. `Provide and install` vs `Supply and install` — CLOSED 08.08.26.** `Supply and install`,
18% against 1%. See rule 5.

**D2. Exclusion style — still open, and this corpus cannot close it.** The PM wrote only the
SCOPE OF WORK sections of the three exhibits on file; their exclusions are the contracts
department's and are attributed `core`. What is known is house practice: terse Title Case noun
phrases (*Concrete Footings*, *Anti-Graffiti Applications*), no routing. Current drafts instead
route the work — *"…which are included in the Scoreboards Scope of Work"* — which forecloses the
"then nobody has it" argument in a change-order dispute. Recommendation stands: keep the
routing, adopt Title Case. **Needs the PM's call, not more corpus.**

Worth noting alongside it: rule 4 shows the PM often handles carve-outs inside the inclusion
(`Includes all gate hardware, excluding cane bolts…`) rather than in the exclusions list at all.

**D3. Standing operational obligations — CLOSED 08.08.26.** Present across all three trades, as
short single-line items. See rule 11.

---

## Growing the corpus

`00-source-docs/voice-corpus/mine/` — exhibits the PM wrote. Anything else goes one level up,
in `00-source-docs/voice-corpus/`, and is read as house style only. The subfolder is the entire
authorship signal, so a self-authored exhibit filed in the wrong place is counted as somebody
else's.

`.pdf` or `.docx`; Bluebeam FINAL packets can go in whole — the exhibit body is found by its own
`Page 1 of N` footer and the cover sheet, price build-up, Bid Form and descope notes are ignored.

```
python3 scripts/build_voice_corpus.py     # rebuild + re-measure
python3 scripts/voice_check.py --all      # re-check every drafted package
```

What would sharpen this further: exhibits from **wet trades and sitework** — the current three
are all building-envelope and interior trades, so rules 8 and 10 may read differently on an
earthwork or utilities package. And if the PM ever writes an exclusions list himself, adding
`"exclusions"` to `SELF_SECTIONS` closes D2.

The PM markup loop (`read_att_a_markup.py`) captures every edit made to a draft in review, and
those edits *are* `self`-authored — a change made twice is a rule that belongs in this file.
