# -*- coding: utf-8 -*-
"""Meals get minutes without her logging them (7 Oct 2026). Every row is
invented; the shapes are the base's.

    python3 plugins/bedo/core/tests/test_meals.py
"""
import os, sys, unittest

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_meals as ML  # noqa: E402

OFF = -5          # CDT
PEOPLE = ('♋ Self', '♑Kid', '♐Partner')


def row(rid, practice, start, end=None, title=None, status='◉ done', details=None):
    return {'id': rid, 'practice': practice, 'datetime': start, 'end': end,
            'title': title or practice, 'status': status, 'details': details}


class Meals(unittest.TestCase):

    def one(self, rows):
        props = ML.propose(rows, OFF, PEOPLE)
        self.assertEqual(len(props), 1, props)
        return props[0]

    def test_a_dinner_logged_as_a_moment_was_cooked_and_eaten(self):
        # the 6 Oct case: a homemade dinner, one moment, no cooking row
        p = self.one([row('r1', '🍴 dinner', '2026-10-06T22:15:00.000Z', title='🍴 Cholula tacos at home')])
        self.assertEqual(p['prep']['class'], 'cooked')
        self.assertEqual(p['prep']['practice'], '🍳 dinner prep')
        self.assertEqual((p['prep']['datetime'], p['prep']['end']),
                         ('2026-10-06T21:30:00.000Z', '2026-10-06T22:15:00.000Z'))
        self.assertEqual(p['eat']['end'], '2026-10-06T22:45:00.000Z')
        self.assertIn('ESTIMATED FROM CONTEXT', p['prep']['details'])

    def test_ordering_out_is_food_prep(self):
        # her word: twenty minutes to order it at McAlister's counts as prep
        p = self.one([row('r1', '🍴 lunch', '2026-10-06T17:11:00.000Z',
                          title="🍴 McAlister's veggie sandwich with turkey, at the ditch")])
        self.assertEqual(p['prep']['class'], 'out')
        self.assertEqual(p['prep']['datetime'], '2026-10-06T16:51:00.000Z')
        self.assertEqual(p['eat']['end'], '2026-10-06T17:31:00.000Z')
        self.assertIn('Timeline', p['line'])

    def test_a_persons_possessive_is_not_a_restaurant(self):
        p = self.one([row('r1', '🍽️ lunch', '2026-10-06T17:00:00.000Z', title="Kid's lunch — a PB&J")])
        self.assertEqual(p['prep']['class'], 'simple')
        self.assertEqual(p['prep']['datetime'], '2026-10-06T16:45:00.000Z')

    def test_a_straightforward_dinner_is_thirty(self):
        p = self.one([row('r1', '🍽️ dinner', '2026-10-06T23:00:00.000Z', title='🍽️ Quick pasta')])
        self.assertEqual(p['prep']['class'], 'straightforward')
        self.assertEqual(p['prep']['datetime'], '2026-10-06T22:30:00.000Z')

    def test_a_meal_already_placed_is_left_alone(self):
        rows = [row('p1', '🍳 dinner prep', '2026-10-06T21:30:00.000Z', '2026-10-06T22:15:00.000Z'),
                row('r1', '🍴 dinner', '2026-10-06T22:15:00.000Z', '2026-10-06T22:45:00.000Z')]
        self.assertEqual(ML.propose(rows, OFF, PEOPLE), [])

    def test_a_timed_meal_still_gets_its_prep(self):
        p = self.one([row('r1', '🍴 dinner', '2026-10-06T22:15:00.000Z', '2026-10-06T22:45:00.000Z')])
        self.assertIsNone(p['eat'])
        self.assertIsNotNone(p['prep'])

    def test_a_second_sitting_of_the_same_meal_is_not_made_again(self):
        rows = [row('r1', '🍴 lunch', '2026-10-06T17:11:00.000Z', '2026-10-06T17:31:00.000Z',
                    title="🍴 McAlister's sandwich, half saved"),
                row('r2', '🍴 lunch', '2026-10-06T17:50:00.000Z', '2026-10-06T18:10:00.000Z',
                    title='🍴 The other half, outside with Partner')]
        props = ML.propose(rows, OFF, PEOPLE)
        self.assertEqual([p['id'] for p in props], ['r1'])

    def test_a_snack_has_no_prep(self):
        p = self.one([row('r1', '🤏🏻 snack', '2026-10-06T20:00:00.000Z')])
        self.assertIsNone(p['prep'])
        self.assertEqual(p['eat']['end'], '2026-10-06T20:10:00.000Z')

    def test_a_planned_meal_is_not_a_meal_yet(self):
        self.assertEqual(ML.propose([row('r1', '🍴 dinner', '2026-10-06T23:00:00.000Z',
                                         status='⬜ intention')], OFF, PEOPLE), [])

    def test_she_is_shown_what_went_in_the_record(self):
        props = ML.propose([row('r1', '🍴 dinner', '2026-10-06T22:15:00.000Z', title='🍴 Tacos at home')],
                           OFF, PEOPLE)
        out = ML.render(props, 'meals')
        self.assertIn("tell me if it's not right", out)
        self.assertIn('4:30–5:15', out)
        self.assertIn('ate 5:15–5:45', out)


if __name__ == '__main__':
    unittest.main(verbosity=1)
