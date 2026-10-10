# -*- coding: utf-8 -*-
"""The child's intention (10 Oct 2026, her words: make this a Johnny's intention
section). A row dated today on the child, titled "<child>'s goal — …", is the
child's own intention: its own section, never one of the three or a task.

Every name below is an obvious invention.

    python3 tests/test_kid.py
"""
import os, sys, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import day_ahead as da  # noqa: E402


def row(i, title, target, status='⬜ intention', person='🐢Pip'):
    return dict(id=i, title=title, target=target, status=status, person=person,
                created='2026-10-10T14:0%s:00.000Z' % i[-1])


def main():
    L = dict(child_calendar='Pip', calendar_people={'Pip': '🐢Pip'})
    today = dt.date(2026, 10, 10)
    noon = '2026-10-10T17:00:00.000Z'
    rows = [row('r1', "Pip's goal — build a raft", noon),
            row('r2', "Pip's goal — feed the turtle", noon, status='✅ done'),
            row('r3', "Pip's goal — yesterday's kite", '2026-10-09T17:00:00.000Z'),
            row('r4', "Pip's goal — dropped one", noon, status='✖️ dropped'),
            row('r5', "Pip's goal — on someone else", noon, person='🦊Fen'),
            row('r6', 'Pack the car', noon)]
    name, got = da.kid_intentions({r['id']: r for r in rows}, today, L)
    assert name == 'Pip', name
    assert [(k['text'], k['st'].strip()) for k in got] == [('build a raft', '⬜'), ('feed the turtle', '✅')], got
    # no child named in the settings: no section
    assert da.kid_intentions({r['id']: r for r in rows}, today, {})[1] == []
    print("ok — the child's goal today is their own intention; other days, drops and other people are not")


if __name__ == '__main__':
    main()
