"""flow.py — how things flow: the day ahead built around the day's lean (29 Oct 2026).

Her words: the whole map should become something like how things flow, and be more
of the basis; tending and growing are different actions, and some days want the
minimum of one and the most of the other, so the system needs to respond to that;
and choose for me, based on my readiness and how caught up I am.

It reads a built day-ahead page (its DATA: the whole map and card 1), the stream
and rhythms reads beside it, and the day behinds of the week before, and writes one
page:

  base flow   the morning card, drawn as water through the last seven mornings:
              body (this morning's readiness), balance (how evenly the day before's
              wheel was shared) and buffer (what is past its date), each 0–100, in
              equal parts. Tap a morning to see how its number was made.
  the lean    be•do chooses a tending day, balanced, or a growing day from base flow
              (and a knocked-back secure base). Today only, no switch.
  the blocks  each rhythm, its tending first, then the drives that grow out of it,
              each drive with its goal, its easiest next step first.
  the flow    steps → drives → rhythms → a balanced wellness wheel, the foundation;
              each drive also on to the destinations it serves.
  intention   after the lean: how much the day holds (today's free hours off the
              calendar, scaled by base flow), filled from the easiest next steps she taps, in
              the lean's order. Steps record no size yet; be•do guesses one, said so.

    python3 flow.py --day-ahead DAY-day-ahead.html --local day_ahead_local.json \
        [--behind DIR] --out DAY-flow.html

`--behind` is a folder of day behinds (YYYY-MM-DD-day-behind.html), read first when
one carries the wheel. The day page that replaced the canon on 25 Oct carries no wheel,
so balance is read from the stream itself (30 Oct 2026): the day's lived rows by their
wellness element (`fields.stream.wellness`); without that field it is left out and
said so. The stream and rhythms reads are data/ beside the
settings file, as the runner leaves them.
"""
import argparse, datetime as dt, glob, json, math, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
BF_DIR = os.path.join(HERE, '..', '..', '..', 'assets', 'base-flow')
OPEN = ('⬜ intention', '▶️ in motion')
CLOSED = ('✅ done', '✖️ dropped')
BUF_TEND, BUF_GROW, BUF_PER = 1.5, 1.0, 6   # buffer: a late tending step weighs 1.5, a growing one 1; 6 a point
WEEK = 7
STEP_DAY_HOURS = 8                          # the hours of a day that could go to steps, before the calendar
SHARE = {'optimal': 0.75, 'good': 0.5, 'pay attention': 0.25}   # how much of the free time to aim for, by base flow
SIZES = (15, 60, 240)                       # 15 min · 1 h · half day, in minutes
QUICK = re.compile(r'\b(call|text|email|e-mail|reply|respond|pay|book|order|schedule|send|ask|confirm|sign|renew|cancel|'
                   r'buy|rsvp|remind|check|forward|share|submit|look up|note)\b', re.I)
LONG = re.compile(r'\b(model|build|draft|write|analy[sz]e|analysis|estimate|database|report|presentation|proposal|'
                  r'paper|chapter|tidy the house|deep clean|decorat\w*|plan the|redesign|set up|organi[sz]e)\b', re.I)


def page_data(path):
    h = open(path, encoding='utf-8').read()
    return h, json.JSONDecoder().raw_decode(h[h.index('{"chip"'):])[0]


def evenness(domains):
    """How evenly the wheel's elements shared the day, 0–100: 100 when all eight are equal."""
    tot = sum(domains.values())
    if not tot:
        return None
    ps = [v / tot for v in domains.values() if v > 0]
    return round(100 * -sum(x * math.log(x) for x in ps) / math.log(max(len(domains), 2)))


WHEEL = ('heart', 'mind', 'body', 'spirit', 'water', 'air', 'earth', 'fire')
NOT_LIVED = ('▫️potential', '⬜ intention', '⨂ skipped', '✖️ dropped')
RESTING = ('sleep', 'nap')                  # sleep scores nothing on the wheel (the canon's zero_practices)
DIVISOR = 6                                 # a real span weighs its minutes over six, as the canon does


