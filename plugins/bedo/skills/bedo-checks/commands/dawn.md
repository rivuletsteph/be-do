# `dawn` (and `dawn --flow dusk`)

**What:** the dawn page (27 Nov 2026). Her dawn flow as four lanes in the wellness wheel colors (heart, body, mind, spirit, from the catalog's `wellness`), the next three steps as buttons, and the steps done in the order done, each with its time and a line from its row. During dawn, Duet hands her its link once, in place of the remaining line. The noon backstop and the flow's self-close stay as they are.

**How it stays cheap** (her words, 27 Nov 2026: that is a lot of Airtable calls): the page reads the day's rows through her own Airtable connector only when she opens it, comes back to it after a minute away, or taps *Read again*. Nothing runs on a timer. A tap writes one row (the step's catalog name, ◉ done, the minute she tapped, typecast off) and fills its own dot without a second read; a 10-second *Undo* deletes the row it just wrote. A morning costs about one read per look and one write per tap.

**What it knows by itself:** the order is `bedo_remaining.flow_steps`, worked out at build and written into the page; the page decides what is done (a row of the step or of its same kind, the covers, an open close row closing nothing), holds 🚽 bm until her other steps are in, and drops 🔅 morning sun from the next three once its by-time has passed. 🗞️ morning gate and 👁️ look ahead fill when Code logs them and are never buttons; 😶 wake, 🪐 and 🌦️ are left off. When the week turns, the page finds the new week's base by name, one search the first time it opens that week.

**When to build it:** only when the order changes, never for a step logged. That is the weekly close, after `order --json`, and any change to a dawn step in the catalog (run with `BEDO_FRESH=1`).

```
bash run_checks.sh dawn --out dawn.html
```

It prints `page.title`, `page.file`, `page.standing` and `page.capabilities`. Publish `page.file` with exactly those capabilities: to `page.standing` (the settings row's `dawn_url`) in place, or, when that is empty, as a new artifact (icon `sunrise`) whose link then goes on the row as `dawn_url`. Her rows reach the page through her connector, so the first tap after a publish may ask her once to allow Airtable for the page.

**The dusk page** (27 Nov 2026, her ask that evening) is the same page for the dusk flow, built with `--flow dusk` and published to `dusk_url` (icon `sunset`). Its settings are `dusk_page` in the facts, over `dawn_page`: the steps a Code run writes (🪐, 🗺️ map check, 📱 screen time, 📧 inbox, 🔀 braid, ⚔️ his quest) fill when the run writes them and are never buttons; ⭐ highlight and 🌟 his highlight open a box for her words, which go above the divider (⭐ as ● log); 💊 evening pills is one tap writing both rows, each with her default from the settings row; 🌬️ evening breaths and 🌌 evening blessing show last and are never offered as next. Rows before 5 AM belong to the evening before, and the page says the evening closes when she falls asleep.

**Its rows go through `sweep`** at the dusk close like any row written outside a check (J17).
