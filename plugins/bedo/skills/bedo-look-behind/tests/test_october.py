# -*- coding: utf-8 -*-
"""October amendments on the day page. Every row is invented.

  · 🔭 a forecast due on the day is listed, on the page and in the QA (20 Oct)

    python3 tests/test_october.py
"""
import os, sys, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_rules_9oct import CFD, DAY, RFD, SF, Fixture, iso  # noqa: E402

SFT = dict(SF, target='fldTarget')


class Forecasts(unittest.TestCase):
    def test_a_forecast_due_today_is_listed(self):
        f = Fixture(); f.whole_day()
        f.row('💡 insight', iso(600, DAY.replace(day=1)), title='forecast: the bridge opens by the 8th')
        f.rows[-1]['cellValuesByFieldId']['fldTarget'] = iso(1000)
        f.row('💡 insight', iso(600, DAY.replace(day=1)), title='forecast: snow in January')
        f.rows[-1]['cellValuesByFieldId']['fldTarget'] = '2027-01-29T23:00:00.000Z'
        r, D = f.build({'fields': {'stream': SFT, 'rhythms': RFD, 'connections': CFD}})
        self.assertIsNotNone(D, r.stderr)
        self.assertEqual(D['forecasts'], [{'t': 'forecast: the bridge opens by the 8th'}])
        self.assertIn('how it turned out', r.stdout)
        self.assertNotIn('snow in January', r.stdout)

    def test_no_forecast_no_section(self):
        f = Fixture(); f.whole_day()
        r, D = f.build()
        self.assertEqual(D['forecasts'], [])


if __name__ == '__main__':
    unittest.main()
