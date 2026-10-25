# -*- coding: utf-8 -*-
"""Keepers and info (25 Oct 2026): which kind a row's photo is, which file in
the week's folder is its photo, and where a photo sits on a page. Every row is
invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_photos.py
"""
import datetime as dt, os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_photos as PH  # noqa: E402
import bedo_dusk_audit as DA  # noqa: E402

OFF = -5          # CDT
ME = '♋ Self'
DAY = dt.date(2026, 10, 25)


def at(h, m=0):
    return dt.datetime(2026, 10, 25, h, m)


def row(rid, practice, title, h, m=0, **kw):
    return dict(id=rid, practice=practice, title=title, _a=at(h, m), **kw)


def pxl(h, m, s=0):
    """The phone's name for a photo taken at local h:m (UTC is five hours on)."""
    u = at(h, m, ) + dt.timedelta(hours=-OFF, seconds=s)
    return f'PXL_{u:%Y%m%d}_{u:%H%M%S}123.jpg'


class Kind(unittest.TestCase):

    def test_her_word_wins(self):
        self.assertEqual(PH.kind({'practice': '🍽️ breakfast', 'photo': 'keeper'}), 'keeper')
        self.assertEqual(PH.kind({'practice': '✨ glimmer', 'photo': 'info'}), 'info')

    def test_just_food_is_info(self):
        r = {'practice': '🍽️ breakfast', 'title': 'sourdough French toast, bacon, strawberries', 'photo_checked': True}
        self.assertEqual(PH.kind(r, ME), 'info')

    def test_food_with_people_or_a_place_is_a_keeper(self):
        for r in ({'practice': '🍽️ lunch', 'title': 'lunch out together', 'person': f'{ME}, ♐Partner'},
                  {'practice': '🍽️ dinner', 'title': "dinner at the neighbours' — beef ragu"},
                  {'practice': '🍽️ dinner', 'title': 'family dinner — meatloaf'}):
            self.assertEqual(PH.kind(dict(r, photo_checked=True), ME), 'keeper', r)

    def test_her_own_name_alone_is_not_company(self):
        r = {'practice': '🍽️ breakfast', 'title': 'oatmeal', 'person': ME, 'photo_checked': True}
        self.assertEqual(PH.kind(r, ME), 'info')

    def test_checks_and_screens_are_info(self):
        for p in ('🌈 supplements', '🪐 evening oura', '🌦️ weather check', "💊 Kid's meds", '🛍️ shopping'):
            self.assertEqual(PH.kind({'practice': p, 'photo_checked': True}), 'info', p)

    def test_everything_else_is_a_keeper(self):
        for p in ('✨ glimmer', '🚶‍♀️ walking', '🔅 evening sun', '👁‍🗨 noticing'):
            self.assertEqual(PH.kind({'practice': p, 'photo_checked': True}), 'keeper', p)

    def test_from_her_photo_in_the_details_counts(self):
        self.assertEqual(PH.kind({'practice': '⭐ highlight', 'details': 'From her photo.'}), 'keeper')

    def test_no_photo_no_kind(self):
        self.assertIsNone(PH.kind({'practice': '✨ glimmer', 'title': 'the kid sleeping'}))


class Match(unittest.TestCase):

    def test_a_photo_shared_late_finds_the_one_taken_before(self):
        # taken 9:12, shared in the chat and logged at 9:40; a later photo is not it
        rows = [row('r1', '✨ glimmer', 'pink sky', 9, 40, photo='keeper')]
        files = [{'id': 'F1', 'name': pxl(9, 12)}, {'id': 'F2', 'name': pxl(10, 30)}]
        m = PH.match(rows, files, OFF, ME)
        self.assertEqual([(x['id'], x['file']) for x in m['links']], [('r1', 'F1')])
        self.assertEqual(m['links'][0]['url'], PH.link('F1'))
        self.assertTrue(PH.link('F1').endswith('/file/d/F1/view'))

    def test_nearest_before_wins_and_each_file_is_used_once(self):
        rows = [row('r1', '🚶‍♀️ walking', 'walk', 9, 40, photo='keeper'),
                row('r2', '🍽️ breakfast', 'toast', 9, 41, photo='info')]
        files = [{'id': 'A', 'name': pxl(9, 12)}, {'id': 'B', 'name': pxl(9, 38)}]
        m = PH.match(rows, files, OFF, ME)
        self.assertEqual({x['id']: x['file'] for x in m['links']}, {'r1': 'B', 'r2': 'A'})

    def test_a_keeper_not_in_the_folder_is_named(self):
        rows = [row('r1', '✨ glimmer', 'Care Bears glass', 18, 45, photo='keeper'),
                row('r2', '🍽️ breakfast', 'toast', 9, photo='info')]
        m = PH.match(rows, [], OFF, ME)
        self.assertEqual([x['id'] for x in m['missing']], ['r1'])     # info is never chased

    def test_a_row_already_linked_keeps_its_file(self):
        rows = [row('r1', '✨ glimmer', 'a', 9, 40, photo='keeper',
                    photo_links=PH.link('A23456789012')),
                row('r2', '✨ glimmer', 'b', 9, 41, photo='keeper')]
        files = [{'id': 'A23456789012', 'name': pxl(9, 39)}, {'id': 'B', 'name': pxl(9, 20)}]
        m = PH.match(rows, files, OFF, ME)
        self.assertEqual([(x['id'], x['file']) for x in m['links']], [('r2', 'B')])

    def test_a_photo_no_row_explains_is_a_clue(self):
        rows = [row('r1', '✨ glimmer', 'a', 9, 40, photo='keeper')]
        m = PH.match(rows, [{'id': 'A', 'name': pxl(9, 39)}, {'id': 'Z', 'name': pxl(15, 0)}], OFF, ME)
        self.assertEqual([x['file'] for x in m['unlogged']], ['Z'])

    def test_rows_from_the_old_checkbox_get_their_kind(self):
        rows = [row('r1', '🍽️ breakfast', 'toast', 9, photo_checked=True),
                row('r2', '✨ glimmer', 'a', 10, photo='keeper')]
        self.assertEqual(PH.match(rows, [], OFF, ME)['kinds'], [{'id': 'r1', 'title': 'toast', 'kind': 'info'}])

    def test_a_drive_connector_listing_reads(self):
        self.assertEqual(PH.files_from({'files': [{'id': 'X', 'title': 'PXL_1.jpg'}]}), [{'id': 'X', 'name': 'PXL_1.jpg'}])


