---
name: "bedo-day-ahead"
description: "Build The Day Ahead page from the stable release. Use at the 👁️ look ahead step of the dawn flow, unasked — a draft before the intention check so the three are in view, the final after it — or when the user asks for the day ahead or the look ahead."
---

# The day ahead

The 👁️ look ahead step IS this page. When the dawn flow reaches that step,
build it without being asked. In the user's words: *I'd like to have it linked
to the Look Ahead practice so it automatically generates.*

**This folder is the skill; what is installed is a loader.** The copy installed
in claude.ai is two files — a loader `SKILL.md` and the user's own
`assets/day_ahead_local.json` — and the loader fetches this folder fresh from
the version store on every run, so a stale copy can never build a page. That
means:

- **A change here needs no upload.** Push it to the version store and the next
  run picks it up.
- **Never upload this folder over the installed skill.** That replaces the
  loader with a copy that goes stale at the next change. It happened on 28 Sep
  2026 and was put back the next morning.
- **Upload only when the settings file or the loader itself changes**, and then
  upload the two-file loader zip. The loader is personal — it names the user's
  calendars — so it is kept with their settings, not in the version store.
- **A new settings key means a new upload.** The builder comes fresh but the
  installed settings do not: a key added to `day_ahead_local.json` reaches a
  claude.ai chat only when the loader zip is uploaded again.

Nothing here depends on project files, so it runs in any project or none.

**Nothing in this file is anyone's in particular.** Every specific — the user's
name, their calendars, the bases and tables, the field ids, the page it
publishes to — lives in `assets/day_ahead_local.json`. **Open that file and read
the value you need** rather than carrying one in memory or guessing from an
earlier chat. The key to read is named below wherever one is wanted.
`assets/day_ahead_local.example.json` is the blank shape, and the README
explains the four keys that aren't self-evident.

## Two passes: the three before the intention check, the final after

**The three come first** (9 Oct 2026, the user's words: *for the look ahead
I'm not seeing the Pareto 3 … it needs to happen in the draft of the look
ahead where you recommend what three things I could do today that would move
the ball forward the most*). From 29 Sep to 9 Oct the dawn ran one build after
the intention check, so the three never reached her while she named her own.
A pass costs little: the rows never pass through the chat, and the second pass
is only `fetch` and `build`. The dawn flow's order is:

1. **⏏️ secure base** — the user's to set, never deduced. **Check the stream
   for one already written today first**, from any chat: one row per practice.
   Since 29 Sep 2026 the ⏏️ row is no longer written every day: `secure` is
   the assumed default, and the other state is written only when the user
   names a knock-back. No row means `secure`.
2. **👁️ look ahead, the draft** — `prep`, the calendars, `cal`, then `build …
   --draft` with no intentions, published to the page. **Say the three in the
   chat, one line each with why it rose** (the build prints them), so they are
   in front of her at the next step.
3. **⚡ intention check** — ask for **one intention** (her rule, 21 and 25 Oct
   2026: *I really just want to be asked for one intention on a daily basis*).
   It is hers, in her words; more only if she offers more. She may fold the
   three into her framing, or ignore them.
4. **👁️ look ahead, the final** — `fetch` (the intention check wrote rows),
   then one build with her intention passed as `--intention "…"`, exactly as
   the user said it (a second or third only if she named them), and without `--draft`. The three stay be•do's
   recommendation; don't rewrite them to match the user's intentions. The plan
   file is written on every build; work from the final one's.

**The chat's three win.** The three are judgment — what moves the ball most,
weighed against the day as the chat knows it — and the chat weighs better than
rules (9 Oct 2026: the day chat's three were the right ones; the builder's
were not). When the chat has named the three, pass each as
`--pick "<row key or record id>::<why, one or two sentences>"`; the page shows
them with their status, so a rebuild later in the day draws one closed as done,
and the builder's own picks step down to next in line. Without `--pick` the
builder chooses.

**Every open card names its next move** (the 7 Oct amendment on the next step
2026, in the builder 9 Oct; the user's words: *what is the website? What is the
thing exactly that I need to do?* and *so I just don't think of the whole big
thing*). Under the title of each of the three, each card after the calendar and
each row past its date: **→ the one step** in bold, *with* the person on the
row, the links (the step's own, then the `deliverable` field, the calendar
event, then any url in the row's words, labelled email thread · doc · calendar
event · the site), and **⏸ waiting on** when that field is set. The step is
read, never invented, in this order:
1. **a `--step "<row key or record id>::<step>"`** from the chat, for a row
   whose words name none. A url inside the step becomes its first link.
