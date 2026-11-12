---
name: "bedo-meal-plan"
description: "Plan a stretch of meals when the user opens it — a week of dinners, or only the next few nights on a minimal week — from what was actually eaten, who is home, what the shelf probably holds and the recipes they cook, then the shopping list it needs and the grocery order. Use when the user asks for a meal plan, to plan dinners or the week's meals, what to cook this week, or to get ready to order groceries. Never on a schedule."
---

# The meal plan

Her words, 5 Nov 2026: *it would be good to have a meal planning skill that I can
access when I am wanting to do that effort.* Built from the first full plan
(26–28 Oct), which drafted a week, was corrected three times by what only she
knew, and ended in a grocery order.

**She opens it. Nothing here fires on a schedule** — no Sunday prompt, no nudge
when a recipe email lands. A plan is something she reaches for when she has the
energy for it, and a week she isn't planning is not a miss.

**This skill plans; the provisions skill owns the shelf.** The shelf's rules —
decay, one row per clock, the standing provisions page, the 🍳 meal prep row when
she cooks — are the provisions skill's, and this follows them.

## Two sizes

Read which one from her words, and ask only when they don't say.

- **a full plan** — the next seven days of dinners, then the shopping list and
  the order. *Plan the week*, *I don't have a meal plan*, *before I order
  groceries*.
- **a minimal plan** — the next two or three nights, from what is already in the
  house: freezer meals, leftovers, the easy dinners. No new recipes, no list
  beyond what those nights can't do without. *Doing the minimal*, *an easy week*,
  *just get us through*. A minimal week is a choice, not a failure; don't argue
  it up into a full plan.

## 1. Read, in code

The brief is one short read of everything the plan rests on, so the chat never
reads the shelf or the stream by eye:

```
python3 scripts/meal_brief.py --stream <this week's stream> [--stream <last week's>] \
    --supplies <supplies> --recipes <recipes> --today YYYY-MM-DD
```

Each dump is a **full** read through the Airtable connector, saved as a file
(I11: a truncated read stops it). Pass last week's stream too early in a week, so
`ate` covers ten days. Settings: `assets/meal_plan_local.json`, else the
`meal_plan_local` row of the settings table; the stream's field ids and the time
zone come from the core's `facts_local`. `--json` gives the same brief as data.

What it gives:

- **ate** — what was actually eaten, each meal marked cooked, reheated, out,
  theirs (a family member's cooking) or eaten. A plan row is not a meal.
- **ahead** — the next seven days, each with the week's typical theme and any
  open intention whose title reads as food (a potluck, a dinner out).
- **shelf** — consumables in date by where they're kept, with days left; past
  their shelf life (probably gone); running low; and the wants, by store.
- **recipes** — in rotation and want to try, scored on key ingredients: probably
  makeable, one or two away, further, or a house dish with no ingredients on
  record.

## 2. The first reply: a draft, then one question

Lead with the plan as a short table — **day · dinner · a note** — and keep the
rest to a few lines. She often doesn't read every bit; the table is what gets
read.

Then ask **the one thing only she knows: who is home, and which nights are
spoken for** — a night out, dinner at someone's house, a night the kid is away,
a late work night. The first plan missed exactly this, three times. Ask it once,
plainly, alongside the draft; don't hold the draft back for it.

How the draft is made:

- **The week's shape is a typical, not a rule** (the settings' `week_shape`). A
  meal fits a theme; it is never placed because of it. A night with nothing that
  fits is named as open, not filled.
- **What was eaten shapes what comes next.** A dish eaten twice this week is not
  offered again; a reheated dish is not a second cook; leftovers in the fridge
  are a dinner. A night someone else cooks counts as a dinner.
- **Freezer and pantry first.** They're the shelf's reliable part. Fresh food
  past its shelf life is *probably gone*, and a meal that needs it goes on the
  list, not on a night.
- **A night that needs shopping sits after the shop.** Ask when the order or
  pickup is, and move a meal that needs fresh things to after it rather than
  planning around an errand that isn't happening.
- **Name the timing that matters, not the method**: move a frozen fish to the
  fridge the night before; fresh meat keeps about four days, so buy it near the
  night it's cooked. That's planning, not a recipe.
- **Cooking with the kid** — a kit, a recipe card, a project — goes on a night
  the kid is home and there's time, and it's a good use of a slow day.

## 3. The rules she set

- **The shelf is probably wrong** (1 Oct 2026). Say *the shelf shows*, never
  *you have* or *you don't have*. An absence proves nothing; offer a missing
  ingredient as a maybe, with the caveat in the same breath.
- **Make the assumptions; don't ask what can be inferred** (28 Oct 2026, her
  words: *you can make those kind of assumptions*). Mom's chili is the frozen
  chili; the leftover steak is the one pulled out to thaw. When a guess is real,
  say it once, in a clause, and carry on.
- **Ask before giving a recipe** (25 Oct 2026). Naming a dish is not asking for
  one. Offer a link in one line; give it only on her yes. No recipe text is ever
  stored — ingredient names and the source link only.
- **Nutrition is qualitative, and only when she raises it**: vegetables, protein,
  variety, too much red meat. No calories, no macros, no score.
- **Her corrections go into the record as she says them**: a meal row that
  turns out to be leftovers, a feeling about who cooked (*I was actually proud of
  him for taking care of things*) — her words above the divider, carried forward
  verbatim with the rest.

## 4. The shopping list

**A shopping list is the supplies table filtered, never a second list**: the
wants, plus running low, plus what this plan adds.

- **Ask once before writing**, then write in one batch: new wants, and existing
  rows flipped back to want rather than duplicated (the old cilantro row becomes
  a want; no second cilantro row). Each new row carries her words above the
  divider and what it is for below it.
- **Store**: only one she named or one the row already carries. Group the list
  by what it's for — a night, a party, the everyday — then the staples that are
  probably gone, as *check first*.
- **Her own list lives in Google Keep, which no connector reaches.** When she
  pastes it in, match each line to the shelf before writing (a brand name to its
  row, a spelling she dictated to the product), say what was matched in one short
  list, and give back the whole merged list as plain lines in a code block, one
  item per line, ready to paste into a Keep note with checkboxes.

## 5. The order

- When she says she'll place an order, write one `🛒 grocery shopping` row,
  `⬜ intention`, targeted at the day she named (end of day when no time was
  said), her words above the divider. The pickup is a row of its own when it
  happens.
- **When the order lands**, ask for the receipt or the confirmation and bring the
  shelf up to date from it: what came in is on hand, added the pickup day.
- **Automating the order is a later step, not this skill.** The likely shape: be•do
  fills the cart in her own browser from the filtered list, and she picks the
  slot and pays. A cloud session can't reach the store's site; it needs a browser
  on her computer.

## 6. Coming back to it

A plan is revisited through the week — before the order, when a night changes,
after a dinner nobody planned. Each time, run the brief again rather than
working from the last table: the stream will show what was actually eaten, and
the plan follows it.

Name the chat with the chat-title skill: a meal plan is a query, not a drive, so
it carries no code (`▶️🍳 W45 dinners — week of 2 Nov`).
