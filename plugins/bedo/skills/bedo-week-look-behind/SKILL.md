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

Test: `python3 plugins/bedo/skills/bedo-week-look-behind/tests/test_week.py`.
