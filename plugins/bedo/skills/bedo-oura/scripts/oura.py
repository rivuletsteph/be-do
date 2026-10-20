# -*- coding: utf-8 -*-
"""Oura into the stream: one night's sleep and one morning's scores per day, planned
from the Oura API (v2) against the rows already there. Nothing here writes; the plan
is rows and patches in the stream's own field ids, for a write-scoped tool to apply.

Her words, 20 Oct 2026: I want to make sure Oura gets uploaded automatically, and I
really want it to access the API. Five of seven nights in W42 had no sleep row until
the QA filled them by hand from her screenshots.

    python3 oura.py --start 2026-10-11 --end 2026-10-17 --local look_behind_local.json \\
        --stream w42.json [--stream w41.json] --out oura-plan.json      # fetch, then plan
    python3 oura.py ... --oura oura.json                                # plan from a saved fetch

The token: OURA_PAT, or an oura_pat in bedo_secrets.json, or in a Claude cloud session
none at all, when the environment carries an API credential for api.ouraring.com and
the proxy attaches it after the request leaves (the Airtable fetch works the same way).

Per day:
  sleep    the main sleep period (type long_sleep) ending that morning becomes a
           😴 sleep row, bedtime_start to bedtime_end. A sleep row already covering
           that night is kept; one with no end gets its end. Naps are left out.
  morning  readiness, sleep and activity scores, HRV, resting heart rate, time asleep
           of time in bed and efficiency, as one line. It goes on that day's 🪐 morning
           oura row (appended, her words kept), or a new row at wake-up when there is none.
  stress   daytime stress and recovery, on the evening oura row when one exists.
Every row it writes says so in its [be•do] block: From the Oura API.
"""
import argparse, datetime as dt, json, os, sys, urllib.error, urllib.parse, urllib.request

API = 'https://api.ouraring.com/v2/usercollection/'
ENDPOINTS = ('sleep', 'daily_sleep', 'daily_readiness', 'daily_activity', 'daily_stress')
DIVIDER = '———'
SLEEP, MORNING, EVENING = '😴 sleep', '🪐 morning oura', '🪐 evening oura'


def die(m):
    sys.exit('ABORT: ' + m)


def token():
    if os.environ.get('OURA_PAT'):
        return os.environ['OURA_PAT']
    for p in [os.environ.get('BEDO_SECRETS'), 'bedo_secrets.json', os.path.join('..', 'bedo_secrets.json')]:
        if p and os.path.exists(p):
            t = json.load(open(p, encoding='utf-8')).get('oura_pat')
            if t:
                return t
    return None


def fetch(start, end):
    """Every endpoint for the window, paged to the end (I11: a short read is no read)."""
    pat = token()
    if not pat and os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        die('no Oura token here — set OURA_PAT, or run in a cloud session whose environment carries one')
    out = {}
    for ep in ENDPOINTS:
        # Oura's end_date is exclusive for some endpoints; ask one day wide on both sides
        q = {'start_date': (start - dt.timedelta(days=1)).isoformat(), 'end_date': (end + dt.timedelta(days=1)).isoformat()}
        rows, nxt = [], None
        while True:
            url = API + ep + '?' + urllib.parse.urlencode(dict(q, **({'next_token': nxt} if nxt else {})))
            req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + pat} if pat else {})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    body = json.load(r)
            except urllib.error.HTTPError as e:
                if e.code in (401, 403):
                    die(f'Oura said {e.code} on {ep} — token missing, revoked or rotated?')
                die(f'Oura said {e.code} on {ep}')
            except (urllib.error.URLError, OSError) as e:
                die(f'Oura unreachable ({e}) — is api.ouraring.com allowed in this environment?')
            rows += body.get('data') or []
            nxt = body.get('next_token')
            if not nxt:
                break
        out[ep] = rows
    return out


def iso(t):
    return dt.datetime.fromisoformat(t.replace('Z', '+00:00'))


def hm(sec):
    m = round((sec or 0) / 60)
    return f'{m // 60} h {m % 60:02d}'


def clock(d):
    return d.strftime('%I:%M %p').lstrip('0')


def zulu(d):
    return d.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:00.000Z')


def by_day(rows):
    return {r.get('day'): r for r in rows if r.get('day')}


def lines(O, day):
    """The morning line for one day, from whatever Oura holds for it."""
    rd, sl, ac = by_day(O['daily_readiness']).get(day), by_day(O['daily_sleep']).get(day), by_day(O['daily_activity']).get(day)
    main = night(O, day)
    bits = []
    if rd and rd.get('score') is not None:
        bits.append(f"readiness {rd['score']}")
    if sl and sl.get('score') is not None:
        bits.append(f"sleep {sl['score']}")
    if ac and ac.get('score') is not None:
        bits.append(f"activity {ac['score']}")
    if main:
        if main.get('average_hrv'):
            bits.append(f"HRV {round(main['average_hrv'])} ms")
        if main.get('lowest_heart_rate'):
            bits.append(f"resting HR {main['lowest_heart_rate']}")
        if main.get('total_sleep_duration') and main.get('time_in_bed'):
            bits.append(f"{hm(main['total_sleep_duration'])} asleep of {hm(main['time_in_bed'])} in bed")
        if main.get('efficiency'):
            bits.append(f"efficiency {main['efficiency']}%")
    if rd and (rd.get('temperature_deviation') is not None):
        bits.append(f"temp {rd['temperature_deviation']:+.1f}°")
    if ac and ac.get('steps'):
        bits.append(f"{ac['steps']:,} steps")
    return ' · '.join(bits)


