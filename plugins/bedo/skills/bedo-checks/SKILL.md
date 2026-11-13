---
name: bedo-checks
description: Run be•do's checks as code instead of from memory — preflight at the start of every be•do chat, the remaining list while a flow is open, the entry check before any stream write, the dusk audit before the dusk close, and stretches for a session's time.
---

# bedo-checks

The checks that used to depend on a chat remembering. Each is code in
`plugins/bedo/core`, tested, and run through `run_checks.sh`. **Run them; never
compose their output by hand when the runner can run.** By hand is the fallback
only where nothing can execute, and then copy the same shape.

**This file is the short one, read at every chat's start.** Each command's own
notes (what to pass it, what to do with what it prints, her words behind it)
are in `commands/<name>.md`. **Before a command's first run in a chat, read its
notes: `bash run_checks.sh how <name>`.** The runner prints that line each time
it runs one, so nothing has to be remembered.

## Every chat

| when | command | what the chat does with it |
|---|---|---|
| the first reply of every be•do chat, before anything else | `judgment` | prints `docs/v53-judgment.md` fresh from the version store. It IS the project's instructions; the project holds only a short pointer to this command, so nobody pastes the long file on a phone. Read every line and follow it for the whole chat. If the download fails, say so in one line and work from the skills |
| the first reply of every be•do chat | `preflight` | line one is the chat's title — put it alone, first, in a code box, and save it as the chat's name in the same reply (`set_session_title` on this session, from `get_session`; where no tool can rename the chat, she renames it). Then the clock and the base. A `STOP` means no read or write until the base is right. The `first` line names yesterday's my day page: final and QA'd, with its link, or what is still missing, then offer to finish it. **The day behind is retired** (8 Nov 2026, her word: I'm just doing my day), so never offer one, and when `first` says *not checked*, say nothing about whether yesterday is finished |
| every reply while a flow is open | `remaining` | end the reply with the code box exactly as printed: one horizontal line — flow glyph, n of N, the remaining practices in order separated by ·, then `also:` and the other glyphs. **Never a widget** (her words 7, 8, 11 and 20 Oct 2026: printed horizontally in code, no widget that needs to drop and go away). While 🔅 morning sun is still to come it carries its sun-by time (an hour after sunrise or waking, whichever is later); name it once more before it passes. `--voice` gives one spoken line |

## At its moment: read the notes first

| when | command | what it is for |
|---|---|---|
| before any stream write | `entry row.json --chat MMDD` | write only rows that print `ok`; fix every `FIX` first |
| before every push, and before a pull request is opened or its text edited | `outgoing --title "TITLE" --text pr.md` | open or push only on `0 hit(s)`, with exactly the text it checked; a hit is rewritten, never pasted anywhere public |
| before the dusk close row | `dusk [--photos folder.json]` | the one-pass dusk list, and the day's photos |
| the dusk close, before its close row | `dayqa YYYY-MM-DD` | be•do's own calls on the day first, then one list for her to accept |
| the dusk close, once the day's rows are written | `calsync YYYY-MM-DD` | the calendar mirrors the stream: the done marks |
| the dusk close after `dayqa`, the weekly close, and on call | `chats --sessions mine.json` | the chat sweep: every open chat against its objective and its row |
| the meals alone | `meals --json` | each meal's prep and eating, placed from context |
| a session entry | `stretches FILE --day YYYY-MM-DD --json` | the session's time, from her own stretches |
| the weekly close, right after the split | `cleanup` | the weekly drive cleanup, one drive at a time |
| the weekly close, after the cleanup; and whenever she asks about her drives | `drives --rhythms rhythms.json --stream live.json` | effort with no drive, drives with no goal or date |
| the weekly close | `order --json` | her predicted flow order, written to the catalog |
| every calendar write, before calling it done | `calendar event.json`, then again with `--readback` | the calendar named, the write read back, work in purple |
| the 📧 clear gmail inbox, before anything is archived | `inbox threads.json --archive planned.json` | her automatic keeps are never archived |
| the end of every chat: she says *let's end the session*, or plainly that she's done | `close --chat URL --title "TITLE"` | QA, then the session entry, then the rename; the chat is done when it prints `closed` |
| only if she asks for a Day Behind by name | `daygate YYYY-MM-DD` | the day behind is retired (8 Nov 2026); nothing routine runs this |

## Running it

```
bash run_checks.sh judgment                  # the judgment file, every chat's first reply
bash run_checks.sh how dayqa                 # a command's notes, before its first run in a chat
bash run_checks.sh preflight                 # my day; --part B when the day already has a chat
bash run_checks.sh preflight --kind week --week 40
bash run_checks.sh preflight --kind branch --n 4 --what "👁️ my day page"   # a branch chat: its numbered title, the clock, the base
bash run_checks.sh remaining                 # the open flow as one code line; --flow dawn|dusk to name one
bash run_checks.sh dusk                      # today; --date YYYY-MM-DD for another day
bash run_checks.sh meals                     # the day's meals: prep and eating, placed from context
bash run_checks.sh dayqa 2026-10-09          # the day's QA: one list to accept, at the dusk close
bash run_checks.sh entry row.json --base "w41 be•do" --chat 1008
bash run_checks.sh stretches transcript.jsonl --day 2026-10-24 --json
bash run_checks.sh outgoing --title "The my week page opens quiet" --text pr.md   # before the push and the PR
bash run_checks.sh cleanup                   # the weekly drive cleanup, after the split
bash run_checks.sh close --chat https://claude.ai/code/session_… --title "▶️1024 … my day" --date 2026-10-24   # at its dusk close a my day chat keeps ▶️; ✔️ is the next morning's
```

`preflight` downloads the core fresh from the version store; the other
commands reuse that copy for the session. Her settings (`facts_local.json`:
base and field ids, the time zone, which check enforces which amendment) come
from the `facts_local` row of the `settings` table in `be•do system`, read live,
and never from the repo. The loader's own copy is only the fallback, for a chat
that can't read Airtable. **A settings change is one edit to that row, never a
skill upload** (25 Oct 2026).

## What the calls cost

Every call to Airtable counts against her plan (4 Nov 2026: the free plan's
month ran out on the 4th). The checks keep what changes slowly — the base list
and schemas for a day; the catalog, the settings row, the amendments, rhythms
and people for four hours — in `~/.bedo/cache`, and read the stream live every
time. **After a change to the catalog or a settings row, run the next check with
`BEDO_FRESH=1`**, so it reads live and refreshes what is kept. A spent month
stops at the first refusal (`monthly API allowance is spent`): say so in one
line and read nothing more, connector included. `run_checks.sh usage` prints
the calls made from here, by day and by script.

## Where there is no token

With a token (`AIRTABLE_PAT`, a `bedo_secrets.json` beside the work or in
`~/.bedo`, or a Claude cloud session whose proxy attaches the credential) the
checks read Airtable themselves, and no rows pass through the chat. Without one
(Cowork, a plain chat) the command says `NO TOKEN HERE` and exits 3. **That is
expected, not a failure, and it is not a reason to run the checks by hand.**
Read through the Airtable connector, save each result to a file, and run the
same command again with the files. Which files, and their compact form:
`bash run_checks.sh how no-token`.

## A build idea from a chat that can't push

It goes to Drive as its own inbox file, never as a stream row: the judgment
file's J15 says how.

## If the download fails

Only a failed download — never `NO TOKEN HERE` — is a reason for this. Say so
plainly in one line and run the checks by hand from the same rules —
never from an older copy of the code.
