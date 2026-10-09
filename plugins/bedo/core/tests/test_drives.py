# -*- coding: utf-8 -*-
"""Drives within drives: a row rolls up through `feeds` (9 Oct 2026).

A two-level chain — a grandchild drive feeding a child feeding a top drive —
and, beside it, two drives that feed each other. Every name is invented.

    python3 plugins/bedo/core/tests/test_drives.py
"""
import os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_drives as D  # noqa: E402

TOP, MID, LEAF = 'D10 — School year', 'D11 — Robot club', 'D12 — Robot arm'
LOOP_A, LOOP_B = 'D20 — Garden', 'D21 — Compost'
RHYTHMS = {
    TOP: dict(name=TOP, code='D10', feeds=[]),
    MID: dict(name=MID, code='D11', feeds=[{'id': 'rec1', 'name': TOP}]),   # a linked cell
    LEAF: dict(name=LEAF, code='D12', feeds='D11'),                          # by code, one value
    LOOP_A: dict(name=LOOP_A, feeds=[LOOP_B]),
    LOOP_B: dict(name=LOOP_B, feeds=[LOOP_A]),
    'D30 — Alone': dict(name='D30 — Alone'),
}
ROWS = [dict(drive=LEAF, min=30), dict(drive=LEAF, min=15), dict(drive=MID, min=60),
        dict(drive=TOP, min=10), dict(drive=LOOP_A, min=20), dict(drive=LOOP_B, min=5),
        dict(drive=None, min=99)]
W = lambda r: r['min']   # noqa: E731


class Chain(unittest.TestCase):
    def test_two_levels_up(self):
        self.assertEqual(D.chain(LEAF, RHYTHMS), [LEAF, MID, TOP])
        self.assertEqual(D.chain(TOP, RHYTHMS), [TOP])

    def test_loop_ends_where_it_closes(self):
        self.assertEqual(D.chain(LOOP_A, RHYTHMS), [LOOP_A, LOOP_B])
        self.assertEqual(D.chain(LOOP_B, RHYTHMS), [LOOP_B, LOOP_A])

    def test_loop_is_named(self):
        self.assertEqual([set(c) for c in D.loops(RHYTHMS)], [{LOOP_A, LOOP_B}])

    def test_unknown_and_self_feeds_are_dropped(self):
        r = dict(RHYTHMS, X=dict(name='X', feeds=['X', 'nowhere']))
        self.assertEqual(D.chain('X', r), ['X'])


class RollUp(unittest.TestCase):
    def setUp(self):
        self.rolled = D.roll_up(ROWS, RHYTHMS, weight=W)

    def test_row_counts_under_its_drive_and_every_drive_it_feeds(self):
        g = self.rolled
        self.assertEqual((g[LEAF]['own'], g[LEAF]['total'], g[LEAF]['n']), (45, 45, 2))
        self.assertEqual((g[MID]['own'], g[MID]['total'], g[MID]['n']), (60, 105, 3))
        self.assertEqual((g[TOP]['own'], g[TOP]['total'], g[TOP]['n'], g[TOP]['n_own']), (10, 115, 4, 1))

    def test_loop_counts_each_row_once_per_drive(self):
        g = self.rolled
        self.assertEqual((g[LOOP_A]['own'], g[LOOP_A]['total']), (20, 25))
        self.assertEqual((g[LOOP_B]['own'], g[LOOP_B]['total']), (5, 25))

    def test_grand_total_counts_each_row_once(self):
        on_a_drive = [r for r in ROWS if r['drive']]
        self.assertEqual(D.grand_total(on_a_drive, W), 140)
        # the per-drive totals overlap on purpose; their sum is not the total
        self.assertGreater(sum(g['total'] for g in self.rolled.values()), 140)

    def test_child_nests_under_parent_not_a_peer(self):
        forest = D.tree(self.rolled, RHYTHMS)
        roots = [n['name'] for n in forest]
        self.assertIn(TOP, roots)
        self.assertNotIn(MID, roots)
        self.assertNotIn(LEAF, roots)
        top = next(n for n in forest if n['name'] == TOP)
        self.assertEqual([c['name'] for c in top['children']], [MID])
        self.assertEqual([c['name'] for c in top['children'][0]['children']], [LEAF])
        flat = [(d, n['name']) for d, n in D.flatten([top])]
        self.assertEqual(flat, [(0, TOP), (1, MID), (2, LEAF)])

    def test_loop_shows_once_with_one_root(self):
        forest = D.tree(self.rolled, RHYTHMS)
        names = [n['name'] for _, n in D.flatten(forest)]
        self.assertEqual(sorted(names), sorted(self.rolled))       # every drive, once
        loop_roots = [n['name'] for n in forest if n['name'] in (LOOP_A, LOOP_B)]
        self.assertEqual(len(loop_roots), 1)

    def test_parent_with_no_rows_of_its_own_still_shows(self):
        rolled = D.roll_up([dict(drive=LEAF, min=30)], RHYTHMS, weight=W)
        forest = D.tree(rolled, RHYTHMS)
        self.assertEqual([n['name'] for n in forest], [TOP])
        self.assertEqual((forest[0]['own'], forest[0]['total']), (0, 30))


if __name__ == '__main__':
    unittest.main()
