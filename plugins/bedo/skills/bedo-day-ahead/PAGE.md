# The day ahead and the my day page: what they draw

**Not loaded to build a page.** The builders draw all of this; a chat needs none
of it to run `prep`, `fetch` and `build`. Read it when she asks why the page
shows something the way it does, or before changing a builder. Moved here from
`SKILL.md` word for word on 11 Nov 2026, so the skill a chat reads every morning
holds only the procedure.

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
   **The top, since 28 Oct 2026** (her words): the chat's name; then *Week 44 —
   Connection*, the week and its word; then the date and the day, with the
   day's intention under it. The lead line, the chore and the secure base are
   off the heading for now (*a clear day ahead* "falls flat" late in a full day;
   the secure base is "too many pointy emojis") — the plan still carries them.
2. **Your intention** — in the header since 28 Oct 2026; one slot, in the user's words; one empty slot before
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

## How things flow (29 Oct 2026, her latest and greatest)

Her words: the whole map should become *how things flow*, and be more of the basis;
tending and growing are different actions, and some days want the minimum of one and
the most of the other; and *choose for me, based on my readiness and how caught up I am*.
`scripts/flow.py` builds it from the built day-ahead page, the reads beside the settings,
and the week's day behinds (`--behind`, a folder; the runner passes `behind/` in the
working folder when it exists). **It is the day's my day page** (since 2 Nov 2026), titled
with the day's my day name, built by every `build` and published to `page.url`.

1. **Base flow** — the morning card, drawn as water through the last seven mornings. Three
   parts, 0–100, in equal shares: **body** (that morning's readiness, the
   `readiness_practice` row, default *morning oura*), **balance** (how evenly the day
   before's wheel was shared: 100 when its eight are equal), **buffer** (her word: the
   space between her and what's due — every open step already past its date that morning,
   tending 1.5 and growing 1, 100 less 6 a point; queued, waiting, quickies, an event's own
   row and hidden build work set aside). The river is as wide as each morning's base flow,
   its strands as wide as their shares; tap a morning to see its sum. A part that can't be
   read is left out and said so.
2. **The lean** — be•do chooses: base flow *optimal* (85+) → a growing day, *good* (70–84)
   → balanced, *pay attention* → a tending day; a knocked-back secure base pulls to tending.
   The page says why. No switch, and no week or month view: just today and the next
   right step, what is actionable (her words, 29 Oct 2026).
3. **The rhythms, with their drives** — one block per rhythm, resting on ☸️ a balanced
   wellness wheel, the foundation (her words): *tend* first, then *grow*, each drive with
   its goal in her words. Each list runs from the easiest next step, read from the row (its
   deliverable on it, in motion, a way in, today) — steps record no effort.
   A tending day shows every tending step and rests the drives; balanced, the easiest one each (no stars, her words); a
   growing day, tending only what's due today and up to four steps a drive.
4. **The flow** — steps → drives → rhythms → the wheel, each drive dotted on to its
   destinations, for today. Done today is
   drawn done, with each drive's % moved today.
5. **The intention** — after the lean, how much the day holds, in one line (*about 3 hours
   you could give to steps today*): the hours a day could give to steps (`step_day_hours`,
   default 8) less her own timed events today on the page's calendar, and
   `travel_buffer_min` for each one at a place (`full_day_hours` booked says *a full day*);
   then base flow scales it — *optimal* aims for most of it (¾), *good* a comfortable share
   (½), *pay attention* a little (¼). She taps the steps she intends — the easiest next
   step on each rhythm and drive, numbered from the highest priority, no stars (her
   words): the lean's own kind first (tending on a tending day, the drives on a growing
   day), then past its date, due today, the easiest way in, the soonest date — and a bar
   fills as she picks. Steps record no size: be•do guesses
   15 min, 1 h or half a day off the step's words and marks it *guess*; a tap on the size
   sets hers. Her picks and sizes stay in that browser for now — a size field on the
   stream is hers to add, not be•do's.
6. **☸️ Today's wheel, so far** — at the bottom (3 Nov 2026, her words: *I would like to see
   the wellness wheel at the bottom … built throughout the day*). Today's lived rows so far,
   each under its wellness element, weighed as balance weighs the day before (a span's
   minutes over six, a moment one; plans, skips, drops and sleep score nothing), drawn as the
   look behind draws its wheel: be to the left, do to the right, a share for each of the
   eight. Tap an element for the rows that made it; the rows fold under one line. It grows
   with each rebuild of the page through the day — `fetch`, then `build`, then republish.

