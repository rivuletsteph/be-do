# -*- coding: utf-8 -*-
"""Who and where on the my day page (28 Nov 2026).

Her words, 27 Nov 2026: I haven't seen a sociogram on the my day in a long time. After that, add geography to the my
day too. Those are both important. The sociogram had been drawn only on the day behind, retired 8 Nov; the day's map
was built for a page that never wired it. Every name and place below is an obvious invention.

    python3 tests/test_who_where.py
"""
import datetime as dt, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
sys.path.insert(1, os.path.join(HERE, '..', '..', '..', 'core'))
import who_where as WW  # noqa: E402

F = dict(when='w', end='e', status='s', title='t', person='p', mentioned='m', practice='pr', details='d', rhythm='rh')
OFF = dt.timedelta(hours=-6)
DAY = dt.date(2030, 3, 4)
NOW_OVER = dt.datetime(2030, 3, 5, 9, 0)
NOW_NOON = dt.datetime(2030, 3, 4, 12, 0)
CONN = [dict(id='recP' + 'a' * 13, fields={'name': 'Wren Example', 'short name': 'wren', 'circle': ['Family']}),
        dict(id='recP' + 'b' * 13, fields={'name': 'Olu Example', 'short name': 'olu', 'circle': ['Friends', 'Work']}),
        dict(id='recP' + 'c' * 13, fields={'name': 'Me Example', 'short name': 'me', 'circle': ['Family']})]
ORDER = ['Family', 'Friends', 'Work']
PL1, PL2, PL3 = ('recL' + c * 13 for c in 'abc')
PLACES = [dict(id=PL1, fields={'place': 'the bakery', 'coordinates': '32.10, -98.10', 'added': '2030-03-04'}),
          dict(id=PL2, fields={'place': 'the library', 'coordinates': '32.20, -98.30'}),
          dict(id=PL3, fields={'place': 'home', 'coordinates': '32.00, -98.00'})]


def utc(h, m=0):
    """Her clock (UTC-6) on DAY, as the stream writes it."""
    return (dt.datetime.combine(DAY, dt.time(h, m)) - OFF).strftime('%Y-%m-%dT%H:%M:%S.000Z')


def row(rid, h, title, status='● log', end=None, person='', mentioned='', practice='📝 log', details='', rhythm=''):
    c = {'w': utc(*h), 's': status, 't': title, 'p': person, 'm': mentioned, 'pr': practice, 'd': details, 'rh': rhythm}
    if end:
        c['e'] = utc(*end)
    return dict(id=rid, createdTime=c['w'], cellValuesByFieldId=c)


ROWS = [
    row('r1', (8, 0), '🥐 breakfast at the bakery', end=(8, 45), person='♋ Me Example, ♑Wren', mentioned='Ana'),
    row('r2', (8, 0), '📍 the bakery', end=(9, 0), person='♑Wren', practice='📍 location', details=f'x\n———\n[be•do] place: {PL1}'),
    row('r3', (13, 0), '📍 the library', end=(15, 0), person='', practice='📍 location', details=f'[be•do] place: {PL2}'),
    row('r4', (13, 30), '📚 reading in the stacks', end=(14, 30), person='Olu (the librarian)'),
    row('r5', (13, 40), 'Screenshot of a sign', person=''),
    row('r6', (14, 0), '⚡ a be•do build', end=(14, 20), rhythm='be•do'),
    row('r7', (12, 20), '🚗 driving to the library', end=(12, 50), practice='🚗 driving'),
    row('r8', (17, 0), '⚡ call Olu about the trip', status='⬜ intention', person='Olu'),
    row('r9', (10, 0), '⚡ a step dropped', status='✖️ dropped', person='Ana Other'),
    row('r10', (19, 0), '📍 home', end=(22, 0), practice='📍 location', details=f'[be•do] place: {PL3}'),
]


