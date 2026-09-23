---
name: "bedo-day-ahead"
description: "Build The Day Ahead page from the stable release. Use at the 👁️ look ahead step of the dawn flow, unasked (a draft before the intention check, the official version after it), or when the user asks for the day ahead or the look ahead."
---

# The day ahead

The 👁️ look ahead step IS this page. When the dawn flow reaches that step,
build it without being asked. In the user's words: *I'd like to have it linked
to the Look Ahead practice so it automatically generates.*

**This skill is self-contained.** The builder, the page engine and the user's
settings travel inside it, so it runs in any project or none. Updating it means
uploading a new zip of this folder in Settings. Nothing here depends on project
files.

**Nothing in this file is anyone's in particular.** Every specific — the user's
name, their calendars, the bases and tables, the field ids, the page it
publishes to — lives in `assets/day_ahead_local.json`. **Open that file and read
the value you need** rather than carrying one in memory or guessing from an
earlier chat. The key to read is named below wherever one is wanted.
`assets/day_ahead_local.example.json` is the blank shape, and the README
explains the four keys that aren't self-evident.

## Two passes, in this order

In the user's words: *I'd like for the secure base practice to fire first, then
look ahead as a draft, then the intention check, and then the look ahead can
potentially integrate the intentions and produce the official version.*

1. **⏏️ secure base** — the user's to set, never deduced. Log their words as the
   ⏏️ row. **Check the stream for one already written today first**, from any
   chat: one row per practice. If one exists, use it.
2. **👁️ look ahead, draft** — build with `--draft`. The page carries a
   "draft · before your intentions" mark and empty intention slots.
3. **⚡ intention check** — the user names their own intentions, in their own
   words. They may fold the three into their own framing, or ignore them.
4. **👁️ look ahead, official** — rebuild with each intention passed as
   `--intention "…"`, exactly as the user said it, and without `--draft`. Their
   intentions fill the slots. The three stay be•do's recommendation; don't
   rewrite them to match the user's intentions.

**The official pass re-reads the live stream** — the intention check nearly
always writes rows (retargets on the three, the ⚡ intention check row). Rhythms
and the calendars from the draft can be reused within the sitting. Both passes
publish to the same link. Log one 👁️ look ahead row and update it in place for
the official pass.

**Build from the stable release. Don't redesign it.** Changes to the layout are
a separate be•do work chat that ends with a new zip of this skill (and a new tag
in `github.com/rivuletsteph/be-do`, which is the version store).

## The files, inside this skill

- `scripts/day_ahead.py` — the reader and builder
- `assets/day_ahead_engine.html` — the page, nothing personal in it
- `assets/day_ahead_local.json` — the user's settings, and the only place a
  specific lives. Personal; this copy of the skill is theirs and is not the one
  that gets shared. It is gitignored.
- `assets/day_ahead_local.example.json` — the same shape, empty. This is the
  one that travels when the skill is shared.
- `tests/test_clock.py` — runs the builder over a small fixture and checks the
  times it writes. Run it after any change to the builder, and first of all on
  a machine the builder hasn't run on before.

Copy them to a working folder from the directory this SKILL.md was read from
(`cp -r <skill dir>/scripts <skill dir>/assets /home/claude/da/`). Their
contents never pass through the chat.

## Steps for each pass

1. **Read live, complete or abort** (I13, I11). `list_records_for_table` with
   pageSize 8000 and every field.
   - The live weekly stream, `w## be•do` resolved by name, then the previous
     week's base (I14). Pass them to the builder live base first (I15).
   - Rhythms: the base and table named in `rhythms_base` and `rhythms_table`
     in the local settings file.
   - **Every calendar the user named, for today plus 14 days**: the one labelled
     `self_calendar` plus each label in `other_calendars`. `calendar_summaries`
     maps each label to the calendar's name as `list_calendars` shows it; take
     the IDs from `list_calendars` every time, never from memory or a doc. A
     read-only calendar (`readonly_calendars`) may come back with no events —
     that is a real read, stated as such. Leave out any calendar not named
     there (holidays, a dropped-events calendar). *A one-calendar read is how an
     appointment kept only on the child's calendar went unseen.*

   **Where the reads land.** In a claude.ai chat an oversized read saves to
   `/mnt/user-data/tool_results/<tool>_<id>.json`, wrapped as
   `[{"text": "<json>"}]`. **The builder unwraps that itself** — `cp` the saved
   file to `w##.json` and pass it. Name the copies by week so the page's
   provenance line reads `w39 635/635`.

   **A read small enough to come back inline doesn't save to disk.** Rhythms
   (about 100 rows) does this. Don't re-read hoping it spills. Write
   `rhythms.json` from the inline result: `{"records":[…],"metadata":
   {"totalRecordCount": <rows written>, "read_total": <the full read count>}}`,
   with every active drive, destination and rhythm and the fields the builder
   reads (name, code, type, status, target, parent, emoji, destination). With
   `read_total` set, the page states it honestly: `100/100 (46 active rows used)`.
2. **Write `cal.json`** in the shape the builder reads:
   `{"calendars":[{"who":"<self_calendar>","events":[…]},{"who":"<an other_calendars label>","events":[…]}],"read":{"window":"…","<self_calendar>":"n/n","<label>":"n/n"}}`.
   The `who` values must match the labels in the local settings file exactly, or
   the builder can't tell the user's events from anyone else's. Each event keeps
   `summary`, `start`, `end`, `htmlLink`, `location` and `recurringEventId` as
   the calendar returns them — **all-day dates can stay as
   `2026-09-20T00:00:00Z`; the builder cuts them to the date.** Add
   `"recurring": true` when the event has a `recurringEventId`, and
   `"transparent": true` when its transparency is `transparent` (an all-day
   occasion that blocks nothing, which carries no row). **`htmlLink` is not
   optional**: it is how an event and its row find each other. Before the page
   names an event a gap, check the stream with a `contains` filter on the
   title (I7).
