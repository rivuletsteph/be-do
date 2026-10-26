---
name: "session-entry"
description: "Write a be•do work-log entry for the current session straight to the stream, as an ⚡ action row. Use when the user asks to create a session entry, log the session, or write a be•do entry."
---

# be•do session entry

She keeps a structured daily log. This skill **writes one `⚡ action` row
straight to the stream**, then shows her what it wrote. She does not paste
anything.

**This folder is the skill; what is installed is a loader** (`loader/SKILL.md`,
backlog 261010a). The loader fetches this file fresh from the version store on
every run, so a change here needs no upload.

Settled with her:
- The entry is written automatically (22 Sep 2026).
- The session entry also **names the chat**, on her yes (22 Sep 2026).
- Three things are left for the **my day** chat to fill: **attention**, the
  **drive** (unless this session already settled it), and the **feeling**.
  Don't ask how it felt; my day does that.
- **Wellness is still deduced**, never left for her (V51).
- **The time is hers, not the session's** (25 Oct 2026, backlog 261024a): the
  row's clock comes from her own messages, never from when the chat opened and
  closed or from when Claude was working. Device time is only as long as the
  data shows.

When the work is done, offer the entry unasked. `still open` is why the entry
exists: it points the way forward.

Schema, IDs and exact choice strings are in the `bedo-airtable` skill. **Load it
first**, and copy every choice string from it verbatim.

## 1. Work out the times: her stretches

Run the checks' `stretches` over this chat's own record, scoped to the day the
entry is for:

```
bash run_checks.sh stretches <the chat's record> --day YYYY-MM-DD --json
```

It counts **her turns only** — never Claude's turns, tool results or skill
text — and splits them wherever more than 15 minutes pass between her
messages. It prints the row's clock and the line its `[be•do]` block carries:

```
{"datetime": "…Z", "time_spent": 1080, "line": "stretches: 3:19–3:21 · 3:52–3:54 · 4:46–5:00 = 18m", "minutes": 18}
```

**The chat's record**, by surface:
- **a Claude Code session, cloud or desktop** — its transcript, the newest
  `.jsonl` under `~/.claude/projects/<the working folder>/`. Or, for a cloud
  session, its own events: `list_events` on the session id from
  `get_session` (omit the id), saved as the tool gave it, paging back
  (`before_id`) until the first page that starts before the day.
- **a claude.ai chat** — the conversation read,
  `GET /api/organizations/{ORG}/chat_conversations/{uuid}?tree=true`, saved as
  it came. Only her side is counted.
- **nowhere to read it** — her message times as a plain list of ISO stamps,
  from what the chat can see (uploads carry their time: a file at
  `/mnt/user-data/uploads/<13 digits>_<name>` landed at those epoch
  milliseconds). Say the time is approximate.

**Clock:** `date -u +%Y-%m-%dT%H:%M:%SZ` and derive Central from it — CDT is
UTC−5, CST is UTC−6. Don't trust `TZ=America/Chicago date` in Git Bash on
Windows; on 21 Sep 2026 it returned UTC labelled as Chicago.

A chat that runs across days logs **each day's stretches on that day's row**
(`--day`). Offer separate rows for the earlier days.

If she stated a time in conversation ("it's 9:33"), that is a real timestamp.
Never present an invented time as certain.

## 2. Compose the row

| field | value |
|---|---|
| title | one line, under 12 words, plain and specific |
| key | `YYMMDD_HHMM` from the **first stretch's start**. 2:15pm on 4 Sep 2026 is `260904_1415` |
| datetime | the first stretch's start, from `stretches --json` |
| end datetime | **one stretch only**: its end, from `stretches --json` |
| time spent | **several stretches**: their sum, from `stretches --json` (seconds), with no end. Never both |
| status | `✅ done` if the thing is finished, `▶️ in motion` if it is real work that isn't done yet |
| practice | `⚡ action`, with one space after the glyph |
| deliverable | one URL, the **output**, never an input. No URL → leave empty |
| chat | the chat's URL, in the stream's own `chat` URL field. The title goes in the `[be•do]` block |
| rhythm / drive | **only if this session already settled it**: the `chat-title` skill ran here, or she named it. Otherwise leave empty for my day |
| wellness | **deduced, always.** See below |
| device | deduced: the device she did this session on. A cloud session she drove from the phone is 📱 phone |
| details | see below |

**Left empty, deliberately:**
- **for my day:** attention, emotion, emotion word, and the drive when it isn't
  settled
- **as before:** phase and person, unless she stated them

**Several stretches carry their line.** The `stretches: …` line goes in the
`[be•do]` block exactly as printed, on its own line. The day behind draws the
session over those stretches only, and `close` checks that the time spent is
their sum. A window chat's ⚡ row (my day, my week) carries no time at all; its
📲 capture rows hold the minutes.

**Deducing wellness.** Read the choice strings from the live schema: the eight
have been **lowercase since 7 Sep** (`💨 air`, not `💨 Wind`). Start from what the
work was *for*:
- be•do's own work logs as **air**
- building tools, layers and pipelines is **air**; the thinking and analysis
  is **mind**; the advocacy and community end of her work is **water**
- the `⚡ action` practice row's own wellness is a fallback, not a verdict

If the master instructions are loaded (a be•do project chat), their wellness
section governs. Pick the one domain the session mostly served. Never leave it
empty because it was hard to call; that call is be•do's, not hers.

**details**, in this order:

