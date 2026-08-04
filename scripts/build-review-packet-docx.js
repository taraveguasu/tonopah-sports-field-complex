/**
 * Build the PM Review Packet as a Word document.
 *
 * Reads the index artifacts directly so figures match the repo rather than being
 * retyped, and restores the full text that the markdown version truncated to fit
 * its table columns.
 *
 * Usage:  node scripts/build-review-packet-docx.js
 * Writes: 04-output/PM-Review-Packet-v2.docx
 */
const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  LevelFormat, PageBreak,
} = require('docx');

const ROOT = path.resolve(__dirname, '..');
const IDX = p => JSON.parse(fs.readFileSync(path.join(ROOT, '01-index', p), 'utf8'));
const v2 = IDX('package-index-v2.json');
const audit = IDX('file-coverage-audit.json');

const GREEN = '008348', DEEP = '004E2B', ASPHALT = '282828';
const DANGER = 'B3261E', WARN = '8A6100', CEMENT = 'BDBEC0', CONCRETE = 'F2F3F3';
const CONTENT_W = 9360; // Letter (12240) minus 1" margins each side

/* ── helpers ─────────────────────────────────────────────────────────────── */
const P = (text, o = {}) => new Paragraph({
  spacing: { after: o.after ?? 120, before: o.before ?? 0, line: 276 },
  alignment: o.align, indent: o.indent, border: o.border,
  children: [new TextRun({ text, bold: o.bold, italics: o.italics, size: o.size ?? 21,
                           color: o.color, font: o.font })],
});
const H = (text, level, o = {}) => new Paragraph({
  heading: level, spacing: { before: o.before ?? 280, after: o.after ?? 120 },
  children: [new TextRun({ text, bold: true, color: o.color ?? DEEP, size: o.size })],
});
const QUOTE = text => new Paragraph({
  spacing: { after: 100, line: 264 }, indent: { left: 360 },
  border: { left: { style: BorderStyle.SINGLE, size: 12, color: GREEN, space: 8 } },
  children: [new TextRun({ text, size: 20, color: ASPHALT })],
});
const RULE = () => new Paragraph({
  spacing: { before: 200, after: 200 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: CEMENT } },
  children: [new TextRun({ text: '' })],
});
const cell = (children, w, o = {}) => new TableCell({
  width: { size: w, type: WidthType.DXA },
  shading: o.fill ? { type: ShadingType.CLEAR, fill: o.fill, color: 'auto' } : undefined,
  margins: { top: 80, bottom: 80, left: 120, right: 120 },
  children: Array.isArray(children) ? children : [children],
});
const table = (widths, rows) => new Table({
  columnWidths: widths, width: { size: CONTENT_W, type: WidthType.DXA },
  borders: {
    top: { style: BorderStyle.SINGLE, size: 4, color: CEMENT },
    bottom: { style: BorderStyle.SINGLE, size: 4, color: CEMENT },
    left: { style: BorderStyle.SINGLE, size: 4, color: CEMENT },
    right: { style: BorderStyle.SINGLE, size: 4, color: CEMENT },
    insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: CEMENT },
    insideVertical: { style: BorderStyle.SINGLE, size: 4, color: CEMENT },
  },
  rows,
});
const hdrRow = (labels, widths) => new TableRow({
  tableHeader: true,
  children: labels.map((l, i) => cell(P(l, { bold: true, size: 18, color: 'FFFFFF' }), widths[i], { fill: DEEP })),
});
const bodyRow = (cells, widths, fill) => new TableRow({
  children: cells.map((c, i) =>
    cell(typeof c === 'string' ? P(c, { size: 19 }) : c, widths[i], fill ? { fill } : {})),
});
const BULLET = t => new Paragraph({
  numbering: { reference: 'bul', level: 0 }, spacing: { after: 80, line: 264 },
  children: [new TextRun({ text: t, size: 20 })],
});
/** Decision line the PM writes on. */
const DECIDE = (label, options) => [
  P(label, { bold: true, before: 120, after: 60, color: DEEP }),
  ...(options ? [P(options.map(o => '☐  ' + o).join('        '), { size: 20, after: 60 })] : []),
  new Paragraph({
    spacing: { after: 200 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: CEMENT } },
    children: [new TextRun({ text: '', size: 22 })],
  }),
  new Paragraph({
    spacing: { after: 240 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: CEMENT } },
    children: [new TextRun({ text: '', size: 22 })],
  }),
];

