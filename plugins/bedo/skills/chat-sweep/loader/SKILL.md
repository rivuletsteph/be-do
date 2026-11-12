---
name: "chat-sweep"
description: "Run the be•do chat sweep on its own, any day: every open chat checked against its objective, ☑️ chats archived, a session entry made sure of, and the open ones given their next step or hang-up for her to decide. Then the drive cleanup's next drive. Use when the user asks to sweep, clean up or archive her chats, close old chats, or check which chats are finished."
---

# chat-sweep — loader

**This skill carries no procedure of its own.** The procedure and the checks it
runs live in the version store, and this fetches them fresh every time, so it
never needs uploading again (backlog 261010a).

## 1. Download the version store

```
curl -sSL -o bedo.tar.gz https://codeload.github.com/rivuletsteph/be-do/tar.gz/refs/heads/main
tar -xzf bedo.tar.gz || { rm -rf be-do-main; git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main; }
```

## 2. Follow `be-do-main/plugins/bedo/skills/chat-sweep/SKILL.md`

It is the real skill. Its checks run from the same download:

```
bash be-do-main/plugins/bedo/skills/bedo-checks/run_checks.sh chats --sessions mine.json
bash be-do-main/plugins/bedo/skills/bedo-checks/run_checks.sh cleanup --drives 2
```

**If the download fails, say so plainly in one line and stop.** Never fall back
to an older copy or to memory.