```
what I did
· objective: <what it was> — met | partly met | not met, <why>   ← first, outside a window chat
· [3–6 bullets, first person, past tense, her voice not yours]
· [each one a thing that actually got finished or moved]

still open
· [one line each, or: none]
———
[be•do] written by session-entry YYYY-MM-DD HH:MM CT
for my day: attention · drive · feeling      ← list only what is still empty
chat: [exact title] · [url]
stretches: [as printed]                        ← several stretches only
```

The divider is three em dashes alone on a line. Everything above it is hers and
survives export; the `[be•do]` block is dropped on export.

**The chat line: title AND url, read, never invented.** In a claude.ai chat, read
`GET /api/organizations/{ORG}/chat_conversations?limit=400` and take `name` and
`uuid` from the same record: `https://claude.ai/chat/<uuid>`. In a Claude Code
session, use `get_session` with no id, taking `title` and the session link. No
readable title → url alone, and say so. 𖡎 (U+1684E) is never typed from memory;
carry it from the read.

**The objective** — set at the open by `chat-title`, or carried in by a `⏯️`
prompt, or the one the chat worked toward when none was set — is the first line
of `what I did`, outside a window chat: met, partly met, or not, and why, in
one line (`close` checks it). Work not met names its next step under
`still open`.

Bullets are in her voice: first person, short, concrete. No grading the session,
no "we explored". Do not editorialise. **The objective line is the one exception**:
it measures the session against what it set out to do, and says so once.

## 3. Name the chat

Name the chat with the `chat-title` skill's format and rules. Load it; don't
restate it here. At a session entry:

- **Status glyph matches the entry:** `☑️` for a `✅ done` row, `▶️` for
  `▶️ in motion`, or `✔️` if it's a window chat (my day, my week). The title takes
  `☑️`, never `✅`. The row's status stays `✅ done`.
- **The two other open states** (3 Oct 2026):
  - `⏯️` when the row is `▶️ in motion` **and** the session ends with a prompt
    for the next one.
  - `⏸️` when she has said she is setting it down on purpose.
  - Otherwise unchanged.
- **The row stays `▶️ in motion` for `▶️`, `⏯️` and `⏸️`.** For `⏯️`, `still
  open` names the next push and says the prompt is at the end of the chat. For
  `⏸️`, `still open` says she set it down on purpose.
- **When she asks for a session entry on paused work**, offer to write the
  next-session prompt so the chat can take `⏯️`. Write the `objective:` and
  `done when:` lines first; without both, the prompt doesn't earn `⏯️`.
- **The code, step and topic emoji** come from chat-title's drive and step rules.
  If the drive genuinely can't be settled, name the chat without a code, and
  leave the drive for my day as above.
- **If the chat already carries a proper title**, only change the status glyph.
  An older `✅` on a finished chat becomes `☑️` here.
- **Show the title and rename once she says yes.** Ask in the same message that
  reports the row, as one line. It's the only question the entry asks.
- **How:**
  - a claude.ai chat: PUT `/api/organizations/{ORG}/chat_conversations/{uuid}`
    with `{"name": …}`, from the browser
  - a Cowork or cloud Code session: `set_session_title` on the session id from
    `get_session`
  - a session that can't be renamed: hand her the title string to apply
- 𖡎 is carried by codepoint, never typed.

The row records the title and the URL together. If she approves the new title,
update the row's `[be•do]` chat line in place to the new title. The URL doesn't
change.

## 4. Write it

1. **Resolve this week's base by name** (`w## be•do`). Never carry a weekly base
   ID from memory. Read the newest stream datetime; if it isn't within about 36h,
   it's the wrong base, so stop and say so.
2. **Check the key and the status, not the chat** (28 Sep 2026). A chat holds
   many sessions, and a my day chat may report on one another chat is still
   working, so "a row exists" is not by itself a duplicate. Filter the stream
   on key = this key:
   - **no row** — write the entry as normal.
   - **a row at an earlier status** — the work has moved on. Write the
     status-change row (`▶️ in motion` → `✅ done`), reusing the key. This is the
     normal close of a session someone else opened.
   - **a row at the same status covering the same stretch** — this is the real
     duplicate. **Don't write a second one.** Show what is there, and offer to
     fill any empty fields in place instead.
   - **a separate working stretch in the same chat** — its own key from its own
     start time, its own row.

   **Don't double-count the time.** When an earlier row on this key already logs
   stretches, the closing row counts only the stretches after them and says so
   in its `[be•do]` block.
3. **Run the entry check** (`bash run_checks.sh entry row.json`) and write only
   a row that prints `ok`.
4. **Write one record** with `create_records_for_table`, using field IDs and
   `typecast` off.
5. **Check the echo:** `createdTime` against the clock, and each select value
   against the exact choice string. Correct in place if anything is off.

If Airtable isn't reachable (no connector, or an auth error), don't retry in a
loop. Show the entry as a code block to paste by hand, say plainly that it was
not written, and say why.

If she asks for a preview first, show it and write on her yes.

## 5. Tell her, briefly

The reply reads in ten seconds (V53 J10): **Objective**, **Met?**, **Next**,
**Title** — four short lines, and the row in a code block below them.

Keep any commentary short: an approximate time, an empty deliverable (because
the thing isn't hosted), a status that could go either way and what would flip
it, an untitled chat. **Don't ask how it felt.**

## What my day does with these rows

For reference; this lives in the my day chat, not here. Rows written by this
skill carry `for my day:` in their `[be•do]` block, followed by the fields still
empty. My day asks her for them, writes them in place, and removes those words
from the list. The weekly close measures attention coverage (flagged under 95%),
so these rows want finishing before the Sunday close.
