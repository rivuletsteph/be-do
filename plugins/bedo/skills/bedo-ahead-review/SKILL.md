---
name: "bedo-ahead-review"
description: "Build the monthly be•do ahead-review swipe deck — every intention and in-motion chain older than 14 days, one per card, with a suggested status — and write the answers back. Use by the 5th of each month, or when the user asks for the ahead-review."
---

# The monthly ahead-review

One card per open chain, answered with the user's five status glyphs on a phone,
then written back to the stream.

**Nothing in this folder is anyone's in particular.** The stream's field ids live
in `assets/ahead_review_local.json` (gitignored); `assets/ahead_review_local.example.json`
is the blank shape. A blank id stops the build, because a blank id reads every row
as empty and the deck would look calm and be wrong. The stream dump, the recs and
the answers are the user's data and never ship.

## Scope

- **Cards are ⬜ intention and ▶️ in motion chains older than 14 days**, by key.
  Still excluded: any chain carrying the queue box, a head with `waiting on`, and
  media practices (stories live in their own base).
- **▫️ potentials are not carded monthly** — they belong to the season review.
  One exception: a ▫️ row whose details say *ask me again in <month>* is carded in
  that month.
- **Resolve every chain across every weekly base and backup it passed through**
  before carding, live base first (I5, I15) — not the live base alone. A key closed
  (✅ or ✖️) in any later base is shown as closed, with where. A patch that carried
  a stale open row forward, details emptied, is how finished work comes back as a
  card.

## The run

1. **Read the live weekly stream** (all fields, full read; abort on a truncated
   read) to a JSON file, and the archives each open key passed through.
2. **Evidence pass**: close in place only on cited evidence; fold duplicates as a
   DEDUPE onto the live key. Match evidence by key **and** by drive plus title
   words — evidence often lands as keyless log rows.
3. **Recommendation pass**: write `recs.json` — `{key: [rec, one-line reason]}`,
   rec one of `done · drop · someday · keep · date · ask`. The page shows them as
   the five statuses: done → ✅ · in motion stays ▶️ · date → ⬜ intention ·
   someday → ▫️ potential · drop → ✖️ dropped. Never invent a target; never drop
   on its own.
4. **Build:**
   `python3 scripts/build_ahead_review.py --stream stream.json --recs recs.json --today YYYY-MM-DD --out ahead-review.html`
   (`--local` if the settings file lives somewhere else).
5. **Publish** to the same artifact URL each month, `capabilities: {db: {}}`.
   Answers live in the artifact's `answers` collection: `{c, date, note}`, where c
   is `done · motion · intention · potential · dropped` (older pages also wrote
   `ok`, `keep`, `someday`, `date`, `drop`). **There is no date picker**: picking ⬜
   asks *when is the right time, and why* — an intention carries its when in the
   user's words, not a target date.
6. **Write back** when the user says they're done (below).

## Reading the answers

- **Open with one numbered yes/no list** of everything the answers leave open — a
  note that contradicts the tapped glyph, a note too unclear to settle a status,
  any rule change the notes ask for. Then write.
- **Status = the tapped glyph.** An empty glyph with a note: the note settles it;
  the suggestion is only a hint. **A skipped card means the user was good with the
  suggestion** — except a suggested ✖️ is still named in the opening list, because
  be•do never drops on its own.
- **The note goes above the divider**, lightly cleaned, first person, no quote
  marks; a phrase too garbled to clean is kept as said and flagged. Below the
  divider, one `[be•do]` line: old → new status, the source (the user's pick ·
  their note · suggestion accepted · their yes to item N), any rebucket, any target
  cleared with its old date named, and **for every ⬜ a "When:" in words** — drawn
  from the note and the stream, or *not named* when nothing sets it.
- **Targets**: an intention keeps only a firm date the user named — an event, an
  outside deadline, a date said as a date. be•do's placeholders are cleared.
- **A dedupe the user names** is ✖️ with *DEDUPE — folded into <key>* on the folded
  row, and one line on the survivor.
- **Carry existing details verbatim** (I6) and insert; never retype a details
  field. Write **one batch per drive** (50 rows at most per call), then re-read the
  whole weekly base and compare every written field byte for byte before the next
  batch.

## Queues

- The deck offers **no queue box on an intention**. A ⬜ whose when is *a spare 30
  minutes* or *a few minutes with Claude* is written as that when-line, and my day
  offers it when the user says they have the time.
- The queue box stays the user's to tick, on ▫️ and 🔎 rows. be•do never ticks it.
