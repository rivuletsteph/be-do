# -*- coding: utf-8 -*-
"""The day ahead first, then its QA, then the day behind (her amendment, 6 Nov 2026):
look_behind.day_ahead_first. Every row is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_daygate.py
"""
import datetime as dt, json, os, subprocess, sys, tempfile, time, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_daygate as G  # noqa: E402
import bedo_preflight as P  # noqa: E402
import bedo_rules as RU  # noqa: E402

DAY = dt.date(2026, 11, 5)
LOCAL = {'utc_offset_hours': -6, 'weekly_name': 'w{n} be•do'}


def look_ahead(state='final', day=DAY, extra=' · v7'):
    return {'id': 'recLA', 'created': '2026-11-05T13:10:00.000Z', 'datetime': '2026-11-05T13:05:00.000Z',
            'practice': '👁️ look ahead', 'title': 'look ahead', 'status': '◉ done',
            'deliverable': 'https://claude.ai/artifact/EXAMPLE',
            'details': f'the three\n———\n[be•do] the three, two gaps\n[be•do] day ahead {day.isoformat()} · {state}{extra}'}


def close(qa=True, practice='🌄 dusk flow close', title='dusk close'):
    return {'id': 'recDC', 'created': '2026-11-06T04:30:00.000Z', 'datetime': '2026-11-06T04:25:00.000Z',
            'practice': practice, 'title': title, 'status': '◉ done',
            'details': '———\n[be•do] closed.' + ('\ndayqa shown 2026-11-05 22:25 · 2 proposed' if qa else '')}


def sleep(start='2026-11-06T05:10:00.000Z'):
    return {'id': 'recSL', 'created': '2026-11-06T13:00:00.000Z', 'datetime': start, 'end': '2026-11-06T12:40:00.000Z',
            'practice': '😴 sleep', 'title': 'sleep', 'status': '● log'}


class TheGate(unittest.TestCase):
    def test_no_final_day_ahead_blocks(self):
        rows = [close()]
        self.assertFalse(G.is_open(rows, DAY))
        why = G.refusal(rows, DAY)
        self.assertIn('look_behind.day_ahead_first', why)
        self.assertIn('no final day ahead for Thu 05 Nov', why)
        self.assertNotIn('dayqa:', why)                                      # the QA is there: only the day ahead named
        self.assertIn('FIX   day ahead', G.render(DAY, G.findings(rows, DAY)))

    def test_a_draft_or_another_days_final_is_not_final(self):
        self.assertFalse(G.is_open([look_ahead('draft'), close()], DAY))
        self.assertIn("only `[be•do] day ahead 2026-11-05 · draft", G.refusal([look_ahead('draft'), close()], DAY))
        self.assertFalse(G.is_open([look_ahead(day=DAY - dt.timedelta(days=1)), close()], DAY))

    def test_a_final_day_ahead_but_no_dayqa_line_blocks(self):
        rows = [look_ahead(), close(qa=False)]
        self.assertFalse(G.is_open(rows, DAY))
        why = G.refusal(rows, DAY)
        self.assertIn('no `dayqa shown 2026-11-05` line in the dusk close row', why)
        self.assertNotIn('no final day ahead', why)

    def test_the_dayqa_line_counts_only_in_the_close_row(self):
        rows = [look_ahead(), close(practice='📝 log', title='a note')]
        self.assertFalse(G.is_open(rows, DAY))
        self.assertIn('is on a note, not the dusk close row', G.refusal(rows, DAY))
        other_day = dict(close(), details='———\n[be•do] dayqa shown 2026-11-04 21:18 · 7 proposed')
        self.assertFalse(G.is_open([look_ahead(), other_day], DAY))         # Wednesday's QA is not Thursday's

    def test_both_and_it_builds(self):
        rows = [look_ahead(), close()]
        self.assertTrue(G.is_open(rows, DAY))
        self.assertIsNone(G.refusal(rows, DAY))
        self.assertTrue(G.render(DAY, G.findings(rows, DAY)).endswith('open: the day behind may be built'))
        # the lines read the same with the [be•do] prefix, or on any row: the date they name is the day
        mixed = [dict(close(), details='———\n[be•do] dayqa shown 2026-11-05 22:25 · 2 proposed\n'
                                       '[be•do] day ahead 2026-11-05 · final')]
        self.assertTrue(G.is_open(mixed, DAY))

    def test_the_line_it_writes(self):
        self.assertEqual(G.line(DAY, 7), '[be•do] day ahead 2026-11-05 · final · v7')
        self.assertEqual(G.line(DAY), '[be•do] day ahead 2026-11-05 · final')
        self.assertEqual(G.day_ahead_final([{'details': G.line(DAY, 7)}], DAY), G.line(DAY, 7))

    def test_it_is_a_registered_check(self):
        self.assertIn(G.CHECK, RU.CHECKS)
        m = {'recGATE': [G.CHECK]}
        self.assertEqual(RU.on_paper([('recGATE', '2026-11-06', 'GATE')], m), [])


