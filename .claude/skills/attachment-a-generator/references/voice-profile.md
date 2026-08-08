# Attachment A voice profile

How this PM writes the SCOPE OF WORK section of an Attachment A, induced from 40 exhibits he
wrote and CORE executed, across two jobs — not from general contract-drafting advice, and not
from the blank template.

`scope-drafter` reads this before writing any scope group, and `scripts/voice_check.py`
enforces the mechanical half of it before an exhibit is built.

---

## Corpus and authorship

Every record in `01-index/voice-corpus.jsonl` carries an `author` and a `project`.

| `author` | What it is | Scope items | Weight |
|---|---|---:|---|
| `self` | **The PM's own SCOPE OF WORK sections** | 1,554 | **The authority.** Outranks everything below |
| `core` | Another CORE author's executed exhibit, and the blank templates | 295 | House style. Governs only where `self` is silent |
| `claude` | This project's generated drafts | 102 | Never defines a rule. Present so drift is measurable |

The `self` corpus spans **two jobs, two years apart**:

| Job | Exhibits | Scope items |
|---|---:|---:|
| 21-01-013 — UNLV College of Engineering, Academic & Research Building | 32 | 1,168 |
| 23-01-011 — SPWD Silverado Ranch Facility (DMV) | 8 | 386 |

Two jobs is what makes this a voice profile rather than a description of one job's conventions.
Every rule below is checked on both, and the report prints that comparison
(`## Does it hold across jobs?` in `01-index/voice-corpus-stats.md`). **A probe that swings
hard between his jobs is a convention, not a voice rule, and is not enforced as one.**

**The SCOPE OF WORK and EXCLUSIONS sections are his** — confirmed 08.08.26. The
construction-documents list, project-specific provisions and scope options are not: they are
assembled from the spec manual, are standing contract terms, or are priced adds, and stay
`core` even inside his own files (`SELF_SECTIONS` in `build_voice_corpus.py`).

| Confidence | Means |
|---|---|
| **fixed** | Boilerplate. The template supplies it verbatim; not a writing choice |
| **high** | Holds on both jobs, with a wide margin over the other author |
| **medium** | Holds on both jobs but at a low rate, or swings between them |
| **thin** | Real but rare — a handful of instances. Do not generalise |
| **open** | Unsettled. Listed as a decision at the bottom |

---

## 1. What is voice here, and what is not

An Attachment A is three layers, and only one is written by a person:

1. **The template's contract prose** — "Subcontractor has accounted for, as part of this lump
   sum Subcontract…". Identical on every exhibit CORE issues. `build_attachment_a.py` only
   edits highlighted runs, so this layer is byte-identical to the template. Do not paraphrase
   it, improve it, or reason about it.
2. **The fixed formulas** — group header, spec-section line, directive line. Fill in the
   blanks; do not restyle.
3. **The scope items** — the authored layer, and the PM's own work. Everything below is about
   this layer.

## 2. The group header is a formula — `fixed`

```
<Trade Name> - Provide all materials, labor, equipment, and supervision for a complete
Scope of Work per plans and specifications. This Scope of Work shall include, but not be
limited to:
```

Across 49 of his group headers the **structure never varies**. Only the casing does — and his
own majority is the lowercase form:

| | count |
|---|---:|
| Verbatim | 15 |
| Same words, lowercase "scope of work" | 26 |
| Trade name repeated inside, or truncated | 8 |

**Write it capitalised anyway.** *Scope of Work* is a defined term in the Subcontract and the
template capitalises it; the lowercase drift is a typing habit, not a decision. This is the one
place the profile recommends against his majority practice, and it is a casing question with no
commercial consequence.

Where a trade's name has a common abbreviation, define it in the header and use the short form
below: *"Fiber-Reinforced Plastic (FRP) Paneling - Provide all materials…"*.

## 3. Scope items are SHORT — `high`

**Median 13 words** across 1,554 items. Quartiles 9 / 13 / 22, p90 32, p95 40, p99 57.

The distribution shape matters more than any single number:

