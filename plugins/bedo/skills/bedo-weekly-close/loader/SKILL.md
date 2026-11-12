---
name: "bedo-weekly-close"
description: "Run the be•do weekly close and the Monday plan. Use when the user says it's Sunday, asks to close the week, run the weekly review, do the split, or plan the week ahead."
---

# bedo-weekly-close — loader

**This skill carries no procedure of its own.** The procedure and the close script
live in the version store, and this fetches them fresh every time.

```
curl -sSL -o bedo.tar.gz https://codeload.github.com/rivuletsteph/be-do/tar.gz/refs/heads/main
tar -xzf bedo.tar.gz || { rm -rf be-do-main; git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main; }
```

Then follow `be-do-main/plugins/bedo/skills/bedo-weekly-close/SKILL.md`.

**If the download fails, say so plainly in one line and stop.** Never fall back to
an older copy or to memory.
