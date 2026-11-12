# -*- coding: utf-8 -*-
"""The weekly drive cleanup (9 Nov 2026): what it leaves alone, what it picks,
and the evidence it finds before she sees anything. Every name is invented.

    python3 plugins/bedo/core/tests/test_cleanup.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_cleanup as C  # noqa: E402

TODAY = dt.date(2026, 11, 9)
GARDEN, BOOKS, CAR = 'Garden Plot', 'Book Club', 'Old Truck'
_n = [0]


def row(title, status='⬜ intention', key=None, rhythm=GARDEN, **kw):
    _n[0] += 1
    r = dict(id=f'rec{_n[0]:04d}', title=title, status=status, key=key, rhythm=rhythm,
             datetime=kw.pop('datetime', '2026-09-01T15:00:00.000Z'), details=kw.pop('details', ''),
             practice=kw.pop('practice', '⚡ action'), queue=kw.pop('queue', False),
             waiting_on=kw.pop('waiting_on', None))
    r.update(kw)
    return r


class Picture(unittest.TestCase):
    def test_sorts_the_open_rows(self):
        rows = [row('plant the bulbs', key='260801_0900'),
                row('a someday greenhouse', status='▫️potential'),
                row('ticked by her', queue=True),
                row('waiting on the neighbour', waiting_on='a neighbour'),
                row('fresh this week', key='261105_0900'),
                row('already done', status='✅ done')]
        p = C.picture(rows, TODAY)
        self.assertEqual({k: len(v) for k, v in p.items()},
                         dict(open=5, potential=1, queue=1, waiting=1, fresh=1, stale=1))

    def test_age_comes_from_the_key(self):
        r = row('x', key='261020_1200', datetime='2026-11-08T15:00:00.000Z')
        C.picture([r], TODAY)
        self.assertEqual(r['age'], 20)


class Pick(unittest.TestCase):
    def test_undriven_first_then_the_stalest(self):
        rows = [row('no home', rhythm='')] + [row(f'garden {i}') for i in range(3)] + \
               [row(f'book {i}', rhythm=BOOKS) for i in range(2)] + [row('truck', rhythm=CAR)]
        rep = C.run(rows, TODAY, n=2)
        self.assertEqual([g['drive'] for g in rep['week']], ['', GARDEN, BOOKS])

    def test_a_drive_cleaned_lately_waits_its_turn(self):
        line = f"———\n{C.MARK}Mon 2 Nov 2026 (branch): ⬜ kept, her yes."
        rows = [row(f'garden {i}', details=line) for i in range(3)] + [row('book', rhythm=BOOKS)]
        rep = C.run(rows, TODAY, n=2)
        self.assertEqual([g['drive'] for g in rep['week']], [BOOKS])
        self.assertIn(GARDEN, rep['waiting_turn'])

    def test_placing_a_row_is_not_reviewing_it(self):
        line = f"———\n{C.MARK}Mon 9 Nov 2026 (branch): drive set to {GARDEN}, be•do's call."
        rows = [row('garden', details=line)]
        self.assertEqual(C.cleaned_on(rows[0]), [])
        self.assertEqual([g['drive'] for g in C.run(rows, TODAY)['week']], [GARDEN])

    def test_a_row_reviewed_lately_is_not_asked_again(self):
        line = f"———\n{C.MARK}Mon 2 Nov 2026 (branch): ⬜ kept, her yes."
        old = f"———\n{C.MARK}Fri 2 Oct 2026 (branch): ⬜ kept, her yes."
        rows = [row('garden a', details=line), row('garden b'), row('garden c'), row('garden d', details=old)]
        titles = [c['title'] for g in C.run(rows, TODAY)['week'] for c in g['rows']]
        self.assertEqual(sorted(titles), ['garden b', 'garden c', 'garden d'])


class Evidence(unittest.TestCase):
    def kinds(self, r, rows):
        return [k for k, _, _ in C.evidence(r, rows, [x for x in rows if x.get('rhythm') == r.get('rhythm')])]

    def test_a_key_closed_elsewhere(self):
        a = row('mulch the beds', key='260901_0800')
        b = row('mulch the beds', key='260901_0800', status='✅ done')
        self.assertIn('done', self.kinds(a, [a, b]))

    def test_a_done_row_in_the_drive_sharing_its_words(self):
        a = row('order compost bins for the garden', key='260901_0800')
        b = row('compost bins ordered', status='✅ done', key='261001_0800')
        c = row('compost bins ordered', status='✅ done', key='261001_0900', rhythm=BOOKS)
        self.assertEqual(self.kinds(a, [a, b, c]).count('done'), 1)

    def test_an_older_done_row_is_not_evidence(self):
        a = row('order compost bins', key='261001_0800')
        b = row('compost bins ordered', status='✅ done', key='260801_0800')
        self.assertNotIn('done', self.kinds(a, [a, b]))

    def test_two_open_rows_saying_the_same_thing_once(self):
        a = row('share the trail map with the club', key='260901_0800')
        b = row('send the trail map to the club members', key='260902_0800')
        found = self.kinds(a, [a, b]) + self.kinds(b, [a, b])
        self.assertEqual(found.count('dedupe'), 1)

    def test_media_goes_to_stories(self):
        self.assertTrue(C.is_media(row('a piece', practice='📰 news')))
        self.assertTrue(C.is_media(row('⚡ Watch the soil webinar recording')))
        self.assertTrue(C.is_media(row('Read the article on cover crops')))
        self.assertFalse(C.is_media(row('⚡ Watch for the seed catalog sale')))
        self.assertFalse(C.is_media(row('read the meter')))


class Render(unittest.TestCase):
    def test_it_prints_and_names_the_rule(self):
        rows = [row('no home', rhythm=''), row('garden')]
        out = C.render(C.run(rows, TODAY))
        self.assertIn('stale ⬜/▶️', out)
        self.assertIn('no drive', out)
        self.assertIn('✖️ and ⏸️ are hers', out)


if __name__ == '__main__':
    unittest.main(verbosity=1)
