# -*- coding: utf-8 -*-
"""Duet's asks reach Code through the stream (23 Nov 2026, her words: so I
don't relay prompts between Duet and Code). An ask is an open ⚡ row whose
details carry `for code:`; a closed one, or a row without the line, is not.

    python3 core/tests/test_asks.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_asks as A  # noqa: E402


def row(rid, title, status, details, at='2026-03-13T15:00:00.000Z'):
    return dict(id=rid, title=title, status=status, details=details, datetime=at, rhythm='Sysdrive')


ROWS = [
    row('recB', '⚡ The page shows the wrong hour', '⬜ intention',
        'It says 3 when it was 4.\n———\n[be•do] for code: fix the hour on the page\ndone when: the page and the row agree',
        '2026-03-13T16:00:00.000Z'),
    row('recA', '⚡ Add a snack practice', '▶️ in motion',
        'for code: add the practice\n———\n[be•do] code: waiting on her pick of a glyph', '2026-03-13T15:00:00.000Z'),
    row('recC', '⚡ Old ask', '✅ done', 'for code: something finished\ndone when: it is'),
    row('recD', '⚡ Buy stamps', '⬜ intention', 'At the post office.'),
]


class Asks(unittest.TestCase):
    def test_open_rows_with_the_line_are_asks_oldest_first(self):
        self.assertEqual([x['id'] for x in A.asks(ROWS)], ['recA', 'recB'])

    def test_the_objective_and_done_when_are_read(self):
        b = A.asks(ROWS)[1]
        self.assertEqual((b['objective'], b['done_when']), ('fix the hour on the page', 'the page and the row agree'))
        self.assertEqual(b['title'], 'The page shows the wrong hour')

    def test_a_missing_done_when_is_said(self):
        a = A.asks(ROWS)[0]
        self.assertIsNone(a['done_when'])
        self.assertEqual(a['said'], 'waiting on her pick of a glyph')
        self.assertIn('NOT GIVEN', '\n'.join(A.report([a])))

    def test_none_is_one_line(self):
        self.assertEqual(A.report([], ('w11',)), ['asks   none open in w11'])


if __name__ == '__main__':
    unittest.main()
