# -*- coding: utf-8 -*-
"""The four V53 slots that used to depend on a chat remembering: preflight,
the remaining list, stretches and the dusk audit. Each test is the way the
rule actually broke. Every row is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_slots.py
"""
import datetime as dt, json, os, sys, tempfile, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_reader as R  # noqa: E402
import bedo_preflight as P  # noqa: E402
import bedo_remaining as RL  # noqa: E402
import bedo_stretches as ST  # noqa: E402
import bedo_dusk_audit as D  # noqa: E402

F = R.FACTS
ACTION, CAPTURE = F['practice']['action'], F['practice']['capture']
INT, MOT, DONE = '⬜ intention', '▶️ in motion', '✅ done'
DONE_LOG = '◉ done'
LOCAL = {'weekly_name': 'w{n} be•do', 'utc_offset_hours': -5, 'time_zone': 'America/Chicago'}
UTC = dt.timezone.utc


def z(s):
    """Local Central daylight time 'YYYY-MM-DD HH:MM' → the stored UTC string."""
    t = dt.datetime.fromisoformat(s) + dt.timedelta(hours=5)
    return t.strftime('%Y-%m-%dT%H:%M:00.000Z')


def at(s):
    return dt.datetime.fromisoformat(z(s).replace('Z', '+00:00'))


_n = [0]


def row(practice, when=None, **kw):
    _n[0] += 1
    r = {'id': f'rec{_n[0]:04d}', 'created': '2026-10-03T12:00:00.000Z', 'practice': practice,
         'datetime': z(when) if when else None}
    r.update(kw)
    return r


def step(name, phase, order=None, group='flow', active=True):
    return {'practice': name, 'phase': F['flows']['phase'][phase], 'order': order, 'group': group,
            'active': active}


# ── stretches ──────────────────────────────────────────────────────────────
class Stretches(unittest.TestCase):
    def test_an_envelope_is_not_a_stretch(self):
        # 3 Oct: 6:50–11:35 PM was counted as one block. Dinner sat in between.
        msgs = [at(f'2026-10-03 {t}') for t in ('18:50', '19:00', '19:14', '19:28', '19:42',
                                                 '22:15', '22:29', '22:40', '23:10', '23:22', '23:35')]
        spans = ST.stretches(msgs)
        self.assertEqual(len(spans), 3)                      # 22:40 → 23:10 is a 30-minute gap
        envelope = (msgs[-1] - msgs[0]).total_seconds() / 60
        self.assertEqual(envelope, 285)
        self.assertEqual(ST.minutes(spans), 52 + 25 + 25)
        self.assertEqual(ST.named(spans, -5), '6:50–7:42 · 10:15–10:40 · 11:10–11:35 = 1h 42m')

    def test_the_gap_is_over_fifteen_not_at_it(self):
        a = at('2026-10-03 09:00')
        self.assertEqual(len(ST.stretches([a, a + dt.timedelta(minutes=15)])), 1)
        self.assertEqual(len(ST.stretches([a, a + dt.timedelta(minutes=16)])), 2)

    def test_a_lone_message_is_never_padded(self):
        spans = ST.stretches([at('2026-10-03 09:00')])
        self.assertEqual(ST.minutes(spans), 0)

    def test_a_stretch_with_no_capture_is_named(self):
        spans = ST.stretches([at('2026-10-03 09:00'), at('2026-10-03 09:10'),
                              at('2026-10-03 14:00'), at('2026-10-03 14:10'), at('2026-10-03 14:20')])
        caps = [(z('2026-10-03 09:00'), z('2026-10-03 09:10'))]
        left = ST.uncaptured(spans, caps)
        self.assertEqual(len(left), 1)
        self.assertEqual(ST.named(left, -5), '2:00–2:20 = 20m')
        self.assertEqual(ST.uncaptured(spans, caps + [(z('2026-10-03 14:05'), None)]), [])

    def test_a_window_chats_row_has_no_duration_and_no_drive(self):
        # 3 Oct: 4h 04m on the captures AND on the row drew 8h 13m of doing.
        title = '▶️1003 ⏳ Sat ' + P.MARK + ' W40 🔆 my day'
        bad = ST.action_row_problems({'time_spent': 14640, 'rhythm': 'be•do'}, title)
        self.assertEqual(len(bad), 2)
        self.assertEqual(ST.action_row_problems({}, title), [])

    def test_a_drive_chats_time_is_the_sum_of_its_stretches(self):
        title = '▶️' + P.MARK + 'D6.53 V53 next slots'
        self.assertEqual(ST.action_row_problems({'time_spent': 3600}, title, 60), [])
        self.assertIn('envelope', ST.action_row_problems({'time_spent': 5 * 3600}, title, 60)[0])

    def test_stamps_from_what_a_chat_can_hand_over(self):
        self.assertEqual(ST.times_from(['2026-10-03T14:00:00Z']), ['2026-10-03T14:00:00Z'])
        conv = {'chat_messages': [{'created_at': '2026-10-03T14:00:00Z'}, {'created_at': '2026-10-03T14:05:00Z'}]}
        self.assertEqual(len(ST.times_from(conv)), 2)
        with tempfile.NamedTemporaryFile('w', suffix='.jsonl', delete=False, encoding='utf-8') as fh:
            fh.write(json.dumps({'type': 'user', 'timestamp': '2026-10-03T14:00:00Z'}) + '\n')
            fh.write(json.dumps({'type': 'summary'}) + '\n')
            fh.write(json.dumps({'type': 'assistant', 'timestamp': '2026-10-03T14:02:00Z'}) + '\n')
            fh.write('{"type": "user", "timest')               # a live transcript, mid-write
        try:
            self.assertEqual(ST.times_from(fh.name), ['2026-10-03T14:00:00Z', '2026-10-03T14:02:00Z'])
        finally:
            os.unlink(fh.name)


