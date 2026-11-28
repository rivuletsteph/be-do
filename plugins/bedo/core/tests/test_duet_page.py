# -*- coding: utf-8 -*-
"""The page Duet reads each morning (24 Nov 2026, her words: why does Duet not
read the judgment file). `docs/duet.md` is the short form of J17. It stays
short, and it stays in step with what the code and the judgment file say: the
ask markers `asks` reads, the capture practices `sweep` applies, the rules J17
names.

    python3 core/tests/test_duet_page.py
"""
import json, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.dirname(HERE)
sys.path.insert(0, CORE)
ROOT = os.path.normpath(os.path.join(CORE, '..', '..', '..'))
import bedo_asks  # noqa: E402

read = lambda *p: open(os.path.join(ROOT, *p), encoding='utf-8').read()
PAGE, JUDG = read('docs', 'duet.md'), read('docs', 'v53-judgment.md')
CAP = json.load(open(os.path.join(CORE, 'facts.json'), encoding='utf-8'))['capture']


class DuetPage(unittest.TestCase):
    def test_it_stays_short(self):
        self.assertLess(len(PAGE.split()), 750, 'the page Duet reads every morning has grown: it is the short form')

    def test_the_ask_format_is_the_one_asks_reads(self):
        self.assertIn(bedo_asks.MARK, PAGE)
        self.assertIn('done when:', PAGE)
        self.assertIn('run asks', PAGE)

    def test_the_capture_practices_are_the_ones_sweep_applies(self):
        for k in ('log', 'journal', 'talk'):
            self.assertIn(CAP[k], PAGE, k)
            self.assertIn(CAP[k], JUDG, k)

    def test_it_carries_what_j17_names(self):
        for words in ('typecast', 'never the messenger', 'one bullet a thing', 'what mattered', 'own row'):
            self.assertIn(words, PAGE.lower(), words)
            self.assertIn(words, JUDG.lower(), words)

    def test_the_judgment_file_points_duet_here(self):
        self.assertIn('docs/duet.md', JUDG)


if __name__ == '__main__':
    unittest.main()
