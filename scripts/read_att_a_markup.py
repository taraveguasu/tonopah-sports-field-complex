#!/usr/bin/env python3
"""
Read a PM-marked-up Attachment A back out of Word.

The exhibits in 02-drafts/ are GENERATED from
01-index/attachment-a-content/<package_id>.json -- rebuilding one overwrites
whatever was typed into it. So a markup pass never edits the generated file in
place. The PM works on a copy named "<stem> - PM markup.docx" and this script
reads the comments and tracked changes back out, so the edits can be applied to
the content record and the recurring ones distilled into drafting rules.

What it pulls out:
  - Word comments: author, date, the text they are anchored to, and the note
  - Tracked insertions and deletions, paragraph by paragraph
  - Which scope item each one lands on, matched against the content JSON, so a
    comment can be traced to the bullet it is about rather than a paragraph index

Usage:  python3 scripts/read_att_a_markup.py "02-drafts/ITB-072/YESCO Draft Att A - PM markup.docx"
        python3 scripts/read_att_a_markup.py <path> --json     # machine-readable
"""

import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "01-index" / "attachment-a-content"

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
P_RE = re.compile(r"<w:p(?: [^>]*)?>(?:(?!</w:p>).)*?</w:p>", re.S)
T_RE = re.compile(r"<w:t(?: [^>]*)?>(.*?)</w:t>", re.S)
DELT_RE = re.compile(r"<w:delText(?: [^>]*)?>(.*?)</w:delText>", re.S)
INS_RE = re.compile(r"<w:ins(?: [^>]*)?>(?:(?!</w:ins>).)*?</w:ins>", re.S)
DEL_RE = re.compile(r"<w:del(?: [^>]*)?>(?:(?!</w:del>).)*?</w:del>", re.S)
CRS_RE = re.compile(r'<w:commentRangeStart[^>]*w:id="(\d+)"')
CRE_RE = re.compile(r'<w:commentRangeEnd[^>]*w:id="(\d+)"')
CREF_RE = re.compile(r'<w:commentReference[^>]*w:id="(\d+)"')
AUTHOR_RE = re.compile(r'w:author="([^"]*)"')
DATE_RE = re.compile(r'w:date="([^"]*)"')


def unescape(s):
    return (s.replace("&lt;", "<").replace("&gt;", ">")
             .replace("&quot;", '"').replace("&apos;", "'").replace("&amp;", "&"))


def text_of(xml):
    """Visible text: normal runs plus deleted runs, so context survives a deletion."""
    return unescape("".join(T_RE.findall(xml) + DELT_RE.findall(xml)))


def load_comments(z):
    """id -> {author, date, text} from word/comments.xml."""
    if "word/comments.xml" not in z.namelist():
        return {}
    xml = z.read("word/comments.xml").decode("utf-8")
    out = {}
    for m in re.finditer(r"<w:comment (?:(?!</w:comment>).)*?</w:comment>", xml, re.S):
        block = m.group(0)
        cid = re.search(r'w:id="(\d+)"', block)
        if not cid:
            continue
        out[cid.group(1)] = {
            "author": (AUTHOR_RE.search(block) or [None, ""])[1]
            if AUTHOR_RE.search(block) else "",
            "date": (DATE_RE.search(block).group(1) if DATE_RE.search(block) else ""),
            "text": text_of(block).strip(),
        }
    return out


def scope_items(pkg):
    """Every drafted line for this package, so a paragraph can be named."""
    f = CONTENT / f"{pkg}.json"
    if not f.exists():
        return []
    spec = json.loads(f.read_text())
    items = []
    for gi, grp in enumerate(spec.get("scope_groups", [])):
        items.append(("scope_groups", gi, "header", grp["header"]))
        for ii, it in enumerate(grp["items"]):
            items.append(("scope_groups", gi, ii, it))
    for key in ("spec_sections", "directives", "exclusions"):
        for ii, it in enumerate(spec.get(key, [])):
            items.append((key, None, ii, it))
    return items


