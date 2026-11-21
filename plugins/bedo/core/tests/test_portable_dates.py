# -*- coding: utf-8 -*-
"""Dates format the same on every platform (21 Nov 2026).

'%-d' and '%-I' are glibc-only and Windows refuses them. One slipped into the
braid on 20 Nov (`{made:%-d %b}`), and the tests on main failed on Windows
from then on. This scans the code, not the tests, for a dash-flag format in
an f-string or a strftime call.

    python3 core/tests/test_portable_dates.py
"""
import os, re, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
BAD = re.compile(r"(\{[^{}]*:[^{}]*%-[a-zA-Z][^{}]*\}|strftime\([^)]*%-[a-zA-Z])")


def offenders():
    out = []
    for base in ('plugins', 'tools'):
        for dp, dn, fn in os.walk(os.path.join(ROOT, base)):
            if os.sep + 'tests' in dp + os.sep:
                continue
            for f in fn:
                if f.endswith('.py'):
                    p = os.path.join(dp, f)
                    for i, ln in enumerate(open(p, encoding='utf-8'), 1):
                        if BAD.search(ln.split('#', 1)[0]):
                            out.append(f'{os.path.relpath(p, ROOT)}:{i}')
    return out


class PortableDates(unittest.TestCase):
    def test_no_dash_flag_formats(self):
        self.assertEqual(offenders(), [])

    def test_the_scan_sees_one(self):
        self.assertTrue(BAD.search("f'carried since {made:%-d %b}'"))
        self.assertTrue(BAD.search("t.strftime('%-I:%M')"))
        self.assertFalse(BAD.search("f'carried since {made.day} {made:%b}'"))


if __name__ == '__main__':
    unittest.main()
