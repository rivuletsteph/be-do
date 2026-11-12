---
name: bedo-weekly-close
description: "Run the be•do weekly close and the Monday plan. Use when the user says it's Sunday, asks to close the week, run the weekly review, do the split, or plan the week ahead."
---

# The weekly close

**Review, then plan.** My day comes first, and the reflective half of Sunday comes
before the mechanical half. Run it on Opus. Everything here reads from
`plugins/bedo/close/close.py`; the judgment is in `docs/v53-judgment.md` J11.

## What is hers

1. **Clone the base** in the Airtable UI, and say when the new one exists.
2. **Her reflection** on the week, including where the word showed up.
3. **The week's one word.** A carry-over is valid.
4. **Her one focus practice** for the week, from either flow.
5. **Her yes to clear** the new base, given after she has seen how many rows go.
6. **Her yes on the fold list,** or a fix to one line.

Everything else is be•do's. It makes the calls, says each in one line, and never
shows her the pile. Three or more flags in a week means the system is asking too
much: shrink it.

## The sequence

Set up once: `BEDO_FACTS_LOCAL` pointing at the facts_local settings, and the
Airtable token in `AIRTABLE_PAT`. `W` is the week being closed.

```
python3 close.py fetch  --week W     # every base's stream to disk
python3 close.py backup --week W     # every table to CSV, before anything deletes
python3 close.py check  --week W     # the self-check and the quest lines
python3 close.py audit  --week W     # every row through the entry check
python3 close.py export --week W     # her words only; needs pandoc or python-docx, else W.md stands
python3 close.py fold   --week W     # the week's amendments, where each landed
python3 close.py plan   --week W     # the carry set and the delete set, by record id
```

1. **Backup first.** Save the CSVs to the closing week's Drive folder. Say plainly
   if they stayed on this machine.
2. **Self-check,** one compact table, no commentary unless something flags. Every
   percentage names its denominator. A flag becomes the first item in that week's
   ⚡ intention check. Steps come from the latest Google Health mail; none is
   *not yet received*, never zero.
3. **The quest tally,** one line: points by day, the total, the dollars (a point is
   50¢, at most $5 a day). A day at his grandparents' or away overnight is a flat
   only. A day she wasn't with him gets no score and no invented one. be•do totals;
   she pays.
4. **Reflection, word, focus practice:** hers. be•do listens and writes.
5. **The order and the review.** `run_checks.sh order --json`, written to the
   catalog's `typical time`. One backlog bucket a week. Drives and rhythms as one
   compact diff, only the few that need her word; an empty destination is never
   raised.
6. **The fold,** about five minutes, and it never holds up the close. `close.py fold`
   lists the week's amendments and a few older active ones, one line each saying
   where it landed. Before she sees it, open each line's evidence: the check it
   names, or the words in `docs/v53-judgment.md`. A mapping can be wrong. She says
   yes or fixes a line. Mark the rows she confirmed folded, by the ids in
   `fold_list.json`; in a cloud chat that goes through the Airtable connector.
   A row that hasn't landed stays active and rolls to next week. The quest's data
   row is never folded. There is no master version to approve.
7. **The chat sweep:** `run_checks.sh chats` (J11).
8. **Her university's events calendar** for the next two weeks (a trial, 27 Oct
   2026; the link is `events_calendar` in her settings). Offer only what fits her
   drives or her interests (talks, theatre, family events), one line each she can
   say yes to. A yes goes on her calendar (purple for work) and in as a ⬜ row.
9. **The split.** Her clone, then `plan`. Rows written after the clone make the
   record-id diff unclean, and `plan` stops: a closed row left behind in the old base
   stays there, an open one is patched across, and a row dated in the new week is
   kept. Show her the delete count and get her yes. Delete by record id only, in
   batches, from `split_plan.json`. Re-carry anything `carry_elsewhere` names, its
   details verbatim and its key kept. Then `close.py fetch` and `close.py verify`.
   Resolved rows stay behind in the old base, whole.
10. **The drive cleanup** (her words, 9 Nov 2026: over 300 lines got carried to the
   new week … it needs to happen on a weekly basis). On the new base, right after
   `verify`: `run_checks.sh cleanup`. Say its first lines to her as the big picture,
   in plain words, never the pile. Then this week's drives, one at a time: the
   undriven rows first, placed by be•do (J12) with only the unsure few named; then
   each picked drive with be•do's call on every row — ✅ on the evidence it prints,
   a fold for a dedupe, ▫️ for watching rather than a step, reading and media to the
   stories queue (amendment, 9 Nov), keep with a *when* in her words. ✖️ and ⏸️ are
   hers; a row she doesn't remember is hers to drop, never be•do's. Write only what
   she confirms, each row through `entry`, with one line in its `[be•do]` block that
   begins `[be•do] drive cleanup, <Day D Mon YYYY> (<chat>):` — that line is how the
   next week's run knows the drive was cleaned and leaves it for its turn. A line
   that only places a row (`drive set to …`) doesn't count as a review. From a
   branch, the rows go to the my day chat in batches; it is the stream's one writer.
   About fifteen minutes of hers; stop when she says.
11. **The new week's rows:** the word and the focus practice, written fresh. Build
   ideas go to the backlog. No handoff document.
12. **The Stories page** for the new week (`stories-queue`): last week's taps
   read back into the stories base first, then the new page. A branch chat can
   run it; it asks her nothing, and the link goes in the close's last reply.

**Not in the close:** a week look behind, a review page, a handoff, three-and-three
priorities. All retired.

## Monday: decide the week

The word first, in an empty slot, then candidates below it, carry-over first. Then
the leverage list, labelled *possible paths*, never a queue.

## Token budget

Never pull a full table into context: fetch to disk, build with code. Ask before a
token-heavy step and narrate long mechanical work. A truncated read supports no
conclusion: check the total against what came back.

Token use gets one line at the close, on the 15% be•do line, and only when the
meter can be read. No daily readings, no friction review.

## Monthly

The ahead-review by the 5th (`bedo-ahead-review`): ⬜ and ▶️ older than 14 days,
answered with her five glyphs, no dates. ▫️ potentials go to the season review.
be•do proposes; it never drops.
