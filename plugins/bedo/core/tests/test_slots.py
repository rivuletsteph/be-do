# -*- coding: utf-8 -*-
"""The four V53 slots that used to depend on a chat remembering: preflight,
the remaining list, stretches and the dusk audit. Each test is the way the
rule actually broke. Every row is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_slots.py
"""
import datetime as dt, json, os, sys, tempfile, unittest, urllib.error
from unittest import mock

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_reader as R  # noqa: E402
import bedo_preflight as P  # noqa: E402
import bedo_remaining as RL  # noqa: E402
import bedo_stretches as ST  # noqa: E402
import bedo_dusk_audit as D  # noqa: E402
import bedo_air as A  # noqa: E402
import bedo_order as O  # noqa: E402

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
        self.assertEqual(names[0], '🔅 morning sun')                       # no typical times: catalog order…
        self.assertGreater(names.index('🥤 morning water'), names.index('☕ coffee'))   # …but water after coffee
        self.assertEqual(names[-2:], ['😶 wake', '🌅 dawn flow close'])   # no order goes late; the close is last
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

    def test_the_compact_form_reads_as_the_connector_read(self):
        # 6 Oct: in Cowork every cell read is a cell the chat writes out again,
        # so the chat writes only the columns the list uses, as .tsv.
        cat_ids = {k: 'fld' + k.upper() for k in F['catalog_fields']}   # ids by field, as facts_local names them
        dawn = F['flows']['phase']['dawn']
        cat_tsv = (f'total 3\tactive=true\tphase={dawn}\n'
                   'practice\tgroup\torder\ttypical_time\n'
                   '☕ coffee\tflow\t6\twake+43\n'
                   '🥤 morning water\tflow\t2\twake+112\n'
                   '🌅 dawn flow close\tflow\t16\n')
        day_tsv = ('total 2\n'
                   'datetime\tpractice\tdetails\n'
                   f'{z("2026-10-06 06:32")}\t😶 wake\n'
                   f'{z("2026-10-06 07:20")}\t🌦️ weather check\tsunrise 7:27 am\n')
        with tempfile.TemporaryDirectory() as d:
            cp, dp = os.path.join(d, 'practices.tsv'), os.path.join(d, 'today.tsv')
            open(cp, 'w', encoding='utf-8').write(cat_tsv)
            open(dp, 'w', encoding='utf-8').write(day_tsv)
            cat = RL.catalog(cp, cat_ids)
            day = R.as_rows(R.complete(dp), {'practice': 'fldP', 'datetime': 'fldD', 'details': 'fldX'})
            self.assertEqual([s['practice'] for s in RL.flow_steps(cat, 'dawn')],
                             ['☕ coffee', '🥤 morning water', '🌅 dawn flow close'])
            self.assertEqual(cat[0]['order'], 6)
            self.assertEqual(RL.sunrise(day, LOCAL), (dt.date(2026, 10, 6), 7 * 60 + 27))
            self.assertEqual(RL.logged(day), {RL.norm('😶 wake'), RL.norm('🌦️ weather check')})
            open(dp, 'w', encoding='utf-8').write(day_tsv.replace('total 2', 'total 3'))
            with self.assertRaises(SystemExit) as e:                 # a short read still stops (I11)
                R.complete(dp)
            self.assertIn('truncated', str(e.exception))

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

    def test_a_week_file_reads_as_its_day(self):
        # a chat with no token passes a whole week; only the day's rows count
        week = [row('☕ coffee', '2026-10-03 07:30', status=DONE_LOG), row('🥤 morning water', '2026-10-04 07:00'),
                row('📿 morning mantra', '2026-10-04 23:30')]                       # 4:30 UTC next day, still the 4th here
        self.assertEqual([r['practice'] for r in R.on_day(week, dt.date(2026, 10, 4), LOCAL)],
                         ['🥤 morning water', '📿 morning mantra'])

    def test_the_widget_is_her_pill_strip(self):
        steps = RL.flow_steps(CAT, 'dusk')
        day = [row('🫖 evening tea', '2026-10-04 20:00', status=DONE_LOG)]
        html = RL.widget('dusk', steps, day)
        self.assertIn(F['flows']['widget']['bar']['dusk'], html)          # the dusk colour, not dawn's
        self.assertNotIn(F['flows']['widget']['bar']['dawn'], html)
        self.assertNotIn('of 4', html)                                    # no count, no caption (A237)
        self.assertNotIn('🌬', html)                                      # glyphs only as numeric references
        self.assertIn('&#x1F32C;&#xFE0F;', html)
        self.assertEqual(html.count('class="p"'), 3)                      # remaining only: tea is done
        self.assertNotIn('sendPrompt(t);n', html.split('onclick=function(){cur=')[0])   # a tap opens the note, sends nothing
        self.assertEqual(RL.short('📧 clear gmail inbox'), ('📧', 'gmail inbox'))

    def test_her_predicted_order(self):
        def st(name, t, order):
            return dict(step(name, 'dawn', order), typical_time=t)
        cat = [st('🌅 dawn flow close', None, 16), st('🥤 morning water', 'wake+20', 2),   # data says early…
               st('☕ coffee', 'wake+43', 6), st('🤸🏻‍♀️ morning movement', 'wake+46', 4),
               st('💪 strength training', 'wake+60', 4.2), st('🔅 morning sun', 'wake+66', 3),
               st('📗 morning book', None, 12), st('🚽 bm', 'wake+8', 14)]
        names = [s['practice'] for s in RL.flow_steps(cat, 'dawn')]
        self.assertEqual(names, ['🚽 bm', '☕ coffee', '🥤 morning water', '🤸🏻‍♀️ morning movement',
                                 '🔅 morning sun', '💪 strength training', '📗 morning book',
                                 '🌅 dawn flow close'])
        # …but water comes after the first coffee and the block after the sun: her sequences win;
        # no typical time sorts after the observed ones; the close is last
        first = [s['practice'] for s in RL.flow_steps(cat, 'dawn', ['📗 morning book'])]
        self.assertEqual(first[0], '📗 morning book')                    # what she says she's doing next
        self.assertEqual(first[-1], '🌅 dawn flow close')

    def test_sunrise_holds_back_morning_sun(self):
        # 2 Oct: woke 5:24, sunrise 7:27 — sun can't come at its usual wake+66
        w = [row('🌦️ weather check', '2026-10-01 07:32', status=DONE_LOG,
                 details='> SUN — sunrise 7:26a, sunset 7:18p.')]
        self.assertEqual(RL.sunrise(w, LOCAL), (dt.date(2026, 10, 1), 7 * 60 + 26))
        w.append(row('🌦️ weather check', '2026-10-02 06:00', status=DONE_LOG,
                      details='SUN · sunrise 7:27 am · sunset 7:15 pm'))
        self.assertEqual(RL.sunrise(w, LOCAL)[1], 7 * 60 + 27)           # the newest one
        day = [row('😶 wake', '2026-10-02 05:24', status=DONE_LOG)]
        gate = RL.sun_gate(day, RL.sunrise(w, LOCAL), LOCAL)
        self.assertEqual(list(gate.values()), [123])

        def st(name, t):
            return dict(step(name, 'dawn', None), typical_time=t)
        cat = [st('🔅 morning sun', 'wake+66'), st('💪 strength training', 'wake+70'),
               st('👁️ look ahead', 'wake+116'), st('🙏 gratitude', 'wake+200')]
        names = [s['practice'] for s in RL.flow_steps(cat, 'dawn', (), gate)]
        self.assertEqual(names, ['👁️ look ahead', '🔅 morning sun', '💪 strength training', '🙏 gratitude'])
        self.assertEqual(RL.sun_gate([], RL.sunrise(w, LOCAL), LOCAL), {})   # no wake row: nothing held
        late = [row('😶 wake', '2026-10-02 07:40', status=DONE_LOG)]
        self.assertEqual(RL.sun_gate(late, RL.sunrise(w, LOCAL), LOCAL), {})  # up after sunrise: nothing held

    def test_typical_time_reads_and_writes(self):
        self.assertEqual(RL.typical_minutes('wake+25'), 25)
        self.assertEqual(RL.typical_minutes('20:40'), 1240)
        self.assertEqual(RL.typical_minutes('00:15'), 1455)              # after midnight is late, not early
        self.assertIsNone(RL.typical_minutes('evenings'))
        self.assertEqual((O.write('dawn', 25.4), O.write('dusk', 1455)), ('wake+25', '00:15'))

    def test_typical_time_is_observed_from_her_rows(self):
        cat = [step('😶 wake', 'dawn', None), step('☕ coffee', 'dawn', 6), step('🫖 evening tea', 'dusk', 34)]
        rows = []
        for d in ('2026-09-28', '2026-09-29', '2026-09-30'):
            rows += [row('😶 wake', f'{d} 06:00', status=DONE_LOG), row('☕ coffee', f'{d} 06:20', status=DONE_LOG),
                     row('🫖 evening tea', f'{d} 20:40', status=DONE_LOG)]
        rows.append(row('🫖 evening tea', '2026-10-01 09:00', status=DONE_LOG))    # filed next morning: not its time
        rows.append(row('☕ coffee', '2026-10-01 06:00', status=INT))              # a plan is not a lived time
        got = {s['practice']: v for s, v, _ in O.typical(rows, cat, LOCAL)}
        self.assertEqual(got['☕ coffee'], 'wake+20')
        self.assertEqual(got['🫖 evening tea'], '20:40')
        self.assertEqual(got['😶 wake'], 'wake+0')

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
        self.assertEqual(P.chat_name(dt.date(2026, 10, 4), part='c'),
                         '▶️1004c ☀️ Sun ' + P.MARK + ' W41 🔆 my day')      # her example, 4 Oct
        self.assertEqual(P.chat_name(dt.date(2026, 9, 18), part='B', status='✔️'),
                         '✔️0918b 🏆 Fri ' + P.MARK + ' W38 🔆 my day')      # lowercase, right after the date
        self.assertEqual(P.chat_name(dt.date(2026, 9, 18), part=1), P.chat_name(dt.date(2026, 9, 18), part='a'))
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

    def test_the_report_opens_with_the_name_line_alone(self):
        text, stop = P.report(LOCAL, {'w41 be•do': 'a', 'w40 be•do': 'b'},
                              [row('☕ coffee', '2026-10-04 07:30')], at('2026-10-04 08:00'))
        self.assertFalse(stop)
        self.assertEqual(text.splitlines()[0], P.chat_name(dt.date(2026, 10, 4)))   # line one, nothing else

    def test_a_short_read_newest_first_is_enough(self):
        # 6 Oct: Cowork read 125 rows to learn one thing, the newest. The
        # connector's newest-first read of five says 396 in its total.
        f = {'datetime': 'fldDATETIME'}
        def dump(stamps, total):
            return {'records': [{'id': 'rec%d' % i, 'createdTime': t,
                                 'cellValuesByFieldId': {f['datetime']: t}} for i, t in enumerate(stamps)],
                    'metadata': {'totalRecordCount': total}}
        newest_first = ['2026-10-06T03:46:00.000Z', '2026-10-06T03:45:00.000Z', '2026-10-06T03:30:00.000Z']
        self.assertEqual(len(P.stream_rows(dump(newest_first, 396), f)), 3)
        with self.assertRaises(SystemExit) as e:                    # short and unsorted: it could hide the newest
            P.stream_rows(dump(newest_first[::-1], 396), f)
        self.assertIn('truncated', str(e.exception))
        self.assertEqual(len(P.stream_rows(dump(newest_first[::-1], 3), f)), 3)   # complete: any order


# ── the live read ──────────────────────────────────────────────────────────
class LiveRead(unittest.TestCase):
    def test_a_cloud_flag_without_a_credential_is_no_token(self):
        # 4 Oct: Cowork sets the cloud flag but carries no credential; preflight
        # stopped on a 401 instead of saying to read through the connector.
        refused = urllib.error.HTTPError(A.API + 'meta/bases', 401, 'Unauthorized', {}, None)
        with mock.patch.dict(os.environ, {'CLAUDE_CODE_REMOTE': 'true'}),                 mock.patch.object(A, 'find_token', return_value=None),                 mock.patch('urllib.request.urlopen', side_effect=refused):
            self.assertFalse(A.can_read())
            with self.assertRaises(SystemExit) as e:
                A.Air().get('meta/bases')
            self.assertIn('NO TOKEN HERE', str(e.exception))

    def test_a_token_is_enough(self):
        with mock.patch.object(A, 'find_token', return_value='pat'):
            self.assertTrue(A.can_read())


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
