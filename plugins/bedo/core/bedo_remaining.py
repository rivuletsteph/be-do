# -*- coding: utf-8 -*-
"""The remaining list: what is left of the open flow, read, never recalled.

Each line is a rule a chat used to have to remember, and skipped:

  A127  built from the CATALOG, filtered to active, for the open flow — 11 Sep
        dropped 🌬️ evening breaths for a whole evening because the list was typed
        from memory
  A166  remainders only, with a done count on top; done steps are left off
  A208  bare practice names: no cadence, no last-logged line, no reasons
  A200 · A227  📿 morning mantra prints as its name; the words come on request
  A228  nothing leaves the catalog and every step counts toward done; the
        core is named, everything else is its glyph after `also:`
  line  ONE line in a code box, never a widget and never a stacked list (her
        words 7, 8, 11 and 20 Oct 2026: printed horizontally in code, no widget
        that needs to drop and go away): flow glyph, n of N, the remaining
        practices in order separated by ·, then also: and the other glyphs
  A126  the dawn list stops printing at noon; dusk opens after 7 PM
  either  🌬️ evening breaths and 🌙 evening meditation are an either-or: one
        logged closes both, and the other is never asked for (8 Oct 2026)
  closes  a flow closes right after its last logged step, read from the stream,
        without waiting for her (21 Nov 2026): a row of the same kind counts as
        the step (facts flows.same_kind: a 📗 book row that morning is 📗
        morning book); once nothing required is left the line below the box
        says to write the close now, at the last step's time; past the backup
        hour (flows.backup_close) it says to write the backup close, unasked
  sun-by  🔅 morning sun by an hour after sunrise or waking, whichever is
        later: the line names that time while the sun is still to come (8 Oct).
        On a cloudy morning (the weather check says so) it names her bright
        light instead: still due, by the same time (28 Oct)

Predicted order is the catalog's `typical time` (bedo_order: which step came
before which on her recent mornings), then its `order` field; see flow_steps. Nothing personal lives here: the flow's practices come from
the live catalog, the core from facts.json.

    python3 bedo_remaining.py --live                 # the open flow, now
    python3 bedo_remaining.py --live --flow dusk     # a named flow
    python3 bedo_remaining.py --catalog practices.json --day day.json --flow dawn
"""
import datetime as dt, re, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, on_day

FLOWS = FACTS['flows']
_MODS = re.compile('[️\U0001F3FB-\U0001F3FF]')


def norm(name):
    """A practice name compared without variation selectors or skin tones, so
    🤸🏻‍♀️ and 🤸‍♀️ are one step. The catalog's own spelling is what prints."""
    return ' '.join(_MODS.sub('', name or '').split()).casefold()


def catalog(src, fields=None):
    """Catalog rows from a complete read (I11), under logical names."""
    return as_rows(complete(src, 'practices catalog'), fields or FACTS['catalog_fields'])


def _hhmm(s):
    h, m = s.split(':')
    return dt.time(int(h), int(m))


def typical_minutes(value):
    """The catalog's `typical time`, as minutes to sort by: 'wake+25' → 25 for
    dawn; '20:40' → 1240 for dusk, with after-midnight counted as late that
    night ('00:15' → 1455). Anything else → None."""
    v = (value or '').strip()
    m = re.fullmatch(r'wake\+(\d+)', v)
    if m:
        return int(m.group(1))
    m = re.fullmatch(r'(\d{1,2}):(\d{2})', v)
    if m:
        h, mm = int(m.group(1)), int(m.group(2))
        return h * 60 + mm + (1440 if h < 5 else 0)
    return None


_SUNRISE = re.compile(r'sunrise\D{0,3}(\d{1,2}):(\d{2})\s*([ap])', re.I)


def sunrise(rows, loc):
    """(date, minutes after midnight) of the newest sunrise her weather check
    wrote down ('sunrise 7:27 am', 'sunrise 7:26a'), or None. A day or two old
    is fine: it moves about a minute a day, and no location is ever stored."""
    for r in sorted(rows, key=lambda r: r.get('datetime') or '', reverse=True):
        m = _SUNRISE.search(r.get('details') or '')
        if m and r.get('datetime'):
            h, mm, ap = int(m.group(1)) % 12, int(m.group(2)), m.group(3).lower()
            t = dt.datetime.fromisoformat(r['datetime'].replace('Z', '+00:00'))
            return (t + dt.timedelta(hours=offset_hours(loc, t))).date(), (h + (12 if ap == 'p' else 0)) * 60 + mm
    return None


