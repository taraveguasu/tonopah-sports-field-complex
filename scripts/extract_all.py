#!/usr/bin/env python3
"""
Extract the full text of every source document to disk.

This is the foundation the previous index skipped. Nothing downstream is allowed
to cite a document that does not have an extraction here, and the coverage audit
reads these files rather than checking whether a path was mentioned somewhere.

Handles:
  .pdf   text layer via PyMuPDF; falls back to Tesseract OCR at 200 dpi when a
         page yields too little text to be real
  .docx  unzip + strip XML (Word emits no plain-text part)
  .xlsx  openpyxl, every sheet, cells joined tab-delimited
  .xlsm  same as .xlsx (macros ignored — we want the values)
  .xls   converted via LibreOffice if present, otherwise reported unextracted

Usage:
  python3 scripts/extract_all.py --census        # report only, extract nothing
  python3 scripts/extract_all.py [--only SUBSTR] # extract
Writes:
  01-index/document-text/<mirrored path>.txt
  01-index/extraction-manifest.json
"""

import argparse
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "00-source-docs"
OUT = ROOT / "01-index" / "document-text"
MANIFEST = ROOT / "01-index" / "extraction-manifest.json"

# A page of a real spec or proposal carries hundreds of characters. Drawing sheets
# are the exception: they are vector art whose "text" is fragmentary, which is why
# a low score triggers OCR rather than being accepted.
MIN_CHARS_PER_PAGE = 120


def docx_text(p: Path) -> str:
    with zipfile.ZipFile(p) as z:
        names = [n for n in z.namelist() if re.match(r"word/(document|header\d*|footer\d*)\.xml$", n)]
        parts = []
        for n in sorted(names):
            xml = z.read(n).decode("utf-8", "ignore")
            xml = re.sub(r"</w:(p|tr)>", "\n", xml)
            xml = re.sub(r"</w:tc>", "\t", xml)
            parts.append(re.sub(r"<[^>]+>", "", xml))
    t = "\n".join(parts)
    for a, b in [("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"), ("&quot;", '"'), ("&apos;", "'")]:
        t = t.replace(a, b)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", t)).strip()


def xlsx_text(p: Path) -> str:
    import openpyxl
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    out = []
    for ws in wb.worksheets:
        out.append(f"=== SHEET: {ws.title} ===")
        for row in ws.iter_rows(values_only=True):
            cells = ["" if c is None else str(c) for c in row]
            if any(c.strip() for c in cells):
                out.append("\t".join(cells).rstrip())
    wb.close()
    return "\n".join(out)


def pdf_pages_text(p: Path):
    import fitz
    d = fitz.open(p)
    pages = [pg.get_text() or "" for pg in d]
    d.close()
    return pages


def ocr_page(p: Path, idx: int, dpi=200) -> str:
    """Render one page and OCR it. Used only where the text layer is unusable."""
    import tempfile, os
    with tempfile.TemporaryDirectory() as td:
        stem = os.path.join(td, "pg")
        subprocess.run(["pdftoppm", "-r", str(dpi), "-f", str(idx + 1), "-l", str(idx + 1),
                        "-png", str(p), stem], check=True, capture_output=True)
        pngs = sorted(Path(td).glob("pg*.png"))
        if not pngs:
            return ""
        r = subprocess.run(["tesseract", str(pngs[0]), "stdout", "--psm", "6"],
                           capture_output=True, text=True)
        return r.stdout or ""


