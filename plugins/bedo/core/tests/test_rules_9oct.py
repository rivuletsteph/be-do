# -*- coding: utf-8 -*-
"""The 9 Oct amendment in the core: the entry check's new refusals, the
deduction rules, dayqa and preflight's rule-on-paper line. Every row and name
is invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_rules_9oct.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_dayqa as Q  # noqa: E402
import bedo_entry as E  # noqa: E402
import bedo_fill as FL  # noqa: E402
import bedo_people as PP  # noqa: E402
import bedo_preflight as P  # noqa: E402
import bedo_rules as RU  # noqa: E402
from bedo_reader import FACTS as F  # noqa: E402

LOG, DONE, INT, POT = '● log', '◉ done', '⬜ intention', '▫️potential'
DAY = dt.date(2026, 10, 8)


def z(h, m=0, day=DAY):
    """A local time on DAY (UTC−5), as the UTC stamp the base stores."""
    return (dt.datetime.combine(day, dt.time(h, m)) + dt.timedelta(hours=5)).strftime('%Y-%m-%dT%H:%M:00.000Z')


def row(**kw):
    r = {'datetime': z(9), 'status': LOG, 'practice': '📝 log', 'title': 'a note',
         'wellness': '🧠 mind', 'device': '📱 phone'}
    r.update(kw)
    return {k: v for k, v in r.items() if v is not None}


def has(probs, start):
    return any(p.startswith(start) for p in probs)


class Deduce(unittest.TestCase):
    ctx = FL.Context(catalog={'📗 morning book': '🧠 mind'}, drives={'Work drive': '💨 air'})

    def test_wellness_drive_first_then_catalog_else_ask(self):
        got, ask = FL.deduce(row(practice='⚡ action', rhythm='Work drive', wellness=None), self.ctx)
        self.assertEqual(got['wellness'][0], '💨 air')
        got, _ = FL.deduce(row(practice='📗 morning book', wellness=None), self.ctx)
        self.assertEqual(got['wellness'][0], '🧠 mind')
        got, ask = FL.deduce(row(practice='🧶 knitting', wellness=None), self.ctx)
        self.assertEqual((got, ask), ({}, ['wellness']))

    def test_device_by_practice_title_and_span(self):
        d = lambda **kw: FL.deduce(row(device=None, **kw), ctx)[0].get('device', (None,))[0]
        ctx = FL.Context(day_rows=[row(practice='🚶‍♀️ walking', datetime=z(17), end=z(18))])
        self.assertEqual(d(practice='☕ coffee'), '🚫 none')
        self.assertEqual(d(practice='🪐 morning oura'), '📱 phone')
        self.assertEqual(d(practice='📝 log', title='notes on the laptop'), '💻 laptop')
        self.assertEqual(d(practice='📝 log', datetime=z(17, 20)), '🚫 none')    # inside the walk
        self.assertIsNone(d(practice='📝 log', datetime=z(19)))

    def test_a_plan_carries_no_device_and_history_only_hints(self):
        self.assertEqual(FL.deduce(row(status=INT, device=None), self.ctx), ({}, []))
        ctx = FL.Context(history=[row(practice='🧶 knitting', device='📺 tv')] * 3)
        got, ask = FL.deduce(row(practice='🧶 knitting', device=None), ctx)
        self.assertEqual((got, ask), ({}, ['device']))                     # history never fills
        self.assertIn('usually 📺 tv', FL.ask_line(row(practice='🧶 knitting'), 'device', ctx))

    def test_personal_practices_extend_the_lists(self):
        ctx = FL.Context(local={'fill': {'device_none': ['🧩 example quest']}})
        self.assertEqual(FL.deduce(row(practice='🧩 example quest', device=None), ctx)[0]['device'][0], '🚫 none')


class Entry(unittest.TestCase):
    def test_a_whole_row_passes(self):
        self.assertEqual(E.problems(row(), utc_offset_hours=-5), [])

    def test_empty_device_or_wellness_is_refused(self):
        p = E.problems(row(practice='☕ coffee', device=None))
        self.assertTrue(any('deduced 🚫 none' in x for x in p))          # refused, with the value to write
        p = E.problems(row(practice='🧶 knitting', wellness=None))
        self.assertTrue(any('ASK her' in x for x in p))                  # not deducible: asked
        self.assertFalse(has(E.problems(row(status=INT, device=None, practice='⚡ action',
                                            key='261008_0900')), 'device'))

    def test_a_row_is_one_day_and_at_most_twelve_hours(self):
        # 8 Oct: a 26 Sep row closed with an 8 Oct end spanned from midnight
        old = row(datetime=z(9, day=dt.date(2026, 9, 26)), end=z(10))
        p = E.problems(old, utc_offset_hours=-5)
        self.assertTrue(any('over 12 h' in x for x in p))
        self.assertTrue(any('one row, one day' in x for x in p))
        late = row(datetime=z(23), end=z(0, 30, DAY + dt.timedelta(days=1)))
        self.assertTrue(has(E.problems(late, utc_offset_hours=-5), 'span'))
        night = row(practice='😴 sleep', device='🚫 none', wellness='🤸‍♀️ body', datetime=z(22, 30),
                    end=z(6, 30, DAY + dt.timedelta(days=1)))
        self.assertEqual(E.problems(night, utc_offset_hours=-5), [])      # a night crosses midnight
        self.assertTrue(has(E.problems(dict(night, end=z(11, 0, DAY + dt.timedelta(days=1))),
                                       utc_offset_hours=-5), 'span'))      # but not twelve hours

    def test_person_on_a_plan_is_refused(self):
        plan = row(status=INT, practice='⚡ action', key='261008_0900', person='Robin', device=None)
        self.assertTrue(has(E.problems(plan), 'person'))
        self.assertFalse(has(E.problems(dict(plan, person=None, mentioned='Robin')), 'person'))
        self.assertTrue(has(E.problems(row(status=POT, practice='⚡ action', key='261008_0900',
                                           person='Robin', device=None)), 'person'))
        self.assertFalse(has(E.problems(row(person='Robin')), 'person'))  # it happened

    def test_every_row_carries_a_practice(self):
        self.assertTrue(has(E.problems(row(practice='')), 'practice'))


class People(unittest.TestCase):
    ix = PP.Index([('m', ['Marigold Example', 'mum']), ('p', ['Pat', 'pop']),
                   ('c', ['Corisande', 'Cori', 'Coz']), ('a', ['Alex One']), ('b', ['Alex Two'])])

    def test_any_form_finds_them(self):
        f = self.ix.find
        self.assertEqual([f('Marigold'), f('mum'), f('Pat Example'), f('Coz'), f('🧡 Cori')],
                         ['m', 'm', 'p', 'c', 'c'])

    def test_a_shared_first_name_finds_nobody(self):
        self.assertIsNone(self.ix.find('Alex'))
        self.assertEqual(self.ix.find('Alex Two'), 'b')


class DayQA(unittest.TestCase):
    def day(self):
        n = iter(range(100))
        mk = lambda **kw: dict(row(**kw), id=f'r{next(n)}')
        return [
            mk(practice='😶 wake', datetime=z(7), device='🚫 none', wellness='🤸‍♀️ body'),
            mk(practice='🍴 dinner', title='🍴 tacos', datetime=z(18), photo=True,
               device='🚫 none', wellness='🤸‍♀️ body'),
            mk(practice='🗨️ text', title='rode my bike to the park', datetime=z(10)),
            mk(practice='🪐 morning oura', details='walking 2:10p–2:40p, sleep 7h', datetime=z(7, 30)),
            mk(practice='⚡ action', status=INT, key='261008_1200', person='Robin', datetime=z(12)),
            mk(practice='☕ coffee', datetime=z(7, 10), device=None),
            mk(practice='🧶 knitting', datetime=z(20), wellness=None),
            mk(practice='⚡ action', title='closed late', datetime=z(9, day=dt.date(2026, 9, 26)),
               end=z(11), status='✅ done', key='260926_0900'),
            mk(practice='📝 log', datetime=z(15), end=z(15, 30)),
            mk(practice='📝 log', datetime=z(16, 30), end=z(17)),
        ]

    def test_one_list_every_fill_estimated_with_its_source(self):
        rows = self.day()
        items = Q.run(rows, DAY, -5, {}, typical={'cycling': 40},
                      catalog_names=['🚴‍♀️ cycling', '🚶‍♀️ walking'])
        checks = {i['check'] for i in items}
        self.assertTrue({'meals', 'gaps', 'movement', 'people', 'device', 'spans'} <= checks)
        fills = [i for i in items if i['kind'] == 'fill']
        self.assertTrue(all(i['source'] for i in fills))
        allowed = set(F['dayqa']['sources'].values())
        for i in fills:
            self.assertTrue(any(s in i['source'] for s in allowed), i)
            self.assertIn('ESTIMATED FROM CONTEXT', i['note'] if not i.get('new') else i['new']['details'] + i['note'])
        text = Q.render(items, DAY, rows, -5)
        self.assertTrue(all('ESTIMATED FROM CONTEXT · source:' in l for l in text.splitlines()
                            if l.strip()[:1].isdigit() and ' ASK ' not in l))
        self.assertIn('dayqa shown 2026-10-08', text)

    def test_what_each_check_proposes(self):
        items = Q.run(self.day(), DAY, -5, {}, typical={'cycling': 40},
                      catalog_names=['🚴‍♀️ cycling', '🚶‍♀️ walking'])
        by = lambda c: [i for i in items if i['check'] == c]
        meal = [i for i in by('meals') if i.get('new')][0]
        self.assertEqual(meal['new']['practice'], '🍳 dinner prep')
        self.assertIn('photo time', meal['source'])
        mv = [i for i in by('movement') if i['kind'] == 'fill']
        self.assertEqual({i['new']['practice'] for i in mv}, {'🚴‍♀️ cycling', '🚶‍♀️ walking'})
        self.assertEqual({i['source'].split(' + ')[0] for i in mv}, {'message time', 'Oura'})
        ppl = by('people')[0]
        self.assertEqual(ppl['patch']['fields'], {'person': '', 'mentioned': 'Robin'})
        dev = [i for i in by('device') if i['kind'] == 'fill'][0]
        self.assertEqual(dev['patch']['fields'], {'device': '🚫 none'})
        self.assertTrue(any('wellness' in i['line'] for i in by('device') if i['kind'] == 'ask'))
        self.assertTrue(any('15:30' in i['line'] or '3:30p' in i['line'] for i in by('gaps')))
        self.assertTrue(by('spans'))

    def test_the_gate_counts(self):
        (lack, n), long_ = Q.gate(self.day(), -5)
        self.assertEqual((lack, n), (2, 9))
        self.assertEqual(len(long_), 1)


class Paper(unittest.TestCase):
    AM = [('recXXXXXXXXXXXXXX', '2026-10-09', 'every row is born whole'),
          ('recXXXXXXXXXXXXX', '2026-10-08', 'a nickname in dictation'),
          ('recXXXXXXXXXXXX', '2026-10-07', 'a rule nobody coded')]

    def test_an_active_amendment_with_no_check_is_on_paper(self):
        m = {'recXXXXXXXXXXXXXX': ['entry.whole', 'look_behind.gate'], 'recXXXXXXXXXXXXX': ['judgment']}
        paper = RU.on_paper(self.AM, m)
        self.assertEqual([p[0] for p in paper], ['recXXXXXXXXXXXX'])
        m['recXXXXXXXXXXXXX'] = ['entry.nickname']                      # a check the code doesn't have
        self.assertEqual(len(RU.on_paper(self.AM, m)), 2)

    def test_active_reads_the_table(self):
        recs = [{'id': a, 'createdTime': '', 'fields': {'date': d, 'decision': t, 'status': s}}
                for (a, d, t), s in zip(self.AM, ['active', 'active', 'folded'])]
        self.assertEqual(len(RU.active(recs, {})), 2)

    def test_preflight_prints_it(self):
        L = {'utc_offset_hours': -5, 'amendment_checks': {'recXXXXXXXXXXXXXX': ['entry.whole']}}
        now = dt.datetime(2026, 10, 9, 14, tzinfo=dt.timezone.utc)
        rows = [{'datetime': '2026-10-09T13:00:00.000Z'}]
        text, stop = P.report(L, {'w41 be•do': 'appXXXXXXXXXXXXXX'}, rows, now, amendments=self.AM)
        self.assertEqual(text.count('rule on paper only'), 2)
        self.assertFalse(stop)                                           # named, never a stop

    def test_every_registered_check_names_a_real_module(self):
        files = {f[:-3] for _, _, fs in os.walk(os.path.dirname(CORE)) for f in fs if f.endswith('.py')}
        for name, what in RU.CHECKS.items():
            for mod in what.split(' — ')[0].split(' + '):
                self.assertIn(mod.strip(), files, name)

if __name__ == '__main__':
    unittest.main()
