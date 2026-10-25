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
import argparse, base64, datetime as dt, json, os, re, sys

# The core lives in plugins/bedo/core; a runner may copy it beside this file. Beside wins.
_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, '..', '..', '..', 'core'), _HERE):
    sys.path.insert(0, os.path.normpath(_p))
import bedo_reader  # noqa: E402
import bedo_drives  # noqa: E402
from day_rings import day_rings  # noqa: E402

STREAM_KEYS = ('title', 'key', 'when', 'end', 'status', 'rhythm')
OPTIONAL_STREAM_KEYS = ('spent', 'deliv', 'target', 'practice', 'wellness', 'person', 'details', 'photo', 'device')
RHYTHM_KEYS = ('name',)
OPTIONAL_RHYTHM_KEYS = ('emoji', 'type', 'status', 'code', 'feeds', 'dest')
WELL = bedo_reader.FACTS['wellness']
SLEEP = bedo_reader.FACTS['practice']['sleep']
ST = bedo_reader.FACTS['status']
DONE = ST['closed'][0]                                   # ✅ done
OPEN = set(ST['open'])                                   # ▫️ ⬜ ▶️
NOT_LIVED = set(ST['plans']) | {ST['actions'][4], ST['logs'][2]}   # ▫️ ⬜ ✖️ ⨂: never happened
MAX_SPAN = dt.timedelta(hours=bedo_reader.FACTS['entry_rules']['max_span_hours'])
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
MARK = chr(0x1684E)                                      # be•do's mark, by codepoint
MOVED = re.compile(r'moved from w\d+ \((rec[A-Za-z0-9]+)\)')   # a row moved between bases names its original


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
    # a row moved between bases names the original it replaced ('moved from w41
    # (recXXXX)'); an original left behind is the same row twice (W42 QA, 19 Oct 2026)
    moved = {m for row in seen.values() for m in MOVED.findall(row.get('details') or '')}
    return [row for i, row in seen.items() if i not in moved], reads


def load_rhythms(path, RF):
    recs = bedo_reader.complete(path)
    out = {}
    for r in recs:
        c = bedo_reader.cells(r)
        row = {k: (c.get(v) if k in ('feeds', 'dest') else sv(c.get(v))) for k, v in RF.items()}
        row['feeds'] = bedo_drives.feeds_of(row)
        row['dest'] = [sv(x) if isinstance(x, dict) else x for x in (row.get('dest') or []) if x]
        if row.get('name'):
            out[row['name']] = row
    return out, len(recs)


def build(rows, rhythms, start, L, ndays=7, words=None, photos=None):
    """Everything the page counts, from rows already deduped."""
    off = dt.timedelta(hours=L['utc_offset_hours'])
    end = start + dt.timedelta(days=ndays)

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
            span = (max(a, start), min(b, end))
            if norm(r.get('practice')) == norm(SLEEP) and start <= b <= end:
                span = (a, b)                               # a night is the morning's, whole, even when it began the evening before
            m = (span[1] - span[0]).total_seconds() / 60
        elif a and r.get('spent') and start <= a < end:
            m = float(r['spent']) / 60
            span = (a, a + dt.timedelta(minutes=m))
        else:
            continue
        if m > 0:
            timed.append(dict(r, _min=round(m), _span=span))

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
    return [node(n) for n in forest], totals, qa, dict(moved=moved, **readings(rows, timed, rhythms, start, L, local, ndays, words, photos))


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


