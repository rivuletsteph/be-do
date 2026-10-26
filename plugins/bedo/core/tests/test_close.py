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


MET = 'what I did\n· objective: the stage IV rainfall layer — met, built and checked against the gauges\n· built it'


def entry(status='✅ done', chat=URL, created='2026-10-25T17:12:10.000Z', details=MET):
    return {'id': 'recE', 'created': created, 'practice': '⚡ action', 'status': status, 'key': '261024_0643',
            'title': 'my day, Sat 24 Oct', 'datetime': '2026-10-24T11:43:00.000Z', 'chat': chat,
            'wellness': '💨 air', 'device': '📱 phone',
            'details': details + '\n\nstill open\n· none\n———\n[be•do] written by session-entry'}


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


class Objective(unittest.TestCase):
    """Her rule, 25 Oct 2026: the close's QA is the objective — what it was, and was it met."""
    TITLE = '☑️💧P03.13 Stage IV rainfall'

    def qa(self, details, status='✅ done', title=None):
        return C.findings([entry(status=status, details=details)], URL, title or self.TITLE, None, LOCAL)[0]

    def test_met_and_named_passes_and_says_so(self):
        ok, _, why = self.qa(MET)
        self.assertTrue(ok)
        self.assertEqual(why, 'objective met — the stage IV rainfall layer')

    def test_no_objective_line_is_owed_with_the_shape(self):
        ok, _, why = self.qa('what I did\n· built it')
        self.assertFalse(ok)
        self.assertIn('· objective: <what it was> — met | partly met | not met, <why>', why)

    def test_the_old_line_without_the_objective_is_not_enough(self):
        self.assertFalse(self.qa('what I did\n· objective met — built it\n· built it')[0])

    def test_the_objective_must_come_first(self):
        self.assertFalse(self.qa('what I did\n· built it\n· objective: the layer — met, built')[0])

    def test_a_verdict_wants_a_why(self):
        ok, _, why = self.qa('what I did\n· objective: the layer — met')
        self.assertFalse(ok)
        self.assertIn('why', why)

    def test_partly_met_with_nothing_still_open_wants_the_next_step(self):
        ok, _, why = self.qa('what I did\n· objective: the layer — partly met, the gauges are missing',
                             status='▶️ in motion', title='▶️💧P03.13 Stage IV rainfall')
        self.assertFalse(ok)
        self.assertIn('still open', why)

    def test_not_met_with_a_next_step_passes(self):
        d = 'what I did\n· objective: the layer — not met, the download failed\n\nstill open\n· retry the download'
        found = C.findings([dict(entry(status='▶️ in motion'), details=d + '\n———\n[be•do]')], URL,
                           '▶️💧P03.13 Stage IV rainfall', None, LOCAL)
        self.assertTrue(found[0][0], found[0][2])
        self.assertEqual(found[0][2], 'objective not met — the layer')

    def test_a_window_chat_takes_no_objective(self):
        found = C.findings([entry(details='what I did\n· closed the week')], URL, '✔️\U0001684E my week W43', None, LOCAL)
        self.assertTrue(found[0][0], found[0][2])

    def test_a_my_day_chat_is_still_its_dayqa(self):
        found = C.findings([close_row(), entry(details='what I did\n· logged the day')], URL,
                           '✔️1024 ⏳ Sat W43 🔆 my day', DAY, LOCAL)
        self.assertTrue(found[0][0])

    def test_an_entry_problem_and_a_missing_objective_both_show(self):
        bad = entry(details='what I did\n· built it'); bad['key'] = ''
        ok, _, why = C.findings([bad], URL, self.TITLE, None, LOCAL)[0]
        self.assertFalse(ok)
        self.assertIn('key', why)
        self.assertIn('objective', why)


class Stretches(unittest.TestCase):
    """A session with gaps carries her stretches and their sum (261024a)."""
    TITLE = '☑️' + 'D6.65 the cards'

    def qa(self, **kw):
        e = dict(entry(), **kw)
        return C.findings([e], URL, self.TITLE, local=LOCAL)[0]

    def test_one_stretch_keeps_its_span_and_needs_no_line(self):
        self.assertTrue(self.qa(end='2026-10-24T12:43:00.000Z')[0])

    def test_gaps_without_her_stretches_are_owed(self):
        ok, _, why = self.qa(time_spent=1500)
        self.assertFalse(ok)
        self.assertIn('stretches', why)

    def test_gaps_with_her_stretches_and_their_sum_pass(self):
        d = MET + '\n\nstill open\n· none\n———\n[be•do] written by session-entry\nstretches: 6:43–6:53 · 8:00–8:15 = 25m'
        self.assertTrue(self.qa(time_spent=1500, details=d)[0])

    def test_a_time_spent_that_is_the_envelope_is_named(self):
        d = MET + '\n\nstill open\n· none\n———\n[be•do] stretches: 6:43–6:53 · 8:00–8:15 = 25m'
        ok, _, why = self.qa(time_spent=92 * 60, details=d)
        self.assertFalse(ok)
        self.assertIn('not the sum of her stretches, 25m', why)


if __name__ == '__main__':
    unittest.main()
