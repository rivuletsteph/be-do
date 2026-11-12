# -*- coding: utf-8 -*-
"""Oura's words on her clock across the 1 Nov 2026 change (backlog 261106_ouraclock: on 6 Nov the
morning plan said in bed 11:47 PM to 8:17 AM when it was 10:47 PM to 7:17 AM). The plan reads the
settings' time_zone per instant; the settings keep the stale summer -5 on purpose.

    python3 tests/test_clock_change.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import oura  # noqa: E402

F = dict(title='fT', when='fW', end='fE', status='fS', practice='fP', details='fD')
L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -5}
UTC = dt.timezone.utc


def night(day, start, end):
    return {'sleep': [{'day': day, 'type': 'long_sleep', 'bedtime_start': start, 'bedtime_end': end,
                       'time_in_bed': 30000, 'total_sleep_duration': 27000, 'efficiency': 88}]}


def said(O, day, off=L):
    P = oura.plan(O, [], [day], F, off, mode='morning', now=dt.datetime(2026, 12, 1, tzinfo=UTC))
    return next(c['fD'] for c in P['create'] if c['fP'] == '😴 sleep')


class Clock(unittest.TestCase):
    def test_a_night_before_the_change(self):
        O = night('2026-10-30', '2026-10-29T22:30:00-05:00', '2026-10-30T06:45:00-05:00')
        self.assertIn('in bed 10:30 PM to 6:45 AM', said(O, dt.date(2026, 10, 30)))

    def test_the_night_of_the_change_reads_each_end_on_its_own_clock(self):
        O = night('2026-11-01', '2026-10-31T23:00:00-05:00', '2026-11-01T07:00:00-06:00')
        self.assertIn('in bed 11:00 PM to 7:00 AM', said(O, dt.date(2026, 11, 1)))

    def test_a_night_after_the_change(self):
        O = night('2026-11-06', '2026-11-05T22:47:00-06:00', '2026-11-06T07:17:00-06:00')
        self.assertIn('in bed 10:47 PM to 7:17 AM', said(O, dt.date(2026, 11, 6)))
        self.assertIn('in bed 11:47 PM to 8:17 AM', said(O, dt.date(2026, 11, 6), -5))   # what the stale number said


if __name__ == '__main__':
    unittest.main()
