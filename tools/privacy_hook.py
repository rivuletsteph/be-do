#!/usr/bin/env python3
"""privacy hook — the check runs before anything a chat writes to GitHub.

The pre-push hook covers what git pushes. What a chat writes through the GitHub
tools — a pull request's title and description, an edit to them, a comment, a
file or a branch made from the API — never passes through git, and that is how
a name reached the public repo (12 Nov 2026, her words: the privacy check only
scans repo files, so PR titles, descriptions and commit messages slip through).

Claude Code runs this before each of those tools (`.claude/settings.json`,
PreToolUse). It reads the tool call on stdin, checks every piece of text in it
with the privacy check's own names and patterns, and on a hit exits 2: the call
is refused, and the chat is told where the hit is, masked, so it can rewrite the
text and try again. Nothing has to be remembered.

    echo '{"tool_name": "…", "tool_input": {…}}' | python3 tools/privacy_hook.py
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import privacy_check as pc

# the parts of a call that only point at something: never written anywhere
POINTERS = {'owner', 'repo', 'sha', 'base', 'method', 'pullNumber', 'issue_number', 'state',
            'state_reason', 'draft', 'maintainer_can_modify', 'page', 'perPage', 'event'}
# the parts that are branch names, read as words
BRANCHES = {'branch', 'head', 'from_branch'}


def pieces(value, where=''):
    """Every string in the call that would be written to GitHub, with where it sits."""
    if isinstance(value, dict):
        for k, v in value.items():
            if k in POINTERS:
                continue
            yield from pieces(v, f'{where}.{k}' if where else k)
    elif isinstance(value, list):
        for n, v in enumerate(value):
            yield from pieces(v, f'{where}[{n}]')
    elif isinstance(value, str) and value.strip():
        yield where, value


def hits_in(tool_input, T):
    hits = []
    for where, text in pieces(tool_input):
        if where.rsplit('.', 1)[-1] in BRANCHES:
            pc.check(pc.branch_words(text), where, T, hits)
        else:
            pc.check(text, where, T, hits)
    return hits


def main(stdin=None):
    try:
        call = json.load(stdin or sys.stdin)
    except ValueError:
        return 0   # not a tool call: nothing to check
    tool_input = call.get('tool_input') or {}
    T = pc.terms()   # exits 2 itself when the live names are configured but unreadable
    hits = hits_in(tool_input, T)
    if not hits:
        return 0
    print(f"privacy check: {call.get('tool_name', 'this call')} refused — "
          f"{len(hits)} hit(s), masked. Rewrite the text without them and try again:", file=sys.stderr)
    for h in hits:
        print('  ' + h, file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main())
