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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(1, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'core'))
import bedo_clock  # noqa: E402  the one clock: the offset from time_zone, per instant

HERE = os.path.dirname(os.path.abspath(__file__))
# in the version store the base-flow assets sit three folders up; in the runner's working folder,
# prep copies them beside the engine (assets/base-flow), so either layout builds
BF_DIR = next((d for d in (os.path.join(HERE, '..', '..', '..', 'assets', 'base-flow'),
                           os.path.join(HERE, '..', 'assets', 'base-flow'))
               if os.path.exists(os.path.join(d, 'base_flow.css'))),
              os.path.join(HERE, '..', '..', '..', 'assets', 'base-flow'))
# the pieces this page shares with the my week page (plugins/bedo/assets/flow-parts): the shell, the card,
# the theme button, the wellness glyphs, the colours of the kinds of time, the a-or-p clock. Same two
# layouts as base-flow — the version store, or copied beside the engine by prep.
PARTS_DIR = next((d for d in (os.path.join(HERE, '..', '..', '..', 'assets', 'flow-parts'),
                              os.path.join(HERE, '..', 'assets', 'flow-parts'))
                  if os.path.exists(os.path.join(d, 'parts.py'))),
                 os.path.join(HERE, '..', '..', '..', 'assets', 'flow-parts'))
sys.path.insert(0, os.path.abspath(PARTS_DIR))
import parts   # noqa: E402 — flow-parts/parts.py, found by PARTS_DIR just above
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


def wheel_of(day, rows, F, off, entries=None):
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
        mins = (bedo_clock.parse(end) - bedo_clock.parse(when)).total_seconds() / 60 if end else 0   # lived minutes, not wall
        dom[k] += mins / DIVISOR if 0 < mins <= 12 * 60 else 1.0
        if entries is not None:
            entries.append(dict(k=k, t=re.sub(r'^⚡\s*', '', (c.get(F['title']) or '').strip()),
                                at=to(when).strftime('%H:%M'), rid=r['id']))   # its row, so a kind of time can light it
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


# a target be•do made up is not a deadline (261112_f20, her words 12 Nov 2026: the made up times, that's uncool):
# the row's latest word on its target calls it a placeholder, or puts it in a block of time (the money day)
PLACEHOLDER = re.compile(r'placeholder|money (?:block|day|batch)|batch\b', re.I)


def made_up(details):
    """True when the last line that speaks of the row's target or its block says be•do supplied the time."""
    said = [ln for ln in (details or '').split('\n') if re.search(r'target|block|batch|placeholder', ln, re.I)]
    return bool(said) and bool(PLACEHOLDER.search(said[-1]))


def grew_on(morning, rows, F, rhythm_names, hidden, local, days=7):
    """Growth, forward (261111_f16): the steps closed ✅ on her drives in the seven days before this morning, and
    on how many drives. A count of what moved, never a score."""
    n, drives = 0, set()
    for r in rows:
        c = r['cellValuesByFieldId']
        if (c.get(F['status']) or '') != '✅ done' or '⚡' not in (c.get(F['practice']) or ''):
            continue
        rh = (c.get(F['rhythm']) or '').strip()
        when = c.get(F['end']) or c.get(F['when'])
        if not rh or rh in hidden or rh in rhythm_names or not when:
            continue
        d = local(when)
        if morning - dt.timedelta(days=days) <= d < morning:
            n += 1
            drives.add(rh)
    return dict(steps=n, drives=len(drives))


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
        if F.get('details') and made_up(c.get(F['details'])):
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
except Exception as _e:                             # a copy without the day behind beside it
    # never silent: on the short list below hygiene, reading and some twenty other practices
    # fall through to work or flow, and the page disagrees with the day QA
    print(f'WARNING: day_rings.py could not be loaded ({type(_e).__name__}: {_e}); the page is sorting time '
          'with the short list built into flow.py. Run prep again so the runner copies it.', file=sys.stderr)
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


def quest_link(L, schedule):
    """His quest page, linked on the day it scores (8 Nov 2026, her words: when I am wrapping up the day I want the
    quest linked to it). `quest_url` from these settings, else her facts_local row; nothing without a
    scored ⚔️ row on the day."""
    if not any(x.get('k') == 'lived' and '⚔' in (x.get('t') or '') and re.search(r'\d+ of \d+', x.get('t') or '')
               for x in schedule or []):
        return None
    S = L if L.get('quest_url') else None
    if S is None:
        try:
            import bedo_settings
            S, _ = bedo_settings.fetch('facts_local')
        except Exception:
            S = None
    S = S or {}
    if not S.get('quest_url'):
        return None
    name = S.get('quest_name') or L.get('quest_name')
    return dict(u=S['quest_url'], t=f"⚔️ {name}'s quest" if name else '⚔️ the quest page')


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


def with_drives(C, W, L):
    """The care settings with each drive's parent rhythm beside them, and which rhythms are work (`work_parents`),
    so a row on a work drive is read as work (7 Nov 2026: a Teams update and a work email, written at home with
    the family about, were drawn as family care)."""
    return dict(C, _parent={d['n']: d.get('parent') or '' for d in W.get('drives') or []},
                _work=frozenset(L.get('work_parents') or ()))


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
    # a work drive is work whoever was about: the drive a row serves says what its time was
    parent = (C.get('_parent') or {}).get(rh, '')
    if rh and (rh in (C.get('_work') or ()) or parent in (C.get('_work') or ())):
        return 'work'
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


def theirs(title, C):
    """A row whose title leads with the name of someone in her care (`care.family.people`, 'Kid's sleep', 'Kid
    awake') is that person's own row (J7: whoever is doing it owns the row)."""
    care = (C or {}).get('care') or {}
    who = (care.get('family') or {}).get('people') or care.get('people') or ()
    t = re.sub(r'^[^\w]+', '', title or '').lower()
    return any(t == w.lower() or t.startswith((w.lower() + ' ', w.lower() + "'s ", w.lower() + '’s ')) for w in who)


