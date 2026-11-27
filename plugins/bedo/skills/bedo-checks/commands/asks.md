# `asks`

**When:** the first reply of every Claude Code session (`preflight` prints it too), and on call

**Command:** `asks`

**What Duet has handed to Code, read from the stream** (23 Nov 2026, her words: so I don't relay prompts between Duet and Code). She is never the messenger (J17). No prompt is pasted: the ask is a row.

**An ask is an ordinary ⚡ action row** in the live weekly base, ⬜ intention, on the drive it is about (be•do for work on the system), written through `entry` like any row. Her words come first. Under the divider, two lines:

```
for code: one sentence, what the session is for
done when: what finished looks like, something you could check
```

`asks` lists every open one, oldest first, from this week's base and last week's while it is still there. One filtered read a base. `asks   none open` is the usual answer.

**One ask per chat** (24 Nov 2026, her words: show what's in progress so asks don't pile into one chat). `asks` knows this chat's link (the cloud session's own, else `--chat URL`) and sorts the open asks three ways:

- **this chat holds:** an ask whose row already carries this chat's link. Carry on with it and take no other.
- **take:** otherwise, the oldest ask still waiting (⬜ or ▫️), and only that one. The line ends with the `apply` op that picks it up.
- **skip, ▶️ in another chat:** an ask in motion with another chat's link, named with that link so she can see where it is. A ▶️ row with no link is named so; ask her where it is.

The rest are listed as waiting for the next `run asks` chat. Several asks mean several `run asks` chats, one each.

**What the Code session owes each ask it takes**, through the connector, each write through `entry` first:

- **picked up:** the row goes ▶️ in motion and carries this chat's link. The first reply reads the objective and done-when back.
- **no done-when:** draft one and get her yes before building.
- **finished:** one `code:` line under the `[be•do]` divider saying what was done and where (the page, the pull request), then ✅ done. The session entry is a separate row, as always. The ask closes with no end: its time is the moment she asked, and the work's time is on the session entry (24 Nov 2026: an ask closed with an end drew five hours of be•do's work as hers). Write it with `apply`: `{"id": …, "status": "✅ done", "append": "code: …"}`.
- **can't yet:** one `code:` line saying what blocks it. The row stays open and the next session sees what was said.

Duet reads the row to answer *is it done*. Nothing is relayed by hand in either direction.

**What Duet's instructions carry**, once:

> When something needs Claude Code (a fix to a page or a check, a build idea, anything in the be•do repo), don't write a prompt for me to paste. Write one ⚡ action row in the live weekly base, status ⬜ intention, drive be•do (or the drive it is about), my words first, then under the divider two lines: `for code: <one sentence, what the session is for>` and `done when: <what finished looks like>`. Then start a Claude Code session on the be•do repo with only the words `run asks`. To see how it went, read the row: Code writes a `code:` line on it and marks it ✅ done.
