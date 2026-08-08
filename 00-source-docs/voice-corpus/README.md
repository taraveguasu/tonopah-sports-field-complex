# Voice corpus drop folder

Executed Attachment A's go here. They are the ground truth the voice profile is
induced from, and **who wrote them is the thing that matters most.**

```
mine/     ← exhibits YOU wrote the scope of work for      (author: self)
./        ← anyone else's, kept for house style            (author: core)
```

The subfolder is the entire authorship signal. An exhibit you wrote, filed in
the wrong place, is silently counted as somebody else's — and the whole point of
the split is that your practice outranks the house's on every judgment call.

Nothing staged in this repo was authored by this project's PM, so until `mine/`
has files in it, `.claude/skills/attachment-a-generator/references/voice-profile.md`
is a **house** profile wearing a personal profile's name. It says so at the top.

**What to drop:** `.pdf` or `.docx`. Bluebeam FINAL packets are fine as-is — the
exhibit body is located by its own `Page 1 of N` footer and the rest of the
packet (cover sheet, price build-up, Bid Form, descope notes) is ignored. A
finished `.docx` works too; its numbering lives in Word's paragraph properties
rather than in the text, so paragraph boundaries are used as item boundaries.

**What is worth most:** breadth over volume. Exhibits from *different trades*
beat several from one — a single-trade corpus cannot tell voice apart from that
trade's vocabulary, which is exactly what open decision D3 is stuck on.

Then rebuild:

    python3 scripts/build_voice_corpus.py     # re-measure
    python3 scripts/voice_check.py --all      # re-check drafted packages

Once `mine/` has content, the stats file grows a **"Where yours diverges from
CORE's other authors"** table. That table is the personal voice profile — the
places your practice and the house's differ are the rules worth encoding, and
they settle the three open decisions the current corpus cannot.

Files in this folder are gitignored — they are reference material from other
jobs, not documents belonging to this project.
