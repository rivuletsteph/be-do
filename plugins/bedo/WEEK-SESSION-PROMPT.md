# One cloud session for the week's look aheads and look behinds

Paste everything under the line into a NEW Claude Code cloud session on the
Default environment (claude.ai/code, or the Code tab in the phone app; check the
environment name says Default). Keep the session open all week; each morning and
evening just say "look ahead" or "look behind".

---

This session runs my be•do dawn and dusk pages for the rest of week W40 (through
Sat 3 Oct). Name it ▶️𖡎 W40 pages — carry the 𖡎 from a tool result, never type it.

Setup, once, before anything else:
1. `mkdir -p ~/bedo && cd ~/bedo && git clone -q --depth 1 -b claude/clever-mccarthy-xqyl2z https://github.com/rivuletsteph/be-do src`
   (until that branch is merged to main, it is the version with the cloud
   credential; if `git -C src log -1 --oneline` shows main already has commit
   589590c or later, clone main instead).
2. Two working folders whose runners come from that clone, and whose overlay/
   makes the runner use the clone's scripts rather than main's:
   `mkdir -p lb/overlay da/overlay`
   `cp src/plugins/bedo/skills/bedo-look-behind/run_look_behind.sh lb/ && cp src/plugins/bedo/skills/bedo-look-behind/scripts/*.py src/plugins/bedo/skills/bedo-day-ahead/scripts/day_digest.py lb/overlay/`
   `cp src/plugins/bedo/skills/bedo-day-ahead/run_day_ahead.sh da/ && cp src/plugins/bedo/skills/bedo-day-ahead/scripts/*.py src/plugins/bedo/skills/bedo-look-behind/scripts/bedo_fetch.py da/overlay/`
   `export LB_OUT=~/bedo/out`
3. Load the skills anthropic-skills:bedo-look-behind and anthropic-skills:bedo-day-ahead
   and read src/plugins/bedo/skills/bedo-look-behind/SKILL.md and
   src/plugins/bedo/skills/bedo-day-ahead/SKILL.md from the clone — those, not the
   installed loader copies, are the steps to follow. The settings files are in
   /root/.claude/skills/synced/*/bedo-*/assets/; the runners find them by
   themselves. There is no token file and none is needed: the fetch sends no
   Authorization header and the environment's credential is attached by the proxy.
   Confirm with `cd ~/bedo/lb && LB_DIR=$PWD bash run_look_behind.sh prep <today>`
   and tell me the `auth:` line it prints.

Each morning when I say "look ahead": the day ahead as one final build, per its
SKILL.md — secure base (secure unless I say otherwise), my intentions in my
words, then prep → calendars through the Calendar connector → cal → build with
--intention ×3 and no --draft → publish to the living page → save the page to
Drive in the week's folder (2026-W40 Sep 27) → log the 👁️ look ahead row.
Show me the three, the today rows written, and one numbered list of asks.

Each evening when I say "look behind": the day behind per its SKILL.md — prep,
words drafted from the digest and shown to me (mark them --draft unless I edit
them there and then), secure base from the digest, build, publish, save to
Drive, calendar sync, and the log row with the --row-block in its [be•do] block.
One or two lines in the chat, not the page.

Rows go in the base whose week contains the row's own datetime; W40's base is
live until Sat 3 Oct and W41's must be cloned at my Sunday close before anything
builds Sunday. Never print a token. Write a session entry when I say the week is
done.
