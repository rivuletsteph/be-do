# -*- coding: utf-8 -*-
"""Where she was: the day's map, from the stream and the places base (5 Nov 2026).

Her word on the map card, 3–5 Nov 2026: where she went, not what she did; no
routes; a dot's size is the time she spent there (the September map's sizes); a
place she has never been before is a star; colours bright enough to read against
the grey map; a tap gives the place, its time, what she did there and who with.
And the location belongs on the stream, integrated, with the coordinates kept in
the location table: so the dots come from the day's `📍 location` rows, each
naming its row in the places base (`place: rec…`), and the coordinates from that
row (`coordinates`, "lat, lng"). Home has no rows; it is drawn underneath, pale,
with no time, when the places base holds it.

An artifact page can't load outside images, so the map's tiles are carried in
the page: the grey CARTO base at the zoom that fits the day and two closer, and
two closer still around each place. CARTO asks for a key (`carto_key` in the
settings, or BEDO_CARTO_KEY); without a key or the network the map draws its
dots on plain ground and says so.

Nothing personal lives here: names and coordinates arrive in the data.
"""
import base64, math, re, urllib.request

import bedo_places as P
import bedo_clock  # the one clock: `off` is the settings, an Offset or a fixed number

TILE = 'https://a.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png?key={key}'   # the key is hers, from the settings, never here
ATTRIB = '© OpenStreetMap contributors © CARTO'
COLOURS = ['#2F6FB5', '#E8691B', '#D93A3A', '#3E9142', '#0B9CA3', '#8A4FBF', '#E8A600', '#DB5C8E']
OTHER = '#6F6A68'
MAX_TILES = 220


def _tile_xy(lat, lng, z):
    n = 2 ** z
    x = (lng + 180) / 360 * n
    y = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    return x, y


def fit_zoom(pts, w=330, h=330, lo=8, hi=15):
    """The closest zoom at which every point fits the card at phone width."""
    for z in range(hi, lo - 1, -1):
        xy = [_tile_xy(a, b, z) for a, b in pts]
        if (max(x for x, _ in xy) - min(x for x, _ in xy)) * 256 <= w * .8 and \
           (max(y for _, y in xy) - min(y for _, y in xy)) * 256 <= h * .8:
            return z
    return lo


def tiles_needed(pts, z0):
    """(z, x, y) for the base: the whole spread at z0..z0+2, then each place's
    neighbourhood two zooms closer, nearest first, up to MAX_TILES."""
    want = []
    for z in range(z0, z0 + 3):
        xy = [_tile_xy(a, b, z) for a, b in pts]
        x0, x1 = int(min(x for x, _ in xy)) - 1, int(max(x for x, _ in xy)) + 1
        y0, y1 = int(min(y for _, y in xy)) - 1, int(max(y for _, y in xy)) + 1
        want += [(z, x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)]
    for z in range(z0 + 3, min(z0 + 5, 18)):
        for a, b in pts:
            tx, ty = map(int, _tile_xy(a, b, z))
            want += [(z, x, y) for x in range(tx - 1, tx + 2) for y in range(ty - 1, ty + 2)]
    return list(dict.fromkeys(want))[:MAX_TILES]


def fetch_tiles(keys, key, get=None, timeout=12):
    """{"z/x/y": data URI} for every tile that came back; {} when none did."""
    def _get(url):
        req = urllib.request.Request(url, headers={'User-Agent': 'bedo-day-map/1.0'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    get = get or _get
    out = {}
    for z, x, y in keys:
        try:
            out[f'{z}/{x}/{y}'] = 'data:image/png;base64,' + base64.b64encode(get(TILE.format(z=z, x=x, y=y, key=key))).decode()
        except Exception:
            if not out:          # the first one failed: no network here, don't wait on the rest
                return {}
    return out


def _local(ts, off):
    import datetime as dt
    return bedo_clock.to_local(off, ts) if ts else None


def build(stays, places, rows, day, off, home_names=('home',), not_lived=(), tiles=True, get=None, key=None):
    """DATA.map for the day page, or None when no stay has coordinates."""
    by_id = {p['id']: p for p in places}
    homes = {h.casefold() for h in home_names}
    dots = {}
    for s in stays:
        if s.get('status') in not_lived:
            continue
        p = by_id.get(s.get('place_ref') or '')
        at = P.coords(p) if p else None
        if not at:
            continue
        a, b = _local(s.get('when') or s.get('datetime'), off), _local(s.get('end'), off)
        mins = max(0, (b - a).total_seconds() / 60) if a and b else 0
        d = dots.setdefault(p['id'], dict(name=p.get('place') or '', lat=at[0], lng=at[1], minutes=0, kind=p.get('serves') or '',
                                          new=(p.get('added') or '') == day.isoformat(), who=[], did=[], at=[]))
        d['minutes'] += mins
        if a and b:
            d['at'].append(f'{a:%H:%M}–{b:%H:%M}')
        for w in re.split(r'\s*,\s*', s.get('person') or ''):
            if w and w not in d['who']:
                d['who'].append(w)
        for r in rows:          # what she did there: her rows inside the stay, never another place or a drive
            t = _local(r.get('when') or r.get('datetime'), off)
            if not (a and b and t and a <= t < b) or P.is_place(r) or r.get('status') in not_lived:
                continue
            if P.word(r.get('practice')) in ('driving', 'travel'):
                continue
            title = re.sub(r'^[^\w]+', '', r.get('title') or '').strip()
            if title and title not in d['did'] and len(d['did']) < 3:
                d['did'].append(title)
    if not dots:
        return None
    home = next((p for p in places if (p.get('place') or '').strip().casefold() in homes and P.coords(p)), None)
    kinds = list(dict.fromkeys(d['kind'] for d in sorted(dots.values(), key=lambda d: -d['minutes']) if d['kind']))
    colour = {k: COLOURS[i % len(COLOURS)] for i, k in enumerate(kinds)}
    out = []
    for d in sorted(dots.values(), key=lambda d: -d['minutes']):
        out.append(dict(name=d['name'], lat=d['lat'], lng=d['lng'], hours=round(d['minutes'] / 60, 2), new=d['new'],
                        colour=colour.get(d['kind'], OTHER), kind=d['kind'] or 'other',
                        who=', '.join(d['who']), did=' · '.join(d['did']), at=', '.join(d['at'])))
    pts = [(d['lat'], d['lng']) for d in out] + ([P.coords(home)] if home else [])
    z0 = fit_zoom(pts)
    got = fetch_tiles(tiles_needed(pts, z0), key, get) if tiles and key else {}
    return dict(places=out, home=dict(lat=P.coords(home)[0], lng=P.coords(home)[1]) if home else None,
                legend=[dict(kind=k, colour=colour[k]) for k in kinds] + ([dict(kind='other', colour=OTHER)]
                                                                          if any(not d['kind'] for d in dots.values()) else []),
                tiles=got, zoom=[z0, min(z0 + 4, 18)], attribution=ATTRIB if got else '')
