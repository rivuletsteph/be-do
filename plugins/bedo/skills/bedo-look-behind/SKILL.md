---
name: "bedo-look-behind"
description: "Build The Day Behind page — the look behind for one day — from the stable release. Use at the dusk close, or when the user asks for the look behind, the day behind, or the daily review of a day that has finished."
---

# The day behind

One day, looked back on. The page is the canon build settled 21 Sep 2026: chip
and date and lead · the story · who was in your day · highlights · how the day
went · balance · effectiveness. That order, those sections, nothing else.

**This folder is the skill; what is installed is a loader.** The copy installed
in claude.ai is two files — a loader `SKILL.md` and the user's own
`assets/look_behind_local.json` — and the loader fetches this folder fresh from
the version store on every run, so a stale copy can never build a page. That
means:

- **A change here needs no upload.** Push it to the version store and the next
  run picks it up.
- **Never upload this folder over the installed skill.** That replaces the
  loader with a copy that goes stale at the next change. It happened to the day
  ahead on 28 Sep 2026 and was put back the next morning.
- **Upload only when the settings file or the loader itself changes**, and then
  upload the two-file loader zip. The loader is personal — it names the user's
  calendars — so it is kept with their settings, not in the version store.
- **A new settings key means a new upload.** The builder comes fresh but the
  installed settings do not: a key added to `look_behind_local.json` reaches a
  claude.ai chat only when the loader zip is uploaded again.

Nothing here depends on project files, so it runs in any project or none.

**Nothing in this file is anyone's in particular.** Every specific — the user's
name, the bases and tables, the field ids, the practice-to-slice map, the page
it publishes to — lives in `assets/look_behind_local.json`. Who belongs to which
circle is not among them: that is read live from the connections table, because
a map kept by hand goes stale the day the user meets somebody. **Open that file
and read the value you need** rather than carrying one in memory or guessing
from an earlier chat. The key to read is named below wherever one is wanted.
`assets/look_behind_local.example.json` is the blank shape.

**Build from the stable release. Don't redesign it.** Changes to the layout are
a separate be•do work chat that ends with a push and a new tag in the version
store — not with a new zip; the installed loader fetches the change by itself.

## Two things on this page are the user's, and you write them

The builder computes every section but two. **The lead and the story are not
computed and must never be invented from the section totals** — they are the
day's own account of itself, and they come from the user's rows.

- **the lead** — one line naming the day. What the day *was*, not what was in
  it. Present tense or none. No pronouns, no "you", no summary of the numbers
  below it.
- **the story** — the day's stretches, one per line, emoji first, no pronouns.
  Length follows the day: a quiet day is three lines, a full one is six. Each
  line is a stretch, not a row — the morning's getting-ready is one line, not
  five. Read the day's titles and the user's own words in the details, and write
  them the way they write: plain, concrete, no adjectives doing work a noun
  could do.

Write them into `words.json`:

```json
{ "lead": "one line naming the day",
  "story": [["🚗", "a stretch of the day"], ["🌙", "another"]] }
```

The builder **refuses to build without them**. That is deliberate: a page with
an empty story reads as a day that didn't happen. `--allow-unwritten` exists for
a shape check only and never for a page the user will see.

### When nobody is there: the draft

A scheduled run has nobody to show the words to. In the user's words, 28 Sep
2026 (amendment `[id]`): *the look behind may draft its own lead
and story for a scheduled run, it just needs to be editable.* So:

- **Draft from the digest, by the same rules as above.** The day's rows and the
  user's own words in them, never the section totals. A draft is not licence to
  embroider: no feeling the rows don't name, no verdict on the day.
- **Write it with `scripts/words.py`, marked as a draft:**
  ```
  python3 scripts/words.py --day YYYY-MM-DD --file words-YYYY-MM-DD.json --new --draft \
    --lead "one line naming the day" --line 🚗 "a stretch" --line 🌙 "another"
  ```
  The file carries its day, and the builder refuses words written for another
  one — yesterday's story on today's page is worse than none.
