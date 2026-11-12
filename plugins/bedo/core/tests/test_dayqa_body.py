# -*- coding: utf-8 -*-
"""dayqa reads her body over the stretches she didn't log (12 Nov 2026). Her words:
*the Oura heart rate really should be built in, especially when I'm looking back
during the QA.* The shapes are Oura's (daily_activity's class_5_min, the heartrate
samples); every number is invented, modelled on Wednesday 11 Nov's morning.

    python3 plugins/bedo/core/tests/test_dayqa_body.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
sys.path.append(os.path.join(os.path.dirname(CORE), 'skills', 'bedo-week-look-behind', 'scripts'))
import bedo_body as B  # noqa: E402
import bedo_dayqa as Q  # noqa: E402

DAY = dt.date(2026, 11, 11)
OFF = -6
L = {'utc_offset_hours': -6, 'time_zone': 'America/Chicago'}


def u(h, m=0):
    return dt.datetime.combine(DAY, dt.time(h, m), dt.timezone.utc) + dt.timedelta(hours=6)


def z(h, m=0):
    return u(h, m).strftime('%Y-%m-%dT%H:%M:00.000Z')


def activity(start_h, classes):
    """class_5_min from start_h local, as Oura gives it (its own offset on the timestamp)."""
    return {'timestamp': f'{DAY}T{start_h:02d}:00:00-06:00', 'class_5_min': classes}


def heart(pairs):
    return [{'timestamp': z(h, m), 'bpm': b} for h, m, b in pairs]


# 6:55 to 9:10, as Wednesday read: up and down until 8:30, then steady movement until 8:55
MORNING = activity(6, '00000000000' + '2334322333332232332' + '44544' + '3443')


class Segments(unittest.TestCase):
    def test_getting_ready_reads_as_up_and_down_then_on_the_move(self):
        b = B.Body(MORNING, heart([(7, 20, 86), (8, 0, 84), (8, 40, 100), (8, 50, 92)]))
        segs = b.segments(u(6, 57), u(9, 0))
        self.assertEqual([s['kind'] for s in segs], ['mixed', 'moving'])
        self.assertEqual(segs[0]['start'], u(6, 57))
        self.assertEqual(segs[0]['end'], u(8, 30))
        self.assertEqual(segs[1]['end'], u(9, 0))
        self.assertEqual(segs[1]['bpm'], 96)

    def test_a_morning_at_the_desk_reads_still(self):
        b = B.Body(activity(6, '000000000000' + '222122212222'), [])
        segs = b.segments(u(7, 0), u(8, 0))
        self.assertEqual([s['kind'] for s in segs], ['still'])

    def test_one_low_slot_inside_a_run_of_movement_stays_in_it(self):
        b = B.Body(activity(8, '2222' + '4434' + '2222'), [])
        self.assertEqual([s['kind'] for s in b.segments(u(8, 0), u(9, 0))], ['still', 'moving', 'still'])

    def test_ten_minutes_of_movement_is_not_its_own_piece(self):
        b = B.Body(activity(8, '222222' + '44' + '2222'), [])
        self.assertEqual([s['kind'] for s in b.segments(u(8, 0), u(9, 0))], ['still'])

    def test_heart_rate_stands_in_when_there_is_no_activity_record(self):
        b = B.Body(None, heart([(14, m, 72) for m in range(0, 30, 2)] + [(14, m, 104) for m in range(30, 60, 2)]))
        self.assertEqual([s['kind'] for s in b.segments(u(14, 0), u(15, 0))], ['still', 'moving'])

    def test_nothing_from_oura_is_no_segments(self):
        self.assertEqual(B.Body(None, []).segments(u(7, 0), u(8, 0)), [])
        self.assertFalse(B.Body(None, []))


def row(title, h, m=0, **kw):
    r = {'id': 'rec' + title[:8].replace(' ', ''), 'datetime': z(h, m), 'status': '● log',
         'practice': '📝 log', 'title': title, 'wellness': '🧠 mind', 'device': '📱 phone'}
    r.update(kw)
    return r


class Gaps(unittest.TestCase):
    ROWS = [row('😶 wake', 6, 30, practice='😶 wake', end=z(6, 57)),
            row('📧 FYI to the team', 8, 25, practice='📧 email', details='sent the hub post'),
            row('🧎‍♀️ barre', 9, 0, practice='🧎‍♀️‍➡️ barre', end=z(9, 30)),
            row('🪐 evening oura', 22, 6, practice='🪐 evening oura',
                details='———\n[be•do] From the Oura API, evening:\nworkouts: housework 8:33a–8:56a (easy), pilates 9:30a–9:52a (easy)')]

    def test_without_oura_the_stretch_is_one_row_as_before(self):
        out = Q.gaps(self.ROWS, OFF, (), None)
        first = next(i for i in out if i.get('new') and i['new']['datetime'] == z(6, 57))
        self.assertEqual(first['new']['end'], z(9, 0))

    def test_with_oura_the_stretch_is_cut_and_named_for_what_her_body_did(self):
        b = B.Body(MORNING, heart([(7, 20, 86), (8, 40, 100), (8, 50, 92)]))
        out = [i for i in Q.gaps(self.ROWS, OFF, (), None, b, DAY)
               if i.get('new') and z(6, 57) <= i['new']['datetime'] < z(9, 0)]
        self.assertEqual([(i['new']['datetime'], i['new']['end']) for i in out],
                         [(z(6, 57), z(8, 30)), (z(8, 30), z(9, 0))])
        up, move = out
        self.assertIn('up and down', up['new']['title'])
        self.assertIn('FYI to the team', up['new']['title'])      # what she logged in it is still listed
        self.assertIn('on the move (housework)', move['new']['title'])
        self.assertIn("Oura's housework 8:33a–8:56a", move['line'])
        self.assertIn('ESTIMATED FROM CONTEXT', move['new']['details'])
        self.assertEqual(move['source'], 'Oura')

    def test_a_stretch_with_nothing_logged_is_filled_from_oura_not_left_open(self):
        rows = [row('📝 a', 13, 0, end=z(13, 10)), row('📝 b', 14, 0, end=z(14, 10))]
        b = B.Body(activity(13, '22' + '2222222222'), [])
        out = Q.gaps(rows, OFF, (), None, b, DAY)
        self.assertEqual([i['kind'] for i in out], ['fill'])
        self.assertIn('sitting', out[0]['new']['title'])

    def test_workouts_are_read_from_the_oura_row(self):
        w = Q.oura_workouts(self.ROWS, OFF, DAY)
        self.assertEqual([(n, a, b) for n, a, b in w], [('housework', u(8, 33), u(8, 56)), ('pilates', u(9, 30), u(9, 52))])


if __name__ == '__main__':
    unittest.main()
