# -*- coding: utf-8 -*-
"""The week look behind's clock across the 1 Nov 2026 change: photos and the day's map read each
instant on its own clock, from time_zone, with the stale summer -5 left in the settings on purpose.

    python3 tests/test_clock_change.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'core'))
import day_photos  # noqa: E402
import day_map  # noqa: E402
import week_look_behind as W  # noqa: E402

L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -5}


class Clock(unittest.TestCase):
    def test_a_photo_on_each_side(self):
        self.assertEqual(day_photos.taken('PXL_20261031_140000000.jpg', L), dt.datetime(2026, 10, 31, 9))
        self.assertEqual(day_photos.taken('PXL_20261102_150000000.jpg', L), dt.datetime(2026, 11, 2, 9))

    def test_the_map_reads_a_stay_on_its_own_clock(self):
        self.assertEqual(day_map._local('2026-11-02T15:00:00.000Z', L), dt.datetime(2026, 11, 2, 9))
        self.assertEqual(day_map._local('2026-10-31T14:00:00.000Z', L), dt.datetime(2026, 10, 31, 9))

    def test_the_settings_need_a_zone_not_the_number(self):
        L2 = {'time_zone': 'America/Chicago', 'week_zero_sunday': '2026-09-13', 'week_zero_number': 38,
              'fields': {'stream': {k: 'f' + k for k in W.STREAM_KEYS}, 'rhythms': {k: 'r' + k for k in W.RHYTHM_KEYS}}}
        W.fields(L2)                                    # no utc_offset_hours: builds
        with self.assertRaises(SystemExit):
            W.fields({k: v for k, v in L2.items() if k != 'time_zone'})   # neither: stops

if __name__ == '__main__':
    unittest.main()
