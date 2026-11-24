# -*- coding: utf-8 -*-
"""The day sweep (24 Nov 2026): rows go through the entry check whoever writes
them, so a day's rows are checked after the fact. What a rule deduces by itself
is be•do's to write in place; the rest is a call for her. A rule about the
moment of writing (the key the base fills on every row) is not asked of a row
already in the stream.

    python3 core/tests/test_sweep.py
"""
import datetime as dt, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_sweep as S  # noqa: E402

L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -6, 'weekly_name': 'w{n} be•do', 'self_person': 'Me'}
NOW = dt.datetime(2026, 3, 14, 3, 0, tzinfo=dt.timezone.utc)


def row(rid, **kw):
    r = dict(id=rid, created='2026-03-13T15:00:00.000Z', datetime='2026-03-13T15:00:00.000Z', end='2026-03-13T15:10:00.000Z',
             status='● log', practice='📝 log', title='A note', details='', wellness='💨 air',
             device='📱 phone', person='Pip Plum', key='260313_0900')
    r.update(kw)
    return r


class Sweep(unittest.TestCase):
    def test_a_row_with_no_practice_is_a_call(self):
        found = S.sweep([row('recA', practice=None)], L, now=NOW)
        self.assertEqual(len(found), 1)
        self.assertTrue(any(p.startswith('practice:') for p in found[0][2]), found)

    def test_a_status_the_base_does_not_carry_is_a_call(self):
        found = S.sweep([row('recB', status='done-ish')], L, now=NOW)
        self.assertTrue(any(p.startswith('status:') for p in found[0][2]), found)

    def test_the_key_the_base_fills_is_not_asked_of_a_written_row(self):
        for _, mine, hers in S.sweep([row('recC')], L, now=NOW):
            self.assertFalse([p for p in mine + hers if p.startswith('key: only an')])

    def test_what_a_rule_deduces_is_bedos_to_write(self):
        self.assertTrue(S._DEDUCED.match('person: empty → Pip Plum — at home'))
        self.assertTrue(S._DEDUCED.match('device: empty — deduced 🚫 none (a body practice)'))
        self.assertFalse(S._DEDUCED.match('practice: every row carries one'))

    def test_the_report_counts_and_names_each_row(self):
        found = S.sweep([row('recA', practice=None), row('recD', datetime='2026-03-13T16:00:00.000Z', end='2026-03-13T16:05:00.000Z')], L, now=NOW)
        out = S.report(found, 2, dt.date(2026, 3, 13), 'w11')
        self.assertIn('Fri 13 Mar: 2 rows in w11', out[0])
        self.assertTrue(any('recA' in l for l in out))
        self.assertIn('every one passes', S.report([], 2, dt.date(2026, 3, 13))[0])


if __name__ == '__main__':
    unittest.main()