def garden(rows, start, L, local, ndays=7):
    """Each moment she marked as mattering, as a flower: the areas it touched (its own,
    heart when shared, and what her words name), a memory it echoes, a synergy glow."""
    G = L.get('garden') or bedo_reader.FACTS['garden']
    kinds = set(G['moment_practices'])
    shared_rx = re.compile(G.get('shared_pattern') or r"'s highlight$")   # a child's or partner's own highlight
    me = L.get('self_person') or ''
    end = start + dt.timedelta(days=ndays)
    out = []
    for r in rows:
        a = local(r.get('when'))
        if not a or not (start <= a < end) or r.get('status') in NOT_LIVED or not (
                norm(r.get('practice')) in kinds or shared_rx.search(norm(r.get('practice')))):
            continue
        mine = (r.get('details') or '').split(bedo_reader.FACTS['divider'])[0]
        text = ' '.join([r.get('title') or '', mine]).lower()
        areas = [norm(r.get('wellness'))] if norm(r.get('wellness')) else []
        people = [p.strip() for p in (r.get('person') or '').split(',') if p.strip() and p.strip() != me]
        if people:
            areas.append('heart')
        areas += [k for k, ws in G['words'].items() if any(w in text for w in ws)]
        areas = list(dict.fromkeys(x for x in areas if x))
        memory = any(w in text for w in G['memory'])
        synergy = any(w in text for w in G['synergy'])
        out.append(dict(day=f'{DAY3[a.weekday()]} {a.day}', at=a.isoformat(), kind=norm(r.get('practice')),
                        t=re.sub(r'^[^\w]+', '', r.get('title') or '').strip(), areas=areas, people=people,
                        memory=memory, synergy=synergy, layers=len(areas) + memory + synergy))
    # the same moment picked by both of them (her highlight and theirs, same minute) is
    # one flower, marked as theirs too
    theirs = [m for m in out if shared_rx.search(m['kind'])]
    mine = [m for m in out if not shared_rx.search(m['kind'])]
    for m in theirs:
        twin = next((x for x in mine if x['at'] == m['at']), None)
        if twin:
            twin['both'] = shared_rx.split(m['kind'])[0]
            twin['layers'] += 1
        else:
            mine.append(m)
    return sorted(mine, key=lambda m: m['at'])


GLYPH = re.compile(r'^([^\w\s]+)\s*')
LEAD = re.compile(r'\[be•do\] look behind (\d{4}-\d\d-\d\d) · (?:draft|final)\s*\n(?:draft )?lead: (.+)')
PHOTO = re.compile(r'[Ff]rom (?:her|the same) photo')


def flow_practices(path, L):
    """The practices whose catalog group is a flow: the being side, dawn and dusk."""
    if not path or not os.path.exists(path):
        return set()
    PF = (L.get('fields') or {}).get('practices') or {}
    if not PF.get('name') or not PF.get('group'):
        return set()
    flows = set(bedo_reader.FACTS['flows']['groups']) - set(bedo_reader.FACTS['flows'].get('never_held_open') or [])
    return {norm(sv(bedo_reader.cells(r).get(PF['name']))) for r in bedo_reader.complete(path)
            if sv(bedo_reader.cells(r).get(PF['group'])) in flows}


