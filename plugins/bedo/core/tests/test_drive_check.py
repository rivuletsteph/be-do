# -*- coding: utf-8 -*-
"""The drive check (10 Nov 2026): effort with no drive, drives with no goal or date.
Every name is invented.

    python3 plugins/bedo/core/tests/test_drive_check.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_drive_check as C  # noqa: E402

RF = C.RF


def bucket(rid, name, typ, code='', goal='', target=None, open_ended=False, status='active'):
    return dict(id=rid, cellValuesByFieldId={RF['name']: name, RF['type']: {'name': typ}, RF['code']: code,
                RF['status']: {'name': status}, RF['goal']: goal, RF['target']: target, RF['open_ended']: open_ended})


RHYTHMS = [
    bucket('r1', 'Garden & House', C.RHYTHM, 'R1'),
    bucket('r4', 'Paid Work', C.RHYTHM, 'R4'),
    bucket('d1', 'Garden beds', C.DRIVE, 'D1', goal='Build two raised beds.\n———\n[be•do] note', target='2026-12-01'),
    bucket('d2', 'River report', C.DRIVE, 'D2', goal='Finish the river report.'),                 # no date
    bucket('d3', 'Someday boat', C.DRIVE, 'D3', goal='', open_ended=True),                        # no goal, open-ended
    bucket('d4', 'Old drive', C.DRIVE, 'D4', goal='x', target='2026-11-01'),                      # date passed
    bucket('d5', 'Budget setup', C.DRIVE, 'D5', goal='Set up the budget.', target='2026-12-31'),
    bucket('d9', 'Gone', C.DRIVE, 'D9', status='dropped'),
]
T = dt.date(2026, 11, 10)


def row(i, title, rhythm, status='✅ done', mins=0, practice='⚡ action', target=None, how=None):
    return dict(id=f'rec{i}', title=title, rhythm=rhythm, status=status, practice=practice, min=mins,
                target=target, how=how, datetime='2026-11-09T15:00:00.000Z')


class Unfinished(unittest.TestCase):
    def setUp(self):
        rows = [row(1, 'Draft the methods', 'River report', '⬜ intention', target='2026-11-20'),
                row(2, 'Pull the gauge data', 'D2 River report', '✅ done')]
        self.rep = C.run(RHYTHMS, rows, T)
        self.by = {x['code']: x for x in self.rep['unfinished']}

    def test_goal_above_the_divider_counts(self):
        self.assertNotIn('D1', self.by)

    def test_no_date_and_its_rows_propose_one(self):
        x = self.by['D2']
        self.assertTrue(x['no_date'])
        self.assertFalse(x['no_goal'])
        self.assertEqual(x['latest_open_target'], '2026-11-20')
        self.assertEqual((x['open'], x['rows']), (1, 2))          # 'D2 River report' resolves by code

    def test_open_ended_needs_no_date_but_still_a_goal(self):
        x = self.by['D3']
        self.assertFalse(x['no_date'])
        self.assertTrue(x['no_goal'])

    def test_a_passed_date_is_named(self):
        self.assertTrue(self.by['D4']['past_date'])

    def test_only_active_drives(self):
        self.assertNotIn('D9', self.by)
        self.assertEqual(self.rep['drives'], 5)


class Undriven(unittest.TestCase):
    def test_long_work_on_a_bare_rhythm_is_flagged(self):
        rows = [row(1, 'Model runs for the bay', 'Paid Work', '● log', 45, practice='💻 work'),
                row(2, '⚡ Quick note to the team', 'Paid Work', '✅ done', 10)]
        rep = C.run(RHYTHMS, rows, T, work=('Paid Work',))
        self.assertEqual([r['id'] for r in rep['long']], ['rec1'])

    def test_tending_is_left_alone(self):
        rows = [row(1, '⚡ Clean the kitchen and the dishes', 'Garden & House', '✅ done', 50),
                row(2, '⚡ Shelves for the garage', 'Garden & House', '✅ done', 50, how='tend')]
        self.assertEqual(C.run(RHYTHMS, rows, T)['long'], [])

    def test_grow_on_a_bare_rhythm_is_always_flagged(self):
        rows = [row(1, 'Shelves for the garage', 'Garden & House', '● log', 40, practice='🔨 building', how='grow')]
        self.assertEqual(len(C.run(RHYTHMS, rows, T)['long']), 1)

    def test_on_a_drive_is_fine(self):
        rows = [row(1, 'Model runs for the bay', 'River report', '● log', 90)]
        self.assertEqual(C.run(RHYTHMS, rows, T)['long'], [])

    def test_recurring_toward_one_end_names_the_drive_it_matches(self):
        rows = [row(i, t, 'Garden & House', '⬜ intention') for i, t in enumerate(
            ['⚡ Budget categories for the house', '⚡ Line out the budget', '⚡ Budget weekly recap'])]
        rep = C.run(RHYTHMS, rows, T)
        self.assertEqual([(g['word'], g['n'], g['drive']) for g in rep['recurring']], [('budget', 3, 'Budget setup')])

    def test_household_names_dont_make_an_end(self):
        rows = [row(i, f'⚡ {t} with Kit', 'Garden & House', '⬜ intention') for i, t in enumerate(['Bake', 'Paint', 'Swim'])]
        self.assertEqual(C.run(RHYTHMS, rows, T, skip=frozenset({'kit'}))['recurring'], [])


class Unknown(unittest.TestCase):
    def test_a_renamed_bucket_is_named(self):
        rep = C.run(RHYTHMS, [row(1, 'x', 'House and Garden'), row(2, 'y', 'House and Garden')], T)
        self.assertEqual(rep['unknown'], [('House and Garden', 2)])


class Minutes(unittest.TestCase):
    def test_span_and_seconds(self):
        self.assertEqual(C.minutes(dict(datetime='2026-11-09T15:00:00Z', end='2026-11-09T15:45:00Z'), None), 45)
        self.assertEqual(C.minutes(dict(time_spent=1800), None), 30)
        self.assertEqual(C.minutes(dict(time_spent=43200), None), 0)        # a 12-hour plan row is not effort


if __name__ == '__main__':
    unittest.main()
