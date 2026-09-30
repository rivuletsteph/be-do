# -*- coding: utf-8 -*-
"""look_behind_log.py — which days still need their final look behind.

The morning routine builds yesterday, never today, and if it missed a day it
builds each missed day in order, oldest first, so the most recent day is built
last and is the one left on the living page. The record of what has been
built is the look behind's own log rows in the stream: a row whose [be•do]
block opens `[be•do] look behind YYYY-MM-DD · final` (words.py --row-block
--final writes that line). A day with a `· draft` row has the dusk build and
its words waiting, and no final yet; a day with no row at all has neither.

    python3 look_behind_log.py --today YYYY-MM-DD --local look_behind_local.json \\
        --stream data/w40.json [--stream data/w39.json] [--cap 3]

Prints JSON: each day from the cap back to yesterday with its state, and
`to_build`, oldest first. The cap is how many days back the routine looks —
three, unless told otherwise — because prep only fetches this week and last,
a day older than that has no rows to build from, and a week of missed pages
is a sign to ask rather than to catch up unattended. Days the fetched streams
cannot reach are named `unreachable` and never built.
"""
import argparse, datetime as dt, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bedo_common import read_dump, weekno  # noqa: E402
from words import parse_block  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--today', required=True, help="the user's local date when the routine fires")
    ap.add_argument('--local', required=True)
    ap.add_argument('--stream', action='append', required=True)
    ap.add_argument('--cap', type=int, default=3, help='how many days back to look (default 3)')
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    fs = L['fields']['stream']
    today = dt.date.fromisoformat(a.today)

    # the weeks the fetched dumps cover, from their file names (w40.json)
    weeks = set()
    for p in a.stream:
        n = os.path.basename(p).rsplit('.', 1)[0].lstrip('w')
        if n.isdigit():
            weeks.add(int(n))

    state = {}                     # day -> (state, row)
    for p in a.stream:
        for r in (read_dump(p) or {}).get('records') or []:
            c = r.get('cellValuesByFieldId') or {}
            W = parse_block(c.get(fs['details']))
            if not W:
                continue
            st = W['page']          # which build the row stands for, from its first line
            cur = state.get(W['day'])
            if not cur or (r.get('createdTime') or '') > cur[1]['created']:
                state[W['day']] = (st, dict(id=r['id'], key=c.get(fs.get('key')),
                                            created=r.get('createdTime') or ''))

    days, to_build = [], []
    for back in range(a.cap, 0, -1):
        d = today - dt.timedelta(days=back)
        wk = weekno(d, L['week_zero_sunday'], L['week_zero_number'])
        st, row = state.get(d.isoformat(), ('none', None))
        if weeks and wk not in weeks:
            st = 'unreachable'
        days.append(dict(day=d.isoformat(), week=wk, state=st, row=row))
        if st in ('none', 'draft'):
            to_build.append(d.isoformat())
    print(json.dumps(dict(today=a.today, yesterday=(today - dt.timedelta(days=1)).isoformat(),
                          cap=a.cap, days=days, to_build=to_build), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