def sun_gate(day_rows, rise, loc):
    """{practice: minutes after today's wake it can't come before} — sunrise
    holds back the steps facts names (A237). Needs today's 😶 wake row; without
    it there is nothing to measure from and nothing is held."""
    if not rise:
        return {}
    wakes = [r['datetime'] for r in day_rows if norm(r.get('practice')) == norm(FLOWS['wake']) and r.get('datetime')]
    if not wakes:
        return {}
    t = dt.datetime.fromisoformat(min(wakes).replace('Z', '+00:00'))
    w = t + dt.timedelta(hours=offset_hours(loc, t))
    after = rise[1] - (w.hour * 60 + w.minute)
    return {norm(p): after for p in FLOWS['after_sunrise']} if after > 0 else {}


def flow_steps(cat, flow, first=(), not_before=None):
    """The open flow's steps: active, in the flow's phase, a flow or optional
    step (or any step the catalog gave an order in that phase), in her
    predicted order (A237):
      1  what she says she is doing next (`first`), that time only
      2  her stated sequences (facts flows.sequences) — they beat any median
      3  the typical time observed from her rows (bedo_order), held back
         past sunrise for the steps that wait for it (`not_before`)
      4  steps with no typical time, in the catalog's order
      5  the flow close, always last
    then her lead steps (facts flows.leads) move to the front, in her order:
    💭 dream record, the 🪐 sleep readout, then 🗞️ morning gate, whatever their
    observed times (10 and 20 Nov 2026). A lead given as a bare glyph is the
    step whose name starts with it."""
    phase = FLOWS['phase'][flow]
    steps = [r for r in cat if r.get('active') and r.get('phase') == phase and r.get('practice')
             and (r.get('group') in FLOWS['groups'] or r.get('order') is not None)]
    close = norm(FLOWS['close'][flow])

    def key(r):
        t = typical_minutes(r.get('typical_time'))
        nb = (not_before or {}).get(norm(r['practice']))
        if nb is not None:
            t = max(t, nb) if t is not None else nb
        return (norm(r['practice']) == close, t is None, t or 0,
                r.get('order') is None, r.get('order') or 0, r['practice'])
    steps.sort(key=key)
    at = lambda name: (next((i for i, r in enumerate(steps) if norm(r['practice']) == norm(name)), None)
                       if ' ' in name.strip() else lead_at(steps, name))   # a bare glyph is the step it starts (24 Nov 2026)
    for _ in range(len(steps)):                   # a stated sequence moves the later step after the earlier
        moved = False
        for a, b in FLOWS.get('sequences', {}).get(flow, []):
            ia, ib = at(a), at(b)
            if ia is not None and ib is not None and ib < ia:
                steps.insert(ia, steps.pop(ib))
                moved = True
        if not moved:
            break
    for name in reversed(FLOWS.get('leads', {}).get(flow, [])):   # her lead steps come next (10 Nov 2026)
        i = at(name) if ' ' in name.strip() else lead_at(steps, name)
        if i is not None:
            steps.insert(0, steps.pop(i))
    for name in reversed([f for f in first if f]):
        i = at(name)
        if i is not None and norm(steps[i]['practice']) != close:
            steps.insert(0, steps.pop(i))
    return steps


def lead_at(steps, glyph):
    """The index of the step whose name starts with this glyph, or None."""
    g = norm(glyph)
    return next((i for i, r in enumerate(steps) if norm(r['practice']).split(' ')[0] == g), None)


def leads(flow, steps):
    """The catalog names of her lead steps in this flow — always named on the
    line, core or not (20 Nov 2026)."""
    out = []
    for name in FLOWS.get('leads', {}).get(flow, []):
        i = (next((j for j, r in enumerate(steps) if norm(r['practice']) == norm(name)), None)
             if ' ' in name.strip() else lead_at(steps, name))
        if i is not None:
            out.append(steps[i]['practice'])
    return out


def _local(r, loc):
    t = dt.datetime.fromisoformat(r['datetime'].replace('Z', '+00:00'))
    return (t + dt.timedelta(hours=offset_hours(loc, t))).replace(tzinfo=None)


def in_hours(flow, r, loc):
    """True when a row falls in the flow's hours: dawn before its backup close,
    dusk from when it opens. Without a clock (`loc`) or a time, the day is enough."""
    if loc is None or not r.get('datetime'):
        return True
    t = _local(r, loc).time()
    return t < _hhmm(FLOWS['backup_close']['dawn']) if flow == 'dawn' else t >= _hhmm(FLOWS['dusk_opens_after'])


