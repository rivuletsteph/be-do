# -*- coding: utf-8 -*-
"""Always-synergy pairs (facts synergy.always, 4 and 21 Nov 2026) and the screen-time split hint.
Every row is invented.

    python3 plugins/bedo/core/tests/test_always_synergy.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_dayqa as Q  # noqa: E402
import bedo_entry as E  # noqa: E402
import bedo_fill as FL  # noqa: E402

DAY = dt.date(2026, 11, 21)


def z(h, m=0):
    return (dt.datetime.combine(DAY, dt.time(h, m)) + dt.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:00.000Z')


def row(practice, a, b, **kw):
    r = {'practice': practice, 'title': practice, 'datetime': z(*a), 'end': z(*b), 'status': '◉ done',
         'device': '🚫 none', 'wellness': '🧠 mind', 'id': practice}
    r.update(kw)
    return r


def notes(r, others):
    return [x for x in E.notes(r, FL.Context(local={}, day_rows=[r] + others)) if 'two things' in x]


class Always(unittest.TestCase):
    def test_morning_movement_with_sun_is_synergy_never_asked(self):
        mv, sun = row('🤸🏻‍♀️ morning movement', (7, 0), (7, 10)), row('🔅 morning sun', (7, 5), (7, 20))
        for r, o in ((mv, sun), (sun, mv)):
            n = notes(r, [o])
            self.assertEqual(len(n), 1, n)
            self.assertIn('always synergy', n[0])
            self.assertIn('overlap — synergizing with', n[0])
            self.assertNotIn('?', n[0])

    def test_journal_with_a_walk_is_synergy(self):
        n = notes(row('📒 journal', (8, 0), (8, 20)), [row('🚶‍♀️ walking', (8, 5), (8, 30))])
        self.assertIn('always synergy', n[0])

    def test_other_pairs_are_still_asked(self):
        n = notes(row('📼 video', (16, 0), (16, 30)), [row('🧎‍♀️ hip exercises', (16, 5), (16, 15))])
        self.assertEqual(len(n), 1)
        self.assertIn('ask in this reply', n[0])

    def test_qa_fills_it_and_asks_nothing(self):
        out = Q.synergy([row('🤸🏻‍♀️ morning movement', (7, 0), (7, 10)), row('🔅 morning sun', (7, 5), (7, 20))], -6)
        self.assertEqual([i['kind'] for i in out], ['fill'])
        self.assertIn('overlap — synergizing with', out[0]['note'])

    def test_no_shared_minutes_no_note(self):
        self.assertEqual(notes(row('🔅 morning sun', (7, 30), (7, 40)), [row('🤸🏻‍♀️ morning movement', (7, 0), (7, 10))]), [])


class ScreenTime(unittest.TestCase):
    def test_navigation_without_a_partial_split_gets_a_hint(self):
        r = {'practice': '📱 screen time', 'title': '5h 10m', 'details': 'maps 1h 20m on the drive'}
        self.assertTrue(E.screen_time_notes(r))
        r['details'] += ' · focused 3h 50m · partial 1h 20m'
        self.assertEqual(E.screen_time_notes(r), [])
        self.assertEqual(E.screen_time_notes({'practice': '📱 screen time', 'details': 'just reading'}), [])


if __name__ == '__main__':
    unittest.main()
