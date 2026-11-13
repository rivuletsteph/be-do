# -*- coding: utf-8 -*-
"""True times (12 Nov 2026). A branch chat read the clock an hour ahead (the
stale summer number, -5, where the zone said -6) and wrote 8:50a at 8:27a; her
words that day: it's 12:44 in the afternoon, and I just want this to work
right. Two rules, both in the entry check:

  the clock   is the zone, read at the row's own instant; the hand-kept number
              is never the truth while the zone can be read
  no future   a row for something that happened can't start or end later than
              now. A plan may

    python3 core/tests/test_true_times.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_entry as E  # noqa: E402

UTC = dt.timezone.utc
L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -5}   # the stale number, kept on purpose
NOW = dt.datetime(2026, 11, 12, 14, 27, tzinfo=UTC)            # 8:27a on the winter clock
LOG, INTENT = E.FACTS['status']['logs'][0], E.FACTS['status']['plans'][-1]


def z(t):
    return t.strftime('%Y-%m-%dT%H:%M:%S.000Z')


def has(problems, word):
    return any(word in p for p in problems)


class TrueTimes(unittest.TestCase):
    def test_a_time_an_hour_ahead_is_refused_and_the_clock_named(self):
        row = {'status': LOG, 'datetime': z(NOW + dt.timedelta(minutes=23))}   # 8:50a, written at 8:27a
        p = E.future_problems(row, L, NOW)
        self.assertEqual(len(p), 1)
        self.assertIn('the clock says Thu 12 Nov 08:27', p[0])       # the zone's clock, not the stale -5 (09:27)
        self.assertIn('08:50', p[0])

    def test_now_and_the_past_pass(self):
        for back in (0, 3, 600):
            self.assertEqual(E.future_problems({'status': LOG, 'datetime': z(NOW - dt.timedelta(minutes=back))}, L, NOW), [])
        # a minute or two ahead is the write racing the clock, not a made-up time
        self.assertEqual(E.future_problems({'status': LOG, 'datetime': z(NOW + dt.timedelta(minutes=4))}, L, NOW), [])

    def test_an_end_in_the_future_is_refused_too(self):
        row = {'status': LOG, 'datetime': z(NOW - dt.timedelta(minutes=30)), 'end': z(NOW + dt.timedelta(hours=1))}
        p = E.future_problems(row, L, NOW)
        self.assertEqual(len(p), 1)
        self.assertTrue(p[0].startswith('end:'))

    def test_a_plan_may_sit_ahead(self):
        for st in E.PLANS:
            self.assertEqual(E.future_problems({'status': st, 'datetime': z(NOW + dt.timedelta(days=3))}, L, NOW), [])

    def test_the_whole_check_carries_it(self):
        row = {'status': LOG, 'practice': '📝 log', 'title': 'x', 'datetime': z(NOW + dt.timedelta(hours=1))}
        self.assertTrue(has(E.problems(row, utc_offset_hours=L, now=NOW), 'later than now'))
        row['datetime'] = z(NOW - dt.timedelta(hours=1))
        self.assertFalse(has(E.problems(row, utc_offset_hours=L, now=NOW), 'later than now'))

    def test_the_settings_are_the_clock_not_the_number(self):
        # 10:50p to 11:10p Wed on the winter clock; the stale -5 reads it as crossing midnight
        late = dt.datetime(2026, 11, 12, 4, 50, tzinfo=UTC)
        row = {'status': LOG, 'practice': '📝 log', 'title': 'x', 'datetime': z(late), 'end': z(late + dt.timedelta(minutes=20))}
        self.assertEqual(E.span_problems(row, L), [])
        self.assertTrue(E.span_problems(row, -5))        # what the entry check used to be handed

    def test_with_no_clock_it_still_refuses(self):
        p = E.future_problems({'status': LOG, 'datetime': z(NOW + dt.timedelta(hours=2))}, None, NOW)
        self.assertTrue(has(p, 'later than now'))


if __name__ == '__main__':
    unittest.main(verbosity=1)
