# -*- coding: utf-8 -*-
"""How the time went counts only her own events (20 Nov 2026).

A done event on her son's calendar, a two-day stay at his grandparents', was
counted as her minutes, and it split her night in half: sleep read 2 h 32
asleep. Another calendar's event stays on the page, but off her pie.

    python3 tests/test_pie_her_events.py
"""
import os, re

HERE = os.path.dirname(os.path.abspath(__file__))


def test_spent_skips_other_calendars():
    page = open(os.path.join(os.path.dirname(HERE), 'assets', 'flow_engine.html'), encoding='utf-8').read()
    body = page[page.index('function spent(){'):]
    body = body[:body.index('\nfunction ', 1)]
    head = body[:body.index('if(!iv.length)')]
    assert "if(x.k==='event'&&x.who&&x.who!=='you') return;" in head


def main():
    test_spent_skips_other_calendars()
    print('ok — her pie counts only her own events')


if __name__ == '__main__':
    main()
