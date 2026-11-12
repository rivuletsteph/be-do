# -*- coding: utf-8 -*-
"""The weekly fold's list, on invented rows, no network.

    python3 plugins/bedo/close/tests/test_fold.py
"""
import os, sys, unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'core'))
import bedo_rules as R  # noqa: E402

FIRST, LAST = '2026-11-01', '2026-11-07'
NEW = ('a', '2026-11-03', 'a new rule')
OLD = [(f'o{i}', f'2026-10-{i + 10}', f'old rule {i}') for i in range(12)]
QUEST = ('q', '2026-11-02', 'the ten mini-quests')


def made(rows, mapping=None, week=45, recheck=5):
    return R.fold_list(rows, mapping, FIRST, LAST, week, ['ten mini-quests'], recheck)


class Fold(unittest.TestCase):
    def test_the_week_is_listed_and_the_quest_row_never_is(self):
        f = made([NEW, QUEST] + OLD)
        self.assertEqual([r['id'] for r in f['this_week']], ['a'])
        self.assertNotIn('q', [r['id'] for r in f['this_week'] + f['recheck']])

    def test_a_row_dated_after_the_week_waits(self):
        f = made([('z', '2026-11-08', 'next week')])
        self.assertEqual((f['this_week'], f['recheck'], f['rolling']), ([], [], 0))

    def test_where_it_landed_is_read_from_the_mapping(self):
        code = next(iter(R.CHECKS))
        self.assertIn('in code', R.landed('a', {'a': [code]}))
        self.assertIn('judgment', R.landed('a', {'a': ['judgment']}))
        self.assertIn('not landed', R.landed('a', {}))
        self.assertIn('lacks', R.landed('a', {'a': ['no.such.check']}))

    def test_the_older_rows_stay_short_and_every_one_comes_round(self):
        f = made(OLD)
        self.assertEqual((len(f['recheck']), f['rolling']), (5, 7))
        seen = {r['id'] for w in range(45, 57) for r in made(OLD, week=w)['recheck']}
        self.assertEqual(len(seen), len(OLD))

    def test_nothing_older_is_no_trouble(self):
        self.assertEqual(made([NEW])['rolling'], 0)

    def test_one_line_each(self):
        lines = R.fold_lines(made([NEW] + OLD))
        self.assertIn('1 this week', lines[0])
        self.assertTrue(any('a new rule → not landed' in x for x in lines))


if __name__ == '__main__':
    unittest.main()