# ── the remaining list ─────────────────────────────────────────────────────
CAT = [step('🥤 morning water', 'dawn', 2), step('🔅 morning sun', 'dawn', 3),
       step('🤸🏻‍♀️ morning movement', 'dawn', 4), step('☕ coffee', 'dawn', 6),
       step('🤲 sun salutations', 'dawn', 5, active=False),
       step('📿 morning mantra', 'dawn', 11.7), step('🌅 dawn flow close', 'dawn', 16),
       step('🪞 mirror check', 'dawn', 20, group='optional'), step('😶 wake', 'dawn', None),
       step('🫖 evening tea', 'dusk', 34), step('🌬️ evening breaths', 'dusk', 35),
       step('🌄 dusk flow close', 'dusk', 49), step('a quest child', 'dusk', None, group='a quest'),
       step('a quest day', 'dusk', 42.1, group='a quest')]


class Remaining(unittest.TestCase):
    def test_built_from_the_catalog_in_predicted_order(self):
        names = [s['practice'] for s in RL.flow_steps(CAT, 'dawn')]
        self.assertNotIn('🤲 sun salutations', names)           # inactive
        self.assertEqual(names[0], '🥤 morning water')
        self.assertEqual(names[-1], '😶 wake')                   # no order goes last
        self.assertLess(names.index('📿 morning mantra'), names.index('🌅 dawn flow close'))

    def test_A127_a_catalog_step_is_never_dropped_from_the_list(self):
        # 11 Sep: 🌬️ evening breaths was left off the dusk list all evening.
        dusk = [s['practice'] for s in RL.flow_steps(CAT, 'dusk')]
        self.assertIn('🌬️ evening breaths', dusk)
        self.assertIn('a quest day', dusk)                       # ordered into the flow
        self.assertNotIn('a quest child', dusk)                  # not a flow step

    def test_remainders_only_bare_names_core_then_one_line(self):
        day = [row('🥤 morning water', '2026-10-04 07:00', status=DONE_LOG),
               row('☕ coffee', '2026-10-04 07:30', status='⨂ skipped')]
        text = RL.render('dawn', RL.flow_steps(CAT, 'dawn'), day)
        block, also = text.split('\n```\n')
        self.assertIn('2 of 8 done', block)
        self.assertNotIn('🥤', block)                             # done steps are left off
        self.assertNotIn('☕', block)                             # skipped is captured too
        self.assertIn('\n📿 morning mantra\n', block)              # the name alone (A227)
        self.assertEqual(also, 'also: 🔅 morning sun · 🪞 mirror check · 😶 wake')

    def test_a_skin_tone_is_the_same_step(self):
        day = [row('🤸‍♀️ morning movement', '2026-10-04 07:10', status=DONE_LOG)]
        self.assertNotIn('morning movement', RL.render('dawn', RL.flow_steps(CAT, 'dawn'), day))

    def test_only_required_steps_hold_the_flow_open(self):
        steps = RL.flow_steps(CAT, 'dawn')
        held = RL.holds_open(steps, [], 'dawn')
        self.assertNotIn('🪞 mirror check', held)                 # optional
        self.assertNotIn('🔅 morning sun', held)                  # collapsed off the core
        self.assertNotIn('🌅 dawn flow close', held)              # the close itself
        self.assertIn('📿 morning mantra', held)

    def test_which_flow_is_open(self):
        sun = dt.datetime(2026, 10, 4, 8, 0)
        self.assertEqual(RL.open_flow(sun, []), 'dawn')
        self.assertIsNone(RL.open_flow(sun.replace(hour=12, minute=1), []))     # A126: noon ends the ask
        self.assertIsNone(RL.open_flow(sun, [row('🌅 dawn flow close', '2026-10-04 07:55')]))
        self.assertEqual(RL.open_flow(sun.replace(hour=19, minute=5), []), 'dusk')
        self.assertIsNone(RL.open_flow(sun.replace(hour=22), [row('🌄 dusk flow close', '2026-10-04 21:00')]))

    def test_all_done_and_the_spoken_line(self):
        steps = RL.flow_steps(CAT, 'dusk')
        day = [row(s['practice'], '2026-10-04 20:00', status=DONE_LOG) for s in steps]
        self.assertIn('all 4 done', RL.render('dusk', steps, day))
        self.assertEqual(RL.spoken('dusk', steps, day[:1]), 'dusk: 3 left, next is 🌬️ evening breaths.')

    def test_the_catalog_read_must_be_complete(self):
        src = {'records': [{'id': 'r1', 'createdTime': 'x', 'fields': {'practice': '☕ coffee'}}],
               'metadata': {'totalRecordCount': 2}}
        with self.assertRaises(SystemExit):
            RL.catalog(src)


