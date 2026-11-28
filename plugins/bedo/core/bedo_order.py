# -*- coding: utf-8 -*-
"""Where each flow practice usually falls — her predicted order, observed from
her own rows, never declared (A237).

  dawn  minutes after the day's 😶 wake row. The wake moves and the sequence
        does not, so a 5:24 and a 7:30 morning sort the same. Written 'wake+25'.
        The ORDER is predicted from which step came before which on each
        morning, the latest mornings counting most (half-life HALF_LIFE days),
        and the minutes are then fitted to that order (20 Nov 2026, her words:
        updating the order of the dawn flow and getting predictive). A median
        alone let one slow morning reorder the list, and a catch-up (several
        rows logged in the same minutes, after the fact) says nothing about
        which came first, so it never counts as the later one.
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
HALF_LIFE = 7                                  # days: a morning a week back counts half as much
CATCH_UP = (3, 2)                              # 3+ dawn rows within 2 minutes were logged after the fact


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


def mornings(rows, cat, loc):
    """{date: {norm(practice): minutes after that day's wake}} for the dawn
    steps, the first lived time of each, from mornings with a wake row."""
    dawn = {RL.norm(s['practice']) for s in RL.flow_steps(cat, 'dawn')}
    wake, seen = {}, {}
    for r in rows:
        if r.get('status') not in LOGS or not r.get('datetime') or not r.get('practice'):
            continue
        p, t = RL.norm(r['practice']), local(r['datetime'], loc)
        if p == RL.norm(WAKE):
            wake[t.date()] = min(wake.get(t.date(), t), t)
        elif p in dawn:
            d = seen.setdefault(t.date(), {})
            d[p] = min(d.get(p, t), t)
    out = {}
    for d, items in seen.items():
        if d in wake:
            m = {p: (t - wake[d]).total_seconds() / 60 for p, t in items.items()}
            m = {p: v for p, v in m.items() if 0 <= v <= _DAWN_LATEST}
            if m:
                out[d] = m
    return out


def catch_up(morning, n=CATCH_UP[0], within=CATCH_UP[1]):
    """The steps of one morning that sit in a catch-up: n or more rows logged
    within a couple of minutes of each other. Each was done by then, not then."""
    return {p for p, t in morning.items() if sum(abs(u - t) <= within for u in morning.values()) >= n}


def before(days, half_life=HALF_LIFE):
    """{(a, b): weight of the mornings a came before b}. The newest morning
    weighs 1 and older ones halve every half_life days. b in a catch-up never
    counts as coming after: it may have been done long before it was logged."""
    if not days:
        return {}
    newest = max(days)
    win = {}
    for d, m in days.items():
        w = 0.5 ** ((newest - d).days / half_life)
        late = catch_up(m)
        for a, ta in m.items():
            for b, tb in m.items():
                if ta < tb and b not in late:
                    win[(a, b)] = win.get((a, b), 0) + w
    return win


def rank(names, win):
    """names in predicted order: by the share of head-to-heads each wins, then
    any neighbour the other beats more often moves ahead of it."""
    def share(a):
        v = [win.get((a, b), 0) / (win.get((a, b), 0) + win.get((b, a), 0))
             for b in names if b != a and win.get((a, b), 0) + win.get((b, a), 0) > 0]
        return sum(v) / len(v) if v else 0.5
    out = sorted(names, key=lambda a: (-share(a), a))
    for _ in range(len(out)):                   # bounded: a cycle (a>b>c>a) can't spin forever
        moved = False
        for i in range(len(out) - 1):
            a, b = out[i], out[i + 1]
            if win.get((b, a), 0) > win.get((a, b), 0):
                out[i], out[i + 1] = b, a
                moved = True
        if not moved:
            break
    return out


def fit(values):
    """The nearest non-decreasing run to values (pool adjacent violators),
    then a minute apart, so the minutes written sort in the predicted order."""
    blocks = []
    for v in values:
        blocks.append([v, 1])
        while len(blocks) > 1 and blocks[-2][0] > blocks[-1][0]:
            (a, n), (b, k) = blocks[-2], blocks.pop()
            blocks[-1] = [(a * n + b * k) / (n + k), n + k]
    out = [v for v, n in blocks for _ in range(n)]
    for i in range(1, len(out)):
        out[i] = max(out[i], out[i - 1] + 1)
    return out


def write(flow, minutes):
    m = round(minutes)
    return f'wake+{m}' if flow == 'dawn' else f'{m // 60 % 24:02d}:{m % 60:02d}'


def typical(rows, cat, loc, floor=FLOOR, half_life=HALF_LIFE):
    """[(catalog row, new value or None, observations)] for every flow step.
    Dawn values follow the predicted order (rank, then fit); dusk is the
    median clock time."""
    obs = observe(rows, cat, loc)
    med = {p: statistics.median(v) for p, v in obs.items() if len(v) >= floor}
    wake = RL.norm(WAKE)
    sure = [p for p in med if p != wake and p in {RL.norm(s['practice']) for s in RL.flow_steps(cat, 'dawn')}]
    order = rank(sure, before(mornings(rows, cat, loc), half_life))
    dawn = dict(zip(order, fit([med[p] for p in order])))
    if wake in med:
        dawn[wake] = 0
    out = []
    for flow in ('dawn', 'dusk'):
        for s in RL.flow_steps(cat, flow):
            p = RL.norm(s['practice'])
            v = obs.get(p, [])
            m = dawn.get(p) if flow == 'dawn' else med.get(p)
            out.append((s, write(flow, m) if m is not None else None, len(v)))
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
    res.sort(key=lambda x: (x[0].get('phase') != RL.FLOWS['phase']['dawn'],
                            RL.typical_minutes(x[1]) is None, RL.typical_minutes(x[1]) or 0))
    for s, v, n in res:
        print(f"  {v or '—':>8}  n={n:<2} {s['practice']}" + ('' if v else '  (too few to say)'))


if __name__ == '__main__':
    main()