def stream(rows, rhythms, start, L, local, flowset=frozenset(), ndays=7, words=None, photos=None):
    """The week as a stream, day by day: each day under its own lead (the look behind's
    words), the moments she marked as stones (what it was, her words, who, a photo, and
    where it flowed: the envelope it sat in, its drive, the drive's destination), and the
    rest of the day as a short line of what it was (19 Oct 2026: show what the thing
    was, a picture, a few words, an emoji for the kind, and how it fits)."""
    G = L.get('garden') or bedo_reader.FACTS['garden']
    kinds = set(G['moment_practices'])
    shared_rx = re.compile(G.get('shared_pattern') or r"'s highlight$")
    me = L.get('self_person') or ''
    end = start + dt.timedelta(days=ndays)
    div = bedo_reader.FACTS['divider']

    def glyph(x):
        m = GLYPH.match(x or '')
        return m.group(1) if m else ''

    def clean(t):
        return GLYPH.sub('', t or '').strip()

    def hers(r):
        return (r.get('details') or '').split(div)[0].strip()

    def flows(drive):
        """drive → the drives it feeds → their destinations, as names."""
        out, seen, todo = [], set(), [drive] if drive else []
        while todo:
            d = todo.pop(0)
            if d in seen or d not in rhythms:
                continue
            seen.add(d)
            out.append(d)
            todo += rhythms[d].get('feeds') or []
        dests = list(dict.fromkeys(x for d in out for x in (rhythms[d].get('dest') or [])))
        # a row on a destination itself (a ♎) reaches that destination
        dests += [d for d in out if 'destination' in (rhythms[d].get('type') or '') and d not in dests]
        return [d for d in out if d not in dests], dests

    def kind(d):
        t = (rhythms.get(d) or {}).get('type') or ''
        return 'rhythm' if 'rhythm' in t else 'destination' if 'destination' in t else 'drive'

    lived = []
    for r in rows:
        a = local(r.get('when'))
        if a and start - dt.timedelta(days=1) <= a < end and r.get('status') not in NOT_LIVED:
            lived.append(dict(r, _a=a, _b=local(r.get('end'))))
    # envelopes: a row over 12 hours on a drive holds the moments inside it (the trip)
    envs = [r for r in lived if r['_b'] and r['_b'] - r['_a'] > MAX_SPAN and r.get('rhythm') in rhythms]
    leads = {}
    for r in rows:
        for d, lead in LEAD.findall(r.get('details') or ''):
            leads[d] = lead.strip()
    if words and words.get('lead'):
        leads[start.date().isoformat()] = words['lead']     # the day's own words, from the day behind's words file

    long_words = G.get('long_words', 300)
    action = norm(bedo_reader.FACTS['practice']['action'])

    def marked(r):
        pr = norm(r.get('practice'))
        return (pr in kinds or bool(shared_rx.search(pr)) or 'synergiz' in hers(r).lower()
                or (len(hers(r)) >= long_words and pr != action and bool(r.get('end'))))   # something she did and wrote about at length

    stones = {}
    for r in sorted(lived, key=lambda r: (r['_a'], r.get('created') or '')):
        if not (start <= r['_a'] < end) or not marked(r):
            continue
        k = r['_a'].strftime('%Y-%m-%d %H:%M')
        s_ = stones.setdefault(k, dict(at=r['_a'].isoformat(), day=r['_a'].date().isoformat(), rows=[]))
        s_['rows'].append(r)
    out, by_row = [], {}
    for s_ in stones.values():
        rs = s_['rows']
        rank = lambda r: (0 if norm(r.get('practice')) not in kinds and not shared_rx.search(norm(r.get('practice')))  # noqa: E731
                          else 1 if norm(r.get('practice')) == 'highlight' else 3 if shared_rx.search(norm(r.get('practice'))) else 2)
        main = min(rs, key=rank)
        words = max((hers(r) for r in rs), key=len)
        words = re.sub(r'\s*\(\d{1,2} \w{3}\)\s*', ' ', words)
        words = re.sub(r'\noverlap — .*', '', words).strip()
        people = list(dict.fromkeys(p.strip() for r in rs for p in (r.get('person') or '').split(',')
                                    if p.strip() and p.strip() != me))
        badges = list(dict.fromkeys(glyph(r.get('practice')) for r in rs if r is not main or norm(r.get('practice')) in kinds))
        theirs = [shared_rx.split(norm(r.get('practice')))[0] for r in rs if shared_rx.search(norm(r.get('practice')))]
        drive = main.get('rhythm') or next((r.get('rhythm') for r in rs if r.get('rhythm')), '')
        # an envelope holds its whole days: the day she left and the day she came home are the trip's
        env = next((e for e in envs if e['_a'].date() <= main['_a'].date() <= e['_b'].date()), None)
        chain, dests = flows(drive or (env.get('rhythm') if env else ''))
        # the being side: a flow practice belongs to its flow, dawn or dusk, not to a rhythm or drive
        flow = None
        if not drive and norm(main.get('practice')) in flowset:
            ph = bedo_reader.FACTS['flows']['phase']
            dusk = (main.get('phase') or '') == ph['dusk'] or (not main.get('phase') and main['_a'].hour >= 15)
            flow = dict(n='the dusk flow' if dusk else 'the dawn flow', e=ph['dusk' if dusk else 'dawn'].split()[0])
            if not env:
                chain, dests = [], []     # inside an envelope, what it names still flows through the trip
        low = words.lower()
        g = glyph(main.get('practice')) or glyph(main.get('title'))
        badges = [b for b in badges if b and b != g]
        if norm(main.get('practice')) in set(G.get('generic_practices') or []):
            tl = (main.get('title') or '').lower()
            named = next((e for e, ws in G.get('kind_words') or []
                          if any(re.search(r'\b' + re.escape(w.strip()) + r'\b', tl) for w in ws)), None)
            if named:
                if norm(main.get('practice')) != 'log' and g not in badges:
                    badges.insert(0, g)
                g = named
        out.append(dict(
            at=s_['at'], day=s_['day'], g=g,
            kind=clean(main.get('practice')), t=clean(main.get('title')), words=words, people=people,
            badges=badges, theirs=theirs,
            memory=next((w for w in G['memory'] if w in low), None),
            synergy=any(w in low for w in G['synergy']) or any('synergiz' in hers(r).lower() for r in rs),
            photo=any(PHOTO.search(r.get('details') or '') or r.get('photo') for r in rs),
            envelope=clean(env.get('title')).split(' — ')[0] if env else None, flow=flow,
            drives=[dict(n=d, e=(rhythms[d].get('emoji') or ''), type=kind(d)) for d in chain],
            dests=[dict(n=d, e=((rhythms.get(d) or {}).get('emoji') or ''), type='destination') for d in dests]))
        for r in rs:
            by_row[r['id']] = out[-1]
    out.sort(key=lambda m: m['at'])
    # the day's photos, each placed by the time it was taken (22 Oct 2026): on the row
    # taken at that minute or spanning it, preferring a row read from a photo, then a
    # moment; inside its moment when it has one, else in the day's pictures. A photo
    # for a routine check (a pill, a screen of scores) is left out.
    skip = set(G.get('photo_skip_practices') or bedo_reader.FACTS['garden'].get('photo_skip_practices') or [])
    skip_re = G.get('photo_skip_pattern') or bedo_reader.FACTS['garden'].get('photo_skip_pattern')
    pics = {}
    for t, src in photos or []:
        near = [r for r in lived if r['_a'].date() == t.date() and (abs((r['_a'] - t).total_seconds()) <= 180
                                                                  or (r['_b'] and r['_a'] <= t <= r['_b']
                                                                      and r['_b'] - r['_a'] <= MAX_SPAN))]
        best = min(near, key=lambda r: ('photo' not in (r.get('details') or '').lower(), not marked(r),
                                        abs((r['_a'] - t).total_seconds()))) if near else None
        if best is not None and (norm(best.get('practice')) in skip
                                 or (skip_re and re.search(skip_re, norm(best.get('practice'))))):
            continue
        if best is not None and best['id'] in by_row:
            by_row[best['id']].setdefault('photos', []).append(src)
        else:
            pics.setdefault(t.date().isoformat(), []).append(dict(
                src=src, at=t.isoformat(), g=glyph(best.get('practice')) if best else '',
                t=clean(best.get('title')) if best else ''))
    days = []
    for i in range(ndays):
        d = (start + dt.timedelta(days=i)).date()
        texture = []
        for r in sorted(lived, key=lambda r: r['_a']):
            if r['_a'].date() != d or marked(r) or not r['_b'] or r in envs:
                continue
            mins = (r['_b'] - r['_a']).total_seconds() / 60
            t = clean(r.get('title'))
            if mins < 20 or norm(r.get('practice')) == norm(SLEEP) or '(estimated)' in t or not glyph(r.get('practice')):
                continue
            if t not in [x['t'] for x in texture]:
                texture.append(dict(g=glyph(r.get('practice')), t=t))
        days.append(dict(date=d.isoformat(), label=f'{DAY3[d.weekday()]} {d.day} {d:%b}', lead=leads.get(d.isoformat()),
                         pictures=pics.get(d.isoformat(), []),
                         stones=[m for m in out if m['day'] == d.isoformat()], texture=texture[:10]))
    # where it flowed: one tile per drive the moments sat on, naming the destinations it
    # serves, so a drive serving four destinations is one tile, not four (21 Oct 2026);
    # the moments on no drive at all are one tile, last
    reach = {}
    for m in out:
        # where it reached: its destinations; on a rhythm (no destination, by her rule), the rhythm itself
        for x in (([m['flow']] if m.get('flow') else []) + (m['dests'] or m['drives'][-1:])) or [dict(n='', e='')]:
            reach.setdefault(x['n'], dict(n=x['n'], e=x['e'], n_moments=0, via=set(), moments=[]))
            reach[x['n']]['n_moments'] += 1
            reach[x['n']]['moments'].append(dict(at=m['at'], g=m['g'], t=m['t'], day=m['day']))
            if m['envelope']:
                reach[x['n']]['via'].add(m['envelope'])
    flowed = sorted(({**v, 'via': sorted(v['via'])} for v in reach.values()), key=lambda v: -v['n_moments'])
    bands = [dict(t=clean(e.get('title')).split(' — ')[0], a=e['_a'].isoformat(), b=e['_b'].isoformat()) for e in envs]
    # the being side, day by day: the flows are practices she returns to, not places she goes
    # (20 Oct 2026), so each day shows how much of each flow was done and whether it was closed
    F = bedo_reader.FACTS['flows']
    closes = {norm(F['close'][k]): k for k in ('dawn', 'dusk')}
    be = []
    for i in range(ndays):
        d = (start + dt.timedelta(days=i)).date()
        day = {k: dict(n=0, closed=False, g=[]) for k in ('dawn', 'dusk')}
        for r in lived:
            if r['_a'].date() != d:
                continue
            pr = norm(r.get('practice'))
            if pr in closes:
                day[closes[pr]]['closed'] = True
            elif pr in flowset:
                k = 'dusk' if (r.get('phase') or '') == F['phase']['dusk'] or (not r.get('phase') and r['_a'].hour >= 15) else 'dawn'
                day[k]['n'] += 1
                if glyph(r.get('practice')) and glyph(r.get('practice')) not in day[k]['g']:
                    day[k]['g'].append(glyph(r.get('practice')))
        be.append(dict(date=d.isoformat(), **day))
    flows_meta = [dict(k=k, n=f'the {k} flow', e=F['phase'][k].split()[0]) for k in ('dawn', 'dusk')]
    return dict(days=days, flowed=flowed, n=len(out), bands=bands, be=be, flows=flows_meta)


