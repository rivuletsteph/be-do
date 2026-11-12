# `calendar`

**When:** every calendar write — create or edit, before calling it done

**Command:** `calendar event.json` (the arguments as sent, plus the row's `drive`), then again with `--readback read.json --from CALENDAR_ID`

write only what prints `ok`: the calendar named (hers, her son's or the dropped one, never the tool default), every work event purple (colorId 3, on the series). Then read it back from that calendar and run it again: until the read-back prints `ok` it isn't done, and the reply says so (6 and 9 Oct 2026). Pass `--rhythms` so a drive under her work parents counts as work
