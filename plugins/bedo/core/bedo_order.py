# -*- coding: utf-8 -*-
"""Where each flow practice usually falls — her predicted order, observed from
her own rows, never declared (A237).

  dawn  minutes after the day's 😶 wake row. The wake moves and the sequence
        does not, so a 5:24 and a 7:30 morning sort the same. Written 'wake+25'.
  dusk  clock time, local, her word 4 Oct 2026. After midnight counts as late
        that night, not early. Written '20:40'.

A practice needs FLOOR observations before it gets a median; below that it
keeps none and the list falls back to the catalog's order. The result goes in
the catalog's `typical time` field, so a chat sorts from one field and never
reads weeks of history. It is refreshed at the weekly close — this prints the
updates, and the chat writes them with the connector.

    python3 bedo_order.py --live [--weeks 3]       # the last weeks' bases, by name
    python3 bedo_order.py --stream w41.json --stream w40.json --catalog practices.json
"""
import datetime as dt, json, statistics, sys

from bedo_reader import FACTS, as_rows, load_local, merge_live_first, offset_hours
import bedo_remaining as RL

FLOOR = 3
LOGS = set(FACTS['status']['logs'])            # ● ◉ ⨂ — what was lived, not planned
WAKE = '😶 wake'
_DUSK_EARLIEST = 12 * 60                       # a dusk row filed the next morning is not its time
_DAWN_LATEST = 12 * 60                         # a dawn row half a day after waking is a late entry


def local(s, loc):
    t = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    return t + dt.timedelta(hours=offset_hours(loc, t))


def observe(rows, cat, loc):
    """{norm(practice): [minutes, …]} for the dawn and dusk flow steps."""
    dawn = {RL.norm(s['practice']) for s in RL.flow_steps(cat, 'dawn')}
    dusk = {RL.norm(s['practice']) for s in RL.flow_steps(cat, 'dusk')}
    days, wake = {}, {}
    for r in rows:
        if r.get('status') not in LOGS or not r.get('datetime') or not r.get('practice'):
            continue
        t = local(r['datetime'], loc)
        days.setdefault(t.date(), []).append((RL.norm(r['practice']), t))
        if RL.norm(r['practice']) == RL.norm(WAKE):
            wake[t.date()] = min(wake.get(t.date(), t), t)
    out = {}
    for d, items in days.items():
        for p, t in items:
            if p in dawn and d in wake:
                m = (t - wake[d]).total_seconds() / 60
                if 0 <= m <= _DAWN_LATEST:
                    out.setdefault(p, []).append(m)
            elif p in dusk:
                m = t.hour * 60 + t.minute + (1440 if t.hour < 5 else 0)
                if m >= _DUSK_EARLIEST:
                    out.setdefault(p, []).append(m)
    return out


def write(flow, minutes):
    m = round(minutes)
    return f'wake+{m}' if flow == 'dawn' else f'{m // 60 % 24:02d}:{m % 60:02d}'


def typical(rows, cat, loc, floor=FLOOR):
    """[(catalog row, new value or None, observations)] for every flow step."""
    obs = observe(rows, cat, loc)
    out = []
    for flow in ('dawn', 'dusk'):
        for s in RL.flow_steps(cat, flow):
            v = obs.get(RL.norm(s['practice']), [])
            out.append((s, write(flow, statistics.median(v)) if len(v) >= floor else None, len(v)))
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='her predicted order, observed')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--weeks', type=int, default=3)
    ap.add_argument('--stream', action='append', default=[], help='a complete read of a weekly base, live first')
    ap.add_argument('--catalog')
    ap.add_argument('--json', action='store_true', help='print the catalog updates for the connector')
    a = ap.parse_args(argv)
    L = load_local()
    fields = {**{k: k for k in ('datetime', 'status', 'practice')}, **L.get('stream_fields', {})}
    if a.live:
        from bedo_air import Air, read_catalog
        from bedo_entry import week_number
        air = Air()
        names = air.bases()
        now = dt.datetime.now(dt.timezone.utc)
        n = week_number((now + dt.timedelta(hours=offset_hours(L, now))).date())
        wanted = [L.get('weekly_name', 'w{n} be•do').format(n=k) for k in range(n, n - a.weeks, -1)]
        sources = [air.dump(names[w], L['stream_table'], by_id=True) for w in wanted if w in names]
        cat_src = read_catalog(air, L)
    else:
        if not (a.stream and a.catalog):
            sys.exit('give --live, or --stream (one or more) and --catalog')
        sources, cat_src = a.stream, a.catalog
    recs, reads = merge_live_first(sources)                      # I15: each record once, live first
    rows = as_rows(recs, fields)
    cat = RL.catalog(cat_src, L.get('practices_fields'))
    res = typical(rows, cat, L)
    field = (L.get('practices_fields') or FACTS['catalog_fields'])['typical_time']
    updates = [{'id': s['id'], 'fields': {field: v}} for s, v, _ in res if v and v != s.get('typical_time')]
    if a.json:
        print(json.dumps(updates, ensure_ascii=False))
        return
    print(f'{len(rows)} rows from {len(reads)} reads · {len(updates)} to write')
    for s, v, n in res:
        print(f"  {v or '—':>8}  n={n:<2} {s['practice']}" + ('' if v else '  (too few to say)'))


if __name__ == '__main__':
    main()
