# -*- coding: utf-8 -*-
"""Her dusk, as she set it on Tue 24 Nov 2026.

Her words: the recorder check needs to happen in the batch that is share the
day's photos, Timeline, screen time, ring stress, and probably just after
evening sun · maybe it's evening BP med / supplements all at once · [her son] and
I do the evening breaths and evening blessing right before falling asleep,
generally after I set my phone down · I want the evening to close when I fall
asleep · my highlight after his highlight · move the braid to where it makes
the most sense · I want to do all the batch checks then upload the photos and
have the system fill in everything based on that info. And dusk opens at sunset.

    python3 core/tests/test_dusk_order.py
"""
import datetime as dt, os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bedo_remaining as R  # noqa: E402

FL = R.FLOWS
LOCAL = {'weekly_name': 'w{n} be•do', 'utc_offset_hours': -6, 'time_zone': 'America/Chicago'}
DAY = dt.date(2026, 11, 24)
PILLS = '💊 evening pills'
CLOSE = FL['close']['dusk']

# the catalog's observed times as they stood that morning: the clock order she replaced
TYPICAL = {'🔅 evening sun': '17:30', '⭐ highlight': '17:30', '🌈 supplements': '20:49', '💊 bp meds': '20:50',
           '🫖 evening tea': '21:02', "⚔️ his quest": '21:30', '🪐 evening ring': '21:39',
           '🗺️ map check': '21:42', '📱 screen time': '21:45', "🌟 his highlight": '22:05',
           '🌬️ evening breaths': '22:20', '📧 clear gmail inbox': '22:22', '🔀 braid': '22:28',
           '🌌 evening blessing': '22:28', '⏺️ recorder check': '22:40', CLOSE: '23:00'}
CAT = [{'practice': p, 'phase': FL['phase']['dusk'], 'group': 'flow', 'active': True, 'order': None,
        'typical_time': t} for p, t in TYPICAL.items()]
STEPS = R.flow_steps(CAT, 'dusk')
BATCH = {'🗺️ map check', '📱 screen time', '🪐 evening ring', '⏺️ recorder check'}


def z(hhmm):
    t = dt.datetime.combine(DAY, dt.time(*map(int, hhmm.split(':')))) + dt.timedelta(hours=6)
    return t.strftime('%Y-%m-%dT%H:%M:00.000Z')


def rows(*names, at='19:00', **extra):
    return [dict({'id': f'r{i}', 'practice': p, 'datetime': z(at)}, **extra) for i, p in enumerate(names)]


class HerOrder(unittest.TestCase):
    def test_her_order_beats_the_clock(self):
        names = [s['practice'] for s in STEPS]
        self.assertEqual(names[0], '🔅 evening sun')
        self.assertEqual(set(names[1:5]), BATCH, 'the batch comes right after evening sun')
        self.assertEqual(names[5:], ['📧 clear gmail inbox', '💊 bp meds', '🌈 supplements',
                                     '🫖 evening tea', "⚔️ his quest", "🌟 his highlight",
                                     '⭐ highlight', '🔀 braid', '🌬️ evening breaths', '🌌 evening blessing', CLOSE])

    def test_the_line_reads_in_her_order(self):
        _, _, left, _ = R.split(STEPS, [], 'dusk', LOCAL)
        self.assertEqual(left[0], '🔅 evening sun')
        self.assertLess(left.index("🌟 his highlight"), left.index('⭐ highlight'))
        self.assertLess(left.index('⭐ highlight'), left.index('🔀 braid'), 'the braid sees the whole evening')


class EveningPills(unittest.TestCase):
    def test_bp_meds_and_supplements_are_one_step(self):
        done, total, left, _ = R.split(STEPS, [], 'dusk', LOCAL)
        self.assertIn(PILLS, left)
        self.assertNotIn('💊 bp meds', left)
        self.assertNotIn('🌈 supplements', left)
        self.assertEqual(left.count(PILLS), 1)

    def test_done_only_once_both_rows_are_in(self):
        _, _, left, _ = R.split(STEPS, rows('💊 bp meds'), 'dusk', LOCAL)
        self.assertIn(PILLS, left)
        done, _, left, _ = R.split(STEPS, rows('💊 bp meds', '🌈 supplements'), 'dusk', LOCAL)
        self.assertNotIn(PILLS, left)
        self.assertEqual(done, 1, 'the two rows count as one step done')


