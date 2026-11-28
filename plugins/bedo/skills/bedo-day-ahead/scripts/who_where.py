# -*- coding: utf-8 -*-
"""Who and where, for the my day page (28 Nov 2026).

Her words, 27 Nov 2026: I haven't seen a sociogram on the my day in a long time. After that, add geography to the
my day too. Those are both important. And on 12 Nov (backlog 261112_f29): I'd also like to see the sociogram, ahead
and behind; for location … and then maybe a map.

The sociogram was drawn only on the day behind, which retired on 8 Nov, so nothing had drawn it since. The day's map
was built for the week look behind's day view, and never wired. Both now come from the same rows the my day page
already reads:

  who     everyone she was with or in touch with today (the `person` field of the rows she lived), grouped by their
          first circle in the connections table and sized by how many of the day's rows they shared; who came up
          with them (`mentioned`) hangs off them. People on what is still ahead today (an open step timed today, an
          event's people) are drawn as ahead, until a lived row has them.
  where   the day's 📍 stays (one row per stay, `place: rec…` naming its row in the places base): the place, when, how
          long, who with and what she did there, longest first; a place added to the base today is new. Today's
          calendar places still ahead are listed as where she's going. Where the places base holds coordinates for
          two places or more, a small map draws them, sized by the time there.

Nothing personal lives here: names, circles and places arrive in the data. The connections and places tables are
read by name in the fetch (`named_connections.json`, `named_places.json`, fields by name), so no id is needed.
"""
import datetime as dt, re

NOT_LIVED = ('▫️potential', '⬜ intention', '⨂ skipped', '✖️ dropped')
OPEN = ('⬜ intention', '▶️ in motion')
_LEAD = re.compile(r'^[^\w]+')


def _sv(v):
    if isinstance(v, dict):
        return v.get('name') or ''
    return v or ''


def _names(v):
    """A person field as names: '♑Wren, ♐Olu' or a list of them."""
    if not v:
        return []
    if isinstance(v, (list, tuple)):
        out = []
        for x in v:
            out += _names(_sv(x))
        return out
    return [n.strip() for n in re.split(r'\s*[,;]\s*', str(v)) if n.strip()]


def _bare(n):
    """A name without its leading glyph, as the page shows it: '♑Wren' → 'Wren'."""
    return _LEAD.sub('', n or '').strip()


# ── the connections table, by name ─────────────────────────────────────────
class People:
    """Who belongs to which circle: the FIRST circle listed wins (the day behind's rule, 25 Sep 2026). A person is
    found by any name they go by (core/bedo_people)."""

    def __init__(self, recs=None, order=None):
        import bedo_people
        self._bp = bedo_people
        people, self.circle, self.label = [], {}, {}
        for r in recs or []:
            f = r.get('fields') or {}
            circ = f.get('circle') or f.get('circles') or []
            circ = [circ] if isinstance(circ, (str, dict)) else circ
            names = [_sv(f.get('name')), _sv(f.get('short name') or f.get('short'))]
            names += bedo_people.split_aliases(f.get('aliases'))
            names = [n for n in names if n]
            if not names:
                continue
            people.append((r['id'], names))
            self.circle[r['id']] = _sv(circ[0]) if circ else ''
            self.label[r['id']] = _sv(f.get('short name') or f.get('short')) or _sv(f.get('name'))
        self.index = bedo_people.Index(people)
        self.order = list(order or []) or sorted({c for c in self.circle.values() if c})

    def key(self, name):
        return self.index.find(name) or ('?' + self._bp.norm(name))

    def circle_of(self, key):
        return self.circle.get(key, '')

    def name_of(self, key, seen):
        """As the rows write them ('♐Olu' → 'Olu', 'Kit (the shop)' → 'Kit'); the table's short name is only for one
        the rows never wrote."""
        return re.sub(r'\s*\([^)]*\)', '', _bare(seen)).strip() or self.label.get(key) or ''


def _to(ts, off):
    """Her own clock, naive, so it compares with the build's `now`."""
    return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).replace(tzinfo=None)


def _later(it, today, now):
    """A calendar item still to come: not ticked, and not over on her clock."""
    if it.get('done'):
        return False
    if now is None or not it.get('b'):
        return True
    try:
        h, m = map(int, it['b'].split(':'))
    except ValueError:
        return True
    return dt.datetime.combine(today, dt.time(h, m)) >= now