def schedule_of(today, rows, day_page, F, off, hidden, flows=frozenset(), C=None, picks=None, me=''):
    """Today as a calendar (31 Oct 2026, her words: I want it to look like how the schedule looks in Google
    calendar, and the whole list of things I said I wanted to do this afternoon — those are my intentions;
    and take into account all the work I've done so far today). What she has done today, each row at its own
    time; every calendar event today; and every step set for a time today, still open, at its time. A step
    holds be•do's guess at its size (at most two hours) unless it carries its own end; a lived row with no
    end holds ten minutes. An event's own row is the event, not twice. Each carries its category (`cat`)."""
    C = C or {}
    to = lambda ts: dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off
    hm = lambda t: t.strftime('%H:%M')
    items, links, own, owner = [], set(), set(), {}
    for e in (day_page or {}).get('events') or []:
        try:
            a = dt.datetime.fromisoformat(e['sort'])
        except (KeyError, ValueError):
            continue
        if not e.get('when'):
            continue
        b = clock(today, e.get('end')) or a + dt.timedelta(hours=1)
        if a.date() != today:
            # a stay that began before today and ends today is part of the day's background (12 Nov 2026, her words:
            # where's the fact that he's at his grandparents', please?): it starts the day at midnight
            if not (a.date() < today and b.date() == today):
                continue
            a = dt.datetime.combine(today, dt.time(0))
        # put on the calendar the same day it happened: last-minute (6 Nov 2026, her words:
        # it was definitely an event that should have been on the calendar; it was just a last-minute thing)
        made = CREATED.get(re.search(r'[?&]eid=([^&#]+)', e.get('link') or '') and re.search(r'[?&]eid=([^&#]+)', e.get('link')).group(1))
        lastmin = bool(made) and (dt.datetime.fromisoformat(made.replace('Z', '+00:00')) + off).date() == today
        summ = e.get('summary') or ''
        items.append(dict(k='event', t=e.get('title') or summ, a=hm(a), b=hm(b), drive=e.get('drive'), who=e.get('who'),
                          done=summ.startswith(('✅', '✔')), link=e.get('link'), cat='event',
                          summary=summ, where=e.get('where') or None, color=e.get('color'), lastmin=lastmin,
                          # an event out in town with other people is no solo work block (6 Nov 2026, her words: the
                          # Expo center event needs to be highlighted better): only her office or a call stays light
                          meet=e.get('meet') or bool((e.get('where') or '').strip()
                                                     and not re.search(r'(?i)office|teams|zoom|virtual', e.get('where') or ''))))
        if e.get('link'):
            links.add(e['link'].split('&')[0])
        if e.get('match'):
            own.add(e['match']); owner[e['match']] = items[-1]
    for r in rows:
        c = r['cellValuesByFieldId']
        st = c.get(F['status']) or ''
        st = st.get('name') if isinstance(st, dict) else st
        rh = (c.get(F['rhythm']) or '').strip()
        title = (c.get(F['title']) or '').strip()
        ev = (c.get(F['event']) or '') if F.get('event') else ''
        if rh in hidden and not (C.get('system_rhythm') and rh == C['system_rhythm']):
            continue
        # a row linked to another occurrence of a series is that day's, not today's (9 Nov 2026: last Monday's
        # ✅ gymnastics row shared today's title and drew today's class done before it happened)
        elsewhere = bool(ev) and ev.split('&')[0] not in links
        if (title in own and not elsewhere) or (ev and not elsewhere):
            # the event's own row is the event: its links ride on the event's card (4 Nov 2026, her words: I want
            # to see the link to the notes, so I can click on it, like when I finish an action with a deliverable)
            mine = owner.get(title) or next((x for x in items if x['k'] == 'event' and ev and x.get('link')
                                             and x['link'].split('&')[0] == ev.split('&')[0]), None)
            if mine is not None:
                mine.setdefault('links', []).extend(links_of(c, F))
                mine['el'] = mine.get('el') or wellness_of(c, F)   # once it has happened, the event wears its row's element
                mine['cat'] = kind_of(c, F, flows, C)   # and its time chunk
                mine['el2'] = mine.get('el2') or second_element(c, F)
                # what happened wins over what was scheduled (6 Nov 2026, her words: why is there a gap between
                # the game and the drive home — we hung out at the end of the game): the event's own row, done,
                # stretches the card to the row's real start and end
                if st not in OPEN and c.get(F['when']) and c.get(F['end']):
                    ra, rb = to(c[F['when']]), to(c[F['end']])
                    if ra.date() == today and rb > ra and rb - ra <= dt.timedelta(hours=6):
                        mine['a'] = hm(ra); mine['b'] = hm(rb)
                mine.setdefault('rids', []).append(r['id'])   # its photos ride on the event's card too
                if st not in OPEN:
                    mine['done'] = True   # its own row closed: it happened, even while her calendar still shows ⬜ (7 Nov 2026)
                if st not in OPEN and _norm(title) != _norm(mine.get('t')):
                    mine.setdefault('covers', []).append(re.sub(r'^⚡\s*', '', title))
            continue
        t = re.sub(r'^⚡\s*', '', title)
        end = c.get(F['end'])
        # a session entry still ▶️ in motion is time she spent today: drawn as lived (7 Nov 2026: a Nectar chat at 6:15 PM
        # was missing from the page because its row stays open for the step after it)
        if st == '▶️ in motion' and c.get(F['when']) and c.get(F['end']) and to(c[F['when']]).date() == today \
                and 'written by session-entry' in (c.get(F['details']) or ''):
            st = '● log'
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
            # its own end wins, as the docstring says (12 Nov 2026: leaving the office at 3:45 drew an hour long)
            if end and a < to(end) and to(end).date() == today:
                b = to(end)
            why = (picks or {}).get(r['id']) or (picks or {}).get(c.get(F['key']) or '')
            nx = [ln.split(':', 1)[1].strip() for ln in (c.get(F['details']) or '').split('\n')
                  if re.match(r'(?i)^\s*next( step)?:', ln)]
            # worked on today and still in motion is not the same as didn't happen (7 Nov 2026, her words: several things
            # on here should have been reconciled during the QA before this got printed)
            worked = st == '▶️ in motion' and bool(c.get(F['when'])) and to(c[F['when']]).date() == today
            items.append(dict(k='step', t=t, a=hm(a), b=hm(b), drive=rh, done=False, nx=nx[-1] if nx else None, worked=worked,
                              key=c.get(F['key']) or None, rid=r['id'],
                              sized=not m or 'guess' in m.group(0).lower(),
                              cat=kind_of(c, F, flows, C), pick=why is not None, why=why or None))
            continue
        if st in NOT_LIVED or not c.get(F['when']):            # skipped, dropped, a potential
            continue
        a = to(c[F['when']])
        if low(c.get(F['practice'])) in SLEEP:
            # his sleep is his (7 Nov 2026, her words: there's no way I've already gotten 8 hours of sleep today — the
            # page had drawn her son's night, 11:52 PM to 8:45 AM, as hers): a sleep row titled for someone in her care
            # is that person's own row, never her time
            if theirs(title, C):
                continue
            # sleep is on the timeline too, clipped to the day: the night before at the start, tonight at the end
            # (6 Nov 2026, her words: I want to know when was I sleeping; that should go on my timeline)
            if c.get(F['end']):
                z = to(c[F['end']])
                d0 = a.replace(year=today.year, month=today.month, day=today.day, hour=0, minute=0, second=0, microsecond=0)
                d1 = d0 + dt.timedelta(hours=23, minutes=59)
                sa, sb = max(a, d0), min(z, d1)
                if sb > sa and sb - sa >= dt.timedelta(minutes=20):
                    t12 = lambda d: f"{d.hour % 12 or 12}:{d.minute:02d} {'AM' if d.hour < 12 else 'PM'}"
                    items.append(dict(k='lived', t=f'😴 sleep {t12(sa)}–{t12(sb)}', a=hm(sa), b=hm(sb), drive='', done=True, cat='sleep',
                                      rid=None, links=None, act=False, pt=False, felt=False, el='body', el2=None, mom=False))
            continue
        if a.date() != today:
            continue
        # a span up to most of a waking day is real (7 Nov 2026: her work from 3:42 to about 10 PM was drawn as ten minutes)
        # (a session's `stretches:` line still wins over its envelope)
        long_ok = not re.search(r'(?im)^stretches:', c.get(F['details']) or '')
        real = end and to(end) > a and to(end) - a <= dt.timedelta(hours=14 if long_ok else 6)
        b = to(end) if real else a + dt.timedelta(minutes=10)
        # a session entry with several stretches keeps its first start and no end; its `stretches:` line holds
        # her real time, so draw each stretch (6 Nov 2026, her words: a lot of gaps in the afternoon)
        sm = None if real else re.search(r'(?im)^stretches:\s*(.+)$', c.get(F['details']) or '')
        spans = re.findall(r'(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})', sm.group(1)) if sm else []
        if len(spans) > 1:
            base = a.replace(hour=0, minute=0, second=0, microsecond=0)
            def at(h, m, after):
                ms = [base + dt.timedelta(minutes=(int(h) % 12) * 60 + int(m) + k) for k in (0, 720)]
                ok = [x for x in ms if x >= after - dt.timedelta(minutes=5)]
                return min(ok) if ok else ms[-1]
            # the line reads from the row's own clock when its first stretch is that clock (session-entry's rule); a line
            # whose first stretch is not (8 Nov 2026: a my day row timed 4:16 PM whose stretches start at 5:11 AM drew its
            # morning in the evening) reads from midnight, in order through the day
            h0, m0 = int(spans[0][0]) % 12, int(spans[0][1])
            prev = a if abs((a.hour % 12) * 60 + a.minute - (h0 * 60 + m0)) <= 5 else base
            first = at(*spans[0][:2], prev)
            for h1, m1, h2, m2 in spans:
                sa = at(h1, m1, prev); sb = at(h2, m2, sa)
                if sb <= sa or sb - sa > dt.timedelta(hours=6):
                    continue
                # no tick while the session's notes still list open work (7 Nov 2026, her words: I didn't finish that page)
                # a card, never the ground band an hour-long action becomes: a session's stretch sits among the
                # other work it ran beside, so it reads as a card with its tick in the title
                items.append(dict(**opens_to(c, F), k='lived', t=('✅ ' if st == '✅ done' and not re.search(r'(?im)^still open', c.get(F['details']) or '') else '') + t, a=hm(sa), b=hm(sb), drive=rh, done=True,
                                  cat='stretch', sk=kind_of(c, F, flows, C),   # its kind of time: a be•do chat is be•do, not work (7 Nov 2026)
                                  rid=r['id'] if sa == first else None, links=links_of(c, F) or None,
                                  act=False, pt=False,
                                  felt=bool(F.get('emotion') and c.get(F['emotion'])), el=wellness_of(c, F), el2=second_element(c, F), hot=bool(re.search(r'🟡|🔴|high energy', str(c.get(F['emotion']) or '') if F.get('emotion') else '')), mom=low(c.get(F['practice'])) in GOLD))
                prev = sb
            continue
        items.append(dict(**opens_to(c, F), phase=(C.get('_phase') or {}).get(low(c.get(F['practice']))), k='lived', t=t, a=hm(a), b=hm(b), drive=rh, done=True, cat=kind_of(c, F, flows, C), rid=r['id'],
                          links=links_of(c, F) or None,
                          act=st == '✅ done', pt=not real,
                          # a feeling or a keeper photo marks what mattered (2 Nov 2026): it stays when the hour folds
                          felt=bool(F.get('emotion') and c.get(F['emotion'])), el=wellness_of(c, F), el2=second_element(c, F), hot=bool(re.search(r'🟡|🔴|high energy', str(c.get(F['emotion']) or '') if F.get('emotion') else '')), mom=low(c.get(F['practice'])) in GOLD,
                          keeper=is_keeper(c, F, me),
                          # a time be•do placed from context is drawn as an estimate (8 Nov 2026, the gap-filling pass)
                          est='ESTIMATED FROM CONTEXT' in (c.get(F['details']) or '')))   # an action she finished, drawn with its green check (2 Nov 2026)
    return star_the_highlight(fold_into_events(fold_done_plans(fill_between(flow_cards(sorted(items, key=lambda x: (x['a'], x['k'] != 'event')))))))