class Place(unittest.TestCase):

    def test_a_linked_photo_lands_on_its_row_however_late_it_was_logged(self):
        fid = '1aBcD3fGhIjKlMnOpQrStUvWxYz012345'
        rows = [row('r1', '✨ glimmer', 'a', 11, photo='keeper', photo_links=PH.link(fid)),
                row('r2', '📝 log', 'b', 9, 12)]
        placed, left = PH.place(rows, [(at(9, 12), fid, 'src1')], ME)
        self.assertEqual((placed[0]['row']['id'], placed[0]['keeper'], left), ('r1', True, 0))

    def test_info_photos_stay_off_the_page(self):
        rows = [row('r1', '🍽️ breakfast', 'toast', 9, photo='info'),
                row('r2', '🍽️ lunch', 'sandwich', 12)]                   # never said; food by rule
        placed, left = PH.place(rows, [(at(9), None, 's1'), (at(12), None, 's2')], ME)
        self.assertEqual((placed, left), ([], 2))

    def test_a_photo_near_nothing_is_loose(self):
        placed, left = PH.place([row('r1', '✨ glimmer', 'a', 9, photo='keeper')], [(at(15), None, 's')], ME)
        self.assertEqual((placed[0]['row'], placed[0]['keeper'], left), (None, False, 0))


class Dusk(unittest.TestCase):

    def test_the_audit_writes_kinds_and_links(self):
        z = lambda h, m=0: f'2026-10-25T{h - OFF:02d}:{m:02d}:00.000Z'  # noqa: E731
        rows = [{'id': 'r1', 'practice': '🍽️ breakfast', 'title': 'toast', 'datetime': z(9, 40),
                 'photo_checked': True, 'status': '◉ done'},
                {'id': 'r2', 'practice': '✨ glimmer', 'title': 'sky', 'datetime': z(18), 'photo': 'keeper',
                 'status': '◉ done'}]
        files = [{'id': 'F1', 'name': pxl(9, 12)}, {'id': 'OLD', 'name': pxl(9, 12).replace('20261025', '20261024')}]
        now = dt.datetime(2026, 10, 26, 3, 0, tzinfo=dt.timezone.utc)
        res = DA.audit(rows, now, OFF, day=DAY, photo_files=files, me=ME)
        w = {x['id']: x for x in res['photo_writes']}
        self.assertEqual(w['r1'], {'id': 'r1', 'photo': 'info',
                                   'photo_links': PH.link('F1')})
        self.assertEqual(res['findings']['photo_missing'], ['sky (6:00 PM)'])
        self.assertNotIn('photo', res['flag'])

    def test_without_the_folder_only_kinds_are_written(self):
        rows = [{'id': 'r1', 'practice': '✨ glimmer', 'title': 'sky', 'datetime': '2026-10-25T23:00:00.000Z',
                 'photo_checked': True, 'status': '◉ done'}]
        now = dt.datetime(2026, 10, 26, 3, 0, tzinfo=dt.timezone.utc)
        res = DA.audit(rows, now, OFF, day=DAY, me=ME)
        self.assertEqual(res['photo_writes'], [{'id': 'r1', 'photo': 'keeper'}])
        self.assertEqual(res['findings']['photo_missing'], [])


if __name__ == '__main__':
    unittest.main(verbosity=1)
