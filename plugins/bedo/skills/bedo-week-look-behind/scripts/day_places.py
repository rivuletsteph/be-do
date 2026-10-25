# -*- coding: utf-8 -*-
"""Where she was: the day's places, in order, with the drives between them.

Her word, 25 Oct 2026: every place that shows up on Google Maps belongs on her
map; the day behind's map card first, the week behind after. The places catalog
(its own base) holds a place once; the stream holds each visit. This reads the
visits back out of the stream, from three kinds of evidence, best first:

1. a 📍 location row — the place, its span, who was there;
2. a Timeline stop named in a row's details, as the map check and the dusk
   retiming write them: "Times from her Timeline: Some Diner, 12 Main St,
   Sometown, 1:47–2:16 PM", "At the Old Mill 11:58 AM–1:24 PM", a map check's
   "> Some Cafe, 5 Elm St · 10:16 AM – 12:22 PM". A line counts only when it
   cites Timeline, or sits on a 🚗 driving, 📍 location or 🗺️ map check row —
   calendar times and estimates are not places;
3. the time between two 🚗 drives, named by the drives ("drive to X", "drive
   home from Y", "X to Y" in the details).

A stop that mostly overlaps one already found is the same visit. Each stop
carries what happened there (the day's lived rows inside it, moments first) and
who was with her, and is matched to the places catalog by name or street
address: a catalog place named home or work names the stop; one she wants to
go to is marked reached. Nothing is written back — a stop the catalog doesn't
know is listed for her to name, never added.

Nothing personal lives here: home, work and every other place come from the
stream and the catalog.
"""
import datetime as dt
import re

DRIVE, LOCATION, MAP_CHECK = 'driving', 'location', 'map check'
MOVING = {'walking', 'cycling', 'hike', 'running'}   # a gap between drives spent moving is a walk, not a place
STOP_MIN = 5            # two drives closer than this are one trip, not a stop
RANGE = re.compile(r'(\d{1,2}):(\d{2})\s*(AM|PM)?\s*[–-]\s*(\d{1,2}):(\d{2})\s*(AM|PM)')
DIST = re.compile(r'\b(\d+(?:\.\d+)?)\s*mi\b')
# a label that is about time, travel or the record itself is not a place
NOT_PLACE = re.compile(r'\b(estimated|about|recorded|screenshots?|logged|messages?|stretch|minutes?|hours?|min|'
                       r'drove|driving|drive|walk(?:ed|ing)?|hike|left|timeline|oura|calendar|times?|retimed|'
                       r'placed|corrected|photos?|steps)\b|\d:\d\d|\bmi\b', re.I)
LEAD = re.compile(r'^(?:\W|\[be•do\])*', re.I)
MOMENT = ('⭐', '✨', '🌟', '💫', '🎉', '🪨')
QUIET = {'map check', 'action check', 'qa check', 'dusk flow close', 'dawn flow close', 'look behind', 'look ahead',
         'evening oura', 'morning oura', 'phone charging', 'intention check', 'usage check', 'weather check'}


def low(p):
    return re.sub(r'^[^\w]+', '', p or '').strip().lower()


def names(v):
    if not v:
        return []
    if isinstance(v, list):
        return [x.get('name') if isinstance(x, dict) else str(x) for x in v]
    return [x.strip() for x in re.split(r',|\s·\s', str(v)) if x.strip()]


def bare(t):
    """A title without its glyph: '🚗 drive to X' → 'drive to X'."""
    return re.sub(r'^[^\w]+', '', t or '').strip()


def key(s):
    """For matching: lower case, no glyphs, no leading 'the', no punctuation."""
    s = re.sub(r'[^\w\s]', ' ', (s or '').lower())
    s = re.sub(r'^\s*the\s+', '', s)
    return ' '.join(s.split())


def street(s):
    """The street address in a text, as a match key: '3080 W Washington St, …' → '3080 w washington st'."""
    m = re.search(r'\b(\d{2,6}\s+[A-Za-z0-9 .\'-]+?)(?:,|$|\.\s)', s or '')
    return key(m.group(1)) if m else ''


