# -*- coding: utf-8 -*-
"""Oura into the stream, morning and evening, planned from the Oura API (v2) against the
rows already there. Nothing here writes; the plan is rows and patches in the stream's
own field ids, for a write-scoped tool to apply.

Her words, 20 Oct 2026: I want to make sure Oura gets uploaded automatically, and I
really want it to access the API. Five of seven nights in W42 had no sleep row until
the QA filled them by hand from her screenshots. And the same day: recovery, sleep and
activity are big.

    python3 oura.py --mode morning --start 2026-10-20 --end 2026-10-20 --local look_behind_local.json \\
        --stream w43.json [--stream w42.json] --out oura-plan.json      # fetch, then plan
    python3 oura.py ... --oura oura.json                                # plan from a saved fetch

--mode morning, evening or both (the default, for catching up missed days).

The token, in this order: OURA_PAT (a token handed in directly), the app sign-in kept by
oura_auth.py, or in a Claude cloud session none at all, when the environment carries an
API credential for api.ouraring.com and the proxy attaches it after the request leaves.

morning, per day
  sleep    the main sleep period (type long_sleep) ending that morning becomes a
           😴 sleep row, bedtime_start to bedtime_end. A sleep row already covering
           that night is kept; one with no end gets its end.
  scores   readiness and its contributors (recovery index, HRV balance, resting heart
           rate, body temperature, sleep balance, previous night, previous day, activity
           balance), the sleep score with its stages, latency, HRV, resting heart rate,
           breathing, temperature and SpO2, and the activity score. On that day's
           🪐 morning oura row (her words kept), or a new row at wake-up when there is none.
evening, per day
  the day  activity, steps, calories and time at each intensity; Oura's workouts in
           the day QA's own form (cycling 10:05a–10:40a); stress, recovery and
           resilience; breathing and meditation moments; cardio age and VO2 max. On
           that day's 🪐 evening oura row, or a new ● log row when there is none.
  naps     a nap becomes a 😴 sleep row.
Every block it writes begins [be•do] From the Oura API. Run again, it replaces its own
block when Oura's numbers have moved (an evening read at dusk is filled out next
morning) and plans nothing when they have not.
"""
import argparse, datetime as dt, json, os, re, sys, urllib.error, urllib.parse, urllib.request

API = 'https://api.ouraring.com/v2/usercollection/'
CORE = ('sleep', 'daily_sleep', 'daily_readiness', 'daily_activity', 'daily_stress')
# read when the sign-in allows them; a refusal here is a note, never an abort
EXTRA = ('workout', 'session', 'daily_spo2', 'daily_resilience', 'daily_cardiovascular_age', 'vO2_max')
DIVIDER = '———'
MARK = '[be•do] From the Oura API'
SLEEP, MORNING, EVENING = '😴 sleep', '🪐 morning oura', '🪐 evening oura'
LOG, DONE = '● log', '◉ done'
READINESS = (('recovery_index', 'recovery index'), ('hrv_balance', 'HRV balance'), ('resting_heart_rate', 'resting HR'),
             ('body_temperature', 'body temp'), ('sleep_balance', 'sleep balance'), ('previous_night', 'previous night'),
             ('previous_day_activity', 'previous day'), ('activity_balance', 'activity balance'))
REST = re.compile(r'(?i)\b(nap|rest|sleep)\b')
DAY_SUMMARY = {'restored': 'a restored day', 'normal': 'a normal day', 'stressful': 'a stressful day'}


def die(m):
    sys.exit('ABORT: ' + m)


def token():
    if os.environ.get('OURA_PAT'):
        return os.environ['OURA_PAT']
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import oura_auth
    return oura_auth.access_token()


def fetch(start, end):
    """Every endpoint for the window, paged to the end (I11: a short read is no read)."""
    pat = None if os.environ.get('CLAUDE_CODE_REMOTE') == 'true' else token()
    if not pat and os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        die('not signed in to Oura here — run scripts/oura_auth.py once (SKILL.md, Setup)')
    # Oura's end_date is exclusive for some endpoints; ask one day wide on both sides
    q = {'start_date': (start - dt.timedelta(days=1)).isoformat(), 'end_date': (end + dt.timedelta(days=1)).isoformat()}
    out, notes = {}, []
    for ep in CORE + EXTRA:
        rows, nxt = [], None
        while True:
            url = API + ep + '?' + urllib.parse.urlencode(dict(q, **({'next_token': nxt} if nxt else {})))
            req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + pat} if pat else {})
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    body = json.load(r)
            except urllib.error.HTTPError as e:
                if e.code == 401:
                    die(f'Oura said 401 on {ep} — ' + ('the cloud Oura key has ended; on the laptop run '
                        'scripts/oura_auth.py --cloud and paste the fresh key into the environment'
                        if os.environ.get('CLAUDE_CODE_REMOTE') == 'true' else
                        'the sign-in has ended; run scripts/oura_auth.py'))
                if ep in EXTRA and e.code in (400, 403, 404):
                    notes.append(f'{ep}: Oura said {e.code}, left out')
                    rows = []
                    break
                if e.code == 403:
                    die(f'Oura said 403 on {ep} — the sign-in lacks that permission, or the membership has lapsed')
                die(f'Oura said {e.code} on {ep}')
            except (urllib.error.URLError, OSError) as e:
                die(f'Oura unreachable ({e}) — is api.ouraring.com allowed in this environment?')
            rows += body.get('data') or []
            nxt = body.get('next_token')
            if not nxt:
                break
        out[ep] = rows
    out['_notes'] = notes
    return out


