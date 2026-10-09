# -*- coding: utf-8 -*-
"""dayqa: one day's meals, gaps, movement, people and device checks, as one
short list for her to accept or not (9 Oct 2026).

Her words, 9 Oct: *Why on Earth did all this get skipped before? It seems like
this should be codified … You just got to use what's at your disposal here.*

Every fill is ESTIMATED FROM CONTEXT and names where it came from: photo time,
Oura, Timeline, message time, or her stated rule. What nothing can fill is
asked, in the same list. Nothing here writes. The dusk close shows the list,
writes only the numbers she accepts (each through the entry check), and puts
the marker line this prints in its own [be•do] block; the look behind won't
build a day whose rows don't carry it.

  meals     each meal's prep and eating (bedo_meals, the 7 Oct rules)
  gaps      15+ minutes between the first and last waking row no span covers
  movement  walking, cycling or exercise she mentions with no movement row
            near it; a movement row with no minutes (rule 7)
  people    person set on a plan (rule 6); a name no connection matches
  device    device and wellness, deduced (rule 1, bedo_fill)
  spans     a row over 12 h, or one whose end is on another day (rules 2, 5)

    python3 bedo_dayqa.py --live --date 2026-10-09 [--json]
    python3 bedo_dayqa.py --day day.json [--catalog practices.json] [--rhythms rhythms.json]
                          [--connections connections.json] [--history w40.json …] --date 2026-10-09
"""
import datetime as dt, json, re, sys

from bedo_reader import FACTS, as_rows, cells, complete, load_local, offset_hours, on_day, sv
from bedo_entry import OVERNIGHT, RULES, span_problems, utc
import bedo_fill as FL
import bedo_meals as ML
import bedo_people as PP

Q = FACTS['dayqa']
SRC = Q['sources']
EST = 'ESTIMATED FROM CONTEXT'
PLANS = set(FACTS['status']['plans'])
NOT_LIVED = PLANS | {FACTS['status']['actions'][4], FACTS['status']['logs'][2]}   # ✖️ dropped, ⨂ skipped
DIVIDER = FACTS['divider']
MOVE = {FL.word(p) for p in Q['movement_practices']}
LOCATION = FL.word(FACTS['practice']['location'])
NAMES = ('datetime', 'end', 'time_spent', 'status', 'title', 'details', 'practice', 'person',
         'mentioned', 'wellness', 'device', 'rhythm', 'photo', 'key')


def _z(t):
    return t.strftime('%Y-%m-%dT%H:%M:00.000Z')


def _clock(t, off):
    t = t + dt.timedelta(hours=off)
    return f'{t.hour % 12 or 12}:{t:%M}{"a" if t.hour < 12 else "p"}'


def _t(r):
    return (r.get('title') or r.get('practice') or '?')[:60]


def her_words(r):
    return (r.get('details') or '').split(DIVIDER, 1)[0].split('[be•do]', 1)[0]


def anchor(r):
    """Where a row's own time came from, in her list's words."""
    p = FL.word(r.get('practice'))
    if r.get('photo'):
        return SRC['photo']
    if p in {FL.word(x) for x in Q['oura_practices']}:
        return SRC['oura']
    if p in {FL.word(x) for x in Q['message_practices']}:
        return SRC['message']
    if p == LOCATION:
        return SRC['timeline']
    return None


def fill(check, line, source, patch=None, new=None, note=None):
    return {'check': check, 'kind': 'fill', 'line': line, 'source': source,
            'patch': patch, 'new': new, 'note': note or f'[be•do] {EST} ({source}): {line}'}


def ask(check, line):
    return {'check': check, 'kind': 'ask', 'line': line}


# ── the five checks ─────────────────────────────────────────────────────
def meals(rows, off, people):
    out = []
    for p in ML.propose(rows, off, people):
        row = next(r for r in rows if r['id'] == p['id'])
        a = anchor(row)
        src = f'{a} + {SRC["rule"]}' if a else SRC['rule']
        if p['prep']:
            pr = {k: v for k, v in p['prep'].items() if k != 'class'}
            c = p['prep']['class']
            out.append(fill('meals', f'{pr["title"]} {_clock(utc(pr["datetime"]), off)}–{_clock(utc(pr["end"]), off)} '
                            f'({ML.M["prep_minutes"][c]} min, {ML.M["prep_why"][c]})', src, new=pr))
        if p['eat']:
            out.append(fill('meals', f'{_t(row)}: ate {_clock(utc(row["datetime"]), off)}–{_clock(utc(p["eat"]["end"]), off)} '
                            f'({p["eat"]["why"]})', src, patch={'id': row['id'], 'fields': {'end': p['eat']['end']}}))
    return out


