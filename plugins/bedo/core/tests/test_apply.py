# -*- coding: utf-8 -*-
"""Rows written by code, never retyped by a model (24 Nov 2026): a change names
only what changes, a new line is added to the details the row already has, and
what the entry check deduces is filled in before the row goes. No network.

    python3 core/tests/test_apply.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_apply as A  # noqa: E402

F = dict(title='fT', status='fS', details='fD', device='fV', person='fP', datetime='fW')
D = A.DIVIDER


class Compose(unittest.TestCase):
    def test_a_line_goes_at_the_end_and_nothing_else_moves(self):
        was = f'Her words.\n{D}\n[be•do] first.'
        self.assertEqual(A.compose(was, append='[be•do] second.'), was + '\n[be•do] second.')

    def test_her_words_go_above_the_divider(self):
        was = f'Her words.\n{D}\n[be•do] first.'
        self.assertEqual(A.compose(was, her_words='More of hers. (9:00p)'),
                         f'Her words.\nMore of hers. (9:00p)\n{D}\n[be•do] first.')

    def test_a_row_with_no_divider_gets_one(self):
        self.assertEqual(A.compose('Her words.', append='[be•do] a note.'), f'Her words.\n{D}\n[be•do] a note.')
        self.assertEqual(A.compose('', append='[be•do] a note.'), f'{D}\n[be•do] a note.')
        self.assertEqual(A.compose(f'{D}\n[be•do] a note.', her_words='Hers.'), f'Hers.\n{D}\n[be•do] a note.')


class Plan(unittest.TestCase):
    def test_a_change_sends_only_what_changes(self):
        c, u, r = A.plan([{'id': 'rec1', 'status': '✅ done'}], {}, F)
        self.assertEqual((c, u, r), ([], [{'id': 'rec1', 'fields': {'fS': '✅ done'}}], []))

    def test_a_new_line_is_added_to_the_details_code_read(self):
        c, u, r = A.plan([{'id': 'rec1', 'append': '[be•do] done.', 'status': '✅ done'}],
                         {'rec1': f'Hers.\n{D}\n[be•do] was.'}, F)
        self.assertEqual(u, [{'id': 'rec1', 'fields': {'fS': '✅ done', 'fD': f'Hers.\n{D}\n[be•do] was.\n[be•do] done.'}}])

    def test_a_row_that_could_not_be_read_is_never_overwritten(self):
        c, u, r = A.plan([{'id': 'rec9', 'append': '[be•do] done.'}], {}, F)
        self.assertEqual((u, len(r)), ([], 1))

    def test_what_the_check_deduces_is_filled_in(self):
        def check(row):
            out = []
            if not row.get('device'):
                out.append('device: empty — deduced 📱 phone (a phone practice); write it with the row')
            if not row.get('person'):
                out.append('person: empty → Pip, Sam — at home with the household by default: alone only when a row says so')
            return out
        c, u, r = A.plan([{'title': 'a new row', 'status': '● log'}], {}, F, check)
        self.assertEqual(c, [{'fT': 'a new row', 'fS': '● log', 'fV': '📱 phone', 'fP': 'Pip, Sam'}])
        self.assertEqual(r, [])

    def test_a_row_the_check_cannot_settle_is_not_written(self):
        c, u, r = A.plan([{'title': 'no practice'}], {}, F, lambda row: ['practice: every row carries one'])
        self.assertEqual((c, r), ([], [('no practice', ['practice: every row carries one'])]))

    def test_a_row_for_another_weeks_base_is_not_written_here(self):
        c, u, r = A.plan([{'title': 'last week'}], {}, F, lambda row: ["base: this row's own date belongs in w10"])
        self.assertEqual((c, len(r)), ([], 1))


if __name__ == '__main__':
    unittest.main()