def same_kind(day_rows, loc=None):
    """[(row, step)] — rows of the same kind as a flow step, inside that flow's
    hours, which show the step done (facts flows.same_kind, 21 Nov 2026: a 📗
    book row that morning is the 📗 morning book step)."""
    out = []
    for flow, kinds in FLOWS.get('same_kind', {}).items():
        for step_, practices in kinds.items():
            want = {norm(p) for p in practices}
            out += [(r, step_) for r in day_rows
                    if norm(r.get('practice')) in want and in_hours(flow, r, loc)]
    return out


def logged(day_rows, loc=None):
    """Every practice the day already carries, in any status — a ⨂ skipped
    step is captured, not remaining. A row of the same kind counts as its step
    (facts flows.same_kind), one of an either-or pair closes the other
    (facts flows.either_or), and a step another covers is done with it
    (facts flows.covers)."""
    closes = {norm(c) for c in FLOWS['close'].values()}
    have = {norm(r.get('practice')) for r in day_rows if r.get('practice')
            and not (norm(r.get('practice')) in closes and is_open_status(r))}
    have |= {norm(s) for _, s in same_kind(day_rows, loc)}
    for by, covered in FLOWS.get('covers', {}).items():   # the gate covers the weather (20 Nov 2026)
        if norm(by) in have:
            have |= {norm(p) for p in covered}
    for pair in FLOWS.get('either_or', []):
        if have & {norm(p) for p in pair}:
            have |= {norm(p) for p in pair}
    return have


OPEN = ('▶️ in motion', '⬜ intention')


def is_open_status(r):
    """A close row still open (24 Nov 2026): the dusk Code run writes the dusk
    close row ▶️ with its markers before she sleeps, and the 🪐 morning ring read closes it
    at the ring's bedtime. Until then it does not close the flow."""
    return norm(r.get('status')) in {norm(o) for o in OPEN}


def together(flow):
    """{group name: [member practices]} — steps taken at once, one step on the
    line (facts flows.together, 24 Nov 2026: 💊 evening pills)."""
    return FLOWS.get('together', {}).get(flow, {})


def from_pattern(flow):
    """The steps nobody asks for: written next morning from her pattern
    (facts flows.from_pattern, 24 Nov 2026: breaths and the blessing, after the
    phone is down)."""
    return {norm(p) for p in FLOWS.get('from_pattern', {}).get(flow, [])}


def collapse(names, flow):
    """Each group's members, where any is still left, become the group's name
    once, at the first member's place."""
    out, seen = [], set()
    for p in names:
        g = next((g for g, ms in together(flow).items() if norm(p) in {norm(m) for m in ms}), None)
        if g is None:
            out.append(p)
        elif g not in seen:
            seen.add(g)
            out.append(g)
    return out


def counted(steps, have, flow):
    """(done, total) with a group counted as one step, done once all its members
    are, and a pattern step counted only once it is logged."""
    pat = from_pattern(flow)
    names = [s['practice'] for s in steps if norm(s['practice']) not in pat or norm(s['practice']) in have]
    groups = {g: {norm(m) for m in ms} for g, ms in together(flow).items()}
    done = total = 0
    seen = set()
    for p in names:
        g = next((g for g, ms in groups.items() if norm(p) in ms), None)
        if g is None:
            total += 1
            done += norm(p) in have
        elif g not in seen:
            seen.add(g)
            members = [n for n in names if norm(n) in groups[g]]
            total += 1
            done += all(norm(n) in have for n in members)
    return done, total


def sun_by(day_rows, rise, loc):
    """Minutes after midnight, local, by which 🔅 morning sun is due: an hour
    after sunrise or waking, whichever is later (8 Oct 2026). None without
    today's 😶 wake row or a sunrise."""
    wakes = [r['datetime'] for r in day_rows if norm(r.get('practice')) == norm(FLOWS['wake']) and r.get('datetime')]
    if not (rise and wakes):
        return None
    t = dt.datetime.fromisoformat(min(wakes).replace('Z', '+00:00'))
    w = t + dt.timedelta(hours=offset_hours(loc, t))
    return max(rise[1], w.hour * 60 + w.minute) + FLOWS['sun_by_minutes']