class TheCommand(unittest.TestCase):
    def run_check(self, rows):
        p = os.path.join(tempfile.mkdtemp(), 'day.json')
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump(rows, fh)
        loc = os.path.join(os.path.dirname(p), 'facts_local.json')
        with open(loc, 'w', encoding='utf-8') as fh:
            json.dump(dict(LOCAL, stream_fields={}), fh)
        return subprocess.run([sys.executable, os.path.join(CORE, 'bedo_daygate.py'), 'check', '--date', DAY.isoformat(),
                               '--rows', p, '--local', loc], capture_output=True, text=True, encoding='utf-8',
                              env=dict(os.environ, PYTHONIOENCODING='utf-8'))

    def test_it_refuses_and_exits_non_zero(self):
        for rows in ([close()], [look_ahead(), close(qa=False)]):
            r = self.run_check(rows)
            self.assertEqual(r.returncode, 1, r.stdout + r.stderr)
            self.assertIn('FIX', r.stdout)
            self.assertIn('closed: finish the day ahead, QA it, then the day behind', r.stdout)

    def test_it_opens_with_both(self):
        r = self.run_check([look_ahead(), close()])
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn('FIX', r.stdout)


class Final(unittest.TestCase):
    """run_day_ahead.sh final: the page whole before its line is written."""
    def page(self, photos=1):
        d = tempfile.mkdtemp()
        s = os.path.join(d, 'w45.json')
        with open(s, 'w') as fh:
            fh.write('{}')
        time.sleep(0.01)
        p = os.path.join(d, '2026-11-05-myday.html')
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write(json.dumps({'schedule': [{'photos': [{'src': 'data:image/jpeg;base64,AA'}] * photos}]}))
        return p, s

    def test_no_bedtime_is_not_final(self):
        p, s = self.page()
        got = G.whole([look_ahead()], DAY, LOCAL, p, [s])
        self.assertFalse(all(ok for ok, _, _ in got))
        self.assertIn('the stream stops before bedtime', ' '.join(w for ok, _, w in got if not ok))

    def test_keepers_off_the_page_are_not_final(self):
        p, s = self.page(photos=0)
        keeper = {'datetime': '2026-11-05T22:00:00.000Z', 'practice': '✨ glimmer', 'photo': 'keeper', 'status': '● log'}
        got = G.whole([sleep(), keeper], DAY, LOCAL, p, [s])
        self.assertIn('hold a keeper photo and the page shows none', ' '.join(w for ok, _, w in got if not ok))

    def test_a_page_older_than_the_fetch_is_not_final(self):
        p, s = self.page()
        os.utime(p, (1, 1))
        got = G.whole([sleep()], DAY, LOCAL, p, [s])
        self.assertIn('built before the last fetch', ' '.join(w for ok, _, w in got if not ok))

    def test_whole_and_final(self):
        p, s = self.page()
        keeper = {'datetime': '2026-11-05T22:00:00.000Z', 'practice': '✨ glimmer', 'photo': 'keeper', 'status': '● log'}
        got = G.whole([sleep(), keeper], DAY, LOCAL, p, [s])
        self.assertTrue(all(ok for ok, _, _ in got), got)
        self.assertIsNone(G.bedtime([sleep('2026-11-05T15:00:00.000Z')], DAY, LOCAL))   # a 9 AM nap is no bedtime


    def test_a_checkbox_keeper_counts(self):
        # 11 Nov 2026: Tuesday's photo rows carried only the old checkbox; a keeper is the day behind's keeper
        p, s = self.page(photos=0)
        box = {'datetime': '2026-11-05T23:16:00.000Z', 'practice': '🔅 evening sun', 'photo_checked': True, 'status': '◉ done'}
        meal = {'datetime': '2026-11-05T18:48:00.000Z', 'practice': '🍽️ lunch', 'title': 'a sandwich', 'photo_checked': True,
                'status': '● log'}
        self.assertEqual(len(G.keepers([box, meal], DAY, LOCAL)), 1)        # a meal on her own is information
        got = G.whole([sleep(), box], DAY, LOCAL, p, [s])
        self.assertIn('the page shows none', ' '.join(w for ok, _, w in got if not ok))