class AfterThePhoneIsDown(unittest.TestCase):
    def test_breaths_and_blessing_show_last_before_the_close(self):
        # her words: I still like to see evening breaths and evening blessing before the close
        done, total, left, _ = R.split(STEPS, [], 'dusk', LOCAL)
        self.assertEqual(left[-3:], ['🌬️ evening breaths', '🌌 evening blessing', CLOSE])
        self.assertEqual(total, len(STEPS) - 1, 'the pills count once')

    def test_they_never_hold_the_flow_open(self):
        self.assertNotIn('🌬️ evening breaths', R.holds_open(STEPS, [], 'dusk', LOCAL))
        self.assertNotIn('🌌 evening blessing', R.holds_open(STEPS, [], 'dusk', LOCAL))


class ClosesAtSleep(unittest.TestCase):
    def all_but_pattern(self):
        names = [s['practice'] for s in STEPS
                 if s['practice'] not in (CLOSE, '🌬️ evening breaths', '🌌 evening blessing')]
        return rows(*names)

    def test_once_the_rest_is_in_it_waits_for_sleep(self):
        line = R.close_line('dusk', STEPS, self.all_but_pattern(), DAY, dt.datetime(2026, 11, 24, 21, 30), LOCAL)
        self.assertIn('closes when you fall asleep', line)
        self.assertIn('morning ring read', line)
        self.assertNotIn('Write', line)

    def test_no_backup_at_midnight(self):
        self.assertIsNone(R.close_line('dusk', STEPS, rows('🔅 evening sun'), DAY,
                                       dt.datetime(2026, 11, 24, 23, 59), LOCAL))

    def test_an_open_close_row_does_not_close_the_flow(self):
        # the dusk Code run writes the close row ▶️ with its markers; the morning ring read closes it
        open_close = rows(CLOSE, status='▶️ in motion')
        self.assertNotIn(R.norm(CLOSE), R.logged(open_close, LOCAL))
        self.assertEqual(R.open_flow(dt.datetime(2026, 11, 24, 21, 0), open_close), 'dusk')
        done_close = rows(CLOSE, status='◉ done')
        self.assertIn(R.norm(CLOSE), R.logged(done_close, LOCAL))


class OpensAtSunset(unittest.TestCase):
    HOME = dict(LOCAL, home={'lat': 32.2, 'lon': -97.8})     # an invented spot in her time zone

    def test_sunset_moves_with_the_season(self):
        late_nov = R.sunset(DAY, 32.2, -97.8, LOCAL)
        june = R.sunset(dt.date(2026, 6, 21), 32.2, -97.8, LOCAL)
        self.assertTrue(17 * 60 + 15 <= late_nov <= 17 * 60 + 40, R.clock12(late_nov))
        self.assertTrue(20 * 60 + 25 <= june <= 20 * 60 + 55, R.clock12(june))

    def test_dusk_opens_at_sunset_not_seven(self):
        self.assertEqual(R.open_flow(dt.datetime(2026, 11, 24, 17, 45), [], self.HOME), 'dusk')
        self.assertIsNone(R.open_flow(dt.datetime(2026, 11, 24, 16, 50), [], self.HOME))

    def test_evening_sun_logged_opens_it(self):
        self.assertEqual(R.open_flow(dt.datetime(2026, 11, 24, 17, 5), rows('🔅 evening sun', at='17:00'), self.HOME), 'dusk')

    def test_without_a_home_the_old_hour_holds(self):
        self.assertIsNone(R.open_flow(dt.datetime(2026, 11, 24, 18, 0), [], LOCAL))
        self.assertEqual(R.open_flow(dt.datetime(2026, 11, 24, 19, 5), [], LOCAL), 'dusk')


if __name__ == '__main__':
    unittest.main()
