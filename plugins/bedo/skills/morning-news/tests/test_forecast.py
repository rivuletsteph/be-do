# -*- coding: utf-8 -*-
"""The Morning Gate's weather band (24 Nov 2026): today's forecast with its
picture, read from the weather service's three answers, and the 🌦️ weather
check's details line. Every place and number below is an invention.

    python3 tests/test_forecast.py
"""
import datetime as dt, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import forecast as F  # noqa: E402
import bedo_remaining as R  # noqa: E402

DAY = '2031-03-04'


def period(name, start, day, temp, short, pop, detail=''):
    return {'name': name, 'startTime': f'{start}-06:00', 'isDaytime': day, 'temperature': temp,
            'shortForecast': short, 'detailedForecast': detail or short + '.',
            'probabilityOfPrecipitation': {'value': pop}, 'windSpeed': '5 to 10 mph', 'windDirection': 'S'}


def hour(h, temp, pop, short='Mostly Cloudy', date=DAY):
    return {'startTime': f'{date}T{h:02d}:00:00-06:00', 'temperature': temp, 'isDaytime': 6 <= h < 18,
            'shortForecast': short, 'probabilityOfPrecipitation': {'value': pop}}


POINTS = {'properties': {'timeZone': 'America/Chicago',
                         'relativeLocation': {'properties': {'city': 'Inventedville', 'state': 'TX'}}}}
FORECAST = {'properties': {'periods': [
    period('Today', f'{DAY}T06:00:00', True, 64, 'Partly Sunny then Chance Showers', 40,
           'Showers likely after noon. Mostly cloudy, with a high near 64.'),
    period('Tonight', f'{DAY}T18:00:00', False, 41, 'Mostly Clear', 10),
    period('Wednesday', '2031-03-05T06:00:00', True, 70, 'Sunny', 0)]}}
HOURLY = {'properties': {'periods': [hour(h, 48 + min(h - 5, 9), 30 if 12 <= h <= 16 else 0)
                                     for h in range(5, 24)] + [hour(1, 40, 0, date='2031-03-05')]}}

checks = []


def ok(cond, what):
    checks.append((bool(cond), what))


f = F.read(POINTS, FORECAST, HOURLY)
ok(f['date'] == DAY and f['place'] == 'Inventedville, TX', 'the day and the place come from the answers')
ok(f['high'] == 64 and f['low'] == 41 and f['rain'] == 40, "today's high, tonight's low, the larger chance of rain")
ok(f['kind'] == 'rain', 'a sky that turns to showers is drawn as rain: the thing to plan around')
ok(f['tonight'] == 'Mostly Clear', 'tonight rides along when today leads')
ok([h['hour'] for h in f['hours']] == list(range(6, 24)), 'the chart holds 6a to 11p of that day only')

# Kinds, from the forecaster's short line.
for text, k in (('Sunny', 'clear'), ('Mostly Sunny', 'partly'), ('Partly Cloudy', 'partly'),
                ('Mostly Cloudy', 'cloud'), ('Chance Rain Showers', 'rain'), ('Slight Chance Thunderstorms', 'storm'),
                ('Patchy Fog', 'fog'), ('Light Snow Likely', 'snow'), ('Breezy', 'wind'), ('', 'cloud')):
    ok(F.kind(text) == k, f'{text!r} reads as {k}')

# An evening run: the day's first period is Tonight.
late = {'properties': {'periods': FORECAST['properties']['periods'][1:]}}
g = F.read(POINTS, late, HOURLY)
ok(not g['daytime'] and g['low'] == 41 and g['tonight'] is None, 'an evening run leads with tonight, drawn at night')

# The band.
band = F.band(f, rise=7 * 60 + 2, sets=18 * 60 + 31)
ok(band.startswith('<section class="weather"') and '<svg class="wx-pic"' in band, 'the band carries its drawn picture')
ok('<svg class="wx-chart"' in band and band.count('wx-bar') >= 3, 'the chart draws the rain bars')
ok('64°' in band and '41°' in band and 'Sunrise 7:02a' in band and 'Sunset 6:31p' in band,
   'high, low, sunrise and sunset are on it')
ok('<img' not in band and 'http' not in band.replace('http://www.w3.org', ''), 'no outside image: nothing for the CSP to block')
ok('Showers likely after noon' in band, "the forecaster's own words, unchanged")
for k in ('clear', 'partly', 'cloud', 'rain', 'storm', 'snow', 'fog', 'wind'):
    for day in (True, False):
        ok(F.picture(k, day).startswith('<svg'), f'a picture for {k}, {"day" if day else "night"}')

# The 🌦️ weather check's details: sunrise first, then the sky that cloudy() reads.
line = F.row_line(f, rise=7 * 60 + 2)
ok(line.startswith('sunrise 7:02a · '), 'sunrise leads the details line')
rows = [{'practice': '🌦️ weather check', 'details': line, 'datetime': f'{DAY}T13:00:00.000Z'}]
ok(R.cloudy(rows), 'a showery day reads as cloudy, so the bright light meets 🔅 morning sun')
ok(R._SUNRISE.search(line), "the remaining list's sunrise reader finds it")

# Sunrise comes before sunset, at an invented spot.
rise, sets = R.sunrise_at(dt.date(2031, 3, 4), 31.0, -98.0, -6), R.sunset(dt.date(2031, 3, 4), 31.0, -98.0, -6)
ok(6 * 60 < rise < 8 * 60 and 18 * 60 < sets < 19 * 60 + 30, f'the sun keeps its hours ({rise}, {sets})')

# Offline from a folder, and the exit code that keeps the paper from waiting.
with tempfile.TemporaryDirectory() as d:
    for n, v in (('points', POINTS), ('forecast', FORECAST), ('hourly', HOURLY)):
        json.dump(v, open(os.path.join(d, n + '.json'), 'w'))
    out = os.path.join(d, 'w.html')
    ok(F.main(['--fixture', d, '--out', out, '--lat', '31', '--lon', '-98']) == 0 and
       open(out, encoding='utf-8').read().startswith('<section'), 'a fixture folder writes the band')
    ok(F.main(['--fixture', os.path.join(d, 'missing'), '--out', out]) == 1, 'an unread forecast exits 1, no guess')

bad = [w for good, w in checks if not good]
for w in bad:
    print('FAIL', w)
print(f'{len(checks) - len(bad)} of {len(checks)} forecast checks pass')
sys.exit(1 if bad else 0)