def _clock(t):
    return f"{t.hour % 12 or 12}:{t.minute:02d}{'a' if t.hour < 12 else 'p'}"


def _day_rows(rows, F, off, today):
    for r in rows:
        c = r.get('cellValuesByFieldId') or {}
        when = c.get(F['when'])
        if not when:
            continue
        a = _to(when, off)
        if a.date() != today:
            continue
        end = c.get(F['end']) if F.get('end') else None
        b = _to(end, off) if end else None
        if b and (b <= a or b - a > dt.timedelta(hours=14)):
            b = None
        yield r, c, a, b, _sv(c.get(F['status']))


def who_of(rows, F, off, today, people, me='', schedule=(), now=None):
    """DATA.who: the day's sociogram, ahead and behind."""
    me_k = people.key(me) if me else None
    first, spans, shared, seen, via = {}, {}, {}, {}, {}
    ahead = {}
    for r, c, a, b, st in sorted(_day_rows(rows, F, off, today), key=lambda x: x[2]):
        names = _names(c.get(F['person']))
        keys = [k for k in (people.key(n) for n in names) if k != me_k]
        for n, k in zip([n for n in names if people.key(n) != me_k], keys):
            seen.setdefault(k, n)
        if st in OPEN and (now is None or a >= now):
            for k in keys:
                ahead.setdefault(k, a)
            continue
        if st in NOT_LIVED:
            continue
        for k in keys:
            first[k] = min(first.get(k, a), a)
            shared[k] = shared.get(k, 0) + 1
            if b:
                spans.setdefault(k, []).append((a, b))
        if F.get('mentioned'):
            for m in _names(c.get(F['mentioned'])):
                mk = people.key(m)
                if mk == me_k or mk in keys:
                    continue
                for k in keys:
                    via.setdefault(k, [])
                    if m not in via[k]:
                        via[k].append(m)
    # an event's people, still ahead (the calendar it came from names them: `calendar_people`)
    for it in schedule or ():
        if it.get('k') != 'event' or not _later(it, today, now):
            continue
        w = it.get('with')
        for n in _names(w if isinstance(w, (list, tuple)) else (w or '')):
            k = people.key(n)
            if k != me_k:
                seen.setdefault(k, n)
                ahead.setdefault(k, None)

    def when_of(k):
        sp = sorted(spans.get(k) or [])
        if not sp:
            return _clock(first[k])
        merged = []
        for s, e in sp:
            if merged and s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        mins = sum((e - s).total_seconds() / 60 for s, e in merged)
        if mins >= 480:
            return 'all day'
        return f'{_clock(merged[0][0])}–{_clock(merged[-1][1])}'

    order = people.order
    rank = lambda k: order.index(people.circle_of(k)) if people.circle_of(k) in order else len(order)
    out = [dict(name=people.name_of(k, seen.get(k, '')), circle=people.circle_of(k), n=shared[k], when=when_of(k),
                **({'via': [_bare(m) for m in via[k]]} if via.get(k) else {}))
           for k in sorted(first, key=lambda k: (rank(k), -shared[k], first[k]))]
    out += [dict(name=people.name_of(k, seen.get(k, '')), circle=people.circle_of(k), n=0, ahead=True,
                 when=_clock(at) if at else 'later today')
            for k, at in sorted(ahead.items(), key=lambda x: (rank(x[0]), x[1] or dt.datetime.max)) if k not in first]
    if not out:
        return None
    return dict(order=order, people=out)


# ── where ──────────────────────────────────────────────────────────────────
PLACE_REF = re.compile(r'\bplace:\s*(rec[A-Za-z0-9]+|new)\b')
_VIRTUAL = re.compile(r'(?i)\b(teams|zoom|virtual|meet\.google|webex|online)\b|https?://')


def _word(p):
    return re.sub(r'^[^\w]+', '', p or '').strip().lower()


def coords(text):
    m = re.match(r'\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$', text or '')
    if not m:
        return None
    lat, lng = float(m.group(1)), float(m.group(2))
    return (lat, lng) if -90 <= lat <= 90 and -180 <= lng <= 180 else None


