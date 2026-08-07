#!/usr/bin/env python3
"""
Build the Attachment A Review Cover Sheet and the contract-amount summary that
sits behind it.

The Bluebeam process document defines the REVIEW packet: cover sheet first, then
"on a separate sheet, include a summary of how we got to the contract amount that
is on the Cover Sheet", then the draft Attachment A, then the bid form, the
subcontractor's own proposal, scope-option backup, and the descope notes.

PM direction: the ONLY place to break out pricing is this cover sheet. The
Attachment A itself carries one LUMP SUM.

This opens CORE's own cover-sheet template and fills its cells, the same way
build_attachment_a.py edits the Word template rather than regenerating it. The
template highlights its editable fields in yellow -- D3, D4, D13, D15, D16, C19,
F19, plus the four approver-name cells -- and nothing outside that set is
touched, so the layout, column widths, row heights, merges, the
=SUM(F19,F21,F23,F25) total and the 'list' sheet all survive byte-for-byte.

Usage:  python3 scripts/build_att_a_cover.py RFP-008
"""

import json
import sys
from pathlib import Path

import openpyxl
from openpyxl.styles import Alignment, Border, Font, Side

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "01-index" / "attachment-a-content"
OUT = ROOT / "02-drafts"
TEMPLATE = (ROOT / "00-source-docs" / "05-supplemental" / "attachment-a-process" /
            "NV Attach A Review Log Cover Bluebeam Template 111425.xlsx")

PROJECT = "NCSD - Tonopah High School Sports Field Replacement"
PROJECT_NO = "26-01-019"

# Cells the template fills in yellow. Writing anywhere else is a template edit,
# not a fill-in, so the build refuses to do it.
EDITABLE = {"D3", "D4", "D13", "D15", "D16", "C19", "F19",
            "B7", "B8", "B9", "E7", "E8", "E9"}

BOLD = Font(bold=True)
THIN = Side(style="thin")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)


def put(ws, coord, value, number_format=None):
    if coord not in EDITABLE:
        raise ValueError(f"{coord} is not a highlighted field in the template")
    ws[coord] = value
    if number_format:
        ws[coord].number_format = number_format


def build(pkg):
    spec = json.loads((CONTENT / f"{pkg}.json").read_text())
    dest = OUT / pkg
    dest.mkdir(parents=True, exist_ok=True)

    wb = openpyxl.load_workbook(TEMPLATE)
    ws = wb["cover sheet"]

    put(ws, "D3", PROJECT)
    put(ws, "D4", PROJECT_NO)
    put(ws, "D13", spec["_subcontractor"])

    # Dates and the phase code are CORE-internal and are not derivable from the
    # bid documents. Blanked with a visible placeholder rather than guessed --
    # the date format is cleared so the text shows instead of a serial date.
    for coord in ("D15", "D16"):
        put(ws, coord, "CONFIRM", number_format="General")
    put(ws, "C19", spec.get("phase_code") or "CONFIRM")

    # One phase code per subcontractor (note under B19), so the whole contract
    # amount lands on the single F19 line and E27's SUM picks it up.
    put(ws, "F19", float(spec["_contract_amount"]))

    # ---- the separate summary sheet: how we got to the contract amount -------
    if "contract amount summary" in wb.sheetnames:
        del wb["contract amount summary"]
    s = wb.create_sheet("contract amount summary", 1)
    s.column_dimensions["A"].width = 72
    s.column_dimensions["B"].width = 18
    s["A1"] = f"How we got to the contract amount — {pkg} — {spec['_subcontractor']}"
    s["A1"].font = Font(bold=True, size=12)
    s["A2"] = ("Reconciled to GMP R2 leveling sheet " + spec["_leveling_sheet"] +
               ". The leveling total is SUM of the priced column; values marked with "
               "an asterisk on that sheet are options and do not count toward it.")
    s["A2"].alignment = Alignment(wrap_text=True)
    s.row_dimensions[2].height = 30

    r = 4
    for label, amt in spec["_amount_buildup"]:
        s[f"A{r}"] = label
        s[f"B{r}"] = amt
        s[f"B{r}"].number_format = '#,##0.00;-#,##0.00'
        for c in (f"A{r}", f"B{r}"):
            s[c].border = BOX
        r += 1
    s[f"A{r}"] = "CONTRACT TOTAL"
    s[f"B{r}"] = spec["_contract_amount"]
    s[f"B{r}"].number_format = '#,##0.00'
    for c in (f"A{r}", f"B{r}"):
        s[c].font = BOLD
        s[c].border = BOX

    f = dest / f"{spec['file_stem']} - Att A Review Cover Sheet.xlsx"
    wb.save(f)
    total = sum(a for _, a in spec["_amount_buildup"])
    print(f"wrote {f.relative_to(ROOT)}")
    print(f"  buildup sums to {total:,.0f} — contract amount {spec['_contract_amount']:,.0f}"
          f"  {'MATCH' if round(total) == spec['_contract_amount'] else 'MISMATCH'}")
    return f


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "RFP-008")
