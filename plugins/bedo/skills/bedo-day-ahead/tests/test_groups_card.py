# -*- coding: utf-8 -*-
"""Could go together, on the my day page (24 Nov 2026, her words: keep track of
these open intentions and potential actions and proactively scan how these
things can be grouped). The page runs the core's groups check on the rows it
already read, so it runs every look ahead with no one asking, and the engine
draws it at the bottom of the page (26 Nov 2026), never on a finished day.

Every name below is an obvious invention.

    python3 tests/test_groups_card.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import flow  # noqa: E402

F = dict(title='t', status='st', rhythm='rh', person='pe', details='de', when='wh', key='k', practice='pr')
L = dict(self_person='♋ Robin', calendar_people={'Sam': '♑Sam'}, hide_drives=['Sysdrive'])


def rec(rid, title, status='⬜ intention', drive='Home', person=None):
    c = dict(t=title, st={'name': status}, rh=drive, pe=person, pr={'name': '⚡ action'}, k=rid)
    return dict(id=rid, createdTime='2026-03-01T09:00:00Z', cellValuesByFieldId={k: v for k, v in c.items() if v})


ROWS = [rec('r1', '⚡ Call the clinic'), rec('r2', '⚡ Text Quill Barrow back', drive='Pals'),
        rec('r3', '⚡ Call the plumber', drive='Sysdrive'),                      # a hidden drive is set aside
        rec('r4', '⚡ Ask Sam about the trip', person='♋ Robin, ♑Sam'),
        rec('r5', '⚡ Old call', status='✅ done')]


class Card(unittest.TestCase):
    def test_the_page_carries_the_groups(self):
        g = flow.groups_of(ROWS, F, L)
        self.assertEqual(g['read'], 3)
        calls = next(x for x in g['lenses']['sitting'] if x['name'] == 'calls and texts')
        self.assertEqual(sorted(r['id'] for r in calls['rows']), ['r1', 'r2', 'r4'])
        self.assertEqual(g['lenses']['person'], [])     # the household is never a group

    def test_the_engine_draws_it_and_not_on_a_finished_day(self):
        h = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()
        self.assertIn('<section class="three" id="three"></section>\n<section class="sat grp" id="grp"></section>', h)
        self.assertIn('groupsCard();', h[h.index('function draw()'):])
        self.assertIn("grpEl.hidden=over", h)


if __name__ == '__main__':
    unittest.main()