# ── preflight ──────────────────────────────────────────────────────────────
class Preflight(unittest.TestCase):
    def test_the_chat_name_line_is_derived(self):
        line = P.chat_name(dt.date(2026, 10, 4))
        self.assertEqual(line, '▶️1004 ☀️ Sun ' + P.MARK + ' W41 🔆 my day')
        self.assertEqual(ord(P.MARK), 0x1684E)
        self.assertEqual(P.chat_name(dt.date(2026, 9, 18), part=2, status='✔️'),
                         '✔️0918 🏆 Fri ' + P.MARK + ' W38 🔆 my day P2')
        self.assertEqual(P.chat_name(dt.date(2026, 10, 4), 'week', week=40), '▶️' + P.MARK + ' my week W40')
        self.assertNotIn('be•do', line)

    def test_sunday_names_last_weeks_base_too(self):
        self.assertEqual(P.bases_in_play(dt.date(2026, 10, 4), LOCAL), ['w41 be•do', 'w40 be•do'])
        self.assertEqual(P.bases_in_play(dt.date(2026, 10, 6), LOCAL), ['w41 be•do'])

    def _check(self, names, rows, now='2026-10-06 09:00', handoff=None):
        n = at(now)
        return P.check_base(names, rows, n, (n - dt.timedelta(hours=5)).date(), LOCAL, handoff)

    def test_the_base_is_found_by_name_and_is_live(self):
        names = {'w41 be•do': 'app1'}
        _, out, stop = self._check(names, [row('☕ coffee', '2026-10-06 07:30')])
        self.assertEqual((out, stop), ([], False))

    def test_a_stale_base_stops_the_run(self):
        _, out, stop = self._check({'w41 be•do': 'app1'}, [row('☕ coffee', '2026-10-04 07:30')])
        self.assertTrue(stop)
        self.assertIn('wrong base', out[0])

    def test_a_row_written_ahead_proves_nothing(self):
        rows = [row('☕ coffee', '2026-10-01 07:30'), row(ACTION, '2026-10-09 10:00', status=INT)]
        self.assertTrue(self._check({'w41 be•do': 'app1'}, rows)[2])

    def test_no_base_by_that_name_stops_the_run(self):
        _, out, stop = self._check({'w40 be•do': 'app0'}, [row('☕ coffee', '2026-10-06 07:30')])
        self.assertTrue(stop)
        self.assertIn('no base named w41', out[0])

    def test_the_handoff_must_name_the_same_base(self):
        rows = [row('☕ coffee', '2026-10-06 07:30')]
        _, out, _ = self._check({'w41 be•do': 'app1'}, rows, handoff='live base: w40 be•do')
        self.assertIn('handoff', out[0])

    def test_the_clock_checks_the_offset_against_the_zone(self):
        _, local, off, out = P.clock(LOCAL, dt.datetime(2026, 7, 1, 12, tzinfo=UTC))
        self.assertEqual((off, out), (-5, []))
        _, local, off, out = P.clock(LOCAL, dt.datetime(2026, 12, 1, 12, tzinfo=UTC))
        self.assertEqual(off, -6)                                   # the zone wins
        self.assertIn('update utc_offset_hours', out[0])

    def test_the_report_opens_with_the_name_line(self):
        text, stop = P.report(LOCAL, {'w41 be•do': 'a', 'w40 be•do': 'b'},
                              [row('☕ coffee', '2026-10-04 07:30')], at('2026-10-04 08:00'))
        self.assertFalse(stop)
        self.assertEqual(text.splitlines()[:3], ['```', P.chat_name(dt.date(2026, 10, 4)), '```'])


