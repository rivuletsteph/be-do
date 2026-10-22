# -*- coding: utf-8 -*-
"""Oura into the stream, over two invented days, morning and evening. Night one has no
sleep row and a morning oura row in her words: a sleep row is created and the morning
block joins her words, readiness with what made it. Night two has a sleep row with no
end and no morning row: the end is patched and a morning row is created at wake-up. The
evening of day one lands on her evening row, replacing an older Oura line, with the
workout in the day QA's own form; day two has no evening row, so one is logged, not
ticked. A nap is its own sleep row, never the night. Read at dusk and again the next
morning, the evening block is refreshed; run twice on the same numbers, nothing is
planned. The week page still finds readiness, sleep and activity on the morning row.

    python3 tests/test_oura.py
"""
import copy, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import oura  # noqa: E402
import datetime as dt  # noqa: E402

F = dict(title='fT', when='fW', end='fE', status='fS', practice='fP', details='fD')
O = {
    'sleep': [
        {'day': '2026-09-29', 'type': 'long_sleep', 'bedtime_start': '2026-09-28T22:06:00-05:00',
         'bedtime_end': '2026-09-29T06:48:00-05:00', 'time_in_bed': 31320, 'total_sleep_duration': 27420,
         'efficiency': 88, 'average_hrv': 37.2, 'lowest_heart_rate': 54, 'deep_sleep_duration': 4800,
         'rem_sleep_duration': 6300, 'light_sleep_duration': 16320, 'awake_time': 3900, 'latency': 720,
         'average_breath': 14.25},
        {'day': '2026-09-29', 'type': 'late_nap', 'bedtime_start': '2026-09-29T15:00:00-05:00',
         'bedtime_end': '2026-09-29T15:40:00-05:00', 'time_in_bed': 2400, 'total_sleep_duration': 2100, 'efficiency': 90},
        {'day': '2026-09-30', 'type': 'long_sleep', 'bedtime_start': '2026-09-29T22:43:00-05:00',
         'bedtime_end': '2026-09-30T06:54:00-05:00', 'time_in_bed': 29460, 'total_sleep_duration': 26280, 'efficiency': 89},
    ],
    'daily_sleep': [{'day': '2026-09-29', 'score': 93}, {'day': '2026-09-30', 'score': 92}],
    'daily_readiness': [{'day': '2026-09-29', 'score': 88, 'temperature_deviation': -0.4,
                         'contributors': {'recovery_index': 95, 'hrv_balance': 72, 'resting_heart_rate': 90,
                                          'sleep_balance': 85, 'activity_balance': 77}},
                        {'day': '2026-09-30', 'score': 89}],
    'daily_activity': [{'day': '2026-09-29', 'score': 92, 'steps': 11234, 'active_calories': 412,
                        'high_activity_time': 2700, 'medium_activity_time': 5400, 'sedentary_time': 30000,
                        'inactivity_alerts': 2},
                       {'day': '2026-09-30', 'score': 91, 'steps': 8000}],
    'daily_stress': [{'day': '2026-09-29', 'stress_high': 4500, 'recovery_high': 900, 'day_summary': 'normal'}],
    'daily_spo2': [{'day': '2026-09-29', 'spo2_percentage': {'average': 97.2}, 'breathing_disturbance_index': 3}],
    'daily_resilience': [{'day': '2026-09-29', 'level': 'solid'}],
    'workout': [{'day': '2026-09-29', 'activity': 'cycling', 'intensity': 'moderate',
                 'start_datetime': '2026-09-29T10:05:00-05:00', 'end_datetime': '2026-09-29T10:40:00-05:00'}],
    'session': [{'day': '2026-09-29', 'type': 'breathing',
                 'start_datetime': '2026-09-29T21:10:00-05:00', 'end_datetime': '2026-09-29T21:20:00-05:00'}],
    '_notes': ['vO2_max: Oura said 404, left out'],
}
STREAM = [
    {'id': 'recMorning1', 'cellValuesByFieldId': {'fP': '🪐 morning oura', 'fW': '2026-09-29T12:20:00.000Z',
                                                   'fD': 'Felt rested.'}},
    {'id': 'recEvening1', 'cellValuesByFieldId': {'fP': '🪐 evening oura', 'fW': '2026-09-30T02:30:00.000Z',
                                                   'fD': 'Calm day.\n———\n[be•do] From the Oura API: stressed 0 h 10, restored 0 h 05.'}},
    {'id': 'recSleep2', 'cellValuesByFieldId': {'fP': '😴 sleep', 'fW': '2026-09-30T03:43:00.000Z'}},
]
DAYS = [dt.date(2026, 9, 29), dt.date(2026, 9, 30)]
NOW = dt.datetime(2026, 10, 1, 13, 0, tzinfo=dt.timezone.utc)


