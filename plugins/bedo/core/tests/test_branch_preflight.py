# -*- coding: utf-8 -*-
"""A branch's own preflight (12 Nov 2026). Thirteen branches opened in one day:
each was handed the my day title, the whole list of rules on paper, and a rule
that it must not write to the stream, so the my day chat spent most of its
turns writing other chats' rows. Her words that night: I don't mind having
multiple branches open as long as they close when the objective is met or at
the end of the day … yes, branches write their own rows.

    python3 core/tests/test_branch_preflight.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_preflight as P  # noqa: E402

UTC = dt.timezone.utc
L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -5, 'weekly_name': 'w{n} be•do'}
NOW = dt.datetime(2026, 11, 12, 18, 40, tzinfo=UTC)              # Thu 12 Nov, 12:40p
ROWS = [{'datetime': '2026-11-12T18:30:00.000Z'}]
NAMES = {'w46 be•do': 'appXXXXXXXXXXXXXX'}
AM = [{'id': 'recPAPER', 'decision': 'a rule nothing checks', 'date': '2026-11-01'}]


class BranchPreflight(unittest.TestCase):
    def test_the_title_is_numbered_in_the_order_it_opened(self):
        self.assertEqual(P.branch_name(dt.date(2026, 11, 12), 4, '👁️ my day page'),
                         '▶️↳1112.4 🌳 Thu 👁️ my day page')

    def test_no_number_is_said_never_guessed(self):
        text, stop = P.report(L, NAMES, ROWS, NOW, kind='branch', what='🧹 drive cleanup')
        first = text.splitlines()[0]
        self.assertIn('↳1112.?', first)
        self.assertIn('bedo:1112', text)                          # where the number comes from
        self.assertFalse(stop)

    def test_a_branch_gets_the_clock_and_the_base_and_its_two_lines(self):
        text, _ = P.report(L, NAMES, ROWS, NOW, kind='branch', n=4, what='👁️ my day page', amendments=AM)
        lines = text.splitlines()
        self.assertEqual(lines[0], '▶️↳1112.4 🌳 Thu 👁️ my day page')
        self.assertIn('12:40 local (UTC-6)', lines[1])            # the zone, not the stale -5
        self.assertTrue(lines[2].startswith('base   w46'))
        self.assertTrue(any(l.startswith('writes ') and 'entry --chat 1112' in l for l in lines))
        self.assertTrue(any(l.startswith('closes ') for l in lines))

    def test_a_branch_is_not_handed_the_days_lists(self):
        text, _ = P.report(L, NAMES, ROWS, NOW, kind='branch', n=4, what='x', amendments=AM)
        for word in ('rule on paper', 'due    ', 'first  ', 'quest  ', 'my day page is'):
            self.assertNotIn(word, text)

    def test_the_my_day_chat_is_unchanged(self):
        text, _ = P.report(L, NAMES, ROWS, NOW, amendments=AM)
        self.assertIn('my day', text.splitlines()[0])
        self.assertIn('rule on paper', text)
        self.assertNotIn('writes ', text)


if __name__ == '__main__':
    unittest.main(verbosity=1)