def iso(t):
    return dt.datetime.fromisoformat(t.replace('Z', '+00:00'))


def hm(sec):
    m = round((sec or 0) / 60)
    return f'{m // 60} h {m % 60:02d}'


def clock(d):
    return d.strftime('%I:%M %p').lstrip('0')


def short(d):
    """The day QA's clock: 2:10p."""
    return d.strftime('%I:%M').lstrip('0') + ('a' if d.hour < 12 else 'p')


def zulu(d):
    return d.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:00.000Z')


def by_day(O, ep):
    return {r.get('day'): r for r in O.get(ep) or [] if r.get('day')}


def on(O, ep, day):
    return [r for r in O.get(ep) or [] if r.get('day') == day]


def night(O, day):
    """The main sleep period that ended on this day's morning."""
    longs = [p for p in O.get('sleep') or [] if p.get('day') == day and p.get('type') in ('long_sleep', None)]
    return max(longs, key=lambda p: p.get('time_in_bed') or 0) if longs else None


def naps(O, day, tz):
    """Naps begun on this day. Oura can hold one nap twice (a short period and the whole
    one, 21 Oct 2026: 4:58–5:35 and 4:58–6:20), so the longer of any overlap is kept."""
    main = night(O, day)
    ps = sorted((p for p in O.get('sleep') or [] if p is not main and p.get('type') in ('late_nap', 'sleep')
                 and p.get('bedtime_start') and p.get('bedtime_end')
                 and iso(p['bedtime_start']).astimezone(tz).date().isoformat() == day
                 and (p.get('time_in_bed') or 0) >= 15 * 60), key=lambda p: -(p.get('time_in_bed') or 0))
    kept = []
    for p in ps:
        a, b = iso(p['bedtime_start']), iso(p['bedtime_end'])
        if not any(a < iso(k['bedtime_end']) and iso(k['bedtime_start']) < b for k in kept):
            kept.append(p)
    return sorted(kept, key=lambda p: p['bedtime_start'])


def overlap(r, a, b):
    """Minutes a row with a span shares with a to b."""
    if not (r['when'] and r['end']):
        return 0
    s, e = max(iso(r['when']), a), min(iso(r['end']), b)
    return max(0, (e - s).total_seconds() / 60)


def morning_lines(O, day):
    """Readiness with what made it, the night in full, the activity score: one line each."""
    rd, sl, ac = by_day(O, 'daily_readiness').get(day), by_day(O, 'daily_sleep').get(day), by_day(O, 'daily_activity').get(day)
    sp = by_day(O, 'daily_spo2').get(day)
    main = night(O, day)
    out = []
    if rd and rd.get('score') is not None:
        c = rd.get('contributors') or {}
        bits = [f"readiness {rd['score']}"] + [f'{n} {c[k]}' for k, n in READINESS if c.get(k) is not None]
        if rd.get('temperature_deviation') is not None:
            bits.append(f"temp {rd['temperature_deviation']:+.1f}°")
        out.append(' · '.join(bits))
    bits = [f"sleep {sl['score']}"] if sl and sl.get('score') is not None else []
    if main:
        if main.get('total_sleep_duration') and main.get('time_in_bed'):
            bits.append(f"{hm(main['total_sleep_duration'])} asleep of {hm(main['time_in_bed'])} in bed")
        if main.get('efficiency'):
            bits.append(f"efficiency {main['efficiency']}%")
        for k, n in (('deep_sleep_duration', 'deep'), ('rem_sleep_duration', 'REM'), ('light_sleep_duration', 'light'),
                     ('awake_time', 'awake')):
            if main.get(k) is not None:
                bits.append(f'{n} {hm(main[k])}')
        if main.get('latency') is not None:
            bits.append(f"fell asleep in {round(main['latency'] / 60)} min")
        if main.get('average_hrv'):
            bits.append(f"HRV {round(main['average_hrv'])} ms")
        if main.get('lowest_heart_rate'):
            bits.append(f"resting HR {main['lowest_heart_rate']}")
        if main.get('average_breath'):
            bits.append(f"breathing {main['average_breath']:.1f}/min")
    if sp and (sp.get('spo2_percentage') or {}).get('average'):
        bits.append(f"SpO2 {sp['spo2_percentage']['average']:.0f}%")
    if sp and sp.get('breathing_disturbance_index') is not None:
        bits.append(f"breathing disturbance {sp['breathing_disturbance_index']}")
    if bits:
        out.append(' · '.join(bits))
    if ac and ac.get('score') is not None:
        out.append(f"activity {ac['score']}")
    return out


