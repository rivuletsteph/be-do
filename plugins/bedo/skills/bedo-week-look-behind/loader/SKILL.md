---
name: "bedo-week-look-behind"
description: "Build the be•do WEEK look behind — the Sunday-to-Saturday review page. Use when the user asks for the week look behind, the weekly review page, or to see the week just closed."
---

# bedo-week-look-behind — loader

**This skill carries no builder and no settings of its own.** The builder, the
page engine, the runner and the tests live in the version store; the settings
are the day behind's, read from Airtable (be•do system › settings). This
fetches them fresh every time, so it never needs uploading again.

## 1. Download the version store

```
curl -sSL -o bedo.tar.gz https://codeload.github.com/rivuletsteph/be-do/tar.gz/refs/heads/main
tar -xzf bedo.tar.gz || { rm -rf be-do-main; git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main; }
```

## 2. Follow `be-do-main/plugins/bedo/skills/bedo-week-look-behind/SKILL.md`

It is the real skill. The build is one command:

```
bash be-do-main/plugins/bedo/skills/bedo-week-look-behind/run_week_look_behind.sh [any day of the week]
```

**If the download or the build fails, say so plainly and stop.** Name what
failed in one line. Never fall back to an older copy.
