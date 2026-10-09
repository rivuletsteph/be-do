# -*- coding: utf-8 -*-
"""The week look behind, by drive — the first cut (9 Oct 2026).

One week, Sunday 00:00 to the next Sunday 00:00, local. Per drive: the time
logged on it, the actions it closed, and what is still open at the week's end.
Drives within drives: a row counts under its own drive and every drive it feeds,
the child nested under its parent; the headline counts each row once
(plugins/bedo/core/bedo_drives.py). The rest of the week page (the reading, the
wheel, the body, who was there …) is not built yet — see SKILL.md.

Nothing about the person lives here: the field ids, the offset and the week
anchor come from the day behind's settings file, look_behind_local.json.

    python3 week_look_behind.py --week 2026-09-27 --local look_behind_local.json \\
      --stream w40.json --stream w39.json --rhythms rhythms.json \\
      --template week_look_behind_engine.html --out week.html
"""
import argparse, datetime as dt, json, os, re, sys

# The core lives in plugins/bedo/core; a runner may copy it beside this file. Beside wins.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, '..', '..', '..', 'core'), _HERE):
    sys.path.insert(0, os.path.normpath(_p))
import bedo_reader  # noqa: E402
import bedo_drives  # noqa: E402

STREAM_KEYS = ('title', 'key', 'when', 'end', 'status', 'rhythm')
OPTIONAL_STREAM_KEYS = ('spent', 'deliv', 'target')
RHYTHM_KEYS = ('name',)
OPTIONAL_RHYTHM_KEYS = ('emoji', 'type', 'status', 'code', 'feeds')
ST = bedo_reader.FACTS['status']
DONE = ST['closed'][0]                                   # ✅ done
OPEN = set(ST['open'])                                   # ▫️ ⬜ ▶️
NOT_LIVED = set(ST['plans']) | {ST['actions'][4], ST['logs'][2]}   # ▫️ ⬜ ✖️ ⨂: never happened
MAX_SPAN = dt.timedelta(hours=bedo_reader.FACTS['entry_rules']['max_span_hours'])
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MARK = chr(0x1684E)                                      # be•do's mark, by codepoint


def die(msg):
    sys.exit('ABORT: ' + msg)


def sv(v):
    return v.get('name') if isinstance(v, dict) else v


def fields(L):
    got = L.get('fields') or {}
    F = {k: got.get('stream', {}).get(k) for k in STREAM_KEYS + OPTIONAL_STREAM_KEYS}
    RF = {k: got.get('rhythms', {}).get(k) for k in RHYTHM_KEYS + OPTIONAL_RHYTHM_KEYS}
    missing = [f'stream.{k}' for k in STREAM_KEYS if not F[k]] + [f'rhythms.{k}' for k in RHYTHM_KEYS if not RF[k]]
    if missing:
        die('local settings: fields.' + ', fields.'.join(missing) + ' missing')
    for k in ('utc_offset_hours', 'week_zero_sunday', 'week_zero_number'):
        if L.get(k) in (None, ''):
            die(f'local settings: {k} is missing')
    return {k: v for k, v in F.items() if v}, {k: v for k, v in RF.items() if v}


def load(paths, F):
    """Deduped by record id, live base first (I15); chains by key (I5)."""
    seen, reads = {}, []
    for p in paths:
        recs = bedo_reader.complete(p)
        reads.append((os.path.basename(p).rsplit('.', 1)[0], len(recs)))
        for r in recs:
            if r['id'] in seen:
                continue
            c = bedo_reader.cells(r)
            row = {k: (c.get(v) if k == 'spent' else sv(c.get(v))) for k, v in F.items()}
            row.update(id=r['id'], created=r.get('createdTime') or '')
            row['rhythm'] = ((row.get('rhythm') or '').split(',')[0]).strip()
            seen[r['id']] = row
    return list(seen.values()), reads


def load_rhythms(path, RF):
    recs = bedo_reader.complete(path)
    out = {}
    for r in recs:
        c = bedo_reader.cells(r)
        row = {k: (c.get(v) if k == 'feeds' else sv(c.get(v))) for k, v in RF.items()}
        row['feeds'] = bedo_drives.feeds_of(row)
        if row.get('name'):
            out[row['name']] = row
    return out, len(recs)