def clock_range(m, day):
    """A Timeline range on the day: the first time takes the second's AM/PM unless that puts it after the second."""
    h1, m1, ap1, h2, m2, ap2 = m.groups()

    def t(h, mm, ap):
        h = int(h) % 12 + (12 if ap == 'PM' else 0)
        return dt.datetime.combine(day, dt.time(h, int(mm)))
    b = t(h2, m2, ap2)
    a = t(h1, m1, ap1 or ap2)
    if not ap1 and a > b:
        a = t(h1, m1, 'AM' if ap2 == 'PM' else 'PM')
    return (a, b) if a < b else (None, None)


def label(text):
    """The place named just before a time range, or None.
    'From her Timeline: Some Diner, 12 Main St, Sometown,' → ('Some Diner', '12 Main St, Sometown')."""
    s = text.strip().rstrip(',;·—–- ').strip()
    if ': ' in s:
        s = s.rsplit(': ', 1)[1]
    s = re.split(r'(?:^|\s)[Aa]t\s+', s)[-1]
    s = re.sub(r'^(?:>\s*)+', '', LEAD.sub('', s)).strip(' ,')
    parts = [p.strip() for p in re.split(r',\s*|\s+·\s+', s) if p.strip()]
    while parts and NOT_PLACE.search(parts[0]):     # 'drove 10:49, rec center' → 'rec center'
        parts.pop(0)
    if not parts or len(parts[0]) < 3 or len(parts[0]) > 70 or any(NOT_PLACE.search(p) for p in parts):
        return None
    return parts[0], ', '.join(parts[1:])


def mentions(text, day, on_travel_row):
    """Every Timeline stop a row's details name: (name, address, start, end)."""
    out = []
    for line in (text or '').split('\n'):
        if not (on_travel_row or 'Timeline' in line):
            continue
        for seg in re.split(r'(?<=[.;])\s|,\s+then\s+|\(|\)', line):
            prev = 0
            for m in RANGE.finditer(seg):
                got = label(seg[prev:m.start()])
                prev = m.end()
                if not got:
                    continue
                a, b = clock_range(m, day)
                if a:
                    out.append((got[0], got[1], a, b))
    return out


def ends(title, details):
    """Where a drive started and where it went, from its title, else from its details."""
    t = bare(title).split(' — ')[0]
    t = re.split(r',\s|\s+(?:with|after|for|on the way|by)\s', t)[0].strip()
    o = d = None
    if re.match(r'(?i)drive home\b', t):
        d = 'home'
        m = re.search(r'(?i)\bfrom\s+(.+)$', t)
        o = m.group(1) if m else None
    else:
        m = re.search(r'(?i)\bfrom\s+(.+?)\s+to\s+(.+)$', t)
        if m:
            o, d = m.groups()
        else:
            m = re.search(r'(?i)\bto\s+(.+)$', t)
            d = m.group(1) if m else None
            m = re.search(r'(?i)\bfrom\s+(.+)$', t)
            o = m.group(1) if m else o
    # the screenshot line often says it plainly: '…, 10:21–10:49 AM, home to Sometown.'
    m = re.search(r'(?:AM|PM),\s*(?:from\s+)?([^,.;]+?)\s+to\s+([^,.;]+)', details or '')
    if m and not DIST.search(m.group(0)):
        o, d = o or m.group(1).strip(), d or m.group(2).strip()
    if not o and re.search(r'(?i)\b(?:from home|left home|home to)\b', details or ''):
        o = 'home'
    clean = lambda x: re.sub(r'^(?:the start of\s+)', '', x.strip()) if x else None   # noqa: E731
    return clean(o), clean(d)


