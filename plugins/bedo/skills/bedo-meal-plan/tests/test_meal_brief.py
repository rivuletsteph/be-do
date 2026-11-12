# -*- coding: utf-8 -*-
"""The meal brief reads what was eaten, the days ahead, the shelf and the
recipes. Every row is invented; the shapes are the bases'.

    python3 plugins/bedo/skills/bedo-meal-plan/tests/test_meal_brief.py
"""
import datetime as dt, os, sys, unittest

SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts')
sys.path.insert(0, SCRIPTS)
import meal_brief as MB  # noqa: E402

LOCAL = {'time_zone': 'America/Chicago', 'utc_offset_hours': -6}
TODAY = dt.date(2026, 11, 5)          # a Thursday
SHAPE = {'mon': 'meatless', 'tue': 'tacos', 'fri': 'pizza'}


def meal(rid, practice, when, title, status='● log', details=None):
    return {'id': rid, 'practice': practice, 'datetime': when, 'title': title,
            'status': status, 'details': details}


def item(name, status='on hand', where='fridge', life=7, added='2026-11-03', kind='consumable', buy=None):
    return {'item': name, 'status': status, 'where': where, 'shelf_life': life, 'added': added,
            'kind': kind, 'buy_where': buy}


class Ate(unittest.TestCase):

    def test_reheated_cooked_out_and_theirs(self):
        rows = [
            meal('a', '🍳 dinner prep', '2026-11-03T23:00:00.000Z', '🍳 tacos'),
            meal('b', '🍽️ dinner', '2026-11-03T23:45:00.000Z', '🍽️ fish tacos'),
            meal('c', '🍽️ dinner', '2026-11-04T22:00:00.000Z', '🍽️ meatloaf, mashed potatoes',
                 details='The meatloaf was leftovers from the freezer.\n———\n[be•do] x'),
            meal('d', '🍽️ lunch', '2026-11-04T18:00:00.000Z', '🍽️ lunch at the diner'),
            meal('e', '🍽️ dinner', '2026-11-02T23:30:00.000Z', "🍽️ Mom's chili and a salad"),
            meal('f', '🍽️ dinner', '2026-10-20T23:30:00.000Z', '🍽️ too long ago'),
            meal('g', '🍽️ dinner', '2026-11-04T01:00:00.000Z', '🍽️ dropped one', status='✖️ dropped'),
        ]
        a = MB.ate(rows, TODAY, 10, LOCAL)
        made = {m['what']: m['made'] for ms in a.values() for m in ms}
        self.assertEqual(made['fish tacos'], 'cooked')
        self.assertEqual(made['meatloaf, mashed potatoes'], 'reheated')
        self.assertEqual(made['lunch at the diner'], 'out')
        self.assertEqual(made["Mom's chili and a salad"], 'theirs')
        self.assertNotIn('too long ago', made)
        self.assertNotIn('dropped one', made)

    def test_a_morning_prep_does_not_cook_dinner_and_a_plan_was_not_eaten(self):
        rows = [
            meal('a', '🍳 meal prep', '2026-11-04T14:00:00.000Z', '🍳 made breakfast'),
            meal('b', '🍽️ dinner', '2026-11-04T23:30:00.000Z', '🍽️ soup and bread'),
            meal('c', '🤏🏻 snack', '2026-11-04T14:30:00.000Z', '🤏🏻 a cookie'),
            meal('d', '🍽️ dinner', '2026-11-04T23:00:00.000Z', '🍽️ dinner at the Taphouse — a burger'),
            meal('e', '🍽️ dinner', '2026-11-05T23:00:00.000Z', '🍽️ family dinner out', status='⬜ intention'),
        ]
        made = {m['what']: m['made'] for ms in MB.ate(rows, TODAY, 10, LOCAL).values() for m in ms}
        self.assertEqual(made['soup and bread'], 'eaten')
        self.assertEqual(made['a cookie'], 'eaten')
        self.assertEqual(made['dinner at the Taphouse — a burger'], 'out')
        self.assertNotIn('family dinner out', made)

    def test_a_meal_counts_on_its_local_day(self):
        # 7:30 PM local on the 4th is 01:30 UTC on the 5th
        a = MB.ate([meal('a', '🍽️ dinner', '2026-11-05T01:30:00.000Z', '🍽️ soup')], TODAY, 10, LOCAL)
        self.assertEqual(list(a), ['2026-11-04'])


