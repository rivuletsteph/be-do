# -*- coding: utf-8 -*-
"""A made-up time is not a deadline (12 Nov 2026, her words: the made up times,
that's uncool). That morning 13 of 17 rows past their date carried a date be•do
had written as its own placeholder. The entry check refuses one at the write.

    python3 core/tests/test_no_made_up_targets.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_entry as E  # noqa: E402

PLAN = E.FACTS['status']['plans'][-1]
DONE = E.FACTS['status']['actions'][3]
D = E.DIVIDER


def row(block, **kw):
    r = {'status': PLAN, 'practice': E.ACTION, 'title': '⚡ call about the bill', 'key': '261111_0900',
         'target': '2026-11-11T18:00:00.000Z', 'details': f'I need to call about the bill.\n{D}\n[be•do] {block}'}
    r.update(kw)
    return r


class NoMadeUpTargets(unittest.TestCase):
    def test_a_date_be_do_made_up_is_refused(self):
        for block in ("Target Wed 11 Nov, the money day (be•do's placeholder, hers to move).",
                      "Target noon tomorrow is be•do's placeholder.",
                      "A few minutes; the target is the outside date, be•do's placeholder, hers to move earlier.",
                      'Target Mon 30 Nov (the date a placeholder for in November).'):
            p = E.target_problems(row(block))
            self.assertEqual(len(p), 1, block)
            self.assertIn('made-up time is not a deadline', p[0])

    def test_a_real_date_with_a_filled_in_clock_time_passes(self):
        for block in ('Target Black Friday, Fri 27 Nov, her words; noon is a placeholder.',
                      'Target Tue 10 Nov afternoon, her word; 2 PM is a placeholder.',
                      "Retargeted to Fri 13 Nov at her word; target time: noon is be•do's placeholder.",
                      'Target put back to the deadline in the mail, Sun 15 Nov (9 AM a placeholder).'):
            self.assertEqual(E.target_problems(row(block)), [], block)

    def test_her_date_an_event_and_a_notice_pass(self):
        for block in ('Target Fri 13 Nov, her word.', 'Target is the event on her calendar.',
                      'Target from the notice: renew by 30 Nov.', 'Filed under Finances.'):
            self.assertEqual(E.target_problems(row(block)), [])

    def test_only_the_last_word_on_the_target_counts(self):
        moved = ("Target Wed 11 Nov, the money day (be•do's placeholder, hers to move). "
                 "[be•do] 12 Nov: retargeted to Fri 13 Nov at her word.")
        self.assertEqual(E.target_problems(row(moved)), [])
        kept = 'No new dates yet, so the target and the ❔ placeholder stay until she names them. Target Sun 13 Dec.'
        self.assertEqual(E.target_problems(row(kept)), [])

    def test_no_target_and_a_closed_row_are_left_alone(self):
        made_up = "Target noon tomorrow is be•do's placeholder."
        self.assertEqual(E.target_problems(row(made_up, target=None)), [])
        self.assertEqual(E.target_problems(row(made_up, status=DONE)), [])

    def test_the_whole_check_carries_it(self):
        p = E.problems(row("Target noon tomorrow is be•do's placeholder."))
        self.assertTrue(any('made-up time' in x for x in p))


if __name__ == '__main__':
    unittest.main(verbosity=1)
