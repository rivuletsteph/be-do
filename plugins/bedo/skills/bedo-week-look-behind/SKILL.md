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
