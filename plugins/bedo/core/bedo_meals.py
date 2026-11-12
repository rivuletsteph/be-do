# -*- coding: utf-8 -*-
"""Meals: the minutes be•do places so she doesn't have to log them (7 Oct 2026,
the meals amendment).

Her words: *I want you to make an educated guess … I don't want to have to be
logging every second in order to get a fairly accurate picture … you could also
just tell me what you're putting in the record and ask if that's accurate.*

A meal is usually logged as a moment — a photo, a line — with no end and no
cooking row, so the day behind counted it as nothing. This reads the day's meal
rows and proposes, for each:

  · the eating, when the row has no end: the meal's usual minutes from facts
  · the prep, when no prep row sits before it, by what the meal reads as:
      out              ordering and picking it up, 20 min
      simple           a sandwich-type meal she made, 15 min
      straightforward  a really straightforward dinner, 30 min
      cooked           a dinner she cooked, 45 min (most take 45 to 60)

An educated guess, not a rule. Every proposal is written ESTIMATED FROM
CONTEXT with its reason, and the chat shows her the list — what went in the
record — so she can say if it's accurate. A snack gets no prep. A meal eaten AT
a restaurant is its time there, which Timeline holds and the rows don't: the
proposal says so rather than guessing.

    python3 bedo_meals.py --day day.json [--date YYYY-MM-DD] [--json]
    python3 bedo_meals.py --live [--date YYYY-MM-DD]
"""
import datetime as dt, json, re, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, on_day
from bedo_entry import utc

M = FACTS['meals']
PLANS = set(FACTS['status']['plans'])
DIVIDER = FACTS['divider']


def word(practice):
    """The practice without its glyph: '🍴 dinner' → 'dinner'."""
    return re.sub(r'^[^\w]+', '', (practice or '').strip()).lower()


def kind_of(row):
    w = word(row.get('practice'))
    return w if w in M['meal_words'] else None


def is_prep(row):
    return word(row.get('practice')) in M['prep_words']


def prep_class(row, people=()):
    """What the meal reads as, from its title and her words. `people` are names
    whose possessive is a person, not a place ("Ana's lunch")."""
    title = row.get('title') or ''
    text = (title + ' ' + (row.get('details') or '').split(DIVIDER, 1)[0]).lower()
    if any(w in text for w in M['out_words']):
        return 'out'
    # a place named in the possessive — "McAlister's veggie sandwich" — is a
    # business, unless it is one of her people. Family ("Mom's cornbread") made
    # it themselves: no prep of hers to place
    for m in re.finditer(r"\b([A-Z][\w&]*)['’]s\b", title):
        if m.group(1).lower() in M.get('family_words', []):
            return 'theirs'
        if not any(m.group(1).lower() in (p or '').lower() for p in people):
            return 'out'
    k = kind_of(row)
    if any(w in text for w in M['simple_words']):
        return 'simple'
    if k == 'dinner':
        return 'straightforward' if any(w in text for w in M['straightforward_words']) else 'cooked'
    return 'simple'


def _local(t, off):
    t = t + dt.timedelta(hours=off)
    return f'{t.hour % 12 or 12}:{t:%M}'


def propose(rows, off, people=()):
    """One proposal per meal of hers that is missing minutes. Returns a list of
    {meal, id, eat, prep, line} where eat and prep are rows to write (logical
    names) or None, and line is what she is shown."""
    mine = [r for r in rows if r.get('datetime') and r.get('status') not in PLANS]
    preps = [r for r in mine if is_prep(r)]
    win = dt.timedelta(minutes=M['prep_window_minutes'])
    out = []
    for r in sorted(mine, key=lambda r: r['datetime']):
        k = kind_of(r)
        if not k:
            continue
        s = utc(r['datetime'])
        eat = prep = None
        notes = []
        if not r.get('end') and not r.get('time_spent'):
            e = s + dt.timedelta(minutes=M['eat_minutes'][k])
            eat = {'id': r['id'], 'end': e.strftime('%Y-%m-%dT%H:%M:00.000Z'),
                   'why': f'{M["eat_minutes"][k]} minutes eating, the usual for {k}'}
            notes.append(f'ate {_local(s, off)}–{_local(e, off)}')
        has_prep = any(s - win <= utc(p['datetime']) <= s for p in preps)
        # a second sitting of the same meal (half the sandwich saved for later) was
        # already made: it gets its eating, not another prep
        again = any(kind_of(o) == k and o is not r and s - win <= utc(o['datetime']) < s for o in mine)
        c = prep_class(r, people) if k != 'snack' and not has_prep and not again else None
        if c == 'theirs':
            notes.append('made by them — no prep of yours')
        elif c:
            n = M['prep_minutes'][c]
            ps = s - dt.timedelta(minutes=n)
            why = M['prep_why'][c]
            prep = {'datetime': ps.strftime('%Y-%m-%dT%H:%M:00.000Z'),
                    'end': s.strftime('%Y-%m-%dT%H:%M:00.000Z'),
                    'status': FACTS['status']['logs'][1],
                    'practice': M['prep_practice'][k],
                    'title': f'{M["prep_practice"][k].split(" ", 1)[0]} '
                             + ('Ordered ' if c == 'out' else 'Made ')
                             + re.sub(r'^[^\w]+', '', r.get('title') or k),
                    'details': f'{DIVIDER}\n[be•do] ESTIMATED FROM CONTEXT: {n} minutes, {why}. '
                               f'Placed before the {k} row at {_local(s, off)}, from its title. '
                               'Hers to correct.',
                    'class': c}
            notes.insert(0, f'{"ordered" if c == "out" else "made it"} '
                            f'{_local(ps, off)}–{_local(s, off)} ({n} min, {why})')
            if c == 'out':
                notes.append('if you ate there, the time there is the meal — from Timeline')
        if eat or prep:
            out.append({'meal': r.get('title') or k, 'id': r['id'], 'eat': eat, 'prep': prep,
                        'line': f'{r.get("title") or k}: ' + ' · '.join(notes)})
    return out


def render(props, label):
    lines = [label]
    if not props:
        lines.append('every meal already carries its minutes')
        return '\n'.join(lines)
    lines.append("what goes in the record — tell me if it's not right:")
    lines += [f'  {i}. {p["line"]}' for i, p in enumerate(props, 1)]
    return '\n'.join(lines)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='place the minutes of the day\'s meals')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--day', help='a complete read of the day\'s rows')
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--json', action='store_true', help='the proposals, with rows ready for the entry check')
    a = ap.parse_args(argv)
    L = load_local()
    now = dt.datetime.now(dt.timezone.utc)
    off = offset_hours(L, now)
    day = dt.date.fromisoformat(a.date) if a.date else (now + dt.timedelta(hours=off)).date()
    names = ('datetime', 'end', 'time_spent', 'status', 'title', 'details', 'practice', 'person', 'photo')
    fields = {**{k: k for k in names}, **{k: v for k, v in L.get('stream_fields', {}).items() if k in names}}
    if a.live:
        from bedo_air import Air, read_day
        air = Air()
        src, _ = read_day(air, L, day, air.bases())
    elif a.day:
        src = a.day
    else:
        sys.exit('give --live, or --day')
    rows = on_day(as_rows(complete(src, 'day'), fields), day, L)
    off = offset_hours(L, dt.datetime.combine(day, dt.time(12), dt.timezone.utc))
    props = propose(rows, off, (L.get('people') or {}).values())
    if a.json:
        print(json.dumps(props, ensure_ascii=False, indent=1))
    else:
        print(render(props, f'meals · {day:%a %d %b}'))


if __name__ == '__main__':
    main()
