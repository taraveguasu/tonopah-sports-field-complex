# Voice corpus drop folder

Executed Attachment A's from past CORE jobs go here. They are the ground truth
the voice profile is induced from, and one exhibit is not a corpus — every rule
still marked *medium* or *open* in
`.claude/skills/attachment-a-generator/references/voice-profile.md` stays that
way until more arrive.

**What to drop:** `.pdf` or `.docx`. Bluebeam FINAL packets are fine as-is — the
exhibit body is located by its own `Page 1 of N` footer and the rest of the
packet (cover sheet, price build-up, Bid Form, descope notes) is ignored.

**What is worth most:** breadth over volume. Exhibits from *different trades*
beat several from one — a single-trade corpus cannot tell house voice apart from
that trade's vocabulary, which is exactly what open decision D3 is stuck on.

Then rebuild:

    python3 scripts/build_voice_corpus.py     # re-measure
    python3 scripts/voice_check.py --all      # re-check drafted packages

Files in this folder are gitignored — they are reference material from other
jobs, not documents belonging to this project.
