# -*- coding: utf-8 -*-
"""Where she was: the day's 📍 stays, written at the dusk map check (5 Nov 2026).

Her words: what I want is the location to be on the stream, integrated; I'd
like to keep the coordinates in the location table; it will give the system it
needs to help me better plan my day ahead.

The shape she said yes to (backlog 261104_where):

  · one `📍 location` row per stay: ● log, datetime = arrived, end = left,
    person = who she was with, her words above the divider, and
    `place: rec…` in the `[be•do]` block naming its row in the places base
  · no rows for home: time not inside a stay is home
  · coordinates live only in the places base (`coordinates`, "lat, lng"),
    matched by `google place id`, whole, never by a prefix: neighbours share one
  · a place enters the places base only with her yes. A stay at a place the
    base doesn't hold is still written (it is where she was), marked
    `place: new`, and the place is put to her as one line

The chat reads her Timeline screenshot and writes what it shows as a stays file:

    {"day": "YYYY-MM-DD", "from": "her Timeline screenshot at 10:07 PM",
     "stays": [{"place": "the office", "arrive": "10:27", "leave": "15:30",
                "google_place_id": "", "who": "", "words": ""}]}

`arrive` and `leave` are her own clock on that day ("+00:30" past midnight).
This turns it into rows ready for the entry check, the new places to ask about,
and the stays already on the stream, so a second run writes nothing twice.

    python3 bedo_places.py --stays stays.json --places places.json --day day.json [--json]
    python3 bedo_places.py --stays stays.json --live [--json]

The day's map reads the same rows back: `stays_of(rows)` and `coords(places)`.
"""
import datetime as dt, json, re, sys

from bedo_reader import FACTS, as_rows, cells, complete, load_local, offset_hours, on_day, sv

PLACE = FACTS['practice']['location']
LOG = FACTS['status']['ad_hoc']
DIVIDER = FACTS['divider']
REF = re.compile(r'\bplace:\s*(rec[A-Za-z0-9]{14}|new)\b')
FIELDS = {'place': 'place', 'standing': 'standing', 'where': 'where', 'serves': 'serves', 'added': 'added',
          'google_place_id': 'google place id', 'coordinates': 'coordinates'}


def word(p):
    """A practice without its glyph: '📍 location' → 'location'."""
    return re.sub(r'^[^\w]+', '', p or '').strip().lower()


def is_place(row):
    return word(row.get('practice')) == word(PLACE)


def places_from(recs, L=None):
    """The places base, by logical name. Its fields are read by name or by id
    (`places_fields` in the settings maps a name to an id)."""
    names = {**FIELDS, **((L or {}).get('places_fields') or ((L or {}).get('fields') or {}).get('places') or {})}
    out = []
    for r in recs:
        c = cells(r)
        p = {k: sv(c.get(v, c.get(FIELDS[k]))) for k, v in names.items()}
        p['id'] = r['id']
        out.append(p)
    return out


def coords(p):
    """(lat, lng) from the base's "lat, lng", or None."""
    m = re.match(r'\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$', p.get('coordinates') or '')
    return (float(m.group(1)), float(m.group(2))) if m else None


def match(stay, places):
    """Its row in the places base: the whole Google id first, then her name for it."""
    gid = (stay.get('google_place_id') or '').strip()
    if gid:
        hit = next((p for p in places if (p.get('google_place_id') or '').strip() == gid), None)
        if hit:
            return hit
    name = (stay.get('place') or '').strip().casefold()
    return next((p for p in places if (p.get('place') or '').strip().casefold() == name), None) if name else None


def is_home(stay, L=None):
    homes = {h.casefold() for h in ((L or {}).get('home_names') or ['home'])}
    return (stay.get('place') or '').strip().casefold() in homes


def _at(day, hm, off):
    """Her clock on the day → UTC ISO. '+HH:MM' is past midnight."""
    nxt = hm.startswith('+')
    h, m = map(int, hm.lstrip('+').split(':'))
    t = dt.datetime.combine(day + dt.timedelta(days=1 if nxt else 0), dt.time(h, m)) - dt.timedelta(hours=off)
    return t.strftime('%Y-%m-%dT%H:%M:00.000Z')


def ref(row):
    m = REF.search(row.get('details') or '')
    return m.group(1) if m else None