- **The page says so.** A dashed mark beside the chip, *draft · not yet your
  words*, a dashed rule down the side of whichever part is drafted, and a line
  in the footer. Nothing else on the page changes.
- **A day with too little on it is not drafted.** If the digest holds nothing
  to name the day by — no rows, or only the flow's own steps — don't draft and
  don't publish. Log that the page is waiting, and why.
- **In a chat with the user present, nothing changes.** Write the words, show
  them, and leave the mark off. The mark is for words nobody saw before they
  went on the page.

**Editing is one command, and it never re-reads Airtable.** When the user next
opens a chat and the page still carries a draft, show them the lead and the
story as they stand and offer to change them. Whatever they say:

```
bash run_look_behind.sh words YYYY-MM-DD                                    # read them back, numbered
bash run_look_behind.sh words YYYY-MM-DD --set-lead "their line" --to-page
bash run_look_behind.sh words YYYY-MM-DD --set-line 2 🌳 "their stretch" --drop-line 4 --to-page
bash run_look_behind.sh words YYYY-MM-DD --add-line 3 ☕ "a stretch that was missing" --to-page
bash run_look_behind.sh words YYYY-MM-DD --accept all --to-page             # fine as they are
```

What they touch, or accept as it stands, stops being a draft; the other part
keeps its mark until it is touched too. `--to-page` writes the words into the
page already built. Then publish the page again and replace the Drive copy.
**Use their words exactly.** An edit is not a prompt to rewrite the rest.

On a machine with no words file, the same command recovers the words from the
built page first, so a Drive copy of the page is enough to edit from.

## The files, inside this skill

- `run_look_behind.sh` — the runner: `prep` reads Airtable directly and prints
  the day's digest, `build` builds, `words` reads the lead and story back or
  changes them
- `scripts/look_behind.py` — the reader and builder
- `scripts/words.py` — the lead and the story as a file: drafted, read back,
  changed, carried to a built page
- `scripts/day_pie.py` — the day's minutes, one slice each
- `scripts/bedo_common.py` — the pieces the builders share
- `scripts/calendar_sync.py` — plans the dusk sync of linked calendar events
  from the stream; never writes the calendar itself
- `scripts/typical_time.py` — median durations from the user's own past rows,
  run occasionally against the weekly CSV archives, not on every build
- `assets/look_behind_engine.html` — the page, nothing personal in it
- `assets/look_behind_local.json` — the user's settings, and the only place a
  specific lives. Personal; this copy of the skill is theirs and is not the one
  that gets shared. It is gitignored.
- `assets/look_behind_local.example.json` — the same shape, empty. This is the
  one that travels when the skill is shared.
- `tests/test_calendar_sync.py` — runs the sync planner over a fixture
- `tests/test_words.py` — drafts, edits and carries the words to a page, and
  checks that what was touched stops being a draft
- `tests/test_canon.py` — runs the builder against a fixture written backwards
  from the canon page and checks every computed section. Run it after any change
  to the builder.

Copy them to a working folder from the directory this SKILL.md was read from
(`cp -r <skill dir>/scripts <skill dir>/assets /home/claude/lb/`). Their
contents never pass through the chat.

## Steps

