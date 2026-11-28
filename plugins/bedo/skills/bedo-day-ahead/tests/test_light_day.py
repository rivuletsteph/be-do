# -*- coding: utf-8 -*-
"""A holiday or a full day is a light day (26 Nov 2026, her words: I'm seeing a lot of
unresolved tasks that I really don't need to see today … it seems totally disconnected
from the fact that today is a full holiday). Its page leads with the plan, leaves off
open steps not due that day, and could go together closes every page.

Every name below is an obvious invention.

    python3 tests/test_light_day.py
"""
import datetime as dt
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import flow  # noqa: E402

ENGINE = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()


class Light(unittest.TestCase):
    def test_holidays_by_rule(self):
        h = flow.fixed_holidays(2026)
        for d in ('2026-01-01', '2026-05-25', '2026-07-04', '2026-09-07', '2026-11-26', '2026-11-27', '2026-12-25'):
            self.assertIn(dt.date.fromisoformat(d), h, d)
        self.assertNotIn(dt.date(2026, 11, 24), h)

    def test_what_makes_a_day_light(self):
        day = dt.date(2026, 3, 11)
        self.assertIsNone(flow.light_day(day, {'events': []}, {'full': False}, {}))
        self.assertEqual(flow.light_day(day, None, None, {}, forced=True), 'holiday')
        self.assertEqual(flow.light_day(day, None, None, {'holidays': ['2026-03-11']}), 'holiday')
        self.assertEqual(flow.light_day(day, None, {'full': True}, {}), 'full')
        # an all-day event of hers named for a holiday, on its last day ("ends today", no end time)
        ev = dict(who='you', title='🏢 Campus Closed — spring break', when='ends today', end='')
        self.assertEqual(flow.light_day(day, {'events': [ev]}, None, {}), 'holiday')
        # a timed event with the word, or someone else's all-day one, doesn't make it a holiday
        self.assertIsNone(flow.light_day(day, {'events': [dict(ev, end='5p'), dict(ev, who='Kid')]}, None, {}))

    def test_the_engine_keeps_only_what_is_due(self):
        self.assertIn('inWin=D.light?(a=>dueToday(a))', ENGINE)
        self.assertIn('const rest=over_||D.light?[]:stars(blocks)', ENGINE)
        self.assertIn('const lite=D.light&&!over3&&!D.picked', ENGINE)

    def test_now_leads_with_a_plan_and_could_go_together_closes(self):
        a = ENGINE[ENGINE.index('function arrange()'):]
        self.assertIn("let L_=(plan?['now']:[]).concat(ids.filter(id=>id!=='grp'&&id!=='now'))", a)
        self.assertIn("if(dl) dl.before(grpEl); else m.parentNode.appendChild(grpEl);", a)
        self.assertNotIn("'grp'", ENGINE[ENGINE.index('DASH={'):ENGINE.index('DASH={') + 80])


if __name__ == '__main__':
    unittest.main()