# ── the dusk audit ─────────────────────────────────────────────────────────
NOW = at('2026-10-02 22:30')
MYDAY = {'title': '▶️1002 🏆 Fri ' + P.MARK + ' W40 🔆 my day', 'url': 'chat/aaa'}
DRIVE = {'title': '▶️' + P.MARK + 'D6.40 a drive chat', 'url': 'chat/bbb'}


def audit(rows, chats=(), steps=None):
    return D.audit(rows, NOW, -5, steps, list(chats), dt.date(2026, 10, 2))


class DuskAudit(unittest.TestCase):
    def test_1_calendar_intentions_whose_time_passed(self):
        # 2 Oct: the vet was written ⬜ from the calendar and never closed.
        rows = [row(ACTION, '2026-10-02 14:00', status=INT, title='⚡ the vet', calendar_event='evt1', person='x'),
                row(ACTION, '2026-10-02 23:00', status=INT, title='⚡ later', calendar_event='evt2', person='x'),
                row(ACTION, '2026-10-02 09:00', status=INT, title='⚡ a to-do', person='x')]
        self.assertEqual(audit(rows)['findings']['open_past'], ['⚡ the vet (2:00 PM)'])

    def test_2_an_end_before_its_start(self):
        rows = [row(ACTION, '2026-10-02 19:25', end=z('2026-10-02 14:00'), status=DONE, title='⚡ greenhouse',
                    attention='🌕 full', rhythm='r', person='x')]
        self.assertEqual(audit(rows)['findings']['end_before_start'],
                         ['⚡ greenhouse — end 2:00 PM, start 7:25 PM'])

    def test_3_attention_is_derived_not_asked(self):
        rows = [row(ACTION, '2026-10-02 09:00', end=z('2026-10-02 10:00'), status=DONE, title='a', rhythm='r'),
                row(ACTION, '2026-10-02 11:00', time_spent=5400, status=MOT, title='b', rhythm='r'),
                row(ACTION, '2026-10-02 12:00', status=DONE, title='c', rhythm='r'),
                row(ACTION, '2026-10-02 13:00', end=z('2026-10-02 14:00'), status=INT, title='d', rhythm='r')]
        res = audit(rows)
        self.assertEqual(res['writes'], [{'id': rows[0]['id'], 'attention': '🌕 full'},
                                         {'id': rows[1]['id'], 'attention': '🌓 partial'}])
        self.assertEqual(res['findings']['no_attention'], ['c'])

    def test_4_every_chat_has_an_action_row(self):
        rows = [row(ACTION, '2026-10-02 09:00', end=z('2026-10-02 10:00'), status=DONE, title='a',
                    chat='https://x/chat/bbb', attention='🌕 full', rhythm='r', person='x')]
        f = audit(rows, [MYDAY, DRIVE])['findings']
        self.assertEqual(f['chat_no_entry'], [MYDAY['title']])

    def test_5_stretches_need_captures_and_a_window_row_carries_no_time(self):
        times = [z('2026-10-02 17:31'), z('2026-10-02 17:41'), z('2026-10-02 19:39')] + [z(f'2026-10-02 {t}') for t in ('19:50', '20:05', '20:20', '20:35', '20:45', '20:52')]
        chat = dict(MYDAY, times=times)
        rows = [row(CAPTURE, '2026-10-02 17:31', end=z('2026-10-02 17:41'), status='● log', person='x'),
                row(ACTION, '2026-10-02 17:31', time_spent=4 * 3600, status=DONE, title='⚡ my day',
                    chat='https://x/chat/aaa', rhythm='be•do', person='x')]
        f = audit(rows, [chat])['findings']
        self.assertEqual(f['uncaptured'], [MYDAY['title'] + ': 7:39–8:52 = 1h 13m'])
        self.assertEqual(len(f['action_row']), 2)                  # no duration, no drive
        self.assertEqual(f['attention'], [])                      # a window row is never derived
        self.assertEqual(f['no_rhythm'], [])

    def test_the_gate_is_the_catalog_against_the_day(self):
        steps = RL.flow_steps(CAT, 'dusk')
        rows = [row('🫖 evening tea', '2026-10-02 20:00', status=DONE_LOG, person='x')]
        f = audit(rows, steps=steps)['findings']
        self.assertEqual(f['gate'], ['🌬️ evening breaths', 'a quest day'])

    def test_for_my_day_lists_are_read_from_the_rows(self):
        d = 'her words\n———\n[be•do] did a thing.\nfor my day: attention · drive'
        rows = [row(ACTION, '2026-10-02 09:00', status=DONE, title='a', details=d, end=z('2026-10-02 09:30'),
                    rhythm='r', person='x')]
        self.assertEqual(audit(rows)['findings']['for_my_day'], ['a — attention · drive'])

    def test_queue_media_and_waiting_rows_are_filtered_at_the_read(self):
        rows = [row(ACTION, '2026-10-02 09:00', status=MOT, title='q', queue='x'),
                row(ACTION, '2026-10-02 09:00', status=MOT, title='w', waiting_on='someone'),
                row(F['practice']['media'][1], '2026-10-02 21:00', status=DONE_LOG)]
        self.assertEqual(audit(rows)['flag'], 'Nothing went uncaptured.')

    def test_the_flag_is_one_line_in_order(self):
        rows = [row(ACTION, '2026-10-02 12:00', status=DONE, title='c', person='x'),
                row('☕ coffee', '2026-10-02 07:00', status=DONE_LOG)]
        self.assertEqual(audit(rows)['flag'],
                         '1 ⚡ actions missing attention · 1 ⚡ actions missing a rhythm · '
                         '1 ⚡ actions with no time · 1 rows with no person')

    def test_more_than_five_says_so(self):
        f = {k: ['x'] for k in ('gate', 'no_attention', 'no_rhythm', 'no_duration', 'no_person',
                                'target_today', 'chat_no_entry')}
        self.assertIn('more than five', D.flag(f))

    def test_the_render_is_one_pass(self):
        res = audit([row(ACTION, '2026-10-02 14:00', status=INT, title='⚡ the vet', calendar_event='e',
                         person='x')])
        text = D.render(res, 'dusk audit')
        self.assertTrue(text.startswith('dusk audit\n1 open, time passed'))
        self.assertTrue(text.splitlines()[-1].startswith('flag: '))


if __name__ == '__main__':
    unittest.main(verbosity=1)
