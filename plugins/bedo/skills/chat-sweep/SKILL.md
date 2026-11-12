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

**It reads the session list it can reach**: the desktop app's `list_sessions`,
or in a cloud session claude-code-remote's `list_sessions` (mine). claude.ai
chats ride along only as another `--sessions`, read with her yes that turn.

## 1. The list and the sweep

Save `list_sessions` (mine, `limit` 100) as it came — the cloud tool's result
wrapped as `{"ccr": {...}}` is fine. **Read every page**: while a page says
`has_more` true, read the next with `after_id` set to its `last_id`, and save
each page as its own file (12 Nov 2026: the second page held an open chat).

```
bash run_checks.sh chats --sessions page1.json --sessions page2.json
```

Exit 2 with `the list goes on` means a page is missing: read it and run again.

With no token, pass `--rows` (the ⚡ rows that carry a chat link, this week's
base and last week's) instead.

## 2. On its own, before she sees anything

- `archive` → `archive_session`. **A line saying `pinned: unpin it, then
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

Leave `left alone` as printed. Never write to a busy chat's rows, and never
rename another chat unless she says so for that chat.

Then one line: `archived N finished chats · unpinned N`.

## 3. Hers, one short list

Each `ask` chat as close, park or keep, with **what it is waiting on, in one
line**: the last question it asked her, or its row's `still open`. Read the
chat's last few turns (`list_events`, a small `limit`) for that line; never
ask her to go and look.

- close → its entry with the objective line, then archive
- park → ⏸️, her word
- keep → `chat sweep: kept YYYY-MM-DD` in its row's `[be•do]` block (a chat
  with no row gets its ▶️ entry first, carrying the line)

Then the in-motion chats the sweep kept, one line each with the decision
waiting on her. A newly written ▶️ entry names it. She asked for that line for
every open chat, not only the quiet ones.

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