def flow_cards(items, gap=240):
    """Each flow spans its first step to its close (7 Nov 2026, her words: my dawn flow and dusk flow are completely missing),
    drawn as a dotted outline in the background around its steps, as the river drew it; its steps keep their own cards.
    It takes no minutes in how the time went: its steps already do."""
    mm = lambda t: int(t[:2]) * 60 + int(t[3:5])
    out = list(items)
    for ph in sorted({x.get('phase') for x in items if x.get('phase')}, key=lambda p: 'dusk' in p):
        steps = sorted([x for x in items if x.get('phase') == ph and x.get('k') == 'lived'], key=lambda x: mm(x['a']))
        # a flow is its steps close together, never one stray step hours away (7 Nov 2026, her question: what's happening
        # with the dawn flow on the stream? — the dusk practice of supplements taken with breakfast at 9:37 AM stretched
        # a dusk outline to 5 PM, over the whole day): steps more than four hours apart are two runs, and the run with
        # the most steps is the flow (the dawn's first, the dusk's last, on a tie)
        runs = []
        for x in steps:
            if runs and mm(x['a']) - max(mm(y['b']) for y in runs[-1]) <= gap:
                runs[-1].append(x)
            else:
                runs.append([x])
        steps = max(runs[::-1] if 'dusk' in ph else runs, key=len) if runs else []
        if len(steps) < 2:
            continue
        a, b = min(mm(x['a']) for x in steps), max(mm(x['b']) for x in steps)
        name = re.sub(r'^\W*', '', ph)
        out.append(dict(k='lived', t=f"{ph.split()[0]} {name} flow · {len(steps)} steps", a=f'{a // 60:02d}:{a % 60:02d}',
                        b=f'{b // 60:02d}:{b % 60:02d}', drive='', done=True, cat='flow', nopie=True, flowcard=True,
                        rid=None, links=None, act=False, pt=False, el=None, el2=None,
                        members=[dict(t=x['t'], s=mm(x['a']), e=mm(x['b']), act=x.get('act')) for x in steps]))
    return sorted(out, key=lambda x: (x['a'], x['k'] != 'event'))


def fold_done_plans(items, before=15):
    """A plan closed by what happened is drawn once (7 Nov 2026, her words: the pizza place plan that didn't happen didn't
    get replaced by the plan that did). A finished action with no span of its own, at or just before a lived row that
    shares two of its words, is that row: it folds in, and the row is marked done and carries its links."""
    mm = lambda t: int(t[:2]) * 60 + int(t[3:5])
    stop = {'with', 'from', 'that', 'this', 'when', 'then', 'into', 'for', 'the', 'and', 'about'}
    words = lambda t: {w for w in re.findall(r"[a-z][a-z']{3,}", (t or '').lower()) if w not in stop}
    gone = set()
    for x in items:
        if not (x.get('k') == 'lived' and x.get('act') and x.get('pt')):
            continue
        xa, xw = mm(x['a']), words(x['t'])
        host = next((o for o in items if o is not x and id(o) not in gone and o.get('k') == 'lived' and not o.get('pt')
                     and not o.get('column') and o.get('cat') not in ('stretch', 'moment', 'sleep')
                     and mm(o['a']) - before <= xa <= mm(o['b']) and len(xw & words(o['t'])) >= 2), None)
        if host is None:
            continue
        gone.add(id(x))
        host['done'] = True
        host['links'] = (host.get('links') or []) + (x.get('links') or [])
        host.setdefault('closes', []).append(x['t'])
    return [x for x in items if id(x) not in gone]


def opens_to(c, F):
    """What a lived card opens to (7 Nov 2026, her words: click on an event and get all of the relevant info in a really
    clear visual way): her words (above the divider), who was there, and the feeling she named."""
    d = c.get(F['details']) or ''
    her = re.split(r'\n?(?:———|---|——)\n?', d, maxsplit=1)[0].strip() if not d.lstrip().startswith(('———', '---')) else ''
    her = re.sub(r'(?m)^overlap — .*$', '', her).strip()
    emo = c.get(F['emotion']) if F.get('emotion') else None
    emo = ', '.join(emo) if isinstance(emo, list) else (emo or '')
    return dict(her=her[:700] or None, who=(c.get(F['person']) or '') if F.get('person') else '', felt_word=emo or None,
                dev=screen_of(c, F))


