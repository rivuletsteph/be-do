# -*- coding: utf-8 -*-
"""A renamed calendar is read by its id (24 Nov 2026, her words: I don't know
why that's a recurring issue. I want everything to be live). The settings
keep each calendar's id under the name it had; when Google's list no longer
holds that name, the id finds the calendar under its new one and one line
says to update the settings. Only an id that is gone stops the read.

    python3 core/tests/test_calendar_renamed.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_reader as R  # noqa: E402

LOCAL = {'calendar': {'calendars': {'Old name': 'id-1', 'Gone': 'id-9'}}}
LIVE = {'New name': 'id-1', 'Other': 'id-2'}


class Renamed(unittest.TestCase):
    def test_a_name_in_the_list_is_itself(self):
        self.assertEqual(R.live_calendar('Other', LIVE, LOCAL), ('Other', None))

    def test_a_renamed_calendar_is_found_by_its_id(self):
        now, note = R.live_calendar('Old name', LIVE, LOCAL)
        self.assertEqual(now, 'New name')
        self.assertIn('"Old name" is now "New name"', note)

    def test_an_id_that_is_gone_is_not_guessed(self):
        self.assertEqual(R.live_calendar('Gone', LIVE, LOCAL), (None, None))
        self.assertEqual(R.live_calendar('Never known', LIVE, LOCAL), (None, None))


if __name__ == '__main__':
    unittest.main()
