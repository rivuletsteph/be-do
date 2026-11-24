# -*- coding: utf-8 -*-
"""The day sweep: every row of a day through the entry check, after the fact.

Rows go through the entry check, whoever writes them (J17). A row Duet writes
in passing reaches the stream without it: its setup can't run the checks, and
a Code session per capture would be too slow (24 Nov 2026, her yes). So the
check comes to the rows: one read of the day, each row through the same rules
`entry` applies before a write, and two short lists.

  be•do's   what the rules deduce by themselves (an empty device, wellness or
            person, printed as `field: empty → value` or `empty — deduced value`): the session writes the
            value in place, through the connector
  hers      anything a rule can't settle: a status or choice the base doesn't
            carry, a key out of shape, a time that can't be right

It runs at the dusk close, before `dayqa`, and on call. It reads; it never
writes. A row checked as it was written prints nothing.

    python3 bedo_sweep.py --live [--date YYYY-MM-DD] [--json]
    python3 bedo_sweep.py --day day.json [--catalog practices.json] [--date YYYY-MM-DD]
"""
import argparse, datetime as dt, json, re, sys

from bedo_entry import problems, week_number
from bedo_reader import as_rows, complete, load_local, offset_hours, on_day
import bedo_fill as FL

# rules about the moment of writing say nothing about a row already in the stream
# (the base fills a key on every row, so `only an action row carries a key` is true of none of them here)
_AT_WRITE = re.compile(r'^(key: .*already|key: not checked|key: only an |base: )')
_DEDUCED = re.compile(r'^\w[\w ]*: empty (→|— deduced) ')


def names(L):
    return {**{k: k for k in ('datetime', 'end', 'time_spent', 'status', 'practice', 'title', 'key', 'details',
                              'phase', 'wellness', 'emotion', 'attention', 'device', 'rhythm', 'person', 'mentioned')},
            **(L.get('stream_fields') or {})}


def shape(row):
    """A row as `entry` takes it: emotion is a list."""
    e = row.get('emotion')
    if isinstance(e, list):
        e = [x.get('name') if isinstance(x, dict) else x for x in e]
    elif e:
        e = [e]
    return dict(row, emotion=e or [])


def sweep(rows, L, base_name=None, catalog=None, now=None):
    """[(row, be•do's fixes, hers)] for each row with something to fix, in time order."""
    now = now or dt.datetime.now(dt.timezone.utc)
    off = offset_hours(L, now)
    rows = [shape(r) for r in rows]
    fill = FL.Context(catalog=FL.catalog_wellness(catalog, L) if catalog else None, day_rows=rows, local=L,
                      flows=FL.catalog_flows(catalog, L) if catalog else None)
    out = []
    for r in sorted(rows, key=lambda r: r.get('datetime') or ''):
        found = [p for p in problems(r, base_name, off, L.get('weekly_name', 'w{n} be•do'), fill=fill,
                                     self_name=L.get('self_person'), now=now)
                 if not _AT_WRITE.match(p)]
        if found:
            out.append((r, [p for p in found if _DEDUCED.match(p)], [p for p in found if not _DEDUCED.match(p)]))
    return out


def report(found, n, day, base=None):
    where = f' in {base}' if base else ''
    if not found:
        return [f'sweep  {day:%a} {day.day} {day:%b}: {n} rows{where}, every one passes the entry check']
    mine = sum(1 for _, a, _h in found if a)
    hers = sum(1 for _, _a, h in found if h)
    out = [f'sweep  {day:%a} {day.day} {day:%b}: {n} rows{where}, {len(found)} to fix ({mine} be•do writes in place, {hers} need a call)']
    for r, a, h in found:
        out.append(f'  {(r.get("title") or r.get("practice") or "?")[:70]} · {r["id"]}')
        out += [f'      be•do  {p}' for p in a] + [f'      FIX    {p}' for p in h]
    out.append('       write each deduced value in place through the connector; put the FIX lines on her dusk list')
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="the day sweep: a day's rows through the entry check, after the fact")
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--day', help="a complete read of the day's rows")
    ap.add_argument('--catalog', help='a read of the practices catalog')
    ap.add_argument('--date', help='the day, YYYY-MM-DD; today when left out')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    now = dt.datetime.now(dt.timezone.utc)
    day = dt.date.fromisoformat(a.date) if a.date else (now + dt.timedelta(hours=offset_hours(L, now))).date()
    base = None
    if a.live:
        from bedo_air import Air, read_catalog, read_day
        air = Air()
        src, base = read_day(air, L, day)
        rows, cat = as_rows(src['records'], names(L)), read_catalog(air, L)['records']
    elif a.day:
        rows = on_day(as_rows(complete(a.day, 'day'), names(L)), day, L)
        cat = complete(a.catalog, 'catalog') if a.catalog else None
        base = L.get('weekly_name', 'w{n} be•do').format(n=week_number(day))
    else:
        sys.exit('give --live or --day FILE')
    found = sweep(rows, L, base, cat, now)
    if a.json:
        print(json.dumps([dict(id=r['id'], title=r.get('title'), bedo=x, hers=h) for r, x, h in found], ensure_ascii=False, indent=1))
    else:
        print('\n'.join(report(found, len(rows), day, base)))


if __name__ == '__main__':
    main()
