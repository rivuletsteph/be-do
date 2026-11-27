# -*- coding: utf-8 -*-
"""Today's forecast for the Morning Gate, with its picture (24 Nov 2026).

Her words: I'd like to handle the weather check in the morning gate a bit more
elegantly, at least the forecast for today with an image.

The paper's weather band is drawn here, in code, so every edition shows it the
same way: today's sky as a drawn illustration, the high and low, the forecast in
the forecaster's own words, sunrise and sunset, and a chart of the day's hours
(temperature as a line, chance of rain as bars). Drawn inline as SVG in the
paper's own colours, so it follows light and dark and needs no outside image.

The forecast is the National Weather Service's (api.weather.gov: free, no key).
Where she is comes from the settings (`home`: lat, lon), or `--lat/--lon` for a
morning away; nothing about the place lives in this repo.

It also prints the 🌦️ weather check's details line, because the Morning Gate
covers that step (facts `covers`): sunrise first, so the remaining list can
place 🔅 morning sun, and the sky in words `cloudy()` reads.

    python3 forecast.py --out weather.html [--date YYYY-MM-DD] [--lat N --lon N] [--json]
    python3 forecast.py --fixture DIR --out weather.html     # points/forecast/hourly .json, no network

Exit 0 with the band written; exit 1 when the forecast couldn't be read (the
paper then runs without the band and says so in one line, never a guess).
"""
import argparse, datetime as dt, html, json, os, sys, urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (os.path.join(_HERE, '..', '..', '..', 'core'), _HERE):
    sys.path.insert(0, os.path.normpath(_p))
import bedo_remaining as R  # noqa: E402  the sun's times, one formula

API = 'https://api.weather.gov'
UA = 'be-do-morning-gate (personal forecast reader)'
DAY_FROM, DAY_TO = 6, 23          # the chart's hours, local


