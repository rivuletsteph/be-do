# -*- coding: utf-8 -*-
"""A branch or a drive chat is never a window, whatever its words say (21 Nov 2026).

Closing the Friday branch "↳1120.1 … 👁️ my day page" was refused ☑️ ("a window chat
wants ✔️") because "my day" is in its title; on 9 Nov the drive chat that built the my
week page (code D6.79) was told the same. The branch marker and the drive code decide.

    python3 core/tests/test_close_window_words.py
"""
import os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_close as C  # noqa: E402


class WindowWords(unittest.TestCase):
    def test_a_branch_with_my_day_in_it_is_a_branch(self):
        self.assertFalse(C.is_window('▶️↳1120.1 🏆 Fri 👁️ my day page'))
        self.assertEqual(C.wanted_glyphs('▶️↳1120.1 🏆 Fri 👁️ my day page', C.DONE), [C.GLYPH['done']])

    def test_a_drive_chat_with_my_week_in_it_is_a_drive_chat(self):
        self.assertFalse(C.is_window('▶️𖡎 My week page · be•do D6.79'))

    def test_the_windows_are_still_windows(self):
        self.assertTrue(C.is_window('▶️🔆1120 🏆 Fri 𖡎 W47 my day'))
        self.assertTrue(C.is_window('▶️𖡎 W47 my week'))


if __name__ == '__main__':
    unittest.main()
