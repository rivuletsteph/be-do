---
name: bedo-checks
description: Run be•do's checks as code instead of from memory — preflight at the start of every be•do chat, the remaining list while a flow is open, the entry check before any stream write, the dusk audit before the dusk close, and stretches for a session's time.
---

# bedo-checks

Five checks that used to depend on a chat remembering. Each is code in
`plugins/bedo/core`, tested, and run through `run_checks.sh`. **Run them; never
compose their output by hand when the runner can run.** By hand is the fallback
only where nothing can execute, and then copy the same shape.

| when | command | what the chat does with it |
|---|---|---|
| the first reply of every be•do chat | `preflight` | line one is the chat's title — put it alone, first, in a code box. Then the clock and the base. A `STOP` means no read or write until the base is right |
| every reply while a flow is open | `remaining --widget` | hand the HTML to the widget tool exactly as printed — her pill strip (A237). Where a widget can't render, `remaining` prints the block and the one line; `--voice` gives one spoken line |
| before any stream write | `entry row.json` | write only rows that print `ok`; fix every `FIX` first |
| before the dusk close row | `dusk` | do the fixes it names; ask her only what is hers, as one list; the flag line goes after the close |
| the dusk close, and the look behind | `meals --json` | every meal's prep and eating placed from context (her rules, amendment `recjqbbyTntq6zP3p`): write the proposed rows ESTIMATED FROM CONTEXT through `entry`, then show her the printed list as what went in the record and ask if it's accurate. Never ask her to fill the times in |
| a session entry | `stretches FILE` | the time spent is the sum it prints, and the stretches are named in the `[be•do]` block |
| the weekly close | `order --json` | her predicted order: each flow practice's typical time from the last weeks of her rows (dawn as minutes after waking, dusk as clock time). Write the printed updates to the catalog's `typical time` field with the connector |

## Running it

```
bash run_checks.sh preflight                 # my day; --part B when the day already has a chat
bash run_checks.sh preflight --kind week --week 40
bash run_checks.sh remaining --widget        # the open flow as her pill strip; --flow dawn|dusk to name one
bash run_checks.sh dusk                      # today; --date YYYY-MM-DD for another day
bash run_checks.sh meals                     # the day's meals: prep and eating, placed from context
bash run_checks.sh entry row.json --base "w41 be•do"
bash run_checks.sh stretches transcript.jsonl
```

`preflight` downloads the core fresh from the version store; the other
commands reuse that copy for the session. Her settings (`facts_local.json`:
base and field ids, the time zone) come from the loader's assets and never from
the repo.

**A row for `entry`** uses the logical names: `datetime`, `end`, `time_spent`,
`status`, `practice`, `title`, `key`, `details`, `phase`, `wellness`,
`emotion` (a list), `attention`, `device`, `rhythm`. One row, or a list.

## Where the Airtable reads come from

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

## What a Cowork chat can't do

It can read the repo — it's public — but it can't write to it; only a session
on the laptop holds the GitHub login. So **a build idea heard in Cowork goes to
the Drive inbox** `be•do/code/backlog-inbox.md` (one line, her words, the date),
never as a stream row. The next be•do work session on the laptop moves it into
`docs/backlog.md` and empties the inbox.

## If the download fails

Only a failed download — never `NO TOKEN HERE` — is a reason for this. Say so
plainly in one line and run the checks by hand from the same rules —
never from an older copy of the code.
