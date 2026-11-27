# -*- coding: utf-8 -*-
"""The daily fold: the amendments worked down a little every day (23 Nov 2026,
her words: it would be nice if we could get into a daily amendment fold).

The weekly fold showed her a list on Sundays, and the pile grew between them:
on 23 Nov 2026, 72 rows were active and 50 of them named no check. This prints
one day's share, read live: what the mapping says has already landed (to be
marked folded once the evidence is seen on main), the last few days' new rows,
and the oldest few of the backlog. A scheduled Code session runs it every day
and does the work; `commands/fold.md` says what each line asks of it.

It reads; it never writes. The sizes are `fold.daily` in facts.json.

    python3 bedo_fold.py --live [--date YYYY-MM-DD] [--json]
    python3 bedo_fold.py --amendments amendments.json     # a read of the table, for a test or a chat with no token
"""
import argparse, datetime as dt, json

import bedo_rules
from bedo_reader import FACTS, load_local, offset_hours, read_dump


def today_of(L, now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    return (now + dt.timedelta(hours=offset_hours(L, now))).date().isoformat()


def made(recs, L, today):
    cfg, d = FACTS['fold'], FACTS['fold'].get('daily') or {}
    return bedo_rules.daily_fold(bedo_rules.active(recs, L), L.get('amendment_checks'), today, cfg['keep_active_words'],
                                 d.get('new_days', 7), d.get('backlog', 5), d.get('mark', 10))


def main(argv=None):
    ap = argparse.ArgumentParser(description='the daily fold: one day\'s share of the amendments')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--amendments', help='a read of the amendments table')
    ap.add_argument('--date', help='the day the fold is for; today, by her clock, when not given')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    if a.live:
        from bedo_air import Air
        base, table = L['bases']['amendments']
        recs = Air().records(base, table, by_id=bool(L.get('amendments_fields')))   # never a kept read: yesterday's marks must show
    elif a.amendments:
        recs = read_dump(a.amendments)['records']
    else:
        raise SystemExit('give --live or --amendments FILE')
    fold = made(recs, L, a.date or today_of(L))
    print(json.dumps(fold, ensure_ascii=False, indent=1) if a.json else '\n'.join(bedo_rules.daily_fold_lines(fold)))


if __name__ == '__main__':
    main()