**The page's order follows the day, and one kind of time runs through it** (7 Nov 2026, her words: *I like to see
the base flow up at the top early in the day, but then drop it down to the very bottom in the afternoon; what I want to
see at the top is the how the time is going viz … and when I click on something in the how I'm spending my time widget,
it highlights those things in the timeline and the wellness wheel*). Before noon on the viewer's clock, base flow
leads; from noon, and on a day already gone, *how the time is going* leads, then today's wheel, then the timeline, and
base flow closes the page (`arrange()` in the engine). A tap on a kind in the pie or its bars lights that kind's cards
on the timeline (the rest fade) and the wheel's elements its rows fed, a second tap, or *show all*, clears it. The bars
sit on top; under them one ring of the day's 24 hours with the wheel in its middle (her words, 7 Nov: *combine those two into one, with the wellness wheel in the middle and the day's 24 hours around the outside*), the wheel only glyphs around its spokes, no labels and no
list under it (her words, 7 Nov: *a simpler smaller wellness wheel that just has the glyphs around it … the time pie
chart and the wellness wheel right next to each other*); a glyph, tapped, lights its rows on the timeline. **Her time is hers**: a row titled for someone in her care (`care.family.people`,
*her son's sleep*) is their own row, never her sleep on the timeline or in the pie (`flow.theirs`).

**Her heart rate decides relaxing versus energizing** (8 Nov 2026, the heart-rate amendment of 8 Nov, her words: *the heart
rate thing is actually really helpful; I think that's how we decide what's relaxing versus energizing*). Every `build`
reads the day's Oura heart rate (`scripts/day_heart.py`, through the environment's Oura credential) and, for each
stretch of play she lived, takes the median over its minutes: at or under `hr_calm_max` (settings, default 80 bpm) it
is relaxation, over it recreation and adventure, whatever feeling the row carries. The card's sheet shows ♥ bpm. Her
son's own play is his and keeps its kind; travel stays adventure; with no heart rate here, play keeps its feeling's kind.
**Screens on the running bars** (8 Nov 2026, her words: *I really want to show when I was on a device, or at least how
long and what device … additively on those bars … if I've got the screen open, I'm looking at it, I'm interacting with
it, I really want that to show up*). Each bar carries a hatched strip for its minutes on a screen, by device, from each
row's device field (`fields.stream.device`; 🚫 none and a journal don't count), with the devices named under the kind.
A last line, *on a screen*, adds the day's screen time by device, each device once a minute, beside her measured phone
time from that day's 📱 screen time row.
A row whose time is ESTIMATED FROM CONTEXT is drawn with a dashed edge (8 Nov 2026), so a guessed time reads as one.
A `photos-YYYY-MM-DD` folder placed by hand (no Drive key) still goes on the page.

**The day's highlights, and the day collapsed to them** (11 Nov 2026, her words: when the my day is done, when I'm
looking behind, I really want the timeline to collapse down to those few things that were the really relevant things
about that day … progressive summarization … but I want to be able to expand it out and see all the little minutia; and
later: when I'm proud or when I've accomplished something or when I'm having a strong feeling or a meaningful moment, or
there's a glimmer … three to twelve, max 12). On a day that's over, a card under her intention lists the day in three to
twelve lines, one each, led by its emoji, in the order they happened. Meaning first: her ⭐ highlight, anyone's 🌟
highlight, a glimmer or milestone, gratitude, an insight or a journal, the words she was proud, moved or upset in, a
feeling she named; then what she finished (more with a deliverable), a keeper photo, her own events; time spent counts a
little; the routine, sleep and the system's own work never; at most four of one kind of time (`sixOf` in the engine).
A tap on a line drops to its card on the timeline. The timeline opens on those lines alone, the hours between them
folded to a sliver, and *show the whole day* expands it to every row; a day still going folds only the routine, as
before. These are the day's progressive summary, the candidates for the week's own.

**A highlight lands when it happened, not when it was told** (11 Nov 2026, her words: the highlights should get tagged
like when they actually happened in the day, not necessarily when I specified what they were at the end of the day). A
⭐ or 🌟 row told at night is matched to the earlier card it names by its rarest words (a name on half the day's cards
says little; the place says where). Her ⭐ stars that card and carries its words; one about being told (*telling me
about his day at school*) stars the first family card with that person after the event instead. Anyone else's 🌟 moves to
that moment (a meal it names lands at the meal, inside the event) and keeps the hour it was told. No strong match, and
the row stays where it was (`star_the_highlight` in flow.py).

