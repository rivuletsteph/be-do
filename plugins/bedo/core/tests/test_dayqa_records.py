# -*- coding: utf-8 -*-
"""dayqa reads the day's own records before her list (30 Oct 2026): every
calendar event she marked done, the day's journal, the day's photos and
screenshots, and how the day page would draw each stretch. Every row and name
is invented; the shapes are the base's and the calendar connector's.

    python3 plugins/bedo/core/tests/test_dayqa_records.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
RINGS = os.path.join(os.path.dirname(CORE), 'skills', 'bedo-week-look-behind', 'scripts')
sys.path.append(RINGS)          # run_checks puts day_rings beside the core; here it is read from its skill
import bedo_dayqa as Q  # noqa: E402

LOG, DONE = '● log', '◉ done'
DAY = dt.date(2026, 10, 8)
OFF = -5
L = {'utc_offset_hours': -5, 'time_zone': 'America/Chicago', 'system_rhythm': 'the system'}


def z(h, m=0):
    return (dt.datetime.combine(DAY, dt.time(h, m)) + dt.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:00.000Z')


def row(**kw):
    r = {'id': 'rec' + kw.get('title', 'x')[:6], 'datetime': z(9), 'status': LOG, 'practice': '📝 log',
         'title': 'a note', 'wellness': '🧠 mind', 'device': '📱 phone'}
    r.update(kw)
    return r


def event(summary, h0, h1, eid='abc', cal='my events'):
    return {'summary': cal, 'events': [{
        'summary': summary, 'id': eid, 'status': 'confirmed',
        'htmlLink': f'https://calendar.example.invalid/event?eid={eid}XYZ',
        'start': {'dateTime': f'{DAY}T{h0:02d}:00:00-05:00'}, 'end': {'dateTime': f'{DAY}T{h1:02d}:00:00-05:00'}}]}


class Calendar(unittest.TestCase):
    def test_a_done_event_with_no_row_gets_its_row(self):
        items = Q.calendar([], Q.events_from(event('✔️🏭 River Project', 10, 11)), OFF, '🗓️ calendar event')
        self.assertEqual(len(items), 1)
        new = items[0]['new']
        self.assertEqual((new['title'], new['datetime'], new['end']), ('🏭 River Project', z(10), z(11)))
        self.assertEqual(new['status'], '✅ done')
        self.assertIn('eid=abc', new['calendar_event'])

    def test_a_row_about_it_gets_the_link_instead(self):
        r = row(title='River project call notes', datetime=z(10, 15), end=z(10, 45))
        items = Q.calendar([r], Q.events_from(event('✔️ River Project', 10, 11)), OFF, '🗓️ calendar event')
        self.assertEqual(items[0]['patch'], {'id': r['id'], 'fields': {'calendar_event': items[0]['patch']['fields']['calendar_event']}})

    def test_linked_open_and_theirs_are_left(self):
        linked = row(title='x', calendar_event='https://calendar.example.invalid/event?eid=abcXYZ')
        self.assertEqual(Q.calendar([linked], Q.events_from(event('✔️ River', 10, 11)), OFF, 'c'), [])
        self.assertEqual(Q.calendar([], Q.events_from(event('⬜ River', 10, 11)), OFF, 'c'), [])
        his = Q.events_from(event('✔️ Grandparents', 8, 15, cal='family123@group.calendar.google.com'))
        self.assertEqual(Q.calendar([], his, OFF, 'c', theirs=('family123',)), [])


class Journal(unittest.TestCase):
    def test_a_journal_never_read_through_is_the_qas_to_do(self):
        j = row(practice='📒 journal', title='journal on the drive', details='I sat in the meeting…\n———\n[be•do] Voice note.')
        done = row(practice='📒 journal', title='read', details='…\n———\n[be•do] Pulled out: the meeting row.')
        items = Q.journals([j, done], OFF)
        self.assertEqual([i['kind'] for i in items], ['do'])
        self.assertEqual(items[0]['rows'], [j['id']])


class Photos(unittest.TestCase):
    def test_a_screenshot_is_read_in_her_own_clock(self):
        import bedo_photos as PH
        self.assertEqual(PH.taken('Screenshot_20261008-220753.png', OFF), dt.datetime(2026, 10, 8, 22, 7, 53))
        self.assertEqual(PH.taken('PXL_20261009_030753000.jpg', OFF), dt.datetime(2026, 10, 8, 22, 7, 53))

    def test_a_timeline_screenshot_no_row_explains_is_to_be_read(self):
        files = [{'id': 'f1', 'name': 'Screenshot_20261008-220753.png'}, {'id': 'f2', 'name': 'Screenshot_20261007-090000.png'}]
        items = Q.photos([row(datetime=z(9))], files, OFF, DAY)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]['rows'], ['f1'])
        self.assertIn('screenshot', items[0]['line'])


class Painted(unittest.TestCase):
    def test_a_stretch_the_page_draws_as_nothing_is_named(self):
        rows = [row(title='at the office', datetime=z(14), end=z(15)),                      # no drive: draws nothing
                row(title='the report', datetime=z(10), end=z(11), rhythm='Paid Work')]     # work
        items = [i for i in Q.painted(rows, DAY, L) if i['kind'] == 'do']
        self.assertEqual(len(items), 1)
        self.assertIn('2:00p–3:00p', items[0]['line'])
        self.assertIn('at the office', items[0]['line'])



class Reconcile(unittest.TestCase):
    """Reconciling the stream (28 and 30 Oct 2026): an open step the day shows done."""
    def test_a_step_the_day_shows_done_is_closed_at_that_rows_time(self):
        book = row(title="finish reading Maslow's hierarchy of needs", status='⬜ intention', key='261020_1732',
                   datetime=z(8) .replace('2026-10-08', '2026-10-01'))
        same_key = row(title='call the clinic', status='⬜ intention', key='261005_0900', datetime=z(7).replace('2026-10-08', '2026-10-05'))
        untouched = row(title='tidy the garage', status='⬜ intention', datetime=z(7).replace('2026-10-08', '2026-10-02'))
        day = [row(title='📗 finished Understanding Maslow and the Hierarchy of Needs', status='◉ done', datetime=z(6, 51)),
               row(title='⚡ Called the clinic back', status='✅ done', key='261005_0900', datetime=z(10), end=z(10, 10)),
               row(title='📝 thinking about the garage', status='● log', datetime=z(12))]          # a note, not done
        items = Q.reconcile(day, [book, same_key, untouched], OFF)
        got = {i['patch']['id']: i['patch']['fields'] for i in items}
        self.assertEqual(got[book['id']], {'status': '✅ done', 'end': z(6, 51)})
        self.assertEqual(got[same_key['id']], {'status': '✅ done', 'end': z(10, 10)})
        self.assertNotIn(untouched['id'], got)
        self.assertIn('the same key', next(i['line'] for i in items if i['patch']['id'] == same_key['id']))

    def test_a_row_from_before_the_step_was_made_is_not_its_evidence(self):
        step = row(title='verify the hourly precipitation data', status='⬜ intention', datetime=z(15))
        earlier = row(title='hourly precipitation data checked', status='✅ done', datetime=z(9), end=z(9, 30))
        self.assertEqual(Q.reconcile([earlier], [step], OFF), [])


if __name__ == '__main__':
    unittest.main()
