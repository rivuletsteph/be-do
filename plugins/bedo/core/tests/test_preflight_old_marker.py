# -*- coding: utf-8 -*-
"""Preflight finds a day closed under the old QA wording (20 Nov 2026).

The dusk step was renamed 🔀 braid that day and its marker became `braid
shown`; the checks still accept `dayqa shown` for days closed before. But
preflight's Airtable search asked only for the new wording, so Thursday's
dusk close row (`dayqa shown 2026-11-19 07:28`) was never read and the morning
said yesterday wasn't finished when it was.

    python3 core/tests/test_preflight_old_marker.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_preflight as P  # noqa: E402

L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -6, 'weekly_name': 'w{n} be•do',
     'stream_table': 'tblSTREAM', 'stream_fields': {'datetime': 'fldDT', 'details': 'fldDE'}}


class FakeAir:
    def __init__(self):
        self.formulas = []

    def dump(self, base, table, by_id=True, formula=None, **kw):
        self.formulas.append(formula)
        return {'records': []}


class OldMarker(unittest.TestCase):
    def test_the_search_asks_for_both_wordings(self):
        air = FakeAir()
        names = {n: 'appXXXXXXXXXXXXXX' for n in P.bases_in_play(dt.date(2026, 11, 20), L)}
        P.read_log_rows(air, names, dt.date(2026, 11, 20), L)
        self.assertTrue(air.formulas)
        for f in air.formulas:
            self.assertIn("FIND('braid shown '", f)
            self.assertIn("FIND('dayqa shown '", f)


if __name__ == '__main__':
    unittest.main()