def build(rows, rhythms, start, L):
    """Everything the page counts, from rows already deduped."""
    off = dt.timedelta(hours=L['utc_offset_hours'])
    end = start + dt.timedelta(days=7)

    def local(ts):
        if not ts:
            return None
        return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).replace(tzinfo=None)

    qa = {'over_span': []}

    # time — minutes inside the window, from rows that happened
    timed = []
    for r in rows:
        if r.get('status') in NOT_LIVED:
            continue
        a, b = local(r.get('when')), local(r.get('end'))
        if a and b:
            if b - a > MAX_SPAN:
                qa['over_span'].append(r.get('title') or r['id'])
                continue
            m = (min(b, end) - max(a, start)).total_seconds() / 60
        elif a and r.get('spent') and start <= a < end:
            m = float(r['spent']) / 60
        else:
            continue
        if m > 0:
            timed.append(dict(r, _min=round(m)))

    # closed and open — one line per action, its state as the week ended
    chains = {}
    for r in rows:
        chains.setdefault(bedo_reader.chain_key(r.get('key'), r.get('status'), r['id']), []).append(r)
    closed, still = [], []
    for ch in chains.values():
        if not any(x.get('status') in bedo_reader.ACTION_STATUSES for x in ch):
            continue
        upto = sorted((x for x in ch if local(x['created']) and local(x['created']) < end),
                      key=lambda x: x['created'])
        if not upto:
            continue
        head = upto[-1]
        at = local(head.get('end')) or local(head.get('when')) or local(head['created'])
        if head.get('status') == DONE and at and start <= at < end:
            closed.append(dict(head, _first=upto[0].get('title') or ''))
        elif head.get('status') in OPEN:
            still.append(head)

    W = dict(time=lambda r: r['_min'], one=lambda r: 1)
    drive = lambda r: r.get('rhythm')  # noqa: E731
    t = bedo_drives.roll_up(timed, rhythms, drive, W['time'])
    c = bedo_drives.roll_up(closed, rhythms, drive, W['one'])
    o = bedo_drives.roll_up(still, rhythms, drive, W['one'])
    z = dict(own=0, total=0, n_own=0, n=0, items=[])
    names = set(t) | set(c) | set(o)
    combined = {n: dict(total=(t.get(n) or z)['total'], tm=t.get(n) or z, cl=c.get(n) or z, op=o.get(n) or z)
                for n in names}
    forest = bedo_drives.tree(combined, rhythms,
                              key=lambda n: (-combined[n]['tm']['total'], -combined[n]['cl']['n'],
                                             -combined[n]['op']['n'], n))

    def clean(s):
        return re.sub(r'^[^\w]+', '', s or '').strip()

    def node(n):
        rec = rhythms.get(n['name']) or {}
        tm, cl, op = n['tm'], n['cl'], n['op']
        return dict(
            drive=n['name'], emoji=rec.get('emoji') or '',
            min=round(tm['total']), own_min=round(tm['own']),
            closed=cl['n'], closed_own=cl['n_own'], open=op['n'], open_own=op['n_own'],
            done=[dict(t=clean(r.get('title')), url=r.get('deliv') or None,
                       **({'set': clean(r['_first'])} if clean(r['_first']) != clean(r.get('title')) else {}))
                  for r in cl['items']],
            still=[dict(t=clean(r.get('title')), st=(r.get('status') or '')[:2],
                        due=(local(r['target']).date().isoformat() if r.get('target') else None))
                   for r in op['items']],
            children=[node(x) for x in n['children']])

    on_drive = lambda xs: [r for r in xs if r.get('rhythm')]  # noqa: E731
    totals = dict(
        min=round(bedo_drives.grand_total(on_drive(timed), W['time'])),
        min_no_drive=round(sum(r['_min'] for r in timed if not r.get('rhythm'))),
        closed=len(on_drive(closed)), closed_no_drive=len(closed) - len(on_drive(closed)),
        open=len(on_drive(still)), open_no_drive=len(still) - len(on_drive(still)))
    qa['feeds_loops'] = [' → '.join(cy + cy[:1]) for cy in bedo_drives.loops(rhythms)]
    return [node(n) for n in forest], totals, qa


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', required=True, help='the Sunday the week opens on, or any day in it')
    ap.add_argument('--local', required=True)
    ap.add_argument('--stream', action='append', required=True, help='live base first')
    ap.add_argument('--rhythms', required=True)
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    F, RF = fields(L)
    day = dt.date.fromisoformat(a.week)
    sun = day - dt.timedelta(days=(day.weekday() + 1) % 7)
    start = dt.datetime.combine(sun, dt.time())
    rows, reads = load(a.stream, F)
    rhythms, nrh = load_rhythms(a.rhythms, RF)
    drives, totals, qa = build(rows, rhythms, start, L)
    wk = L['week_zero_number'] + (sun - dt.date.fromisoformat(L['week_zero_sunday'])).days // 7
    sat = sun + dt.timedelta(days=6)
    DATA = dict(
        chip=f'✔️{sat:%m%d} ⏳ Sat {MARK} W{wk} 🔆 my day',
        week=f'W{wk}', range=f'Sun {sun.day} {sun:%b} – Sat {sat.day} {sat:%b}',
        totals=totals, drives=drives, loops=qa['feeds_loops'],
        read=' · '.join(f'{n} {k}/{k}' for n, k in reads) + f' · rhythms {nrh}/{nrh}')
    tpl = open(a.template, encoding='utf-8').read()
    if '/*__DATA__*/null' not in tpl:
        die(f'{a.template}: no /*__DATA__*/null placeholder — is this the engine?')
    open(a.out, 'w', encoding='utf-8').write(tpl.replace('/*__DATA__*/null', json.dumps(DATA, ensure_ascii=False)))

    def outline(ns, d=0):
        for n in ns:
            yield '  ' * d + f"{n['drive']} · {n['min']} min · {n['closed']} closed · {n['open']} open"
            yield from outline(n['children'], d + 1)
    print(json.dumps(dict(out=a.out, week=DATA['week'], range=DATA['range'], totals=totals,
                          drives=list(outline(drives)), qa=qa, read=DATA['read']), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
