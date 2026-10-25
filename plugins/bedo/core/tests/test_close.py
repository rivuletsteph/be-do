# -*- coding: utf-8 -*-
"""The chat close: QA, then the session entry, then the rename (25 Oct 2026).
Every row is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_close.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_close as C  # noqa: E402

URL = 'https://claude.ai/code/session_01EXAMPLE'
DAY = dt.date(2026, 10, 24)
LOCAL = {'utc_offset_hours': -5, 'weekly_name': 'w{n} be•do'}


def entry(status='✅ done', chat=URL, created='2026-10-25T17:12:10.000Z'):
    return {'id': 'recE', 'created': created, 'practice': '⚡ action', 'status': status, 'key': '261024_0643',
            'title': 'my day, Sat 24 Oct', 'datetime': '2026-10-24T11:43:00.000Z', 'chat': chat,
            'wellness': '💨 air', 'device': '📱 phone',
            'details': 'what I did\n· logged the day\n———\n[be•do] written by session-entry'}


def close_row(marker=True):
    d = '———\n[be•do] closed.\n' + ('dayqa shown 2026-10-24 22:49 · 3 proposed' if marker else '')
    return {'id': 'recC', 'created': '2026-10-25T14:56:33.000Z', 'practice': '🌄 dusk flow close',
            'status': '◉ done', 'datetime': '2026-10-25T04:59:00.000Z', 'details': d}


def oks(found):
    return [ok for ok, _, _ in found]


class MyDay(unittest.TestCase):
    TITLE = '✔️1024 ⏳ Sat W43 🔆 my day'

    def test_all_three_done_closes(self):
        self.assertEqual(oks(C.findings([close_row(), entry()], URL, self.TITLE, DAY, LOCAL)), [True] * 3)

    def test_no_marker_means_qa_is_owed(self):
        ok, what, why = C.findings([close_row(marker=False), entry()], URL, self.TITLE, DAY, LOCAL)[0]
        self.assertFalse(ok)
        self.assertIn('dayqa 2026-10-24', why)

    def test_a_marker_for_another_day_is_not_this_days_qa(self):
        r = close_row(); r['details'] = r['details'].replace('2026-10-24', '2026-10-23')
        self.assertFalse(C.findings([r, entry()], URL, self.TITLE, DAY, LOCAL)[0][0])

    def test_no_entry_and_the_title_waits_for_it(self):
        found = C.findings([close_row()], URL, '▶️1024 ⏳ Sat W43 🔆 my day', DAY, LOCAL)
        self.assertEqual(oks(found), [True, False, False])
        self.assertIn('once the entry is written', found[2][2])

    def test_a_window_chat_still_open_is_renamed_to_the_check(self):
        found = C.findings([close_row(), entry()], URL, '▶️1024 ⏳ Sat W43 🔆 my day', DAY, LOCAL)
        self.assertFalse(found[2][0])
        self.assertIn('✔️', found[2][2])

    def test_an_entry_for_another_chat_is_not_this_ones(self):
        found = C.findings([close_row(), entry(chat=URL + 'X')], URL, self.TITLE, DAY, LOCAL)
        self.assertFalse(found[1][0])


class DriveChat(unittest.TestCase):

    def test_done_work_takes_the_box(self):
        found = C.findings([entry()], URL, '☑️💧P03.13 Stage IV rainfall', None, LOCAL)
        self.assertEqual(oks(found), [True] * 3)

    def test_done_work_still_marked_moving_is_renamed(self):
        found = C.findings([entry()], URL, '▶️💧P03.13 Stage IV rainfall', None, LOCAL)
        self.assertFalse(found[2][0])
        self.assertIn('☑️', found[2][2])

    def test_work_in_motion_may_take_any_open_glyph(self):
        for g in ('▶️', '⏯️', '⏸️'):
            found = C.findings([entry(status='▶️ in motion')], URL, g + '💧P03.13 Stage IV', None, LOCAL)
            self.assertTrue(found[2][0], g)

    def test_qa_is_the_entry_check_on_the_entry(self):
        bad = entry(); bad['key'] = ''
        ok, _, why = C.findings([bad], URL, '☑️ x', None, LOCAL)[0]
        self.assertFalse(ok)
        self.assertIn('key', why)

    def test_the_newest_entry_wins(self):
        old = entry(status='▶️ in motion', created='2026-10-24T12:00:00.000Z')
        found = C.findings([old, entry()], URL, '☑️ x', None, LOCAL)
        self.assertIn('✅ done', found[1][2])

    def test_render_names_what_is_left_in_order(self):
        text = C.render('t', C.findings([], URL, '▶️ t', None, LOCAL))
        self.assertIn('still to do, in order: QA, session entry, title', text)


if __name__ == '__main__':
    unittest.main()