3. **Secure base.** Today's ⏏️ row, in the user's words. If there isn't one yet,
   ask once and log it before building.
4. **Build:**
   ```
   cd /home/claude/da
   python3 scripts/day_ahead.py --today YYYY-MM-DD --local assets/day_ahead_local.json \
     --stream w##.json --stream w##-prev.json --rhythms rhythms.json \
     --calendar cal.json --template assets/day_ahead_engine.html \
     --out YYYY-MM-DD-day-ahead.html --secure <state> --secure-words "<their words>" \
     --now HH:MM [--draft]  |  [--intention "…" --intention "…" --intention "…"]
   ```
   `--now` is the local clock read for this write (I12); it keys today's rows.
   If it aborts on a short read, don't build from a partial read. Say which read
   came back short and read it again.

   It aborts the same way when the local settings file is missing a field id or
   the clock offset. That is deliberate: a blank id reads every row as empty, and
   the page would look calm and be wrong.
5. **The plan — the calendar's two horizons.** Beside the page the builder
   writes `<out>.plan.json`. Draft pass only; the official pass rebuilds the
   page and leaves the plan alone.
   - **`today_rows` — written, then shown.** Every event today with no row of
     its own. The calendar is the record of what is scheduled, so this is
     recording, not supplying. Each carries its fields by id — title, key,
     ⬜ intention, ⚡ action, person, datetime (the write), target (the event),
     the drive read off the event's glyph, and the event link in the stream's
     `event` field. **Add phase, wellness and device** the usual way (deduced,
     never asked), then write them in one call and show them as a short list.
     A row closes ✅ when the event happens.
   - **`today_asks` — asked, in the one list at the end.** An event whose glyph
     names no single active drive, or where a row about the same subject is
     already on today and may be its own. For the second, the answer is usually
     *link that row*: put the event link on it rather than writing a new one.
   - **`prep` — drafted, shown, written only on the user's okay.** For each event in the
     next two weeks (the next one of each recurring series, with a count of the
     rest), be•do drafts **what it needs prepared** — one short line, read off
     the event and its drive's open work — and the prep ⬜ row the builder
     proposes, with its target. **A target the user did not state is supplied, so it
     is asked** (I3): one numbered list, answered once. Skip anything plainly
     needing nothing. Written prep rows carry the event link too.
   - **`conflicts` — named, never resolved.** Overlaps on the user's calendar, a child's
     event overlapping theirs (who has the child?), a child's event inside a stay
     elsewhere, a readonly calendar's event over a child's, a day too full
     (`full_day_hours`, `full_day_events`), and tight travel between two places
     (`travel_buffer_min`). be•do never schedules.
   Matching an event to its row goes: the row's `event` link first, then
   `event_aliases` (the user's own names for a recurring thing), then shared
   words. **Today is held stricter**: a same-subject row only counts as the
   event's own if it is timed within the hour; otherwise it becomes an ask.
6. **Publish** to the same artifact, copying the page to
   `/mnt/user-data/outputs/` first. The link is `artifact_url` in the local
   settings file (title The Day Ahead, favicon 👁️). One living page,
   republished in place, pinned in the sidebar.
7. **Save the official page** to that week's Drive folder,
   `be•do/<year>-W## <Mon D>/YYYY-MM-DD-day-ahead.html`, and read back a line
   to confirm. The draft isn't saved separately. **A claude.ai chat has no Drive
   commit tool**, and uploading through the Drive connector would pass the whole
   page through the chat. There, skip it and say so in one line: the published
   page and `/mnt/user-data/outputs/` are the copies of record.
8. **Log the step**: the ◉ 👁️ look ahead row, dawn, with the page URL as its
   deliverable and one `[be•do]` line naming the three, the gaps and the clashes.

## Clock and drive names

- **Re-read the clock before the first write (I12).** When the time tool isn't
  available in a turn, write with a best estimate, then correct the row's
  datetime and key to its `createdTime` in place. The builder's own offset is
  `utc_offset_hours` in the local settings file.
- **The drive field on a row is the drive's plain name.** For a drive named
  `D9 — Example drive`, the row reads exactly that, never `🌊 D9 — …`.
  The builder joins rows to drives by name, so a glyph in front drops the row
  out of its drive's lane and out of the three. A strand's glyph belongs in the
  chat title, not on the row. When a row turns up with a glyph in front, clear
  it: an obvious fix, one line. (`drive_name_example` in the local settings file
  holds one of the user's own, if the real shape helps.)

## What the user sees in the chat

One or two lines, not the page again. After the draft: the three, the today
rows just written, and anything the calendar flagged as a clash. Then **one
numbered list** holding every ask — today's asks and the prep drafts with their
targets — so the user answers once. After the official pass: one line saying the
page now carries their intentions. The page holds the rest. Don't list the
overdue pile.

## The three are recommendations

The page's three are be•do's; the user's intentions are their own. If they turn
one of the three down, name the next in line (the page shows it) instead of
rebuilding.

## Not built yet

The builder reading Airtable by itself, and firing unattended at dusk. The
other half of the calendar work — mirroring what happened back onto linked
events — runs at the dusk close, in `bedo-look-behind`.

## If it can't run here

If this surface can't save the reads to disk or run Python, say so in one line
and offer to run it from a Cowork session on the user's laptop, which can.
