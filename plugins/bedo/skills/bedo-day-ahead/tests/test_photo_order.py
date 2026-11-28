# -*- coding: utf-8 -*-
"""Her own photo order wins on a card, and a moment's photo sits above her words (27 Nov 2026, her words: the picture I
took at the end right before everybody left was the best picture of the gathering).

    python3 tests/test_photo_order.py
"""
import os, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ENGINE = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()
FLOW = open(os.path.join(HERE, '..', 'scripts', 'flow.py'), encoding='utf-8').read()


class Order(unittest.TestCase):
    def test_the_first_linked_photo_is_the_cards(self):
        self.assertIn("key=lambda p: (not p.get('linked'), first(p), p['t'])", FLOW)
        self.assertIn("bedo_photos.linked(p['row']).index(p['file'])", FLOW)

    def test_a_moments_photo_comes_before_her_words(self):
        body = ENGINE[ENGINE.index('const momBody='):]
        body = body[:body.index('};')]
        self.assertLess(body.index('class="mph"'), body.index('class="mw"'))


if __name__ == '__main__':
    unittest.main()