def evening_lines(O, day, tz):
    """The day as Oura saw it: moving, working out, stress and recovery, moments."""
    ac, st = by_day(O, 'daily_activity').get(day), by_day(O, 'daily_stress').get(day)
    rs, cv, vo = by_day(O, 'daily_resilience').get(day), by_day(O, 'daily_cardiovascular_age').get(day), by_day(O, 'vO2_max').get(day)
    out = []
    if ac:
        bits = [f"activity {ac['score']}"] if ac.get('score') is not None else []
        if ac.get('steps') is not None:
            bits.append(f"{ac['steps']:,} steps")
        if ac.get('active_calories') is not None:
            bits.append(f"{ac['active_calories']} active cal")
        for k, n in (('high_activity_time', 'high'), ('medium_activity_time', 'medium'), ('low_activity_time', 'low'),
                     ('sedentary_time', 'sitting')):
            if ac.get(k):
                bits.append(f'{hm(ac[k])} {n}')
        if ac.get('inactivity_alerts'):
            bits.append(f"{ac['inactivity_alerts']} inactivity alert{'s' if ac['inactivity_alerts'] != 1 else ''}")
        if ac.get('equivalent_walking_distance'):
            bits.append(f"{ac['equivalent_walking_distance'] / 1000:.1f} km walking-equivalent")
        if bits:
            out.append(' · '.join(bits))
    wk = sorted(on(O, 'workout', day), key=lambda w: w.get('start_datetime') or '')
    if wk:
        out.append('workouts: ' + ', '.join(
            f"{(w.get('activity') or 'workout').replace('_', ' ').lower()} "
            f"{short(iso(w['start_datetime']).astimezone(tz))}–{short(iso(w['end_datetime']).astimezone(tz))}"
            + (f" ({w['intensity']})" if w.get('intensity') else '')
            for w in wk if w.get('start_datetime') and w.get('end_datetime')))
    bits = []
    if st:
        bits.append(f"stressed {hm(st.get('stress_high'))}, restored {hm(st.get('recovery_high'))}")
        if DAY_SUMMARY.get(st.get('day_summary')):
            bits.append(DAY_SUMMARY[st['day_summary']])
    if rs and rs.get('level'):
        bits.append(f"resilience {rs['level']}")
    if bits:
        out.append(' · '.join(bits))
    ss = [s for s in on(O, 'session', day) if s.get('start_datetime') and s.get('end_datetime')]
    if ss:
        out.append('moments: ' + ', '.join(
            f"{(s.get('type') or 'session').replace('_', ' ')} "
            f"{round((iso(s['end_datetime']) - iso(s['start_datetime'])).total_seconds() / 60)} min "
            f"at {short(iso(s['start_datetime']).astimezone(tz))}" for s in ss))
    bits = []
    if cv and cv.get('vascular_age'):
        bits.append(f"cardio age {cv['vascular_age']}")
    if vo and vo.get('vo2_max'):
        bits.append(f"VO2 max {vo['vo2_max']:.0f}")
    if bits:
        out.append(' · '.join(bits))
    return out


def merge(d, block):
    """Her words kept; its own block replaced in place, or added after the divider."""
    d = d or ''
    i = d.find(MARK)
    if i < 0:
        return d + '\n' + block if DIVIDER in d else (d + '\n' if d else '') + f'{DIVIDER}\n{block}'
    j = d.find('\n[be•do]', i + 1)
    return d[:i] + block + (d[j:] if j >= 0 else '')