/* ── Part A content ──────────────────────────────────────────────────────── */
const RFP030 = v2.packages['RFP-030'];
const A1_SAMPLES = RFP030.scope_items_verbatim.filter(s =>
  /slot drain|Dowel all exterior|slick dowels|Athletic Equipment footings|sacking exposed/i.test(s)).slice(0, 5);

const A1_SUMMARY =
  'Site Concrete. Supply and place concrete and reinforcement for all site flatwork, athletic equipment pads, ' +
  'curbs, take-off boards, turndown edges, and associated concrete items, including layout. Concrete curbs at the ' +
  'Synthetic Turf Sports Field and Running Track. Slot/trench drains and concrete curb along the track perimeter ' +
  'per detail D/L1.03, including excavation, trenching, bedding, backfill, all piping, radius slot drains, storm ' +
  'drain collector pipe, concrete encasements, cleanouts, and storm water drainage structures — connection to ' +
  'the site storm drainage system by others. Equipment pads including transformer pad. Keyed, saw-cut, control and ' +
  'expansion joints with filler, sealants, and white cap; control joint layout shop drawings for architectural ' +
  'approval. Dowel exterior sidewalks to the building slab at all entrances and doorways whether or not detailed, ' +
  'and provide 5/8" x 18" slick dowels at 18" o.c. minimum at all cold joints whether shown or not. Cast-in-place ' +
  'footings for site items including overexcavation per the Geotechnical Report: scoreboard, pressbox, ticket booth ' +
  'slab-on-grade and footings, bleacher footings and grade beams, athletic equipment footings (football goal posts, ' +
  'high jump posts), and sports field light pole bases — coordinating requirements with each respective ' +
  'subcontractor. Sacking of exposed surfaces, drypack under light pole base plates, and installation of anchor ' +
  'bolts furnished by others (templates by Electrical). Install steel embeds and bollards supplied by others, with ' +
  'footings, concrete infill and domed tops. Supply Type II, prepare sub-base, place and compact.';

const A2_SEAMS = [
  ['"Scoreboard footings. Coordinate with Scoreboard Subcontractor"', 'Does ITB-089 exclude its own footings?', 'ITB-089'],
  ['"Pressbox footings… Bleacher footings / grade beams"', 'Does RFP-094 exclude footings?', 'RFP-094'],
  ['"Prefabricated Ticket Booth slab-on-grade and footings"', 'Does RFP-109 exclude slab and footings?', 'RFP-109'],
  ['"Athletic Equipment footings (football goal posts, high jump posts)"', 'Does ITB-019 exclude footings?', 'ITB-019'],
  ['"installing anchor bolts furnished by others… templates supplied by Electrical"', 'Who furnishes vs installs?', 'RFP-103'],
  ['"Install all steel embeds (supplied by others)… all bollards"', 'Who supplies?', 'RFP-033'],
  ['"Coordinate required masonry laps… rebar safety caps"', 'Handoff point', 'RFP-031'],
  ['"sleeves in slab-on-grade" / "layout requirements"', 'Sleeve and layout responsibility', 'RFP-098, RFP-100, RFP-103'],
];