1. **Read live, complete or abort** (I13, I11). `list_records_for_table` with
   pageSize 8000 and every field.
   - The weekly stream for the day's week, `w## be•do` resolved by name. If the
     day sits near a week boundary, read the neighbouring week too and pass both
     **live base first** (I15). The builder **dedupes by record id before it
     resolves any chain**, so a row cloned between bases counts once.
   - Rhythms: the base and table named in `rhythms_base` and `rhythms_table`.
   - Practices: `practices_base` and `practices_table`, filtered to active.
     Optional — without it every practice carries `default_effort_band` and
     nothing is zeroed by catalogue or by group.
   - Connections: `connections_base` and `connections_table`. **This is the
     fourth saved read and it is not optional in practice** — it is where the
     circles come from, and without it the people chips fall back to plain
     order of appearance. Carry the name, the short name and the circles field.
     A person sits in several circles and **the first one listed is the one
     they are grouped by**; the builder takes that one and ignores the rest.
     It matches on either the full name or the short one, with any glyph in
     front stripped, because the stream's person field carries whichever one
     the user typed.

   **Where the reads land.** In a claude.ai chat an oversized read saves to
   `/mnt/user-data/tool_results/<tool>_<id>.json`, wrapped as
   `[{"text": "<json>"}]`. **The builder unwraps that itself** — `cp` the saved
   file to `w##.json` and pass it. Name the copies by week so the page's
   provenance line reads `w39 · 635/635`.

   **A read small enough to come back inline doesn't save to disk.** Rhythms,
   practices and connections all do this. Don't re-read hoping it spills. Write
   the file from the inline result as `{"records":[…],"metadata":
   {"totalRecordCount": <rows written>}}`, carrying the fields named under
   `fields` in the local settings.
2. **Write the words** — the lead and the story, as above, into
   `words-YYYY-MM-DD.json` with `scripts/words.py --new`. A scheduled run adds
   `--draft`. (A hand-written `words.json` still builds.)
3. **Build:**
   ```
   cd /home/claude/lb
   python3 scripts/look_behind.py --day YYYY-MM-DD \
     --local assets/look_behind_local.json --stream w##.json [--stream w##-prev.json] \
     --rhythms rhythms.json --practices practices.json --connections connections.json \
     [--typical typical_time.json] \
     --words words.json --template assets/look_behind_engine.html \
     --out YYYY-MM-DD-day-behind.html --secure <state> [--baseline-days N] [--usual-min N]
   ```
   If it aborts on a short read, don't build from a partial read. Say which read
   came back short and read it again.

   It aborts the same way when the local settings file is missing a field id or
   the clock offset. That is deliberate: a blank id reads every row as empty, and
   the page would look calm and be wrong.
4. **Check what it printed.** The builder prints what it did, and three lines
   are worth reading before publishing:
   - `estimates_trimmed_min` above zero means the logged and estimated minutes
     overran twenty-four hours and estimates were cut to fit. Say so in the chat.
   - `containers_set_aside` names how many rows held other rows and scored
     nothing — a trip, a field day. Expected on a travel day, odd on a quiet one.
   - `destinations` empty on a working day usually means rows are missing a
     drive, not that nothing moved.
   - `circles_read` at zero means the connections read didn't arrive and the
     people chips are in bare order of appearance.
5. **Publish** to the same artifact, copying the page to `/mnt/user-data/outputs/`
   first. The link is `artifact_url` in the local settings file. One living page,
   republished in place.
6. **Save the page** to that week's Drive folder,
   `be•do/<year>-W## <Mon D>/YYYY-MM-DD-day-behind.html`, and read back a line to
   confirm. **A claude.ai chat has no Drive commit tool**, and uploading through
   the Drive connector would pass the whole page through the chat. There, skip it
   and say so in one line: the published page and `/mnt/user-data/outputs/` are
   the copies of record.
7. **Sync the calendar from the stream.** The stream is the record of what
   happened; the calendar mirrors it. Every row tied to an event carries the
   event's link in its `event` field, and at the dusk close each linked event
   takes the row's status as its title prefix (⬜ → ✅ / ✖️) and, when the row
   holds a real span, its real times. The script plans; the chat writes.
   ```
   python3 scripts/calendar_sync.py --list --day YYYY-MM-DD \
     --local assets/look_behind_local.json --stream w##.json [--stream w##-prev.json]
   ```
   Fetch each listed event fresh with `get_event` (its `calendar_id` and
   `event_id` are in the list) and save them to `events.json` with the
   calendar id added to each as `calendarId`. Save `list_calendars` to
   `calendars.json`. Then:
   ```
   python3 scripts/calendar_sync.py --plan --day YYYY-MM-DD \
     --local assets/look_behind_local.json --stream w##.json [--stream w##-prev.json] \
     --events events.json --calendars calendars.json --out sync-plan.json
   ```
   Make each change in `changes` with `update_event`, passing exactly the
   `update` object it names — **`notificationLevel` is always `NONE`** — and
   nothing else. Say what moved in one line.

   What it leaves alone, by design, and lists under `unchanged`:
   - an event on a calendar not in `sync_calendars`, or one someone else organises
   - an event linked by a row **about** it rather than its own row — a row
     rescheduling or preparing for it. Only a row timed to the event moves it,
     so closing the phone call never marks the appointment done.
   - two rows on one event that disagree — named, for the user's word
   - an all-day event's dates, and the times of any row with no real span

   For what was **scheduled**, the calendar is authoritative; for what
   **happened**, the stream wins. This step is what keeps the two agreeing.
   `tests/test_calendar_sync.py` checks the plan; run it after any change.
