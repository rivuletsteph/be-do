import datetime as dt, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bedo_remaining as R


class PassedSun(unittest.TestCase):
    steps = [{'practice': '🔅 morning sun'}, {'practice': '👁️ look ahead'}]

    def test_dropped_after_due(self):
        got = R.drop_passed_sun(self.steps, 7 * 60 + 57, dt.datetime(2026, 11, 11, 12, 0))
        self.assertEqual([s['practice'] for s in got], ['👁️ look ahead'])

    def test_kept_before_due(self):
        got = R.drop_passed_sun(self.steps, 7 * 60 + 57, dt.datetime(2026, 11, 11, 7, 30))
        self.assertEqual(len(got), 2)

    def test_kept_without_a_time(self):
        self.assertEqual(len(R.drop_passed_sun(self.steps, None, dt.datetime(2026, 11, 11, 12, 0))), 2)


if __name__ == '__main__':
    unittest.main()