**Long work behind, breaks across it** (11 Nov 2026, her words: when I was eating dinner you can bet that I wasn't
actively working, so that bar should extend all the way across … if there's a continuous work session, show it, but then
show the breaks kind of overlapping it). A running effort of three hours or more is drawn behind at full width (two at
once share it), and what she did meanwhile — the meal, the photo, the sunset — is drawn across it on top.

**Every card leads to its drive and its rhythm** (11 Nov 2026, her words: I want each of those cards to link to the drive
that they were part of, to the rhythm they were part of … all linked up so that it's all coherent): a card's sheet carries
its drive and the rhythm above it; a tap goes to that node in *How things flow* and opens its steps.

**Her settings row wins** (11 Nov 2026): `prep` reads `day_ahead_local` from the `be•do system › settings` row first,
whatever `LB_LOCAL` says; `LB_LOCAL` and the skill's own file are only the fallback when Airtable can't be read. A run
that pointed `LB_LOCAL` at the installed file skipped the row and built a whole day without its wellness, device, photo
and calendar settings, all of which the row had.

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

**Saturday's my day page** (7 Nov 2026, her words: *take the time slot things off of my calendar for today because
those aren't — it's not work. Those are just tasks. And then just show the calendar shortened if it's empty … and I
really want you to try harder to pull up all the things that I might want to do on Saturday*):

- **No step on the clock** on a Saturday or a Sunday: only her calendar and what she has lived sit on the timeline.
  Open steps go to *tasks, if you want them*, a folded list under it (`flow.off_the_clock`).
- **An empty stretch ahead folds** to one short band, *open · 2:15–9 PM*, never hours of empty grid; on a weekend
  the clock runs to the evening's end so a wide-open afternoon shows as open. Any day: a gap of two hours or more
  after now.
- **for a Saturday** leads the page, under her intention: `scripts/saturday.py` gathers every open row under the fun
  rhythms (`saturday_fun` in the settings, else every rhythm whose name says adventure, connection or stories; the
  `tending` rhythms and rows with no rhythm only when the words are fun, never a chore) and the drives under them; the
  trails and parks of the last two weeks (*with the dogs* when they came); the stories queue by the Morning Gate's
  Off the clock moods (with her kid — `child_calendar` — learn something, on your own, for a drive or a walk, to read); and the places
  table's `want to go` rows. One place said several ways is one card. Groups, easy first: easy at home, off the
  clock, out for a bit, coming up (the one date an idea has, said in words — *tomorrow 2:00 PM · a maybe*), people,
  a day out, fun to plan, and farther off (folded; `saturday_far` adds words that mean far). Each carries its way
  in — her link, a map for a place, the calendar event — and no time.
- **Three to start, then folded moods** (7 Nov 2026, her words: *it's overwhelming the way it is … your top three
  suggestions … an expandable list: do you want to watch a movie? read a book? an urban adventure or an outdoor
  adventure? grouping the things according to energy and distance and practicality*). The list opens on three — one
  dated today, one easy at home, one outside, else the next nearest, never one dated or named for another day (her
  words, 7 Nov: *the Spirits of Erath County walk should not be showing up on my Saturday my day*) — and every other idea sits folded under
  its mood, from the least energy and the closest out: watch something, read or listen, something fun at home, call or
  see someone, an urban adventure, an outdoor adventure, coming up, a day out, fun to plan, farther off; *if you feel
  like it* folds last. The grouping is the engine's (`sat()`); `saturday.py` still gathers.
  **Stories and media live on her Morning Gate** (her words, 7 Nov: *I'd prefer to see all of the stories / media stuff
  on my morning gate and just link to it*): with `media_gate` in the settings (the gate's link), watch and read become
  one link to it; without it, each story leads with its kind's glyph (🎥 📺 📗 🎧).
- **if you feel like it** closes the Saturday list (her words: *I know I have more actions that are priority that
  are out there, but I forget them*): at most three open actions with the most pull (`saturday.feel`): someone
  waiting on her, a date within four days (or one day past), money. One per drive. Never a row she is blocked on (its
  waiting field), an event's own row, a quickie, build work, or anything already on the fun list. No time on them.
- A row from any drive that is not work (`work_parents`) joins the fun list when its words are plainly fun (art, a
  game, a trail, a museum).
- The stories and places are read by the fetch **on a Saturday only** (`ideas_stories.json`, `ideas_places.json`,
  found by base and table name), so the week's API allowance is not spent on them.

The settings keys (`tending`, `sunday_morning`, `sunday_morning_until`,
`saturday_lead`) are optional and live in the `day_ahead_local` settings row,
so changing one is an edit to that row, not an upload. Without `tending`,
Saturday draws no tending section.