def screen_of(c, F):
    """The screen a row's time was on, from its device field (8 Nov 2026, her words: if I've got the screen open, I'm
    looking at it, I'm interacting with it, I really want that to show up). None for no device or 🚫 none, and for a
    journal, which is talking, not a screen."""
    if not F.get('device'):
        return None
    d = c.get(F['device']) or ''
    d = (d.get('name') if isinstance(d, dict) else d) or ''
    name = re.sub(r'^[^\w]+', '', d).strip().lower()
    if not name or name == 'none' or 'journal' in low(c.get(F['practice'])):
        return None
    return name


def screen_measured(rows, F, off, today):
    """The day's measured phone time, from her 📱 screen time row (her Digital Wellbeing screenshot, written to the day
    it covers): minutes, or None."""
    for r in rows:
        c = r['cellValuesByFieldId']
        if 'screen time' not in low(c.get(F['practice'])) or not c.get(F['when']):
            continue
        if (dt.datetime.fromisoformat(c[F['when']].replace('Z', '+00:00')) + off).date() != today:
            continue
        m = re.search(r'(\d+)\s*h\s*(\d+)?', c.get(F['title']) or '')
        if m:
            return int(m.group(1)) * 60 + int(m.group(2) or 0)
    return None


def fill_between(items, long_min=180):
    """A long stretch of one thing she did whenever nothing else was going on is one running column beside the rest
    (7 Nov 2026, her words: I was working on the nlgca budget justification from the time we got home until I sent the
    email … whenever I wasn't eating or doing something else obvious; it would make sense to have that as a whole
    running effort during that time, a column instead of a bunch of different entries). Drawn as a ground band it read
    as empty time. A 📝 log row (be•do's own catch-all for time she describes in her words) runs from half that length.
    A finished action of that length is one too (11 Nov 2026, her words: the whole evening work block is just missing …
    I worked all damn evening and it's not showing up): drawn as a ground band, her 4:15–10:08 and 5:15–10:22 work
    read as a pale empty box with its name only in the list above the timeline."""
    mm = lambda t: int(t[:2]) * 60 + int(t[3:5])
    for x in items:
        if (x.get('k') == 'lived' and x.get('cat') not in ('sleep', 'stretch', 'moment')
                and not x.get('pt') and mm(x['b']) - mm(x['a']) >= (long_min // 2 if (x.get('t') or '').startswith('📝') else long_min)):
            x['column'] = True
    return items


TELLING = re.compile(r"\b(tell|tells|telling|told|talk|talks|talking|talked|said|saying|showed me|showing me)\b", re.I)
MEALTIME = {'breakfast': 8 * 60, 'lunch': 12 * 60, 'dinner': 18 * 60 + 30, 'supper': 18 * 60 + 30}


DAYTIME_END = '17:00'   # a highlight logged before this sits where it happened; one told after it is matched to its card


def star_the_highlight(items):
    """A highlight is drawn when it happened, not when she named it (6 Nov 2026, her words: mark the actual event that
    was the highlight, not when I chose the highlight; 11 Nov 2026: the highlights should get tagged like when they
    actually happened in the day, not necessarily when I specified what they were at the end of the day).

    A highlight told at night (⭐ hers, 🌟 anyone's) is matched to the earlier card it names, by its rarest words: a
    name that is on half the day's cards (her son) says little, the place he went (his school) says where. Then:
      · her ⭐ highlight stars that card and carries its words (`hl`), and is not drawn again at the hour she said it;
        one that is about being told (telling me about his day at school) stars the first time she was with
        that person after it, not the event itself
      · anyone else's 🌟 highlight moves to that moment (a meal it names, inside the event: pizza for lunch at
        school lands at noon), keeping the hour it was told as `told`
    No match strong enough, and the row stays where it was. A highlight logged before DAYTIME_END already sits where
    it happened (its time read from her photos): it keeps its own card (14 Nov 2026)."""
    mm = lambda s: int(s[:2]) * 60 + int(s[3:5])
    hm = lambda m: f'{m // 60 % 24:02d}:{m % 60:02d}'
    stop = {'the', 'and', 'with', 'for', 'was', 'that', 'there', 'him', 'her', 'his', 'hers', 'highlight', 'game',
            'everyone', 'about', 'day', 'today', 'tonight', 'from', 'what', 'when', 'then', 'they', 'them', 'had', 'got',
            'one', 'our', 'out', 'really', 'very', 'pretty', 'happy'}
    words = lambda t: {w[:-2] if w.endswith("'s") else w for w in re.findall(r"[a-z][a-z']{2,}", (t or '').lower())} - stop
    told = lambda o: o.get('k') == 'lived' and re.match(r'^\W*(⭐|🌟)', o.get('t') or '')
    text = lambda o: (o.get('summary') or '') + ' ' + (o.get('t') or '') + ' ' + ' '.join(o.get('covers') or [])
    pool = [o for o in items if o.get('k') in ('event', 'lived') and not told(o) and not o.get('flowcard')
            and o.get('cat') not in ('sleep', 'flow', 'system')]
    df = {}
    for o in pool:
        for w in words(text(o)):
            df[w] = df.get(w, 0) + 1
    out = []
    for x in items:
        if not told(x):
            out.append(x)
            continue
        if x['a'] < DAYTIME_END:
            # placed during the day (by its photo, or told then): it keeps its own card at its own time (14 Nov 2026, her
            # words: these need to be integrated into the stream with the correct times and pictures)
            out.append(x)
            continue
        hw = words(re.sub(r'^\W*', '', x['t']))
        weigh = lambda o: sum(1 / df[w] for w in hw & words(text(o)) if df.get(w))
        cands = [(weigh(o), o.get('k') == 'event', o) for o in pool if o['a'] < x['a']]
        cands = [c for c in cands if c[0] >= 0.34]          # at least one word on no more than three of the day's cards
        if not cands:
            out.append(x)
            continue
        best = max(cands, key=lambda c: (c[0], c[1]))[2]
        mine = bool(re.match(r'^\W*⭐', x['t']))
        if mine and TELLING.search(x['t']):
            # the person who told her: a name in the highlight that the event itself does not carry
            ppl = {w.lower() for w in re.findall(r"\b([A-Z][a-z]+)", re.sub(r'^\W*', '', x['t']))} - words(text(best))
            ppl = {p[:-2] if p.endswith("'s") else p for p in ppl} - stop
            after = [o for o in pool if mm(best['b']) <= mm(o['a']) and o['a'] < x['a'] and o.get('cat') == 'family'
                     and ppl & (words(text(o)) | words(o.get('who') or ''))]
            best = min(after, key=lambda o: o['a']) if after else best
        if mine:
            best['star'] = True
            best['hl'] = x['t']
            continue
        at = mm(best['a'])
        meal = next((MEALTIME[w] for w in hw if w in MEALTIME), None)
        if meal is not None and best.get('b') and mm(best['a']) <= meal < mm(best['b']):
            at = meal
        out.append(dict(x, told=x['a'], a=hm(at), b=hm(at + 10)))
    return sorted(out, key=lambda x: (x['a'], x['k'] != 'event'))


def did_of(rows, F, off, today):
    """What she did that day, for a finished day's top list: each ⚡ action closed ✅ that day and each ⭐ highlight, in
    time order, as the three's items (title, glyph, drive, why from her words)."""
    out = []
    for r in rows:
        c = r['cellValuesByFieldId']
        st = c.get(F['status']) or ''
        st = st.get('name') if isinstance(st, dict) else st
        pr = (c.get(F['practice']) or '').strip()
        when = c.get(F['when'])
        if not when or (dt.datetime.fromisoformat(when.replace('Z', '+00:00')) + off).date() != today:
            continue
        if not ((st == '✅ done' and pr.startswith('⚡')) or pr.startswith('⭐')):
            continue
        t = re.sub(r'^\s*(⚡|⭐)\s*', '', c.get(F['title']) or '')
        her = (c.get(F['details']) or '').split('———')[0].strip().split('\n')[0]
        rh = c.get(F['rhythm']) if F.get('rhythm') else ''
        out.append(dict(t=t, g='⭐' if pr.startswith('⭐') else '', drive=rh or '', st='✅', why=her[:160], at=when))
    return sorted(out, key=lambda x: x['at'])


def night_of(rows, F, off, today, C=None):
    """Her night that ended this morning, as her ring measured it: minutes asleep, read from the 😴 sleep row's own words
    ("7 h 26 asleep"), and the night's name (Thu night). The time-went line shows this, never the clock-day sum of two
    nights in bed (14 Nov 2026, her words: there's no way I slept 9 hours and 55 minutes — the line had added Thursday
    night after midnight to Friday night before it). None when no sleep row says how long she slept."""
    best = None
    for r in rows:
        c = r['cellValuesByFieldId']
        if low(c.get(F['practice'])) not in ('sleep',) or not c.get(F['end']) or theirs(c.get(F['title']), C):
            continue
        z = dt.datetime.fromisoformat(c[F['end']].replace('Z', '+00:00')) + off
        a = dt.datetime.fromisoformat(c[F['when']].replace('Z', '+00:00')) + off
        if z.date() != today or z.hour >= 14:
            continue
        m = re.search(r'(\d+)\s*h\s*(\d+)\s*asleep', c.get(F['details']) or '')
        if not m:
            continue
        mins = int(m.group(1)) * 60 + int(m.group(2))
        if best is None or mins > best['asleep']:
            best = dict(asleep=mins, label=f"{a.strftime('%a')} night", inbed=int((z - a).total_seconds() // 60))
    return best


def links_of(c, F):
    """The row's deliverable as links: every url in the field, labelled by what it is."""
    out = []
    for u in re.findall(r'https?://[^\s)\]>"]+', (c.get(F['deliverable']) or '') if F.get('deliverable') else ''):
        kind = ('notes' if re.search(r'loop|onenote|docs\.google|sharepoint|1drv|onedrive', u) else
                'the page' if 'claude.ai' in u else 'deliverable')
        out.append(dict(l=kind, u=u))
    return out


def _created_map():
    import base64
    out = {}
    for f in glob.glob(os.path.join(os.environ.get('BEDO_CAL_DIR') or 'cal', '*.json')):
        try:
            d = json.load(open(f, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for e in (d.get('events') or []) if isinstance(d, dict) else []:
            if e.get('created') and e.get('htmlLink'):
                m = re.search(r'[?&]eid=([^&#]+)', e['htmlLink'])
                if m:
                    out[m.group(1)] = e['created']
    return out


CREATED = _created_map()


def wellness_of(c, F):
    """The row's wellness element, one word (heart, mind, body, spirit, water, air, earth, fire), or None."""
    g = c.get(F['wellness']) if F.get('wellness') else None
    g = g.get('name') if isinstance(g, dict) else g
    m = re.search(r'(heart|mind|body|spirit|water|air|earth|fire)', (g or '').lower())
    return m.group(1) if m else None


def second_element(c, F):
    """A second element (6 Nov 2026, her pick: a main element and a second, drawn as a split): for now a
    `second element: 🌊 water` line in the row's words or [be•do] block, until the stream has a field for it."""
    m = re.search(r'(?im)^\W*second element:\s*\W*(heart|mind|body|spirit|water|air|earth|fire)\b', c.get(F['details']) or '')
    return m.group(1).lower() if m else None


GOLD = {'highlight', 'glimmer', 'milestone'}   # gold marks what mattered, nothing else (6 Nov 2026)


class _Gold(set):
    # anyone's highlight practice (a family member's highlight, say) is gold too
    def __contains__(self, x):
        return super().__contains__(x) or (isinstance(x, str) and x.endswith('highlight'))


GOLD = _Gold(GOLD)


def _norm(t):
    return re.sub(r'[^a-z0-9]+', '', (t or '').lower())


def fold_into_events(items, start_min=10, end_min=5):
    """An event is drawn once (4 Nov 2026, her words: my class is on here twice … it only needs to show up as
    one line, and then it can indicate that it covered my hip exercises practice; and for a meeting: I only want
    to see the calendar event). A lived row is folded into the event it belongs to — its own title, or a row that starts
    within `start_min` of the event and ends with it — and the event's card names what it covered and carries the
    row's links. A moment (a glimmer, a highlight) keeps its own card."""
    mm = lambda s: int(s[:2]) * 60 + int(s[3:5])
    evs = [x for x in items if x['k'] == 'event' and x.get('a') and x.get('b')]
    gone = set()
    for e in evs:
        ea, eb, en = mm(e['a']), mm(e['b']), _norm(e.get('t'))
        for x in items:
            if x['k'] != 'lived' or id(x) in gone or x.get('cat') == 'moment':
                continue
            xa, xb = mm(x['a']), mm(x['b'])
            same = bool(en) and _norm(x['t']) == en and xa < eb and ea < xb
            inside = e.get('who') in (None, 'you') and ea <= xa <= ea + start_min and xb <= eb + end_min
            # a row inside two events goes to the one that starts nearest it (6 Nov 2026, her words: the Expo center
            # event needs to be highlighted better — a free ticket-email event at 5 had swallowed the open house at 5:15)
            if inside and not same and any(o is not e and o.get('who') in (None, 'you') and xa - mm(o['b']) < 0
                                           and abs(xa - mm(o['a'])) < abs(xa - ea) and mm(o['a']) <= xa <= mm(o['a']) + start_min
                                           and xb <= mm(o['b']) + end_min for o in evs):
                continue
            if same or inside:
                gone.add(id(x))
                e.setdefault('rids', []).append(x.get('rid'))
                # a finished action closed onto the event (a booking thread, the event's own ⬜) is the event; only a
                # practice done inside it is named as covered (4 Nov 2026: the massage listed its booking row)
                if not same and not x.get('act'):
                    e.setdefault('covers', []).append(x['t'])
                e.setdefault('links', []).extend(x.get('links') or [])
                e['done'] = True
    return [x for x in items if id(x) not in gone]


def photo_row(c, F):
    """A stream row's photo cells under the names bedo_photos reads, as the day behind reads them (look_behind.py):
    `photo` the kind (keeper or info, a select), `photo_checked` the old checkbox, `photo_links` its files. A select
    may arrive as {id, name}; it is read by its name."""
    g = lambda k: (c.get(F[k]) if F.get(k) else None)
    k = g('photo')
    k = k.get('name') if isinstance(k, dict) else k
    pe = g('person')
    pr = g('practice')
    pr = pr.get('name') if isinstance(pr, dict) else pr
    return dict(photo=k or None, photo_checked=bool(g('photo_checked')), photo_links=g('photo_links') or '',
                details=c.get(F['details']) or '' if F.get('details') else '', practice=pr or '',
                title=c.get(F['title']) or '' if F.get('title') else '',
                person=', '.join(pe) if isinstance(pe, list) else (pe or ''))


def is_keeper(c, F, me=''):
    """A keeper the way the day behind decides it (11 Nov 2026: Tuesday's photo rows carried only the old checkbox,
    and the card asked whether the word keeper was in it, so none reached the page): the kind she or the chat set
    wins; a row with only the checkbox, or *from her photo* in its words, is sorted by rule (bedo_photos.kind)."""
    import bedo_photos
    return bedo_photos.kind(photo_row(c, F), me) == bedo_photos.KEEPER


def photos_onto(items, today, rows, F, off, folder, me=''):
    """Her keeper photos on the cards they belong to (5 Nov 2026, her words: yes please — a small picture on the
    card at its time, tap to open it). The day's photos come from the week's Drive folder (day_photos.py, the same
    read the day behind uses); each is placed on its row the way the day behind places it (bedo_photos.place: the
    row whose photo links name it, else the row at that minute), and only a photo on a keeper row is drawn. A photo
    on an info row, or with no row, stays off the page."""
    import base64
    import bedo_photos
    if not folder or not os.path.isdir(folder):
        return 0
    idx_path = os.path.join(folder, 'index.json')
    ids = json.load(open(idx_path, encoding='utf-8')) if os.path.exists(idx_path) else {}
    pics = []
    for n in sorted(os.listdir(folder)):
        t = bedo_photos.taken(n, off)
        if t and t.date() == today:
            pics.append((t, ids.get(n), 'data:image/jpeg;base64,' + base64.b64encode(open(os.path.join(folder, n), 'rb').read()).decode()))
    to = lambda ts: (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).replace(tzinfo=None)
    g = lambda c, k: (c.get(F[k]) if F.get(k) else None)
    lived = []
    for r in rows:
        c = r['cellValuesByFieldId']
        st = c.get(F['status']) or ''
        st = st.get('name') if isinstance(st, dict) else st
        if st in NOT_LIVED or st in OPEN or not c.get(F['when']):
            continue
        a = to(c[F['when']])
        if a.date() != today:
            continue
        b = to(c[F['end']]) if c.get(F['end']) else a + dt.timedelta(minutes=10)
        lived.append(dict(photo_row(c, F), id=r['id'], _a=a, _b=b, felt=bool(g(c, 'emotion'))))
    # a photo prefers the row read from a photo, as the day behind places it (week_look_behind.py; 11 Nov 2026:
    # Tuesday's 8:30 photo of him asleep went to the row beside it, logged the same minute)
    placed, _ = bedo_photos.place(lived, pics, me, prefer=lambda r, t: (not bedo_photos.has_photo(r), abs((r['_a'] - t).total_seconds())))
    # selective, as the day behind is (2 Nov 2026, her words: less photos is good, like no more than six)
    # a row that names its photos holds only those (5 Nov 2026, her words: I really don't want to see a picture of
    # the TV on the wall — it was placed on the show's row by its time, though the row linked another)
    placed = [p for p in placed if p['row'] and (not bedo_photos.linked(p['row']) or p['file'] in bedo_photos.linked(p['row']))]
    # one photo a card, as the day behind keeps it (never two of one moment), so six reach six moments
    seen, one = set(), []
    for p in sorted([p for p in placed if p['keeper'] and p['row']], key=lambda p: (not p.get('linked'), p['t'])):
        k = p['row']['id']
        if k not in seen or (p['row'].get('felt') and not p.get('file') and sum(x['row']['id'] == k for x in one) < 2):
            seen.add(k); one.append(p)
    # a moment she named a feeling for ranks with a moment with people (6 Nov 2026: the open house was very
    # important, meaningful, and its one photo was losing its place to a photo someone sent her)
    for p in one:
        if p['row'].get('felt') and not [x for x in (p['row'].get('person') or '').split(',') if x.strip() and x.strip() != me]:
            p['row'] = dict(p['row'], person=(p['row'].get('person') or '') + ', (felt)')
    placed, _ = bedo_photos.select(sorted(one, key=lambda p: p['t']), me, n=int(os.environ.get('BEDO_DAY_PHOTOS') or 0) or None)
    card = {}
    for x in items:
        for rid in [x.get('rid')] + (x.get('rids') or []):
            if rid:
                card.setdefault(rid, x)
    n = 0
    for p in placed:
        x = card.get(p['row']['id']) if p['keeper'] and p['row'] else None
        if x is not None:
            x.setdefault('photos', []).append(dict(src=p['src'], url=bedo_photos.link(p['file']) if p['file'] else None,
                                                   at=p['t'].strftime('%H:%M')))
            n += 1
    return n


def heart_onto(items, path, off, calm_max=80, C=None):
    """Heart rate decides relaxing versus energizing (8 Nov 2026, her words: the heart rate thing is actually really
    helpful; I think that's how we decide what's relaxing versus energizing — the heart-rate amendment of 8 Nov). For each
    stretch of play she lived (recreation, a session whose kind is recreation), the median of her Oura heart rate over
    its minutes: at or under `calm_max` (her `hr_calm_max`, default 80 bpm) it is relaxation, over it recreation and
    adventure. Its `hr` rides on the card; without three samples in its span, its feeling and practice decide as
    before. Travel stays adventure whatever the heart does (the 7 Nov play amendment)."""
    if not path or not os.path.exists(path):
        return 0
    pts = []
    for x in json.load(open(path, encoding='utf-8')):
        try:
            t = (dt.datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')) + off).replace(tzinfo=None)
        except (KeyError, ValueError):
            continue
        pts.append((t.hour * 60 + t.minute, x['bpm']))
    mm = lambda h: int(h[:2]) * 60 + int(h[3:5])
    n = 0
    for x in items:
        kind = x.get('sk') if x.get('cat') == 'stretch' else x.get('cat')
        if x.get('k') not in ('lived', 'event') or kind != 'recreation' or x.get('flowcard'):
            continue
        if theirs(x.get('t'), C):                          # her son's own play is his: her heart doesn't judge it
            continue
        a, b = mm(x['a']), mm(x['b'])
        bp = sorted(v for m, v in pts if a <= m < b)
        if b - a < 10 or len(bp) < 3:
            continue
        x['hr'] = bp[len(bp) // 2]
        x['hot'] = x['hr'] > calm_max
        n += 1
    return n


SESSION_MIN = 15   # each item in a session: a plain default she can change, said so on the card


def session_arg(s):
    """'💰 financial session::16:00-17:00::Money|Taxes' → its name, window and drives."""
    name, win, drives = (s.split('::') + ['', ''])[:3]
    a, _, b = win.partition('-')
    return dict(name=name.strip(), a=a.strip(), b=b.strip(), drives={d.strip() for d in drives.split('|') if d.strip()})


def sessions_of(items, sessions, tops=None):
    """Small open steps of one kind, batched into one named session at a time she has (4 Nov 2026, her words:
    the problem where it stacks up a bunch of tasks at the end of the day doesn't work for me at all … I need to
    see those things batched, and it needs to say something like 'financial session' … put the session on the
    timeline, and when I tap on it, show me a list of the tasks you recommend I tackle in that period).
    Each session takes the steps due today on its drives, except be•do's picks; its `top` (row keys or ids, with
    a why) lead the list, the rest follow folded. Every item is SESSION_MIN, a default, not her history."""
    out = list(items)
    for S in sessions:
        mine = [x for x in out if x.get('k') == 'step' and not x.get('done') and not x.get('pick')
                and (x.get('drive') or '') in S['drives']]
        if not mine or not S.get('a') or not S.get('b'):
            continue
        order = {k: i for i, (k, _) in enumerate(S.get('top') or [])}
        why = dict(S.get('top') or [])
        rank = lambda x: min(order.get(x.get('key') or '', 99), order.get(x.get('rid') or '', 99))
        mine.sort(key=rank)
        lst = [dict(t=x['t'], nx=x.get('nx'), drive=x.get('drive'), sz=SESSION_MIN, links=x.get('links') or None,
                    top=rank(x) < 99, why=why.get(x.get('key') or '') or why.get(x.get('rid') or '') or None)
               for x in mine]
        out = [x for x in out if x not in mine]
        out.append(dict(k='step', t=S['name'], a=S['a'], b=S['b'], drive=mine[0].get('drive'), done=False,
                        session=True, list=lst, cat=mine[0].get('cat'), sized=False,
                        nx=f'{len(lst)} small things, about {SESSION_MIN} min each by default — tap for the list'))
    return sorted(out, key=lambda x: (x['a'], x['k'] != 'event'))


def off_the_clock(schedule):
    """A weekend's clock holds her calendar and what she has lived; each open step leaves it for a list, with no time
    (7 Nov 2026, her words: take the time slot things off of my calendar for today because it's not work)."""
    step = lambda x: x.get('k') == 'step' and not x.get('done')
    tasks = [dict(t=x['t'], drive=x.get('drive') or None, nx=x.get('nx'), links=x.get('links') or None,
                  worked=x.get('worked'), key=x.get('key')) for x in schedule if step(x)]
    return [x for x in schedule if not step(x)], tasks


def sized(acts):
    """Each step with be•do's guess at its size (sz, minutes), marked a guess (szg)."""
    return [dict(a, sz=size_guess(a.get('t')), szg=True) for a in acts]


def build(D, rows, rhythms_read, L, behind_dir):
    F = L['fields']['stream']
    RF = L['fields']['rhythms']
    off = bedo_clock.Offset(L)   # per instant, from time_zone: a night across a change reads each end right
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
    data['timegoals'] = L.get('time_goals') or {}
    data['screen_measured'] = screen_measured(rows, F, off, today)
    # stories and media live on her Morning Gate; the page links there (7 Nov 2026, her words: I'd prefer to see all of the
    # stories / media stuff on my morning gate and just link to it). `media_gate` in her settings: the gate's link
    data['media_gate'] = L.get('media_gate') or None
    data['timelimits'] = L.get('time_limits') or {}   # hours a day at most, hers (7 Nov 2026: be•do, one would be good, two at most)   # hours a day for a kind of time, hers (7 Nov 2026: sleep 8, work 4, movement 2, food 1)
    data['hidden'] = list(L.get('hide_drives') or [])   # build work set aside, as everywhere on the page
    data['me'] = L.get('self_person') or ''   # her own name, left out of who was with her
    data['calcolors'] = L.get('calendar_colors') or {}   # each calendar's own colour, as Google shows it
    data['intentions'] = [x for x in (D.get('intentions') or []) if x]
    data['schedule'] = schedule_of(today, rows, today_page, F, off, set(L.get('hide_drives') or []),
                                   L.get('_flows') or frozenset(), dict(with_drives(care_settings(L), W, L), _phase=L.get('_phase') or {}),
                                   L.get('_picks'), me=L.get('self_person') or '')
    data['quest'] = quest_link(L, data['schedule'])
    data['night'] = night_of(rows, F, off, today, care_settings(L))
    # each card opens to what the 28 Oct day ahead showed (2 Nov 2026, her words: it would be so awesome to
    # have the day ahead show the detail about the next steps and everything the way that day ahead did):
    # her words on the row and its ways in (the chat, the deliverable, the links), from card 1's steps
    strip = lambda t: re.sub(r'^⚡\s*', '', (t or '').strip())
    detail = {strip(s.get('t')): s for s in C.get('steps') or []}
    # and only the links that serve the next step (her words, 2 Nov: not everything that's relevant, just what
    # is very relevant for the next step): the look ahead's own move for the row, its step and its ways in
    # the due lines of each day carry their move too (4 Nov 2026: a step's chat link sat there, unreached)
    moves = {strip(t.get('title')): t for t in [d for x in D.get('days') or [] for d in x.get('due') or []]
             + (D.get('tasks') or []) if isinstance(t, dict) and t.get('move')}
    for it in data['schedule']:
        s = detail.get(strip(it.get('t')))
        if s:
            it['det'] = s.get('det') or None
        t = moves.get(strip(it.get('t')))
        if t:
            mv = t.get('move') or {}
            it['emoji'] = t.get('emoji') or None
            if mv.get('step') and not it.get('nx'):
                it['nx'] = mv['step']
            got = [dict(l=x.get('label'), u=x.get('url')) for x in mv.get('links') or [] if x.get('url')]
            # an event keeps its own: `who` there is the calendar it came from, which picks its colour, and its links
            # are the ones folded in from its rows (5 Nov 2026, her words: when there is a calendar item that's on my
            # calendar and on this timeline the colors must match — the G&Gs were blue, not his calendar's yellow)
            if it.get('k') == 'event':
                it['links'] = (it.get('links') or []) + [x for x in got if x not in (it.get('links') or [])]
                it['with'] = mv.get('who') or None
            else:
                it['links'] = got
                it['who'] = mv.get('who') or None
            it['wait'] = mv.get('waiting') or None
    data['schedule'] = sessions_of(data['schedule'], L.get('_sessions') or [])
    # a Saturday or a Sunday is not a work day (7 Nov 2026, her words: take the time slot things off of my calendar
    # for today because it's not work; those are just tasks): only her calendar and what she has lived sit on the
    # clock; an open step goes to a list under it, with no time
    data['shape'] = D.get('shape') or ('saturday' if today.weekday() == 5 else 'sunday' if today.weekday() == 6 else 'weekday')
    if data['shape'] in ('saturday', 'sunday'):
        data['schedule'], data['tasks'] = off_the_clock(data['schedule'])
    # and Saturday's things she might want to do: fun first, low effort first, each with its way in and no clock
    if data['shape'] == 'saturday':
        import saturday
        data['ideas'] = saturday.ideas(today, rows, F, off, rhythms_read, RF, L, L.get('_stories'), L.get('_places'),
                                       data['intentions'])
        data['feel'] = saturday.feel(today, rows, F, off, L, rhythms_read, RF)
    if L.get('_photos'):
        photos_onto(data['schedule'], today, rows, F, off, L['_photos'], L.get('self_person') or '')
    if L.get('_heart'):
        heart_onto(data['schedule'], L['_heart'], off, L.get('hr_calm_max') or 80, care_settings(L))
    # the wheel at the bottom, built through the day (3 Nov 2026, her words: I would like to see the
    # wellness wheel at the bottom ... built throughout the day): today's lived rows so far, each under
    # its element, read the same way balance reads the day before; every rebuild of the page adds to it
    ents = []
    dom = wheel_of(today, rows, F, off, ents)
    data['wheel'] = dict(domains=dom, entries=sorted(ents, key=lambda e: e['at'])) if dom else None
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
        w['grew'] = grew_on(m, rows, F, rhythm_names, hidden, local)
        week.append(w)
    t = week[-1]
    keys = ('body', 'balance', 'effectiveness')
    # be•do's three, right under base flow (12 Nov 2026, her words: I like seeing the base flow first … and then I
    # want to see the Pareto 3, like the recommendation about what I work on today)
    data['three'] = [dict(t=p.get('title'), why=p.get('why'), drive=p.get('drive'), g=p.get('emoji'), st=(p.get('st') or '').strip(),
                          nx=((p.get('move') or {}).get('step')), who=(p.get('move') or {}).get('who') or [],
                          links=(p.get('move') or {}).get('links') or [], waiting=(p.get('move') or {}).get('waiting'))
                     for p in (D.get('pareto') or [])]
    # a finished day shows what she did, never a recommendation (14 Nov 2026, her words: no reason to do this; the thing I
    # accomplished was teaching and starting the trip): the actions closed that day and her ⭐ highlight; her
    # own picks (--pick) take their place when she names them
    data['picked'] = bool(L.get('_picks'))
    data['did'] = did_of(rows, F, off, today)
    data['three_next'] = [dict(t=x.get('title'), kind=x.get('kind')) for x in (D.get('next') or [])]
    data['three_more'] = [dict(t=p.get('title'), why=p.get('why'), drive=p.get('drive'), g=p.get('emoji'), st=(p.get('st') or '').strip(),
                               nx=((p.get('move') or {}).get('step')), links=(p.get('move') or {}).get('links') or [])
                          for p in (D.get('pareto_more') or [])]
    data['baseflow'] = dict(week=week, parts=[dict(name=k, value=t[k]) for k in keys if t[k] is not None],
                            missing=[k for k in keys if t[k] is None])
    return data


def plan_items(specs, rows, L):
    """The rest of today in order (12 Nov 2026, her journal: I'm happiest doing one thing at a time; the page leads with
    NOW and NEXT). Each names a row; it carries the row's time today (its target, or its own end), whether it is closed,
    its next step and its links. A label after :: replaces the row's title on the page."""
    F = L['fields']['stream']
    off = bedo_clock.Offset(L)
    by = {}
    for r in rows:
        c = r['cellValuesByFieldId']
        by[r['id']] = r
        if c.get(F['key']):
            by.setdefault(c[F['key']], r)
    out = []
    for spec in specs:
        ref, _, label = spec.partition('::')
        r = by.get(ref.strip())
        if not r:
            raise SystemExit(f'--plan/--later {ref.strip()!r}: no row with that key or record id in the stream read')
        c = r['cellValuesByFieldId']
        det = c.get(F['details']) if F.get('details') else ''
        tg = c.get(F['target'])
        t0 = dt.datetime.fromisoformat(tg.replace('Z', '+00:00')) + off if tg else None
        # only a time today that wasn't made up holds a place on the clock; the rest keep their place in the order
        if t0 and (t0.date().isoformat() != L.get('_day') or made_up(det)):
            t0 = None
        en = c.get(F['end']) if t0 else None
        t1 = (dt.datetime.fromisoformat(en.replace('Z', '+00:00')) + off) if en else \
            (t0 + dt.timedelta(minutes=60 if (F.get('event') and c.get(F['event'])) or re.search(r'(?i)meeting|with \\w+', c.get(F['title']) or '') else 15) if t0 else None)
        at, end = (t0.strftime('%H:%M') if t0 else None), (t1.strftime('%H:%M') if t1 else None)
        nx = [ln.split(':', 1)[1].strip() for ln in (det or '').split('\n') if re.match(r'(?i)\s*next( step)?:', ln)]
        links = re.findall(r'https?://[^\s)\],]+', det or '')
        if F.get('event') and c.get(F['event']):
            links.insert(0, c[F['event']])
        out.append(dict(id=r['id'], t=label.strip() or re.sub(r'^⚡\s*', '', c.get(F['title']) or ''), at=at, end=end,
                        st=c.get(F['status']) or '', done=(c.get(F['status']) or '') in CLOSED,
                        nx=nx[-1] if nx else None, links=links[:3], drive=c.get(F['rhythm']) or ''))
    return out


def phases_of(dd, L):
    """Each flow practice's phase (dawn or dusk), from the catalog read, when her settings name the catalog's `phase` field."""
    PF = (L.get('fields') or {}).get('practices') or {}
    path = os.path.join(dd, 'practices.json')
    if not PF.get('phase') or not os.path.exists(path):
        return {}
    out = {}
    for r in json.load(open(path, encoding='utf-8')).get('records') or []:
        c = r.get('cellValuesByFieldId') or {}
        ph = c.get(PF['phase']); ph = ph.get('name') if isinstance(ph, dict) else ph
        if ph and re.search(r'dawn|dusk', str(ph)) and c.get(PF.get('active'), True) is not False:
            out[low(c.get(PF['name']))] = ph
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day-ahead', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--behind')
    ap.add_argument('--out', required=True)
    ap.add_argument('--pick', action='append', default=[],
                    help='"<row key or record id>::<why>" — be•do\'s three for today, starred on the calendar')
    ap.add_argument('--photos', help="a folder of the day's small photos (day_photos.py --out), for her keepers")
    ap.add_argument('--heart', help="the day's Oura heart rate (day_heart.py --out): it decides relaxing versus energizing play")
    ap.add_argument('--session', action='append', default=[],
                    help='"<name>::HH:MM-HH:MM::<drive>|<drive>" — small steps on those drives, batched at that time')
    ap.add_argument('--session-top', action='append', default=[],
                    help='"<row key or record id>::<why>" — the session\'s top three, in order')
    ap.add_argument('--plan', action='append', default=[],
                    help='"<row key or record id>[::<label>]" — the rest of today in order, one thing at a time: NOW and NEXT')
    ap.add_argument('--later', action='append', default=[],
                    help='"<row key or record id>[::<label>]" — what waits quietly under NOW and NEXT')
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
    L['_phase'] = phases_of(dd, L)
    L['_flows'] = frozenset(L['_phase'])
    tops = [tuple((t.split('::', 1) + [''])[:2]) for t in a.session_top]
    L['_sessions'] = [dict(session_arg(s), top=tops) for s in a.session]
    L['_photos'] = a.photos
    L['_heart'] = a.heart
    # a Saturday's ideas: the stories queue and the places, when the fetch read them (by name, Saturdays only)
    for nm in ('stories', 'places'):
        pth = os.path.join(dd, f'ideas_{nm}.json')
        L[f'_{nm}'] = json.load(open(pth, encoding='utf-8')).get('records') if os.path.exists(pth) else None
    data = build(D, rows, rhythms_read, L, a.behind)
    L['_day'] = data['day']
    data['plan'] = plan_items(a.plan, rows, L)
    data['later'] = plan_items(a.later, rows, L)
    root = re.search(r':root\{[^}]*--c-moss[^}]*\}', h).group(0)
    night = re.search(r'html\[data-bedo="night"\]\{[^}]*\}', h).group(0)
    page = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()
    # the shared parts (the shell, the card, the theme button, the glyphs, the colours, the clock, the
    # base flow) come from plugins/bedo/assets/flow-parts, the one copy the my week page reads too
    page = (parts.fill(page.replace('/*ROOT*/', root).replace('/*NIGHT*/', night))
            .replace('/*DATA*/', json.dumps(data, ensure_ascii=False).replace('</', '<\\/')))
    # the flow page IS the day's my day page (since 2 Nov 2026), so it carries the day's my day name
    esc = lambda t: t.replace('&', '&amp;').replace('<', '&lt;')
    page = page.replace('<title>How Things Flow</title>', f'<title>{esc(data["chip"] or "How Things Flow")}</title>', 1)
    open(a.out, 'w', encoding='utf-8').write(page)
    bf = data['baseflow']['week'][-1]
    print(json.dumps(dict(out=a.out, body=bf['body'], balance=bf['balance'], buffer=bf['effectiveness']), ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
