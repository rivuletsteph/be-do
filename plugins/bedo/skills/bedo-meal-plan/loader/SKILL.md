---
name: "bedo-meal-plan"
description: "Plan a stretch of meals when the user opens it — a week of dinners, or only the next few nights on a minimal week — from what was actually eaten, who is home, what the shelf probably holds and the recipes they cook, then the shopping list it needs and the grocery order. Use when the user asks for a meal plan, to plan dinners or the week's meals, what to cook this week, or to get ready to order groceries. Never on a schedule."
---

# bedo-meal-plan — loader

**This skill carries no procedure of its own.** The procedure and the brief it
runs live in the version store, and this fetches them fresh every time, so it
never needs uploading again (backlog 261010a).

## 1. Download the version store

```
curl -sSL -o bedo.tar.gz https://codeload.github.com/rivuletsteph/be-do/tar.gz/refs/heads/main
tar -xzf bedo.tar.gz || { rm -rf be-do-main; git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main; }
```

In Cowork the tarball URL can come back as a JSON refusal instead of a tarball;
a plain `git clone` of the public repo works there, which is why the fallback is
in the same line.

## 2. Follow `be-do-main/plugins/bedo/skills/bedo-meal-plan/SKILL.md`

It is the real skill. Its brief runs from the same download:

```
python3 be-do-main/plugins/bedo/skills/bedo-meal-plan/scripts/meal_brief.py \
    --stream week.json [--stream last-week.json] --supplies supplies.json --recipes recipes.json --today YYYY-MM-DD
```

**If the download fails, say so plainly in one line and stop.** Never fall back
to an older copy or to memory: a plan read from a remembered shelf suggests food
that isn't in the house.
