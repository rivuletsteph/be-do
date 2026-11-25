# -*- coding: utf-8 -*-
"""Her open actions read together (24 Nov 2026, her words: keep track of these
open intentions and potential actions and proactively scan how these things
can be grouped), and asks by email that never reached the stream.

    python3 core/tests/test_groups.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_groups as G  # noqa: E402

ME, KID = '♋ Robin', '♑Sam'


def row(rid, title, status='⬜ intention', drive='Home', person=None, details='', key=None, at='2026-03-13T15:00:00Z'):
    return dict(id=rid, title=title, status=status, rhythm=drive, person=person, details=details, key=key or rid,
                datetime=at, practice='⚡ action')


ROWS = [
    row('r1', '⚡ Call the dentist about the crown', drive='Health'),
    row('r2', '⚡ Text Quill about Saturday', drive='Pals', person=f'{ME}, Quill Barrow'),
    row('r3', '⚡ Email the grant officer the budget', drive='Work'),
    row('r4', '⚡ Send Quill the photos', drive='Pals', person=f'{ME} · Quill Barrow'),
    row('r5', '⚡ Look at swim classes in Riverton', status='▫️potential', drive='School', person=KID),
    row('r6', '⚡ Pick up the frame in Riverton', drive='Home'),
    row('r7', '⚡ Fix the gate at Oak Hall', drive='Home'),
    row('r8', '⚡ Pay the water bill', drive='Home'),
    row('r9', '⚡ Old call, done', status='✅ done', drive='Home'),
    row('r10', '⚡ The page shows the wrong hour', drive='Home', details='———\nfor code: fix it\ndone when: right'),
    row('r11', '⚡ Call the dentist about the crown', drive='Health', key='r1'),   # last week's copy of r1
    row('r12', '⚡ Ask Sam to tidy his room at Oak Hall', drive='Home', person=KID),
    row('r13', '⚡ Sam visits Sam\'s friends', drive='School', person=KID),
]


def lens(g, name):
    return {x['name']: [r['id'] for r in x['rows']] for x in g['lenses'][name]}


class Groups(unittest.TestCase):
    def setUp(self):
        self.g = G.groups(ROWS, [ME, KID])

    def test_only_open_action_rows_once_each_and_no_asks(self):
        # a closed row, Duet's ask for Code and last week's copy of a row are not read
        self.assertEqual(self.g['read'], 10)

    def test_one_sitting_reads_the_kind_of_doing(self):
        s = lens(self.g, 'sitting')
        self.assertEqual(sorted(s['calls and texts']), ['r1', 'r12', 'r2'])
        self.assertEqual(sorted(s['email and posts']), ['r3', 'r4'])

    def test_a_person_other_than_the_household(self):
        p = lens(self.g, 'person')
        self.assertEqual(sorted(p['Quill Barrow']), ['r2', 'r4'])
        self.assertNotIn('Robin', p)
        self.assertNotIn('Sam', p)       # the household is with her by default

    def test_one_place_from_the_titles(self):
        p = lens(self.g, 'place')
        self.assertEqual(sorted(p['Riverton']), ['r5', 'r6'])
        self.assertEqual(sorted(p['Oak Hall']), ['r12', 'r7'])
        self.assertFalse(any("'s" in k for k in p))

    def test_a_drive_with_two_waiting_steps(self):
        d = lens(self.g, 'drive')
        self.assertIn('Home', d)
        self.assertNotIn('School', d)    # a maybe is not a waiting step

    def test_meant_comes_before_maybe(self):
        x = next(x for x in self.g['lenses']['place'] if x['name'] == 'Riverton')
        self.assertEqual([r['id'] for r in x['rows']], ['r6', 'r5'])
        self.assertEqual((x['n'], x['intent']), (2, 1))

    def test_a_single_row_is_not_a_group(self):
        self.assertNotIn('bookings and sign-ups', lens(self.g, 'sitting'))

    def test_the_report_says_nothing_is_written(self):
        self.assertIn('offers only, nothing written', G.report(self.g)[0])


MAIL = [
    dict(id='t1', viewUrl='https://mail.example.com/t1', messages=[dict(sender='Ottoline Fenwick <someone@example.org>',
         subject='Can you post the progress note on the channel?', snippet='Could you post it by Friday?')]),
    dict(id='t2', messages=[dict(sender='noreply@example.com', subject='Your weekly digest?', snippet='please read')]),
    dict(id='t3', messages=[dict(sender='Quill Barrow <user@example.com>', subject='Photos from Saturday',
         snippet='can you send the photos?')]),
    dict(id='t4', messages=[dict(sender='Zeb Quorn <test@example.org>', subject='Lunch notes', snippet='Thanks, all good.')]),
]


class Mail(unittest.TestCase):
    def test_an_ask_with_no_row_is_named_and_marked_work(self):
        got = G.unlanded(MAIL, ROWS, work=['example.org'])
        self.assertEqual([m['thread'] for m in got], ['t1'])
        self.assertTrue(got[0]['work'])
        self.assertEqual(got[0]['sender'], 'Ottoline Fenwick')

    def test_a_list_and_a_note_with_no_ask_are_not_flagged(self):
        ids = [m['thread'] for m in G.unlanded(MAIL, ROWS)]
        self.assertNotIn('t2', ids)
        self.assertNotIn('t4', ids)

    def test_an_ask_already_on_the_stream_is_not_flagged(self):
        # "Send Quill the photos" is a row: Quill's ask has landed
        self.assertNotIn('t3', [m['thread'] for m in G.unlanded(MAIL, ROWS)])

    def test_the_report_puts_them_on_her_list(self):
        text = '\n'.join(G.report(self.g if hasattr(self, 'g') else G.groups(ROWS), G.unlanded(MAIL, ROWS)))
        self.assertIn('only on her yes', text)
        self.assertIn('https://mail.example.com/t1', text)


if __name__ == '__main__':
    unittest.main()