def wheel_of(day, rows, F, off):
    """The day's wheel from its own rows (30 Oct 2026): each lived row under its wellness
    element, a real span weighing its minutes over six and a moment weighing one (the canon
    weighs a moment by its practice's effort band, which this read doesn't carry)."""
    if not F.get('wellness'):
        return None
    dom = {k: 0.0 for k in WHEEL}
    to = lambda ts: dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off
    for r in rows:
        c = r['cellValuesByFieldId']
        w, st = c.get(F['wellness']), c.get(F['status']) or ''
        w = (w.get('name') if isinstance(w, dict) else w) or ''
        k = next((x for x in WHEEL if w.lower().endswith(x)), None)
        when = c.get(F['when'])
        if not k or not when or st in NOT_LIVED or to(when).date() != day:
            continue
        if any(x in (c.get(F['practice']) or '').lower() for x in RESTING):
            continue
        end = c.get(F['end'])
        mins = (to(end) - to(when)).total_seconds() / 60 if end else 0
        dom[k] += mins / DIVISOR if 0 < mins <= 12 * 60 else 1.0
    return {k: round(v, 1) for k, v in dom.items()}


def first_sentence(goal):
    """A drive's goal in her words: above the divider, the first sentence or so."""
    g = (goal or '').split('———')[0].split('[be•do]')[0].strip()
    if not g:
        return ''
    g = ' '.join(g.split())
    m = re.match(r'(.{40,160}?[.;:])(\s|$)', g)
    return (m.group(1) if m else g[:160]).strip()


def size_guess(title):
    """be•do's guess at a step's size in minutes, read off its words — 15 min, 1 h or half a day.
    Steps record no size yet, so every one of these is a guess and the page says so."""
    t = title or ''
    if LONG.search(t):
        return SIZES[2]
    if QUICK.search(t):
        return SIZES[0]
    return SIZES[1]


def clock(day, s):
    """'3:30p' / '11a' on that day, as a time; None when there is no time."""
    m = re.fullmatch(r'(\d{1,2})(?::(\d\d))?([ap])m?', (s or '').strip())
    if not m:
        return None
    h = int(m.group(1)) % 12 + (12 if m.group(3) == 'p' else 0)
    return dt.datetime.combine(day, dt.time(h, int(m.group(2) or 0)))


def day_holds(day_page, L):
    """Today's free hours, off the calendar the day-ahead page carries: the hours a day could give to
    steps (`step_day_hours`, default 8), less her own timed events today and the travel buffer around
    each one at a place. Someone else's events, all-day ones and ones carried in from yesterday don't
    take her time. `full_day_hours` booked is a full day, as the day-ahead page reads it."""
    day = dt.date.fromisoformat(day_page['date'])
    booked = travel = 0.0
    n = 0
    for e in day_page.get('events') or []:
        if e.get('who') != 'you':
            continue
        try:
            a = dt.datetime.fromisoformat(e['sort'])
        except (KeyError, ValueError):
            continue
        b = clock(day, e.get('end'))
        if a.date() != day or not e.get('when') or not b or b <= a:
            continue
        n += 1
        booked += (b - a).total_seconds() / 3600
        if (e.get('where') or '').strip():
            travel += L.get('travel_buffer_min', 45) / 60
    whole = L.get('step_day_hours', STEP_DAY_HOURS)
    return dict(whole=whole, booked=round(booked, 2), travel=round(travel, 2), events=n,
                free=round(max(0.0, whole - booked - travel), 2),
                full=booked >= L.get('full_day_hours', 4) or n >= L.get('full_day_events', 4), share=SHARE)


def buffer_on(morning, rows, F, rhythm_names, hidden, local):
    """Open steps already past their date that morning (closed later counts as open before), tending
    heavier than growing. Set aside as the page sets them aside: queued, waiting, quickies, a row that is
    a calendar event's own, and build work on a hidden drive."""
    tend = grow = 0
    for r in rows:
        c = r['cellValuesByFieldId']
        tg = c.get(F['target'])
        if not tg or c.get(F['queue']) or c.get(F['waiting']):
            continue
        if (F.get('quickie') and c.get(F['quickie'])) or (F.get('event') and c.get(F['event'])):
            continue
        rh = (c.get(F['rhythm']) or '').strip()
        if rh in hidden or local(tg) >= morning or local(r['createdTime']) > morning:
            continue
        st = c.get(F['status']) or ''
        end = c.get(F['end'])
        if not (st in OPEN or (st in CLOSED and end and local(end) >= morning)):
            continue
        if rh in rhythm_names:
            tend += 1
        else:
            grow += 1
    return dict(value=max(0, round(100 - BUF_PER * (BUF_TEND * tend + BUF_GROW * grow))), tend=tend, grow=grow)


