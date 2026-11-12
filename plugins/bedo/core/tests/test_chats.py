# -*- coding: utf-8 -*-
"""The chat sweep (her amendment, 2 Nov 2026; built 5 Nov). Every chat and
row is invented; the shapes are list_sessions' and the base's.

    python3 plugins/bedo/core/tests/test_chats.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_chats as CH  # noqa: E402

NOW = dt.datetime(2026, 11, 5, 21, 0, tzinfo=dt.timezone.utc)
MET = 'what I did\n· objective: the rainfall memo — met, written and read through\n· wrote it\n\nstill open\n· none\n———\n[be•do] x'
PARTLY = ('what I did\n· objective: the place database — partly met, one month built\n· built September\n\n'
          'still open\n· build October from the new export\n———\n[be•do] x')


def chat(n, title, days_ago=2.0, **kw):
    last = (NOW - dt.timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return {'sessionId': f'local_0000000{n}-aaaa-bbbb-cccc-00000000000{n}', 'title': title, 'isArchived': False,
            'isRunning': False, 'lastActivityAt': last, **kw}


def row(n, status='✅ done', details=MET, key='261101_0900', chat_url=None):
    return {'id': f'rec{n}', 'created': '2026-11-01T15:00:00.000Z', 'practice': '⚡ action', 'status': status,
            'key': key, 'title': 'a session', 'datetime': '2026-11-01T15:00:00.000Z', 'details': details,
            'chat': chat_url or f'claude://claude.ai/epitaxy/local_0000000{n}-aaaa-bbbb-cccc-00000000000{n}'}


LOCAL = {'time_zone': 'America/Chicago', 'utc_offset_hours': -6}


def run(chats, rows):
    return {x['title']: x for x in CH.sweep(CH.chats_of([chats]), rows, NOW, LOCAL)}


class Finished(unittest.TestCase):
    def test_done_and_logged_is_archived(self):
        got = run([chat(1, '☑️💦P03.9 Rainfall memo')], [row(1)])
        self.assertEqual(got['☑️💦P03.9 Rainfall memo']['verdict'], 'archive')

    def test_done_chat_with_a_moving_row_closes_the_row(self):
        got = run([chat(1, '☑️💦P03.9 Rainfall memo')], [row(1, status='▶️ in motion')])
        self.assertEqual(got['☑️💦P03.9 Rainfall memo']['verdict'], 'close_row')

    def test_objective_not_met_carries_its_next_step(self):
        got = run([chat(1, '☑️ Place database')], [row(1, details=PARTLY)])['☑️ Place database']
        self.assertEqual(got['verdict'], 'carry')
        self.assertIn('October', got['next'])

    def test_finished_with_no_row_gets_an_entry(self):
        got = run([chat(1, '☑️ Something done')], [])
        self.assertEqual(got['☑️ Something done']['verdict'], 'entry')

    def test_window_and_dropped_chats_archive(self):
        got = run([chat(1, '✔️🔆1101 ☀️ Sun W45 my day'), chat(2, '✖️ News skill')], [])
        self.assertEqual({x['verdict'] for x in got.values()}, {'archive'})

    def test_row_done_and_met_archives_even_with_a_moving_title(self):
        got = run([chat(1, '▶️💦P03.9 Rainfall memo')], [row(1)])
        self.assertEqual(got['▶️💦P03.9 Rainfall memo']['verdict'], 'archive')

    def test_pinned_finished_chat_is_unpinned_then_archived(self):
        # her rule, 11 Nov 2026: a finished pinned chat is unpinned and archived
        got = run([chat(1, '☑️ Pinned one', pinned=True)], [row(1)])
        self.assertEqual(got['☑️ Pinned one']['verdict'], 'archive')
        self.assertTrue(got['☑️ Pinned one']['unpin'])

    def test_pinned_chat_in_motion_and_touched_today_stays_pinned(self):
        got = run([chat(1, '▶️ Pinned work', pinned=True, days_ago=2 / 24)], [row(1, status='▶️ in motion')])
        self.assertEqual(got['▶️ Pinned work']['verdict'], 'keep')
        self.assertFalse(got['▶️ Pinned work']['unpin'])

    def test_pinned_chat_in_motion_not_touched_today_is_unpinned(self):
        # her amendment, 12 Nov 2026: pinned is what she's on that day
        got = run([chat(1, '▶️ Pinned work', pinned=True, days_ago=1)], [row(1, status='▶️ in motion')])
        self.assertEqual(got['▶️ Pinned work']['verdict'], 'unpin')
        self.assertTrue(got['▶️ Pinned work']['unpin'])


class InMotion(unittest.TestCase):
    def test_quiet_for_more_than_a_week_goes_on_her_list(self):
        got = run([chat(1, '▶️ Old work', days_ago=10)], [row(1, status='▶️ in motion')])
        self.assertEqual(got['▶️ Old work']['verdict'], 'ask')

    def test_touched_this_week_is_kept(self):
        got = run([chat(1, '▶️ Live work', days_ago=2)], [row(1, status='▶️ in motion')])
        self.assertEqual(got['▶️ Live work']['verdict'], 'keep')

    def test_her_keep_sticks_for_a_week(self):
        kept = MET.replace('[be•do] x', '[be•do] x\n' + CH.keep_line(dt.date(2026, 11, 2)))
        got = run([chat(1, '▶️ Old work', days_ago=20)], [row(1, status='▶️ in motion', details=kept)])
        self.assertEqual(got['▶️ Old work']['verdict'], 'keep')
        old = MET.replace('[be•do] x', '[be•do] x\n' + CH.keep_line(dt.date(2026, 10, 20)))
        got = run([chat(1, '▶️ Old work', days_ago=20)], [row(1, status='▶️ in motion', details=old)])
        self.assertEqual(got['▶️ Old work']['verdict'], 'ask')

    def test_a_break_is_never_nudged(self):
        got = run([chat(1, '⏸️ Set down', days_ago=40)], [row(1, status='▶️ in motion')])
        self.assertEqual(got['⏸️ Set down']['verdict'], 'keep')

    def test_no_row_gets_an_entry_until_it_goes_quiet(self):
        got = run([chat(1, '▶️ New work', days_ago=1), chat(2, 'Untitled thing', days_ago=9)], [])
        self.assertEqual(got['▶️ New work']['verdict'], 'entry')
        self.assertEqual(got['Untitled thing']['verdict'], 'ask')


class LeftAlone(unittest.TestCase):
    def test_a_chat_she_just_touched_is_busy(self):
        got = run([chat(1, '☑️ Closing it now', days_ago=5 / 1440)], [row(1)])
        self.assertEqual(got['☑️ Closing it now']['verdict'], 'busy')

    def test_a_running_chat_is_busy(self):
        got = run([chat(1, '☑️ Working', isRunning=True)], [row(1)])
        self.assertEqual(got['☑️ Working']['verdict'], 'busy')

    def test_archived_chats_and_routines_are_not_swept(self):
        got = run([chat(1, '☑️ Gone', isArchived=True), chat(2, 'Weekly status', tags=['trigger'])], [])
        self.assertNotIn('☑️ Gone', got)
        self.assertEqual(got['Weekly status']['verdict'], 'routine')

    def test_a_parent_waits_for_a_side_chat_that_is_not_ready(self):
        parent = chat(1, '☑️ Parent work')
        kid = chat(2, '☑️ Side work', startedBy=parent['sessionId'])
        got = run([parent, kid], [row(1)])
        self.assertEqual(got['☑️ Side work']['verdict'], 'entry')
        self.assertEqual(got['☑️ Parent work']['verdict'], 'hold')


class Links(unittest.TestCase):
    def test_a_cloud_chat_matches_its_session_link(self):
        cloud = {'id': 'cse_01EXAMPLEcloud', 'title': '☑️ Cloud work', 'status': 'active',
                 'last_event_at': '2026-11-03T15:00:00Z'}
        r = row(9, chat_url='https://claude.ai/code/session_01EXAMPLEcloud')
        self.assertEqual(run([cloud], [r])['☑️ Cloud work']['verdict'], 'archive')

    def test_a_link_in_the_block_counts_when_the_chat_field_holds_another(self):
        r = row(9, details=MET + '\nalso: https://claude.ai/code/session_01EXAMPLEsecond')
        cloud = {'id': 'cse_01EXAMPLEsecond', 'title': '☑️ Same work, phone', 'last_event_at': '2026-11-03T15:00:00Z'}
        self.assertEqual(run([cloud], [r])['☑️ Same work, phone']['verdict'], 'archive')

    def test_two_lists_count_a_chat_once(self):
        c = chat(1, '☑️ Rainfall memo')
        self.assertEqual(len(CH.chats_of([[c], [c]])), 1)


class Render(unittest.TestCase):
    def test_render_groups_and_names_the_after_line(self):
        found = CH.sweep(CH.chats_of([[chat(1, '☑️ Done one'), chat(2, '▶️ Old one', days_ago=12)]]),
                         [row(1), row(2, status='▶️ in motion')], NOW)
        text = CH.render(found, NOW)
        self.assertIn('on its own', text)
        self.assertIn('hers, one short list', text)
        self.assertIn('archived 1 finished chat', text)


if __name__ == '__main__':
    unittest.main()
