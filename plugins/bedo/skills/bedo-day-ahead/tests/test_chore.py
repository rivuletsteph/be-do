# -*- coding: utf-8 -*-
"""The look ahead plants one chore for her son each morning (11 Oct 2026).
Every event and name is invented.

    python3 tests/test_chore.py
"""
import datetime as dt, os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import day_ahead as DA  # noqa: E402

L = {'self_calendar': 'you', 'child_calendar': 'Kid'}
DAY = dt.date(2026, 10, 27)


def ev(who, title, h, location='', allday=False, day=DAY):
    a = dt.datetime.combine(day, dt.time(h))
    return dict(who=who, title=title, a=a, b=a + dt.timedelta(hours=2), allday=allday, location=location)


class Chore(unittest.TestCase):
    def test_one_chore_every_morning(self):
        c = DA.chore_for(DAY, [], L)
        self.assertEqual(c['kid'], 'Kid')
        self.assertIn(c['text'], DA.CHORES)
        self.assertNotEqual(c['text'], DA.chore_for(DAY + dt.timedelta(days=1), [], L)['text'])   # it turns

    def test_an_outing_is_help_packing_for_it(self):
        c = DA.chore_for(DAY, [ev('you', 'the dentist', 9, 'a clinic'), ev('Kid', 'the park picnic', 14, 'the park')], L)
        self.assertEqual(c['text'], 'help pack for the dentist')
        c = DA.chore_for(DAY, [ev('Sam', 'his trip', 9, 'the airport'), ev('you', 'a call', 10)], L)
        self.assertIn(c['text'], DA.CHORES)                                  # someone else's outing, or no place

    def test_her_own_list_wins(self):
        self.assertEqual(DA.chore_for(DAY, [], dict(L, kid_chores=['sort the socks']))['text'], 'sort the socks')


if __name__ == '__main__':
    unittest.main()