class Calendar(unittest.TestCase):
    """A stale calendar is never published silently (11 Nov 2026: Tuesday's day-as-lived page was built at night on
    the morning's cal.json)."""

    def files(self, cal_at, fetch_at, today=DAY.isoformat()):
        d = tempfile.mkdtemp()
        cal, data = os.path.join(d, 'cal.json'), os.path.join(d, 'w45.json')
        with open(cal, 'w') as fh:
            json.dump({'calendars': [], 'read': {'today': today, 'at': cal_at}}, fh)
        with open(data, 'w') as fh:
            fh.write('{}')
        os.utime(data, (fetch_at, fetch_at))
        return cal, data

    def at(self, hhmm, day=DAY):
        h, m = map(int, hhmm.split(':'))      # local, at -6
        return dt.datetime(day.year, day.month, day.day, h, m, tzinfo=dt.timezone(dt.timedelta(hours=-6))).timestamp()

    def test_the_mornings_read_at_night_is_stale(self):
        cal, data = self.files(self.at('06:40'), self.at('22:30'))
        ok, what, why = G.calendar_fresh(cal, DAY, [data], 90, LOCAL)
        self.assertFalse(ok)
        self.assertIn('older than the last fetch (22:30)', why)
        self.assertIn('list_calendars', why)

    def test_the_dawn_refetch_passes_the_build_but_final_wants_a_fresh_read(self):
        cal, data = self.files(self.at('06:40'), self.at('07:10'))
        self.assertTrue(G.calendar_fresh(cal, DAY, [data], 90, LOCAL)[0])
        self.assertFalse(G.calendar_fresh(cal, DAY, [data], 0, LOCAL)[0])

    def test_final_allows_the_minute_between_the_read_and_the_fetch(self):
        # 11 Nov 2026: calendars read at 6:40, the fetch landed at 6:41, and final FIXed the tie
        cal, data = self.files(self.at('06:40'), self.at('06:41'))
        self.assertTrue(G.calendar_fresh(cal, DAY, [data], 10, LOCAL)[0])
        cal, data = self.files(self.at('06:40'), self.at('07:10'))
        self.assertFalse(G.calendar_fresh(cal, DAY, [data], 10, LOCAL)[0])
        cal, data = self.files(self.at('22:35'), self.at('22:30'))         # the day done: fetch, then the calendars
        self.assertTrue(G.calendar_fresh(cal, DAY, [data], 0, LOCAL)[0])

    def test_yesterdays_read_is_stale(self):
        cal, data = self.files(self.at('21:00', DAY - dt.timedelta(days=1)), self.at('06:00'))
        self.assertIn('before Thu 05 Nov began', G.calendar_fresh(cal, DAY, [data], 9999, LOCAL)[2])
        cal, data = self.files(self.at('06:40'), self.at('06:30'), today='2026-11-04')
        self.assertIn('the read for 2026-11-04', G.calendar_fresh(cal, DAY, [data], 90, LOCAL)[2])
        self.assertFalse(G.calendar_fresh(os.path.join(tempfile.mkdtemp(), 'cal.json'), DAY, [data], 90, LOCAL)[0])

    def test_final_names_the_calendar(self):
        cal, data = self.files(self.at('06:40'), self.at('22:30'))
        d = os.path.dirname(cal)
        page = os.path.join(d, 'p.html')
        with open(page, 'w') as fh:
            fh.write('<html></html>')
        got = G.whole([sleep()], DAY, LOCAL, page, [data], cal)
        self.assertEqual([w for ok, w, _ in got if not ok], ['calendar'])


class Preflight(unittest.TestCase):
    """The morning's first line follows the gate: it offers the day ahead and its QA, never a day behind."""
    TODAY = dt.date(2026, 11, 6)
    URL = 'https://claude.ai/artifact/LIVING'

    def lb(self, state='final'):
        return {'datetime': '2026-11-06T09:00:00.000Z', 'created': '2026-11-06T09:01:00.000Z',
                'details': f'———\n[be•do] look behind 2026-11-05 · {state}', 'deliverable': self.URL, 'practice': '📝 log'}

    def first(self, rows):
        return P.yesterday_line(self.TODAY, self.URL, P.built_pages(rows), rows)

    def test_unfinished_offers_the_day_ahead_and_never_a_day_behind(self):
        text = self.first([close()])
        self.assertIn("yesterday's my day page isn't finished: Thu 05 Nov", text)
        self.assertIn("Offer to finish yesterday's day ahead", text)
        self.assertNotIn('run its QA', text)                                 # the QA is there already
        self.assertNotIn('look behind', text)

    def test_unfinished_on_the_qa_offers_the_qa(self):
        text = self.first([look_ahead(), close(qa=False)])
        self.assertIn("its dayqa isn't in the dusk close row", text)
        self.assertIn('Offer to run its QA', text)
        self.assertIn(', then run its QA', self.first([]))                  # her order: the day ahead, then the QA

    def test_finished_needs_no_day_behind(self):
        # 8 Nov 2026: the day behind is retired, so a finished day never asks for one
        text = self.first([look_ahead(), close()])
        self.assertIn("yesterday's my day page is final and QA'd", text)
        self.assertIn('becomes', text)
        self.assertNotIn('look behind', text)
        self.assertNotIn('build', text)

    def test_unread_rows_claim_nothing(self):
        # 8 Nov 2026: a thin read told her a finished Saturday wasn't
        text = P.yesterday_line(self.TODAY, self.URL, None, None)
        self.assertIn('not checked', text)
        self.assertIn('say nothing', text)
        self.assertNotIn('Offer', text)

    def test_the_report_carries_it(self):
        local = dict(LOCAL, look_behind_url=self.URL)
        now = dt.datetime(2026, 11, 6, 14, 30, tzinfo=dt.timezone.utc)
        rows = [{'datetime': '2026-11-06T13:00:00.000Z'}]
        log = [close()]
        text, _ = P.report(local, {'w45 be•do': 'a'}, rows, now, built=P.built_pages(log), log_rows=log)
        self.assertIn("yesterday's my day page isn't finished", text)


if __name__ == '__main__':
    unittest.main()