def extract(p: Path, census_only=False):
    """Return (method, text, pages, ocr_pages)."""
    ext = p.suffix.lower()
    if ext == ".docx":
        return ("docx", "" if census_only else docx_text(p), 1, 0)
    if ext in (".xlsx", ".xlsm"):
        return ("xlsx", "" if census_only else xlsx_text(p), 1, 0)
    if ext == ".xls":
        return ("xls-unsupported", "", 1, 0)
    if ext != ".pdf":
        return ("skip", "", 0, 0)

    pages = pdf_pages_text(p)
    n = len(pages)
    total = sum(len(t.strip()) for t in pages)
    thin = [i for i, t in enumerate(pages) if len(t.strip()) < MIN_CHARS_PER_PAGE]
    if census_only:
        return ("pdf-text" if not thin else "pdf-mixed", "", n, len(thin))

    ocr_count = 0
    for i in thin:
        try:
            o = ocr_page(p, i)
            if len(o.strip()) > len(pages[i].strip()):
                pages[i] = o
                ocr_count += 1
        except Exception as e:
            pages[i] += f"\n[OCR FAILED: {e}]\n"
    body = "\n".join(f"\n===== PAGE {i+1} =====\n{t}" for i, t in enumerate(pages))
    return ("pdf-text" if ocr_count == 0 else "pdf-ocr", body, n, ocr_count)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--census", action="store_true")
    ap.add_argument("--only", default="")
    a = ap.parse_args()

    files = [p for p in sorted(SRC.rglob("*"))
             if p.is_file() and p.name != ".gitkeep" and "/_extracted/" not in str(p)]
    if a.only:
        files = [p for p in files if a.only.lower() in str(p).lower()]

    recs, agg = [], {}
    for p in files:
        rel = str(p.relative_to(SRC))
        try:
            method, text, pages, ocr = extract(p, census_only=a.census)
        except Exception as e:
            recs.append({"file": rel, "method": "ERROR", "error": f"{type(e).__name__}: {e}"})
            agg["ERROR"] = agg.get("ERROR", 0) + 1
            print(f"  ERROR  {rel}: {type(e).__name__}: {e}", file=sys.stderr)
            continue

        rec = {"file": rel, "method": method, "pages": pages}
        if not a.census:
            dest = OUT / (rel + ".txt")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text)
            rec.update({"chars": len(text), "ocr_pages": ocr,
                        "extracted_to": str(dest.relative_to(ROOT))})
            per = len(text) / max(pages, 1)
            rec["quality"] = "ok" if per >= MIN_CHARS_PER_PAGE else "THIN"
        else:
            rec["thin_pages"] = ocr
        recs.append(rec)
        agg[method] = agg.get(method, 0) + 1

    if a.census:
        print("CENSUS — extraction method by document\n")
        for k, v in sorted(agg.items()):
            print(f"  {k:18} {v:>4}")
        thin_tot = sum(r.get("thin_pages", 0) for r in recs)
        pg_tot = sum(r.get("pages", 0) for r in recs)
        print(f"\n  pages total: {pg_tot:,}   pages needing OCR: {thin_tot:,}")
        print("\n  documents with the most OCR-needed pages:")
        for r in sorted(recs, key=lambda x: -x.get("thin_pages", 0))[:12]:
            if r.get("thin_pages"):
                print(f"    {r['thin_pages']:>4}/{r.get('pages',0):<4} {r['file'][:88]}")
        return

    MANIFEST.write_text(json.dumps({
        "_generated": "2026-08-04",
        "_purpose": "Full text of every source document. Downstream indexing reads these, not the source paths.",
        "_min_chars_per_page": MIN_CHARS_PER_PAGE,
        "_totals": {"documents": len(recs), "by_method": agg,
                    "chars": sum(r.get("chars", 0) for r in recs),
                    "ocr_pages": sum(r.get("ocr_pages", 0) for r in recs),
                    "thin": sum(1 for r in recs if r.get("quality") == "THIN")},
        "documents": recs,
    }, indent=2) + "\n")
    t = json.loads(MANIFEST.read_text())["_totals"]
    print(f"documents: {t['documents']}   chars: {t['chars']:,}   OCR pages: {t['ocr_pages']}   THIN: {t['thin']}")
    for k, v in sorted(t["by_method"].items()):
        print(f"  {k:18} {v:>4}")


if __name__ == "__main__":
    main()
