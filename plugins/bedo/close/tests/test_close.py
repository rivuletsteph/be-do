# -*- coding: utf-8 -*-
"""close.py end to end on invented rows, no network: plan, verify, audit,
export. The rows are the REST shape the close fetches (fields by name).

    python3 plugins/bedo/close/tests/test_close.py
"""
import json, os, subprocess, sys, tempfile, unittest

CLOSE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'close.py')
DIV = '—' * 3
LOCAL = {'weekly_name': 'w{n} be•do', 'stream_table': 'tblX', 'week_zero_sunday': '2026-05-03',
         'week_zero_number': 19, 'utc_offset_hours': -5, 'archive_depth': 1, 'tables': {}}


def r(rid, created, **f):
    return {'id': rid, 'createdTime': created, 'fields': f}


W40 = [
    r('o1', '2026-09-28T13:00:00.000Z', **{'action key': '260928_0800', 'status': '⬜ intention',
       'practice text': '⚡ action', 'datetime': '2026-09-28T13:00:00.000Z', 'action': 'an open thing'}),
    r('l1', '2026-09-28T13:00:30.000Z', **{'action key': '260928_0800', 'status': '● log',
       'practice text': '📲 capture', 'datetime': '2026-09-28T13:00:00.000Z', 'action': 'capture',
       'details': 'my words\n---\n[be•do] leaked block'}),
    r('g1', '2026-10-01T13:00:00.000Z', **{'status': '● log', 'practice text': '📝 log',
       'datetime': '2026-10-01T12:05:00.000Z', 'action': 'a morning',
       'details': '[be•do] only be•do wrote this'}),
    r('g2', '2026-10-02T02:00:00.000Z', **{'status': '● log', 'practice text': '📝 log',
       'datetime': '2026-10-02T02:00:00.000Z', 'action': 'an evening',
       'details': f'her evening\n{DIV}\n[be•do] a note\n> screen text'}),
]
W39 = [r('x1', '2026-09-05T12:42:00.000Z', **{'action key': '260905_0742', 'status': '⬜ intention',
         'practice text': '⚡ action', 'datetime': '2026-09-05T12:42:00.000Z', 'action': 'archived open'})]


def run(d, *a):
    env = dict(os.environ, BEDO_CLOSE_LOCAL=os.path.join(d, 'close_local.json'), PYTHONUTF8='1')
    return subprocess.run([sys.executable, CLOSE, *a], cwd=d, capture_output=True, text=True,
                          encoding='utf-8', env=env)


class Close(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        d = self.d = self.t.name
        json.dump(LOCAL, open(os.path.join(d, 'close_local.json'), 'w', encoding='utf-8'))
        os.makedirs(os.path.join(d, 'w40-close'))
        for n, rows in ((41, W40), (40, W40), (39, W39)):
            with open(os.path.join(d, 'w40-close', f'w{n}.json'), 'w', encoding='utf-8') as fh:
                json.dump({'base': f'b{n}', 'records': rows, 'metadata': {'totalRecordCount': len(rows)}},
                          fh, ensure_ascii=False)

    def tearDown(self):
        self.t.cleanup()

    def test_plan_carries_the_open_action_and_names_the_archive_gap(self):
        p = run(self.d, 'plan', '--week', '40', '--clone', '2026-10-04T15:00:00.000Z')
        self.assertEqual(p.returncode, 0, p.stderr)
        plan = json.load(open(os.path.join(self.d, 'w40-close', 'split_plan.json'), encoding='utf-8'))
        self.assertIn('o1', plan['carry_ids'])
        self.assertEqual(sorted(plan['delete_ids']), ['g1', 'g2', 'l1'])
        self.assertEqual(plan['carry_elsewhere'], ['x1'])
        self.assertIn('re-carry', p.stdout)

    def test_verify_stops_until_the_gap_is_carried(self):
        p = run(self.d, 'verify', '--week', '40')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('260905_0742', p.stderr)

    def test_a_truncated_read_stops_the_plan(self):
        with open(os.path.join(self.d, 'w40-close', 'w39.json'), 'w', encoding='utf-8') as fh:
            json.dump({'records': W39, 'metadata': {'totalRecordCount': 5}}, fh)
        p = run(self.d, 'plan', '--week', '40', '--clone', '2026-10-04T15:00:00.000Z')
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('I11', p.stderr)

    def test_audit_names_the_broken_rules(self):
        p = run(self.d, 'audit', '--week', '40')
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn('key', p.stdout)          # a capture carrying an action key
        self.assertIn('details', p.stdout)      # the --- divider

    def test_export_is_her_words_only(self):
        p = run(self.d, 'export', '--week', '40')
        if p.returncode and 'python-docx' in p.stderr:
            self.skipTest('neither pandoc nor python-docx here')
        self.assertEqual(p.returncode, 0, p.stderr)
        md = open(os.path.join(self.d, 'w40-close', 'W40.md'), encoding='utf-8').read()
        self.assertNotIn('[be•do]', md)
        self.assertNotIn('leaked block', md)
        self.assertNotIn('only be•do wrote this', md)
        self.assertIn('her evening', md)
        self.assertIn('> screen text', md)
        self.assertIn('**7:05 AM', md)           # no %-I, no leading zero
        self.assertTrue(any(f.endswith('.docx') for f in os.listdir(os.path.join(self.d, 'w40-close'))))


if __name__ == '__main__':
    unittest.main()
