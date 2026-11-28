---
name: "chat-sweep"
description: "Run the be•do chat sweep on its own, any day: every open chat checked against its objective, ☑️ chats archived, a session entry made sure of, and the open ones given their next step or hang-up for her to decide. Then the drive cleanup's next drive. Use when the user asks to sweep, clean up or archive her chats, close old chats, or check which chats are finished."
---

# be•do chat sweep, on call

Her words, 11 Nov 2026: *I want something that I can run every day that just
does what I said. It goes through, checks the objectives of the sessions, makes
sure they're complete. If they're complete, gives them a check mark. Makes sure
there's a session entry in the stream. And then archives them. For the ones
that are still open, it identifies what the next step is or what the hang up
is, or lets me make a decision about that. And this should be tied in with my
drive cleanup work.*

The judgment is code (`bedo_chats.py`, the 2 Nov amendment, built 5 Nov). It
also runs at the dusk close and the weekly close (bedo-checks). This skill is
the same sweep when she asks for it, on any day (her pick, 11 Nov: both).

**Her sidebar holds three kinds of chat, and the sweep reads every one this
chat can reach** (27 Nov 2026: a Code-tab sweep closed 15 laptop chats and
never saw her cloud sessions or her plain claude.ai chats; a Chat-tab sweep
said it had no list at all and sent her to the Code tab).

| Kind | Where its list is | How it is renamed, unpinned, archived |
|---|---|---|
| the laptop's own Code chats (`local_…`) | only the desktop app's `list_sessions`, in a Code-tab chat on the laptop | the app's `set_session_title`, `set_pinned`, `archive_session` |
| cloud Code sessions and Cowork tasks (`cse_…`, `session_…`) | claude-code-remote's `list_sessions` in a cloud session, or claude.ai in a browser | claude-code-remote's tools, or `claude_ai_act.js` in the browser |
| plain claude.ai chats | claude.ai in a browser only | `claude_ai_act.js` in the browser |

## 0. What this chat can reach, then one step

Look at the tools this chat has, then:

- **A Code-tab chat on the laptop** (it has `list_sessions` from the desktop
  app): read that list (step 1), and ask once to read claude.ai too (step 1b).
- **A cloud session** (claude-code-remote's `list_sessions`), the one she can
  always start from her phone (her goal, 27 Nov 2026: *always be able to run
  this on my phone for the cloud sessions*): read that list and sweep the cloud
  sessions with claude-code-remote's own tools (`archive_session`,
  `set_session_title`, `set_session_tags`), needing nothing on the laptop. Ask
  for claude.ai's plain chats (step 1b) only when this session has a browser
  tool. Without one, don't ask and don't stop: the sweep's `not in this sweep:`
  lines name the rest, and that is the whole report on them.
- **A Chat-tab or Cowork chat linked to her computer** (no session list, but a
  browser: Claude in Chrome's `javascript_tool`, or the built-in browser's,
  `mcp__remote-devices__Claude_Browser__javascript_tool`, turned on with
  `enable__mcp__remote-devices__Claude_Browser` where that is all there is):
  claude.ai is the list (step 1b). The sweep then runs on claude.ai alone and
  says, in its `not in this sweep:` line, that the laptop's Code chats were not
  read. End with that one line: *the laptop's Code chats are swept from a
  Code-tab chat: say chat sweep there.*
- **No list, no browser, or no shell to run the checks**: one line and stop:
  *this chat can't reach your chat list: open a Code-tab chat on the laptop and
  say chat sweep.* Never a longer explanation, never the sweep by hand.

## 1. The list and the sweep

Save `list_sessions` (mine, `limit` 100) as it came — the cloud tool's result
wrapped as `{"ccr": {...}}` is fine. **Read every page**: while a page says
`has_more` true, read the next with `after_id` set to its `last_id`, and save
each page as its own file (12 Nov 2026: the second page held an open chat).

### 1b. claude.ai, in the browser, with her yes that turn

Reading claude.ai is reading her account: **ask that turn, once for the
sweep** (*read your claude.ai chats and cloud sessions for the sweep?*), in
either browser. Her Chrome needs that yes every time, even signed in. Prefer
the built-in browser when it is signed in to claude.ai, and open a new tab on
`https://claude.ai/recents`; never sign her in or out.

On her yes, pass the text of `claude_ai_read.js` (beside this file) to the
browser's `javascript_tool` as it is, and save what it returns, as it came, to
`claude_ai.json`. It reads her plain chats, her cloud Code sessions and her
Cowork tasks (every page), leaves out what is archived and every scheduled run,
and changes nothing. A `401`/`403` means the browser isn't signed in to
claude.ai: say so in one line and sweep what the other lists hold.

```
bash run_checks.sh chats --sessions page1.json --sessions page2.json --sessions claude_ai.json
```

(The dusk sweep in `run braid` renames, her yes 27 Nov 2026. Only a sweep started on a schedule adds `--no-rename`.)

Exit 2 with `the list goes on` means a page is missing: read it and run again.
A `not in this sweep:` line names a kind of chat no list given covered, and
where it is read.

