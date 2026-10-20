# -*- coding: utf-8 -*-
"""Oura into the stream, over two invented mornings. Night one has no sleep row and a
morning oura row in her words: a sleep row is created and the scores are appended to her
row, her words kept. Night two has a sleep row with no end and no morning row: the end
is patched and a morning row is created at wake-up. A nap is never a night. Run twice,
nothing new is planned for what it already wrote.

    python3 tests/test_oura.py
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import oura  # noqa: E402
import datetime as dt  # noqa: E402

F = dict(title='fT', when='fW', end='fE', status='fS', practice='fP', details='fD')
O = {
    'sleep': [
        {'day': '2026-09-29', 'type': 'long_sleep', 'bedtime_start': '2026-09-28T22:06:00-05:00',
         'bedtime_end': '2026-09-29T06:48:00-05:00', 'time_in_bed': 31320, 'total_sleep_duration': 27420,
         'efficiency': 88, 'average_hrv': 37.2, 'lowest_heart_rate': 54},
        {'day': '2026-09-29', 'type': 'late_nap', 'bedtime_start': '2026-09-29T15:00:00-05:00',
         'bedtime_end': '2026-09-29T15:40:00-05:00', 'time_in_bed': 2400, 'total_sleep_duration': 2100, 'efficiency': 90},
        {'day': '2026-09-30', 'type': 'long_sleep', 'bedtime_start': '2026-09-29T22:43:00-05:00',
         'bedtime_end': '2026-09-30T06:54:00-05:00', 'time_in_bed': 29460, 'total_sleep_duration': 26280, 'efficiency': 89},
    ],
    'daily_sleep': [{'day': '2026-09-29', 'score': 93}, {'day': '2026-09-30', 'score': 92}],
    'daily_readiness': [{'day': '2026-09-29', 'score': 88, 'temperature_deviation': -0.4}, {'day': '2026-09-30', 'score': 89}],
    'daily_activity': [{'day': '2026-09-29', 'score': 92, 'steps': 11234}, {'day': '2026-09-30', 'score': 91}],
    'daily_stress': [{'day': '2026-09-29', 'stress_high': 4500, 'recovery_high': 900}],
}
STREAM = [
    {'id': 'recMorning1', 'cellValuesByFieldId': {'fP': '🪐 morning oura', 'fW': '2026-09-29T12:20:00.000Z',
                                                   'fD': 'Felt rested.'}},
    {'id': 'recEvening1', 'cellValuesByFieldId': {'fP': '🪐 evening oura', 'fW': '2026-09-30T02:30:00.000Z',
                                                   'fD': '———\n[be•do] her screenshot'}},
    {'id': 'recSleep2', 'cellValuesByFieldId': {'fP': '😴 sleep', 'fW': '2026-09-30T03:43:00.000Z'}},
]
DAYS = [dt.date(2026, 9, 29), dt.date(2026, 9, 30)]


def main():
    P = oura.plan(O, STREAM, DAYS, F, -5)
    made = {c['fP']: c for c in P['create']}
    s = [c for c in P['create'] if c['fP'] == '😴 sleep']
    assert len(s) == 1 and s[0]['fW'] == '2026-09-29T03:06:00.000Z' and s[0]['fE'] == '2026-09-29T11:48:00.000Z', s
    assert 'From the Oura API' in s[0]['fD'] and '7 h 37 asleep' in s[0]['fD'], s[0]['fD']
    pt = {p['id']: p['fields'] for p in P['patch']}
    assert pt['recSleep2'] == {'fE': '2026-09-30T11:54:00.000Z'}, pt
    mo = pt['recMorning1']['fD']
    assert mo.startswith('Felt rested.\n———\n[be•do] From the Oura API: readiness 88 · sleep 93 · activity 92'), mo
    assert 'HRV 37 ms' in mo and 'resting HR 54' in mo and '11,234 steps' in mo, mo
    assert 'stressed 1 h 15, restored 0 h 15' in pt['recEvening1']['fD'], pt['recEvening1']
    new_mo = made['🪐 morning oura']
    assert new_mo['fW'] == '2026-09-30T11:54:00.000Z' and new_mo['fT'] == 'morning oura · readiness 89', new_mo
    # the nap is never a night
    assert not any('15:00' in c.get('fW', '') or '20:00' in c.get('fW', '') for c in P['create']), P['create']
    # applied, then planned again: nothing new for what it wrote
    stream2 = [
        {'id': 'recNew1', 'cellValuesByFieldId': s[0]},
        {'id': 'recNew2', 'cellValuesByFieldId': new_mo},
        {'id': 'recMorning1', 'cellValuesByFieldId': {'fP': '🪐 morning oura', 'fW': '2026-09-29T12:20:00.000Z', 'fD': mo}},
        {'id': 'recSleep2', 'cellValuesByFieldId': {'fP': '😴 sleep', 'fW': '2026-09-30T03:43:00.000Z',
                                                     'fE': '2026-09-30T11:54:00.000Z'}},
        {'id': 'recEvening1', 'cellValuesByFieldId': {'fP': '🪐 evening oura', 'fW': '2026-09-30T02:30:00.000Z',
                                                       'fD': pt['recEvening1']['fD']}},
    ]
    P2 = oura.plan(O, stream2, DAYS, F, -5)
    assert P2['create'] == [] and P2['patch'] == [], P2
    print('ok — a night becomes a sleep row, a missing end is filled, scores join her words, nothing twice')


if __name__ == '__main__':
    main()