def night(O, day):
    """The main sleep period that ended on this day's morning."""
    longs = [p for p in O['sleep'] if p.get('day') == day and p.get('type') in ('long_sleep', None)]
    return max(longs, key=lambda p: p.get('time_in_bed') or 0) if longs else None


def plan(O, stream_rows, days, F, off):
    """Rows to create and patches to make, in the stream's field ids."""
    tz = dt.timezone(dt.timedelta(hours=off))
    rows = []
    for r in stream_rows:
        c = r.get('cellValuesByFieldId') or r.get('fields') or {}
        v = lambda k: (c.get(F[k]) or {}).get('name') if isinstance(c.get(F[k]), dict) else c.get(F[k])  # noqa: E731
        rows.append(dict(id=r['id'], practice=v('practice') or '', when=v('when'), end=v('end'), details=v('details') or ''))
    create, patch, notes = [], [], []
    for day in days:
        ds = day.isoformat()
        main = night(O, ds)
        if main:
            a, b = iso(main['bedtime_start']).astimezone(tz), iso(main['bedtime_end']).astimezone(tz)
            have = [r for r in rows if r['practice'] == SLEEP and r['when']
                    and abs(iso(r['when']) - a) < dt.timedelta(hours=3)]
            src = (f"From the Oura API: in bed {clock(a)} to {clock(b)}, {hm(main.get('time_in_bed'))}; "
                   f"{hm(main.get('total_sleep_duration'))} asleep, efficiency {main.get('efficiency')}%.")
            if not have:
                create.append({F['title']: f"😴 sleep, night before {day:%a %d %b}", F['when']: zulu(a), F['end']: zulu(b),
                               F['status']: '● log', F['practice']: SLEEP,
                               F['details']: f"{DIVIDER}\n[be•do] {src}"})
            elif not have[0]['end']:
                patch.append({'id': have[0]['id'], 'fields': {F['end']: zulu(b)}})
                notes.append(f"{ds}: sleep row {have[0]['id']} had no end; Oura gives {clock(b)}")
        line = lines(O, ds)
        if not line:
            notes.append(f'{ds}: Oura holds nothing for this day')
            continue
        mo = [r for r in rows if r['practice'] == MORNING and r['when'] and iso(r['when']).astimezone(tz).date() == day]
        block = f"[be•do] From the Oura API: {line}."
        if mo:
            r = mo[0]
            if 'From the Oura API' not in r['details']:
                d = r['details']
                patch.append({'id': r['id'], 'fields': {F['details']: (d + '\n' if DIVIDER in d else d + f'\n{DIVIDER}\n') + block}})
        elif main:
            wake = iso(main['bedtime_end'])
            create.append({F['title']: f"morning oura · {line.split(' · ')[0]}", F['when']: zulu(wake), F['status']: '◉ done',
                           F['practice']: MORNING, F['details']: f"{DIVIDER}\n{block}"})
        st = by_day(O['daily_stress']).get(ds)
        ev = [r for r in rows if r['practice'] == EVENING and r['when'] and iso(r['when']).astimezone(tz).date() == day]
        if st and ev and 'From the Oura API' not in ev[0]['details']:
            d = ev[0]['details']
            patch.append({'id': ev[0]['id'], 'fields': {F['details']: (d + '\n' if DIVIDER in d else d + f'\n{DIVIDER}\n') +
                          f"[be•do] From the Oura API: stressed {hm(st.get('stress_high'))}, restored {hm(st.get('recovery_high'))}."}})
    return dict(create=create, patch=patch, notes=notes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--local', required=True, help="the day behind's look_behind_local.json")
    ap.add_argument('--stream', action='append', required=True, help='live base first')
    ap.add_argument('--oura', help='a saved fetch; without it, the API is read')
    ap.add_argument('--out', default='oura-plan.json')
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    S = L['fields']['stream']
    F = dict(title=S['title'], when=S['when'], end=S['end'], status=S['status'], practice=S['practice'], details=S['details'])
    start, end = dt.date.fromisoformat(a.start), dt.date.fromisoformat(a.end)
    O = json.load(open(a.oura, encoding='utf-8')) if a.oura else fetch(start, end)
    if not a.oura:
        json.dump(O, open('oura.json', 'w', encoding='utf-8'), ensure_ascii=False)
    seen, recs = set(), []
    for p in a.stream:
        d = json.load(open(p, encoding='utf-8'))
        for r in d.get('records', d if isinstance(d, list) else []):
            if r['id'] not in seen:
                seen.add(r['id'])
                recs.append(r)
    days = [start + dt.timedelta(days=i) for i in range((end - start).days + 1)]
    P = plan(O, recs, days, F, L['utc_offset_hours'])
    json.dump(P, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'create': len(P['create']), 'patch': len(P['patch']), 'notes': P['notes'], 'out': a.out},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