def gaps(rows, off, proposed=()):
    """Asked last, so the spans the other checks propose already cover their minutes."""
    lived = [r for r in rows if r.get('status') not in NOT_LIVED and r.get('datetime')]
    ends = {i['patch']['id']: i['patch']['fields']['end'] for i in proposed
            if i.get('patch') and 'end' in i['patch']['fields']}
    spanned = [dict(r, end=ends.get(r.get('id'), r.get('end'))) for r in lived]
    spanned += [i['new'] for i in proposed if i.get('new') and i['new'].get('end')]
    covers = [(utc(r['datetime']), utc(r['end'])) for r in spanned
              if r.get('end') and FL.word(r.get('practice')) != LOCATION and utc(r['end']) > utc(r['datetime'])]
    places = [r for r in lived if FL.word(r.get('practice')) == LOCATION and r.get('end')]
    awake = [r for r in lived if FL.word(r.get('practice')) not in OVERNIGHT]
    if not awake:
        return []
    lo = min(utc(r['datetime']) for r in awake)
    hi = max(utc(r.get('end') or r['datetime']) for r in awake)
    step = dt.timedelta(minutes=1)
    out, t = [], lo
    while t < hi:
        if any(a <= t < b for a, b in covers):
            t += step
            continue
        g = t
        while t < hi and not any(a <= t < b for a, b in covers):
            t += step
        mins = int((t - g).total_seconds() // 60)
        if mins >= Q['gap_minutes']:
            at = next((p for p in places if utc(p['datetime']) <= g < utc(p['end'])), None)
            clue = f' — {SRC["timeline"]} has you at {_t(at)}' if at else ''
            out.append(ask('gaps', f'{_clock(g, off)}–{_clock(t, off)} ({mins} min) nothing logged{clue}; what were you doing?'))
    return out


_OURA = re.compile(r'(?i)\b([a-z][a-z ]{2,20}?)\s+(\d{1,2}):(\d{2})\s*([ap])m?\s*[–-]\s*(\d{1,2}):(\d{2})\s*([ap])m?')


def movement(rows, off, day, local, catalog_names, typical):
    out = []
    lived = [r for r in rows if r.get('status') not in NOT_LIVED and r.get('datetime')]
    moves = [r for r in lived if FL.word(r.get('practice')) in MOVE]
    by_word = {FL.word(n): n for n in catalog_names}

    def practice_for(w):
        w = w.lower()
        key = ('cycling' if re.search(r'bik|bicycl|cycl|rode', w) else 'walking' if 'walk' in w
               else 'hike' if 'hik' in w else 'yoga' if 'yoga' in w else 'other movement')
        return by_word.get(key)

    def near(t, mins=60):
        return any(abs((utc(m['datetime']) - t).total_seconds()) <= mins * 60
                   or (m.get('end') and utc(m['datetime']) <= t <= utc(m['end'])) for m in moves)

    # Oura's own workout lines: "cycling 10:05a–10:40a"
    read = set()
    for r in lived:
        if anchor(r) != SRC['oura']:
            continue
        for m in _OURA.finditer(r.get('details') or ''):
            what = m.group(1).strip().split()[-1]
            if not any(w in what.lower() for w in Q['movement_words']):
                continue
            def at(h, mi, ap):
                h = int(h) % 12 + (12 if ap.lower() == 'p' else 0)
                loc = dt.datetime.combine(day, dt.time(h, int(mi)))
                return (loc - dt.timedelta(hours=off)).replace(tzinfo=dt.timezone.utc)
            s, e = at(*m.group(2, 3, 4)), at(*m.group(5, 6, 7))
            read.add(r.get('id'))
            if e <= s or near(s, 15):
                continue
            pr = practice_for(what)
            if not pr:
                out.append(ask('movement', f'{what} {_clock(s, off)}–{_clock(e, off)} from {SRC["oura"]}: which practice?'))
                continue
            new = {'datetime': _z(s), 'end': _z(e), 'status': FACTS['status']['logs'][1], 'practice': pr,
                   'title': f'{pr.split(" ", 1)[0]} {what}',
                   'details': f'{DIVIDER}\n[be•do] {EST}: the times are {SRC["oura"]}\'s workout.'}
            out.append(fill('movement', f'{pr} {_clock(s, off)}–{_clock(e, off)}', SRC['oura'], new=new))
            moves.append(new)
    # a movement she mentions, with no movement row near it (rule 7)
    words = re.compile(r'(?i)\b(' + '|'.join(re.escape(w) for w in Q['movement_words']) + r')\b')
    for r in lived:
        if FL.word(r.get('practice')) in MOVE or r.get('id') in read:
            continue
        m = words.search((r.get('title') or '') + ' ' + her_words(r))
        if not m:
            continue
        s = utc(r['datetime'])
        if near(s):
            continue
        pr = practice_for(m.group(1))
        a = anchor(r)
        n = (typical or {}).get(FL.word(pr)) if pr else None
        if pr and a and n:
            new = {'datetime': _z(s), 'end': _z(s + dt.timedelta(minutes=n)), 'status': FACTS['status']['logs'][1],
                   'practice': pr, 'title': f'{pr.split(" ", 1)[0]} {m.group(1)}',
                   'details': f'{DIVIDER}\n[be•do] {EST}: from “{_t(r)}” ({a}), {n} min, its typical length.'}
            out.append(fill('movement', f'{pr} {_clock(s, off)}–{_clock(utc(new["end"]), off)}, from “{_t(r)}”',
                            f'{a} + {SRC["rule"]}', new=new))
        else:
            out.append(ask('movement', f'“{_t(r)}” at {_clock(s, off)} mentions “{m.group(1)}” — '
                                       'its own movement row: when, and how long?'))
    for r in moves:
        if r.get('id') and not r.get('end') and not r.get('time_spent'):
            out.append(ask('movement', f'{_t(r)} at {_clock(utc(r["datetime"]), off)} has no minutes — how long?'))
    return out


def people(rows, index):
    out = []
    for r in rows:
        who = [p.strip() for p in (r.get('person') or '').split(',') if p.strip()]
        if not who:
            continue
        if r.get('status') in PLANS:
            had = [p.strip() for p in (r.get('mentioned') or '').split(',') if p.strip()]
            ment = ', '.join(dict.fromkeys(had + who))
            out.append(fill('people', f'{_t(r)}: {", ".join(who)} from person to mentioned — a plan, not yet met',
                            SRC['rule'] + ' (rule 6)', patch={'id': r['id'], 'fields': {'person': '', 'mentioned': ment}}))
        elif index is not None:
            for p in who:
                if index.find(p) is None:
                    out.append(ask('people', f'“{p}” on {_t(r)} matches no connection — who is it, or which name?'))
    return out


def device(rows, ctx):
    out = []
    for r in rows:
        if r.get('status') in NOT_LIVED - PLANS:
            continue
        got, asks = FL.deduce(r, ctx)
        if got:
            fields = {f: v for f, (v, _) in got.items()}
            why = '; '.join(f'{f} {v}: {w}' for f, (v, w) in got.items())
            out.append(fill('device', f'{_t(r)} → {" · ".join(fields.values())}', f'{SRC["rule"]} (rule 1: {why})',
                            patch={'id': r['id'], 'fields': fields}))
        for f in asks:
            out.append(ask('device', FL.ask_line(r, f, ctx)))
    return out


def spans(rows, off):
    out = []
    for r in rows:
        why = [p.split(': ', 1)[1].split(' — ')[0] for p in span_problems(r, off)]
        if why:
            out.append(ask('spans', f'{_t(r)}: {"; ".join(why)} — when did it happen? '
                                    'Its datetime becomes the act (rule 2)'))
    return out


def gate(rows, off):
    """(share lacking device or wellness, rows over 12 h) — the look behind's gate."""
    lived = [r for r in rows if r.get('status') not in NOT_LIVED]
    lack = [r for r in lived if not r.get('wellness') or not r.get('device')]
    long_ = [r for r in rows if r.get('datetime') and r.get('end')
             and utc(r['end']) - utc(r['datetime']) > dt.timedelta(hours=RULES['max_span_hours'])]
    return (len(lack), len(lived)), long_


def run(rows, day, off, local, ctx=None, index=None, catalog_names=(), typical=None):
    ctx = ctx or FL.Context(day_rows=rows, local=local)
    items = (meals(rows, off, (local.get('people') or {}).values())
             + movement(rows, off, day, local, catalog_names, typical)
             + people(rows, index)
             + device(rows, ctx)
             + spans(rows, off))
    items += gaps(rows, off, items)
    for i, it in enumerate(items, 1):
        it['n'] = i
    return items


def render(items, day, rows, off, now_local=None):
    (lack, n), long_ = gate(rows, off)
    fills = [i for i in items if i['kind'] == 'fill']
    lines = [f'dayqa · {day:%a %d %b} — {len(fills)} to accept, {len(items) - len(fills)} to ask']
    for i in items:
        if i['kind'] == 'fill':
            lines.append(f'  {i["n"]}. {i["check"]} · {i["line"]} · {EST} · source: {i["source"]}')
        else:
            lines.append(f'  {i["n"]}. {i["check"]} · ASK · {i["line"]}')
    if not items:
        lines.append('  nothing to fill: every row is whole')
    share = lack / n if n else 0
    lines.append(f'gate: {lack} of {n} rows lack device or wellness ({share:.0%}, the gate is '
                 f'{Q["unfilled_share_max"]:.0%}) · {len(long_)} row(s) over {RULES["max_span_hours"]} h')
    lines.append(marker(day, len(fills), now_local))
    return '\n'.join(lines)


def marker(day, n, now_local=None):
    t = f' {now_local:%H:%M}' if now_local else ''
    return f'{Q["marker"]} {day.isoformat()}{t} · {n} proposed'


# ── reads ───────────────────────────────────────────────────────────────
def connections_index(recs, local):
    cf = local.get('connections_fields') or {}
    people = []
    for r in recs:
        c = cells(r)
        names = [sv(c.get(cf.get('name', 'full name'), c.get('name'))),
                 sv(c.get(cf.get('short', 'short name'), c.get('short')))]
        names += PP.split_aliases(c.get(cf.get('aliases', 'aliases'), c.get('aliases')))
        if any(names):
            people.append((r['id'], [n for n in names if n]))
    return PP.Index(people)


def catalog_typical(recs, local):
    pf = local.get('practices_fields') or {}
    out = {}
    for r in recs:
        c = cells(r)
        name = sv(c.get(pf.get('practice', 'practice'), c.get('practice')))
        v = c.get(pf.get('typical_time', 'typical duration'), c.get('typical duration'))
        if name and isinstance(v, (int, float)) and v > 0:
            out[FL.word(name)] = int(v // 60) if v > 300 else int(v)   # a duration field is seconds
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="one day's QA: meals, gaps, movement, people, device")
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--day', help="a complete read of the day's rows")
    ap.add_argument('--catalog'), ap.add_argument('--rhythms'), ap.add_argument('--connections')
    ap.add_argument('--history', action='append', default=[], help="other weeks' streams, for the ASK hints")
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    now = dt.datetime.now(dt.timezone.utc)
    day = dt.date.fromisoformat(a.date) if a.date else (now + dt.timedelta(hours=offset_hours(L, now))).date()
    sf = L.get('stream_fields', {})
    fields = {**{k: k for k in NAMES}, **{k: v for k, v in sf.items() if k in NAMES}}
    cat = rh = con = None
    hist = []
    if a.live:
        from bedo_air import Air, read_day, read_catalog
        air = Air()
        src, _ = read_day(air, L, day, air.bases())
        cat = complete(read_catalog(air, L), 'catalog')
        b = L.get('bases') or {}
        if b.get('rhythms'):
            rh = complete(air.dump(*b['rhythms'], by_id=bool(L.get('rhythms_fields'))), 'rhythms')
        if b.get('connections'):
            con = complete(air.dump(*b['connections'], by_id=bool(L.get('connections_fields'))), 'connections')
    elif a.day:
        src = a.day
        cat = complete(a.catalog, 'catalog') if a.catalog else None
        rh = complete(a.rhythms, 'rhythms') if a.rhythms else None
        con = complete(a.connections, 'connections') if a.connections else None
    else:
        sys.exit('give --live, or --day')
    for h in a.history:
        hist += as_rows(complete(h, h), fields)
    rows = on_day(as_rows(complete(src, 'day'), fields), day, L)
    off = offset_hours(L, dt.datetime.combine(day, dt.time(12), dt.timezone.utc))
    ctx = FL.Context(catalog=FL.catalog_wellness(cat, L) if cat else None,
                     drives=FL.drive_elements(rh, L) if rh else None,
                     day_rows=rows, history=hist, local=L)
    names = list(FL.catalog_wellness(cat, L)) if cat else []
    items = run(rows, day, off, L, ctx, connections_index(con, L) if con else None, names,
                catalog_typical(cat, L) if cat else None)
    now_local = now + dt.timedelta(hours=offset_hours(L, now))
    if a.json:
        print(json.dumps({'day': day.isoformat(), 'items': items,
                          'marker': marker(day, sum(i['kind'] == 'fill' for i in items), now_local)},
                         ensure_ascii=False, indent=1))
    else:
        print(render(items, day, rows, off, now_local))


if __name__ == '__main__':
    main()
