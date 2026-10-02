#!/usr/bin/env python3
"""privacy check — nothing personal goes into this public repo.

This repo is the generic engine. Everything specific to a person — names,
places, projects, ids, links, their words — lives in their own settings files
and bases, never here. This check enforces that on every push and pull request.

Two kinds of hit:
  · the private terms list — names, places and projects, read from
    $BEDO_PRIVATE_TERMS (one per line; a repo secret in CI) or from
    ~/.bedo/private_terms.txt. The list itself is never committed, and a hit is
    printed masked, so the check never writes a private word into a public log.
  · patterns anyone's data has — Airtable ids, real email addresses, artifact,
    Drive and Docs links, calendar ids.

    python3 tools/privacy_check.py              # every tracked file, as it is now
    python3 tools/privacy_check.py --diff BASE  # lines added and commit messages since BASE
    python3 tools/privacy_check.py --history    # every version of every file, every message

Exit 1 on any hit.
"""
import os, re, subprocess, sys

PATTERNS = [
    ('airtable id', re.compile(r'\b(?:app|tbl|fld|rec|viw|sel|usr|wsp)[A-Za-z0-9]{14}\b')),
    ('email', re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b')),
    ('artifact link', re.compile(r'claude\.ai/(?:code/)?artifact/[\w-]{8,}')),
    ('drive or docs link', re.compile(r'(?:drive|docs)\.google\.com/\S+')),
    ('calendar event link', re.compile(r'google\.com/calendar/event\?eid=\w+')),
]
# placeholders the tests and examples use on purpose
ALLOW = re.compile(r'^(?:me|you|kid|fam|someone|user|name|example|test|noreply)@'
                   r'|@(?:example\.(?:com|org)|anthropic\.com|users\.noreply\.github\.com)$'
                   r'|@group(?:\.v)?\.calendar\.google\.com$|^\w@'
                   r'|^(?:fld|tbl|app|rec)X+$', re.I)
SKIP = ('tools/privacy_check.py',)


def terms():
    raw = os.environ.get('BEDO_PRIVATE_TERMS')
    if raw is None:
        p = os.path.expanduser('~/.bedo/private_terms.txt')
        raw = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
    ts = sorted({t.strip() for t in raw.replace(',', '\n').splitlines() if len(t.strip()) >= 3},
                key=len, reverse=True)
    if not ts:
        print('privacy check: no private terms list — checking patterns only', file=sys.stderr)
    return [(t, re.compile(r'(?<![\w])' + re.escape(t) + r'(?![\w])', re.I)) for t in ts]


def mask(s):
    return s[0] + '·' * (len(s) - 1)


def check(text, where, T, hits):
    for n, line in enumerate(text.splitlines(), 1):
        if 'privacy: ok' in line:   # a made-up value in a test, marked by hand and reviewed
            continue
        for t, rx in T:
            if rx.search(line):
                hits.append(f'{where}:{n}: private term {mask(t)}')
        for name, rx in PATTERNS:
            for m in rx.finditer(line):
                if not ALLOW.search(m.group(0)):
                    hits.append(f'{where}:{n}: {name} {mask(m.group(0))}')


def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True, check=True).stdout


def main():
    a = sys.argv[1:]
    T, hits = terms(), []
    if a[:1] == ['--diff']:
        base = a[1]
        for line_no, line in enumerate(git('diff', '-U0', f'{base}...HEAD', '--', '.', *[f':!{s}' for s in SKIP]).splitlines()):
            if line.startswith('+') and not line.startswith('+++'):
                check(line[1:], f'diff+{line_no}', T, hits)
        for sha in git('rev-list', f'{base}..HEAD').split():
            check(git('log', '-1', '--format=%B', sha), f'commit {sha[:7]}', T, hits)
    elif a[:1] == ['--history']:
        seen = set()
        for row in git('rev-list', '--all', '--objects').splitlines():
            sha, _, path = row.partition(' ')
            if not path or path in SKIP or sha in seen:
                continue
            seen.add(sha)
            if git('cat-file', '-t', sha).strip() != 'blob':
                continue
            try:
                check(git('cat-file', 'blob', sha), f'{path}@{sha[:7]}', T, hits)
            except (subprocess.CalledProcessError, UnicodeDecodeError):
                continue
        for sha in git('rev-list', '--all').split():
            check(git('log', '-1', '--format=%B', sha), f'commit {sha[:7]}', T, hits)
    else:
        for path in git('ls-files').splitlines():
            if path in SKIP:
                continue
            try:
                check(open(path, encoding='utf-8').read(), path, T, hits)
            except (UnicodeDecodeError, FileNotFoundError):
                continue
    for h in hits:
        print(h)
    print(f'privacy check: {len(hits)} hit(s)', file=sys.stderr)
    sys.exit(1 if hits else 0)


if __name__ == '__main__':
    main()
