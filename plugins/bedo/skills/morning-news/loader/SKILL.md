---
name: "morning-news"
description: "The user's morning news roundup, published as a one-reader newspaper page: the places, topics and newsletters they follow, with photos. Use when the user asks for the morning news, the news, the paper, or what's new on any topic or place in their news settings."
---

# morning-news — loader

**This skill carries no procedure of its own.** The procedure, the page's
assets and its reference notes live in the version store, and this fetches
them fresh every time, so it never needs uploading again (backlog 261010a).

## 1. Download the version store

```
curl -sSL -o bedo.tar.gz https://codeload.github.com/rivuletsteph/be-do/tar.gz/refs/heads/main
tar -xzf bedo.tar.gz || { rm -rf be-do-main; git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main; }
```

In Cowork the tarball URL can come back as a JSON refusal instead of a tarball;
a plain `git clone` of the public repo works there, which is why the fallback is
in the same line.

## 2. Follow `be-do-main/plugins/bedo/skills/morning-news/SKILL.md`

It is the real skill. Its `assets` and `reference` folders are beside it in the
same download. What the reader follows (places, topics, newsletters) is never in
the repo: the skill reads it from the settings row it names.

**If the download fails, say so plainly in one line and stop.** Never fall back
to an older copy or to memory.
