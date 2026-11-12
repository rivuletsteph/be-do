# -*- coding: utf-8 -*-
"""The shared parts put a page back together, and the page still parses.

A part lifted out of an engine is a brace that moved between two files. A diff
cannot see that — the characters are all still there, just somewhere else — and
the page is dead. It happened once on the way in: the base-flow card's comment
began one line below the closing brace of the function above it, the grab took
the brace, and the my day page threw `Unexpected token '}'` before it drew
anything. So this test does not compare text. It fills each engine and hands
every <script> block to `node --check`.

    python3 tests/test_parts.py

Without node it says so and checks what it can — that every placeholder an
engine carries has a part behind it, and that no part holds a dangling comment.
"""
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.dirname(HERE)
BEDO = os.path.dirname(os.path.dirname(PARTS))
sys.path.insert(0, PARTS)
import parts  # noqa: E402

ENGINES = [
    os.path.join(BEDO, 'skills', 'bedo-day-ahead', 'assets', 'flow_engine.html'),
    os.path.join(BEDO, 'skills', 'bedo-week-ahead', 'assets', 'week_engine.html'),
]
HAS_NODE = subprocess.run(['node', '--version'], capture_output=True,
                          shell=(os.name == 'nt')).returncode == 0


class TheParts(unittest.TestCase):

    def test_every_part_is_on_disk(self):
        for mark, path in parts.PARTS.items():
            self.assertTrue(os.path.exists(path), f'{mark} has no file: {path}')

    def test_every_placeholder_an_engine_carries_is_filled(self):
        for eng in ENGINES:
            page = open(eng, encoding='utf-8').read()
            marks = [m for m in parts.PARTS if m in page]
            self.assertTrue(marks, f'{os.path.basename(eng)} carries no shared part')
            out = parts.fill(page)
            for m in marks:
                self.assertNotIn(m, out, f'{m} was not filled in {os.path.basename(eng)}')

    def test_no_part_holds_a_dangling_comment(self):
        """A part that opens more comments than it closes swallows the page after it."""
        for mark, path in parts.PARTS.items():
            if not path.endswith(('.js', '.css')):
                continue
            body = open(path, encoding='utf-8').read()
            # a regex literal can hold */ (the engine has one), so only count comment opens
            self.assertEqual(body.count('/*'), body.count('*/'),
                             f'{os.path.basename(path)} does not close every comment it opens')

    def test_no_part_carries_a_placeholder_of_its_own(self):
        """A part holding /*ROOT*/ or another mark would be filled twice, or broken in half."""
        for path in parts.PARTS.values():
            if not path.endswith(('.js', '.css')):
                continue
            body = open(path, encoding='utf-8').read()
            for m in list(parts.PARTS) + ['/*ROOT*/', '/*NIGHT*/', '/*DATA*/']:
                self.assertNotIn(m, body, f'{os.path.basename(path)} carries {m}')

    @unittest.skipUnless(HAS_NODE, 'node is not here; the parse check needs it')
    def test_each_engine_still_parses_once_it_is_filled(self):
        for eng in ENGINES:
            page = parts.fill(open(eng, encoding='utf-8').read()).replace('/*DATA*/', '{}')
            blocks = re.findall(r'<script>(.*?)</script>', page, re.S)
            self.assertGreaterEqual(len(blocks), 2, os.path.basename(eng))
            for i, b in enumerate(blocks):
                with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False,
                                                 encoding='utf-8') as f:
                    f.write(b)
                    tmp = f.name
                try:
                    r = subprocess.run(['node', '--check', tmp], capture_output=True, text=True,
                                       shell=(os.name == 'nt'))
                    self.assertEqual(r.returncode, 0,
                                     f'{os.path.basename(eng)} script {i + 1} does not parse:\n{r.stderr}')
                finally:
                    os.unlink(tmp)


class TheClock(unittest.TestCase):
    """Her amendment of 9 Nov 2026: a lowercase a or p at the end, no space,
    no m, no AM/PM. The javascript side is clock.js; this is the Python side, and the two
    have to agree."""

    def test_a_time_ends_in_a_or_p(self):
        self.assertEqual(parts.am_pm('09:00'), '9:00a')
        self.assertEqual(parts.am_pm('14:45'), '2:45p')
        self.assertEqual(parts.am_pm('00:05'), '12:05a')
        self.assertEqual(parts.am_pm('12:00'), '12:00p')
        self.assertEqual(parts.am_pm('23:59'), '11:59p')

    def test_a_range_drops_the_first_letter_only_when_both_share_it(self):
        self.assertEqual(parts.span('14:00', '15:30'), '2:00–3:30p')
        self.assertEqual(parts.span('11:30', '13:00'), '11:30a–1:00p')

    @unittest.skipUnless(HAS_NODE, 'node is not here; the two sides can only be run apart')
    def test_the_javascript_side_says_the_same_thing(self):
        """clock.js writes the times on the pages and parts.am_pm writes them in the replies and
        the files. If the two ever disagree, a page and a chat would say different clocks."""
        times = ['00:00', '00:05', '07:30', '09:00', '11:59', '12:00', '12:30', '14:45', '23:59']
        script = (parts.read('/*CLOCKJS*/')
                  + '\nconsole.log(JSON.stringify(%s.map(wt)));\n' % times).replace("'", '"')
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as f:
            f.write(script)
            tmp = f.name
        try:
            r = subprocess.run(['node', tmp], capture_output=True, text=True,
                               shell=(os.name == 'nt'))
            self.assertEqual(r.returncode, 0, r.stderr)
            import json
            self.assertEqual(json.loads(r.stdout.strip()), [parts.am_pm(t) for t in times])
        finally:
            os.unlink(tmp)


if __name__ == '__main__':
    unittest.main(verbosity=2)
