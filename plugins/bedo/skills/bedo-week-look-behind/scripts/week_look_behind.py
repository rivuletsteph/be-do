# -*- coding: utf-8 -*-
"""The week look behind, by drive — the first cut (9 Oct 2026).

One week, Sunday 00:00 to the next Sunday 00:00, local. Per drive: the time
logged on it, the actions it closed, and what is still open at the week's end.
Drives within drives: a row counts under its own drive and every drive it feeds,
the child nested under its parent; the headline counts each row once
(plugins/bedo/core/bedo_drives.py).

Her build notes, Sun 18 Oct 2026, add four readings of the same rows: where the
time went (the eight areas, being and doing), what moved forward (closed and in
motion), rest as a reset (nights in bed, play, the morning readiness), and the
needs — deficiency against growth, day by day, on the secure base (facts.json
`needs`). The rest of the week page (the reading, the wheel, who was there …) is
not built yet — see SKILL.md.

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
OPTIONAL_STREAM_KEYS = ('spent', 'deliv', 'target', 'practice', 'wellness', 'person', 'details')
RHYTHM_KEYS = ('name',)
OPTIONAL_RHYTHM_KEYS = ('emoji', 'type', 'status', 'code', 'feeds')
WELL = bedo_reader.FACTS['wellness']
SLEEP = bedo_reader.FACTS['practice']['sleep']
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
    moved = dict(closed=[dict(t=clean(r.get('title')), drive=r.get('rhythm') or '', url=r.get('deliv') or None)
                         for r in sorted(closed, key=lambda r: r.get('end') or r.get('when') or '')],
                 motion=[dict(t=clean(r.get('title')), drive=r.get('rhythm') or '')
                         for r in moving(rows, chains, start, end, local)])
    return [node(n) for n in forest], totals, qa, dict(moved=moved, **readings(rows, timed, rhythms, start, L, local))


def norm(p):
    """A practice or area name without its glyph: '😴 sleep' → 'sleep'."""
    return re.sub(r'^[^\w]+', '', p or '').strip().lower()


def moving(rows, chains, start, end, local):
    """▶️ heads whose chain had a row in the week: in motion, and touched."""
    out = []
    for ch in chains.values():
        upto = sorted((x for x in ch if local(x['created']) and local(x['created']) < end), key=lambda x: x['created'])
        if not upto or upto[-1].get('status') != ST['actions'][2]:
            continue
        if any(start <= (local(x.get('when')) or local(x['created'])) < end for x in upto):
            out.append(upto[-1])
    return sorted(out, key=lambda r: r.get('when') or '')


def needs_map(L):
    N = L.get('needs') or bedo_reader.FACTS['needs']
    side = {}
    for k in ('deficiency', 'growth'):
        for g in N[k]:
            for a in g['areas']:
                side[norm(a)] = k
    return N, side


def readings(rows, timed, rhythms, start, L, local):
    """Time by area, rest, and the needs, per day and for the week. Minutes only:
    two rows at once both count, as on the wheel. Sleep is in bed, never an area."""
    N, side = needs_map(L)
    be = {norm(a) for a in WELL['be']}
    growing = set(L.get('growing_types') or [])
    play = {norm(p) for s in (L.get('pie') or []) if s.get('k') == 'play' for p in s.get('practices', [])}
    zero = {norm(p) for p in (L.get('zero_practices') or [])}
    me = L.get('self_person') or ''
    days = [start.date() + dt.timedelta(d) for d in range(7)]
    D = {d: dict(day=f'{DAY3[d.weekday()]} {d.day}', bed=0, play=0, be=0, tend=0, grow=0,
                 deficiency=0, growth=0, none=0, readiness=None, sleep_score=None, secure=None) for d in days}
    areas = {norm(a): 0 for a in WELL['be'] + WELL['do']}
    for r in timed:
        pr = norm(r.get('practice'))
        people = [p.strip() for p in (r.get('person') or '').split(',') if p.strip()]
        if pr == norm(SLEEP):
            if people and me not in people:
                continue                                    # somebody else's night
            day = (local(r.get('end')) or local(r.get('when'))).date()   # a night is the morning's
            if day in D:
                D[day]['bed'] += r['_min']
            continue
        a = local(r.get('when'))
        d = max(a, start).date() if a else None
        if d not in D or pr in zero:
            continue
        if pr in play:
            D[d]['play'] += r['_min']
        w = norm(r.get('wellness'))
        if w in areas:
            areas[w] += r['_min']
            if w in be:
                D[d]['be'] += r['_min']
            elif (rhythms.get(r.get('rhythm')) or {}).get('type') in growing:
                D[d]['grow'] += r['_min']
            else:
                D[d]['tend'] += r['_min']
            D[d][side.get(w, 'none')] += r['_min']
    # the morning readiness, from the Oura row's own words; the secure base from ⏏️
    rx = {k: re.compile(r'\b' + k + r'\b\D{0,3}(\d{2,3})', re.I) for k in ('readiness', 'sleep')}
    for r in sorted(rows, key=lambda r: r.get('when') or ''):
        a = local(r.get('when'))
        if not a or a.date() not in D or r.get('status') in NOT_LIVED:
            continue
        pr, text = norm(r.get('practice')), ' '.join(filter(None, [r.get('title'), r.get('details')]))
        if N.get('oura_practice') and pr == N['oura_practice'] and D[a.date()]['readiness'] is None:
            for k, key in (('readiness', 'readiness'), ('sleep', 'sleep_score')):
                m = rx[k].search(text)
                if m and 30 <= int(m.group(1)) <= 100:
                    D[a.date()][key] = int(m.group(1))
        if N.get('secure_practice') and pr == N['secure_practice']:
            # her titles vary ('⏏️ Secure', 'Secure base — secure', 'Yes this morning — …',
            # 'above the line'); anything else is the other state, in her words
            t = re.sub(r'^secure base\W*', '', norm(r.get('title')))
            D[a.date()]['secure'] = ('secure' if re.match(r'(secure|yes|above the line)\b', t)
                                     else (r.get('title') or '').strip())
    out = [dict(v, secure=v['secure'] or 'secure', assumed=v['secure'] is None) for v in D.values()]
    rest = dict(bed=sum(v['bed'] for v in out), play=sum(v['play'] for v in out),
                nights=sum(1 for v in out if v['bed']),
                readiness=[v['readiness'] for v in out if v['readiness'] is not None])
    groups = {k: [dict(label=g['label'], says=g['says'],
                       min=round(sum(areas.get(norm(a), 0) for a in g['areas'])),
                       areas=[dict(a=a, min=round(areas.get(norm(a), 0))) for a in g['areas']]) for g in N[k]]
              for k in ('deficiency', 'growth')}
    return dict(days=out, rest=rest, needs=groups,
                time=dict(be=sum(v['be'] for v in out), tend=sum(v['tend'] for v in out),
                          grow=sum(v['grow'] for v in out), bed=rest['bed'],
                          areas=[dict(a=a, min=round(areas[norm(a)])) for a in WELL['be'] + WELL['do']]),
                secure_days=sum(1 for v in out if v['secure'] == 'secure'),
                secure_assumed=sum(1 for v in out if v['assumed']))


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
    drives, totals, qa, more = build(rows, rhythms, start, L)
    wk = L['week_zero_number'] + (sun - dt.date.fromisoformat(L['week_zero_sunday'])).days // 7
    sat = sun + dt.timedelta(days=6)
    DATA = dict(
        chip=f'✔️{sat:%m%d} ⏳ Sat {MARK} W{wk} 🔆 my day',
        week=f'W{wk}', range=f'Sun {sun.day} {sun:%b} – Sat {sat.day} {sat:%b}',
        totals=totals, drives=drives, loops=qa['feeds_loops'], **more,
        read=' · '.join(f'{n} {k}/{k}' for n, k in reads) + f' · rhythms {nrh}/{nrh}')
    tpl = open(a.template, encoding='utf-8').read()
    if '/*__DATA__*/null' not in tpl:
        die(f'{a.template}: no /*__DATA__*/null placeholder — is this the engine?')
    open(a.out, 'w', encoding='utf-8').write(tpl.replace('/*__DATA__*/null', json.dumps(DATA, ensure_ascii=False)))

    def outline(ns, d=0):
        for n in ns:
            yield '  ' * d + f"{n['drive']} · {n['min']} min · {n['closed']} closed · {n['open']} open"
            yield from outline(n['children'], d + 1)
    rest, tm = more['rest'], more['time']
    print(json.dumps(dict(out=a.out, week=DATA['week'], range=DATA['range'], totals=totals,
                          time=dict(be=round(tm['be']), tending=round(tm['tend']), growing=round(tm['grow']), bed=round(tm['bed'])),
                          moved=dict(closed=len(more['moved']['closed']), in_motion=len(more['moved']['motion'])),
                          rest=dict(nights=rest['nights'], bed=round(rest['bed']), play=round(rest['play']), readiness=rest['readiness']),
                          needs={k: [f"{g['label']} {g['min']}" for g in v] for k, v in more['needs'].items()},
                          secure=f"{more['secure_days']}/7 ({more['secure_assumed']} assumed)",
                          drives=list(outline(drives)), qa=qa, read=DATA['read']), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
