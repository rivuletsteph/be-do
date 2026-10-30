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
  gaps      15+ minutes between the first and last waking row no span covers,
            filled from the clues (2 Oct 2026: fill it from the clues, don't ask):
            where Timeline has her, or what she logged inside it. The rows
            either side name the stretch but never fill it on their own — a
            row that says only 'between two things' is padding, not the day.
            A stretch with no clue at all is left open, quietly: one line
            counts it, never a question (9 Oct: the system works even when
            she isn't logging every minute)
  movement  walking, cycling or exercise she mentions with no movement row
            near it; a movement row with no minutes (rule 7)
  people    person set on a plan (rule 6); a name no connection matches
  device    device and wellness, deduced (rule 1, bedo_fill)
  spans     a row over 12 h, or one whose end is on another day (rules 2, 5)
  overlaps  two things at once are both recorded, in full, and each carries
            🌓 partial attention (9 Oct 2026: nothing is beaten out)
  synergy   and are they synergizing or competing? (24 Aug and 9 Oct 2026).
            What her words already say is noticed back — synergy, do more of
            that; competing, try them apart. A pair she answered in past weeks
            is proposed with that answer. Anything new is one optional question

What the day's own records hold (30 Oct 2026, her words at Thursday's day
behind: I want those things built into the QA, so they're already in the
stream when it gets built). These come first, and the four marked `do` are
the QA's own work, done before her list is shown, never asked of her:
  calendar  every event on her calendars that she marked done (✔️) gets its
            own row, its times as the calendar has them now (she corrects the
            calendar to what happened); a row already about it gets the link
  journal   a journal whose [be•do] block has no `Pulled out:` line was never
            read through: read it now for what it names with a time, a place
            or a person (a meeting she sat in, what she worked on meanwhile)
  photos    a photo or screenshot from the day no row explains, Timeline
            screenshots above all: read it and write what it shows
  painted   a stretch a row covers that the day page draws as nothing, being
            or doing (the rainbow's own rules, day_rings): give the row a
            practice or a drive the page reads

    python3 bedo_dayqa.py --live --date 2026-10-09 [--json]
    python3 bedo_dayqa.py --day day.json [--catalog practices.json] [--rhythms rhythms.json]
                          [--connections connections.json] [--history w40.json …] --date 2026-10-09
"""
import collections, datetime as dt, json, re, sys

from bedo_reader import FACTS, as_rows, cells, complete, load_local, offset_hours, on_day, sv
from bedo_entry import OVERNIGHT, PARTIAL, RULES, overlaps, span_problems, utc
import bedo_entry as E
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
NOTES = {FL.word(p) for p in Q['note_practices']}
LOCATION = FL.word(FACTS['practice']['location'])
NAMES = ('datetime', 'end', 'time_spent', 'status', 'title', 'details', 'practice', 'person',
         'mentioned', 'wellness', 'device', 'rhythm', 'photo', 'key', 'attention',
         'calendar_event', 'photo_checked', 'photo_links')


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


def todo(check, line, rows=()):
    """The QA's own work, done before her list is shown (30 Oct 2026)."""
    return {'check': check, 'kind': 'do', 'line': line, 'rows': list(rows)}


# ── what the day's own records hold (30 Oct 2026) ───────────────────────
DONE_MARKS = tuple(Q.get('calendar_done_marks') or ('✔️', '✔', '✅'))
READ_MARK = Q.get('journal_read_mark') or 'Pulled out'
JOURNAL = 'journal'
EID = re.compile(r'[?&]eid=([\w-]+)')


def _event_link(e):
    return e.get('htmlLink') or ''


def _event_at(x):
    v = (x or {}).get('dateTime')
    return utc(v).astimezone(dt.timezone.utc) if v else None


def _same_event(link, e):
    """A row's event link names this event (its eid, or its id inside the eid)."""
    if not link:
        return False
    m, mine = EID.search(link), EID.search(_event_link(e))
    if m and mine and m.group(1).rstrip('=') == mine.group(1).rstrip('='):
        return True
    return bool(e.get('id')) and e['id'] in link


def _words(s):
    return {w for w in re.findall(r'[a-z]{4,}', (s or '').lower())}


def _bare(summary):
    t = summary or ''
    for m in DONE_MARKS + ('⬜',):
        t = t.replace(m, '')
    return t.strip()


def events_from(listing):
    """The day's events from one or more list_events results saved as they came
    ({"events": […]}, or a list), each keeping the calendar it came from."""
    out = []
    for x in listing if isinstance(listing, list) and listing and isinstance(listing[0], dict) \
            and 'events' in listing[0] else [listing]:
        evs = x.get('events') if isinstance(x, dict) else x
        cal = x.get('summary') if isinstance(x, dict) else None
        for e in evs or []:
            out.append(dict(e, _calendar=e.get('calendarId') or cal))
    return out


def calendar(rows, events, off, practice, theirs=()):
    """Every event she marked done gets its row (30 Oct 2026: it seems to leave
    off my meeting calendar items that I just adjusted to more accurately match
    what happened). Her son's calendar is his day, not hers."""
    out = []
    lived = [r for r in rows if r.get('status') not in NOT_LIVED and r.get('datetime')]
    for e in events:
        a, b = _event_at(e.get('start')), _event_at(e.get('end'))
        s = e.get('summary') or ''
        if not a or not b or e.get('status') == 'cancelled' or not s.startswith(DONE_MARKS):
            continue
        if any(t and t in (e.get('_calendar') or '') + ' ' + (e.get('organizer') or {}).get('email', '')
               for t in theirs):
            continue
        if any(_same_event(r.get('calendar_event'), e) for r in rows):
            continue
        t = _bare(s)
        when = f'{_clock(a, off)}–{_clock(b, off)}'
        about = [r for r in lived if utc(r['datetime']) < b and utc(r.get('end') or r['datetime']) >= a
                 and _words(t) & _words(r.get('title'))]
        if about:
            r = about[0]
            out.append(fill('calendar', f'“{_t(r)}” is your calendar\'s {t} ({when}): link it', SRC['calendar'],
                            patch={'id': r['id'], 'fields': {'calendar_event': _event_link(e)}}))
            continue
        out.append(fill('calendar', f'{t} {when}, from your calendar', SRC['calendar'], new={
            'datetime': _z(a), 'end': _z(b), 'status': FACTS['status']['actions'][3], 'practice': practice,
            'title': t, 'calendar_event': _event_link(e),
            'details': f'{DIVIDER}\n[be•do] From her calendar, as she marked it done: {s}, {when}.'}))
    return out


def journals(rows, off):
    """A journal read through when it came in carries `Pulled out:` in its block."""
    out = []
    for r in rows:
        if FL.word(r.get('practice')) != JOURNAL or r.get('status') in NOT_LIVED:
            continue
        block = (r.get('details') or '').split(DIVIDER, 1)[-1]
        if READ_MARK.lower() not in block.lower():
            out.append(todo('journal', f'the journal at {_clock(utc(r["datetime"]), off)} (“{_t(r)}”) was never read '
                            'through: pull out what it names with a time, a place or a person as rows, and what she '
                            f'was doing meanwhile, then write `{READ_MARK}:` in its block', [r.get('id')]))
    return out


def photos(rows, files, off, day, me=''):
    """A photo or screenshot from the day no row explains is read, not left as a
    clue (30 Oct 2026: especially the timeline)."""
    import bedo_photos as PH
    def loc(s):
        return (utc(s) + dt.timedelta(hours=off)).replace(tzinfo=None) if s else None
    lived = [dict(r, _a=loc(r.get('datetime')), _b=loc(r.get('end'))) for r in rows if r.get('datetime')]
    listing = [x for x in PH.files_from(files) if (PH.taken(x['name'], off) or dt.datetime.min).date() == day]
    m = PH.match(lived, listing, off, me)
    if not m['unlogged']:
        return []
    shots = [f for f in m['unlogged'] if PH.is_screenshot(f['name'])]
    rest = [f for f in m['unlogged'] if f not in shots]
    names = ', '.join(f'{f["name"]} ({f["taken"]:%H:%M})' for f in shots + rest)
    return [todo('photos', f'{len(m["unlogged"])} photo(s) from the day no row explains'
                 + (f', {len(shots)} of them screenshots (a Timeline screenshot holds the day\'s places and drives)'
                    if shots else '') + f': read each and write what it shows — {names}', [f['file'] for f in shots + rest])]


def painted(rows, day, L, lb=None):
    """Stretches a row covers that the day page draws as neither being nor doing,
    by the page's own rules (30 Oct 2026: how it would be categorized for the
    graphic). Needs day_rings beside the core; without it, says so once."""
    try:
        from day_rings import day_rings
    except ImportError:
        return [{'check': 'painted', 'kind': 'count', 'line': 'painted: not checked (day_rings is not beside the core)'}]
    R2 = {**L, **{k: v for k, v in (lb or {}).items() if k in ('care', 'recreation', 'system_rhythm', 'day_goals')}}
    rr = [dict(r, when=r.get('datetime'), event=r.get('calendar_event'), spent=r.get('time_spent')) for r in rows]
    R = day_rings(rr, day, R2, frozenset(), NOT_LIVED)
    cov = [False] * 1440
    for b in R['bands']:
        if b['k'] in ('being', 'doing'):
            for run in b['runs']:
                for m in range(run[1], run[2]):
                    cov[m] = True
    for k, a, b in R['night']:
        for m in range(a, b):
            cov[m] = True
    off = offset_hours(L, dt.datetime.combine(day, dt.time(12), dt.timezone.utc))
    s0 = dt.datetime.combine(day, dt.time(0))
    def local(ts):
        return (utc(ts) + dt.timedelta(hours=off)).replace(tzinfo=None)
    spans = []
    for r in rows:
        if r.get('status') in NOT_LIVED or not r.get('datetime') or not r.get('end'):
            continue
        a, b = local(r['datetime']), local(r['end'])
        if b > a and b - a <= dt.timedelta(hours=14):
            spans.append((max(0, int((a - s0).total_seconds() // 60)), min(1440, int((b - s0).total_seconds() // 60)), r))
    out, m = [], 0
    need = Q['gap_minutes']
    while m < 1440:
        if cov[m] or not any(a <= m < b for a, b, _ in spans):
            m += 1
            continue
        g = m
        while m < 1440 and not cov[m] and any(a <= m < b for a, b, _ in spans):
            m += 1
        if m - g >= need:
            who = [r for a, b, r in spans if a < m and b > g]
            hm = lambda x: f'{x // 60 % 12 or 12}:{x % 60:02d}{"a" if x < 720 else "p"}'
            out.append(todo('painted', f'{hm(g)}–{hm(m)} ({m - g} min) draws as nothing on the day page: '
                            + '; '.join(f'“{_t(r)}”' for r in who[:3])
                            + ' — give it the practice or drive that says what it was', [r.get('id') for r in who]))
    return out


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


LOG_PRACTICE = '📝 log'


def _gap_fill(g, t, mins, off, at, inside, before, after, ctx):
    """One row for the stretch, from the best clue there is, or None."""
    clues, src = [], None
    if at:
        clues.append(f'{SRC["timeline"]} has you at {_t(at)}')
        src = SRC['timeline']
    for r in inside:
        clues.append(f'“{_t(r)}” at {_clock(utc(r["datetime"]), off)}')
        src = src or anchor(r)
    if before:
        clues.append(f'after “{_t(before)}”')
    if after:
        clues.append(f'before “{_t(after)}”')
    if not (at or inside):
        return None
    src = src or SRC['rule'] + ' (fill a stretch from what you logged in it)'
    what = f'at {_t(at)}' if at else f'{_t(inside[0])}'
    new = {'datetime': _z(g), 'end': _z(t), 'status': FACTS['status']['logs'][0], 'practice': LOG_PRACTICE,
           'title': f'{LOG_PRACTICE.split(" ")[0]} {what} (estimated)',
           'details': f'{DIVIDER}\n[be•do] {EST}: not logged by her. Clues: ' + '; '.join(clues) + '.'}
    # wellness from what she logged in it, or the place's own; device by the rules
    well = collections.Counter(r['wellness'] for r in inside + [at] if r and r.get('wellness'))
    if well:
        new['wellness'] = well.most_common(1)[0][0]
    # a stretch with family that nothing else names is heart, with the people on it (19 Oct 2026)
    people = (getattr(ctx, 'local', None) or {}).get('people') or {}
    fam = {v for k, v in people.items() if k != 'self' and v}
    with_ = sorted({p.strip() for r in inside + [at] if r for p in (r.get('person') or '').split(',')} & fam)
    if with_:
        new['person'] = ', '.join(with_)
        if not well:
            new['wellness'] = FACTS['wellness']['be'][0]
    got, _ = FL.deduce(new, ctx) if ctx else ({}, [])
    new.update({f: v for f, (v, _) in got.items()})
    return fill('gaps', f'{_clock(g, off)}–{_clock(t, off)} ({mins} min) {new["title"]}; clues: '
                        + '; '.join(clues), src, new=new)


def gaps(rows, off, proposed=(), ctx=None):
    """Last, so the spans the other checks propose already cover their minutes."""
    lived = [r for r in rows if r.get('status') not in NOT_LIVED and r.get('datetime')]
    ends = {i['patch']['id']: i['patch']['fields']['end'] for i in proposed   # a synergy note patches no fields
            if i.get('patch') and 'end' in (i['patch'].get('fields') or {})}
    spanned = [dict(r, end=ends.get(r.get('id'), r.get('end'))) for r in lived]
    spanned += [i['new'] for i in proposed if i.get('new') and i['new'].get('end')]
    covers = [(utc(r['datetime']), utc(r['end'])) for r in spanned
              if r.get('end') and FL.word(r.get('practice')) != LOCATION and utc(r['end']) > utc(r['datetime'])]
    places = [r for r in lived if FL.word(r.get('practice')) == LOCATION and r.get('end')]
    awake = [r for r in lived if FL.word(r.get('practice')) not in OVERNIGHT]
    if not awake:
        return []
    lo = min(utc(r['datetime']) for r in awake)
    woke = [utc(r['datetime']) for r in awake if FL.word(r.get('practice')) == FL.word(FACTS['flows']['wake'])]
    lo = max([lo] + woke[:1])          # the day opens when she wakes; the night is not a gap
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
        # a place covers only its own hours: split the stretch at its edges
        cuts = sorted({g, t} | {x for p in places for x in (utc(p['datetime']), utc(p['end'])) if g < x < t})
        for a_, b_ in zip(cuts, cuts[1:]):
            out += _one_gap(a_, b_, off, lived, places, ctx)
    return out


def _one_gap(g, t, off, lived, places, ctx):
    """A stretch filled from a clue, or counted open. A clue inside it is a row
    with her words, a photo, a message or Oura — a bare routine tick (a coffee
    logged as a moment) says nothing about the stretch around it."""
    mins = int((t - g).total_seconds() // 60)
    if mins < Q['gap_minutes']:
        return []
    not_place = lambda r: FL.word(r.get('practice')) != LOCATION
    at = next((p for p in places if utc(p['datetime']) <= g < utc(p['end'])), None)
    inside = [r for r in lived if g <= utc(r['datetime']) < t and not r.get('end') and not_place(r)
              and (anchor(r) or FL.word(r.get('practice')) in NOTES)]
    before = max((r for r in lived if utc(r['datetime']) < g and not_place(r)), key=lambda r: r['datetime'], default=None)
    after = min((r for r in lived if utc(r['datetime']) >= t and not_place(r)), key=lambda r: r['datetime'], default=None)
    it = _gap_fill(g, t, mins, off, at, inside, before, after, ctx)
    return [it or {'check': 'gaps', 'kind': 'open', 'mins': mins,
                   'line': f'{_clock(g, off)}–{_clock(t, off)} ({mins} min)'}]


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
    # a movement row with no minutes isn't asked about: the look behind gives it
    # her typical length, marked estimated (9 Oct: don't ding her for every minute)
    return out


def people(rows, index, self_name=None):
    """Her own name on her own row stays: only other people move to mentioned."""
    out = []
    for r in rows:
        who = [p.strip() for p in (r.get('person') or '').split(',') if p.strip()]
        others = [p for p in who if p != self_name]
        if not others:
            continue
        if r.get('status') in PLANS:
            keep = [p for p in who if p == self_name]
            who = others
            had = [p.strip() for p in (r.get('mentioned') or '').split(',') if p.strip()]
            ment = ', '.join(dict.fromkeys(had + who))
            out.append(fill('plans', f'{_t(r)}: {", ".join(who)} from person to mentioned — a plan, not yet met',
                            SRC['rule'] + ' (rule 6)',
                            patch={'id': r['id'], 'fields': {'person': ', '.join(keep), 'mentioned': ment}}))
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
            usual = all(w == 'what this practice usually carries' for _, w in got.values())
            src = SRC['usual'] if usual else f'{SRC["rule"]} (rule 1: {why})'
            out.append(fill('device', f'{_t(r)} → {" · ".join(fields.values())}', src,
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


def overlapping(rows, off):
    out = []
    for r in sorted(rows, key=lambda r: r.get('datetime') or ''):
        both = overlaps(r, rows)
        if not both or r.get('attention') == PARTIAL or not r.get('id'):
            continue
        with_ = ', '.join(f'{_t(o)[:40]} ({_clock(utc(o["datetime"]), off)}–{_clock(utc(o["end"]), off)})' for o in both[:3])
        was = f', not {r["attention"]}' if r.get('attention') else ''
        out.append(fill('overlaps', f'{_t(r)} {_clock(utc(r["datetime"]), off)}–{_clock(utc(r["end"]), off)} '
                                    f'→ {PARTIAL}{was}: it shared minutes with {with_}',
                        SRC['rule'] + ' (nothing is beaten out: both recorded, partial attention)',
                        patch={'id': r['id'], 'fields': {'attention': PARTIAL}}))
    return out


SY = FACTS['synergy']
_NOTE = re.compile(r'(?i)overlap\s*[—–-]+\s*(' + '|'.join(SY['answers']) + r')\b,?\s*with\s+(.+)')


def _pair_key(a, b):
    return tuple(sorted((FL.word(a.get('practice')), FL.word(b.get('practice')))))


def _said(r):
    """(answer, partner text) from her overlap note, else (answer, None) read
    from her own words about it ('there was a lot of synergy there', 'I was so
    distracted'), else (None, None)."""
    words = her_words(r)
    m = _NOTE.search(words)
    if m:
        return m.group(1).lower(), m.group(2).strip()
    return E.synergy_from(words)[0], None


def _partner(o):
    return f'{o["key"]} ({_t(o)[:40]})' if o.get('key') else _t(o)[:50]


def synergy(rows, off, history=()):
    """Noticed lines, the note line filled from her words or her past weeks,
    and a count of the rest. Never a question (her rule, 23 and 27 Oct 2026:
    deduce it from what I say; it doesn't work to ask me after the fact): a pair
    her words say nothing about is counted and the QA moves on."""
    past = {}
    by_key = {r.get('key'): r for r in history if r.get('key')}
    for r in history:
        ans, partner = _said(r)
        if not ans or not partner:
            continue
        o = by_key.get(partner.split()[0])
        if o:
            past.setdefault(_pair_key(r, o), ans)
    out, seen, unknown = [], set(), []
    for r in sorted(rows, key=lambda r: r.get('datetime') or ''):
        for o in overlaps(r, rows):
            pk = tuple(sorted((r.get('id') or '', o.get('id') or '')))
            if pk in seen:
                continue
            seen.add(pk)
            pair = f'{_t(r)[:40]} + {_t(o)[:40]}'
            noted = _NOTE.search(her_words(r)) or _NOTE.search(her_words(o))
            mine, other = r, o                      # the note goes on the row whose words carry it
            ans, cue = E.synergy_from(her_words(r))
            if not ans:
                ans, cue = E.synergy_from(her_words(o))
                mine, other = o, r
            if noted:
                a = noted.group(1).lower()
                out.append({'check': 'synergy', 'kind': 'notice', 'answer': a,
                            'line': f'{pair}: {SY["say"][a]}'})
            elif ans:
                note = SY['note'].format(answer=ans, partner=_partner(other))
                out.append(fill('synergy', f'{pair}: {ans}, from your words (“{cue}”) — {SY["say"][ans]}',
                                SRC['words'], patch={'id': mine.get('id'), 'append_her_words': note}, note=note))
            elif past.get(_pair_key(r, o)):
                a = past[_pair_key(r, o)]
                note = SY['note'].format(answer=a, partner=_partner(o))
                out.append(fill('synergy', f'{pair}: {a}, as you said of these two before — {SY["say"][a]}',
                                SRC['usual'], patch={'id': r.get('id'), 'append_her_words': note}, note=note))
            else:
                unknown.append(pair)
    if unknown:
        out.append({'check': 'synergy', 'kind': 'count', 'n': len(unknown),
                    'line': f'{len(unknown)} two things at once with no answer — counted, not asked after the fact'})
    return out


def gate(rows, off):
    """(share lacking device or wellness, rows over 12 h) — the look behind's gate."""
    lived = [r for r in rows if r.get('status') not in NOT_LIVED]
    lack = [r for r in lived if not r.get('wellness') or not r.get('device')]
    long_ = [r for r in rows if r.get('datetime') and r.get('end')
             and utc(r['end']) - utc(r['datetime']) > dt.timedelta(hours=RULES['max_span_hours'])]
    return (len(lack), len(lived)), long_


def run(rows, day, off, local, ctx=None, index=None, catalog_names=(), typical=None, history=(),
        events=None, files=None, lb=None):
    ctx = ctx or FL.Context(day_rows=rows, local=local)
    cal_practice = next((n for n in catalog_names if FL.word(n) == 'calendar event'), '🗓️ calendar event')
    theirs = tuple(((lb or {}).get('care') or {}).get('family', {}).get('calendars') or ())
    first = (calendar(rows, events_from(events), off, cal_practice, theirs) if events is not None else []) \
        + journals(rows, off) \
        + (photos(rows, files, off, day, (local.get('people') or {}).get('self') or '') if files is not None else []) \
        + painted(rows, day, local, lb)
    items = first + (meals(rows, off, (local.get('people') or {}).values())
             + movement(rows, off, day, local, catalog_names, typical)
             + people(rows, index, (local.get('people') or {}).get('self'))
             + device(rows, ctx)
             + spans(rows, off)
             + overlapping(rows, off)
             + synergy(rows, off, history))
    items += gaps(rows, off, items, ctx)
    # Logging the important things well is what matters (9 Oct 2026): what she did,
    # ate, moved and who she was with, one item each; the bookkeeping — device,
    # wellness, partial attention — one item per kind, accepted at once. Then the
    # few questions, wrong data first; a stretch with no clue is counted, never asked.
    order = ['calendar', 'meals', 'movement', 'people', 'gaps', 'synergy', 'overlaps', 'plans', 'device', 'spans']
    rank = lambda i: order.index(i['check']) if i['check'] in order else len(order)
    fills = [i for i in items if i['kind'] == 'fill']
    batched = []
    for check, what in (('overlaps', 'partial attention where two things happened at once'),
                        ('synergy', 'two things at once, synergy or competition read from your words'),
                        ('plans', 'people on plans moved to mentioned'),
                        ('device', 'device and wellness')):
        mine = [i for i in fills if i['check'] == check]
        if len(mine) > 1:
            srcs = collections.Counter(i['source'].split(' (')[0] for i in mine)
            batched.append({'check': check, 'kind': 'fill', 'line': f'{what}: {len(mine)} rows — accept all, or name any to leave',
                            'source': ' · '.join(f'{s} ({n})' for s, n in srcs.most_common()),
                            'patches': [i['patch'] for i in mine], 'rows': [i['line'] for i in mine],
                            'note': f'[be•do] {EST}: {what}'})
            fills = [i for i in fills if i['check'] != check]
    asks = [i for i in items if i['kind'] == 'ask']
    nodev = [i for i in asks if i['check'] == 'device']
    if len(nodev) > 1:      # one line, not a question per row
        asks = [i for i in asks if i['check'] != 'device'] + [{
            'check': 'device', 'kind': 'ask', 'rows': [i['line'] for i in nodev],
            'line': f'{len(nodev)} rows nothing deduces (no rule, no usual) — name a device or wellness, '
                    'or leave them: ' + '; '.join(i['line'].split('“', 1)[-1].split('”')[0][:40] for i in nodev[:4])
                    + (' …' if len(nodev) > 4 else '')}]
    asks.sort(key=lambda i: -('spans' == i['check']))
    items = ([i for i in items if i['kind'] == 'do'] + sorted(fills + batched, key=rank) + asks
             + [i for i in items if i['kind'] == 'open']
             + [i for i in items if i['kind'] in ('notice', 'count')])
    for i, it in enumerate(i for i in items if i['kind'] in ('fill', 'ask')):
        it['n'] = i + 1
    return items


def render(items, day, rows, off, now_local=None):
    (lack, n), long_ = gate(rows, off)
    fills = [i for i in items if i['kind'] == 'fill']
    asks = [i for i in items if i['kind'] == 'ask']
    open_ = [i for i in items if i['kind'] == 'open']
    seen = [i for i in items if i['kind'] == 'notice']
    todo_ = [i for i in items if i['kind'] == 'do']
    lines = []
    if todo_:
        lines.append(f'first, for the QA itself — {len(todo_)} to do before her list is shown, then run dayqa again:')
        lines += [f'  · {i["check"]} · {i["line"]}' for i in todo_]
    lines.append(f'dayqa · {day:%a %d %b} — {len(fills)} to accept' + (f', {len(asks)} if you want' if asks else ''))
    for i in fills:
        lines.append(f'  {i["n"]}. {i["check"]} · {i["line"]} · {EST} · source: {i["source"]}')
    if asks:
        lines.append('  if you want — skip any of these and the day stands as it is:')
        lines += [f'  {i["n"]}. {i["check"]} · {i["line"]}' for i in asks]
    if seen:
        lines.append('  noticed — two things at once:')
        lines += [f'    {"🔗" if i["answer"] == "synergizing" else "⚔" if i["answer"] == "competing" else "·"} {i["line"]}'
                  for i in seen]
    lines += [f'  {i["line"]}' for i in items if i['kind'] == 'count']
    if open_:
        lines.append(f'  left open, no clue: {sum(i["mins"] for i in open_)} min (' + ', '.join(i['line'] for i in open_) + ')')
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
    ap.add_argument('--calendar', action='append', default=[],
                    help="a list_events result for one of her calendars for the day, saved as it came (once per calendar)")
    ap.add_argument('--photos', help="the week's W## photos folder listing, as saved for the dusk audit")
    ap.add_argument('--look-behind-local', dest='lbl', help='the page settings, for the painted check (--live reads them)')
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    lb = json.load(open(a.lbl, encoding='utf-8')) if a.lbl else None
    if lb is None and a.live:
        try:
            from bedo_settings import fetch
            lb, _ = fetch('look_behind_local')
        except Exception:
            lb = None
    if lb and not (L.get('stream_fields') or {}).get('photo_links'):
        got = (lb.get('fields') or {}).get('stream') or {}
        L.setdefault('stream_fields', {}).update({k: got[k] for k in ('photo_links', 'photo_checked') if got.get(k)})
    events = [json.load(open(f, encoding='utf-8')) for f in a.calendar] if a.calendar else None
    files = json.load(open(a.photos, encoding='utf-8')) if a.photos else None
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
        # last week, for her usuals and the pairs she has answered before
        from bedo_entry import week_number
        prev = L.get('weekly_name', 'w{n} be•do').format(n=week_number(day) - 1)
        names_ = air.bases()
        if prev in names_ and not a.history:
            hist += as_rows(complete(air.dump(names_[prev], L['stream_table'], by_id=True), prev), fields)
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
                catalog_typical(cat, L) if cat else None, hist, events, files, lb)
    now_local = now + dt.timedelta(hours=offset_hours(L, now))
    if a.json:
        print(json.dumps({'day': day.isoformat(), 'items': items,
                          'marker': marker(day, sum(i['kind'] == 'fill' for i in items), now_local)},
                         ensure_ascii=False, indent=1))
    else:
        print(render(items, day, rows, off, now_local))


if __name__ == '__main__':
    main()