class Ahead(unittest.TestCase):

    def test_seven_days_with_theme_and_food_intentions(self):
        rows = [{'id': 'p', 'status': '⬜ intention', 'target': '2026-11-07T22:00:00.000Z',
                 'title': '🎃 potluck at our house', 'details': ''},
                {'id': 'q', 'status': '⬜ intention', 'target': '2026-11-07T15:00:00.000Z',
                 'title': 'TPS report', 'details': ''},
                {'id': 'r', 'status': '✅ done', 'target': '2026-11-06T22:00:00.000Z',
                 'title': 'dinner out', 'details': ''}]
        a = MB.ahead(rows, TODAY, SHAPE, LOCAL)
        self.assertEqual(len(a), 7)
        self.assertEqual(a[0]['day'], 'thu')
        fri = next(x for x in a if x['day'] == 'fri')
        sat = next(x for x in a if x['day'] == 'sat')
        self.assertEqual(fri['theme'], 'pizza')
        self.assertEqual(fri['on the stream'], [])          # a done row is not ahead
        self.assertEqual(sat['on the stream'], ['potluck at our house'])


class Shelf(unittest.TestCase):

    def test_decay_wants_and_durables(self):
        s = MB.shelf([
            item('cilantro', life=7, added='2026-10-01'),
            item('mahi-mahi', where='freezer', life=180, added='2026-10-26'),
            item('whole milk', status='running low', life=14, added='2026-11-01'),
            item('limes', status='want', buy=[{'name': 'Corner Market'}]),
            item('spaghetti', status='want'),
            item('a blender', status='want', kind='durable'),
        ], TODAY)
        self.assertEqual(s['probably gone'], ['cilantro'])
        self.assertEqual(s['in date']['freezer'][0][0], 'mahi-mahi')
        self.assertIn('whole milk', s['running low'])
        self.assertIn('whole milk', [i for i, _ in s['in date']['fridge']])
        self.assertEqual(s['want'], {'Corner Market': ['limes'], 'store not named': ['spaghetti']})


class Recipes(unittest.TestCase):

    def test_matching_is_by_words_and_noun(self):
        self.assertTrue(MB.matches('chicken thighs', 'bone-in skin-on chicken thighs'))
        self.assertTrue(MB.matches('parmesan cheese', 'grated parmesan'))
        self.assertTrue(MB.matches('avocado', 'hass avocados'))
        self.assertTrue(MB.matches('jasmine rice', 'brown jasmine rice'))
        self.assertTrue(MB.matches('tomatoes', 'cherry tomatoes'))
        self.assertFalse(MB.matches('pasta', 'marinara pasta sauce'))
        self.assertFalse(MB.matches('long grain white rice', 'brown jasmine rice'))
        self.assertTrue(MB.matches('steak', 'steaks — freezer'))

    def test_scored_and_ordered(self):
        in_date = {'freezer': [['shrimp', 100], ['steaks — freezer', 90]],
                   'pantry': [['brown jasmine rice', 200], ['olive oil', 300]]}
        out = MB.score([
            {'title': 'shrimp rice bowl', 'standing': 'want to try', 'key_ingredients': 'shrimp\njasmine rice'},
            {'title': 'steak dinner', 'standing': 'in rotation', 'key_ingredients': ''},
            {'title': 'shrimp tacos', 'standing': 'in rotation', 'key_ingredients': 'shrimp\ntortillas\nlimes'},
            {'title': 'lasagna', 'standing': 'in rotation', 'key_ingredients': 'noodles\nricotta\nmozzarella\nbeef'},
            {'title': 'retired one', 'standing': 'retired', 'key_ingredients': 'shrimp'},
        ], in_date)
        fits = [(e['title'], e['fit']) for e in out]
        self.assertEqual(fits, [('shrimp rice bowl', 'probably makeable'), ('shrimp tacos', '2 away'),
                                ('lasagna', 'further'), ('steak dinner', 'no ingredients on record')])


class Text(unittest.TestCase):

    def test_the_brief_prints_with_its_caveat(self):
        b = MB.brief([], [item('eggs', life=30)], [], TODAY, LOCAL, SHAPE)
        t = MB.as_text(b)
        self.assertIn('the shelf shows', t)
        self.assertIn('eggs (28d)', t)
        self.assertIn('fri 2026-11-06  pizza', t)


if __name__ == '__main__':
    unittest.main()