def cloudy(day_rows):
    """True when today's 🌦️ weather check says the sky is cloudy (28 Oct 2026)."""
    words = FACTS['cloudy']['words']
    return any(norm(r.get('practice')) == norm('🌦️ weather check') and
               any(w in (r.get('details') or '').lower() for w in words) for r in day_rows)


def drop_passed_sun(steps, due, now_local):
    """Once the sun-by time has passed, 🔅 morning sun leaves the list: there is
    nothing left she can do about it, and naming it is only noise (her words,
    11 Nov 2026: the mirror light thing is just annoying … there's no point at
    all to showing me this). The dusk audit still sees a day without it."""
    if due is None or now_local is None or now_local.hour * 60 + now_local.minute <= due:
        return steps
    sun = {norm(p) for p in FLOWS['after_sunrise']}
    return [s for s in steps if norm(s['practice']) not in sun]


def clock12(minutes):
    h, m = divmod(int(minutes) % 1440, 60)
    return f'{h % 12 or 12}:{m:02d}'


def sunset(day, lat, lon, local=None):
    """Local minutes after midnight of the day's sunset at (lat, lon), by NOAA's
    solar formula; the offset is her time zone's on that evening. None at the poles."""
    import math
    n = day.timetuple().tm_yday
    g = 2 * math.pi / 365 * (n - 1)
    eq = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                   - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g) - 0.006758 * math.cos(2 * g)
            + 0.000907 * math.sin(2 * g) - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    la = math.radians(lat)
    x = math.cos(math.radians(90.833)) / (math.cos(la) * math.cos(decl)) - math.tan(la) * math.tan(decl)
    if not -1 <= x <= 1:
        return None
    utc = 720 - 4 * (lon - math.degrees(math.acos(x))) - eq
    at = dt.datetime.combine(day, dt.time(18), dt.timezone.utc)
    off = offset_hours(local, at) if local is not None else -6
    return int(round(utc + off * 60)) % 1440


def dusk_opens(day, day_rows, local=None):
    """Local minutes after midnight when dusk opens (her yes, 24 Nov 2026: at
    sunset): sunset at her home from the settings row (`home`: lat, lon), or
    dusk_opens_after without one; earlier the moment 🔅 evening sun is logged."""
    h = (local or {}).get('home') or {}
    at = None
    if FLOWS.get('dusk_opens_at_sunset') and h.get('lat') is not None and h.get('lon') is not None:
        at = sunset(day, h['lat'], h['lon'], local)
    if at is None:
        t = _hhmm(FLOWS['dusk_opens_after'])
        at = t.hour * 60 + t.minute
    sun = norm('🔅 evening sun')
    for r in day_rows:
        if norm(r.get('practice')) == sun and r.get('datetime') and local is not None:
            t = _local(r, local)
            at = min(at, t.hour * 60 + t.minute)
    return at


def open_flow(now_local, day_rows, local=None):
    """dawn until its close is logged or noon passes (A126); dusk from sunset
    (dusk_opens) until its close is logged; otherwise none."""
    have = logged(day_rows)
    t = now_local.time()
    if t < _hhmm(FLOWS['backup_close']['dawn']) and norm(FLOWS['close']['dawn']) not in have:
        return 'dawn'
    if t.hour * 60 + t.minute >= dusk_opens(now_local.date(), day_rows, local) and norm(FLOWS['close']['dusk']) not in have:
        return 'dusk'
    return None


def split(steps, day_rows, flow, loc=None):
    """(done count, total, core remaining, other remaining) — each a list of
    catalog names in predicted order. An ask-if-missing step (facts
    flows.ask_if_missing: 🚽 bm, 20 Nov 2026) stays off the line until only the
    close is left, then is named just before it."""
    have = logged(day_rows, loc)
    pat = from_pattern(flow)
    left = collapse([s['practice'] for s in steps if norm(s['practice']) not in have | pat], flow)
    quiet = {norm(p) for p in FLOWS.get('ask_if_missing', {}).get(flow, [])}
    close = norm(FLOWS['close'][flow])
    if any(norm(p) not in quiet | {close} for p in left):          # asked only once all else is done
        left = [p for p in left if norm(p) not in quiet]
    else:
        asked = [p for p in left if norm(p) in quiet]
        left = asked + [p for p in left if norm(p) not in quiet]
    done, total = counted(steps, have, flow)
    core = FLOWS['core'].get(flow)
    if core is None:
        return done, total, left, []
    want = {norm(c) for c in core} | {norm(p) for p in leads(flow, steps)}
    want |= {norm(g) for g, ms in together(flow).items() if want & {norm(m) for m in ms}}
    return (done, total,
            [p for p in left if norm(p) in want or norm(p) in quiet],
            [p for p in left if norm(p) not in want and norm(p) not in quiet])