2. **a `Next: …` line in the row's details** (also `Next step:` or `Step:`,
   in her words or the `[be•do]` block, newest link in the chain first). This
   is the durable place: **when a chat learns a row's next step, it writes a
   `Next:` line on the row**, and every later build shows it without being told.
3. otherwise the card says **no next step named yet**, so it gets one.
When the stream shows a row may already be done (a later log or close on the
same subject), the step says so — *may already be done — <the evidence>. Close
it* — and the chat asks about it in the one list. Never a guess at the step.

**How the builder chooses** (J9): from uncalendared work, in the order of pull
— someone waiting (another person on the row, due within three days) · target
passed (the most recently passed first) · in motion (▶️, target nearest today)
· named as weighing on her (`weighing_phrases` in her words). One of each kind
first, then the empty slots refilled in the same order. Never a row that is a
calendar event's own (a calendar event never needs recommending), never two
on the same subject, never two from the same person waiting, never more than
two from one drive. A pick that is past its date shows once, in the three, not
again under past its date; the plan's `overdue` still holds it for the asks.

**Build from the stable release. Don't redesign it.** Changes to the layout are
a separate be•do work chat that ends with a push and a new tag in
`github.com/rivuletsteph/be-do`, which is the version store — not with a new
zip; the installed loader fetches the change by itself.

## The files, inside this skill

- `run_day_ahead.sh` — the runner: `prep` · `cal` · `fetch` · `build`. Reads
  Airtable directly with the read-only token, so no row passes through the chat.
- `scripts/day_ahead.py` — the reader and builder
- `scripts/ledger.py` — the ledger of older weeks, for how far each drive has come.
- `scripts/myday.py` — the my day page's two cards, where they lead and the
  whole map, from the same read; the page's name and the day's own link
- `scripts/bedo_cal.py` — the calendar reader: prints what to fetch from the
  Calendar connector, checks what was saved, writes `cal.json`
- `assets/day_ahead_engine.html` — the page, nothing personal in it
- `assets/day_ahead_local.json` — the user's settings, and the only place a
  specific lives. Personal; this copy of the skill is theirs and is not the one
  that gets shared. It is gitignored.
- `assets/day_ahead_local.example.json` — the same shape, empty. This is the
  one that travels when the skill is shared.
- `tests/test_clock.py` — runs the builder over a small fixture and checks the
  times it writes. Run it after any change to the builder, and first of all on
  a machine the builder hasn't run on before.
- `tests/test_cal.py` — drives the calendar reader and checks what it refuses.
- `tests/test_three.py` — how be•do's three are chosen (J9).
- `tests/test_myday.py` — the two cards, the ledger, and the day's own link.

The runner copies them into the working folder fresh from the version store on
every `prep`; nothing here is used from a project copy. Three things differ by
machine and each is an override: `LB_DIR` (the working folder, default
`/home/claude/da`), `LB_LOCAL` (where `day_ahead_local.json` is copied from if
not already there) and `LB_OUT` (where the finished page is also copied). Their
contents never pass through the chat.

**Where the Airtable token is** decides which surface this runs on:

- **A Claude Code cloud session** — claude.ai/code, the Code tab of the phone
  app, a routine — on an environment carrying the read-only token as an API
  credential for `api.airtable.com`: the fetch sends no `Authorization` header
  and the proxy attaches the token after the request leaves the VM. The
  session never holds it. The settings file is synced there with the installed
  skill (`/root/.claude/skills/synced/*/bedo-day-ahead/assets/`) and the runner
  finds it by itself. The calendars come through the Calendar connector, which
  on this surface returns `htmlLink`, `id`, `recurringEventId` and
  `transparency` as the reader expects (checked 29 Sep 2026).
- **The laptop**: `bedo_secrets.json` in the working folder or the folder above
  it, never in the repo.
- **A plain claude.ai chat** has neither: `prep` still clones and prints the
  calendar plan, says the rows must come through the chat, and exits 3.

## Steps

