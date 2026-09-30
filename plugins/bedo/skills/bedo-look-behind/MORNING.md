# The morning routine — finishing yesterday's look behind

A Claude Code cloud routine, due at **03:00 in the user's time zone**, that
finishes yesterday's look behind by itself: re-reads the rows, takes the words
the dusk chat left in the stream, builds the **final**, publishes, saves. It
reads this file from the version store at the start of every run and follows
it; nothing personal is in it — every specific comes from
`look_behind_local.json`, which the routine's environment carries with the
installed skill.

**It builds yesterday, never today**: the user's local date at the moment it
fires, minus one. The first line of anything it writes states the date built.

## The routine itself

- **Where**: the user's Default cloud environment — the one carrying the
  read-only Airtable token as an API credential for `api.airtable.com` and the
  synced skills with the settings file. A fresh session on every firing.
- **When**: `CRON_TZ=<time_zone> 0 3 * * *`, the zone from the settings file.
  Written in the zone, so the clock change on 1 Nov 2026 does not move it.
  (`utc_offset_hours` in the settings file still has to change that day; the
  builder refuses to build when it disagrees with `time_zone`.)
- **What it can reach**: `git` for the version store; Airtable, read only,
  through the credential; the Artifact tool to publish. **The connectors —
  Airtable for the row, Calendar, Drive — only if the routine was created from
  the claude.ai routines page with them attached.** A routine created from
  inside a session carries none (29 Sep 2026). Without them it builds and
  publishes, and leaves the row, the Drive copy and the calendar to the next
  chat, saying so.
- **What the dry run found (29 Sep 2026)**: a session fired by a routine has
  no repository checked out (it clones), Python 3.11, the Artifact tool, the
  synced skills and the settings file, and the credential on
  `api.airtable.com`; it has none of the claude-code-remote tools (no
  `get_session`, no `send_later`), its `SendMessage` reaches no other session,
  and it ran on Sonnet. So its only reliable channels out are the page it
  publishes and the row it writes.
- **Model**: any. Judgment is needed only when there is no dusk row and the
  words must be drafted.

## What it may do — the user's word, 29 Sep 2026

| step | allowed? |
|---|---|
| publish the final to the living page | *asked — pending* |
| update the look behind's log row (status, link, the words block) | *asked — pending; yes is what makes the row the channel* |
| sync the calendar from the stream | *asked — pending* |
| a day with no ⏏️ secure base row | build `secure`, the assumed default since 29 Sep, and say the row was absent |

Until an answer is in, the routine does everything up to that step and stops
before it, saying so in its own account. Change this table when she answers;
it is the only place the routine looks.

## Steps

0. **The date.** `TZ=<time_zone> date +%F` is today; yesterday is today minus
   one. Say *building YYYY-MM-DD* before anything else.
1. **A working folder and the settings.** Any folder (`LB_DIR`), the runner
   fetched fresh from the version store, the settings found by the runner
   itself in the synced skill (`LB_LOCAL` if not):
   ```
   git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main
   cp be-do-main/plugins/bedo/skills/bedo-look-behind/run_look_behind.sh .
   export LB_DIR=$PWD LB_OUT=$PWD/out
   ```
2. **Prep yesterday.** `bash run_look_behind.sh prep <yesterday>` — Airtable
   read directly, the credential attached by the proxy, no token in the
   session. **If it aborts with *no base named "w## be•do"*, the week has
   turned and the new base is not cloned yet** (the Sunday close does that):
   say so and stop. Never fall back to the old week's base.
3. **Which days.**
   ```
   python3 scripts/look_behind_log.py --today <today> --local look_behind_local.json \
     --stream data/w##.json [--stream data/w##-prev.json] --cap 3
   ```
   `to_build` lists the days with no final yet, oldest first, at most three
   back. Empty: nothing to do, say so, stop. Several: each in order, so the
   most recent day is built last and is the one left on the living page. A day
   marked `unreachable` (its week was not fetched) is named and not built; a
   run that finds three days missing says so plainly — a week of missed pages
   is a sign to ask, not to catch up unattended.
4. **For each day, in order:**
   1. **The words, from the dusk row.**
      ```
      bash run_look_behind.sh words <day> --from-stream data/w##.json [--from-stream data/w##-prev.json] \
        --local look_behind_local.json
      ```
      It finds the row by the first line of its `[be•do]` block and prints
      which parts are still be•do's. **NO ROW**: draft the words yourself from
      the digest (`prep` printed it; `scripts/day_digest.py` prints it again),
      by the rules in `SKILL.md`, and write them with `--new --draft`. **Too
      little on the day** — no rows, or only the flow's own steps — do not
      build; log why, and go to the next day.
   2. **Secure base**: the day's ⏏️ row in the digest, or `secure` when there
      is none (the table above).
   3. **Build**: `bash run_look_behind.sh build <day> <state>`. Read what it
      printed. An abort is the end of that day, named, not worked around.
   4. **Publish** (if allowed): the Artifact tool, `url` = `artifact_url` from
      the settings, the same file path every day.
   5. **Save to Drive** (if a Drive tool exists): the week's folder by name,
      created by the same rule if missing and said so; never over a page
      already there without saying what it replaced.
   6. **The log row** (if allowed and an Airtable write tool exists): the row
      `--from-stream` named, updated in place — status ◉ done, deliverable the
      page URL, and the details' `[be•do]` block replaced by
      `bash run_look_behind.sh words <day> --row-block --final`, the user's
      words above the divider carried forward verbatim. No dusk row: write one,
      dusk, dated on the day it stands for, **in the base whose week contains
      that datetime** (amendment `[id]`) — a Monday routine
      writing Sunday's row across a week boundary is the case that rule is for.
   7. **Sync the calendar** (if allowed): `SKILL.md` step 8.
5. **Its own account**, one line per day built: the date, draft or final
   words, what was published and saved, and what it could not do and why.

## What it never does

- Build today. Build from a partial read. Fall back to last week's base.
- Invent a lead or a story from the section totals, or rewrite words the user
  touched.
- Print a token: it never holds one.
- Publish a page that failed to build, or a day with too little on it.
