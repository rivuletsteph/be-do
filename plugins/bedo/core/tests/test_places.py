# -*- coding: utf-8 -*-
"""Where she was (5 Nov 2026): the day's stays as 📍 rows, the shape she said yes to.

Every place and person here is an invention. The day is UTC-5.

    python3 plugins/bedo/core/tests/test_places.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_places as P  # noqa: E402

DAY = dt.date(2026, 3, 4)
OFF = -5
PLACES = P.places_from([
    {'id': 'recOFFICEaaaaaaaa', 'createdTime': '', 'fields': {
        'place': 'the office', 'standing': 'been', 'google place id': 'ChIJabcdefghijk1234567',
        'coordinates': '30.100000, -97.200000'}},
    {'id': 'recPARKbbbbbbbbbb', 'createdTime': '', 'fields': {'place': 'Fern Park', 'standing': 'want to go'}},
])


class Stays(unittest.TestCase):
    def test_a_stay_becomes_one_row_named_by_its_place(self):
        p = P.propose([dict(place='Office', arrive='10:27', leave='15:30', google_place_id='ChIJabcdefghijk1234567',
                            who='Ivy Moss', words='the weekly')], PLACES, [], DAY, OFF, 'her Timeline screenshot at 10:07 PM')
        (r,) = p['write']
        self.assertEqual(r['title'], '📍 the office')          # her name for it, from the base
        self.assertEqual(r['practice'], '📍 location')
        self.assertEqual(r['status'], '● log')
        self.assertEqual((r['datetime'], r['end']), ('2026-03-04T15:27:00.000Z', '2026-03-04T20:30:00.000Z'))
        self.assertEqual(r['person'], 'Ivy Moss')
        self.assertTrue(r['details'].startswith('the weekly\n———\n[be•do] place: recOFFICEaaaaaaaa'))
        self.assertIn('from her Timeline screenshot at 10:07 PM', r['details'])
        self.assertNotIn('30.1', r['details'])                  # coordinates live only in the places base
        self.assertEqual(p['ask'], [])

    def test_the_whole_google_id_matches_never_a_prefix(self):
        near = dict(place='the furniture shop', arrive='12:00', leave='12:10', google_place_id='ChIJabcdefghijk1234999')
        p = P.propose([near], PLACES, [], DAY, OFF)
        self.assertIn('place: new', p['write'][0]['details'])
        self.assertEqual([x['place'] for x in p['ask']], ['the furniture shop'])

    def test_home_gets_no_row(self):
        p = P.propose([dict(place='Home', arrive='07:00', leave='10:20')], PLACES, [], DAY, OFF)
        self.assertEqual((p['write'], p['home']), ([], ['Home']))

    def test_a_new_place_is_written_and_asked_once(self):
        two = [dict(place='Poppy Sushi', arrive='12:00', leave='12:50'), dict(place='Poppy Sushi', arrive='18:00', leave='19:00')]
        p = P.propose(two, PLACES, [], DAY, OFF)
        self.assertEqual(len(p['write']), 2)
        self.assertEqual(len(p['ask']), 1)
        self.assertIn('Add it to your places?', p['ask'][0]['line'])

    def test_a_second_run_writes_nothing_twice(self):
        stay = dict(place='the office', arrive='10:27', leave='15:30')
        first = P.propose([stay], PLACES, [], DAY, OFF)['write'][0]
        again = P.propose([stay], PLACES, [dict(first, id='recROWccccccccccc')], DAY, OFF)
        self.assertEqual((again['write'], [x['id'] for x in again['already']]), ([], ['recROWccccccccccc']))

    def test_past_midnight_and_a_backwards_stay(self):
        p = P.propose([dict(place='Fern Park', arrive='23:30', leave='+00:30')], PLACES, [], DAY, OFF)
        self.assertEqual(p['write'][0]['end'], '2026-03-05T05:30:00.000Z')
        self.assertIn('no coordinates yet', p['write'][0]['details'])
        with self.assertRaises(SystemExit):
            P.propose([dict(place='Fern Park', arrive='14:00', leave='13:00')], PLACES, [], DAY, OFF)

    def test_the_map_reads_the_rows_back(self):
        rows = P.propose([dict(place='the office', arrive='10:27', leave='15:30')], PLACES, [], DAY, OFF)['write']
        rows.append(dict(practice='🍽️ lunch', title='lunch'))
        (s,) = P.stays_of(rows)
        self.assertEqual(s['place_ref'], 'recOFFICEaaaaaaaa')
        self.assertEqual(P.coords(PLACES[0]), (30.1, -97.2))
        self.assertIsNone(P.coords(PLACES[1]))


if __name__ == '__main__':
    unittest.main()
