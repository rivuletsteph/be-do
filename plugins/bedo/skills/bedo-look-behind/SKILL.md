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
2026 (an amendment): *the look behind may draft its own lead
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
  changed, carried to a built page, and carried through the stream from the
  dusk chat to the morning routine (`--row-block`, `--from-stream`)
- `scripts/look_behind_log.py` — which days still need their final, read off
  the look behind's own log rows; the morning routine's first question
- `MORNING.md` — the morning routine, step by step: what it reads, what it
  builds, what it may write, and what it does when a day is missing
- `scripts/day_pie.py` — the day's minutes, one slice each
- `scripts/bedo_fetch.py` — reads Airtable directly: the token from
  `AIRTABLE_PAT`, a secrets file, or — in a Claude cloud session — from the
  environment's API credential, attached by the proxy so the session never
  holds it
- `scripts/bedo_common.py` — the pieces the builders share, including the
  clock-offset check that refuses to build when `utc_offset_hours` disagrees
  with `time_zone` on the day being built (daylight saving ends 1 Nov 2026)
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

## Where this runs, and what each place can reach

Three surfaces run this skill, and they differ in one thing: where the
Airtable token is.

- **A Claude Code cloud session** — claude.ai/code on the laptop, the Code tab
  of the phone app, and a routine — on an environment that carries the
  read-only token as an **API credential** for `api.airtable.com`. The fetch
  sends no `Authorization` header and the proxy attaches the token after the
  request has left the VM; nothing in the session ever holds it. The settings
  file is there too, synced with the installed skill
  (`/root/.claude/skills/synced/*/bedo-look-behind/assets/`), and the runner
  finds it by itself. The Artifact tool publishes; the Airtable, Calendar and
  Drive connectors write the row, sync the calendar and save the page. **This
  is the surface the dusk draft and the morning routine are built for.** A
  routine created from inside a session carries no connectors (checked 29 Sep
  2026); one created from the claude.ai routines page can.
- **The laptop**, with `bedo_secrets.json` in the working folder or the folder
  above it: the same runner, the same commands. `LB_DIR`, `LB_LOCAL` and
  `LB_OUT` are the three things that differ by machine (runner header).
- **A plain claude.ai chat** has neither. The runner's `prep` stops at the
  fetch with *no token in hand*. There, the old path still works — the rows
  read through the Airtable connector and saved as `data/w##.json` (an
  oversized read lands in `/mnt/user-data/tool_results/…`, wrapped
  `[{"text": "<json>"}]`, which the builder unwraps itself) — at ~45k tokens
  a build. Say so in one line, and prefer a cloud session.

## Steps

Every step is one runner command. Nothing about the rows passes through the
chat except the digest the words are written from.

1. **Prep** — `LB_DIR=<working folder> bash run_look_behind.sh prep YYYY-MM-DD`
   Clones the version store fresh, reads Airtable directly — the day's week
   `w## be•do` resolved by name, the week before it (I14, passed to the builder
   live first, I15), rhythms, practices and connections, each paged to the end
   or the run aborts (I11) — and prints the day's digest: one line per logged
   row, the user's words above the divider. **On the first day of a new week
   it aborts until the new base is cloned** (the Sunday close does that): say
   so and stop; never fall back to the old week's base.
2. **Words** — the lead and the story, from the digest, by the rules above.
   With the user present:
   ```
   bash run_look_behind.sh words YYYY-MM-DD --new --lead "…" --line 🚗 "…" --line 🌙 "…"
   ```
   shown to them, and left unmarked. Nobody present, or the day not over yet:
   add `--draft`. Either way, `bash run_look_behind.sh words YYYY-MM-DD
   --row-block` prints the `[be•do]` block the log row carries (step 7).
3. **Secure base** — the day's ⏏️ row is in the digest: `secure`, or the other
   state as the row names it. **No row:** `secure` is the assumed default
   since 29 Sep 2026 — the ⏏️ row is no longer written every day, and the other
   state is written only when the user names a knock-back — so build `secure`
   and say the row was absent. (Her word on this is still being asked for;
   until it comes, this is the rule.)
4. **Build** — `bash run_look_behind.sh build YYYY-MM-DD <state>`
   Read what it printed (below) before publishing. If it aborts on a short
   read, don't build from a partial read: read again. It aborts the same way
   on a missing field id, a missing clock offset, or an offset that disagrees
   with `time_zone` on that day — all three are the settings file's to fix,
   never worked around.
