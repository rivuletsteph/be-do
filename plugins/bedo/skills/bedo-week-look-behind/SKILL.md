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
night that ended that morning counts whole, in day and week alike. Since 25 Oct
2026 it is the day behind: the day skill's `run_look_behind.sh build` runs it and
publishes to the living page. It carries `day`, `title` (the lead) and `draft`
in its data, so the day skill's `words … --to-page` edits it in place.

**How the day went** (24 Oct 2026, settled with her on Fri 23 Oct; every
decision and her words are in `docs/day-behind-cards.md`). On a single day the
page opens, after the lead and story, with the waking day as a rainbow:
`scripts/day_rings.py` reads the day's rows and the engine draws them.
- The rainbow is the 16 hours from getting up, bent back like an open book;
  the gap at the bottom is the 8 hours of a night, filled blue for the hours in
  bed the night before (dashed where short, a deeper rim where over).
- From the inside out: a thin neutral band for the dawn and dusk flows (their
  span and a line per step); **being** in cool hues (eating and drinking,
  moving, recreation); **doing** in warm hues (professional work, caretaking of
  others and of herself, cooking, be•do); a thin line for time on a screen.
  Bands overlap: one stretch can be two things.
- Doing makes or moves something; being is when the moment itself is the
  point. Work is what she did, not what the laptop did: a session's minutes
  count only while she wasn't driving, eating, moving or asleep. A meal is not
  moving. Food is all nutrition, drinks too.
- The moments that mattered sit outside at their own times. Tapping any piece
  names the rows inside it.
- Under the rainbow, the totals as bars on one scale, each in its part's
  colour: in bed the night before; being (flow steps, eating, moving,
  recreation); doing (work, caretaking, cooking, be•do); on a screen. A goal is
  a mark on its bar.
- Settings (`look_behind_local`): `care` — `{"rhythms": [...], "people": [...]}`,
  the rhythms and people whose rows are caretaking (name parts);
  `system_rhythm`, the drive that is be•do itself; and `day_goals`, minutes a
  day by part (`{"inbed": 480, "move": 120}`; the night is measured against
  `inbed`). All three were added to the live row on 24 Oct 2026. `recreation` —
  `{"rhythms": [...]}`, rhythms whose lived rows with a span are recreation too,
  whatever else they were (added 25 Oct 2026: her adventure rhythm).
- A flow step placed at the moment's own time (a ⭐ highlight told later) does
  not stretch its flow's span.
Test: `tests/test_day_rings.py`.

**The map card — groundwork only** (D6.68, 25 Oct 2026). `scripts/day_places.py`
finds the day's stops from what the stream already holds — a 📍 location row; a
Timeline stop named in a row's details (only on a line that cites Timeline or on
a 🚗, 📍 or 🗺️ row, so calendar times and estimates are never places); the time
between two 🚗 drives — and matches each to the places catalog (`places.json`,
read by `bedo_fetch.py` by name). `--places` puts it in the day page's data as
`places`; **the engine does not draw it yet.** A first pass drew it as a route
with what happened at each stop and was turned down: routes are out, and the
card is only where, never what (the rainbow's job). The card to build is the
meaningful-geography map in `docs/day-behind-cards.md`.
Test: `tests/test_day_places.py`.

**Photos** (22 Oct 2026, her word: photos that piece the day together).
`scripts/day_photos.py --day D --local … --out photos/` reads the week's
`W## photos` Drive folder with a service account the folder is shared with (its
JSON key in `BEDO_DRIVE_SA`, or a path in `BEDO_DRIVE_SA_FILE`), keeps the photos
taken that day by the phone's own file name (`PXL_YYYYMMDD_HHMMSS…`, UTC), and
writes each at 900 px. No key prints `NO DRIVE KEY HERE` and exits 3; the page
builds without photos. `--from DIR` reads originals from a folder instead.
`week_look_behind.py --photos photos/` places each (`core/bedo_photos`, 25 Oct
2026): on the row whose `photo_links` name its file (the dusk match), else on
the row taken at that minute or spanning it, preferring a row read from a photo,
then a moment. Inside its moment when it has one, else in the day's pictures
under the story, keepers first. A photo whose row is info — the stream's `photo`
field, or by rule for an older row: food on its own, a pill, a screen of scores
(`photos` in `core/facts.json`) — is left out; a moment shows 📷 when one of its
rows holds a keeper. `run_week_look_behind.sh` fetches the seven days into
`photos/` when a key is here. The Drive connector is not the way: every photo
would pass through the chat.

Test: `python3 plugins/bedo/skills/bedo-week-look-behind/tests/test_week.py`.
