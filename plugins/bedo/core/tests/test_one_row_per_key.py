# -*- coding: utf-8 -*-
"""One row per key (12 Nov 2026). An action sat in motion and done at once on
one key, and closes written as a second row left the open one showing past its
date. The entry check is handed every row the live base already holds on the
key, and refuses a second.

    python3 core/tests/test_one_row_per_key.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_entry as E  # noqa: E402

A = E.FACTS['status']['actions']
MOVING = next(s for s in A if 'motion' in s)
DONE = next(s for s in A if 'done' in s)
OPEN = {'id': 'recOPEN', 'key': '261110_1210b', 'status': MOVING, 'title': '⚡ Send the corrected data'}


def has(problems, word):
    return any(word in p for p in problems)


class OneRowPerKey(unittest.TestCase):
    def test_a_close_written_as_a_second_row_is_refused(self):
        new = {'key': '261110_1210b', 'status': DONE, 'title': '⚡ Send the corrected data'}
        p = E.key_problems(new, [OPEN])
        self.assertEqual(len(p), 1)
        self.assertIn('update that row in place', p[0])
        self.assertIn('recOPEN', p[0])                      # the row to update is named

    def test_the_close_as_an_update_of_that_row_passes(self):
        self.assertEqual(E.key_problems(dict(OPEN, status=DONE), [OPEN]), [])

    def test_an_update_that_shares_its_key_with_another_row_is_named(self):
        other = dict(OPEN, id='recOTHER', status=DONE)
        p = E.key_problems(dict(OPEN, status=DONE), [OPEN, other])
        self.assertTrue(has(p, 'on another row too'))
        self.assertIn('recOTHER', p[0])

    def test_a_new_key_and_a_row_with_no_key_pass(self):
        self.assertEqual(E.key_problems({'key': '261112_0827', 'status': DONE}, [OPEN]), [])
        self.assertEqual(E.key_problems({'status': 'x', 'title': 'a log'}, [OPEN]), [])
        self.assertEqual(E.key_problems({'key': '261110_1210b', 'status': DONE}, None), [])

    def test_the_whole_check_carries_it(self):
        new = {'key': '261110_1210b', 'status': DONE, 'practice': E.ACTION, 'title': '⚡ x',
               'datetime': '2026-11-12T16:25:00.000Z'}
        self.assertTrue(has(E.problems(new, existing=[OPEN]), 'already has a row'))
        self.assertFalse(has(E.problems(new, existing=[]), 'already has a row'))


if __name__ == '__main__':
    unittest.main(verbosity=1)