# the day behind's own categories (31 Oct 2026, her words: I'd love to see the colour coding of the being
# and doing on my calendar, the same as the day behind graphic, maybe even the same categories — as I move
# through the day I see the blocks, and at the end of the day it all gets turned into a circle). The sets
# are the day behind's (bedo-week-look-behind/scripts/day_rings.py), read from there when it's beside us.
try:
    sys.path.insert(0, os.path.join(HERE, '..', '..', 'bedo-week-look-behind', 'scripts'))
    sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'core'))
    import day_rings as _DR
    SLEEP, EAT, MOVE, PERSONAL, RECREATION, TV, COOK, MAKE, HOME, TRAVEL, MOMENTS = (
        _DR.SLEEP, _DR.EAT, _DR.MOVE, _DR.PERSONAL, _DR.RECREATION, _DR.TV, _DR.COOK, _DR.MAKE, _DR.HOME,
        _DR.TRAVEL, _DR.MOMENTS)
except Exception:                                   # a copy without the day behind beside it
    SLEEP = {'sleep', 'nap'}
    EAT = {'breakfast', 'lunch', 'dinner', 'snack', 'coffee', 'smoothie', 'tea', 'morning water', 'water', 'drink'}
    MOVE = {'morning movement', 'walking', 'strength training', 'barre', 'cycling', 'yoga', 'morning sun', 'evening sun'}
    PERSONAL = {'shower', 'bath', 'evening hygiene', 'getting ready', 'skincare'}
    RECREATION = {'book', 'podcast', 'show', 'movie', 'video', 'game', 'glimmer', 'social', 'song', 'puzzle'}
    TV = {'show', 'movie', 'video'}
    COOK = {'dinner prep', 'meal prep', 'cooking', 'lunch prep', 'breakfast prep', 'baking'}
    MAKE = {'cooking', 'baking', 'building', 'gardening', 'crafting', 'making'}
    HOME = {'clean', 'laundry', 'laundry move', 'care task', 'dishes', 'tidy', 'errand'}
    TRAVEL = {'riding', 'flight', 'travel'}
    MOMENTS = {'highlight', 'glimmer', 'gratitude', 'insight', 'milestone', 'journal'}
BEING = ('eat', 'move', 'personal', 'recreation', 'travel')


def care_settings(L):
    """The day behind's care and recreation settings (`care`, `recreation`, `system_rhythm`): from the day-ahead
    settings when they carry them, else the look-behind settings row, read live; without either, none."""
    if L.get('care'):
        return L
    try:
        import bedo_settings
        B, _ = bedo_settings.fetch('look_behind_local')
        return B or {}
    except Exception:
        return {}


def low(p):
    return re.sub(r'^[^\w]+', '', p or '').strip().lower()


def kind_of(c, F, flows, C):
    """One row's category on the day behind's rainbow, one per block: being (eating and drinking, moving,
    personal care, recreation, travel) or doing (professional work, family care, pet care, home care,
    making, driving, be•do), else a flow step or a moment."""
    pr = low(c.get(F['practice']))
    rh = (c.get(F['rhythm']) or '')
    title = c.get(F['title']) or ''
    who = (c.get(F['person']) or '') + ' ' + (c.get(F.get('mentioned', '')) or '' if F.get('mentioned') else '')
    care = C.get('care') or {}
    fam = care.get('family') or care
    if pr in MOMENTS:
        return 'moment'
    for k, ks in (('eat', EAT), ('move', MOVE), ('personal', PERSONAL), ('drive', {'driving'}), ('travel', TRAVEL)):
        if pr in ks:
            return k
    if pr in COOK or pr in MAKE:
        return 'cook'
    if pr == 'action':                                       # an action says what it is in its own words
        tl = title.lower()
        if re.search(r'\b(clean|tidy|vacuum|laundry|dishes|bathrooms?|kitchen|mop|sweep)\b', tl):
            return 'home'
        if re.search(r'\b(cook|bake|baking|appetizers?|bruschetta|spaghetti|dinner|lunch|breakfast|zombie brains|food)\b', tl):
            return 'cook'
    if pr in RECREATION or pr in TV or any(x in rh for x in (C.get('recreation') or {}).get('rhythms') or ()):
        return 'recreation'
    if any(x in rh for x in fam.get('rhythms') or ()) or any(w in who for w in fam.get('people') or ()):
        return 'family'
    if any(x in rh for x in (care.get('pet') or {}).get('rhythms') or ()) or any(
            re.search(r'\b%s\b' % re.escape(n), title) for n in (care.get('pet') or {}).get('names') or ()):
        return 'pet'
    if pr in HOME or any(x in rh for x in (care.get('home') or {}).get('rhythms') or ()):
        return 'home'
    if any(x in rh for x in (care.get('personal') or {}).get('rhythms') or ()):
        return 'personal'
    if rh == (C.get('system_rhythm') or 'be•do'):
        return 'system'
    st = c.get(F['status']) or ''
    st = st.get('name') if isinstance(st, dict) else st
    if pr in flows or st == '◉ done':                       # a flow step is a ◉ be-row
        return 'flow'
    if rh or pr == 'action':
        return 'work'
    return 'flow'