5. **Publish** to the living page: the Artifact tool, `url` set to
   `artifact_url` from the settings file, the same file path every day. One
   living page, republished in place; every republish is kept as a version.
6. **Save the page to Drive**, in the folder of its own week:
   `be•do/<year>-W## <Mon D>/YYYY-MM-DD-day-behind.html` — the folder named for
   the week number and its Sunday, no leading zero. Search the folder by name;
   create a missing one by the same rule and say so; if a file of that name is
   already there, say what it replaces before replacing it. From the cloud this
   is the Drive connector — `create_file` with `contentMimeType` `text/html` and
   conversion off — and the page passes through the chat, about 20k tokens a
   page (measured 29 Sep 2026: a 57 KB page). `\uXXXX` escapes in the engine's
   script come out as the characters they name, which renders identically and
   is not byte-identical; read back the file's size to confirm the save. A
   surface with no Drive tool skips this and says so in one line.
7. **Log the step**: one row for the look behind, dusk, the page URL as its
   deliverable, and in its details, under the divider, **the block from
   `--row-block`, exactly as printed**:
   ```
   [be•do] look behind YYYY-MM-DD · draft
   draft lead: …
   draft story: 🚗 …
   ```
   The first line is how the morning routine finds the row and knows which
   build it stands for — `· draft` at dusk, `· final` once the morning has
   built from the whole day's rows (`--row-block --final`) — never by the
   row's title or practice, which a chat may write differently. The `draft `
   prefix on a line says whose words they are: a part the user touches or
   accepts loses it. When the words change later, rewrite the block in place
   (`--row-block` again, the rest of the details carried forward verbatim).
8. **Sync the calendar from the stream.** The stream is the record of what
   happened; the calendar mirrors it. Every row tied to an event carries the
   event's link in its `event` field, and at the dusk close each linked event
   takes the row's status as its title prefix (⬜ → ✅ / ✖️) and, when the row
   holds a real span, its real times. The script plans; the chat writes.
   ```
   python3 scripts/calendar_sync.py --list --day YYYY-MM-DD \
     --local look_behind_local.json --stream data/w##.json [--stream data/w##-prev.json]
   ```
   Fetch each listed event fresh with `get_event` (its `calendar_id` and
   `event_id` are in the list) and save them to `events.json` with the
   calendar id added to each as `calendarId`. Save `list_calendars` to
   `calendars.json`. Then:
   ```
   python3 scripts/calendar_sync.py --plan --day YYYY-MM-DD \
     --local look_behind_local.json --stream data/w##.json [--stream data/w##-prev.json] \
     --events events.json --calendars calendars.json --out sync-plan.json
   ```
   An event `get_event` can't find on its own calendar may have been moved to
   the user's dropped calendar (named by `dropped_calendar` in the settings; its
   id from `list_calendars`): fetch it there with the same event id, and save it
   with that calendar's id. Then the plan says `already on <dropped calendar>`
   rather than calling it deleted.

   Make each change in `changes` with `update_event`, passing exactly the
   `update` object it names — **`notificationLevel` is always `NONE`** — and
   nothing else. Say what moved in one line.

   **`to_move`** lists the dropped rows whose event is still on a synced
   calendar. The calendar connector can't move an event between calendars, so
   name them to the user in one line, with their links, to move to the dropped
   calendar themselves (the user's word, 3 Oct 2026: be consistent about moving
   dropped things there). Never copy-and-delete instead: that breaks the row's
   link and can't single out one instance of a repeating event.

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