def day_places(rows, day, L, catalog=(), not_lived=frozenset(), flows=frozenset()):
    """The map card's data for one day, from rows already deduped (live base first).
    Rows carry 'when', 'end' (ISO, UTC), 'practice', 'title', 'status', 'person', 'details'.
    `catalog` is the places base as a list of {'id', 'place', 'standing', 'where', 'serves'}."""
    off = dt.timedelta(hours=L['utc_offset_hours'])
    s0 = dt.datetime.combine(day, dt.time())
    e0 = s0 + dt.timedelta(days=1)
    me = {key(x) for x in names(L.get('self_person'))}

    def local(ts):
        return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).replace(tzinfo=None) if ts else None

    lived = []
    for r in rows:
        if r.get('status') in not_lived:
            continue
        a, b = local(r.get('when')), local(r.get('end'))
        if a and (s0 <= a < e0 or (b and a < s0 < b)):
            lived.append(dict(r, _a=a, _b=b if b and b > a else None, _p=low(r.get('practice'))))
    lived.sort(key=lambda r: r['_a'])

    # ── the drives: the legs of the day's route ──
    legs = []
    for r in lived:
        if r['_p'] != DRIVE or not r['_b']:
            continue
        o, d = ends(r.get('title'), r.get('details'))
        mi = DIST.search(r.get('details') or '')
        legs.append(dict(a=r['_a'], b=r['_b'], o=o, d=d, mi=float(mi.group(1)) if mi else None, t=bare(r.get('title'))))

    # ── the stops, best evidence first ──
    cands = []
    for r in lived:
        if r['_p'] == LOCATION:
            t = bare(r.get('title'))
            name, _, note = t.partition(' — ')            # a 📍 title is the place as she'd say it
            cands.append(dict(n=name.strip(), addr=_address(r.get('details')), a=r['_a'],
                              b=r['_b'] or r['_a'] + dt.timedelta(minutes=STOP_MIN),
                              note=note.strip(), src='📍', rank=0))
    for r in lived:
        travel = r['_p'] in (DRIVE, LOCATION, MAP_CHECK)
        for n, addr, a, b in mentions(r.get('details'), r['_a'].date(), travel):
            if s0 <= a < e0:
                cands.append(dict(n=n, addr=addr, a=a, b=b, note='', src='Timeline', rank=1))
    def placename(*xs):
        return next((x for x in xs if x and not NOT_PLACE.search(x)), None)

    for i, lg in enumerate(legs):     # between two drives, she was somewhere
        nxt = legs[i + 1] if i + 1 < len(legs) else None
        if i == 0 and placename(lg['o']):
            cands.append(dict(n=lg['o'], addr='', a=None, b=lg['a'], note='', src='drives', rank=2))
        if nxt and (nxt['a'] - lg['b']).total_seconds() >= STOP_MIN * 60:
            a, b = lg['b'], nxt['a']
            walk = [r for r in lived if r['_p'] in MOVING and r['_b'] and r['_a'] < b and r['_b'] > a]
            if sum((min(r['_b'], b) - max(r['_a'], a)).total_seconds() for r in walk) >= (b - a).total_seconds() / 2:
                mi = DIST.search(' '.join(r.get('details') or '' for r in walk))
                cands.append(dict(n=bare(walk[0].get('title')).split(' — ')[0], addr='', a=a, b=b, note='', src='drives',
                                  rank=2, move=_glyph(walk[0].get('practice')), mi=float(mi.group(1)) if mi else None))
            else:
                cands.append(dict(n=placename(lg['d'], nxt['o']) or 'a stop', addr='', a=a, b=b, note='', src='drives', rank=2))
        if not nxt and placename(lg['d']):
            cands.append(dict(n=lg['d'], addr='', a=lg['b'], b=None, note='', src='drives', rank=2))

    def span(c):
        return (c['a'] or s0, c['b'] or e0)

    def overlap(x, y):
        (a1, b1), (a2, b2) = span(x), span(y)
        o = (min(b1, b2) - max(a1, a2)).total_seconds()
        shortest = min((b1 - a1).total_seconds(), (b2 - a2).total_seconds()) or 1
        return o / shortest

    stops = []
    for c in sorted(cands, key=lambda c: c['rank']):
        same = [s for s in stops if overlap(c, s) > .5]
        if same:
            s = same[0]       # the better evidence keeps the visit; a later one may still carry its address
            s['addr'] = s['addr'] or c['addr']
            continue
        stops.append(c)
    stops.sort(key=lambda s: s['a'] or s0)

    # ── the catalog: home and work by name, a reached want-to-go, the rest left for her ──
    cat = [dict(p, _k=key(p.get('place')), _s=street(p.get('where'))) for p in (catalog or []) if p.get('place')]

    def within(short, long):
        """Whole words of a name of some length inside another: 'pine hollow' in 'pine hollow smokehouse'."""
        return len(short) >= 8 and f' {short} ' in f' {long} '

    def match(s):
        if s.get('move'):
            return None
        k, st = key(s['n']), street(s['n'] + ', ' + s['addr'])
        for p in cat:
            if p['_s'] and st and p['_s'] == st:
                return p
            if p['_k'] and (p['_k'] == k or within(p['_k'], k) or within(k, p['_k'])):
                return p
        return None

    out, names_seen = [], set()
    for s in stops:
        p = match(s)
        name = s['n']
        if p and key(p['place']) in ('home', 'work'):
            name = p['place']
        home = key(name) == 'home'
        a, b = s['a'], s['b']
        lo, hi = a or s0, b or e0
        inside = [r for r in lived if lo <= r['_a'] < hi and r['_p'] not in (DRIVE, LOCATION) and r['_p'] not in QUIET
                  and r['_p'] not in flows]
        inside.sort(key=lambda r: (not (r.get('practice') or '').startswith(MOMENT), r['_a']))
        if s.get('move'):
            inside = [r for r in inside if r['_p'] not in MOVING]
        if home:      # at home, only what stood out: the rest of a day at home is the rest of the page
            inside = [r for r in inside if (r.get('practice') or '').startswith(MOMENT)]
        who = []
        for r in lived:
            if r['_p'] == DRIVE:
                continue
            ra, rb = r['_a'], r['_b'] or r['_a']
            if lo <= ra < hi or (ra < lo < rb):
                for n in names(r.get('person')):
                    if key(n) not in me and n not in who:
                        who.append(n)
        standing = (p.get('standing') or '') if p else ''
        if isinstance(standing, dict):
            standing = standing.get('name') or ''
        mins = int((b - a).total_seconds() // 60) if a and b else None
        out.append(dict(n=name, addr=s['addr'], a=_m(a, s0), b=_m(b, s0), min=mins, home=home, src=s['src'],
                        move=s.get('move'), mi=s.get('mi'),
                        note=s['note'], who=who,
                        did=[[_glyph(r.get('practice')), bare(r.get('title')).split(' — ')[0]] for r in inside[:4]],
                        more=max(0, len(inside) - 4),
                        place=dict(id=p['id'], standing=standing) if p else None))
        if not home and not s.get('move'):
            names_seen.add(key(name))

    legs_out = [dict(a=_m(lg['a'], s0), b=_m(lg['b'], s0), mi=lg['mi'], t=lg['t'],
                     min=int((lg['b'] - lg['a']).total_seconds() // 60)) for lg in legs]
    miles = sum(lg['mi'] or 0 for lg in legs)
    return dict(stops=out, legs=legs_out,
                totals=dict(places=len(names_seen), miles=round(miles, 1), drive_min=sum(lg['min'] for lg in legs_out),
                            drives=len(legs_out)),
                unknown=sorted({s['n'] for s in out if not s['place'] and not s['home'] and not s['move'] and s['n'] != 'a stop'}))


def _address(text):
    """The first street address in a row's details, as written."""
    m = re.search(r'\b\d{2,6}\s+[A-Za-z0-9 .\'-]+?(?:,\s*[A-Z][A-Za-z .]+?)?(?=[.;\n]|$)', text or '')
    return m.group(0).strip() if m else ''


def _glyph(p):
    m = re.match(r'^([^\w\s]+)', (p or '').strip())
    return m.group(1) if m else '·'


def _m(t, s0):
    return int((t - s0).total_seconds() // 60) if t else None