# ── reading ────────────────────────────────────────────────────────────────
def _get(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/geo+json'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def fetch(lat, lon, fixture=None):
    """(points, forecast, hourly) as the service returns them."""
    if fixture:
        rd = lambda n: json.load(open(os.path.join(fixture, n + '.json'), encoding='utf-8'))
        return rd('points'), rd('forecast'), rd('hourly')
    pts = _get(f'{API}/points/{lat:.4f},{lon:.4f}')
    p = pts['properties']
    return pts, _get(p['forecast']), _get(p['forecastHourly'])


def _when(s):
    return dt.datetime.fromisoformat(s)


def _pop(period):
    v = (period.get('probabilityOfPrecipitation') or {}).get('value')
    return int(v) if v is not None else 0


def read(points, forecast, hourly, day=None):
    """The day's forecast as plain values, from the three responses."""
    periods = forecast['properties']['periods']
    hours = hourly['properties']['periods']
    first = _when(periods[0]['startTime'])
    day = day or first.date()
    on = [p for p in periods if _when(p['startTime']).date() == day]
    today = next((p for p in on if p['isDaytime']), None)
    tonight = next((p for p in on if not p['isDaytime']), None)
    lead = today or tonight or periods[0]
    loc = (points.get('properties') or {}).get('relativeLocation', {}).get('properties', {})
    hrs = [h for h in hours if _when(h['startTime']).date() == day
           and DAY_FROM <= _when(h['startTime']).hour <= DAY_TO]
    temps = [h['temperature'] for h in hrs]
    return {
        'date': day.isoformat(),
        'place': ', '.join(x for x in (loc.get('city'), loc.get('state')) if x),
        'tz': (points.get('properties') or {}).get('timeZone'),
        'offset_hours': first.utcoffset().total_seconds() / 3600,
        'name': lead['name'],
        'daytime': bool(today),
        'short': lead['shortForecast'],
        'detail': lead['detailedForecast'],
        'kind': kind(lead['shortForecast']),
        'high': today['temperature'] if today else (max(temps) if temps else None),
        'low': tonight['temperature'] if tonight else (min(temps) if temps else None),
        'rain': max([_pop(p) for p in (today, tonight) if p] or [0]),
        'wind': f"{lead.get('windDirection', '')} {lead.get('windSpeed', '')}".strip(),
        'tonight': tonight['shortForecast'] if tonight and today else None,
        'hours': [{'hour': _when(h['startTime']).hour, 'temp': h['temperature'],
                   'rain': _pop(h), 'kind': kind(h['shortForecast']), 'day': h['isDaytime']}
                  for h in hrs],
    }


# ── the sky's kind ─────────────────────────────────────────────────────────
KINDS = (('storm', ('thunder', 't-storm', 'tstorm')),
         ('snow', ('snow', 'sleet', 'flurr', 'ice', 'freezing')),
         ('rain', ('rain', 'shower', 'drizzle')),
         ('fog', ('fog', 'haze', 'smoke', 'mist')),
         ('cloud', ('mostly cloudy', 'cloudy', 'overcast')),
         ('partly', ('partly', 'mostly sunny', 'mostly clear')),
         ('wind', ('wind', 'breezy', 'blustery')),
         ('clear', ('sunny', 'clear', 'fair', 'hot', 'cold')))


def kind(text):
    """One of storm · snow · rain · fog · cloud · partly · wind · clear, from the
    forecaster's short line. The first word that matches wins, in that order, so
    'Partly Sunny then Chance Rain' reads as rain: the thing to plan around."""
    t = (text or '').lower()
    if 'partly cloudy' in t and not any(w in t for _, ws in KINDS[:4] for w in ws):
        return 'partly'
    for k, words in KINDS:
        if any(w in t for w in words):
            return k
    return 'cloud'


# ── drawing ────────────────────────────────────────────────────────────────
def _sun(cx, cy, r):
    rays = ''.join(
        f'<line x1="{cx + (r + 6) * c:.1f}" y1="{cy + (r + 6) * s:.1f}" x2="{cx + (r + 16) * c:.1f}" '
        f'y2="{cy + (r + 16) * s:.1f}"/>'
        for c, s in ((1, 0), (.707, .707), (0, 1), (-.707, .707), (-1, 0), (-.707, -.707), (0, -1), (.707, -.707)))
    return (f'<g class="wx-sun"><circle cx="{cx}" cy="{cy}" r="{r}"/>'
            f'<g class="wx-rays">{rays}</g></g>')


def _moon(cx, cy, r):
    return (f'<path class="wx-moon" d="M{cx + r * .35:.1f} {cy - r:.1f} a{r} {r} 0 1 0 {r * .65:.1f} {r * 1.6:.1f} '
            f'a{r * .8:.1f} {r * .8:.1f} 0 0 1 {-r * .65:.1f} {-r * 1.6:.1f}z"/>')


def _cloud(x, y, w, cls='wx-cloud'):
    h = w * .5
    return (f'<path class="{cls}" d="M{x + w * .18:.1f} {y + h:.1f} h{w * .66:.1f} '
            f'a{h * .42:.1f} {h * .42:.1f} 0 0 0 0 {-h * .84:.1f} '
            f'a{h * .62:.1f} {h * .62:.1f} 0 0 0 {-w * .38:.1f} {-h * .3:.1f} '
            f'a{h * .5:.1f} {h * .5:.1f} 0 0 0 {-w * .34:.1f} {h * .3:.1f} '
            f'a{h * .42:.1f} {h * .42:.1f} 0 0 0 {.06 * w:.1f} {h * .84:.1f}z"/>')


def picture(k, daytime=True, size=132, label=''):
    """The day's sky as an inline SVG drawing, coloured by the page's tokens."""
    body = (_sun if daytime else _moon)
    parts = {
        'clear': body(60, 60, 26) if daytime else body(60, 60, 30),
        'partly': (_sun(44, 44, 20) if daytime else _moon(44, 44, 22)) + _cloud(34, 46, 76),
        'cloud': _cloud(14, 30, 70, 'wx-cloud wx-back') + _cloud(30, 44, 80),
        'rain': _cloud(20, 22, 84) + ''.join(
            f'<line class="wx-drop" x1="{x}" y1="80" x2="{x - 6}" y2="96"/>' for x in (42, 60, 78, 96)),
        'storm': _cloud(20, 18, 84) + '<path class="wx-bolt" d="M66 72 l-12 22 h10 l-6 18 l20 -26 h-10 l8 -14z"/>',
        'snow': _cloud(20, 22, 84) + ''.join(
            f'<text class="wx-flake" x="{x}" y="100" text-anchor="middle">✻</text>' for x in (42, 64, 86)),
        'fog': _cloud(22, 18, 80) + ''.join(
            f'<line class="wx-fog" x1="{a}" y1="{y}" x2="{b}" y2="{y}"/>' for a, b, y in ((20, 96, 78), (30, 106, 90), (24, 90, 102))),
        'wind': (body(78, 40, 18) if daytime else _moon(78, 40, 18)) + ''.join(
            f'<path class="wx-gust" d="M{a} {y} h{w} a8 8 0 1 0 -8 -8"/>' for a, y, w in ((14, 70, 62), (24, 88, 74), (14, 104, 44))),
    }
    inner = parts.get(k, parts['cloud'])
    t = f'<title>{html.escape(label)}</title>' if label else ''
    return (f'<svg class="wx-pic" viewBox="0 0 120 120" width="{size}" height="{size}" role="img" '
            f'aria-label="{html.escape(label or k)}">{t}{inner}</svg>')


def chart(hours, width=480, height=180):
    """The day's hours: temperature as a line with its labels, chance of rain as
    bars under it. Empty when the day has fewer than three hours left to draw."""
    if len(hours) < 3:
        return ''
    pad_l, pad_r, top, base = 22, 22, 34, height - 44
    n = len(hours)
    step = (width - pad_l - pad_r) / (n - 1)
    lo, hi = min(h['temp'] for h in hours), max(h['temp'] for h in hours)
    span = max(hi - lo, 6)
    y = lambda t: top + (hi - t) / span * (base - top - 50)
    xs = [pad_l + i * step for i in range(n)]
    bars = ''.join(
        f'<rect class="wx-bar" x="{x - step * .32:.1f}" y="{base - h["rain"] * .5:.1f}" '
        f'width="{step * .64:.1f}" height="{h["rain"] * .5:.1f}"/>'
        for x, h in zip(xs, hours) if h['rain'])
    line = 'M' + ' L'.join(f'{x:.1f} {y(h["temp"]):.1f}' for x, h in zip(xs, hours))
    marks, ticks = [], []
    keep = {i for i, h in enumerate(hours) if h['hour'] % 3 == 0}
    for end in (0, n - 1):            # the ends, unless a labelled hour sits right beside them
        if not any(abs(hours[j]['hour'] - hours[end]['hour']) < 2 for j in keep):
            keep.add(end)
    for i, (x, h) in enumerate(zip(xs, hours)):
        if i in keep:
            marks.append(f'<circle class="wx-dot" cx="{x:.1f}" cy="{y(h["temp"]):.1f}" r="4.5"/>'
                         f'<text class="wx-t" x="{x:.1f}" y="{y(h["temp"]) - 12:.1f}" text-anchor="middle">{h["temp"]}°</text>')
            lab = f'{h["hour"] % 12 or 12}{"a" if h["hour"] < 12 else "p"}'
            rain = f'<tspan class="wx-r" x="{x:.1f}" dy="20">{h["rain"]}%</tspan>' if h['rain'] >= 10 else ''
            ticks.append(f'<text class="wx-h" x="{x:.1f}" y="{base + 22}" text-anchor="middle">{lab}{rain}</text>')
    return (f'<svg class="wx-chart" viewBox="0 0 {width} {height + 4}" role="img" '
            f'aria-label="Temperature and chance of rain by the hour">'
            f'<line class="wx-base" x1="0" y1="{base}" x2="{width}" y2="{base}"/>{bars}'
            f'<path class="wx-line" d="{line}"/>{"".join(marks)}{"".join(ticks)}</svg>')


def band(f, rise=None, sets=None):
    """The paper's weather band, as an HTML fragment for the template's slot."""
    e = html.escape
    temps = ' '.join(x for x in (
        f'<span class="wx-hi">{f["high"]}°</span>' if f['high'] is not None else '',
        f'<span class="wx-lo">{f["low"]}°</span>' if f['low'] is not None else '') if x)
    facts = [x for x in (
        f'Rain {f["rain"]}%' if f['rain'] else 'No rain expected',
        f'Wind {e(f["wind"])}' if f['wind'] else '',
        f'Sunrise {R.clock12(rise)}a' if rise is not None else '',
        f'Sunset {R.clock12(sets)}p' if sets is not None else '') if x]
    tonight = f'<p class="wx-tonight">Tonight: {e(f["tonight"].lower())}{f", low {f["low"]}°" if f["low"] is not None else ""}.</p>' \
        if f.get('tonight') else ''
    return (
        '<section class="weather" aria-label="Today\'s weather">\n'
        f'  {picture(f["kind"], f["daytime"], label=f["short"])}\n'
        '  <div class="wx-now">\n'
        f'    <p class="kicker">Weather · {e(f["place"] or "your forecast")}</p>\n'
        f'    <h2>{e(f["short"])} <span class="wx-temps">{temps}</span></h2>\n'
        f'    <p class="wx-detail">{e(f["detail"])}</p>\n'
        f'    {tonight}\n'
        f'    <p class="wx-facts">{" · ".join(facts)}</p>\n'
        '  </div>\n'
        f'  <div class="wx-hours">{chart(f["hours"])}</div>\n'
        '  <p class="source">National Weather Service forecast</p>\n'
        '</section>\n')


def row_line(f, rise=None):
    """The 🌦️ weather check's details: sunrise first, then the sky in words."""
    bits = [f'sunrise {R.clock12(rise)}a' if rise is not None else None,
            ', '.join(x for x in (f['short'].lower(),
                                   f'high {f["high"]}°' if f['high'] is not None else None,
                                   f'low {f["low"]}°' if f['low'] is not None else None) if x),
            f'rain {f["rain"]}%' if f['rain'] else None]
    return ' · '.join(b for b in bits if b)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', help='write the band here (an HTML fragment)')
    ap.add_argument('--date', help='YYYY-MM-DD, default the forecast\'s first day')
    ap.add_argument('--lat', type=float)
    ap.add_argument('--lon', type=float)
    ap.add_argument('--fixture', help='a folder of points/forecast/hourly .json, no network')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    lat, lon = a.lat, a.lon
    if (lat is None or lon is None) and not a.fixture:
        import bedo_reader
        h = (bedo_reader.load_local(required=False) or {}).get('home') or {}
        lat, lon = h.get('lat'), h.get('lon')
        if lat is None or lon is None:
            print('forecast  no home in the settings (home: lat, lon) and no --lat/--lon: the paper runs without weather')
            return 1
    try:
        f = read(*fetch(lat, lon, a.fixture), day=dt.date.fromisoformat(a.date) if a.date else None)
    except Exception as ex:  # the paper never waits on the weather
        print(f'forecast  not read ({type(ex).__name__}: {ex}): the paper runs without weather; say so in one line')
        return 1
    day = dt.date.fromisoformat(f['date'])
    rise = sets = None
    if lat is not None and lon is not None:
        rise = R.sunrise_at(day, lat, lon, f['offset_hours'])
        sets = R.sunset(day, lat, lon, f['offset_hours'])
    if a.out:
        with open(a.out, 'w', encoding='utf-8') as fh:
            fh.write(band(f, rise, sets))
    if a.json:
        print(json.dumps(dict(f, sunrise=rise, sunset=sets, row=row_line(f, rise)), ensure_ascii=False, indent=1))
    else:
        print(f'forecast  {f["name"]}: {f["short"]}, high {f["high"]}°, low {f["low"]}°, rain {f["rain"]}%'
              + (f'  → {a.out}' if a.out else ''))
        print(f'row       🌦️ weather check details: {row_line(f, rise)}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
