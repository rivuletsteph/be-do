# -*- coding: utf-8 -*-
"""Open pull requests, brought back to her (27 Nov 2026, her words: why on earth are these not getting merged? … each of
those merges needed to happen for a reason).

Every build chat ended by asking "merge pull request N?" in that chat; when she didn't answer there, nothing asked again,
and main moved on until seven pull requests, up to two weeks old, no longer merged. This reads the open ones (the GitHub
connector's `list_pull_requests`, state open, saved as it came) and prints each with its age and be•do's one
recommendation. Each was made because she asked for something, so the default is to bring it in: merge it when it still
merges, or bring it onto main and merge it when it doesn't. Closing one is hers to say, never the default.

    python3 bedo_prs.py prs.json [--today YYYY-MM-DD] [--json]

A pull request whose `mergeable_state` says it clashes (dirty) is named so; any other state is read as mergeable, and the
session checks with a trial merge before it acts. Her yes or no on the printed list is the whole of her part.
"""
import argparse, datetime as dt, json, sys

STALE_DAYS = 1      # older than a day without her answer is stranded


def rows(prs, today):
    out = []
    for p in prs:
        made = dt.date.fromisoformat(str(p.get('created_at') or '')[:10]) if p.get('created_at') else today
        age = (today - made).days
        clash = (p.get('mergeable_state') or '').lower() == 'dirty'
        rec = 'bring it onto main, then merge' if clash else 'merge'
        out.append(dict(n=p.get('number'), title=p.get('title') or '', age=age, clash=clash, rec=rec,
                        stranded=age > STALE_DAYS, url=p.get('html_url') or ''))
    return sorted(out, key=lambda r: -r['age'])


def report(rs):
    if not rs:
        return 'prs    none open'
    old = sum(r['stranded'] for r in rs)
    lines = [f'prs    {len(rs)} open' + (f', {old} waiting more than a day for her yes' if old else '')
             + ' · each was made for a reason she gave: bring it in unless she says close']
    for r in rs:
        lines.append(f"  #{r['n']} {r['title']} · {r['age']} d{' · clashes with main' if r['clash'] else ''} → {r['rec']}?")
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description='open pull requests, each with its age and one recommendation')
    ap.add_argument('prs')
    ap.add_argument('--today')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    data = json.load(open(a.prs, encoding='utf-8'))
    prs = data if isinstance(data, list) else data.get('pull_requests') or data.get('items') or []
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    rs = rows(prs, today)
    print(json.dumps(rs, ensure_ascii=False) if a.json else report(rs))


if __name__ == '__main__':
    sys.exit(main())
