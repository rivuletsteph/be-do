# -*- coding: utf-8 -*-
"""His quest page joins the morning (4 Nov 2026): preflight hands her its link beside the look behind.

    python3 plugins/bedo/core/tests/test_quest_morning.py
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bedo_preflight as P  # noqa: E402

assert P.quest_line({}) is None
line = P.quest_line({'quest_url': 'https://claude.ai/artifact/QUEST'})
assert line.startswith("quest  his quest page · https://claude.ai/artifact/QUEST"), line
assert "once he's rested" in line
print('ok — the morning opens on his quest page too, when the settings name it')