def applied(P, stream):
    """The stream after the plan went in."""
    out = copy.deepcopy(stream)
    for p in P['patch']:
        next(r for r in out if r['id'] == p['id'])['cellValuesByFieldId'].update(p['fields'])
    return out + [{'id': f'recNew{i}', 'cellValuesByFieldId': c} for i, c in enumerate(P['create'])]


def main():
    P = oura.plan(O, STREAM, DAYS, F, -5, now=NOW)
    sleeps = [c for c in P['create'] if c['fP'] == '😴 sleep']
    s = [c for c in sleeps if 'night before' in c['fT']]
    assert len(s) == 1 and s[0]['fW'] == '2026-09-29T03:06:00.000Z' and s[0]['fE'] == '2026-09-29T11:48:00.000Z', s
    assert 'From the Oura API' in s[0]['fD'] and '7 h 37 asleep' in s[0]['fD'], s[0]['fD']
    nap = [c for c in sleeps if 'nap' in c['fT']]
    assert len(nap) == 1 and nap[0]['fW'] == '2026-09-29T20:00:00.000Z' and nap[0]['fT'] == '😴 nap 3:00 PM', nap
    pt = {p['id']: p['fields'] for p in P['patch']}
    assert pt['recSleep2'] == {'fE': '2026-09-30T11:54:00.000Z'}, pt

    mo = pt['recMorning1']['fD']
    assert mo.startswith('Felt rested.\n———\n[be•do] From the Oura API:\nreadiness 88 · recovery index 95 · HRV balance 72'), mo
    for bit in ('resting HR 90', 'temp -0.4°', 'sleep 93 · 7 h 37 asleep of 8 h 42 in bed', 'deep 1 h 20', 'REM 1 h 45',
                'fell asleep in 12 min', 'HRV 37 ms', 'resting HR 54', 'breathing 14.2/min', 'SpO2 97%', '\nactivity 92'):
        assert bit in mo, (bit, mo)
    # the week page's own reading of the morning row
    rx = {k: re.compile(r'\b' + k + r'\b\D{0,3}(\d{2,3})', re.I) for k in ('readiness', 'sleep', 'activity')}
    assert [int(rx[k].search(mo).group(1)) for k in ('readiness', 'sleep', 'activity')] == [88, 93, 92], mo

    ev = pt['recEvening1']['fD']
    assert ev.startswith('Calm day.\n———\n[be•do] From the Oura API, evening:\nactivity 92 · 11,234 steps · 412 active cal'), ev
    assert 'stressed 0 h 10' not in ev, ev
    for bit in ('0 h 45 high', '2 inactivity alerts', 'workouts: cycling 10:05a–10:40a (moderate)',
                'stressed 1 h 15, restored 0 h 15 · a normal day · resilience solid', 'moments: breathing 10 min at 9:10p'):
        assert bit in ev, (bit, ev)
    made = {c['fP']: c for c in P['create']}
    new_mo = made['🪐 morning oura']
    assert new_mo['fW'] == '2026-09-30T11:54:00.000Z' and new_mo['fT'] == 'morning oura · readiness 89', new_mo
    assert new_mo['fS'] == '◉ done', new_mo
    new_ev = made['🪐 evening oura']
    assert new_ev['fS'] == '● log' and new_ev['fW'] == '2026-10-01T02:00:00.000Z', new_ev
    assert new_ev['fT'] == 'evening oura · activity 91', new_ev
    assert P['notes'][0] == 'vO2_max: Oura said 404, left out', P['notes']

    # applied, then planned again on the same numbers: nothing new
    s2 = applied(P, STREAM)
    P2 = oura.plan(O, s2, DAYS, F, -5, now=NOW)
    assert P2['create'] == [] and P2['patch'] == [], P2

    # the evening read at dusk, then again the next morning when the day is complete
    dusk = copy.deepcopy(O)
    dusk['daily_activity'][0].update(score=80, steps=9000)
    P3 = oura.plan(dusk, STREAM, DAYS[:1], F, -5, mode='evening', now=NOW)
    assert [c['fP'] for c in P3['create']] == ['😴 sleep'], P3['create']        # the nap only, no morning work
    ev3 = {p['id']: p['fields'] for p in P3['patch']}['recEvening1']['fD']
    assert '9,000 steps' in ev3, ev3
    P4 = oura.plan(O, applied(P3, STREAM), DAYS[:1], F, -5, mode='evening', now=NOW)
    ev4 = {p['id']: p['fields'] for p in P4['patch']}['recEvening1']['fD']
    assert '11,234 steps' in ev4 and '9,000' not in ev4 and ev4.startswith('Calm day.\n———\n'), ev4

    # 21 Oct 2026: Oura held the 4:58 nap twice, and read a bath and the sun as a nap.
    # Her rest row is the nap; her other rows win over Oura's guess.
    d21 = {'sleep': [
        {'day': '2026-10-21', 'type': 'sleep', 'bedtime_start': '2026-10-21T14:58:00-05:00',
         'bedtime_end': '2026-10-21T16:10:00-05:00', 'time_in_bed': 4320, 'total_sleep_duration': 2430},
        {'day': '2026-10-21', 'type': 'sleep', 'bedtime_start': '2026-10-21T16:58:00-05:00',
         'bedtime_end': '2026-10-21T17:35:00-05:00', 'time_in_bed': 2220, 'total_sleep_duration': 690},
        {'day': '2026-10-22', 'type': 'late_nap', 'bedtime_start': '2026-10-21T16:58:00-05:00',
         'bedtime_end': '2026-10-21T18:20:00-05:00', 'time_in_bed': 4890, 'total_sleep_duration': 3120}]}
    mine = [
        {'id': 'recBath', 'cellValuesByFieldId': {'fP': '🛀 bath', 'fT': '🛀 Epsom salt bath',
                                                  'fW': '2026-10-21T19:30:00.000Z', 'fE': '2026-10-21T20:00:00.000Z'}},
        {'id': 'recNeck', 'cellValuesByFieldId': {'fP': '🦒 neck stretch', 'fT': '🦒 on the therapillow',
                                                  'fW': '2026-10-21T20:30:00.000Z', 'fE': '2026-10-21T20:50:00.000Z'}},
        {'id': 'recSun', 'cellValuesByFieldId': {'fP': '🔅 sunshine', 'fT': '🔅 in the sun',
                                                 'fW': '2026-10-21T20:50:00.000Z', 'fE': '2026-10-21T21:35:00.000Z'}},
        {'id': 'recRest', 'cellValuesByFieldId': {'fP': '🛌 power rest · 10-hour charge', 'fT': '🛌 nap — 4:58 to 6:20 PM',
                                                  'fW': '2026-10-21T21:58:00.000Z', 'fE': '2026-10-21T23:20:00.000Z'}}]
    P6 = oura.plan(d21, mine, [dt.date(2026, 10, 21)], F, -5, mode='evening', now=NOW)
    assert P6['create'] == [] and P6['patch'] == [], P6
    assert any('2:58 PM–4:10 PM' in n and 'left out' in n for n in P6['notes']), P6['notes']
    P7 = oura.plan(d21, mine[-1:], [dt.date(2026, 10, 21)], F, -5, mode='evening', now=NOW)
    assert [c['fT'] for c in P7['create']] == ['😴 nap 2:58 PM'], P7['create']    # with nothing of hers over it, it is a nap

    # before the ring has synced: a note, never a row
    P5 = oura.plan({'sleep': []}, [], [dt.date(2026, 10, 2)], F, -5, mode='morning', now=NOW)
    assert P5['create'] == [] and 'ring syncs' in P5['notes'][0], P5
    print('ok — a night and a nap become sleep rows, recovery and sleep join her morning words, '
          'the evening carries activity, workouts and stress, refreshed in place, nothing twice')


if __name__ == '__main__':
    main()
