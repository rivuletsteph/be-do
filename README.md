# be•do

be•do is a personal system for living one day at a time and keeping a record
that makes sense as a story. Each day runs as a small set of flows: a morning
flow, a day of work and life, an evening flow. Along the way it logs what
matters: moments, time with people, work sessions, sleep and food. The rest it
lets go.

This repository is its engine: the checks, the page builders and the skills
that a chat runs. It holds no one's life. That lives in the person's own
bases and settings.

## How it works

- **Airtable holds the record.** Every day's rows live in a weekly stream base,
  beside the catalog of practices, people, drives and the rest. The record is
  the source of truth; pages and summaries are built from it.
- **This repo is the engine.** A chat (usually a Claude Code cloud session)
  fetches the skills and checks fresh from `main` each time, so a stale copy
  never runs. A change here reaches the next chat with no upload.
- **The checks run as code, not from memory.** Anything a chat used to have to
  remember is a script in `plugins/bedo/core`, tested and run through
  `run_checks.sh`. What still needs judgment is one living file,
  `docs/v53-judgment.md`, read at the start of every chat.
- **Settings never live here.** Base and field ids, the time zone, names and
  everything else personal live in a private settings row in Airtable, read live
  on every run. A settings change is one edit to that row. The repo ships only
  blank examples (`*.example.json`).

## The checks

All run through `plugins/bedo/skills/bedo-checks/run_checks.sh <name>`; each
has its notes in `commands/<name>.md`.

| check | when | what it guards |
|---|---|---|
| `judgment` | first reply of every chat | the rules that need a model, printed fresh |
| `preflight` | first reply of every chat | the chat's title, the clock and the live base. Nothing is read or written until the base is right |
| `remaining` | every reply while a flow is open | what's left in the flow, as one line, so nothing is forgotten |
| `entry` | before any row is written | every row is whole, on the right day, and in the right shape |
| `dusk` · `dayqa` | the evening close | one pass over the day, then be•do's own calls and one short list to accept |
| `close` | the end of every chat | QA, then the session entry, then the rename. The chat is done when it prints `closed` |
| `chats` | evening close, weekly close, on call | the chat sweep: every open chat checked against its objective, finished ones archived |
| `outgoing` | before every push, PR, comment or branch | the privacy check (below) |

There are more for their own moments: `stretches` (a session's real time),
`meals`, `calendar` and `calsync`, `inbox`, `cleanup`, `drives`, `order`.

## The privacy check

This repo is public, and so is everything around it: pull request titles and
descriptions, comments, commit messages, authors and branch names.
`tools/privacy_check.py` reads the names in the person's own bases live, plus
any private terms they keep outside the repo, and refuses on any hit (printed
masked). It runs:

- on every push and pull request, in CI (`.github/workflows/privacy.yml`);
- before every push from a clone, through the pre-push hook (`.githooks/`);
- before every GitHub write in a Claude Code session, through a hook in
  `.claude/settings.json`;
- by hand, as `outgoing --title "…" --text pr.md`, before a PR is opened or
  its text changed.

The hooks are the backstop. Running `outgoing` first is the step.

## The skills

Each lives in `plugins/bedo/skills/<name>/SKILL.md` with its own procedure.

- **`bedo-checks`**: the checks above, and how to run them anywhere.
- **`bedo-day-ahead`**: the my day page, drafted in the morning and finished as the day is lived.
- **`bedo-week-ahead`**: the my week page, the same idea across a whole week.
- **`bedo-weekly-close`**: the Sunday close and Monday plan: backup, split, chat sweep, drive cleanup.
- **`bedo-ahead-review`**: the monthly review of older intentions, one card at a time.
- **`session-entry`**: one work-log row for a session, with its objective and whether it was met.
- **`chat-sweep`**: the chat sweep on its own, any day.
- **the sleep tracker skill**: sleep, readiness and activity from a sleep tracker into the record.
- **`bedo-meal-plan`**: a stretch of meals, its shopping list and the order.
- **`morning-news`**: a one-reader morning paper from the topics and places in the settings.
- **`stories-queue`**: the weekly page of things to read, watch and listen to.
- **`grant-watch`**: the weekly watch on federal grant deadlines and new funding opportunities.

Retired, kept for a later look, and built only when asked for by name:

- **`bedo-look-behind`**: the day behind page. *Retired 8 Nov 2026.*
- **`bedo-week-look-behind`**: the week behind page, by drive. *Retired 8 Nov 2026.*

## Working on it

- All tests, one command: `PYTHONUTF8=1 python tools/run_tests.py`. CI runs
  them on Linux and Windows.
- Build ideas live in `docs/backlog.md`, added by pull request.
- `docs/reference.md` has the detail: where the Airtable token comes from,
  how the clock handles the time change, how settings are read from Airtable,
  what the less obvious settings keys mean, and how the retired builders work.
- `docs/v53-crosswalk.md` places every older rule in code, settings or the
  judgment file.