def where_of(rows, F, off, today, places=None, schedule=(), now=None, location='location', home_names=('home',),
             me='', skip_rhythms=()):
    """DATA.where: the day's stays from its 📍 rows, the calendar's places still ahead, and a map when the places
    base holds coordinates."""
    by_id = {p['id']: p.get('fields') or {} for p in places or []}
    loc = _word(location)
    day = list(_day_rows(rows, F, off, today))
    stays = {}
    for r, c, a, b, st in day:
        if _word(_sv(c.get(F['practice']))) != loc or st in NOT_LIVED:
            continue
        det = c.get(F['details']) or ''
        m = PLACE_REF.search(det)
        ref = m.group(1) if m else ''
        p = by_id.get(ref) or {}
        name = (_sv(p.get('place')) or _LEAD.sub('', (c.get(F['title']) or '')).strip() or 'a place')
        if name.strip().casefold() in {h.casefold() for h in home_names}:
            continue
        k = ref if ref.startswith('rec') else name.casefold()
        s = stays.setdefault(k, dict(name=name, minutes=0, at=[], who=[], did=[], kind=_sv(p.get('serves')),
                                     new=ref == 'new' or _sv(p.get('added')) == today.isoformat(),
                                     ll=coords(_sv(p.get('coordinates'))), first=a))
        s['first'] = min(s['first'], a)
        if b:
            s['minutes'] += (b - a).total_seconds() / 60
            s['at'].append(f'{_clock(a)}–{_clock(b)}')
        else:
            s['at'].append(_clock(a))
        for n in _names(c.get(F['person'])):
            n = _bare(n)
            if n and n != _bare(me) and n not in s['who']:
                s['who'].append(n)
        # what she did there: the day's other lived rows inside the stay, never another place or the drive there
        for r2, c2, a2, b2, st2 in day:
            if not b or st2 in NOT_LIVED or not (a <= a2 < b):
                continue
            if _word(_sv(c2.get(F['practice']))) in (loc, 'driving', 'travel'):
                continue
            # be•do's own work and a filler row are not what she did there
            if F.get('rhythm') and (c2.get(F['rhythm']) or '').strip() in skip_rhythms:
                continue
            t = _LEAD.sub('', (c2.get(F['title']) or '')).strip()
            if '📍' in t or re.match(r'(?i)(screenshots?|screen clips?|receipts?)\b', t):
                continue
            if t and t not in s['did'] and len(s['did']) < 3:
                s['did'].append(t)
    out = sorted(stays.values(), key=lambda s: (-s['minutes'], s['first']))
    # the calendar's places still ahead today, off her own clock (a call or an office link is no place)
    going = []
    for it in schedule or ():
        w = (it.get('where') or '').strip()
        if it.get('k') != 'event' or not w or _VIRTUAL.search(w) or not _later(it, today, now):
            continue
        going.append(dict(t=it.get('t') or '', a=it.get('a') or '', where=w))
    # the drive between, from the day's 🚗 rows: how much of the day was on the road
    road = sum((b - a).total_seconds() / 60 for r, c, a, b, st in day
               if b and st not in NOT_LIVED and _word(_sv(c.get(F['practice']))) in ('driving', 'travel'))
    if not out and not going:
        # a finished day with no stay was at home, by the record: time not inside a stay is home (5 Nov 2026)
        return dict(stays=[], going=[], road=round(road), map=None, placed=0, home=True) \
            if now is not None and now.date() > today else None
    pts = [s for s in out if s['ll']]
    dots = None
    if len(pts) >= 2:
        la = [s['ll'][0] for s in pts]; lo = [s['ll'][1] for s in pts]
        y0, y1, x0, x1 = min(la), max(la), min(lo), max(lo)
        k = max(y1 - y0, (x1 - x0) * 0.85, 1e-6)    # the same scale both ways, longitude narrowed for her latitude
        dots = [dict(i=out.index(s), x=round(0.5 + ((s['ll'][1] - (x0 + x1) / 2) * 0.85) / k * 0.8, 3),
                     y=round(0.5 - (s['ll'][0] - (y0 + y1) / 2) / k * 0.8, 3)) for s in pts]
    return dict(stays=[dict(name=s['name'], hours=round(s['minutes'] / 60, 2), at=', '.join(s['at']),
                            who=', '.join(s['who']), did=' · '.join(s['did']), kind=s['kind'], new=s['new'])
                       for s in out],
                going=going, road=round(road), map=dots,
                placed=sum(1 for s in out if s['ll']))