8. **Log the step**: one row for the look behind, dusk, with the page URL as its
   deliverable. **When the words are a draft, the row says so** and carries them
   in its `[be•do]` block — `draft lead: …` and one `draft story:` line per
   stretch — so any later chat can see what is waiting to be edited without
   opening the page.

## What the builder decides, so you don't have to

Read these before second-guessing a number on the page.

- **A row scores nothing** when it is a plan or a skipped row, when it is
  somebody else's own row kept in the user's stream, or when it holds other
  rows — four hours or more with at least three moments inside it is an
  envelope, not an activity. On top of that, `zero_practices` names practices that happened but
  are not effort, and `zero_practice_groups` does the same for a whole
  catalogue group at once.
- **Sleep is the case that splits in two.** It scores zero on the wheel and its
  minutes are still logged on the pie, because the hours happened. `zero_note`
  in the local settings is the sentence the page prints about this.
- **Estimated minutes are never presented as logged.** A row with no end gets
  the median of the user's own past rows for that practice, from
  `typical_time.json`, and only where that median was earned — five observations and a tight spread.
  No median means no estimate; the minutes stay uncounted rather than guessed.
  The engine draws estimates striped and states the total.
- **The screen slice comes from the row's device field**, not from the practice,
  and only for rows the practice map didn't already place. Eating in front of
  the television is still eating.
- **be and do, tending and growing.** Being is heart, mind, body and spirit.
  Doing is water, air, earth and fire, and it is cut in two: a row bucketed to a
  drive is **growing**, a row bucketed to a standing rhythm is **tending**, and
  a row carrying **no bucket at all is tending too** — an unnamed doing hour was
  the floor being held up. Tending is the default, not something a row earns,
  which is what makes the bar add up: every doing row lands in one of the two,
  so the page is never left with a remainder it has to draw as something else.
  `growing_types` lists the types that count as growing; everything else on the
  doing side is tending.
- **Effort weighs minutes over six.** A row with a real span weighs its minutes
  ÷ 6, so an hour weighs ten; a row that holds no time weighs its catalogue
  effort band. `effort_minute_divisor` can override it, but six is the user's
  amendment and changing it moves every wheel and every bar.

## Effectiveness, and what it still can't say

Effectiveness is discharge: the time that moved destinations forward, measured
against the user's own baseline. The baseline needs fourteen clean days and is still
forming, so the page says so rather than inventing a percentage. Pass
`--baseline-days` and `--usual-min` only when there is a real count behind them.

## What the user sees in the chat

One or two lines, not the page again. What the day was, and anything the build
flagged — trimmed estimates, a container set aside, work with no drive on it.
The page holds the rest.

## Not built yet

- **Photos.** The canon page reserves up to five thumbnails and hides the strip
  when there are none. The stream carries a photo checkbox but no attachment, so
  there is nothing to draw and the page correctly shows none.
- **Firing unattended at dusk.** The pieces are all here — `run_look_behind.sh`
  reads Airtable by itself, and a scheduled run may draft the lead and the
  story — but nothing schedules it yet, and publishing, the Drive copy, the
  calendar sync and the log row still need a session that can reach them.

## If it can't run here

If this surface can't save the reads to disk or run Python, say so in one line
and offer to run it from a Cowork session on the user's laptop, which can.
