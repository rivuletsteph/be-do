# `daysteps`

**When:** at dusk, for today, in order, not at a set time (24 Nov 2026, her words: I'd rather not do this stuff at a certain time but generally in a certain order … I'd like to run the daily fold as part of the dusk flow). Two short sessions, each started by Duet, unasked:

- **`run dusk`**, the moment her photos are up. She does the batch checks first (🗺️ Timeline, 📱 screen time and 🪐 ring stress screenshots, ⏺️ recorder check), then uploads the day's photos last (her words: I want to do all the batch checks then upload the photos and have the system fill in everything based on that info). It fills in the day from them: steps 1 to 6.
- **`run braid`**, once her ⭐ highlight is logged, so the braid sees the whole evening (her words: move the braid to where it makes the most sense): steps 7 to 11, then her short list, before her phone goes down.

In the morning: see **The morning** below, three sessions in her order.

**Nothing runs on a clock** (27 Nov 2026, her words: I don't want anything to run on the clock, but I do want to make sure that the things that were running on the clock are still getting done, which means they need to be part of the flow). The 3:23a fold, the 4:41a Code steps and the evening chat sweep were paused that day. A night the dusk runs didn't happen is caught by the next `run morning`: it runs whatever of steps 1 to 11 for DAY is still missing, first. The only clocks left are the flows' own backstops: dawn closes at noon, dusk at 11:59 PM.

**Command:** `daysteps` prints this page; the steps are the commands it names.

**Each run is one cheap session** (24 Nov 2026, her words: I'd like these practices to run on its own … in a way that conserves tokens, and this just ran on the largest model at high effort). On 23 Nov the same steps took five asks, two helpers that each carried the whole chat, and every row typed back through the model.

**How to run it**

- **One session, no helpers.** A helper that inherits the chat pays for the whole chat again. The steps are in order and none is long.
- **The mechanical model, low effort** (J15): every step below is a command and its plan. Judgment is asked for in three places only, each marked *look*.
- **Every write goes through `apply`** (`how apply`): a plan a command prints as `--json` goes into the ops file as it is, and a line added to a row is `append`. Never type a row's existing text.
- **Read each command's notes once** (`how NAME`), not the skill files around them.
- **Open an image only when code can't place it**, once, and write what it shows in the same step.

**`run dusk`, in order** (DAY is today)

0. **🌅 the dawn close**, if the morning never wrote it (25 Nov 2026, her words: the dawn flow closes at noon). `remaining --flow dawn --close` prints the row, or `[]` when today has one: it goes to `apply` as it is.
1. **Photos.** List the week's photos folder, then `dusk --date DAY --photos folder.json --json`: write its `photo_writes`. *Look* at each photo no row explains and give it its row (J2); several photos of one moment share a row.
1b. **Screen clips.** Photos and screen clips serve different purposes (24 Nov 2026, her words: I have this to run every evening as part of the photos import, so there are photos and then screen clips). Every clip she takes points to an action. `dusk` lists each clip of the day that no action, event, batch check or media row links yet (`screen_clips`). *Look* at each one, then search the open actions for it two or three ways, by what she would have called it. If one fits, add the clip as a step on that action (`append`). If none does, write a new ⚡ action, ⬜ intention, at the clip's time, with its key. Either way the clip's link goes on that action's `photo_links`, as info, so the next run sees it placed. A 📝 log, 🗨️ text or 📲 capture row that only holds the clip is not where it ends. Batch screenshots (Timeline, screen time, ring) are placed by steps 2 to 4 and are never listed here.
2. **🗺️ map check.** *Look* at the Timeline screenshots among the day's photos, write `stays.json`, then `places --stays stays.json --json`: its rows go to `apply`, and each drive between stays is a 🚗 row with the Timeline's own times. No screenshot: say so on her list and write no stays.
3. **📱 screen time.** *Look* at the screen-time screenshots: one row, the total in its title, split focused and partial (`entry` asks for the split).
4. **🪐 the evening ring read.** The ring skill's runner, `evening DAY`: the day's stress, recovery and activity from the API, so her screenshot only adds what the app shows. Its plan's `create` and `patch` go to `apply`.
5. **📧 clear gmail inbox.** `how inbox`. Read, pull out what is hers in a few lines, and archive only on her go. Then `groups --mail threads.json` on the same read: each ask by email with no row goes on her list, with its link, to add on her yes.
6. **🗂 daily fold.** `how fold`, and its procedure as written: one pull request, never merged here.

Then one line to Duet: what was filled in (counts), and anything from the inbox that is hers.

**`run braid`, in order** (DAY is today)

7. **🔀 braid.** `sweep DAY --json`, then `dayqa DAY --json` with the calendars and the photos listing. Write be•do's own calls and everything under `written, then told`. Open the evidence of each `reconcile` line before proposing it: a row that says a step stays open has not closed it. Her list goes on the braid row, in her plain words, and nothing on it is written until she answers.
8. **Calendar.** `calsync DAY`, its two runs, the changes made and read back.
9. **The my day page, drafted.** The `bedo-day-ahead` skill rebuilds today's page to the day as lived so far and republishes it at the same link. It is not final: the morning makes it so.
10. **The markers.** The 🌄 dusk flow close row carries `braid shown …` and `calsync done …`. Nobody has written it yet at this hour: write it now, status ▶️ in motion, with the two lines. It stays open until she falls asleep; an open close row does not close the flow.
11. **🧹 chat sweep.** `how chats`, then the `chat-sweep` skill's steps 1 and 2 only: every page of `list_sessions` (mine), `chats` with renames on, and what it does on its own: each chat takes its glyph (☑️ ✖️ ▶️) before it is archived (her yes, 27 Nov 2026: rename at dusk; it runs in her flow, not on a clock). Her `ask` chats go on her list; the drive cleanup waits for her. This session needs the chat tools (`list_sessions`, `archive_session`): a session started on a schedule has none, so this step never moves to one.

Then one line to Duet: her list, in plain words, so she has it before her phone goes down.

**The morning** runs in her order, never by the clock (24 Nov 2026, her words: I don't want to do any kind of timed run on a time … I want it to be in the correct order … I want to see the look behind then the morning gate then the look ahead). Three short sessions, each its own, each started by Duet when the step before it is in. DAY is yesterday.

1. **`run morning`, once she's up** (her first entry, or her 💭 dream record): the look behind.
   - **First, last night's catch-up.** If yesterday's 🌄 dusk close row lacks `braid shown` or `calsync done`, or no chat sweep ran, run the missing steps of 1 to 11 for DAY before anything else, and say so in its line to Duet.
   - **🪐 the morning ring read.** `run_oura.sh morning TODAY`: the night's 😴 sleep and her 🪐 morning row, and with it last night's close (her words: I want the evening to close when I fall asleep). The dusk close row takes the ring's bedtime and is closed; with none, one is written there. 🌬️ evening breaths and 🌌 evening blessing, done with her son after her phone is down, are written from her pattern at the same time when no row has them. She corrects. The ring not synced yet: say so to Duet and stop; Duet starts it again once she has opened the ring's app.
   - **Yesterday's my day page, final.** Rebuilt to the whole day as lived, the sleep included, then `run_day_ahead.sh final DAY` and its line on the 👁️ look ahead row. It goes to its own link (`page.url`, else a new artifact, with the link on DAY's 👁️ look ahead row; a day with none gets one). That is what she opens first.
   - One line to Duet: the page's link.
2. **🗞️ the morning gate**, once the look behind is back: its own branch, as always.
3. **`run look ahead`**, once the 🗞️ morning gate row is in: today's draft (the `bedo-day-ahead` skill: `prep`, the calendars, `cal`, `build … --draft`), published to `page.standing`, with the plan's `today_rows` and `future_rows` and the 👁️ look ahead row naming the three. One line to Duet: the three. The final follows her one intention at the ⚡ intention check, in the same session or a new `run look ahead`.

Each session looks first and skips what is already on the stream, so starting one twice does nothing twice.

**What it leaves for her**, one short list: the braid's questions, the inbox's few, any place new to her places, and a photo it could not read. Nothing is trashed, archived, dropped or merged on its own.

**An ask it answers closes without an end.** The ask row marks the moment she asked; an end hours later draws be•do's work as her time and marks whatever she did meanwhile as partial attention.
