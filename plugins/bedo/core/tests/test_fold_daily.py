# -*- coding: utf-8 -*-
"""The daily fold's list (23 Nov 2026, her words: it would be nice if we could get
into a daily amendment fold), on invented rows, no network: what main already
holds is marked, the new rows and the oldest of the backlog are built, and the
count comes first so each run can say how far the pile went down.

    python3 core/tests/test_fold_daily.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_rules as R  # noqa: E402

TODAY = '2026-03-13'
CODE = next(iter(R.CHECKS))
OLD = [(f'o{i:02d}', f'2026-01-{i + 10}', f'old rule {i}') for i in range(12)]
NEW = [('n1', '2026-03-12', 'a rule from yesterday'), ('n2', '2026-03-07', 'a rule from last week')]
IN = [('c1', '2026-02-01', 'a rule the code checks'), ('j1', '2026-02-02', 'a rule the judgment file holds')]
QUEST = ('q', '2026-01-02', 'the ten mini-quests')
MAP = {'c1': [CODE], 'j1': ['judgment'], 'o03': ['no.such.check']}


def made(rows, **kw):
    return R.daily_fold(sorted(rows, key=lambda a: a[1]), MAP, TODAY, ['ten mini-quests'], **kw)


class DailyFold(unittest.TestCase):
    def test_what_has_landed_is_marked_and_the_rest_is_built(self):
        f = made(OLD + NEW + IN + [QUEST])
        self.assertEqual([r['id'] for r in f['mark']], ['c1', 'j1'])
        self.assertEqual([r['id'] for r in f['new']], ['n2', 'n1'])              # the last week, oldest first
        self.assertEqual([r['id'] for r in f['backlog']], ['o00', 'o01', 'o02', 'o03', 'o04'])   # a few a day
        self.assertEqual((f['waiting'], f['active'], f['kept']), (7, 16, 1))

    def test_the_quest_row_is_never_listed(self):
        f = made([QUEST] + IN)
        self.assertNotIn('q', [r['id'] for k in ('mark', 'new', 'backlog') for r in f[k]])

    def test_a_check_the_code_lacks_has_not_landed(self):
        self.assertIn('o03', [r['id'] for r in made(OLD)['backlog']])

    def test_the_pile_goes_down_run_by_run(self):
        rows, days = list(OLD), 0
        while made(rows)['backlog']:                       # each run builds its share; they leave the list
            done = {r['id'] for r in made(rows)['backlog']}
            rows = [a for a in rows if a[0] not in done]
            days += 1
        self.assertEqual(days, 3)

    def test_a_long_list_to_mark_is_spread_over_days(self):
        many = [(f'm{i:02d}', '2026-02-01', 'landed') for i in range(14)]
        global MAP
        keep, MAP = MAP, {a[0]: ['judgment'] for a in many}
        try:
            f = made(many)
        finally:
            MAP = keep
        self.assertEqual((len(f['mark']), f['mark_later']), (10, 4))

    def test_what_a_run_built_waits_for_its_pull_request_and_is_never_built_twice(self):
        global MAP
        keep, MAP = MAP, dict(MAP, n1=['judgment', 'pr:41'], o00=[CODE, 'pr:41'])
        try:
            f = made(OLD + NEW + IN)
            lines = R.daily_fold_lines(f)
            paper = R.on_paper([NEW[0]], MAP)
        finally:
            MAP = keep
        self.assertEqual([(r['id'], r['pr']) for r in f['pending']], [('o00', '41'), ('n1', '41')])
        waiting = {r['id'] for k in ('mark', 'new', 'backlog') for r in f[k]}
        self.assertFalse({'n1', 'o00'} & waiting)                  # neither marked nor built again
        self.assertIn('2 built and waiting on a pull request', lines[0])
        self.assertTrue(any(x.endswith('→ pull request 41') for x in lines))
        self.assertEqual(paper[0][3], 'built, waiting on pull request 41')   # still on paper until she accepts it

    def test_the_count_comes_first(self):
        lines = R.daily_fold_lines(made(OLD + NEW + IN))
        self.assertEqual(lines[0], 'fold   16 active: 2 landed and not yet marked, 14 still to build')
        self.assertTrue(any(x.startswith('  c1 · 02-01 · a rule the code checks → in code') for x in lines))
        self.assertTrue(any('7 wait their turn' in x for x in lines))

    def test_an_empty_backlog_is_one_line(self):
        self.assertEqual(R.daily_fold_lines(made([QUEST])), ['fold   nothing active: the backlog is empty'])


if __name__ == '__main__':
    unittest.main()