1. **Read live, complete or abort** (I13, I11) — one command, no rows through
   the chat:
   ```
   LB_DIR=<working folder> bash run_day_ahead.sh prep YYYY-MM-DD
   ```
   `prep` clones the version store, then reads straight from Airtable with the
   read-only token: the live weekly stream `w## be•do` resolved by name, the
   previous week's base (I14, passed to the builder live first, I15), and
   rhythms from `rhythms_base` / `rhythms_table`. Each read is paged to the end
   or the run aborts; a partial file is never written. It ends by printing the
   **calendar plan**: the 14-day window and, for each calendar the settings
   name, the exact `list_events` arguments and the file to save the result to.

   *Without the runner* (a surface that can't run Python), the old path still
   works: `list_records_for_table` with pageSize 8000 and every field, saved
   oversized results (`/mnt/user-data/tool_results/…`, wrapped
   `[{"text": "<json>"}]`, which the builder unwraps itself) copied to
   `w##.json`, and an inline rhythms read written out as
   `{"records":[…],"metadata":{"totalRecordCount": n, "read_total": N}}`.
2. **The calendars, through the connector.** This is the one read that still
   passes through the chat: the Airtable token cannot read Google Calendar, and
   on 28 Sep the connector was chosen over Google credentials on disk. Fourteen
   days of two calendars is a few thousand tokens.
   - `list_calendars` → save the whole result to `cal/calendars.json`.
   - For **every calendar the settings name** — `self_calendar` plus each label
     in `other_calendars`, whose names `calendar_summaries` gives as
     `list_calendars` shows them — `list_events` with the plan's arguments, the
     id taken from `calendars.json` every time, never from memory or a doc.
     Save each result to the file the plan names, `cal/<label>.json`: as
     returned, or trimmed to `summary`, `nextPageToken` and, per event, `id`,
     `summary`, `status`, `start`, `end`, `htmlLink`, `location`,
     `recurringEventId`, `transparency`. A result that carries `nextPageToken`
     is not finished: fetch the next page and save every page as a list.
   - Then
     ```
     bash run_day_ahead.sh cal YYYY-MM-DD
     ```
     writes `cal.json` in the shape the builder reads — `who` is the settings
     label, `recurring` and `transparent` are marked, `htmlLink` is kept because
     it is how an event and its row find each other — and prints **one line per
     event. Read those lines against the calendar before building.** The
     reader refuses a calendar missing from the list, a result whose `summary`
     is not that calendar's name (the wrong id), a last page still carrying
     `nextPageToken`, an event outside the window, an event with no link, and
     a link that names a different event than its id says. It cannot see an
     event that was never saved; the read-back is for that.

   A read-only calendar (`readonly_calendars`) may come back with no events —
   that is a real read, stated as such. Leave out any calendar not named in
   the settings (holidays, a dropped-events calendar). *A one-calendar read is
   how an appointment kept only on the child's calendar went unseen.* Before the
   page names an event a gap, check the stream with a `contains` filter on the
   title (I7).
3. **Secure base.** Today's ⏏️ row, in the user's words, if there is one;
   otherwise `secure`, the assumed default, with no words.
4. **The draft, the intention check, then the final.** Before the intention
   check, `bash run_day_ahead.sh build YYYY-MM-DD <state> --now HH:MM --draft`,
   publish, and say the three. After it — the intention check nearly always
   writes rows (retargets on the three, the ⚡ intention check row) — re-read
   the live stream first, `bash run_day_ahead.sh fetch YYYY-MM-DD`, then:
   ```
   bash run_day_ahead.sh build YYYY-MM-DD <state> [--secure-words "<their words>"] --now HH:MM \
     --intention "…" \
     [--pick "<key>::<why>" --pick "…" --pick "…"] [--step "<key or record id>::<step>" …]
   ```
   Everything after `<state>` goes to `scripts/day_ahead.py` unchanged. The
   direct call, for a surface without the runner:
   ```
   python3 scripts/day_ahead.py --today YYYY-MM-DD --local day_ahead_local.json \
     --stream w##.json --stream w##-prev.json --rhythms rhythms.json \
     --calendar cal.json --template day_ahead_engine.html \
     --out YYYY-MM-DD-day-ahead.html --secure <state> [--secure-words "<their words>"] \
     --now HH:MM --intention "…"
   ```
   `--now` is the local clock read for this write (I12); it keys today's rows.
   If it aborts on a short read, don't build from a partial read. Say which read
   came back short and read it again.

   It aborts the same way when the local settings file is missing a field id or
   the clock offset, or when `utc_offset_hours` disagrees with `time_zone` on
   the day being built (daylight saving ends 1 Nov 2026). That is deliberate:
   a blank id reads every row as empty, and the page would look calm and be
   wrong.
5. **The plan — the calendar's two horizons.** Beside the page the builder
   writes `<out>.plan.json` on every build; read it from this one.
   - **`today_rows` — written, then shown.** Every event today with no row of
     its own. The calendar is the record of what is scheduled, so this is
     recording, not supplying. Each carries its fields by id — title, key,
     ⬜ intention, ⚡ action, person, datetime (the write), target (the event),
     the drive read off the event's glyph, and the event link in the stream's
     `event` field. **Add phase, wellness and device** the usual way (deduced,
     never asked), then write them in one call and show them as a short list.
     A row closes ✅ when the event happens.
   - **Every event today gets its own row** (9 Oct 2026, the user's words: *why
     don't they have a row? They should have a row*). A same-subject intention
     (*show up at the two celebrations*) is hers and stays; the event's row is
     separate. An ask left unanswered leaves `no row yet` on the page, so ask
     it in the first reply after the build, never let it sit.
   - **`future_rows` — every event in the next two weeks, written** (9 Oct 2026,
     the user's words: *I want all of these events in the system 2 weeks ahead of
     time … to give it future vision*). One ⬜ row per occurrence, each with its
     own event link, the drive read off the glyph (written without one when no
     drive is clear, and named), people on a plan in `mentioned`. Not an
     occasion (an all-day free marker) and not an event marked ✖️. Run them
     through `entry` and write them in one call. **Then reconcile, before the
     final build** (next item).
   - **Reconcile the two weeks — the calendar is not taken verbatim** (9 Oct
     2026, the user's words: *it's not just taking verbatim what's in the
     calendar. It's helping me make the decisions and having them show up
     properly on the calendar*). Read `conflicts` and each event's clashes as
     decisions waiting on her: work inside a vacation, a child's events while
     the child is away with her, a trip still ❔, two copies of one meeting, a
     trip's end that disagrees with its own rows. Ask them as **one short set
     of questions, a recommended answer first**, then carry the answers out the
     same morning:
     - **Dropped** — `✖️` in front of the title and **moved to the ✖️dropped
       calendar**, so it stays visible but off her own. The connector cannot
       move an event, so: create the ✖️ copy on the dropped calendar (free,
       no reminders, a one-line why), then delete that one occurrence from
       the original with no notifications; the series stays. Its row goes
       ✖️ dropped with the new event link and her words.
     - **Undecided** — stays ❔ and gets a decide-by: the date from her own
       words when she gave one, on the row that holds the decision, with a
       `Next:` line.
     - **Dates that disagree** — the calendar is corrected to her answer.
     Never decide for her, never delete a series, never touch a read-only
     calendar.
     - **Work events are purple** (9 Oct 2026: her university's colour): any
       work event be•do creates or edits gets `colorId` 3; a recurring series is coloured on the
       series. Work is a drive under `work_parents`, or a university or
       project meeting.
     - **A duplicate** is merged into the one she keeps (her ⬜, her colour,
       the other's details), and the copy is dropped as above, its row ✖️ as a
       dedupe onto the kept one.
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
   - **`overdue` — every open row past its date, resolved, never carried.**
     Decided 1 Oct 2026, at the user's word: *those are actually super relevant
     and important, so they need to be resolved — they can't be buried.* The
     page lists them all in their own open section near the top, oldest first,
     each with how many days late it is; nothing past its date is folded away.
     Before the final build, **sweep them against the stream**: a later row
     that shows the thing happened, was done, or lives under another live key
     closes it in place, with the evidence named in the `[be•do]` note (✅ done,
     or ✖️ dropped as a DEDUPE onto the live key, or as passed when its moment
     is gone with no record). A shared word is not evidence. **Everything the
     sweep can't close goes into the one numbered list** — done, a new date,
     drop, or someday — and the user's answers are written the same morning. A
     date they give is a retarget; a target they didn't give is not supplied.
   Matching an event to its row goes: the row's `event` link first, then
   `event_aliases` (the user's own names for a recurring thing), then shared
   words. **Today is held stricter**: a same-subject row only counts as the
   event's own if it is timed within the hour; otherwise it becomes an ask.
6. **Publish to the day's own page** (261028_myday, her decision of 28 Oct
   2026: *at the end of the day it just becomes the day behind, and that's
   what's saved for the record*). Each day has one my day page, named like that
   day's my day chat — the build prints it as `page.title` and puts it in the
   page's `<title>` (`▶️🔆1028 💧 Wed 𖡎 W44 my day`). The build also reads
   today's ◉ 👁️ look ahead row and prints `page.url` and `page.row`:
   - **`page.url` set** — the day's page exists: republish to that link, in
     place. The draft, the final, and every later piece of the day (its rows
     and photos, the close) go to this one link.
   - **`page.url` empty** — the first publish of the day: publish a new
     artifact (favicon 👁️), then write its link to the look ahead row's
     `deliverable` (`page.row`; if the row isn't written yet, write it with the
     link in it). That row is where every later build finds the link.
   `artifact_url` in the settings is the old single living page; it is never a
   day's own, and the build ignores it as one. No Drive copy each time: the
   pages are exported at the desktop (her word, 28 Oct 2026).
7. **Log the step**: the ◉ 👁️ look ahead row, dawn, with the day's page as its
   deliverable and one `[be•do]` line naming the three, the gaps and the clashes.

**Saving to Drive from the cloud** is the Drive connector's `create_file`,
`contentMimeType` `text/html`, conversion off, into the week's folder found by
name (created by the same rule if missing, and said so). The page passes
through the chat, about 15k tokens for this page. A surface with no Drive tool
skips it and says so in one line.

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
- **Drives within drives.** A drive can feed another (the rhythms field
  `feeds`, `fields.rhythms.feeds` in the settings; optional). *Open by drive*
  counts each open row under its own drive and every drive it feeds, the child
  nested under its parent; its headline counts each row once. A pick's lane runs
  through the drives above it to what they serve, two picks from one drive's
  tree share one lane, and a drive feeding a hidden drive is hidden with it. The
  plan carries the same tree as `drives` — read it before advising on what is
  coming up: a step on the child is progress on the parent. A loop in `feeds` is
  listed under `drives.loops`; ask her which way it runs.

## What the page shows, in order

Set by the user between 1 and 5 Oct 2026; the engine draws exactly this.

**The test for every item** (5 Oct 2026, in their words): *what is the next
right thing to do — the step that is waiting on me to take.* Every item
carries both its drive or rhythm (what it serves) and the one step waiting on
the user. A project with no named next step is the defect.

1. **The date**, with ⏏️ beside it when the base is secure — a small emoji,
   no callout. Anything other than secure gets one line under it, in the
   user's words. Under the lead, **one chore for her son** (11 Oct 2026): one
   small thing that fits the day — help packing when there's an outing, else
   the next of `kid_chores` (or the builder's own list). Name it once in the
   reply, as the build prints it; she decides whether he does it, and it is
   never pushed again that day. It feeds Hero's Service on his quest.
2. **Your intention** — one slot, in the user's words; one empty slot before
   they name it. More slots only when they name more. Above the week's word (8 Oct 2026, their
   words: *my daily intention above the week's intention, then the calendar*).
3. **The next right thing** — be•do's three, their own section (28 Oct 2026,
   her words: *I really just want to see what is the next right thing … sometimes
   I like to have choices*). The first not yet done stands in front; the others
   sit under *or, if that can't happen now*; one done today drops to the end,
   struck through. Each card says why it rose and its way in: the chat, the
   deliverable, the links in its words, or, plainly, *no way in yet · open a
   chat for it*. Before the intentions are named this is what the draft is for.
4. **This week's word** — one small line since 28 Oct 2026 (her words: *it's
   too prominent*). **Today on the calendar** (5, below) now sits above the next
   right thing, right under the intention (28 Oct 2026: *those are the things
   that are not moving … what I do a lot in response to*).
5. **Today on the calendar** — every event as the calendar shows it
   (its own title and glyphs, start and end, a 🗓️ link), in the day behind's
   event cards, with its drive underneath. A child's calendar gets the ochre
   edge.
   **Past its date** — every open row past its target, oldest first, never
   folded away (see `overdue` above). Empty when the morning's answers are in.
6. **After the calendar** — not drawn on a weekday since 28 Oct 2026 (her
   words: *these are all things I wanted to do today, but it's not all going to
   happen*); the plan still carries `tasks`. What it held: what else is due within `task_horizon_days` (7) and dated work
   within `soon_days` (3; `0` keeps the list to today, her setting from 28 Oct 2026),
   at most `max_tasks` (10) with the three, never a row that is a calendar
   event's own and never a row past its date (it has its own section). Each card: the date on the left (`today`, or
   the weekday and day; plum once passed), the status and ⚡ **drawn, not
   typed** — a brick-outlined square for an intention, filled with a play mark
   in motion, teal with a check when done, dashed for a potential, and a gold
   bolt — then the title in semibold, the drive's emoji and name beneath, and
   why it rose (`someone waiting`, `in motion`…) in small type.
7. **The next three days, from tomorrow** — today is not repeated here; it has its
   own section above (9 Oct 2026). The rest of the two weeks folds into one closed
   line, *later in the two weeks*, its calendar events only (28 Oct 2026: the
   next 1, 2 or 3 days need to show up more than the things way out). Each due
   line names its drive and, when the row has them, its next step and links
   (28 Oct 2026: *it's not clear what [it] is … what is the next step?*). Both calendars matched against the stream,
   with `no row yet` and `clash` tags. Each due line starts with the same
   drawn status and bolt, then its drive's emoji (the drive's name on hover).
   **On the horizon** — after the days (28 Oct 2026, her words: *the big events
   … the things I really need to prepare for … here's what you need to do to
   prepare for those*). Each item: its date and how far off, or *no date yet ·
   not on the calendar*; and the open steps that prepare it, in motion first,
   four at a time, each with its step and links when the row has them; an item
   with none says *no steps yet · break it down in a chat*. Two sources, both
   off the rows: an active drive whose own date falls within
   `horizon_drive_days` (14), and each `horizon` entry in the settings —
   `{label, emoji, match}`, a pattern on open row titles, dated within ten
   weeks or undated, gathered as one item.
8. **Where they lead** — card 1, saved 4 Oct 2026: the day only. Today's
   steps (due today, carried in from the last week, set this morning, or done
   today) under the drive or rhythm they serve, drives first, then rhythms;
   every step shown with her words and its way in (as in the three), a red open
   box in front and the bolt after; each drive's % progress (`done of done +
   open, since` its first row in the read or the ledger) and its line on to its
   date and destinations.
9. **The whole map** — map v3, saved 5 Oct 2026: every rhythm in code order,
   and only the drives with a step today (28 Oct 2026; the rest fold into `+N
   resting`); the past folded into one narrow shaded band (*since jun*), the
   months ahead given the room, today's red boxes, the curves into the
   destinations; tap a drive or a destination to follow it — four steps at a
   time, each with its way in, and a step still open with a deliverable on it
   marked *has its deliverable · done?*. *How far you've come* reaches back as
   far as the ledger does (below).
   Both are built by `scripts/myday.py` from the same read, never by hand: the
   rhythms, drives and destinations from the rhythms table (a rhythm's code
   orders it and picks its earthy colour; `rhythm_colours` in the settings
   can name one), the steps and the ground covered from the stream.
   **The ledger** — `history/*.json` beside the settings file (or `--history`),
   made by `scripts/ledger.py` from older reads and the weekly CSV backups:
   every finished step and lived row on a rhythm or drive, so a drive's % does
   not drop to 0 when its work is older than the read (28 Oct 2026). It is the
   person's, kept in the working folder, never in the repo; without it the
   page reaches back only as far as the read.
10. **Open by drive** — not drawn since 28 Oct 2026 (*redundant … overwhelming*);
   the plan still carries `drives`.

**Kept off the page, at the read** (5 Oct 2026):
- **Build work on the system itself** — any row on a drive named in
  `hide_drives`, *except* a row whose title names one of the user's own
  reviews (`hide_keep`: their weekly and monthly reviews and look aheads).
  Those are theirs, not build work, and stay.
- **⏱️ quickies** — the row's `quickie` checkbox (`fields.stream.quickie`).
  Quickies are offered when the user says they have a few minutes, never here.
- The **still-true strip** is gone (one of the five V53 drops).

**Practices with a cadence** (5 Oct 2026, making A132 of 13 Sep real): the
practices catalog carries a `cadence` field, free text like `weekly · Monday`
— chosen, where `regularity` and `drift` are observed. When the settings name
the catalog (`practices_base`, `practices_table`, `fields.practices` with
`name`, `active`, `cadence`), the fetch reads it and the build draws each active
practice with a cadence on its weekday: first in the task list today, first
among the due lines in the next fourteen days. It shows done (teal check) once
a row logged that day, not open, carries that practice; its drive is the drive
of the latest row that carried it. Nothing here is a parallel mechanism —
cadence lives on the practice, as A132 asked.

The provenance line counts what each filter set aside.

**Light or dark, as the device is** (her word, 28 Oct 2026: *I like to be able
to view it in dark or light mode. Dark mode is good at night when I'm looking at
it or first thing in the morning*): the page follows the device's setting, and
the switch at the top (device · light · dark) sets it for that device. Never
light-then-dark by the clock. Both are the now palette
(`plugins/bedo/assets/now-palette.css`), which `test_palette.py` holds it to;
the two cards keep their earthy colours in both. It must fit a phone: no
horizontal scroll at 390 px (the whole map scrolls sideways inside its card).

## Saturday and Sunday have their own shape

25 Oct 2026, the user's words: *a Sunday look ahead is fundamentally different
from Monday through Friday. Saturday is also different. The goals are generally
different* — and *Sunday morning is reserved for reflection*. V53 dropped the
SUNDAY section (crosswalk row 66) and the Sunday look ahead's shape went with
it; this puts it back in code. The builder picks the shape from the date;
`--shape weekday|saturday|sunday` overrides it (a Sunday that is a travel day
may want the weekday page).

**Sunday** — big picture only, no leverage list, no task queue (the 6 Sep
Sunday look ahead's own words). In order: the date and the lead, which reads
the week in one line (*Monday is open, Tuesday is the peak, Thursday has a
clash*); her intention; **sunday morning**, held for reflection until
`sunday_morning_until` (12:00), with the day's cadence practices (the 🕯️
reflection) and any event that would cut into the morning named, not moved;
the week's word; today on the calendar; **the week ahead**, Monday to
Saturday, each day tagged *the peak* (the most hours on her calendar), *open*
(a weekday with nothing of hers), *clash* (a named conflict, said under it) or
*away* (a stretch away; a ⬜ window like early voting is not one); **ready for
Monday**, open work due in the next two days that isn't a calendar event's own
row, the chat's `--pick`s first when given; past its date; **the week after**.
No be•do's three, no task list, no cards, no open by drive. In the chat, say the
lead line and what's ready for Monday, not the three.

**Saturday** — fun first; the calendar comes after (her words, 24 Oct). Her
intention, today on the calendar, past its date, **when there's room:
tending** (at most three open rows under the rhythms the settings name in
`tending`, never under `work_parents`: past their date first, then due this
week, then in motion), then the next two weeks. No three, no task list, no cards.
`saturday_lead` in the settings can reword the lead.

The settings keys (`tending`, `sunday_morning`, `sunday_morning_until`,
`saturday_lead`) are optional and live in the `day_ahead_local` settings row,
so changing one is an edit to that row, not an upload. Without `tending`,
Saturday draws no tending section.

## What the user sees in the chat

One or two lines, not the page again: the three, the today rows just written,
that the page carries their intentions, and anything the calendar flagged as a
clash. Then **one numbered list** holding every ask — today's asks and the prep
drafts with their targets, and every row still past its date after the
evidence sweep — so the user answers once. Say how many the sweep closed and
on what evidence, in a line. The page holds the rest.

## The three are recommendations

The page's three are be•do's; the user's intentions are their own. If they turn
one of the three down, name the next in line (the page shows it) instead of
rebuilding.

## Not built yet

Nothing fires this unattended, by design: the day ahead is on call, built when
the user reaches the 👁️ look ahead step. The other half of the calendar work —
mirroring what happened back onto linked events — runs at the dusk close, in
`bedo-look-behind`.

## If it can't run here

If this surface can't save the reads to disk or run Python, say so in one line
and offer to run it from a Claude Code cloud session (the phone app's Code tab
reaches the same environment as claude.ai/code) or from the laptop, which can.