const A3_PROMOTE = [
  ['S1-30  Foundation Plan – Scoreboard', '"Scoreboard footings"'],
  ['S1-40  Foundation Plan – Home Grand Stands', '"Bleacher footings / grade beams"'],
  ['S2-10  Foundation & Roof Framing – Concessions', '"continuous footings, slab-on-grade, turned-down edges"'],
  ['S3-00, S3-01  Typical Foundation Sections', '"cast-in-place footings", "stepped footings at utility entrances"'],
  ['S0-00  General Notes', '"Class D Seismic Design Category; Importance Factor 1.0"'],
  ['A1-20  Site Details  ⚠', '"expansion joints… control joints" — must be re-read at ADD 1 revision'],
];

/* ── Part B content ──────────────────────────────────────────────────────── */
const PART_B = [
  ['B1', 'HIGH', 'Three packages have no specification from any source',
   'ITB-008 Surveying, ITB-066 Fluid-Applied Flooring and RFP-109 Ticket Booth have no "Primary Specifications" ' +
   'section in their scope docs — verified against the source text, not a parsing artifact. The other 30 docs ' +
   'all have one. ITB-066 also has no matching CSI section in the spec manual, so it has no execution standard ' +
   'from any source. RFP-109’s substitute is the written spec block on sheet A1-40.',
   'What governs execution for each?'],
  ['B2', 'HIGH', '"070 Final Cleaning" — four proposals, no package',
   'CSI, Lady Lux and Nevada Angels (plus a Nevada Angels descope) bid a package numbered 070 Final Cleaning. ' +
   'No such package exists on either the 1% list or the ITB list. Final cleaning is the classic scope every trade ' +
   'assumes belongs to someone else.',
   'Is this a 34th package, a CORE general-conditions scope, or folded into another package?'],
  ['B3', 'HIGH', 'Prevailing wage — Clark County vs Nye County',
   'Clarification No. 2 replaced the prevailing wage section in its entirety and directs bidders to CLARK County ' +
   'rates. The project sits in Nye County, and CLAUDE.md records the Southern Nevada Rural Region. This affects ' +
   'all 33 subcontracts as a direct cost and compliance item.',
   'Which rate schedule governs?'],
  ['B4', 'MEDIUM', '"065 Sealed Concrete" straddles ITB-066 and ITB-067',
   'Sealed concrete appears under filename numbers 065, 066, 067 and combined "066, 067". Both packages currently ' +
   'show the identical four bidders (FW Specialties, NRC, Ryerson, SI Legacy), and ITB-066 has no spec section.',
   'Which package carries sealed concrete?'],
  ['B5', 'MEDIUM', 'Supply-only vs install-only bids split several packages',
   'ITB-019: Exerplay and SportsEdge bid SUPPLY, Great Western bid INSTALL. ITB-056: Hallgren SUPPLY, SNV ' +
   'Specialties INSTALL. RFP-094 and RFP-109 received SUPPLY-only proposals — but sheet A1-20’s Site ' +
   'Equipment Matrix designates Bleachers, Press Box and Ticket Booth as CFCI (contractor furnished, contractor ' +
   'installed), so those cannot be left supply-only.',
   'For each split package, which package carries installation?'],
  ['B6', 'MEDIUM', 'Procurement flags on proposals',
   '15 proposals have no signed Bid Form, 5 are late, 2 bypassed Building Connected, 2 are marked DO NOT USE, and ' +
   '1 is value-only with no scope detail (Conti, RFP-103). RFP-045’s awarded sub Foursquare carries both the ' +
   'no-Form and the bypassed-Building-Connected flags. NRS 338.16995 governs the 1% list, so this is a procurement ' +
   'process exposure rather than a paperwork gap.',
   'Do any of these block subcontract execution?'],
  ['B7', 'MEDIUM', '32 91 13 leveling exposure on RFP-016',
   'Your ruling put Section 32 91 13 Track & Field Event Inorganic Material Mix — the discus and shot put ' +
   'material — in RFP-016. BrightView/GTI’s scope review explicitly EXCLUDED "discuss and shot put pads". ' +
   'The awarded sub is Black Canyon.',
   'Confirm Black Canyon carries 32 91 13.'],
  ['B8', 'LOW', 'Addendum #1 change list disagrees with the revised drawing index',
   'The addendum’s narrative §5.01 names five reissued sheets. The revised G0-00 drawing index marks ' +
   'seven, adding A2-10 and A10-30 — both of which carry real scope changes (locker re-layout, new filler ' +
   'keynote, restroom partition changes). A bidder working from the addendum text gets a different picture than ' +
   'one cross-checking the cover sheet.',
   'Worth raising with KNIT? Should the subcontract state that G0-00’s index governs current revisions?'],
  ['B9', 'LOW', 'Two project facts still unconfirmed',
   'The CORE job number is recorded as "likely 25-10-003". The Precon→Ops handoff date, which starts the ' +
   '30-day buy-out clock, is still TBD — which is why the Buy-Out Console shows TBD rather than a countdown.',
   'Confirm both.'],
];

