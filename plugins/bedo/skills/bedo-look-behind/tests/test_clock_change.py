# -*- coding: utf-8 -*-
"""The look behind's clock across the 1 Nov 2026 change: each instant on the clock that held then,
from time_zone, with the stale summer -5 left in the settings on purpose.

    python3 tests/test_clock_change.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'core'))   # calendar_sync lives in the core (11 Nov 2026)
import look_behind as LB  # noqa: E402
import calendar_sync as CS  # noqa: E402
import bedo_common  # noqa: E402
import bedo_clock  # noqa: E402

L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -5}


class LookBehind(unittest.TestCase):
    def setUp(self):
        LB.CLOCK.clear()
        LB.CLOCK.update(L)

    def test_local_on_each_side(self):
        self.assertEqual(LB.local('2026-10-31T14:00:00.000Z'), dt.datetime(2026, 10, 31, 9))
        self.assertEqual(LB.local('2026-11-02T15:00:00.000Z'), dt.datetime(2026, 11, 2, 9))

    def test_no_offset_check_left_to_tell_her_to_edit_a_number(self):
        self.assertFalse(hasattr(bedo_common, 'offset_check'))
        self.assertFalse(hasattr(LB, 'offset_check'))


class CalendarSync(unittest.TestCase):
    def test_a_linked_row_lands_on_its_own_day(self):
        off = bedo_clock.Offset(L)
        late_sat = dict(event='x', when='2026-11-01T04:30:00.000Z', end=None)    # 11:30 PM Sat 31 Oct, CDT
        late_sun = dict(event='y', when='2026-11-02T05:30:00.000Z', end=None)    # 11:30 PM Sun 1 Nov, CST
        latest = {'a': late_sat, 'b': late_sun}
        self.assertEqual(CS.linked_for_day(latest, dt.date(2026, 10, 31), off), [late_sat])
        self.assertEqual(CS.linked_for_day(latest, dt.date(2026, 11, 1), off), [late_sun])


if __name__ == '__main__':
    unittest.main()