def main():
    people = WW.People(CONN, ORDER)

    # ── the sociogram ──
    w = WW.who_of(ROWS, F, OFF, DAY, people, '♋ Me Example', (), NOW_OVER)
    names = [p['name'] for p in w['people']]
    assert 'Me Example' not in names and 'Me' not in names, 'she is never in her own sociogram'
    assert names[0] == 'Wren', names                     # family first, as the row writes the name, glyph off
    wren = w['people'][0]
    assert wren['circle'] == 'Family' and wren['n'] == 2, wren   # two lived rows shared
    assert wren['via'] == ['Ana'], 'who came up with them hangs off them'
    olu = next(p for p in w['people'] if p['name'] == 'Olu')
    assert olu['circle'] == 'Friends', 'the first circle listed wins'
    assert not olu.get('ahead'), 'once a lived row has them they are behind, not ahead'
    assert 'Ana Other' not in names, 'a dropped step is no one she met'
    assert w['order'] == ORDER

    # at noon the call with Olu is still ahead; with nobody lived yet, Olu is drawn ahead
    early = [r for r in ROWS if r['id'] in ('r1', 'r8')]
    w2 = WW.who_of(early, F, OFF, DAY, people, '♋ Me Example', (), NOW_NOON)
    olu2 = next(p for p in w2['people'] if p['name'] == 'Olu')
    assert olu2.get('ahead') and olu2['when'] == '5:00p', olu2
    # an event still to come brings its people, from the calendar it came from
    ev = [dict(k='event', t='swim', a='16:00', b='17:00', **{'with': ['♑Wren', 'Kit Stranger']})]
    w3 = WW.who_of([], F, OFF, DAY, people, '♋ Me Example', ev, NOW_NOON)
    assert {p['name'] for p in w3['people']} == {'Wren', 'Kit Stranger'} and all(p['ahead'] for p in w3['people'])
    assert next(p for p in w3['people'] if p['name'] == 'Kit Stranger')['circle'] == '', 'unknown: no circle yet'
    assert WW.who_of([], F, OFF, DAY, people, '', (), NOW_OVER) is None

    # ── where ──
    g = WW.where_of(ROWS, F, OFF, DAY, PLACES, (), NOW_OVER, me='♋ Me Example', skip_rhythms={'be•do'})
    st = g['stays']
    assert [s['name'] for s in st] == ['the library', 'the bakery'], 'longest first, home never a stay'
    lib, bak = st
    assert lib['hours'] == 2 and lib['at'] == '1:00p–3:00p'
    assert lib['did'] == 'reading in the stacks', 'what she did there; a screen clip and be•do work are not'
    assert bak['who'] == 'Wren' and bak['new'] and not lib['new'], 'a place added that day is new'
    assert g['road'] == 30
    assert g['placed'] == 2 and len(g['map']) == 2, 'two places with coordinates draw the map'
    assert all(0 <= d['x'] <= 1 and 0 <= d['y'] <= 1 for d in g['map'])
    north = max(g['map'], key=lambda d: -d['y'])
    assert st[north['i']]['name'] == 'the library', 'north is up'

    # a place the base doesn't hold keeps its row's name, and no map without two coordinates
    lone = [row('n1', (9, 0), '📍 a market stall', end=(9, 30), practice='📍 location', details='[be•do] place: new')]
    g2 = WW.where_of(lone, F, OFF, DAY, PLACES, (), NOW_OVER)
    assert g2['stays'][0]['name'] == 'a market stall' and g2['stays'][0]['new'] and g2['map'] is None

    # the calendar's places still ahead; a call is no place, and an event already over is not ahead
    sched = [dict(k='event', t='dentist', a='15:00', b='16:00', where='12 Example St'),
             dict(k='event', t='standup', a='13:00', b='13:30', where='https://zoom.example/j/1'),
             dict(k='event', t='coffee', a='09:00', b='10:00', where='the cafe')]
    g3 = WW.where_of([], F, OFF, DAY, PLACES, sched, NOW_NOON)
    assert [x['t'] for x in g3['going']] == ['dentist'] and g3['stays'] == []

    # a finished day with no stay was home, by the record; a day still going with nothing says nothing
    assert WW.where_of([], F, OFF, DAY, PLACES, (), NOW_OVER).get('home')
    assert WW.where_of([], F, OFF, DAY, PLACES, (), NOW_NOON) is None

    # ── the page draws both, ahead of the moved drives, and the fetch reads both tables by name ──
    eng = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()
    for sid in ('who', 'where'):
        assert f'<section class="{sid}" id="{sid}"></section>' in eng
        assert f'function {sid}()' in eng
    assert re.search(r"over\?\['three','today','spent','wheel','who','where'", eng), 'a finished day: who and where under the wheel'
    fetch = open(os.path.join(HERE, '..', '..', 'bedo-look-behind', 'scripts', 'bedo_fetch.py'), encoding='utf-8').read()
    assert "for name in ('connections', 'places'):" in fetch and "named_{name}.json" in fetch
    flow_src = open(os.path.join(HERE, '..', 'scripts', 'flow.py'), encoding='utf-8').read()
    assert "data['who'], data['where'] = who_where_of(" in flow_src
    print('who and where: ok')


if __name__ == '__main__':
    main()