/* ── Part C ──────────────────────────────────────────────────────────────── */
const SPOTCHECK = ['RFP-030', 'RFP-008', 'ITB-077', 'RFP-016'];
const inv = IDX('proposal-inventory.json');

/* ── build ───────────────────────────────────────────────────────────────── */
const kids = [];

kids.push(new Paragraph({
  spacing: { after: 60 },
  children: [new TextRun({ text: 'CORE CONSTRUCTION', bold: true, size: 20, color: GREEN,
                           characterSpacing: 60 })],
}));
kids.push(H('Attachment A Index — PM Review Packet (v2)', HeadingLevel.TITLE, { before: 0, after: 60 }));
kids.push(P('Tonopah THS Sports Complex  ·  Nye County School District  ·  CMAR / GMP',
            { size: 22, color: ASPHALT }));
kids.push(P('Generated 2026-07-31 from 01-index/package-index-v2.json and companions. Every figure and quotation ' +
            'below is pulled from the artifacts, not retyped.', { size: 19, italics: true, color: ASPHALT }));
kids.push(RULE());
kids.push(P('How to use this packet', { bold: true, color: DEEP }));
kids.push(BULLET('Part A gates everything else and takes minutes. Three structural decisions that shape all 33 exhibits.'));
kids.push(BULLET('Part B is nine open decisions only you can settle, ranked by severity.'));
kids.push(BULLET('Part C is a four-package content spot-check to confirm the verbatim parse is faithful.'));
kids.push(BULLET('Part D lists what is known to be still missing, so nothing is hidden going into review.'));
kids.push(P('The parts are ordered by leverage — stop wherever you like.', { size: 19, italics: true, after: 200 }));

/* PART A */
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(H('Part A — Three structural decisions', HeadingLevel.HEADING_1, { before: 0 }));
kids.push(P('These decide the shape of all 33 exhibits. Every option below is worked out using RFP-030 Concrete, ' +
            'so you are comparing actual output rather than choosing from a description.', { color: ASPHALT }));

kids.push(H('A1.  How scope items are stored', HeadingLevel.HEADING_2));
kids.push(P(`RFP-030’s scope doc contains ${RFP030.scope_items_verbatim.length} items across three sub-scopes ` +
            '(Site Concrete, Cast-in-Place Structural, General Requirements).'));
