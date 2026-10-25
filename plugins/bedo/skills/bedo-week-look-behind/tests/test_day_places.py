# -*- coding: utf-8 -*-
"""Where she was (the day behind's map card), over an invented day.

Checks the rules of 25 Oct 2026 (scripts/day_places.py): a 📍 row is a stop; a
Timeline stop named in a row's details is a stop, with its address; calendar
times and estimates are not; the time between two drives is a stop named by
the drives, or a walk when she was walking; the same visit found twice is one;
the catalog names work by its street address and marks a place on her list as
reached; a loose word never matches a catalog place; people and what happened
sit at the stop they belong to.

Every name below is an obvious invention. Times are UTC; the day is UTC-5.

    python3 tests/test_day_places.py
"""
import datetime as dt, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
from day_places import day_places, label  # noqa: E402

L = {'utc_offset_hours': -5, 'self_person': '☀️ Wren'}
DAY = dt.date(2026, 3, 4)
CATALOG = [
    {'id': 'recWORK', 'place': 'work', 'standing': 'been', 'where': '400 Sample Ave, Testville'},
    {'id': 'recLIST', 'place': 'Pretend Falls Park', 'standing': 'want to go', 'where': 'north of Testville'},
    {'id': 'recWALK', 'place': 'Fable Lake floating boardwalk', 'standing': 'want to go', 'where': 'Fable Lake'},
]


