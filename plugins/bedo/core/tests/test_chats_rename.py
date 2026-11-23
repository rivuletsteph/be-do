# -*- coding: utf-8 -*-
"""The chat sweep's rename step (her yes, 16 Nov 2026). Everything is invented.

    python3 plugins/bedo/core/tests/test_chats_rename.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_chats as CH  # noqa: E402

NOW = dt.datetime(2026, 11, 20, 21, 0, tzinfo=dt.timezone.utc)
MET = 'what I did\n· objective: the memo — met, written\n· wrote it\n\nstill open\n· none\n———\n[be•do] x'
LOCAL = {'time_zone': 'America/Chicago', 'utc_offset_hours': -6}


def chat(n, title, days_ago=2.0, **kw):
    last = (NOW - dt.timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return {'sessionId': f'local_0000000{n}-aaaa-bbbb-cccc-00000000000{n}', 'title': title, 'isArchived': False,
            'isRunning': False, 'lastActivityAt': last, **kw}


def row(n, status='✅ done', details=MET, title='a session'):
    return {'id': f'rec{n}', 'created': '2026-11-19T15:00:00.000Z', 'practice': '⚡ action', 'status': status,
            'key': '261119_0900', 'title': title, 'datetime': '2026-11-19T15:00:00.000Z', 'details': details,
            'chat': f'claude://claude.ai/epitaxy/local_0000000{n}-aaaa-bbbb-cccc-00000000000{n}'}


def run(chats, rows, **kw):
    return CH.sweep(CH.chats_of([chats]), rows, NOW, LOCAL, **kw)[0]


class Finished(unittest.TestCase):
    def test_plain_title_with_done_row_takes_done_glyph(self):
        x = run([chat(1, 'Rainfall memo')], [row(1)])
        self.assertEqual((x['verdict'], x['rename']), ('archive', '☑️ Rainfall memo'))

    def test_drive_code_on_the_row_is_used(self):
        x = run([chat(1, 'Rainfall memo')], [row(1, title='P03.9 rainfall memo')])
        self.assertEqual(x['rename'], '☑️ P03.9 Rainfall memo')

    def test_drive_code_in_the_title_is_not_doubled(self):
        x = run([chat(1, '▶️ P03.9 Rainfall memo')], [row(1, title='P03.9 rainfall memo')])
        self.assertEqual(x['rename'], '☑️ P03.9 Rainfall memo')

    def test_no_code_is_never_guessed(self):
        self.assertNotRegex(run([chat(1, 'Rainfall memo')], [row(1)])['rename'], r'[A-Z]\d+\.\d+')

    def test_dropped_row_takes_dropped_glyph(self):
        x = run([chat(1, 'News skill')], [row(1, status='✖️ dropped')])
        self.assertEqual(x['rename'], '✖️ News skill')

    def test_window_chat_takes_closed_glyph(self):
        x = run([chat(1, 'Sun W45 my day')], [row(1)])
        self.assertEqual(x['rename'], '✔️ Sun W45 my day')

    def test_already_in_form_is_not_renamed(self):
        self.assertIsNone(run([chat(1, '☑️ Rainfall memo')], [row(1)])['rename'])
        self.assertIsNone(run([chat(1, '✖️ News skill')], [])['rename'])


class Open(unittest.TestCase):
    def test_open_chat_with_no_glyph_gets_moving(self):
        x = run([chat(1, 'Place database', days_ago=1)], [row(1, status='▶️ in motion', details='x')])
        self.assertEqual((x['verdict'], x['rename']), ('keep', '▶️ Place database'))

    def test_open_chat_with_a_glyph_is_left(self):
        self.assertIsNone(run([chat(1, '⏯️ Place database', days_ago=1)], [row(1, status='▶️ in motion')])['rename'])

    def test_todays_my_day_chat_is_never_renamed(self):
        x = run([chat(1, 'Fri W47 my day', days_ago=0.1)], [])
        self.assertIsNone(x['rename'])

    def test_busy_chat_is_never_renamed(self):
        x = run([chat(1, 'Place database', days_ago=0.001)], [])
        self.assertEqual((x['verdict'], x['rename']), ('busy', None))


class OnItsOwn(unittest.TestCase):
    def test_no_rename_switch(self):
        x = run([chat(1, 'Rainfall memo')], [row(1)], rename=False)
        self.assertIsNone(x['rename'])
        self.assertNotIn('rename', CH.render([x], NOW))

    def test_line_carries_the_rename(self):
        x = run([chat(1, 'Rainfall memo')], [row(1)])
        self.assertIn('rename → ☑️ Rainfall memo', CH.render([x], NOW))


if __name__ == '__main__':
    unittest.main()