kids.push(H('Option 1 — Verbatim (what the index does today)', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('Every sentence stored exactly as written, unedited. Five of the 72:', { size: 20 }));
A1_SAMPLES.forEach(s => kids.push(QUOTE(s)));
kids.push(P('Length: 72 lines.   Traceability: every line quotable back to the scope doc verbatim.',
            { bold: true, size: 19 }));

kids.push(H('Option 2 — Summarized', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('Same scope condensed to prose. This is RFP-030’s Site Concrete sub-scope written out from its ' +
            '24 verbatim items, losing nothing material:', { size: 20 }));
kids.push(QUOTE(A1_SUMMARY));
kids.push(P('Length: roughly one paragraph per sub-scope, so about 3 paragraphs instead of 72 lines.',
            { bold: true, size: 19 }));
kids.push(P('What you give up: you can no longer cite one sentence and point at it in the scope doc. Merging ' +
            'sentences also blurs boundaries — note how "whether or not detailed on drawings" and "whether ' +
            'shown or not" now sit mid-paragraph, when verbatim they stand out as the deliberate catch-all ' +
            'provisions they are.', { size: 20, color: DANGER }));

kids.push(H('Option 3 — Both', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('Verbatim retained in the index as the source of record; condensed prose generated into the exhibit. ' +
            'Costs nothing but a generation step — the exhibit reads cleaner while the index stays quotable.',
            { size: 20 }));
kids.push(...DECIDE('DECIDE A1:', ['Verbatim only', 'Summarized only', 'Both']));

kids.push(H('A2.  What gap/overlap QA is built on', HeadingLevel.HEADING_2));
kids.push(H('Option 1 — Coordination clauses (what I proposed)', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P(`RFP-030’s scope doc names ${RFP030.coordination_clauses.length} coordination clauses. Each names ` +
            'a counterparty, so each becomes a specific checkable question:', { size: 20 }));
{
  const w = [4200, 3200, 1960];
  kids.push(table(w, [
    hdrRow(['RFP-030 says', 'Seam to check', 'Counterparty'], w),
    ...A2_SEAMS.map((r, i) => bodyRow(r, w, i % 2 ? CONCRETE : undefined)),
  ]));
}
kids.push(P('→  8 distinct counterparties, 8 concrete questions, each traceable to a sentence in the contract.',
            { bold: true, before: 120, color: DEEP }));

kids.push(H('Option 2 — CSI divisions', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('RFP-030 is Division 03 Concrete. Checking overlaps by division finds only two packages: ITB-067 ' +
            'Concrete Finishing, which claims Division 03, and RFP-031 Masonry, which lists it as related.',
            { size: 20 }));
kids.push(P('What it misses: every footing seam above. Scoreboard, bleachers, press box, ticket booth and athletic ' +
            'equipment are Division 11/13 items — their footings are Division 03, but a division-level check ' +
            'never pairs RFP-030 with ITB-089 or ITB-019, because those packages are not Div 03. Those footing ' +
            'seams are exactly where your rulings have already been needed twice.',
            { size: 20, color: DANGER }));
kids.push(H('Option 3 — Both', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('Coordination clauses as the primary spine, CSI divisions as a secondary sweep to catch packages that ' +
            'share a division but never mention each other — which is how ITB-066 vs ITB-067 sealed concrete ' +
            'surfaced.', { size: 20 }));
kids.push(...DECIDE('DECIDE A2:', ['Coordination clauses', 'CSI divisions', 'Both']));

kids.push(H('A3.  How drawings get cited', HeadingLevel.HEADING_2));
kids.push(P(`RFP-030 today: ${RFP030.drawing_sheets.length} authoritative citation, ` +
            `${RFP030.drawing_sheet_candidates.length} candidates.`));
kids.push(H('Option 1 — Conservative (what the index does today)', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('Only sheets the scope narrative names outright become citations. Cited: L1.03, because the scope doc ' +
            'says "per detail D/L1.03". Held as candidates: L1.00, L1.01, L1.06, A1-12, A1-20 ⚠, S0-00, ' +
            'S0-01, S1-30, S1-40, S2-10, S3-00, S3-01.', { size: 20 }));
kids.push(P('Risk: RFP-030’s exhibit would cite one landscape detail sheet and none of the structural ' +
            'foundation sheets — no S1-30 Scoreboard Foundation, no S1-40 Home Grand Stands, no S3-00/S3-01 ' +
            'Typical Foundation Sections. For a concrete package that is visibly too thin.',
            { size: 20, color: DANGER }));
kids.push(H('Option 2 — Promote where the scope doc corroborates the content', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('Promote a candidate when the scope doc describes that work even without naming the sheet. Seven would ' +
            'become citations:', { size: 20 }));
{
  const w = [3800, 5560];
  kids.push(table(w, [
    hdrRow(['Sheet', 'Scope doc language that corroborates it'], w),
    ...A3_PROMOTE.map((r, i) => bodyRow(r, w, i % 2 ? CONCRETE : undefined)),
  ]));
}
kids.push(P('Would stay candidates: L1.00, L1.01, L1.06 (landscape sheets, more likely RFP-016/RFP-022 territory), ' +
            'A1-12, S0-01.', { size: 20, before: 120 }));
kids.push(H('Option 3 — Promote all, flag the doubtful', HeadingLevel.HEADING_3, { color: ASPHALT }));
kids.push(P('All 12 become citations; the landscape sheets carry a "verify ownership" flag. Risk: RFP-030’s ' +
            'exhibit would cite three landscape construction sheets. If those belong to RFP-016 or RFP-022, you ' +
            'have handed the concrete sub drawings for someone else’s work — the exact ' +
            'assignment-from-drawings failure that got v1 rejected.', { size: 20, color: DANGER }));
kids.push(...DECIDE('DECIDE A3:', ['Conservative', 'Promote where corroborated', 'Promote all, flag doubtful']));

/* PART B */
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(H('Part B — Open decisions', HeadingLevel.HEADING_1, { before: 0 }));
kids.push(P('Nine items only you can settle, ranked by severity.', { color: ASPHALT }));
PART_B.forEach(([id, sev, title, detail, ask]) => {
  const col = sev === 'HIGH' ? DANGER : sev === 'MEDIUM' ? WARN : ASPHALT;
  kids.push(new Paragraph({
    spacing: { before: 260, after: 80 },
    children: [
      new TextRun({ text: `${id}   `, bold: true, size: 24, color: DEEP }),
      new TextRun({ text: `[${sev}]  `, bold: true, size: 19, color: col }),
      new TextRun({ text: title, bold: true, size: 24, color: DEEP }),
    ],
  }));
  kids.push(P(detail, { size: 20 }));
  kids.push(...DECIDE('Decision needed: ' + ask));
});

/* PART C */
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(H('Part C — Content spot-check', HeadingLevel.HEADING_1, { before: 0 }));
kids.push(P('Four packages, chosen because they carry the most boundary surface or your recent rulings. For each, ' +
            'open the scope doc and confirm the index did not lose or distort anything.', { color: ASPHALT }));
SPOTCHECK.forEach(pid => {
  const p = v2.packages[pid], ip = inv.packages[pid] || {};
  kids.push(H(`${pid} — ${p.title}`, HeadingLevel.HEADING_2));
  kids.push(P('Open:  00-source-docs/' + p.scope_of_work_doc.file, { size: 19, font: 'Consolas' }));
  const specs = p.primary_specifications.map(s => `${s.section} ${s.title}`).join(';  ') || '—';
  const divs = p.primary_divisions.map(d => `Div ${d.division} ${d.title}`).join(';  ') || '—';
  const w = [2600, 6760];
  const rows = [
    ['Scope items captured', String(p.scope_items_verbatim.length) + ' (verbatim)'],
    ['Coordination clauses', String(p.coordination_clauses.length)],
    ['Alternates', String(p.alternates.length)],
    ['Primary specifications', specs],
    ['Primary divisions', divs],
    ['Bidders on file', `${ip.bidder_count || 0} — ${(ip.bidders || []).join(', ') || 'none'}`],
  ];
  if (p._pm_rulings) rows.push(['Your rulings applied', p._pm_rulings.map(r => r.ruling).join('  ')]);
  kids.push(table(w, rows.map(([k, v], i) =>
    new TableRow({
      children: [cell(P(k, { bold: true, size: 19 }), w[0], { fill: CONCRETE }),
                 cell(P(v, { size: 19 }), w[1])],
    }))));
  const cw = [6360, 3000];
  kids.push(new Paragraph({ spacing: { before: 120 }, children: [new TextRun({ text: '' })] }));
  kids.push(table(cw, [
    hdrRow(['Check', 'Verdict'], cw),
    bodyRow(['Scope items complete and undistorted', '☐ OK   ☐ Missing   ☐ Distorted'], cw),
    bodyRow(['Primary specifications correct', '☐ OK   ☐ Wrong   ☐ Incomplete'], cw, CONCRETE),
    bodyRow(['Alternates complete', '☐ OK   ☐ Missing'], cw),
  ]));
});

/* PART D */
kids.push(new Paragraph({ children: [new PageBreak()] }));
kids.push(H('Part D — What is still missing', HeadingLevel.HEADING_1, { before: 0 }));
const t = audit._totals;
kids.push(P(`The coverage audit walked all ${t.files_total} files under 00-source-docs. ${t.processed} are ` +
            `processed, ${t.derived_artifacts} are derived artifacts produced by this pipeline, and ` +
            `${t.NOT_PROCESSED} have never been opened — 17 of those are high impact and are listed in full ` +
            'below.', { color: ASPHALT }));
const partD = JSON.parse(fs.readFileSync(
  '/tmp/claude-0/-home-user-tonopah-sports-field-complex/d3ec1f7b-4441-5ca6-83a6-f24645257215/scratchpad/partD.json', 'utf8'));
partD.forEach(g => {
  kids.push(P(g.why, { size: 20, bold: true, before: 200, color: DEEP }));
  g.files.forEach(f => kids.push(BULLET(f)));
});
kids.push(RULE());
kids.push(P('Recommendation', { bold: true, color: DEEP }));
kids.push(P('Close the Bid Form and the four cut sheets before reviewing content. The Bid Form is a regression — ' +
            'the v1 index carried bid_form_line_items and v2 lost it — and the cut sheets resolve ' +
            'basis-of-design that has no other source. Defer the Attachment A/B templates, which are Stage 7 output ' +
            'format rather than index input, and read the geotech and asbestos reports while drafting the specific ' +
            'packages they govern (RFP-002, RFP-008, RFP-030) rather than as a blanket pass now.', { size: 20 }));

/* ── document ────────────────────────────────────────────────────────────── */
const doc = new Document({
  creator: 'CORE Construction',
  title: 'Attachment A Index — PM Review Packet (v2)',
  description: 'Tonopah THS Sports Complex — buy-out index review',
  numbering: {
    config: [{
      reference: 'bul',
      levels: [{ level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
                 style: { paragraph: { indent: { left: 460, hanging: 260 } } } }],
    }],
  },
  styles: {
    default: { document: { run: { font: 'Calibri', size: 21 } } },
    paragraphStyles: [
      { id: 'Title', name: 'Title', basedOn: 'Normal', next: 'Normal',
        run: { size: 40, bold: true, color: DEEP, font: 'Calibri' } },
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 30, bold: true, color: GREEN, font: 'Calibri' },
        paragraph: { spacing: { before: 300, after: 140 },
                     border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GREEN, space: 6 } } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 25, bold: true, color: DEEP, font: 'Calibri' },
        paragraph: { spacing: { before: 260, after: 100 } } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal', quickFormat: true,
        run: { size: 21, bold: true, color: ASPHALT, font: 'Calibri' },
        paragraph: { spacing: { before: 180, after: 80 } } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, bottom: 1080, left: 1440, right: 1440 } } },
    children: kids,
  }],
});

const out = path.join(ROOT, '04-output', 'PM-Review-Packet-v2.docx');
fs.mkdirSync(path.dirname(out), { recursive: true });
Packer.toBuffer(doc).then(b => {
  fs.writeFileSync(out, b);
  console.log(`wrote ${path.relative(ROOT, out)}  (${(b.length / 1024).toFixed(0)} KB)`);
});