def schedule_of(today, rows, day_page, F, off, hidden, flows=frozenset(), C=None, picks=None):
    """Today as a calendar (31 Oct 2026, her words: I want it to look like how the schedule looks in Google
    calendar, and the whole list of things I said I wanted to do this afternoon — those are my intentions;
    and take into account all the work I've done so far today). What she has done today, each row at its own
    time; every calendar event today; and every step set for a time today, still open, at its time. A step
    holds be•do's guess at its size (at most two hours) unless it carries its own end; a lived row with no
    end holds ten minutes. An event's own row is the event, not twice. Each carries its category (`cat`)."""
    C = C or {}
    to = lambda ts: dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off
    hm = lambda t: t.strftime('%H:%M')
    items, links, own = [], set(), set()
    for e in (day_page or {}).get('events') or []:
        try:
            a = dt.datetime.fromisoformat(e['sort'])
        except (KeyError, ValueError):
            continue
        if a.date() != today or not e.get('when'):
            continue
        b = clock(today, e.get('end')) or a + dt.timedelta(hours=1)
        summ = e.get('summary') or ''
        items.append(dict(k='event', t=e.get('title') or summ, a=hm(a), b=hm(b), drive=e.get('drive'), who=e.get('who'),
                          done=summ.startswith('✅'), link=e.get('link'), cat='event'))
        if e.get('link'):
            links.add(e['link'].split('&')[0])
        if e.get('match'):
            own.add(e['match'])
    for r in rows:
        c = r['cellValuesByFieldId']
        st = c.get(F['status']) or ''
        st = st.get('name') if isinstance(st, dict) else st
        rh = (c.get(F['rhythm']) or '').strip()
        title = (c.get(F['title']) or '').strip()
        ev = (c.get(F['event']) or '') if F.get('event') else ''
        if rh in hidden and not (C.get('system_rhythm') and rh == C['system_rhythm']):
            continue
        if title in own or (ev and ev.split('&')[0] in links):
            continue
        t = re.sub(r'^⚡\s*', '', title)
        end = c.get(F['end'])
        if st in OPEN:                                         # a step still to do, at its time today
            tg = c.get(F['target'])
            if not tg or to(tg).date() != today:
                continue
            if F.get('quickie') and c.get(F['quickie']):
                continue
            a = to(tg)
            # a size on the row wins (31 Oct 2026, her words: a lot of those things aren't going to take an
            # hour; the bike ride with Rosa will probably take 20 minutes): a `size: 20 min` line in its words
            # or the [be•do] block, `guess` on that line when it is be•do's; else be•do's guess off the words
            m = re.search(r'(?im)^.*?\bsize:\s*(\d+)\s*min\b(.*)$', c.get(F['details']) or '')
            mins_ = int(m.group(1)) if m else min(size_guess(t), 120)
            b = a + dt.timedelta(minutes=mins_)
            why = (picks or {}).get(r['id']) or (picks or {}).get(c.get(F['key']) or '')
            items.append(dict(k='step', t=t, a=hm(a), b=hm(b), drive=rh, done=False,
                              sized=not m or 'guess' in m.group(0).lower(),
                              cat=kind_of(c, F, flows, C), pick=why is not None, why=why or None))
            continue
        if st in NOT_LIVED or not c.get(F['when']):            # skipped, dropped, a potential
            continue
        a = to(c[F['when']])
        if a.date() != today or low(c.get(F['practice'])) in SLEEP:
            continue
        real = end and to(end) > a and to(end) - a <= dt.timedelta(hours=6)
        b = to(end) if real else a + dt.timedelta(minutes=10)
        items.append(dict(k='lived', t=t, a=hm(a), b=hm(b), drive=rh, done=True, cat=kind_of(c, F, flows, C)))
    return sorted(items, key=lambda x: (x['a'], x['k'] != 'event'))


def sized(acts):
    """Each step with be•do's guess at its size (sz, minutes), marked a guess (szg)."""
    return [dict(a, sz=size_guess(a.get('t')), szg=True) for a in acts]