def needs_map(L):
    N = L.get('needs') or bedo_reader.FACTS['needs']
    side = {}
    for k in ('deficiency', 'growth'):
        for g in N[k]:
            for a in g['areas']:
                side[norm(a)] = k
    return N, side


def readings(rows, timed, rhythms, start, L, local, ndays=7, words=None, photos=None):
    """Time by area, rest, and the needs, per day and for the week. Minutes only:
    two rows at once both count, as on the wheel. Sleep is in bed, never an area."""
    N, side = needs_map(L)
    be = {norm(a) for a in WELL['be']}
    growing = set(L.get('growing_types') or [])
    play = {norm(p) for s in (L.get('pie') or []) if s.get('k') == 'play' for p in s.get('practices', [])}
    zero = {norm(p) for p in (L.get('zero_practices') or [])}
    me = L.get('self_person') or ''
    days = [start.date() + dt.timedelta(d) for d in range(ndays)]
    D = {d: dict(day=f'{DAY3[d.weekday()]} {d.day}', bed=0, play=0, be=0, tend=0, grow=0, people=0,
                 deficiency=0, growth=0, none=0, readiness=None, sleep_score=None, activity=None,
                 secure=None, logged=0) for d in days}
    spans = {d: [] for d in days}
    heart = norm(WELL['be'][0])
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
        if r.get('_span'):
            spans[d].append(r['_span'])
        w = norm(r.get('wellness'))
        # time with somebody is belonging, whatever else it was: dinner with the
        # family is body AND heart, both counted, as two things at once are on the
        # wheel (her word, 19 Oct 2026: I had a ton of family time last week)
        others = [p for p in people if p != me]
        if others:
            D[d]['people'] += r['_min']
            if w != heart:
                areas[heart] += r['_min']                  # the heart bar and the needs, not the being total
                D[d][side.get(heart, 'none')] += r['_min']
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
    rx = {k: re.compile(r'\b' + k + r'\b\D{0,3}(\d{2,3})', re.I) for k in ('readiness', 'sleep', 'activity')}
    for r in sorted(rows, key=lambda r: r.get('when') or ''):
        a = local(r.get('when'))
        if not a or a.date() not in D or r.get('status') in NOT_LIVED:
            continue
        pr, text = norm(r.get('practice')), ' '.join(filter(None, [r.get('title'), r.get('details')]))
        if N.get('oura_practice') and pr == N['oura_practice'] and D[a.date()]['readiness'] is None:
            for k, key in (('readiness', 'readiness'), ('sleep', 'sleep_score'), ('activity', 'activity')):
                m = rx[k].search(text)
                if m and 30 <= int(m.group(1)) <= 100:
                    D[a.date()][key] = int(m.group(1))
        if N.get('secure_practice') and pr == N['secure_practice']:
            # her titles vary ('⏏️ Secure', 'Secure base — secure', 'Yes this morning — …',
            # 'above the line'); anything else is the other state, in her words
            t = re.sub(r'^secure base\W*', '', norm(r.get('title')))
            D[a.date()]['secure'] = ('secure' if re.match(r'(secure|yes|above the line)\b', t)
                                     else (r.get('title') or '').strip())
    # how much of the waking day a row covers at all: the honest size of every number above it
    for d, v in D.items():
        cov, last = 0, None
        for a, b in sorted(spans[d]):
            if last is None or a > last:
                cov += (b - a).total_seconds() / 60
                last = b
            elif b > last:
                cov += (b - last).total_seconds() / 60
                last = b
        v['awake'] = max(0, 24 * 60 - v['bed']) if v['bed'] else 16 * 60
        v['logged'] = min(round(cov), v['awake'])      # a late night runs past the day's own waking hours
    out = [dict(v, secure=v['secure'] or 'secure', assumed=v['secure'] is None) for v in D.values()]
    rest = dict(bed=sum(v['bed'] for v in out), play=sum(v['play'] for v in out),
                nights=sum(1 for v in out if v['bed']),
                readiness=[v['readiness'] for v in out if v['readiness'] is not None],
                activity=[v['activity'] for v in out if v['activity'] is not None])
    groups = {k: [dict(label=g['label'], says=g['says'],
                       min=round(sum(areas.get(norm(a), 0) for a in g['areas'])),
                       areas=[dict(a=a, min=round(areas.get(norm(a), 0))) for a in g['areas']]) for g in N[k]]
              for k in ('deficiency', 'growth')}
    return dict(days=out, rest=rest, needs=groups, garden=garden(rows, start, L, local, ndays),
                stream=stream(rows, rhythms, start, L, local, L.get('_flowset') or frozenset(), ndays, words, photos),
                time=dict(be=sum(v['be'] for v in out), tend=sum(v['tend'] for v in out),
                          grow=sum(v['grow'] for v in out), bed=rest['bed'],
                          people=sum(v['people'] for v in out),
                          logged=sum(v['logged'] for v in out), awake=sum(v['awake'] for v in out),
                          areas=[dict(a=a, min=round(areas[norm(a)])) for a in WELL['be'] + WELL['do']]),
                secure_days=sum(1 for v in out if v['secure'] == 'secure'),
                secure_assumed=sum(1 for v in out if v['assumed']))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', help='the Sunday the week opens on, or any day in it')
    ap.add_argument('--day', help='one day instead of a week: the day behind as a stream (20 Oct 2026)')
    ap.add_argument('--words', help="with --day: the day behind's words file (lead and story)")
    ap.add_argument('--photos', help='a folder of small photos named by the phone (day_photos.py --out)')
    ap.add_argument('--local', required=True)
    ap.add_argument('--stream', action='append', required=True, help='live base first')
    ap.add_argument('--rhythms', required=True)
    ap.add_argument('--practices', help="the catalog, so a flow practice shows under its flow")
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    F, RF = fields(L)
    if bool(a.week) == bool(a.day):
        die('give --week or --day, one of them')
    day = dt.date.fromisoformat(a.week or a.day)
    sun = day - dt.timedelta(days=(day.weekday() + 1) % 7)
    ndays = 1 if a.day else 7
    start = dt.datetime.combine(day if a.day else sun, dt.time())
    words = json.load(open(a.words, encoding='utf-8')) if a.words else None
    if words and words.get('day') not in (None, day.isoformat()):
        die(f"{a.words} holds the words for {words.get('day')}, not {day}")
    rows, reads = load(a.stream, F)
    L['_flowset'] = flow_practices(a.practices, L)
    rhythms, nrh = load_rhythms(a.rhythms, RF)
    photos = []
    if a.photos and os.path.isdir(a.photos):
        from day_photos import taken
        for n in sorted(os.listdir(a.photos)):
            t = taken(n, L['utc_offset_hours'])
            if t:
                b64 = base64.b64encode(open(os.path.join(a.photos, n), 'rb').read()).decode()
                photos.append((t, 'data:image/jpeg;base64,' + b64))
    drives, totals, qa, more = build(rows, rhythms, start, L, ndays, words, photos)
    wk = L['week_zero_number'] + (sun - dt.date.fromisoformat(L['week_zero_sunday'])).days // 7
    sat = sun + dt.timedelta(days=6)
    last = sat if not a.day else day
    DATA = dict(
        chip=f'✔️{last:%m%d} ⏳ {DAY3[last.weekday()]} {MARK} W{wk} 🔆 my day',
        span='day' if a.day else 'week', ndays=ndays,
        story=[list(x) for x in (words or {}).get('story') or []],
        week=f'W{wk}', range=(f'{DAY3[day.weekday()]} {day.day} {day:%b}' if a.day
                              else f'Sun {sun.day} {sun:%b} – Sat {sat.day} {sat:%b}'),
        totals=totals, drives=drives, loops=qa['feeds_loops'], **more,
        rings=day_rings(rows, day, L, L.get('_flowset') or frozenset(), NOT_LIVED) if a.day else None,
        read=' · '.join(f'{n} {k}/{k}' for n, k in reads) + f' · rhythms {nrh}/{nrh}')
    tpl = open(a.template, encoding='utf-8').read()
    if '/*__DATA__*/null' not in tpl:
        die(f'{a.template}: no /*__DATA__*/null placeholder — is this the engine?')
    if a.day:
        tpl = tpl.replace('<title>The Week Behind</title>', '<title>The Day Behind</title>', 1)
    open(a.out, 'w', encoding='utf-8').write(tpl.replace('/*__DATA__*/null', json.dumps(DATA, ensure_ascii=False)))

    def outline(ns, d=0):
        for n in ns:
            yield '  ' * d + f"{n['drive']} · {n['min']} min · {n['closed']} closed · {n['open']} open"
            yield from outline(n['children'], d + 1)
    rest, tm = more['rest'], more['time']
    placed = sum(len(m.get('photos') or []) for d in more['stream']['days'] for m in d['stones'])
    strip = sum(len(d['pictures']) for d in more['stream']['days'])
    print(json.dumps(dict(out=a.out, week=DATA['week'], range=DATA['range'], totals=totals,
                          photos=dict(read=len(photos), on_moments=placed, in_pictures=strip, left_out=len(photos) - placed - strip),
                          time=dict(be=round(tm['be']), tending=round(tm['tend']), growing=round(tm['grow']), bed=round(tm['bed'])),
                          moved=dict(closed=len(more['moved']['closed']), in_motion=len(more['moved']['motion'])),
                          rest=dict(nights=rest['nights'], bed=round(rest['bed']), play=round(rest['play']), readiness=rest['readiness']),
                          needs={k: [f"{g['label']} {g['min']}" for g in v] for k, v in more['needs'].items()},
                          secure=f"{more['secure_days']}/{ndays} ({more['secure_assumed']} assumed)",
                          drives=list(outline(drives)), qa=qa, read=DATA['read']), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
