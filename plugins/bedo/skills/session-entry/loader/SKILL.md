---
name: "session-entry"
description: "Write a be•do work-log entry for the current session straight to the stream, as an ⚡ action row. Use when the user asks to create a session entry, log the session, or write a be•do entry."
---

# session-entry — loader

**This skill carries no procedure of its own.** The procedure and the checks it
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

## 2. Follow `be-do-main/plugins/bedo/skills/session-entry/SKILL.md`

It is the real skill. Its checks run from the same download:

```
bash be-do-main/plugins/bedo/skills/bedo-checks/run_checks.sh stretches <the chat's record> --day YYYY-MM-DD --json
bash be-do-main/plugins/bedo/skills/bedo-checks/run_checks.sh entry row.json
```

**If the download fails, say so plainly in one line and stop.** Never fall back
to an older copy or to memory: the times come from the code, not from the
chat's open and close.