def build(D, rows, rhythms_read, L, behind_dir):
    F = L['fields']['stream']
    RF = L['fields']['rhythms']
    off = dt.timedelta(hours=L['utc_offset_hours'])
    local = lambda ts: (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).date()
    W, C = D['whole'], D['card']
    today = dt.date.fromisoformat(W['day'])
    data = dict(day=W['day'], chip=D['chip'], label=D['dateLabel'], word=(D.get('word') or {}).get('word'),
                drives=[{k: d[k] for k in ('n', 'short', 'g', 'c', 'parent', 'dest', 'prog')} | dict(acts=sized(d['acts']))
                        for d in W['drives']],
                rhythms=[{k: r[k] for k in ('n', 'short', 'g', 'c')} | dict(acts=sized(r['acts'])) for r in W['rhythms']],
                order=W['order'], dest=W['dest'],
                done=[dict(t=x['t'], rd=x['rd']) for x in C['steps'] if x['s'] == 'done'],
                secure=(D.get('secure') or {}).get('state'))
    today_page = next((x for x in D.get('days') or [] if x.get('date') == W['day']), None)
    data['holds'] = day_holds(today_page, L) if today_page else None
    data['intentions'] = [x for x in (D.get('intentions') or []) if x]
    data['schedule'] = schedule_of(today, rows, today_page, F, off, set(L.get('hide_drives') or []),
                                   L.get('_flows') or frozenset(), care_settings(L), L.get('_picks'))
    data['goals'] = {c.get(RF['name']): first_sentence(c.get(RF['goal'])) for c in
                     (r['cellValuesByFieldId'] for r in rhythms_read) if c.get(RF['goal'])}
    # body: each morning's readiness, from the readiness practice's row ("readiness 81")
    practice = L.get('readiness_practice', 'morning oura')
    ready = {}
    for r in rows:
        c = r['cellValuesByFieldId']
        m = re.search(r'readiness (\d+)', c.get(F['title']) or '')
        if m and practice in (c.get(F['practice']) or ''):
            ready[local(c.get(F['when']) or r['createdTime'])] = int(m.group(1))
    rhythm_names = {r['n'] for r in W['rhythms']}
    hidden = set(L.get('hide_drives') or [])
    week = []
    for i in range(WEEK - 1, -1, -1):
        m = today - dt.timedelta(days=i)
        y = m - dt.timedelta(days=1)
        w = dict(day=m.isoformat(), label=m.strftime('%a'), yday=y.strftime('%A'), body=ready.get(m), balance=None)
        bp = os.path.join(behind_dir, f'{y.isoformat()}-day-behind.html') if behind_dir else ''
        if bp and os.path.exists(bp) and 'balance' in page_data(bp)[1]:
            w['balance'] = evenness(page_data(bp)[1]['balance']['domains'])
        else:
            dom = wheel_of(y, rows, F, off)
            w['balance'] = evenness(dom) if dom else None
        b = buffer_on(m, rows, F, rhythm_names, hidden, local)
        w['effectiveness'], w['late'] = b['value'], [b['tend'], b['grow']]
        week.append(w)
    t = week[-1]
    keys = ('body', 'balance', 'effectiveness')
    data['baseflow'] = dict(week=week, parts=[dict(name=k, value=t[k]) for k in keys if t[k] is not None],
                            missing=[k for k in keys if t[k] is None])
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day-ahead', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--behind')
    ap.add_argument('--out', required=True)
    ap.add_argument('--pick', action='append', default=[],
                    help='"<row key or record id>::<why>" — be•do\'s three for today, starred on the calendar')
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    h, D = page_data(a.day_ahead)
    dd = os.path.join(os.path.dirname(os.path.abspath(a.local)), 'data')
    rows, seen = [], set()
    for p in sorted(glob.glob(os.path.join(dd, 'w*.json')), reverse=True):   # the live week first
        for r in json.load(open(p, encoding='utf-8'))['records']:
            if r['id'] not in seen:
                seen.add(r['id']); rows.append(r)
    rhythms_read = json.load(open(os.path.join(dd, 'rhythms.json'), encoding='utf-8'))['records']
    L['_picks'] = dict((p.split('::', 1) + [''])[:2] for p in a.pick)
    data = build(D, rows, rhythms_read, L, a.behind)
    root = re.search(r':root\{[^}]*--c-moss[^}]*\}', h).group(0)
    night = re.search(r'html\[data-bedo="night"\]\{[^}]*\}', h).group(0)
    page = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()
    page = (page.replace('/*ROOT*/', root).replace('/*NIGHT*/', night)
            .replace('/*BFCSS*/', open(os.path.join(BF_DIR, 'base_flow.css'), encoding='utf-8').read())
            .replace('/*BFJS*/', open(os.path.join(BF_DIR, 'base_flow.js'), encoding='utf-8').read())
            .replace('/*DATA*/', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
    open(a.out, 'w', encoding='utf-8').write(page)
    bf = data['baseflow']['week'][-1]
    print(json.dumps(dict(out=a.out, body=bf['body'], balance=bf['balance'], buffer=bf['effectiveness']), ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
