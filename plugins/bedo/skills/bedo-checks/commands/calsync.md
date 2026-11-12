# `calsync`

**When:** the dusk close, once the day's rows are written

**Command:** `calsync YYYY-MM-DD`, then again with `--events events.json --calendars calendars.json`

**The calendar mirrors the stream** (kept, her yes 11 Nov 2026; the step used to live in the retired day behind, so it was being skipped): each event a row is tied to takes the row's status as its title prefix (⬜ → ✔️ or ✖️: the plain check, never the green one) and, when the row holds a real span, its real times. The first run lists the linked events: fetch each fresh with `get_event` (its `calendar_id` and `event_id` are in the list), save them to `events.json` with the calendar id added to each as `calendarId`, and save `list_calendars` to `calendars.json`; an event not found on its own calendar may already be on her dropped calendar, so fetch it there. The second run prints the plan: make each change in `changes` with `update_event`, passing exactly its `update` object (`notificationLevel` is always `NONE`) and nothing else, and say what moved in one line. `to_move` names dropped rows whose event is still on a synced calendar: give her those in one line, with their links, to move herself (the connector can't move an event between calendars; never copy-and-delete). An empty list: say nothing