| | items | median | p90 |
|---|---:|---:|---:|
| **PM — 21-01-013** | 1,168 | **13** | 32 |
| **PM — 23-01-011** | 386 | **14** | 32 |
| CORE, other author | 295 | 28 | 34 |
| Current drafts | 102 | 26 | 43 |

Note what does *and does not* separate them. The 90th percentiles are nearly identical (32 vs
34) — both authors write the occasional long item. **The median is the whole difference:** his
typical item is half the length of the other author's, because most of his items do one small
thing. `Includes all half-height doors.` is a complete, enforceable item at five words.

So the check is on the *package median*, not on individual items. `voice_check.py` errors only
past 60 words — just beyond his p99, where an item is almost certainly two obligations — and
reports the package median separately. A wordy register is one finding, not twenty.

## 4. `Includes …` is the signature construction — `high`

**244 of 1,554 items (15.7%) open with `Includes`, against 1 of 295 (0.3%) for the other
author.** A verb-initial fragment with no subject, pulling a specific thing inside a scope the
group header already established:

> "Includes frames at kiosks, mockup, and half-height door frames."
> "Includes compound radius trusses as required to achieve compound radius structure at DMV roof."
> "Includes 40 additional manhours to complete minor repairs due to undefinable or miscellaneous damage."
> "Includes surfaces receiving intumescent coatings."

The rate swings between jobs — 12% on 21-01-013, 27% on 23-01-011 — so treat the *construction*
as established and the frequency as a range, not a target.

⚠️ An earlier version of this file presented `Includes X, excluding Y` as a characteristic
pattern. It occurs **once** in 1,554 items. Withdrawn — see `thin` in the table above.

## 5. Install verbs — `high`

| | PM | Other author |
|---|---:|---:|
| `Supply and install` | **183 (11.8%)** | 3 (1.0%) |
| `Provide …` | 274 (17.6%) | 21 (7.1%) |
| `Provide and install` | 25 (1.6%) | 10 (3.4%) |

`Supply and install` is the install verb, stable across both jobs (11% and 14%).
`Provide and install` — which the blank template uses in 24% of its examples — he uses at 1.6%,
*less* than the other author does. Don't reach for it.

Other openers in his corpus: `Coordinate with` · `Subcontractor shall` · `Furnish and install` ·
`Verify` · `Prepare` · `Reinforce` · `Supply and apply` · `Install only` · `Supply all`.

`Supply only, F.O.B. jobsite` is his form for supply-without-install (4 instances — `thin`, but
precise where it fits: structural steel embeds and bollards).

## 6. Abbreviate freely — `high`

**He writes `CMU`, `MEP`, `FRP`, `HSS`, `HVAC`, `RTU`, `BMS`, `AHU`, `E.I.F.S.`, `F.O.B.`,
`AHJ`, `LLV`, `NRC`, `VIN`, `CDL` without expansion.**

⚠️ An earlier version of this file said the opposite — spell out `Concrete Masonry Unit`, never
write `CMU` — on the strength of one masonry exhibit by a different author. It was wrong for
this PM, and `voice_check.py` would have flagged his own writing. Withdrawn.

Defining an abbreviation on first use appears 8 times (`thin`) and is worth copying when the
term is not universal: *"fiberglass reinforced plastic (FRP) panels"*, *"Testing, Adjusting,
and Balancing (TAB)"*.

## 7. Name the trade you are coordinating with — `high`

| | PM | Other author |
|---|---:|---:|
| `Coordinate` opener | **125 (8.0%)** | 3 (1.0%) |
| Coordination sentence anywhere | **177 (11.4%)** | 5 (1.7%) |
| Capitalised `<Trade> Subcontractor` | **96 (6.2%)** | 4 (1.4%) |

Holds on both jobs (7%/10% and 10%/15%). It always names a counterparty by its subcontract role:

> "Coordinate with Low Voltage Subcontractor to ensure that all doors and frames to receive
> door contact sensors, access controls, and card readers are properly prepped."
> "Coordinate with Fire Sprinkler, Plumbing, and HVAC Subcontractors for hanging loads."
> "Coordinate all keying requirements with Contractor and Owner, including providing keying
> schedule required to obtain Letter of Authorization."

Capitalised as a proper noun — *Low Voltage Subcontractor*, *Electrical Subcontractor* — never
"the electrician" or "the GC". Defined contract terms stay capitalised throughout: Scope of
Work, Subcontract Amount, Contract Documents, Project Manual, Owner, Architect, Contractor.

## 8. `as indicated` is the citation idiom — `high`

| | PM | Other author |
|---|---:|---:|
| `as indicated` / `as detailed` / `as scheduled` | **147 (9.5%)** | 2 (0.7%) |
| `specifically referencing` | **0** | 8 (2.7%) |
| `per plans and specifications` inside an item | 1% | 3% |
| Detail or sheet number | 18 (1.2%) | 3 (1.0%) |

The dominant form is the light one — `as indicated`, `as indicated and required`, `as
scheduled` — carried by 9.5% of his items and stable across jobs. Pinpoint drawing citations
are used **sparingly**, where a specific detail fixes the obligation:

> "LLV steel angles for Kiosk Screen connection per 5/S5.44."
> "1/4" Bent plate wall cover per 13/AS4.01."
> "Tube steel and steel angle at Security Grille per detail 23/A2.16."

⚠️ Two earlier claims here were wrong and are withdrawn. The blank template's
`specifically referencing` idiom was recommended — he never uses it. And the profile reported
that he cites spec-section numbers at 0% "against 33% for the other CORE author": that 33% came
from the other author's CONSTRUCTION DOCUMENTS *list* lines, not scope items. Compared like
with like, **neither author cites spec sections inside a scope item** (5 of 1,554 vs 0 of 295).
Spec sections belong in the CONSTRUCTION DOCUMENTS section, which is not the PM's layer.

## 9. Numbers are bare numerals — `high`

`40 additional manhours`, `35 steel pipe bollards`, `1/4" Bent plate`, `24" and 42" AFF`,
`roughly 47,000 SF`.

The word-plus-parenthesis form (`thirty-four (34)`) is the blank template's habit — 24% of its
examples — and appears in **0.8%** of his items, less than the other author's 2.7%. Never spell
a dimension longhand: `4" x 6"`, not "four inches by six inches".

He also does not use `(i.e., …)` or `(e.g., …)` in scope items — 0 of 1,554, against 2.0% for
the other author.

## 10. Standing obligations get one line each — `medium`

Testing, layout, protection and cleanup appear as their own short items, not folded into a
paragraph:

> "Provide all tests and certifications required for complete and operational systems."
> "Provide all layout related to this scope of work."
> "All templates shall arrive to jobsite preassembled with bolts attached to templates."
> "Exterior structural members shall be sealed watertight."

An obligation that constrains *how* rather than *what* is written `<Noun> shall <verb>` — the
one place he drops the imperative opener.

⚠️ An earlier rule here claimed scope-expanding language (`whether shown or not`) was
characteristic. It occurs **once** in 1,554 items. Withdrawn.

## 11. The closing group is titled bare — `high`

Most packages end with a catch-all group covering testing, coordination, cleanup and the like.
**It appears 25 times across his 40 exhibits, and he writes the title on its own line with no
formula after it:**

```
General Scope Requirements
   Provide all tests and certifications required for complete and operational systems.
   Subcontractor responsible for scope coordination, including but not limited to:
   Coordinate roof penetration requirements with Roofing Subcontractor to maintain
   roofing system integrity and warranty.
```

Not `<Title> - Provide all materials, labor, equipment, and supervision…` — that formula is for
trade groups. And **not** `<Title> - The following requirements shall apply to all work under
this Scope of Work package:`, which both current drafts use and which appears nowhere in his
writing or in the template. `voice_check.py` errors on that sentence.

⚠️ This was warned about as an unverified invention when the corpus was one exhibit. With 40 it
resolves the other way: the *group* is his, the *sentence* is not.

