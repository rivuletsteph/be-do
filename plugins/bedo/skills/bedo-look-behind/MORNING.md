# The morning routine — building yesterday's look behind

A Claude Code cloud routine, due at **03:00 in the user's time zone**, that
builds yesterday's look behind by itself, so it is already on the living page
when the morning chat opens: reads the rows, takes the words the dusk chat left
in the stream if there are any and **drafts them itself if not**, builds,
publishes. It
reads this file from the version store at the start of every run and follows
it; nothing personal is in it — every specific comes from
`look_behind_local.json`, which the routine's environment carries with the
installed skill.

**It builds yesterday, never today**: the user's local date at the moment it
fires, minus one. The first line of anything it writes states the date built.
**Only yesterday**: an older day with no page is named in its account, not
built — the living page shows one day, and that day is yesterday.

**Who writes the words** (decided 8 Oct 2026, backlog 260924_2221b): the
routine. The builder refuses to build without a lead and a story, and at 03:00
nobody is there to write them, so the routine drafts them from the digest and
marks them as a draft (the 28 Sep amendment allows it). Dusk is not asked to
write them or to build anything: less time in the system at the end of the
day. If a dusk chat did leave words in a look behind row, the routine uses
them as they stand. The morning chat shows the draft and she edits or accepts
it there (`SKILL.md`, *Editing is one command*).

**Failures reach her phone, never the page.** The routine is created with push
notifications on. A run that cannot build publishes nothing — the page keeps
the last good day — and its final message opens with `FAILED <date>:` and the
one reason, which is what the notification carries.

## The routine as created (8 Oct 2026)

- `trig_01TVzvCv9aDCJ4FWvC4qr9y1`, created from a Claude Code session with `create_trigger`: a fresh session on
  every firing, `CRON_TZ=America/Chicago 0 3 * * *`, push notifications on, no
  connectors (none are needed to build and publish).
- Its prompt is short and points here: *read `MORNING.md` from the version
  store and follow it*. Change this file, not the routine, to change what it does.
- First run by hand on 8 Oct 2026 for 7 Oct: no dusk row (dusk didn't close),
  the words drafted and marked, built, published to the living page.

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
| publish to the living page | **yes** — her word, 8 Oct 2026 |
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
3. **Is yesterday already final?**
   ```
   python3 scripts/look_behind_log.py --today <today> --local look_behind_local.json \
     --stream data/w##.json [--stream data/w##-prev.json] --cap 3
   ```
   If yesterday is not in `to_build`, a final already exists: say so, stop.
   Any older day in `to_build` is named in the account, not built.
4. **Yesterday:**
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
   4. **Publish**: the Artifact tool, `url` = `artifact_url` from the
      settings. A fresh session has not viewed the live page, so the first
      publish is refused and hands back the live version: read it through, and
      publish again — the living page is replaced whole every day, so there is
      nothing on it to merge.
   5. **Save to Drive** (if a Drive tool exists): the week's folder by name,
      created by the same rule if missing and said so; never over a page
      already there without saying what it replaced.
   6. **The log row** (if allowed and an Airtable write tool exists): the row
      `--from-stream` named, updated in place — status ◉ done, deliverable the
      page URL, and the details' `[be•do]` block replaced by
      `bash run_look_behind.sh words <day> --row-block --final`, the user's
      words above the divider carried forward verbatim. No dusk row: write one,
      dusk, dated on the day it stands for, **in the base whose week contains
      that datetime** (an amendment) — a Monday routine
      writing Sunday's row across a week boundary is the case that rule is for.
   7. **Sync the calendar** (if allowed): `SKILL.md` step 8.
5. **Its own account**, the run's last message: one line — the date, draft or
   dusk words, published or not, the QA items the morning chat will meet, and
   what it could not do and why. On any failure the line opens `FAILED <date>:`.

## What it never does

- Build today. Build from a partial read. Fall back to last week's base.
- Invent a lead or a story from the section totals, or rewrite words the user
  touched.
- Print a token: it never holds one.
- Publish a page that failed to build, or a day with too little on it.
- Ask anything: nobody is there. A question is a `FAILED` line.
