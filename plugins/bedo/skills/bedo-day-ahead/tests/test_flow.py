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

    # balance from the stream, when no day behind carries the wheel (30 Oct 2026)
    W = dict(F, wellness='wl')
    zero = dt.timedelta(0)
    day_rows = [row('R', None, status='● log', end='2026-03-04T10:00:00Z', wh='2026-03-04T09:00:00Z', wl='🤸‍♀️ body'),
                row('R', None, status='● log', wh='2026-03-04T11:00:00Z', wl='🧠 mind'),           # a moment weighs one
                row('R', None, status='⬜ intention', wh='2026-03-04T12:00:00Z', wl='🔥 fire'),    # a plan: not lived
                row('R', None, status='● log', end='2026-03-04T08:00:00Z', wh='2026-03-04T00:00:00Z',
                    wl='🤸‍♀️ body', pr='😴 sleep'),                                                  # sleep scores nothing
                row('R', None, status='● log', wh='2026-03-05T09:00:00Z', wl='🌊 water')]          # another day
    d = flow.wheel_of(dt.date(2026, 3, 4), day_rows, W, zero)
    assert (d['body'], d['mind'], d['fire'], d['water']) == (10.0, 1.0, 0.0, 0.0), d
    assert flow.wheel_of(dt.date(2026, 3, 4), day_rows, F, zero) is None                       # no wellness field

    # how much the day holds: her own timed events today, plus the travel buffer for one at a place
    day = dict(date='2026-03-04', events=[
        dict(who='you', when='10:30a', end='11:30a', sort='2026-03-04T10:30:00', where=''),
        dict(who='you', when='3p', end='4:30p', sort='2026-03-04T15:00:00', where='The Library'),
        dict(who='Kid', when='9a', end='3p', sort='2026-03-04T09:00:00', where=''),        # someone else's
        dict(who='you', when='', end='', sort='2026-03-04T00:00:00', where=''),            # all day
        dict(who='you', when='ends 9a', end='9a', sort='2026-03-03T20:00:00', where=''),   # carried in
    ])
    h = flow.day_holds(day, dict(travel_buffer_min=30, full_day_hours=4))
    assert (h['events'], h['booked'], h['travel'], h['free'], h['full']) == (2, 2.5, 0.5, 5.0, False), h
    assert flow.day_holds(day, dict(step_day_hours=2))['free'] == 0
    assert flow.clock(dt.date(2026, 3, 4), '12p').hour == 12 and flow.clock(dt.date(2026, 3, 4), '12:15a').hour == 0
    # a step's size, guessed off its words
    assert flow.size_guess('Call the plumber about the leak') == 15
    assert flow.size_guess('Draft the methods chapter') == 240
    assert flow.size_guess('Walk the dog') == 60
    print('ok — balance is evenness, a goal is her first sentence, buffer counts what is late that morning, '
          'the day holds her free hours, a size is a guess off the words')


if __name__ == '__main__':
    main()
