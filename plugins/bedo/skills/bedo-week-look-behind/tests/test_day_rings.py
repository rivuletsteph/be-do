# -*- coding: utf-8 -*-
"""How the day went (the rainbow), over an invented day.

Checks the rules settled on 24 Oct 2026 (docs/day-behind-cards.md): the night
before and the waking day; sitting to eat is not moving; drinks are food; a
session that ran while she drove isn't her work; caring for herself and for the
people in `care` is caretaking; a show is recreation and a screen; a flow step
logged while asleep is not a flow; the moments keep their times.

Every name below is an obvious invention. Times are UTC; the day is UTC-5.

    python3 tests/test_day_rings.py
"""
import datetime as dt, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'core'))
from day_rings import day_rings  # noqa: E402

L = {'utc_offset_hours': -5, 'care': {'rhythms': ['Kid Club'], 'people': ['Pip']}, 'system_rhythm': 'the system',
     'recreation': {'rhythms': ['Play Days']}, 'day_goals': {'inbed': 450, 'move': 120}}
DAY = dt.date(2026, 3, 4)


def row(p, a, b=None, **kw):
    """a and b are local 'HH:MM' on DAY ('-HH:MM' the evening before, '+HH:MM' the morning after)."""
    def utc(x):
        shift = {'-': -1, '+': 1}.get(x[0], 0)
        h, m = map(int, x.lstrip('-+').split(':'))
        t = dt.datetime.combine(DAY + dt.timedelta(days=shift), dt.time(h, m)) + dt.timedelta(hours=5)
        return t.strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return dict(practice=p, title=kw.pop('title', p), when=utc(a), end=utc(b) if b else None, status=kw.pop('status', '✅ done'), **kw)


ROWS = [
    row('😴 sleep', '-23:00', '07:30'),                                  # the night before: 8 h 30 in bed
    row('☕ coffee', '07:45'),                                             # a drink is food, a five-minute tick
    row('📿 morning mantra', '08:00'),                                    # a flow step
    row('⚡ action', '09:00', '10:00', rhythm='Paid Work', device='💻 laptop', title='the report'),
    row('🚗 driving', '09:30', '10:00', title='to the shop'),             # the session ran while she drove
    row('🚶‍♀️ walking', '11:00', '12:00'),
    row('🍽️ lunch', '11:30', '11:45'),                                    # sitting to eat is not moving
    row('✨ glimmer', '14:00', title='the heron'),                         # a moment, no length
    row('⭐ highlight', '14:30', title='the heron again'),                 # a flow step placed at its moment
    row('📝 log', '16:00', '17:00', rhythm='Play Days', title='the trampoline park with Pip'),   # recreation and care
    row('🚗 driving', '15:00', '15:30', person=['Pip Plum'], title='school run'),
    row('📺 show', '20:00', '20:30', device='📺 tv', title='a mystery'),
    row('🚿 shower', '21:00', '21:20'),                                    # caring for herself
    row('🌄 dusk flow close', '23:30'),                                    # logged asleep: not a flow
    row('😴 sleep', '23:00', '+07:00'),                                     # tonight
    row('⚡ action', '13:00', '14:00', rhythm='Paid Work', status='⬜ intention'),   # never happened
]

R = day_rings(ROWS, DAY, L, flows={'morning mantra', 'highlight'}, not_lived={'⬜ intention'})
B = {b['k']: b for b in R['bands']}
K = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in R['bands']}

assert R['goals'] == {'inbed': 450, 'move': 120} and R['ideal_bed'] == 450, R['goals']   # the night is measured against her own goal
assert R['wake'] == 7 * 60 + 30 and R['bed'] == 23 * 60 and R['inbed'] == 510, (R['wake'], R['bed'], R['inbed'])
assert K['being']['eat'] == 5 + 15, K['being']                       # coffee tick + lunch
assert K['being']['move'] == 60 - 15, K['being']                     # the walk less the meal
assert K['being']['recreation'] == 30 + 60, K['being']              # the show and the trampoline park
assert K['doing']['work'] == 30, K['doing']                          # 9:00-9:30 only; the drive took the rest
assert K['doing']['care'] == 30 + 20 + 60, K['doing']                # the school run, the shower, the trampoline park
assert B['screen']['total'] == 60 + 30, B['screen']                  # the laptop hour and the show
assert 'dusk' not in R['win'] and R['win']['dawn'] == [480, 485], R['win']
assert [(m['m'], m['p']) for m in R['moments']] == [(14 * 60, 'glimmer'), (14 * 60 + 30, 'highlight')], R['moments']
care = next(r for r in B['doing']['runs'] if r[0] == 'care' and r[1] == 15 * 60)
assert care[3] == ['school run'], care                               # a tap names what the chunk was
# A session that ran 6:00 to 7:30 with her away in between: the row names her
# stretches, and only those are her work and her screen (261024a, 25 Oct 2026).
NIGHT = [row('😴 sleep', '-23:00', '07:30')]
gap = row('⚡ action', '18:00', rhythm='the system', device='💻 laptop', title='the cards', spent=25 * 60,
          details='what I did\n· moved the cards\n———\n[be•do] stretches: 6:00–6:10 · 7:15–7:30 = 25m')
R2 = day_rings(NIGHT + [gap], DAY, L)
B2 = {b['k']: b for b in R2['bands']}
runs = [(r[1], r[2]) for r in B2['doing']['runs']]
assert runs == [(18 * 60, 18 * 60 + 10), (19 * 60 + 15, 19 * 60 + 30)], runs
assert B2['screen']['total'] == 25, B2['screen']
# the same row without the line falls back to its time spent from the start, as before
old = dict(gap, details='what I did\n· moved the cards')
assert [(r[1], r[2]) for r in {b['k']: b for b in day_rings(NIGHT + [old], DAY, L)['bands']}['doing']['runs']] == \
    [(18 * 60, 18 * 60 + 25)]
print('ok — the night, food and moving, her work not the laptop\'s, her stretches not the envelope, caretaking, '
      'recreation, screens, flows and moments')