def row(p, a, b=None, **kw):
    def utc(x):
        h, m = map(int, x.split(':'))
        return (dt.datetime.combine(DAY, dt.time(h, m)) + dt.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return dict(practice=p, title=kw.pop('title', p), when=utc(a), end=utc(b) if b else None,
                status=kw.pop('status', '● log'), **kw)


ROWS = [
    row('📝 log', '07:30', '08:00', title='a slow morning', person='☀️ Wren, 🐢 Pip'),
    row('🚗 driving', '08:30', '08:40', title='🚗 drive to work',
        details='———\n[be•do] From her Timeline screenshot: 2.5 mi, 8:30–8:40 AM, from home.'),
    row('⚡ action', '09:00', '10:00', title='the report', person='Ada Example'),
    row('🚗 driving', '11:50', '12:00', title='🚗 drive to Make-Believe Diner for lunch',
        details='[be•do] From her Timeline screenshot: 1.2 mi, 11:50–11:55 AM, then windowside pickup at '
                'Make-Believe Diner 11:55–12:00 PM.'),
    row('🍽️ lunch', '12:05', '12:40', title='🍽️ lunch at Pretend Falls Park', person='🐢 Pip',
        details='So nice.\n———\n[be•do] Times from her Timeline: Pretend Falls Park, 12 Falls Rd, Testville, 12:05–12:40 PM.\n'
                '[be•do] Times from the calendar (Lunch Club, 12:00–1:00 PM); about 12:00–12:30 PM, ESTIMATED.'),
    row('✨ glimmer', '12:20', title='✨ ducks on the falls', person='🐢 Pip'),
    row('🚗 driving', '12:45', '13:00', title='🚗 drive from the park to the trail',
        details='[be•do] From her Timeline screenshot: 4 mi, 12:45–1:00 PM.'),
    row('🚶‍♀️ walking', '13:00', '13:50', title='🚶‍♀️ walking on the Imaginary Trail',
        details='[be•do] From her Timeline: one walk, 2.1 mi, 1:00–1:50 PM.'),
    row('🚗 driving', '13:55', '14:05', title='🚗 drive back to work', details='3 mi.'),
    row('📍 location', '14:05', '17:00', title='📍 400 Sample Ave — the office, all afternoon',
        details='[be•do] From Timeline. 400 Sample Ave, Testville.'),
    row('🚗 driving', '17:00', '17:20', title='🚗 drive home, a stop for milk',
        details='[be•do] From her Timeline screenshot: 3.1 mi, 5:00–5:20 PM, work to home.'),
    row('⭐ highlight', '18:00', title='⭐ dinner on the porch', person='🐢 Pip, Ada Example'),
    row('🗺️ map check', '21:00', title='map check',
        details='> Home · 5:20 PM – Now\n> Driving 3.1 mi · 20 min · 5:00–5:20 PM'),
    row('🍳 dinner prep', '17:30', '18:00', status='⨂ skipped'),
]

P = day_places(ROWS, DAY, L, CATALOG, not_lived={'⨂ skipped'})
S = P['stops']
N = [s['n'] for s in S]
clock = lambda m: f'{m // 60}:{m % 60:02d}' if m is not None else None   # noqa: E731

assert N == ['home', 'work', 'Make-Believe Diner', 'Pretend Falls Park', 'walking on the Imaginary Trail', 'work', 'home'], N

home0, work, diner, park, walk, office, home1 = S
assert (home0['a'], clock(home0['b'])) == (None, '8:30'), home0         # the first drive left from home
assert home0['did'] == [] and home0['who'] == ['🐢 Pip'], home0         # at home only what stood out; never herself
assert (clock(work['a']), clock(work['b'])) == ('8:40', '11:50'), work  # between two drives, named by the first
assert work['place']['id'] == 'recWORK' and work['src'] == 'drives'          # 'work' is a catalog place
assert work['who'] == ['Ada Example'] and work['did'] == [['⚡', 'the report']], work
assert (clock(diner['a']), clock(diner['b'])) == ('11:55', '12:00'), diner   # 'then … at X' inside a drive's details
assert park['addr'] == '12 Falls Rd, Testville', park                    # the Timeline line's address, as written
assert (clock(park['a']), clock(park['b'])) == ('12:05', '12:40'), park  # not the calendar's or the estimate's times
assert park['place'] == {'id': 'recLIST', 'standing': 'want to go'}, park    # a place on her list, reached
assert park['did'][0] == ['✨', 'ducks on the falls'], park['did']       # moments first
assert walk['move'] == '🚶‍♀️' and walk['mi'] == 2.1 and walk['place'] is None, walk   # a walk, not the boardwalk
assert walk['did'] == [], walk
assert office['n'] == 'work' and office['src'] == '📍' and office['place']['id'] == 'recWORK', office   # by street
assert (clock(office['a']), clock(office['b'])) == ('14:05', '17:00'), office
assert (clock(home1['a']), home1['b']) == ('17:20', None), home1        # 'Home · 5:20 PM – Now' is no range; the drive says home
assert home1['did'] == [['⭐', 'dinner on the porch']], home1

assert len(P['legs']) == 5 and [lg['mi'] for lg in P['legs']] == [2.5, 1.2, 4.0, 3.0, 3.1], P['legs']
assert P['totals'] == {'places': 3, 'miles': 13.8, 'drive_min': 65, 'drives': 5}, P['totals']
assert P['unknown'] == ['Make-Believe Diner'], P['unknown']              # for her to name; nothing is added

# labels: what is a place and what isn't
assert label('[be•do] From her Timeline: Some Cafe, 5 Elm St, Testville,') == ('Some Cafe', '5 Elm St, Testville')
assert label('Her Timeline has a stop at the Shell in Fakeburg,') == ('the Shell in Fakeburg', '')
assert label('drove 10:49, rec center') == ('rec center', '')
for not_a_place in ('[be•do] From her Timeline,', 'Time ESTIMATED FROM CONTEXT, about', 'working stretch Mon 2 Mar',
                    '11 mi to Some Cafe in Testville,', 'Her Timeline and Day Behind screenshots at', ', home, walk'):
    assert label(not_a_place) is None, not_a_place

# a day with no drives and no places draws no card
assert day_places([row('📝 log', '09:00', '10:00')], DAY, L)['stops'] == []
print('ok — day places')