With no token, pass `--rows` (the ⚡ rows that carry a chat link, this week's
base and last week's) instead.

## 2. On its own, before she sees anything

Each chat is acted on where it lives (the table at the top). **A chat read
from claude.ai** — the sweep's `in the browser:` line counts them — is
renamed, unpinned and archived from the browser too: run the sweep again with
`--json`, put that output in place of `__FOUND__` in `claude_ai_act.js`, and
pass the text to the same `javascript_tool`. It does at most 25 steps a call,
spaced for claude.ai's rate limit, and reads each one back; run it again with
`START` set to the `next` it returns until `next` is null. Each chat's rename
comes first, then its unpin (`is_starred` false for a plain chat, the
`ui:pinned` tag off a cloud session), then its archive, and only an `archive`
verdict is archived: a `close_row`, `carry` or `entry` chat is archived once its
row is written, by reading claude.ai and running the sweep again. Anything in
`failed` is said in one line, never retried blind. (Tried 27 Nov 2026: the cloud
archive and the unstar took. A plain chat's archive and a cloud tag's removal
were not yet tried then: the read-back is the check.)

- `archive` → archived where it lives: `archive_session` (the desktop app's, or
  claude-code-remote's in a cloud session), or the browser step above. **A line saying `pinned: unpin it, then
  archive`**: unpin it first (as for `unpin` below), then archive (her rule,
  11 Nov 2026).
- `close_row` → its row ✅ in the base it lives in, then archive.
- `carry` → its next step on an open ⚡ row (check that an open row doesn't
  already hold it), or into a ⏯️ prompt for a new chat, then archive.
- `entry` → its session entry (the session-entry skill from the version store),
  one row for its newest day with her time. Several of them can run at once,
  one helper per chat. Each one first looks for a row already carrying the
  chat's id. Then run the sweep again.
- `hold` clears itself once its side chat is archived. Run again.
- `unpin` → unpin it (her amendment, 12 Nov 2026,
  her words: *I really just want to have either pinned or recents showing up
  and then rely on my system to do the rest of the organizing. But pinned
  needs to be what I'm actively working on that day.*). A pinned chat not
  touched today in her time zone is unpinned and stays open in recents; the
  my day chat never is. Any other chat whose line ends `pinned, not touched
  today: unpin it` is unpinned the same way. **In the cloud a pin is the
  `ui:pinned` tag**: `set_session_tags` with `remove: ["ui:pinned"]` on the
  ids the sweep's `cloud:` line prints, then `get_session` on one to see the
  tag gone (tried 12 Nov 2026; she saw the chat leave Pinned). The desktop
  app's tool is `set_pinned` false. Only where neither tool is there, give her
  the `unpin:` line, and she unpins them.

**Rename** (her yes, 16 Nov 2026: rename them before archiving; the first
sweep archived 419 chats under the app's own names): a line ending
`rename → <title>` is renamed to that title before it is archived, and an open
chat with one is renamed ▶️ and left open, nothing sent into it. The title is
the glyph (☑️ done, ✔️ a closed window chat, ✖️ dropped, ▶️ open), a drive code
only when the title or its row already shows one, and a short title; never a
guessed code. Never a chat touched in the last 15 minutes, or today's my day
chat. **A sweep started on a schedule never renames another chat (her rule, 22
Nov 2026): it runs with `--no-rename`.** The dusk sweep in `run braid` is part
of her flow and renames (her yes, 27 Nov 2026).

Leave `left alone` as printed. Never write to a busy chat's rows.

Then one line: `archived N finished chats · unpinned N`.

## 3. Hers, one short list

**be•do makes the call; she says go** (her words, 27 Nov 2026: *I feel like
you're still putting a lot on me to make these decisions. Can you please make a
clear recommendation … keeping the responses relatively concise*). Every `ask`
chat and every kept chat gets be•do's pick, close or keep, never a question.
Close when its wait is already answered elsewhere (a pull request merged, a day
gone by, a question its row now carries). Keep only what needs her own answer
or her own hands. Park is hers alone, so never pick it.

The list is one line per chat, `pick · chat · why`, with the closes first, and
then a single question: *go?* She answers once, or names the ones to change.
Don't restate the sweep's output, and don't ask for anything she has already
answered.

Each line says **what the chat is waiting on**: the last question it asked her,
or its row's `still open`. Read the chat's last few turns (`list_events`, a
small `limit`) for that line, and check a waited-on pull request's state before
calling it open. Never ask her to go and look.

- close → its entry with the objective line, then archive
- park → ⏸️, her word
- keep → `chat sweep: kept YYYY-MM-DD` in its row's `[be•do]` block (a chat
  with no row gets its ▶️ entry first, carrying the line)

The in-motion chats the sweep kept go on the same list with be•do's pick. A
newly written ▶️ entry names what the chat is waiting on. She asked for that
line for every open chat, not only the quiet ones.

## 4. Then the drive cleanup

```
bash run_checks.sh cleanup --drives 2
```

Say the big picture in plain words, then work **one drive at a time in this
chat** (her pick, 11 Nov). Make every call, check mail for evidence where a row
names a bill, a refund or a notice, and write only what she confirms, each
with its `[be•do] drive cleanup, <date> (<this chat>):` line. Carry her words
above the divider. ✖️ and ⏸️ are hers. A ✖️ for a fold or a dedupe is the one
be•do writes, naming the row it folded into.

## Learned on the first run (11 Nov 2026)

- The app's archive call can come back asking for its own input echoed back.
  Send it again with the `session` field it quotes.
- A new row's key can collide with an old one in the same base. The entry check
  doesn't catch it, so search the key before writing and add `b` on a clash.
- An entry goes in the base whose week holds its date, even when that's an
  older base.
