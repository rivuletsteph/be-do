# -*- coding: utf-8 -*-
"""How things flow (29 Oct 2026): base flow's parts, read the same way every morning.

Balance is how evenly the wheel's elements shared the day; a drive's goal is her words
above the divider, first sentence; buffer counts the open steps already past their date
that morning — tending heavier than growing — and sets aside what the page sets aside.

Every name below is an obvious invention.

    python3 tests/test_flow.py
"""
import datetime as dt, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import flow  # noqa: E402

F = dict(title='t', target='tg', status='st', end='en', rhythm='rh', queue='q', waiting='w',
         quickie='qk', event='ev', when='wh', practice='pr')
local = lambda ts: dt.datetime.fromisoformat(ts.replace('Z', '+00:00')).date()
n = [0]


def row(rhythm, target, status='⬜ intention', created='2026-03-01T09:00:00Z', end=None, **extra):
    n[0] += 1
    c = dict(rh=rhythm, tg=target, st=status, en=end, **extra)
    return dict(id=f'rec{n[0]:05d}', createdTime=created, cellValuesByFieldId={k: v for k, v in c.items() if v})


def main():
    assert flow.evenness({k: 10 for k in 'abcdefgh'}) == 100
    assert flow.evenness({'a': 10, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'f': 0, 'g': 0, 'h': 0}) == 0
    assert flow.evenness({k: 0 for k in 'abcdefgh'}) is None
    assert flow.first_sentence('Build the thing for the class, a real exercise not a lecture. Then more.\n———\n[be•do] note') \
        == 'Build the thing for the class, a real exercise not a lecture.'
    assert flow.first_sentence('') == ''

    rows = [
        row('Rhythm One', '2026-03-03T15:00:00Z'),                                   # tending, late on the 4th
        row('Drive A', '2026-03-02T15:00:00Z'),                                      # growing, late
        row('Drive A', '2026-03-02T15:00:00Z', status='✅ done', end='2026-03-05T10:00:00Z'),  # closed later: late on the 4th
        row('Drive A', '2026-03-02T15:00:00Z', status='✅ done', end='2026-03-03T10:00:00Z'),  # closed before: not late
        row('Drive A', '2026-03-04T15:00:00Z'),                                      # due that day: not late yet
        row('Drive A', '2026-03-02T15:00:00Z', q=True),                              # queued: set aside
        row('Drive A', '2026-03-02T15:00:00Z', qk=True),                             # a quickie: set aside
        row('Drive A', '2026-03-02T15:00:00Z', ev='https://example.invalid/event'),  # an event's own row
        row('Build Work', '2026-03-02T15:00:00Z'),                                   # a hidden drive
        row('Drive A', '2026-03-02T15:00:00Z', created='2026-03-05T09:00:00Z'),     # not yet made that morning
    ]
    b = flow.buffer_on(dt.date(2026, 3, 4), rows, F, {'Rhythm One'}, {'Build Work'}, local)
    assert (b['tend'], b['grow']) == (1, 2), b
    assert b['value'] == round(100 - 6 * (1.5 * 1 + 2)), b
    assert flow.buffer_on(dt.date(2026, 3, 1), rows, F, {'Rhythm One'}, {'Build Work'}, local)['value'] == 100
    print('ok — balance is evenness, a goal is her first sentence, buffer counts what is late that morning')


if __name__ == '__main__':
    main()