def holds_open(steps, day_rows, flow, loc=None):
    """What still keeps the flow from closing itself: required steps only —
    never an optional one, never one collapsed off the core (A228), never the
    close itself."""
    have = logged(day_rows, loc)
    core = FLOWS['core'].get(flow)
    want = {norm(c) for c in core} if core is not None else None
    close = norm(FLOWS['close'][flow])
    pat = from_pattern(flow)
    return [s['practice'] for s in steps
            if norm(s['practice']) not in have | pat and norm(s['practice']) != close
            and s.get('group') not in FLOWS['never_held_open']
            and (want is None or norm(s['practice']) in want)]


def render(flow, steps, day_rows, due=None, light=None, loc=None):
    """ONE line in a code box: the flow's glyph, n of N, the core still to do
    by name, then also: and the other steps as their glyphs. `due` is the
    sun-by time (minutes after midnight), named on 🔅 morning sun; `light` is
    her bright light on a cloudy morning, named in its place."""
    done, total, core, rest = split(steps, day_rows, flow, loc)
    glyph = FLOWS['phase'][flow].split(' ')[0]
    if not core and not rest:
        return f'```\n{glyph} all {total} done\n```'
    sun = {norm(p) for p in FLOWS['after_sunrise']}

    def by(p, text):
        if norm(p) not in sun:
            return text
        if light:
            text = f'{p.split(" ")[0]} {light}'
        return f'{text} by {clock12(due)}' if due is not None else text
    parts = [f'{glyph} {done} of {total}'] + [by(p, p) for p in core]
    if rest:
        parts.append('also: ' + ' '.join(by(p, p.split(' ')[0]) for p in rest))
    return '```\n' + ' · '.join(parts) + '\n```'


def ampm(t):
    """10:26 AM — a wall-clock time as the close line prints it."""
    return f'{t.hour % 12 or 12}:{t.minute:02d} {"AM" if t.hour < 12 else "PM"}'


def last_step(steps, day_rows, flow, loc):
    """(catalog name, local time) of the flow's latest logged step — its own
    row or one of the same kind — or None. The close is written at this time."""
    names = {norm(s['practice']): s['practice'] for s in steps}
    names.pop(norm(FLOWS['close'][flow]), None)
    hits = [(r, names[norm(r.get('practice'))]) for r in day_rows if norm(r.get('practice')) in names]
    hits += [(r, s) for r, s in same_kind(day_rows, loc) if norm(s) in names]
    hits = [(r, s) for r, s in hits if r.get('datetime')]
    if not hits:
        return None
    r, s = max(hits, key=lambda h: h[0]['datetime'])
    return s, _local(r, loc if loc is not None else 0)


def close_line(flow, steps, day_rows, day=None, now_local=None, loc=None):
    """The flow closes itself (21 Nov 2026): once nothing required is left, the
    line that says to write the close now, at the last step's time, without
    asking her; past the backup hour on the day itself, the line that says to
    write the backup close, naming what it couldn't capture, without waiting
    for a reply. None while the flow still runs, or once its close is logged."""
    close = FLOWS['close'][flow]
    if norm(close) in logged(day_rows, loc):
        return None
    say = FLOWS['closes_itself']
    glyph = FLOWS['phase'][flow].split(' ')[0]
    if flow in FLOWS.get('close_at_sleep', []):      # her words, 24 Nov 2026: the evening closes when I fall asleep
        if holds_open(steps, day_rows, flow, loc):
            return None
        return say['at_sleep'].format(glyph=glyph, flow=flow, close=close,
                                      pattern=' and '.join(FLOWS.get('from_pattern', {}).get(flow, [])) or 'nothing else')
    if not holds_open(steps, day_rows, flow, loc):
        last = last_step(steps, day_rows, flow, loc)
        if last:
            return say['line'].format(glyph=glyph, flow=flow, step=last[0], time=ampm(last[1]), close=close)
    if day is None or now_local is None:
        return None
    now = now_local.replace(tzinfo=None)
    backup = dt.datetime.combine(day, _hhmm(FLOWS['backup_close'][flow]))
    if now.date() != day or now < backup:
        return None
    _, _, core, rest = split(steps, day_rows, flow, loc)
    missed = [p for p in core + rest if norm(p) != norm(close)]
    return say['backup'].format(glyph=glyph, backup=ampm(backup), close=close,
                                missed=f', naming what it couldn\'t capture: {" · ".join(missed)}' if missed else '')