def plan(O, stream_rows, days, F, off, mode='both', now=None):
    """Rows to create and patches to make, in the stream's field ids."""
    tz = dt.timezone(dt.timedelta(hours=off))
    now = now or dt.datetime.now(dt.timezone.utc)
    rows = []
    for r in stream_rows:
        c = r.get('cellValuesByFieldId') or r.get('fields') or {}
        v = lambda k: (c.get(F[k]) or {}).get('name') if isinstance(c.get(F[k]), dict) else c.get(F[k])  # noqa: E731
        rows.append(dict(id=r['id'], practice=v('practice') or '', when=v('when'), end=v('end'), details=v('details') or '',
                         title=v('title') or ''))
    create, patch, notes = [], [], list(O.get('_notes') or [])

    def nap(p):
        """Her rows beat Oura's guess. A rest or sleep row of hers over the nap is the nap;
        her other rows filling most of it mean Oura read rest as sleep (21 Oct 2026: a
        bath, the therapillow and the sun, 2:58–4:10 PM), so it is left out with a note."""
        a, b = iso(p['bedtime_start']), iso(p['bedtime_end'])
        span = (b - a).total_seconds() / 60
        restful = lambda r: r['practice'] == SLEEP or REST.search(r['practice'] + ' ' + r['title'])  # noqa: E731
        if any(restful(r) and overlap(r, a, b) >= span / 2 for r in rows):
            return
        busy = [r for r in rows if overlap(r, a, b) > 0]
        if sum(overlap(r, a, b) for r in busy) >= span / 2:
            notes.append(f"{p['day']}: Oura saw a nap {clock(a.astimezone(tz))}–{clock(b.astimezone(tz))}, but your rows "
                         f"cover it ({', '.join(r['title'] or r['practice'] for r in busy[:3])}); left out")
            return
        sleep_row(p, f"😴 nap {clock(a.astimezone(tz))}", dt.timedelta(hours=1))

    def sleep_row(p, title, near):
        a, b = iso(p['bedtime_start']).astimezone(tz), iso(p['bedtime_end']).astimezone(tz)
        have = [r for r in rows if r['practice'] == SLEEP and r['when'] and abs(iso(r['when']) - a) < near]
        src = (f"{MARK}: in bed {clock(a)} to {clock(b)}, {hm(p.get('time_in_bed'))}; "
               f"{hm(p.get('total_sleep_duration'))} asleep, efficiency {p.get('efficiency')}%.")
        if not have:
            new = {F['title']: title, F['when']: zulu(a), F['end']: zulu(b), F['status']: LOG,
                   F['practice']: SLEEP, F['details']: f"{DIVIDER}\n{src}"}
            create.append(new)
            rows.append(dict(id=None, practice=SLEEP, when=new[F['when']], end=new[F['end']], details=src, title=title))
        elif not have[0]['end']:
            patch.append({'id': have[0]['id'], 'fields': {F['end']: zulu(b)}})
            notes.append(f"{p['day']}: sleep row {have[0]['id']} had no end; Oura gives {clock(b)}")

    def onto(practice, day, lines, label, make):
        """The block onto that day's row of this practice, or a new row from make()."""
        block = f"{MARK}{label}:\n" + '\n'.join(lines)
        mine = [r for r in rows if r['practice'] == practice and r['when'] and iso(r['when']).astimezone(tz).date() == day]
        if mine:
            r = mine[0]
            d = merge(r['details'], block)
            if d != r['details']:
                patch.append({'id': r['id'], 'fields': {F['details']: d}})
        else:
            new = make(block)
            if new:
                create.append(new)

    for day in days:
        ds = day.isoformat()
        if mode in ('morning', 'both'):
            main = night(O, ds)
            if main:
                sleep_row(main, f"😴 sleep, night before {day:%a %d %b}", dt.timedelta(hours=3))
            ml = morning_lines(O, ds)
            if not ml:
                notes.append(f'{ds} morning: Oura holds nothing yet — open the Oura app so the ring syncs')
            else:
                head = next((x.split(' · ')[0] for x in ml if x.startswith('readiness')), ml[0].split(' · ')[0])
                onto(MORNING, day, ml, '', lambda b: main and {
                    F['title']: f"morning oura · {head}", F['when']: zulu(iso(main['bedtime_end'])),
                    F['status']: DONE, F['practice']: MORNING, F['details']: f"{DIVIDER}\n{b}"})
        if mode in ('evening', 'both'):
            for p in naps(O, ds, tz):
                nap(p)
            el = evening_lines(O, ds, tz)
            if not el:
                notes.append(f'{ds} evening: Oura holds nothing yet — open the Oura app so the ring syncs')
                continue
            # a missed evening is logged, not ticked: the flow step stays hers to do
            at = now if now.astimezone(tz).date() == day else dt.datetime.combine(day, dt.time(21), tz)
            onto(EVENING, day, el, ', evening', lambda b: {
                F['title']: f"evening oura · {el[0].split(' · ')[0]}", F['when']: zulu(at),
                F['status']: LOG, F['practice']: EVENING, F['details']: f"{DIVIDER}\n{b}"})
    return dict(create=create, patch=patch, notes=notes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mode', choices=('morning', 'evening', 'both'), default='both')
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
    P = plan(O, recs, days, F, L['utc_offset_hours'], a.mode)
    json.dump(P, open(a.out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps({'create': len(P['create']), 'patch': len(P['patch']), 'notes': P['notes'], 'out': a.out},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
