# -*- coding: utf-8 -*-
"""Where in the night she was asleep: Oura's sleep periods around one day, with
their five-minute timelines, for the day behind's night (26 Oct 2026, her words:
"in bed is the whole span, but the actual asleep part darker blue", and the day
split at midnight).

    python3 day_sleep.py --day 2026-10-25 --out sleep-2026-10-25.json

Writes a list of periods, each {start, end, type, phases}: start and end as Oura
gives them (with their offset), phases one character per five minutes from the
start (1 deep, 2 light, 3 REM, 4 awake). The builder reads it with --sleep.

The token is read the way bedo-oura reads it: in a Claude cloud session none at
all (the environment's API credential is attached by the proxy), else OURA_PAT.
Without either, or when Oura can't be reached, it writes nothing and says so;
the page then places the asleep minutes from the sleep row's own Oura line.
"""
import argparse, datetime as dt, json, os, sys, urllib.error, urllib.parse, urllib.request

API = 'https://api.ouraring.com/v2/usercollection/sleep'


def periods(day):
    remote = os.environ.get('CLAUDE_CODE_REMOTE') == 'true'
    pat = None if remote else os.environ.get('OURA_PAT')
    if not remote and not pat:
        return None, 'no Oura token here (OURA_PAT), so the night uses the sleep row alone'
    q = {'start_date': (day - dt.timedelta(days=1)).isoformat(), 'end_date': (day + dt.timedelta(days=2)).isoformat()}
    out, nxt = [], None
    while True:
        url = API + '?' + urllib.parse.urlencode(dict(q, **({'next_token': nxt} if nxt else {})))
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + pat} if pat else {})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                body = json.load(r)
        except (urllib.error.URLError, OSError) as e:
            return None, f'Oura not read ({e}), so the night uses the sleep row alone'
        out += body.get('data') or []
        nxt = body.get('next_token')
        if not nxt:
            break
    return [dict(start=p['bedtime_start'], end=p['bedtime_end'], type=p.get('type'),
                 phases=p.get('sleep_phase_5_min') or '') for p in out if p.get('bedtime_start') and p.get('bedtime_end')], None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    got, note = periods(dt.date.fromisoformat(a.day))
    if got is None:
        print('sleep: ' + note)
        sys.exit(1)
    json.dump(got, open(a.out, 'w', encoding='utf-8'), indent=1)
    print(f'sleep: {len(got)} Oura period(s) around {a.day}')


if __name__ == '__main__':
    main()
