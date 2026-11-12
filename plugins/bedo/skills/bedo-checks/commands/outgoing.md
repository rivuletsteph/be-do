# `outgoing`

**When:** before every push, before a pull request is opened, and before its title or description is edited

**Command:** `outgoing --title "TITLE" --text pr.md`, from inside the be-do clone (`BEDO_REPO` points at it from anywhere else)

Her words, 12 Nov 2026: *the privacy check only scans repo files, so PR titles, descriptions and commit messages slip through.* A name had reached two pull request descriptions, and GitHub keeps every edit of a description, so rewriting it later never takes it back. **What the public sees is checked before it is public.**

One run checks what leaves: every file, the lines and commit messages since `origin/main` and their author emails, this branch's name, and the PR's own title and description. Write the description to a file first (`pr.md` in the scratchpad), then run this, then open or edit the PR with **exactly that text**. A push without a PR needs no `--title` or `--text`.

- `0 hit(s)`: go ahead.
- A hit names where it is, masked (`title`, `text pr.md:4`, `commit 1a2b3c4`, `branch name c·····`). Rewrite that part — a role (her son, a neighbour), never the name — and run it again. Never paste the masked word, or a guess at it, into anything public.
- A hit in a commit message or a branch name on a branch nobody has pushed yet: amend or rename before the push. Once pushed, it's the session's own branch: fix it on a new branch and say so; never rewrite someone else's history, or main's.
- `could not read the live names` (exit 2): nothing goes out. Say so in one line; the push and the PR wait.

**It also runs on its own, as a backstop.** In a Claude Code session on this repo, `.claude/settings.json` runs the same check before every GitHub tool that writes (a PR opened or edited, a comment, a file or branch made from the API) and refuses the call on a hit; the pre-push hook checks branch names; and the privacy workflow checks a PR's title, description and branch on every edit. Running `outgoing` first is still the step: a refused call costs a turn, and the workflow only sees text once it is already public.
