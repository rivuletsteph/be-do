# -*- coding: utf-8 -*-
"""day_heart.py — the day's heart rate from Oura, for the my day page (8 Nov 2026).

Her words, reading Saturday's heart rate beside her day: *the heart rate thing is actually really helpful;
I think that's how we decide what's relaxing versus energizing*. The page reads this file and lets the heart
rate over a stretch of play decide its kind (flow.heart_onto).

    python3 day_heart.py --day 2026-11-07 --local day_ahead_local.json --out heart-2026-11-07.json

Reads api.ouraring.com/v2/usercollection/heartrate for the local day, every page, and writes the samples as
Oura gave them ([{timestamp, bpm, source}]). The key is the environment's: the proxy attaches it, so nothing
here holds one. Exit 3 when Oura can't be read here; the page builds without it.
"""
import argparse, datetime as dt, json, sys, urllib.parse, urllib.request
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_os.path.join(_HERE, '..', '..', '..', 'core'), _HERE):   # the core: beside wins, else three folders up
    sys.path.insert(0, _os.path.normpath(_p))
import bedo_clock  # noqa: E402  the one clock: the offset from time_zone

API = 'https://api.ouraring.com/v2/usercollection/heartrate'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    start, end = bedo_clock.day_bounds_utc(L, dt.date.fromisoformat(a.day))   # 23 or 25 hours on a change day
    q = dict(start_datetime=start.strftime('%Y-%m-%dT%H:%M:%SZ'),
             end_datetime=end.strftime('%Y-%m-%dT%H:%M:%SZ'))
    out, tok = [], None
    try:
        while True:
            url = API + '?' + urllib.parse.urlencode(dict(q, **({'next_token': tok} if tok else {})))
            with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
                d = json.load(r)
            out += [dict(timestamp=x['timestamp'], bpm=x['bpm'], source=x.get('source')) for x in d.get('data') or []]
            tok = d.get('next_token')
            if not tok:
                break
    except Exception as e:                       # noqa: BLE001 — no Oura here is not an error for the page
        print(f'heart rate: not read ({type(e).__name__}) — the page builds without it')
        sys.exit(3)
    json.dump(out, open(a.out, 'w'))
    print(json.dumps({'day': a.day, 'samples': len(out), 'out': a.out}))


if __name__ == '__main__':
    main()
