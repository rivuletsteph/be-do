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
  sun-by  🔅 morning sun by an hour after sunrise or waking, whichever is
        later: the line names that time while the sun is still to come (8 Oct)

Predicted order is the catalog's own `order` field, low first; a step with no
order goes last. Nothing personal lives here: the flow's practices come from
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
      5  the flow close, always last"""
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
    at = lambda name: next((i for i, r in enumerate(steps) if norm(r['practice']) == norm(name)), None)
    for _ in range(len(steps)):                   # a stated sequence moves the later step after the earlier
        moved = False
        for a, b in FLOWS.get('sequences', {}).get(flow, []):
            ia, ib = at(a), at(b)
            if ia is not None and ib is not None and ib < ia:
                steps.insert(ia, steps.pop(ib))
                moved = True
        if not moved:
            break
    for name in reversed([f for f in first if f]):
        i = at(name)
        if i is not None and norm(steps[i]['practice']) != close:
            steps.insert(0, steps.pop(i))
    return steps


def logged(day_rows):
    """Every practice the day already carries, in any status — a ⨂ skipped
    step is captured, not remaining. One of an either-or pair closes the other
    (facts flows.either_or)."""
    have = {norm(r.get('practice')) for r in day_rows if r.get('practice')}
    for pair in FLOWS.get('either_or', []):
        if have & {norm(p) for p in pair}:
            have |= {norm(p) for p in pair}
    return have


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


def clock12(minutes):
    h, m = divmod(int(minutes) % 1440, 60)
    return f'{h % 12 or 12}:{m:02d}'


def open_flow(now_local, day_rows):
    """dawn until its close is logged or noon passes (A126); dusk after 7 PM
    until its close is logged; otherwise none."""
    have = logged(day_rows)
    t = now_local.time()
    if t < _hhmm(FLOWS['backup_close']['dawn']) and norm(FLOWS['close']['dawn']) not in have:
        return 'dawn'
    if t >= _hhmm(FLOWS['dusk_opens_after']) and norm(FLOWS['close']['dusk']) not in have:
        return 'dusk'
    return None


def split(steps, day_rows, flow):
    """(done count, total, core remaining, other remaining) — each a list of
    catalog names in predicted order."""
    have = logged(day_rows)
    left = [s['practice'] for s in steps if norm(s['practice']) not in have]
    core = FLOWS['core'].get(flow)
    if core is None:
        return len(steps) - len(left), len(steps), left, []
    want = {norm(c) for c in core}
    return (len(steps) - len(left), len(steps),
            [p for p in left if norm(p) in want], [p for p in left if norm(p) not in want])


def holds_open(steps, day_rows, flow):
    """What still keeps the flow from closing itself: required steps only —
    never an optional one, never one collapsed off the core (A228), never the
    close itself."""
    have = logged(day_rows)
    core = FLOWS['core'].get(flow)
    want = {norm(c) for c in core} if core is not None else None
    close = norm(FLOWS['close'][flow])
    return [s['practice'] for s in steps
            if norm(s['practice']) not in have and norm(s['practice']) != close
            and s.get('group') not in FLOWS['never_held_open']
            and (want is None or norm(s['practice']) in want)]


def render(flow, steps, day_rows, due=None):
    """ONE line in a code box: the flow's glyph, n of N, the core still to do
    by name, then also: and the other steps as their glyphs. `due` is the
    sun-by time (minutes after midnight), named on 🔅 morning sun."""
    done, total, core, rest = split(steps, day_rows, flow)
    glyph = FLOWS['phase'][flow].split(' ')[0]
    if not core and not rest:
        return f'```\n{glyph} all {total} done\n```'
    sun = {norm(p) for p in FLOWS['after_sunrise']}

    def by(p, text):
        return f'{text} by {clock12(due)}' if due is not None and norm(p) in sun else text
    parts = [f'{glyph} {done} of {total}'] + [by(p, p) for p in core]
    if rest:
        parts.append('also: ' + ' '.join(by(p, p.split(' ')[0]) for p in rest))
    return '```\n' + ' · '.join(parts) + '\n```'


def spoken(flow, steps, day_rows):
    """The one spoken line on voice — names only."""
    done, total, core, rest = split(steps, day_rows, flow)
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
        from bedo_air import Air, read_day, read_catalog
        air = Air()
        cat_src, (day_src, _) = read_catalog(air, L), read_day(air, L, day)
    else:
        if not (a.catalog and a.day):
            sys.exit('give --live, or both --catalog and --day')
        cat_src, day_src = a.catalog, a.day
    cat = catalog(cat_src, L.get('practices_fields'))
    every = as_rows(complete(day_src, 'day'), fields)
    rows = on_day(every, day, L)
    flow = a.flow or open_flow(now_local, rows)
    if not flow:
        print('no flow open')
        return
    gate, due = {}, None
    if flow == 'dawn':
        rise = sunrise(every, L)
        if not rise and a.live:                      # the weather check often comes after the sun
            for back in (1, 2, 3):
                prev = as_rows(complete(read_day(air, L, day - dt.timedelta(days=back))[0], 'day'), fields)
                rise = sunrise(prev, L)
                if rise:
                    break
        gate, due = sun_gate(rows, rise, L), sun_by(rows, rise, L)
    steps = flow_steps(cat, flow, a.next, gate)
    print(spoken(flow, steps, rows) if a.voice else render(flow, steps, rows, due))


if __name__ == '__main__':
    main()
