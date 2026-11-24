# `daysteps`

**When:** at dusk, for today, in order, not at a set time (24 Nov 2026, her words: I'd rather not do this stuff at a certain time but generally in a certain order … I'd like to run the daily fold as part of the dusk flow). Duet starts it, unasked, the moment her batch is in: the day's photos, 🗺️ Timeline, 📱 screen time and 🪐 ring stress shared, and ⏺️ recorder check done (her words: when the batch is in, it should kick off automatically). The session's first words are `run dusk`. In the morning only the sleep is left: see **The morning** below. The 3:23a fold and 4:41a Code steps are the backup for a night the dusk run didn't happen, and do only what is still missing.

**Command:** `daysteps` prints this page; the steps are the commands it names.

**The day's Code steps run in one session, cheaply** (24 Nov 2026, her words: I'd like these practices to run on its own … in a way that conserves tokens, and this just ran on the largest model at high effort). On 23 Nov the same steps took five asks, two helpers that each carried the whole chat, and every row typed back through the model.

**How to run it**

- **One session, no helpers.** A helper that inherits the chat pays for the whole chat again. The steps are in order and none is long.
- **The mechanical model, low effort** (J15): every step below is a command and its plan. Judgment is asked for in three places only, each marked *look*.
- **Every write goes through `apply`** (`how apply`): a plan a command prints as `--json` goes into the ops file as it is, and a line added to a row is `append`. Never type a row's existing text.
- **Read each command's notes once** (`how NAME`), not the skill files around them.
- **Open an image only when code can't place it**, once, and write what it shows in the same step.

**The steps at dusk, in order** (DAY is today)

1. **Photos.** List the week's photos folder, then `dusk --date DAY --photos folder.json --json`: write its `photo_writes`. *Look* at each photo no row explains and give it its row (J2); several photos of one moment share a row.
2. **🗺️ map check.** *Look* at the Timeline screenshots among the day's photos, write `stays.json`, then `places --stays stays.json --json`: its rows go to `apply`, and each drive between stays is a 🚗 row with the Timeline's own times. No screenshot: say so on her list and write no stays.
3. **📱 screen time.** *Look* at the screen-time screenshots: one row, the total in its title, split focused and partial (`entry` asks for the split).
4. **🪐 the evening ring read.** The ring skill's runner, `evening DAY`: the day's stress, recovery and activity from the API, so her screenshot only adds what the app shows. Its plan's `create` and `patch` go to `apply`.
5. **📧 clear gmail inbox.** `how inbox`. Read, pull out what is hers in a few lines, and archive only on her go.
6. **🔀 braid.** `sweep DAY --json`, then `dayqa DAY --json` with the calendars and the photos listing. Write be•do's own calls and everything under `written, then told`. Open the evidence of each `reconcile` line before proposing it: a row that says a step stays open has not closed it. Her list goes on the braid row, in her plain words, and nothing on it is written until she answers. The braid reads the rows in by then; what she logs after it (her pills, the quest, the highlights) reaches the page in the morning rebuild.
7. **Calendar.** `calsync DAY`, its two runs, the changes made and read back.
8. **🗂 daily fold.** `how fold`, and its procedure as written: one pull request, never merged here.
9. **The my day page, drafted.** The `bedo-day-ahead` skill rebuilds today's page to the day as lived so far and republishes it at the same link. It is not final: the morning makes it so.
10. **The markers.** The 🌄 dusk flow close row carries `braid shown …` and `calsync done …`. Nobody has written it yet at this hour: write it now, status ▶️ in motion, with the two lines. It stays open until she falls asleep; an open close row does not close the flow.

Then one line to Duet: what was written (counts), and her list, in plain words, so she has it before her phone goes down.

**The morning** (DAY is yesterday), after she wakes, in one short session that Duet starts:

1. **🪐 the morning ring read.** `run_oura.sh morning TODAY`: the night's 😴 sleep and her 🪐 morning row, and with it last night's close (her words: I want the evening to close when I fall asleep). The dusk close row takes the ring's bedtime and is closed; with none, one is written there. 🌬️ evening breaths and 🌌 evening blessing, done with her son after her phone is down, are written from her pattern at the same time when no row has them. She corrects.
2. **Yesterday's my day page, final.** Rebuilt to the whole day as lived, the sleep included, republished, then `run_day_ahead.sh final DAY` and its line on the 👁️ look ahead row. That is what she opens next.

**What it leaves for her**, one short list: the braid's questions, the inbox's few, any place new to her places, and a photo it could not read. Nothing is trashed, archived, dropped or merged on its own.

**An ask it answers closes without an end.** The ask row marks the moment she asked; an end hours later draws be•do's work as her time and marks whatever she did meanwhile as partial attention.