## 12. Exclusions are terse noun phrases, and do not route — `high`

**192 exclusion lines. Median 5 words**, p75 8, p90 11. Sentence case, no trailing period, no
verb:

> Building permits · Shoring for concrete pours · Glazing at non-rated door lites ·
> Dedicated firewatch · Furnishing and placing of grout · Cost of inspection and tests ·
> All non-ferrous material · Roof access hatches

**They do not say who has the work instead: 2 of 192 (1.0%).** No "by others", no "which is
included in the X Scope of Work". An exclusion states that this Subcontractor is not doing it
and stops there.

Only four lines recur across many exhibits — *Building permits*, *Payment and Performance
Bond*, *General Liability Insurance – Onsite Coverage*, *Temporary power*. Those are the
standing defaults. **134 of 152 distinct lines appear on exactly one exhibit**, written off
that package's descope, and some cite a sheet: *"Site fencing and gates at mechanical yard and
outdoor breakroom per AS2.14 & AS4.02."*

Qualifiers are used sparingly where a boundary needs one (6%): *"Shoring and bracing, except as
included above."*

### Why not route

An earlier version of this file recommended the opposite — that exclusions name the package
that *does* carry the work, on the reasoning that it forecloses the "then nobody has it"
argument. That recommendation is withdrawn.

Routing writes a representation about **another subcontract's contents** into this one. Telling
the signage subcontractor that track signage sits in the sitework package is a statement by
CORE about what the sitework subcontract contains — and if it does not contain it, the
subcontractor has that in writing. On this project that risk was live: RFP-008 and ITB-072 both
excluded track and field signage, so the routing would have been false.

Route only where the receiving package is already bought and its executed Attachment A actually
carries the work. Otherwise exclude and stop.

## 13. Small packages skip the group-header structure — `medium`

A scope small enough to state in two or three items is written as flat items directly under the
turnkey clause, with no trade group header at all. The $33,700 cleaning package is two items.
Do not manufacture group headers for a package that does not need them.

---

## Open decisions

**D1. `Provide and install` vs `Supply and install` — CLOSED.** `Supply and install`, 11.8%
against 1.6%. See rule 5.

**D3. Standing operational obligations — CLOSED.** Present across both jobs as short single-line
items. See rule 10.

**D2. Exclusion style — CLOSED 08.08.26, from evidence.** The exclusions on his exhibits were
tagged `core` on his description of his own role and never read. Reading them showed 134 of 152
distinct lines unique to a single exhibit, several citing sheet numbers — authored per package,
not template. He confirmed they are his, `SELF_SECTIONS` gained `"exclusions"`, and rule 12 is
the measured result: terse, median 5 words, 1% routed. The earlier recommendation to keep the
drafts' routing is withdrawn there, with the reasoning.

---

## Growing the corpus

```
00-source-docs/voice-corpus/mine/        exhibits the PM wrote      (author: self)
00-source-docs/voice-corpus/             anyone else's, house style (author: core)
```

The subfolder is the entire authorship signal. `.pdf` and `.docx` are read directly; Bluebeam
FINAL packets can go in whole, since the exhibit body is found by its own `Page 1 of N` footer.

Exhibits pulled from OneDrive cannot be downloaded as PDFs from a Claude Code session — the
Graph connector returns extracted text, not bytes. `scripts/ingest_packet_text.py` takes that
text, finds the exhibit inside the packet, and writes it to `mine/text/`.

```
python3 scripts/build_voice_corpus.py     # rebuild + re-measure
python3 scripts/voice_check.py --all      # re-check every drafted package
```

At 40 exhibits over two jobs the openers, length distribution and citation idiom have stopped
moving; a third job would mostly re-confirm them. With D2 closed there is no open question the
corpus is waiting on. The one register not represented is a job outside Nevada public works.

The PM markup loop (`read_att_a_markup.py`) captures every edit he makes to a draft in review,
and those edits *are* `self`-authored — a change made twice is a rule that belongs in this file.