**The gate** (the 9 Oct amendment, rule 5). The builder refuses to write the
page, and says why, when:
- more than 10% of the day's rows that happened lack device or wellness;
- any row spans more than 12 hours (an old row closed with today's end); or
- no row of the day carries the `dayqa shown …` line — `run_checks.sh dayqa
  DATE` hasn't been shown to her at the dusk close (bedo-checks). Run it, show
  her the list, write what she accepts, put its last line in the dusk close
  row, and build again.

There is no way round it for a page that goes out. `--shape-check` exists for
the tests and builds a page that is never published.

**The pie** (9 Oct 2026): walking, cycling, morning movement and any exercise
are Moving whatever the settings' map says, and Moving wins a minute shared
with anything else. 📺 show, 🎥 movie, 📼 video and 🎮 game are Play, never a
drive slice. A row on a drive or rhythm with a real span is Doing — *work and
drives* — whether or not a screen was used. **Who was in your day** reads only
rows that happened (a plan's people are not met yet) and finds each person by
any name they go by.

**Clear the QA before publishing** (the user's word, 2 Oct 2026: a thorough QA every
day). The build prints a `qa` block; work every item, in the stream, before the
page goes out:
- `no_drive` — an action or a meeting with no drive or rhythm. Set it when the
  row plainly belongs to one (a project's row goes to its drive); ask when it doesn't.
- `unknown_practice` / `no_practice` — the practice doesn't match the catalog,
  often an invisible character or a near-miss ("walk" for "walking"). Fix it to
  the catalog's exact string.
- `overlapping_work` — two drive rows on the same minutes. Fine when a Code
  session ran while the user was in a meeting; say so, don't silently keep both.
- `unexplained` — a stretch of 15+ minutes nothing covers. **Fill it from the
  clues, don't ask the user for it** (amendment, 2 Oct 2026): read the rows either
  side and inside it, and write one row for the stretch with the best reading —
  a real practice when the clues name one (getting ready before a drive,
  cooking between home and "dinner made"), else 📝 log — its `[be•do]` block
  saying ESTIMATED FROM CONTEXT, not logged by the user, and naming the clues. Only
  a stretch with no clue on either side stays open, named in one line.
- `meals` — a meal with no minutes, or no prep row before it. Place it by her
  rules, don't ask her for times (the meals amendment, 7 Oct 2026):
  `bash run_checks.sh meals --json` proposes each meal's prep (ordering out 20,
  a simple meal 15, a straightforward dinner 30, a cooked dinner 45) and its
  eating; write them ESTIMATED FROM CONTEXT, then show her the list as what went
  in the record and ask if it's accurate. Timeline beats the defaults.
- `no_sleep` — no sleep row for last night, so the morning draws as nothing
  logged. Write it from the morning Oura row (in bed to out of bed).
- And the calendar: read the day's events after the user has corrected them, give
  each one that happened its own row (a 🗓️ calendar event, ✅ done, titled as
  the calendar line, with the event link), and note any drift from the plan.

**Check what the build printed** before publishing. Three lines are worth
reading:
- `estimates_trimmed_min` above zero means the logged and estimated minutes
  overran twenty-four hours and estimates were cut to fit. Say so in the chat.
- `containers_set_aside` names how many rows held other rows and scored
  nothing — a trip, a field day. Expected on a travel day, odd on a quiet one.
- `destinations` empty on a working day usually means rows are missing a
  drive, not that nothing moved.
- `circles_read` at zero means the connections read didn't arrive and the
  people chips are in bare order of appearance.

## Dusk, on call: the draft

At the end of the dusk flow, in whatever chat is running it, build the day's
look behind **as a draft** and show it. The day is not over — sleep and the
late rows land after — and the words are be•do's until the user says
otherwise, so the mark is right. Steps 1–7 above with `--draft` at step 2;
the calendar sync (step 8) runs here too, at the dusk close, as before.

If the user edits the words there and then, the parts they touch stop being
a draft (`words … --set-lead … --to-page`, republish), and the log row's block
is rewritten to match. The morning routine builds the final from whatever the
row says in the morning.

## Morning, by itself: the routine

A cloud routine, due at 03:00 in the user's time zone, finishes yesterday's
look behind: re-reads the rows, takes the words from the dusk row, builds the
final, publishes, saves. **It builds yesterday, never today**, states the date
it built in its first line, and if it missed a day builds each missed day in
order, oldest first. The whole of it is in `MORNING.md`, which the routine
reads from the version store on every run.

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
- **The grey is two things, drawn apart.** Minutes a row covers that no named
  slice claims are "everything else", solid; minutes no row covers at all are
  "nothing logged", dashed. Before 7 Oct 2026 both were one grey slice, and a
  well-logged day read as half unaccounted for.
- **A dropped intention check is never a line.** A ✖️ or ⨂ intention row is a
  duplicate or a withdrawn one; the action check's glyph is read whether it
  leads or closes each part of its title.
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
- **A routine with connectors.** A routine created from inside a session
  carries no connectors, so it can read Airtable (the credential), build and
  publish (the Artifact tool), but cannot write the log row, save to Drive or
  sync the calendar until it is created from the claude.ai routines page with
  those attached. `MORNING.md` says what to do in each case.

## If it can't run here

If this surface can't save the reads to disk or run Python, say so in one line
and offer to run it from a Claude Code cloud session (the phone app's Code tab
reaches the same environment as claude.ai/code) or from the laptop, which can.