def locate(para_text, items):
    """Match a paragraph to the content-record entry that produced it."""
    t = " ".join(para_text.split())
    if not t:
        return None
    for key, gi, ii, val in items:
        v = " ".join(val.split())
        if not v:
            continue
        # A tracked edit changes the text, so match on a stable leading slice.
        head = v[:60]
        if head and (head in t or t[:60] in v):
            where = f"{key}[{gi}].items[{ii}]" if gi is not None and ii != "header" \
                else f"{key}[{gi}].header" if gi is not None else f"{key}[{ii}]"
            return {"field": where, "original": val}
    return None


def build(path, pkg=None):
    path = Path(path)
    if pkg is None:
        for p in path.parts:
            if re.fullmatch(r"(RFP|ITB)-\d{3}", p):
                pkg = p
                break
    items = scope_items(pkg) if pkg else []

    with zipfile.ZipFile(path) as z:
        doc = z.read("word/document.xml").decode("utf-8")
        comments = load_comments(z)

    paras = [m.group(0) for m in P_RE.finditer(doc)]
    open_ids, found_comments, edits = {}, [], []

    for idx, p in enumerate(paras):
        ptext = text_of(p)
        for cid in CRS_RE.findall(p):
            open_ids[cid] = idx
        anchored = set(CRE_RE.findall(p)) | set(CREF_RE.findall(p))
        for cid in anchored:
            c = comments.get(cid)
            if not c:
                continue
            found_comments.append({
                "id": cid, "paragraph": idx,
                "author": c["author"], "date": c["date"], "comment": c["text"],
                "anchored_to": " ".join(ptext.split())[:400],
                "content_record": locate(ptext, items),
            })

        ins = [unescape("".join(T_RE.findall(m.group(0)))) for m in INS_RE.finditer(p)]
        dels = [unescape("".join(DELT_RE.findall(m.group(0)))) for m in DEL_RE.finditer(p)]
        ins = [x for x in ins if x.strip()]
        dels = [x for x in dels if x.strip()]
        if ins or dels:
            authors = sorted(set(AUTHOR_RE.findall(
                "".join(m.group(0) for m in INS_RE.finditer(p)) +
                "".join(m.group(0) for m in DEL_RE.finditer(p)))))
            edits.append({
                "paragraph": idx, "authors": authors,
                "inserted": ins, "deleted": dels,
                "result": " ".join(unescape("".join(T_RE.findall(p))).split())[:400],
                "content_record": locate(ptext, items),
            })

    return {"file": str(path), "package": pkg,
            "comments": found_comments, "tracked_edits": edits}


def report(r):
    print(f"{r['file']}")
    print(f"package: {r['package'] or 'UNKNOWN — pass it explicitly'}")
    print(f"{len(r['comments'])} comment(s), {len(r['tracked_edits'])} paragraph(s) "
          f"with tracked changes\n")

    if r["comments"]:
        print("COMMENTS")
        for c in r["comments"]:
            who = c["author"] or "unknown"
            print(f"  [p{c['paragraph']}] {who} {c['date'][:10]}")
            if c["content_record"]:
                print(f"    on: {c['content_record']['field']}")
            print(f"    text: {c['anchored_to'][:160]}")
            print(f"    >>>   {c['comment']}\n")

    if r["tracked_edits"]:
        print("TRACKED CHANGES")
        for e in r["tracked_edits"]:
            who = ", ".join(e["authors"]) or "unknown"
            print(f"  [p{e['paragraph']}] {who}")
            if e["content_record"]:
                print(f"    on: {e['content_record']['field']}")
            for d in e["deleted"]:
                print(f"    -   {d}")
            for i in e["inserted"]:
                print(f"    +   {i}")
            print(f"    =   {e['result']}\n")

    if not r["comments"] and not r["tracked_edits"]:
        print("Nothing found. If you commented in Word, make sure the file was saved "
              "as .docx (not .doc) and that Track Changes was on for edits.")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        sys.exit(__doc__)
    res = build(args[0], args[1] if len(args) > 1 else None)
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
    else:
        report(res)