def week_turn(day, day_rows):
    """Sunday's turn to the week (1 Nov 2026, her words: after I get through my dawn flow, you're kind of
    pushing, like, hey, you ready to do the transition to the next week?). Once the dawn flow is closed on
    a Sunday and no my week chat has a row yet, the line to say; else None."""
    if day.weekday() != 6:
        return None
    close = norm(FLOWS['close']['dawn'])
    closed = [r for r in day_rows if norm(r.get('practice')) == close]
    if not closed:
        return None
    t0 = min(r.get('datetime') or '' for r in closed)
    week = (FACTS.get('week_turn') or {}).get('window', 'my week')
    if any(week in (r.get('title') or '').lower() and (r.get('datetime') or '') >= t0 for r in day_rows):
        return None
    return (FACTS.get('week_turn') or {}).get('line') or \
        'next: ready for the transition to the next week? say yes and I\'ll open the my week chat'


def spoken(flow, steps, day_rows, loc=None):
    """The one spoken line on voice — names only."""
    done, total, core, rest = split(steps, day_rows, flow, loc)
    left = core + rest
    name = flow
    if not left:
        return f'{name}: all {total} done.'
    return f'{name}: {len(left)} left, next is {left[0]}.'


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the remaining list for the open flow')
    ap.add_argument('--live', action='store_true', help='read the catalog and today from Airtable')
    ap.add_argument('--catalog'); ap.add_argument('--day', help='a complete read of the day\'s rows')
    ap.add_argument('--flow', choices=['dawn', 'dusk'])
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--voice', action='store_true')
    ap.add_argument('--widget', action='store_true', help='retired: the list is the code line, never a widget')
    ap.add_argument('--next', action='append', default=[], help='what she says she is doing next; goes first')
    a = ap.parse_args(argv)
    L = load_local()
    now = dt.datetime.now(dt.timezone.utc)
    now_local = now + dt.timedelta(hours=offset_hours(L, now))
    day = dt.date.fromisoformat(a.date) if a.date else now_local.date()
    fields = {**{k: k for k in ('practice', 'status', 'datetime', 'details')}, **L.get('stream_fields', {})}
    if a.live:
        from bedo_air import Air, SLOW, read_day, read_catalog
        air = Air()
        cat_src, (day_src, _) = read_catalog(air, L), read_day(air, L, day)
    else:
        if not (a.catalog and a.day):
            sys.exit('give --live, or both --catalog and --day')
        cat_src, day_src = a.catalog, a.day
    cat = catalog(cat_src, L.get('practices_fields'))
    every = as_rows(complete(day_src, 'day'), fields)
    rows = on_day(every, day, L)
    flow = a.flow or open_flow(now_local, rows, L)
    turn = week_turn(day, rows)
    dawn_left = None                                 # the dawn flow, still open past its backup hour
    if flow != 'dawn' and norm(FLOWS['close']['dawn']) not in logged(rows, L):
        dawn_left = close_line('dawn', flow_steps(cat, 'dawn'), rows, day, now_local, L)
    if not flow:
        print(dawn_left or (f'```\n{turn}\n```' if turn else 'no flow open'))
        return
    if dawn_left:
        print(dawn_left)
    gate, due, light = {}, None, None
    if flow == 'dawn':
        rise = sunrise(every, L)
        if not rise and a.live:                      # the weather check often comes after the sun
            for back in (1, 2, 3):
                prev = as_rows(complete(read_day(air, L, day - dt.timedelta(days=back), ttl=SLOW)[0], 'day'), fields)
                rise = sunrise(prev, L)
                if rise:
                    break
        gate, due = sun_gate(rows, rise, L), sun_by(rows, rise, L)
        if cloudy(rows):
            light = L.get('cloudy_light') or FACTS['cloudy']['light']
    steps = flow_steps(cat, flow, a.next, gate)
    steps = drop_passed_sun(steps, due, now_local if not a.date else None)
    print(spoken(flow, steps, rows, L) if a.voice else render(flow, steps, rows, due, light, L))
    shut = close_line(flow, steps, rows, day, now_local, L)
    if shut:
        print(shut)
    if turn and flow == 'dawn':
        print(turn)


if __name__ == '__main__':
    main()
