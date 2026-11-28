# -*- coding: utf-8 -*-
"""A flow closes right after its last logged step, read from the stream,
without waiting for her (amendment, Sat 21 Nov 2026). On Fri 20 Nov the last
dawn step was logged at 10:26 AM, but the morning book step had come in as its
own book row, so the flow never counted as complete and the close waited until
she asked in the afternoon."""
import datetime as dt, io, json, os, sys, tempfile, unittest
from unittest import mock
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bedo_remaining as R  # noqa: E402

FL = R.FLOWS
LOCAL = {'weekly_name': 'w{n} be•do', 'utc_offset_hours': -6, 'time_zone': 'America/Chicago'}
DAY = dt.date(2026, 11, 20)
BOOK_STEP = next(iter(FL['same_kind']['dawn']))             # the step a row of its kind shows done
BOOK_ROW = FL['same_kind']['dawn'][BOOK_STEP][0]
CLOSE = FL['close']['dawn']


def z(hhmm):
    """Local Central standard time on DAY → the stored UTC string."""
    t = dt.datetime.combine(DAY, dt.time(*map(int, hhmm.split(':')))) + dt.timedelta(hours=6)
    return t.strftime('%Y-%m-%dT%H:%M:00.000Z')


def step(name, group='flow'):
    return {'practice': name, 'phase': FL['phase']['dawn'], 'order': None, 'group': group, 'active': True}


CAT = [step(p) for p in FL['core']['dawn']] + [step('🔅 morning sun', 'optional')]
STEPS = R.flow_steps(CAT, 'dawn')


def day(book_at='09:00', without=()):
    """Every required dawn step logged, the last at 10:26 AM, the book step
    only as a row of its own kind."""
    req = [p for p in FL['core']['dawn'] if p not in (CLOSE, BOOK_STEP) and p not in without]
    rows = [{'id': f'r{i}', 'practice': p, 'datetime': z(f'{7 + i // 6}:{(i * 7) % 60:02d}')}
            for i, p in enumerate(req)]
    rows[-1]['datetime'] = z('10:26')
    if book_at:
        rows.append({'id': 'rb', 'practice': BOOK_ROW, 'datetime': z(book_at)})
    return rows


class SameKind(unittest.TestCase):
    def test_a_book_row_that_morning_is_the_book_step(self):
        rows = day()
        self.assertIn(R.norm(BOOK_STEP), R.logged(rows, LOCAL))
        self.assertEqual(R.holds_open(STEPS, rows, 'dawn', LOCAL), [])
        self.assertNotIn(BOOK_STEP, R.render('dawn', STEPS, rows, loc=LOCAL))

    def test_an_afternoon_book_row_is_not_the_morning_step(self):
        rows = day(book_at='15:00')
        self.assertEqual(R.holds_open(STEPS, rows, 'dawn', LOCAL), [BOOK_STEP])

    def test_the_mapping_is_data(self):
        self.assertIsInstance(FL['same_kind'], dict)
        self.assertEqual(set(FL['same_kind']), {'dawn', 'dusk'})


class ClosesItself(unittest.TestCase):
    def test_complete_says_close_now_at_the_last_steps_time(self):
        line = R.close_line('dawn', STEPS, day(), DAY, None, LOCAL)
        last = day()[-2]['practice']                          # the row at 10:26 AM (the book row is last in the list)
        self.assertEqual(line, f'🌅 dawn flow complete: last step {last} at 10:26 AM. '
                               f'Write {CLOSE} now, at 10:26 AM, without asking her.')

    def test_complete_even_when_asked_in_the_afternoon(self):
        line = R.close_line('dawn', STEPS, day(), DAY, dt.datetime(2026, 11, 20, 14, 21), LOCAL)
        self.assertIn('flow complete', line)
        self.assertIn('10:26 AM', line)

    def test_the_book_row_can_be_the_last_step(self):
        line = R.close_line('dawn', STEPS, day(book_at='11:02'), DAY, None, LOCAL)
        self.assertIn(f'last step {BOOK_STEP} at 11:02 AM', line)

    def test_still_running_says_nothing_before_the_backup(self):
        rows = day(without=('🙏 gratitude',))
        self.assertIsNone(R.close_line('dawn', STEPS, rows, DAY, dt.datetime(2026, 11, 20, 11, 30), LOCAL))

    def test_past_the_backup_says_write_it_without_waiting(self):
        rows = day(without=('🙏 gratitude',))
        line = R.close_line('dawn', STEPS, rows, DAY, dt.datetime(2026, 11, 20, 12, 5), LOCAL)
        self.assertIn('past the 12:00 PM backup', line)
        self.assertIn(f'write the backup {CLOSE} now, at 12:00 PM', line)
        self.assertIn('without waiting for a reply', line)
        self.assertIn('🙏 gratitude', line)
        self.assertNotIn(CLOSE + ',', line.split('capture:')[1])

    def test_dusk_writes_no_backup_at_night(self):
        # her words, 24 Nov 2026: I want the evening to close when I fall asleep
        steps = [{'practice': '🫖 evening tea', 'phase': FL['phase']['dusk'], 'group': 'flow', 'order': 1},
                 {'practice': FL['close']['dusk'], 'phase': FL['phase']['dusk'], 'group': 'flow', 'order': 2}]
        self.assertIsNone(R.close_line('dusk', steps, [], DAY, dt.datetime(2026, 11, 20, 23, 59), LOCAL))

    def test_another_day_never_gets_a_backup_line(self):
        rows = day(without=('🙏 gratitude',))
        self.assertIsNone(R.close_line('dawn', STEPS, rows, DAY, dt.datetime(2026, 11, 21, 9, 0), LOCAL))

    def test_a_logged_close_says_nothing(self):
        rows = day() + [{'id': 'rc', 'practice': CLOSE, 'datetime': z('10:27')}]
        self.assertIsNone(R.close_line('dawn', STEPS, rows, DAY, dt.datetime(2026, 11, 20, 14, 0), LOCAL))

    def test_main_prints_the_line_under_the_box(self):
        rows = day()
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as d:
            cp, dp, lp = (os.path.join(d, n) for n in ('c.json', 'd.json', 'l.json'))
            json.dump({'records': [{'id': f'p{i}', 'createdTime': 'x', 'fields': s} for i, s in enumerate(CAT)],
                       'metadata': {'totalRecordCount': len(CAT)}}, open(cp, 'w', encoding='utf-8'))
            json.dump({'records': [{'id': r['id'], 'createdTime': 'x', 'fields': r} for r in rows],
                       'metadata': {'totalRecordCount': len(rows)}}, open(dp, 'w', encoding='utf-8'))
            json.dump(LOCAL, open(lp, 'w', encoding='utf-8'))
            with mock.patch.dict(os.environ, {'BEDO_FACTS_LOCAL': lp}), mock.patch('sys.stdout', out):
                R.main(['--catalog', cp, '--day', dp, '--flow', 'dawn', '--date', DAY.isoformat()])
        text = out.getvalue()
        self.assertIn('```', text)
        self.assertTrue(text.strip().splitlines()[-1].startswith('🌅 dawn flow complete: last step'))
        self.assertIn('10:26 AM', text)


if __name__ == '__main__':
    unittest.main()
