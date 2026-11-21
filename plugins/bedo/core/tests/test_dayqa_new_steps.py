# -*- coding: utf-8 -*-
"""The braid asks about the day's own new steps, and reads "tomorrow" as
tomorrow (21 Nov 2026, her words: the reconciliation isn't working well … you
didn't even ask me). On Fri 20 Nov a ⬜ step made that morning with no date was
never raised though she did it, and a visit "tomorrow morning" was read as
Friday's. With her rule of that morning: obvious closes are written, then told.
Names, places and drives are invented.

    python3 plugins/bedo/core/tests/test_dayqa_new_steps.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_dayqa as Q  # noqa: E402
import bedo_entry as E  # noqa: E402

FRI = dt.date(2026, 11, 20)
SAT = dt.date(2026, 11, 21)
OFF = -6
D = E.DIVIDER


def z(h, m=0, d=FRI):
    return (dt.datetime.combine(d, dt.time(h, m)) + dt.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:00.000Z')


def row(rid, **kw):
    r = {'id': rid, 'datetime': z(9), 'status': '● log', 'practice': '📝 log', 'title': 'a note'}
    r.update(kw)
    return r


# made Friday morning with no date; she did it at midday
SCOPE = row('recScope', title='⚡ Bring the spare microscope to the river lab for my partner', status='⬜ intention',
            practice='⚡ action', key='261120_0815', datetime=z(8, 15),
            details=f'I need to bring the spare microscope over to the lab today.\n{D}\n[be•do] No date given.')
STAY = row('recStay', title='📍 the river lab', practice='📍 location', status='◉ done', datetime=z(12, 5), end=z(12, 40))
DROP = row('recDrop', title='⚡ Dropped the spare microscope off at the river lab', status='✅ done',
           practice='⚡ action', key='261120_1210', datetime=z(12, 10), end=z(12, 20))
# said Friday, meant Saturday
VISIT = row('recVisit', title='⚡ Friends from the co-op come by tomorrow morning', status='⬜ intention',
            practice='⚡ action', key='261120_1630', datetime=z(16, 30),
            details=f'The co-op friends are coming by tomorrow morning.\n{D}\n[be•do] Her words.')
SUPPER = row('recSupper', title='⚡ Start the soup tonight', status='⬜ intention', practice='⚡ action',
             key='261120_1400', datetime=z(14))
LATER = row('recLater', title='⚡ Sort the seed packets next week', status='⬜ intention', practice='⚡ action',
            key='261120_1500', datetime=z(15))
OLD = row('recOld', title='⚡ Return the borrowed ladder', status='⬜ intention', practice='⚡ action',
          key='261118_0900', datetime=z(9, 0, dt.date(2026, 11, 18)))


def due(rows, opens=()):
    return Q.due(rows, list(opens), OFF, FRI)


class UndatedSteps(unittest.TestCase):
    def test_a_step_made_today_with_no_date_is_raised(self):
        items = due([SCOPE])
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['kind'], 'ask')
        self.assertIn('made today with no date', items[0]['line'])

    def test_a_row_in_its_words_and_a_stay_settle_it_written_then_told(self):
        items = due([SCOPE, STAY, DROP])
        self.assertEqual(len(items), 1)
        i = items[0]
        self.assertEqual((i['kind'], i.get('tell')), ('fill', True))
        self.assertEqual(i['patch']['fields'], {'status': '✅ done', 'end': z(12, 20)})
        self.assertIn('Dropped the spare microscope', i['line'])
        self.assertIn('the river lab', i['line'])

    def test_a_stay_alone_is_hers_to_accept(self):
        i = due([SCOPE, STAY])[0]
        self.assertEqual(i['kind'], 'fill')
        self.assertFalse(i.get('tell'))
        self.assertIn('likely done', i['line'])

    def test_a_row_before_the_step_was_made_is_no_answer(self):
        early = dict(DROP, id='recEarly', datetime=z(7), end=z(7, 10))
        self.assertEqual(due([SCOPE, early])[0]['kind'], 'ask')

    def test_steps_made_another_day_or_for_later_are_left(self):
        self.assertEqual(due([LATER], [OLD]), [])

    def test_tonight_is_the_day_itself(self):
        items = due([SUPPER])
        self.assertEqual(len(items), 1)
        self.assertIn('for today', items[0]['line'])


class TomorrowIsTomorrow(unittest.TestCase):
    def test_tomorrow_said_friday_is_not_fridays(self):
        self.assertEqual(due([VISIT]), [])

    def test_it_comes_up_on_the_day_it_names(self):
        items = Q.due([], [VISIT], OFF, SAT)
        self.assertEqual(len(items), 1)
        self.assertIn('its words say so', items[0]['line'])

    def test_said_day(self):
        self.assertEqual(E.said_day('come by tomorrow morning', FRI), (SAT, 'tomorrow'))
        self.assertEqual(E.said_day('the day after tomorrow', FRI)[0], dt.date(2026, 11, 22))
        self.assertEqual(E.said_day('start it tonight', FRI), (FRI, 'tonight'))
        self.assertEqual(E.said_day('call on Monday', FRI)[0], dt.date(2026, 11, 23))
        self.assertIsNone(E.said_day('on Friday', FRI))           # this Friday or next: no day
        self.assertIsNone(E.said_day('bring the microscope', FRI))


class EntrySetsTheDay(unittest.TestCase):
    def test_a_step_saying_tomorrow_is_given_its_target(self):
        p = E.when_problems(VISIT, OFF)
        self.assertEqual(len(p), 1)
        self.assertIn('2026-11-21', p[0])
        self.assertIn('Sat 21 Nov', p[0])

    def test_a_weekday_names_the_next_one(self):
        r = dict(VISIT, title='⚡ Call the co-op on Tuesday', details='')
        self.assertIn('2026-11-24', E.when_problems(r, OFF)[0])

    def test_left_alone(self):
        self.assertEqual(E.when_problems(SUPPER, OFF), [])                       # tonight is the day it was said
        self.assertEqual(E.when_problems(dict(VISIT, target='2026-11-21'), OFF), [])
        self.assertEqual(E.when_problems(dict(VISIT, status='✅ done'), OFF), [])
        decided = dict(VISIT, details=f'Tomorrow morning.\n{D}\n[be•do] No target: the visit may move, her word.')
        self.assertEqual(E.when_problems(decided, OFF), [])
        self.assertEqual(E.when_problems(VISIT), [])                             # no clock, no reading

    def test_the_whole_check_carries_it(self):
        self.assertTrue(any('its words say' in p for p in E.problems(VISIT, utc_offset_hours=OFF)))


class TheBraid(unittest.TestCase):
    def test_a_settled_step_is_told_not_asked(self):
        rows = [SCOPE, STAY, DROP, VISIT]
        items = Q.run(rows, FRI, OFF, {'utc_offset_hours': OFF}, opens=list(rows))
        tells = [i for i in items if i.get('tell')]
        self.assertEqual([i['patch']['id'] for i in tells], ['recScope'])
        self.assertNotIn('n', tells[0])
        self.assertFalse(any('Friends from the co-op' in i.get('line', '') for i in items if i['check'] == 'due'))
        text = Q.render(items, FRI, rows, OFF)
        self.assertIn('written, then told — 1', text)
        self.assertIn('✓ due · “⚡ Bring the spare microscope', text)
        top = text.split('written, then told')[0]
        self.assertNotIn('microscope', top)


if __name__ == '__main__':
    unittest.main()
