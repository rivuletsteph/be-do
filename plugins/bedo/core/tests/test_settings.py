# -*- coding: utf-8 -*-
"""Settings from an Airtable row, and the fallback that keeps every build running.

    python3 plugins/bedo/core/tests/test_settings.py
"""
import json, os, subprocess, sys, tempfile, unittest
from unittest import mock

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_settings as S  # noqa: E402


def rec(name, text):
    return {'id': 'rec' + name, 'fields': {'name': name, 'json': text}}


class Rows(unittest.TestCase):
    def test_the_named_row_is_read(self):
        d, why = S.from_records([rec('day_ahead_local', '{"a": 1}'), rec('look_behind_local', '{"b": 2}')],
                                'look_behind_local')
        self.assertEqual((d, why), ({'b': 2}, None))

    def test_a_code_fence_is_forgiven(self):
        self.assertEqual(S.parse('```json\n{"a": 1}\n```'), {'a': 1})

    def test_missing_broken_or_doubled_rows_say_why(self):
        self.assertIn('no row', S.from_records([], 'x')[1])
        self.assertIn('not a JSON object', S.from_records([rec('x', '{"a": ')], 'x')[1])
        self.assertIn('not a JSON object', S.from_records([rec('x', '[]')], 'x')[1])
        self.assertIn('2 rows', S.from_records([rec('x', '{}'), rec('x', '{}')], 'x')[1])


class Fallback(unittest.TestCase):
    def test_no_airtable_here_is_not_a_crash(self):
        with mock.patch('bedo_air.can_read', return_value=False):
            self.assertEqual(S.fetch('x'), (None, 'Airtable cannot be read here'))

    def test_an_http_error_falls_back(self):
        with mock.patch('bedo_air.can_read', return_value=True), \
             mock.patch('bedo_air.Air.bases', side_effect=SystemExit('ABORT: meta/bases: HTTP 401')):
            d, why = S.fetch('x')
        self.assertIsNone(d)
        self.assertIn('401', why)

    def test_the_cli_leaves_the_old_file_alone_when_it_cannot_read(self):
        tmp = tempfile.mkdtemp()
        out = os.path.join(tmp, 'look_behind_local.json')
        open(out, 'w').write('{"kept": true}')
        env = {k: v for k, v in os.environ.items() if k not in ('AIRTABLE_PAT', 'BEDO_SECRETS', 'CLAUDE_CODE_REMOTE')}
        r = subprocess.run([sys.executable, os.path.join(CORE, 'bedo_settings.py'), 'look_behind_local', '--out', out],
                           capture_output=True, text=True, cwd=tmp, env=dict(env, HOME=tmp))
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("using the skill's own copy", r.stderr)
        self.assertEqual(json.load(open(out)), {'kept': True})


if __name__ == '__main__':
    unittest.main()
