# Where the Airtable reads come from


- **With a token** — `AIRTABLE_PAT`, a `bedo_secrets.json` beside the work or
  in `~/.bedo`, or a Claude cloud session whose proxy attaches the credential —
  the checks read Airtable themselves. No rows pass through the chat.
- **Without one** (Cowork, a plain chat), the command says `NO TOKEN HERE` and
  exits 3. **That is expected, not a failure — it is not a reason to run the
  checks by hand.** Read through the Airtable connector, save each result to a
  file, and run the same command again with the files:
  - `preflight --bases names.json --stream recent.json` — `names.json` is
    `{"w41 be•do": "app…", …}` from searching the bases for `be•do`;
    `recent.json` is **five rows, newest first, the datetime field only** —
    preflight asks only how old the newest row is. Every row read here is a row
    the chat writes out again, so never read more. One connector call on the
    live weekly base's stream: `fieldIds` the stream's `datetime` field, `sort`
    that field `desc`, `filters` that field `<=` `{"mode": "today"}` in her time
    zone, `pageSize` 5. Save the result as it came; its total will be larger
    than five, and that is fine for this read only.
    Add `--look-behind log.json` so the `first` line can read yesterday: one
    more call on the live base's stream (and last week's on a Sunday), rows
    whose `details` contain `[be•do] day ahead ` or `dayqa shown `, the datetime
    on or after four days ago, fields `datetime`, `details`, `deliverable`,
    `practice` and `title` only. Rows of any other kind make a finished day
    look unfinished (8 Nov 2026). Without the file the line says not checked.
  - `remaining --catalog practices.tsv --day today.tsv` — it runs every
    reply, so write both in **the compact form** below, never the connector's
    JSON:
    - `practices.tsv`, **once per flow**, reused every reply after: one read
      of the catalog filtered to `active` checked and `phase` the open flow's
      (a filter takes the choice's id: one `get_table_schema` call for the
      `phase` field alone gives it), fields `practice`,
      `group`, `order`, `typical time`. Line one carries what every row
      shares, tab-separated: `total N`, `active=true`, `phase=🌅 dawn`.
    - `today.tsv`, fresh every reply: today's stream rows (`datetime` `=`
      `{"mode": "today"}` in her time zone), fields `datetime` and `practice`
      only — never status, never details. The one exception is the 🌦️ weather
      check row: once it exists, read its `details` once (by its record id)
      and carry its sunrise into that row's `details` cell in every
      `today.tsv` after — the sunrise orders the steps that wait for the sun.
  - `dusk --day dusk_day.tsv --catalog practices.tsv`, once, before the dusk
    close — also the compact form. `practices.tsv` is the dusk one above.
    `dusk_day.tsv` is today's rows with these columns: `datetime`, `end`,
    `time_spent`, `status`, `practice`, `title`, `attention`, `target`, then
    `person`, `rhythm`, `waiting_on`, `queue`, `calendar_event` written as
    `✓` when the row has one and blank when not — the audit asks only whether
    they are there — then `details`, holding **only** the `for my day:` line
    when the row's details carry one, blank otherwise. Add a `chat` column (the
    row's chat link) only when passing `--chats`.

  **The compact form** (`.tsv`, tabs between cells): line one `total N` with
  the connector's own `totalRecordCount`, then any `name=value` every row
  shares; line two the columns by their logical names (`typical_time`, not
  `typical time`); then one record per line, the cells copied as they came —
  a select's `name` only. A blank cell is left blank.

  ```
  total 2
  datetime	practice	details
  2026-10-05T11:32:00.000Z	😶 wake
  2026-10-05T14:25:00.000Z	🌦️ weather check	sunrise 7:27 am
  ```

  Every other file is the connector's result as it came — `{"records": [...],
  "metadata": {"totalRecordCount": n}}`, or the saved `[{"text": "…"}]` wrapper.
  **Every other read must be complete:** if the result has no total, page until there is
  no offset and write the total yourself. A short read stops the check (I11),
  and that is the point. A file holding more than the day is fine; the checks
  keep only the day's rows.