def _overlap(a1, b1, a2, b2):
    return a1 < b2 and a2 < b1


def stays_of(rows):
    """The 📍 rows of a day, each with the place it names."""
    return [dict(r, place_ref=ref(r)) for r in rows if is_place(r)]


def propose(stays, places, day_rows, day, off, source='', L=None):
    """Rows to write, places to ask about, stays already written, homes left out."""
    on = stays_of(day_rows)
    out = dict(write=[], ask=[], already=[], home=[])
    for s in stays:
        if is_home(s, L):
            out['home'].append(s.get('place'))
            continue
        a, b = _at(day, s['arrive'], off), _at(day, s['leave'], off)
        if b <= a:
            sys.exit(f"bedo_places: {s.get('place')} leaves ({s['leave']}) before it arrives ({s['arrive']})")
        hit = match(s, places)
        name = (hit or {}).get('place') or s['place']
        title = f'{PLACE.split()[0]} {name}'
        dup = next((r for r in on if _overlap(a, b, r.get('datetime') or '', r.get('end') or r.get('datetime') or '')
                    and ((hit and r['place_ref'] == hit['id']) or (r.get('title') or '').strip() == title)), None)
        if dup:
            out['already'].append(dict(title=title, id=dup.get('id')))
            continue
        note = [f"place: {hit['id'] if hit else 'new'}"]
        if not hit:
            note.append('not in the places base yet: written as where she was, the place itself waits on her yes')
        elif not coords(hit):
            note.append('its row in the places base has no coordinates yet')
        if source:
            note.append(f'from {source}')
        words = (s.get('words') or '').strip()
        out['write'].append(dict(
            title=title, practice=PLACE, status=LOG, datetime=a, end=b,
            person=(s.get('who') or '').strip() or None,
            details=(words + '\n' if words else '') + DIVIDER + '\n[be•do] ' + ' · '.join(note)))
        if not hit and not any(x['place'] == s['place'] for x in out['ask']):
            out['ask'].append(dict(place=s['place'], google_place_id=(s.get('google_place_id') or '').strip() or None,
                                   line=f"New place today: {s['place']} ({s['arrive']}–{s['leave']}). Add it to your places?"))
    return out


def render(p, head):
    lines = [head]
    for r in p['write']:
        a, b = r['datetime'][11:16], r['end'][11:16]
        lines.append(f"  write  {r['title']}  {a}–{b} UTC" + (f"  with {r['person']}" if r.get('person') else ''))
    lines += [f"  have   {x['title']} (already on the stream)" for x in p['already']]
    lines += [f'  home   {h}: no row, time not in a stay is home' for h in p['home']]
    lines += [f"  ask    {x['line']}" for x in p['ask']]
    if len(lines) == 1:
        lines.append('  nothing to write')
    return '\n'.join(lines)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description="the day's 📍 stays, from her Timeline screenshot")
    ap.add_argument('--stays', required=True, help='what the screenshot shows, as a stays file')
    ap.add_argument('--places', help='a complete read of the places base')
    ap.add_argument('--day', help="a complete read of the day's rows")
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    S = json.load(open(a.stays, encoding='utf-8'))
    day = dt.date.fromisoformat(S['day'])
    off = offset_hours(L, dt.datetime.combine(day, dt.time(12), dt.timezone.utc))
    names = ('datetime', 'end', 'status', 'title', 'details', 'practice', 'person')
    fields = {**{k: k for k in names}, **{k: v for k, v in L.get('stream_fields', {}).items() if k in names}}
    if a.live:
        from bedo_air import Air, read_day
        air = Air()
        day_src, _ = read_day(air, L, day, air.bases())
        base, table = (L.get('bases') or {}).get('places') or (None, None)
        if not base:
            sys.exit('bedo_places: no places base in the settings (bases.places)')
        places_src = air.dump(base, table)
    elif a.places and a.day:
        day_src, places_src = a.day, a.places
    else:
        sys.exit('give --live, or --places and --day')
    rows = on_day(as_rows(complete(day_src, 'day'), fields), day, L)
    places = places_from(complete(places_src, 'places'), L)
    p = propose(S.get('stays') or [], places, rows, day, off, S.get('from') or '', L)
    print(json.dumps(p, ensure_ascii=False, indent=1) if a.json else render(p, f'places · {day:%a %d %b}'))


if __name__ == '__main__':
    main()
