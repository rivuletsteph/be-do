# -*- coding: utf-8 -*-
"""Reconciling what she did against her open steps (20 Nov 2026, her words: you
suck at reconciling what I actually did with the tasks … you need to be smarter
about it). The Thursday 19 Nov cases, in their shape before they were closed by
hand; names and drives are invented.

    python3 plugins/bedo/core/tests/test_dayqa_reconcile.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
sys.path.append(os.path.join(os.path.dirname(CORE), 'skills', 'bedo-week-look-behind', 'scripts'))
import bedo_dayqa as Q  # noqa: E402

DAY = dt.date(2026, 11, 19)
OFF = -6
L = {'utc_offset_hours': -6, 'time_zone': 'America/Chicago', 'system_rhythm': 'the system'}


def z(h, m=0, d=DAY):
    return (dt.datetime.combine(d, dt.time(h, m)) + dt.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:00.000Z')


def row(rid, **kw):
    r = {'id': rid, 'datetime': z(9), 'status': '● log', 'practice': '📝 log', 'title': 'a note'}
    r.update(kw)
    return r


# the step made on 5 Nov and answered on Thursday, its [be•do] block naming the step
HELP = row('recHelp', title='⚡ Help Dana with the river intake tables when Dana gets back to me', status='⬜ intention',
           practice='⚡ action', key='261105_1153', rhythm='River Intake', datetime=z(11, 53, dt.date(2026, 11, 5)),
           target=z(14))
ANSWERED = row('recAns', title="⚡ The reviewer's Table C questions 13–16 answered with Dana; datum re-query",
               status='✅ done', practice='⚡ action', key='261119_1324', rhythm='River Intake',
               datetime=z(13, 24), end=z(15, 16),
               details='Went through them together.\n———\n[be•do] drive: River Intake, from the intention row this '
                       'work answers (261105_1153 “Help Dana with the tables”). That row is still ⬜; closing it is '
                       "my day's call.")
# two steps for the day with no key: one happened, one was called off
LEAVE = row('recLeave', title='⚡ Leave the office by 3:15, meet my partner at the house at 3:30', status='⬜ intention',
            practice='⚡ action', rhythm='Taxes', datetime=z(9, 36), target=z(15, 15))
PICKUP = row('recPick', title='🚗 Drive to the next town to get Robin, arrive by 5:15', status='⬜ intention',
             practice='🚗 travel', rhythm='Raising My Son', datetime=z(9, 30), target=z(17, 15))
TAXES = row('recTax', title='⚡ Tax prep — do the taxes, get everything to the preparer, organize the office papers', status='✅ done',
            practice='⚡ action', rhythm='Taxes', key='260831_1000', datetime=z(15, 51), end=z(16))
TEXT = row('recText', title='🗨️ texted Mom that Robin could stay another night; he wants to', practice='🗨️ text',
           rhythm='Raising My Son', datetime=z(11, 58))
# her colleague's name is in many titles, so it names nothing in particular (on Thursday only “table” was left)
CROWD = [row(f'recC{i}', title=f'📝 a word with Dana about thing {i}', datetime=z(8, i)) for i in range(3)]


class NamedInItsBlock(unittest.TestCase):
    def test_a_done_row_naming_the_steps_key_closes_it(self):
        items = Q.reconcile([ANSWERED], [HELP], OFF)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['patch']['fields'], {'status': '✅ done', 'end': z(15, 16)})
        self.assertIn('named in its block', items[0]['line'])

    def test_a_row_that_says_the_step_stays_open_does_not_close_it(self):
        # 23 Nov 2026: a session entry said "the build row (key) stays open", and the braid proposed closing it
        key = HELP['key']
        OTHER = dict(ANSWERED, title='⚡ A long session about other things')   # its words alone close nothing
        for words in (f'what I did\n· moved a thing\n\nstill open\n· the build row ({key}) for a later session',
                      f'· the build row ({key}) stays open for a later session',
                      f'[be•do] {key} is not done yet.'):
            self.assertEqual(Q.reconcile([dict(OTHER, details=words)], [HELP], OFF), [], words)
        # the same row answering it plainly still closes it
        self.assertEqual(len(Q.reconcile([dict(OTHER, details=f'[be•do] answers {key}.')], [HELP], OFF)), 1)

    def test_its_own_key_in_its_block_names_nothing(self):
        own = dict(ANSWERED, key='261105_1153', details='[be•do] 261105_1153 is this row.', status='● log')
        self.assertEqual(Q.reconcile([own], [dict(HELP, rhythm=None, title='call the clinic')], OFF), [])

    def test_a_log_naming_the_key_is_not_a_close(self):
        note = dict(ANSWERED, status='● log', title='a thought about it', rhythm=None)
        self.assertEqual(Q.reconcile([note], [dict(HELP, title='something else entirely')], OFF), [])


class SameDrive(unittest.TestCase):
    def test_one_uncommon_word_on_the_same_drive_closes(self):
        bare = dict(ANSWERED, details='')                  # no key named: the drive and “table” carry it
        items = Q.reconcile([bare] + CROWD, [HELP], OFF)
        self.assertEqual(len(items), 1)
        self.assertIn('the same drive, its words: table', items[0]['line'])

    def test_one_word_on_another_drive_is_not_enough(self):
        bare = dict(ANSWERED, details='', rhythm='Another Drive')
        self.assertEqual(Q.reconcile([bare] + CROWD, [HELP], OFF), [])

    def test_the_systems_own_drive_needs_two_words(self):
        a = dict(HELP, rhythm='the system', title='⚡ the day page heading in plain words', key=None)
        b = dict(ANSWERED, rhythm='the system', details='', title='⚡ week page fixes')
        self.assertEqual(Q.reconcile([b], [a], OFF, 'the system'), [])

    def test_words_still_never_close_a_step_days_from_its_date(self):
        later = dict(HELP, target=z(14, 0, dt.date(2026, 11, 24)), key=None)
        self.assertEqual(Q.reconcile([dict(ANSWERED, details='')], [later], OFF), [])


class DueToday(unittest.TestCase):
    def test_every_step_for_today_nothing_closed_gets_a_line(self):
        items = Q.due([TAXES, TEXT], [LEAVE, PICKUP, HELP], OFF, DAY)
        got = {i['line'].split('”')[0][1:]: i for i in items}
        leave = next(i for i in items if 'Leave the office' in i['line'])
        self.assertEqual(leave['kind'], 'fill')                          # a done row on its drive at that time
        self.assertTrue(leave['tell'])                                   # settled by the record: written, then told (21 Nov)
        self.assertIn('done — ', leave['line'])
        self.assertEqual(leave['patch']['fields'], {'status': '✅ done', 'end': z(16)})
        pick = next(i for i in items if 'next town' in i['line'])
        self.assertEqual(pick['kind'], 'ask')                            # a later row says it changed
        self.assertIn('moved or dropped', pick['line'])
        self.assertIn('another night', pick['line'])
        help_ = next(i for i in items if 'Help Dana' in i['line'])
        self.assertEqual((help_['kind'], help_['line'].split(': ')[-1]), ('ask', 'done, moved or dropped?'))
        self.assertEqual(len(got), 3)

    def test_what_reconcile_closed_and_other_days_are_left(self):
        tomorrow = dict(LEAVE, id='recTom', target=z(15, 0, dt.date(2026, 11, 20)))
        self.assertEqual(Q.due([], [HELP, tomorrow], OFF, DAY, closed={'recHelp'}), [])

    def test_last_weeks_copy_of_a_step_closed_this_week_is_not_due(self):
        closed_here = dict(LEAVE, status='✅ done', end=z(15, 40))        # the split keeps a row's id in both weeks
        self.assertEqual(Q.due([closed_here], [LEAVE], OFF, DAY), [])

    def test_a_calendared_step_her_calendar_marks_done(self):
        link = 'https://calendar.example.invalid/event?eid=abcXYZ'
        step = dict(LEAVE, rhythm=None, title='⚡ the client party', calendar_event=link)
        ev = {'summary': '✔️ the client party', 'id': 'abc', 'htmlLink': link,
              'start': {'dateTime': f'{DAY}T16:00:00-06:00'}, 'end': {'dateTime': f'{DAY}T18:00:00-06:00'}}
        items = Q.due([], [step], OFF, DAY, events=[ev])
        self.assertEqual(items[0]['kind'], 'fill')
        self.assertEqual(items[0]['patch']['fields']['end'], z(18))


class Thursday(unittest.TestCase):
    def test_the_whole_day_closes_one_and_asks_two_near_the_top(self):
        rows = CROWD + [ANSWERED, TAXES, TEXT, row('recLunch', title='🍽️ lunch at the potluck', practice='🍽️ lunch',
                                            datetime=z(12, 22), end=z(12, 42))]
        items = Q.run(rows, DAY, OFF, L, opens=[HELP, LEAVE, PICKUP])
        numbered = [i for i in items if i.get('n')]
        self.assertEqual(numbered[0]['check'], 'reconcile')
        self.assertIn('Help Dana', numbered[0]['line'])
        checks = [i['check'] for i in numbered]
        self.assertEqual(checks[:3], ['reconcile', 'reconcile', 'due'])   # the office step closes on its drive's word
        self.assertIn('next town', numbered[2]['line'])
        self.assertFalse(any(i['check'] == 'due' and 'Help Dana' in i['line'] for i in items))
        text = Q.render(items, DAY, rows, OFF)
        self.assertIn('1 to answer', text)


# the drives (20 Nov 2026): Thursday's taxes, signed and filed, on a drive with no goal
TAXDRIVE = {'Taxes': dict(id='recD', name='Taxes', type='♐ drive', code='D1', goal='', target=None, open_ended=False, parent=''),
            'River Intake': dict(id='recR', name='River Intake', type='♐ drive', code='D2', goal='Intake tables for the river permit, reviewed',
                                 target=None, open_ended=False, parent=''),
            'the system': dict(id='recS', name='the system', type='♐ drive', code='D3', goal='', target=None, open_ended=False, parent='')}
FILED = row('recFiled', title='⚡ Tax prep — do the taxes, get everything to the preparer', status='✅ done', practice='⚡ action',
            rhythm='Taxes', key='260831_1000', datetime=z(15, 51), end=z(16),
            calendar_event='https://calendar.example.invalid/event?eid=taxXYZ',     # on her calendar, still an action
            details='The tax prep has been done, and now it is just waiting on her.\nYes, we signed, and they will have been filed today.'
                    '\n———\n[be•do] closed at her word.')
STATEMENT = row('recStmt', title='⚡ The year-end statement from the school, for the taxes', status='⬜ intention',
                practice='⚡ action', rhythm='Taxes', key='260930_1817', datetime=z(18, 17, dt.date(2026, 9, 30)))


class Drives(unittest.TestCase):
    def test_a_step_carried_for_months_lands_a_milestone_in_her_words(self):
        items = Q.drives([FILED], [STATEMENT], OFF, DAY, TAXDRIVE)
        moved = [i for i in items if i['kind'] == 'moved']
        self.assertIn('Taxes: 1 action closed', moved[0]['line'])
        self.assertIn('1 open', moved[0]['line'])
        mile = next(i for i in items if i['kind'] == 'fill')
        self.assertEqual(mile['new']['practice'], '🪨 milestone')
        self.assertEqual(mile['new']['rhythm'], 'Taxes')
        self.assertTrue(mile['new']['details'].startswith('Yes, we signed, and they will have been filed today.'))
        self.assertIn('carried since 31 Aug', mile['line'])
        self.assertTrue(any(i['kind'] == 'ask' and 'no goal yet' in i['line'] for i in items))
        self.assertTrue(any('one step left' in i['line'] for i in moved))

    def test_a_meeting_from_the_calendar_is_not_carried(self):
        meet = dict(FILED, id='recMeet', practice='🗓️ calendar event', title='the team meeting', key='261001_0900', details='')
        self.assertFalse(any(i['kind'] == 'fill' for i in Q.drives([meet], [STATEMENT], OFF, DAY, TAXDRIVE)))

    def test_a_milestone_already_written_is_not_proposed_again(self):
        mark = row('recM', practice='🪨 milestone', title='🪨 the returns signed and filed', rhythm='Taxes', datetime=z(20))
        items = Q.drives([FILED, mark], [STATEMENT], OFF, DAY, TAXDRIVE)
        self.assertFalse(any(i['kind'] == 'fill' for i in items))

    def test_a_proposed_close_counts_and_the_last_step_asks_about_the_goal(self):
        items = Q.drives([ANSWERED], [HELP], OFF, DAY, TAXDRIVE, closing={'recHelp': z(15, 16)})
        line = next(i for i in items if i['kind'] == 'moved')['line']
        self.assertIn('2 actions closed', line)
        self.assertIn('if you accept it above', line)
        self.assertIn('goal: Intake tables', line)
        self.assertTrue(any(i['kind'] == 'ask' and 'nothing is open on River Intake' in i['line'] for i in items))

    def test_the_systems_own_drive_and_a_bare_rhythm_are_left_out(self):
        work = dict(FILED, rhythm='the system', key='261119_0836')
        loose = dict(FILED, id='recL', rhythm='Around the House')
        self.assertEqual(Q.drives([work, loose], [], OFF, DAY, TAXDRIVE, system='the system'), [])

    def test_they_lead_her_list_under_one_heading(self):
        rows = CROWD + [ANSWERED, FILED, TEXT]
        items = Q.run(rows, DAY, OFF, L, opens=[HELP, PICKUP, STATEMENT], drive_b=TAXDRIVE, catalog_names=['🪨 milestone'])
        text = Q.render(items, DAY, rows, OFF)
        self.assertTrue(text.startswith(Q.Q.get('together_heading') + ' · '))
        self.assertIn('the threads — your actions and your drives:', text)
        self.assertLess(text.index('↳ Taxes'), text.index('the rest of the day') if 'the rest of the day' in text else len(text))
        self.assertLess(text.index('reconcile ·'), text.index('🪨 a milestone on Taxes'))


class TheBraidsMarker(unittest.TestCase):
    def test_the_new_line_and_the_old_one_both_read_as_done(self):
        import bedo_close as C, bedo_daygate as G
        old = {'practice': '🌄 dusk flow close', 'details': '———\n[be•do] closed.\ndayqa shown 2026-11-19 23:55 · 4 proposed'}
        new = {'practice': '🌄 dusk flow close', 'details': '———\n[be•do] closed.\nbraid shown 2026-11-20 23:55 · 4 proposed'}
        self.assertTrue(C.qa_done([old], DAY))
        self.assertTrue(C.qa_done([new], DAY + dt.timedelta(days=1)))
        self.assertTrue(G.dayqa_shown([old], DAY)[0])
        self.assertTrue(Q.marker(DAY, 0).startswith('braid shown 2026-11-19'))


if __name__ == '__main__':
    unittest.main()
