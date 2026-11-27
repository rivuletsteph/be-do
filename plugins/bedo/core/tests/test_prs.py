# -*- coding: utf-8 -*-
"""Open pull requests come back to her with an age and one recommendation (27 Nov 2026, her words: each of those
merges needed to happen for a reason). Every name below is an obvious invention.

    python3 core/tests/test_prs.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_prs as P  # noqa: E402

TODAY = dt.date(2026, 3, 20)
PRS = [dict(number=7, title='Snack row on the page', created_at='2026-03-19T10:00:00Z', mergeable_state='clean'),
       dict(number=3, title='Old map fix', created_at='2026-03-06T10:00:00Z', mergeable_state='dirty'),
       dict(number=5, title='Gate photos', created_at='2026-03-12T10:00:00Z')]


class Prs(unittest.TestCase):
    def test_oldest_first_with_age_and_one_recommendation(self):
        rs = P.rows(PRS, TODAY)
        self.assertEqual([r['n'] for r in rs], [3, 5, 7])
        self.assertEqual(rs[0]['age'], 14)
        self.assertEqual(rs[0]['rec'], 'bring it onto main, then merge')   # a clash is brought in, never closed by default
        self.assertEqual(rs[1]['rec'], 'merge')                           # an unknown state is read as mergeable
        self.assertFalse(rs[2]['stranded'])                              # a day old is not yet stranded

    def test_the_report_counts_the_stranded_and_never_proposes_close(self):
        out = P.report(P.rows(PRS, TODAY))
        self.assertTrue(out.startswith('prs    3 open, 2 waiting more than a day'))
        self.assertIn('#3 Old map fix · 14 d · clashes with main → bring it onto main, then merge?', out)
        self.assertNotIn('close?', out)
        self.assertEqual(P.report([]), 'prs    none open')


if __name__ == '__main__':
    unittest.main()
