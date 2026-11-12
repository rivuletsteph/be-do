# -*- coding: utf-8 -*-
"""The inbox rules, run at the 📧 clear gmail inbox before anything is
archived, so a sweep can't forget them:

  keep     an automatic keep, like a star: a thread from someone on her keep
           list always gets a line on the one list and is never archived (26
           Oct 2026: anything from her husband is important)
  archive  a sender archived by default, kept only when the thread is about
           what she cares about there (25 Oct 2026: a club's mail, unless
           it's about the one thing she follows there)
  nudge    before anything is archived, one line asks her to glance through
           the inbox herself, with the count and the link, and archiving waits
           for her go (22 Oct 2026)

The senders are hers, in facts_local under `inbox`, never here:

    "inbox": {"keep_from": {"a name": ["…@…"]},
              "archive_unless": [{"name": "…", "from": ["…"], "keep_words": ["…"]}]}

    python3 bedo_inbox.py threads.json [--archive planned.json]

`threads.json` is the Gmail connector's search_threads result as it came.
`planned.json` is the thread ids the sweep means to archive: a keep among them
is a FIX. Exit 0 when it passes, 1 when there is a FIX.
"""
import json, sys

from bedo_reader import FACTS, load_local, read_dump

IN = FACTS['inbox']


def threads_of(read):
    if isinstance(read, list):
        return read
    return (read or {}).get('threads') or []


def _msgs(t):
    return t.get('messages') or [t]


def _senders(t):
    return [(m.get('sender') or m.get('from') or '').lower() for m in _msgs(t)]


def _text(t):
    return ' '.join(f'{m.get("subject") or ""} {m.get("snippet") or ""}' for m in _msgs(t)).lower()


def subject(t):
    return next((m.get('subject') for m in _msgs(t) if m.get('subject')), '') or '(no subject)'


def classify(t, rules):
    """('keep' | 'archive' | None, why). A keep wins over an archive."""
    senders = _senders(t)
    for who, addrs in (rules.get('keep_from') or {}).items():
        if any(a.lower() in s for a in addrs for s in senders):
            return 'keep', f'from {who} — an automatic keep'
    text = _text(t)
    for r in rules.get('archive_unless') or []:
        if any(f.lower() in s for f in r.get('from') or [] for s in senders):
            hit = next((w for w in r.get('keep_words') or [] if w.lower() in text), None)
            if hit:
                return 'keep', f'{r.get("name", "this sender")} about {hit}'
            return 'archive', f'{r.get("name", "this sender")} — archive by default'
    return None, None


def check(threads, rules, planned=None):
    """{keeps, archives, fixes, nudge}. `planned` is the ids the sweep means to
    archive; without it, the rule's archives are what would go."""
    keeps, archives = [], []
    for t in threads:
        kind, why = classify(t, rules)
        if kind == 'keep':
            keeps.append((t.get('id'), why, subject(t)))
        elif kind == 'archive':
            archives.append((t.get('id'), why, subject(t)))
    kept = {k[0] for k in keeps}
    fixes = [f'{why}: “{s[:60]}” is planned for the archive — take it out; it gets a line on the one list'
             for i, why, s in keeps if planned is not None and i in set(planned)]
    n = len(set(planned) - kept) if planned is not None else len(archives)
    nudge = IN['nudge'].format(n=n, link=IN['link']) if n else None
    return {'keeps': keeps, 'archives': archives, 'fixes': fixes, 'nudge': nudge}


def render(res, n):
    out = [f'inbox · {n} thread(s) read']
    if res['keeps']:
        out.append(f'automatic keeps ({len(res["keeps"])}) — a line each on the one list, never archived')
        out += [f'  · {why} · {s[:70]}' for _, why, s in res['keeps']]
    if res['archives']:
        out.append(f'archive by her rule ({len(res["archives"])})')
        out += [f'  · {why} · {s[:70]}' for _, why, s in res['archives']]
    out += ['FIX   ' + f for f in res['fixes']]
    if res['nudge']:
        out.append('before archiving, say in one line: ' + res['nudge'])
        out.append('archive only on her go')
    return '\n'.join(out)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the inbox rules: automatic keeps, archive by rule, the nudge')
    ap.add_argument('threads')
    ap.add_argument('--archive', help='a JSON list of the thread ids the sweep means to archive')
    a = ap.parse_args(argv)
    L = load_local()
    ts = threads_of(read_dump(a.threads))
    planned = json.load(open(a.archive, encoding='utf-8')) if a.archive else None
    res = check(ts, L.get('inbox') or {}, planned)
    print(render(res, len(ts)))
    sys.exit(1 if res['fixes'] else 0)


if __name__ == '__main__':
    main()
