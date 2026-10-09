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

**Not built yet** (from the full page spec): the week's word and the reading,
balance and the wheel, the river, the body, highlights, the quest grid, the
queues, who was there, what had a date and didn't happen, what you got stuck on.
Add them one at a time, only when she misses one.

## Settings

The day behind's `look_behind_local.json` — same field ids, offset and week
anchor. It needs `fields.rhythms.feeds` for the nesting; without it every drive
is a root.

## Steps

1. Read the week's bases, live first (I15), with the day behind's fetcher —
   once with `--day` set to a day of the week (that base and the one before)
   and, when the week is past, once more for the live base:
   `python3 plugins/bedo/skills/bedo-look-behind/scripts/bedo_fetch.py --day <Saturday> --local look_behind_local.json --out reads`
2. Build:
   `python3 plugins/bedo/skills/bedo-week-look-behind/scripts/week_look_behind.py --week <Sunday> --local look_behind_local.json --stream <live>.json --stream w##.json --stream w##-1.json --rhythms rhythms.json --template plugins/bedo/skills/bedo-week-look-behind/assets/week_look_behind_engine.html --out week.html`
3. The builder prints the drive outline, the totals and its QA (`over_span`:
   rows over 12 h, left out of the minutes; `feeds_loops`). Name anything in QA
   in one line.

Test: `python3 plugins/bedo/skills/bedo-week-look-behind/tests/test_week.py`.
