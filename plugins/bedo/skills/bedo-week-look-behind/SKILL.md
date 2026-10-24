---
name: "bedo-week-look-behind"
description: "Build the be•do WEEK look behind — Sunday to Saturday, by drive: time, what closed, what is still open, drives nested through feeds. Use when the user asks for the week look behind or the weekly review page."
---

# The week look behind — first cut: by drive

One week, Sunday 00:00 to the next Sunday 00:00, local. Per drive: the minutes
logged on it, the actions it closed (✅, one line per action, never its rows),
and what was still open (⬜ ▶️ ▫️) as the week ended.

**Drives within drives.** A row counts under its own drive and every drive it
feeds (the rhythms field `feeds`), the child nested under its parent. The three
numbers at the top count each row once. A loop in `feeds` is named in the
footer; fix it in the base. The rule is `plugins/bedo/core/bedo_drives.py`, the
same one the day behind and the day ahead use.

**What gave the week meaning — the stream, first on the page** (19 Oct 2026, her
words: what the thing was, a picture, a few words, an emoji for the kind, and how
it fits; the look and the rhythm → drive → destination thread are The Whole Map
Ahead's). The days flow top to bottom, each under its own look-behind lead when
one was written. A stone is a moment she marked (highlight, glimmer, gratitude,
insight, a milestone, someone's own highlight, a synergy note; milestone added 20 Oct 2026, a journal entry tried and taken back 22 Oct: a note on the work is not a moment) or something she did and wrote
about at length (`garden.long_words`). Each stone is its emoji (the practice's,
or for a log or a mark what its title names, `garden.kind_words`, the mark kept
as a badge), its title, her words, who, a memory (↺), synergy (∞), a photo when
the row was read from one, and where it flowed: the envelope it sat in (a row
over 12 hours on a drive, like the trip), its drive and the destinations. The
rest of each day is one line of what it was. The numbers (time, rest, needs,
drives) fold below. The garden's data is still built but no longer drawn.

Above the stream, the river runs on time, Sunday to Saturday. Its top strip is the
being side (20 Oct 2026, her words: the flows are practices, fundamentally different
from drives): one row per flow, one ring per day, sized by how many of its practices
were done, full when the flow was closed, dashed when left open (`stream.be`). Below
it the doing side: a lane per rhythm or drive, each moment an emoji at its time,
leading on to its destinations. A moment caught in a flow lives on the rhythm or
drive it was about, with a small flow-coloured dot; only one with no other home
sits on the flow's row. Tapping a flow, lane or destination filters the stream.

**What mattered — the garden (data only now)** (her words, 19 Oct 2026: show
and reflect meaning, the layers of a day). Each moment she marked as mattering
(a highlight, a glimmer, a gratitude, an insight, and a child's or partner's own
`'s highlight`) is one flower. Its petals are the areas the moment touched, in
the day behind's wheel colours: the row's own area, heart when it was shared,
and whatever her words name (`garden.words` in `core/facts.json`). A dashed ring
is a memory it carries ("five years ago"), a glow is a moment made more by
sharing it (her synergy rule), and her highlight and theirs at the same minute
are one flower, marked as theirs too. The flower with the most layers is drawn
large. Time and meaning are kept apart: the garden never counts minutes.

**Four readings of the same rows** (her build notes, Sun 18 Oct 2026), above the
drives:

- **Where the time went** — first, how much of the waking week any row covers
  at all, per day, so a thin record reads as thin. Then minutes from rows with a
  real span, by the eight areas: being, doing (tending and growing, by the
  drive's type) and time with people. Two rows at once both count, as on the
  wheel, and **time with somebody counts toward heart whatever else it was**
  (her amendment, 19 Oct 2026): it feeds the heart bar and
  belonging, never the being total. Sleep is in bed, never an area.
- **What moved forward** — every ✅ closed in the week, on a drive or not, and
  every ▶️ head whose chain had a row in it.
- **Rest as a reset** — nights in bed (a night is the morning's day; somebody
  else's sleep row is theirs), play minutes (the pie's play practices), and the
  morning readiness, sleep and activity scores read from the 🪐 morning oura
  row's words.
  Rest is shown as part of the week's work, not time away from it.
- **Needs, on the secure base** — Maslow's deficiency needs against his growth
  needs, by the wellness pairs: body and earth, heart and water are deficiency;
  mind and air, spirit and fire are growth (`needs` in `core/facts.json`; a
  `needs` key in the settings overrides it). Day by day beside the secure base:
  a day with no ⏏️ row is secure, the default, and is starred as assumed; any
  other ⏏️ title is the other state, in her words.

**By drive** shows only the drives that moved (time or a ✅); the drives holding
open items alone fold into one line. **A row moved between bases** names its
original (`moved from w## (recID)`), and the original is skipped.

**QA the week first.** The page reads what was logged, so every day gets its
dayqa before the build (the same amendment): sleep from the Oura rows, meals,
the stretches between rows, wellness on every row.

**Not built yet** (from the full page spec): the week's word and the reading,
the wheel, the river, highlights, the quest grid, the queues, who was there,
what had a date and didn't happen, what you got stuck on. Add them one at a
time, only when she misses one.

**Where it lands**: one living week page, republished in place each week (first
published at the W42 close, 19 Oct 2026). Its link is personal and is kept with
her settings and the week's handoff, not here.

## Run it

```
bash plugins/bedo/skills/bedo-week-look-behind/run_week_look_behind.sh [any day of the week]
```

With no day, it builds the week just closed. It fetches the builder fresh, the
settings from Airtable (`be•do system › settings`, the day behind's
`look_behind_local` row; the installed day behind's copy when Airtable can't be
read), the live week and the asked week's bases, and writes
`<Saturday>-week-behind.html`. It prints the drive outline, the totals and its
QA (`over_span`: rows over 12 h, left out of the minutes; `feeds_loops`). Name
anything in QA in one line, then publish the page the way the day behind does.

**One day, drawn the same way** (20 Oct 2026, her ask: Monday's day behind
from the updated week page). `week_look_behind.py --day YYYY-MM-DD --words
words-YYYY-MM-DD.json` (the day behind's words file, refused if written for
another day) builds the page for that day alone: its lead and story on top,
its moments as stones, the numbers folded below, titled The Day Behind. The
night that ended that morning counts whole, in day and week alike. It is a
trial beside the canon day behind, published to its own page, not the living
one.

**Photos** (22 Oct 2026, her word: photos that piece the day together).
`scripts/day_photos.py --day D --local … --out photos/` reads the week's
`W## photos` Drive folder with a service account the folder is shared with (its
JSON key in `BEDO_DRIVE_SA`, or a path in `BEDO_DRIVE_SA_FILE`), keeps the photos
taken that day by the phone's own file name (`PXL_YYYYMMDD_HHMMSS…`, UTC), and
writes each at 900 px. No key prints `NO DRIVE KEY HERE` and exits 3; the page
builds without photos. `--from DIR` reads originals from a folder instead.
`week_look_behind.py --photos photos/` places each by its time: on the row taken
at that minute or spanning it, preferring a row read from a photo, then a moment.
Inside its moment when it has one, else in the day's pictures under the story; a
photo for a routine check (`photo_skip_practices` in `core/facts.json`) is left
out. The Drive connector is not the way: every photo would pass through the chat.

Test: `python3 plugins/bedo/skills/bedo-week-look-behind/tests/test_week.py`.
