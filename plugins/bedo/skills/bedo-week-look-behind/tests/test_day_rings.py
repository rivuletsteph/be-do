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

L = {'utc_offset_hours': -5, 'care': {'rhythms': ['Kid Club'], 'people': ['Pip'], 'together': ['the kids']}, 'system_rhythm': 'the system',
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
    row('😴 sleep', '-23:00', '07:30', details='———\n[be•do] From her Oura: 7 h 52 min asleep, efficiency 93%'),   # 8 h 30 in bed
    row('☕ coffee', '07:45'),                                             # a drink is food, a five-minute tick
    row('📿 morning mantra', '08:00'),                                    # a flow step
    row('⚡ action', '09:00', '10:00', rhythm='Paid Work', device='💻 laptop', title='the report'),
    row('🚗 driving', '09:30', '10:00', title='to the shop'),             # the session ran while she drove
    row('📝 log', '12:10', '12:30', rhythm='the system', title='a voice note on the drive'),   # her own, at the wheel
    row('🚗 driving', '12:10', '12:40', title='to the trailhead'),
    row('🚶‍♀️ walking', '11:00', '12:00'),
    row('🍽️ lunch', '11:30', '11:45'),                                    # sitting to eat is not moving
    row('✨ glimmer', '14:00', title='the heron'),                         # a moment, no length
    row('⭐ highlight', '14:30', title='the heron again'),                 # a flow step placed at its moment
    row('📝 log', '16:00', '17:00', rhythm='Play Days', person=['Pip Plum'], title='the trampoline park with Pip'),   # recreation and care
    row('🚗 driving', '15:00', '15:30', person=['Pip Plum'], title='school run'),
    row('📺 show', '20:00', '20:30', device='📺 tv', title='a mystery'),
    row('🚿 shower', '21:00', '21:20'),                                    # caring for herself
    row('✈️ flight', '18:00', '19:00', title='home from Denver'),          # carried: travel, being
    row('🌄 dusk flow close', '23:30'),                                    # logged asleep: not a flow
    row('😴 sleep', '23:00', '+07:00'),                                     # tonight
    row('⚡ action', '13:00', '14:00', rhythm='Paid Work', status='⬜ intention'),   # never happened
]

R = day_rings(ROWS, DAY, L, flows={'morning mantra', 'highlight'}, not_lived={'⬜ intention'})
B = {b['k']: b for b in R['bands']}
K = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in R['bands']}

assert R['goals'] == {'inbed': 450, 'move': 120} and R['ideal_bed'] == 450, R['goals']   # the night is measured against her own goal
assert R['wake'] == 7 * 60 + 30 and R['bed'] == 23 * 60 and R['inbed'] == 510, (R['wake'], R['bed'], R['inbed'])
assert R['asleep'] == 472, R['asleep']                                   # asleep, from Oura's line, inside the hours in bed
assert K['being']['eat'] == 5 + 15, K['being']                       # coffee tick + lunch
assert K['being']['move'] == 60 - 15, K['being']                     # the walk less the meal
assert K['being']['recreation'] == 30 + 60, K['being']              # the show and the trampoline park
assert K['doing']['work'] == 30, K['doing']                          # 9:00-9:30 only; the drive took the rest
assert K['doing']['family'] == 30 + 60, K['doing']                    # the school run, the trampoline park
assert K['doing']['drive'] == 30 + 30 + 30, K['doing']                # at the wheel: the trailhead, the shop, the school run
assert K['doing']['system'] == 20, K['doing']                        # her voice note on the drive stays hers, beside the driving
assert K['being']['travel'] == 60, K['being']                         # on the plane: carried, not driving
assert K['being']['personal'] == 20, K['being']                       # the shower: personal care
assert B['screen']['total'] == 60 + 30, B['screen']                  # the laptop hour and the show
assert 'dusk' not in R['win'] and R['win']['dawn'] == [480, 485], R['win']
assert [(m['m'], m['p']) for m in R['moments']] == [(14 * 60, 'glimmer'), (14 * 60 + 30, 'highlight')], R['moments']
care = next(r for r in B['doing']['runs'] if r[0] == 'family' and r[1] == 15 * 60)
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

# An action is professional work only when it is: reading with Pip on a recreation rhythm is caretaking and
# recreation, a playmate's visit with Pip along is too, and a paid-work action stays work (27 Oct 2026).
MIX = NIGHT + [
    row('⚡ action', '09:00', '09:40', rhythm='Play Days', person=['Pip Plum'], title='finished the book with Pip'),
    row('⚡ action', '12:00', '14:00', rhythm='Play Days', person=['Moss Quill', 'Pip Plum'], title='Moss came to play'),
    row('⚡ action', '15:00', '16:00', rhythm='Play Days', title='booked the zipline'),
    row('⚡ action', '17:00', '18:00', rhythm='Paid Work', title='the report'),
    row('💦 weekly check', '20:00', '20:10', rhythm='Paid Work', title='the weekly check, posted'),   # a work practice
]
KM = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in day_rings(MIX, DAY, L)['bands']}
assert KM['doing'].get('family') == 40 + 120, KM['doing']
assert KM['being'].get('recreation') == 40 + 120 + 60, KM['being']
assert KM['doing'].get('work') == 60 + 10, KM['doing']                # the report and the weekly check
print('ok — reading and a visit with Pip are caretaking and recreation, not work; the report is still work')

# the night split at midnight, asleep from Oura's timeline (26 Oct 2026)
SLEEP = [dict(start='2026-%s-%sT23:00:00-05:00' % ((DAY - dt.timedelta(days=1)).strftime('%m'), (DAY - dt.timedelta(days=1)).strftime('%d')),
              end=DAY.isoformat() + 'T07:30:00-05:00', type='long_sleep', phases='4' * 12 + '2' * 90 + '4' * 0),
         dict(start=DAY.isoformat() + 'T23:30:00-05:00', end=(DAY + dt.timedelta(days=1)).isoformat() + 'T07:00:00-05:00',
              type='long_sleep', phases='4' * 6 + '2' * 84)]
ROWS2 = [r for r in ROWS] + [row('🌌 evening blessing', '23:10')]
R2 = day_rings(ROWS2, DAY, L, flows={'morning mantra', 'highlight', 'evening blessing'}, not_lived={'⬜ intention'}, sleep=SLEEP)
N = {(st, a): b for st, a, b in R2['night']}
assert R2['asleep_from'] == 'oura', R2['asleep_from']
assert N.get(('asleep', 0)) == 450, R2['night']                             # midnight to 7:30, asleep all the way (awake 23:00–24:00 was the day before)
assert N.get(('bed', 1380)) == 1440, R2['night']                              # tonight: in bed at 23:00, awake to midnight (Oura's fours)
assert R2['inbed_day'] == 450 + 60 and R2['asleep_day'] == 450, (R2['inbed_day'], R2['asleep_day'])
FB = {b['k']: b for b in R2['bands']}
assert FB['flow']['total'] >= B['flow']['total'], (FB['flow']['total'], B['flow']['total'])
print('ok — the night split at midnight: in bed from the rows, asleep from Oura, a bedtime step in bed still a flow')

# Caretaking is when her focus is on them (28 Oct 2026): a care task or something done with or for them is;
# being nearby while she does her own thing is not, and their own play is theirs.
FOCUS = NIGHT + [
    row('🍳 lunch prep', '11:00', '11:20', person=['Pip Plum'], title='cut apples for the kids'),     # a care task: cooking and care
    row('🍽️ lunch', '11:20', '11:50', person=['Pip Plum'], title='lunch outside'),                  # her lunch with Pip there
    row('⚡ action', '13:00', '14:00', rhythm='Paid Work', title='the report'),                     # working while Pip plays
    row('🎮 game', '13:00', '14:00', person=['Pip Plum'], title='Pip playing blocks'),               # Pip's own play
    row('🚶‍♀️ walking', '15:00', '15:30', person=['Pip Plum'], title='walked to the park with Pip'),  # her words: together
    row('📺 show', '18:00', '18:30', person=['Pip Plum'], title='a mystery with Pip'),              # the show: recreation only
    row('📺 show', '19:00', '19:20', person=['Pip Plum'], title="Pip's show, the dog cartoon"),     # his show: both
    row('📝 log', '16:00', '16:30', person=['Pip Plum'], title='a quiet hour',
        details='Pip and I built a fort.\n———\n[be•do] logged'),                                    # together, in her words
]
KF = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in day_rings(FOCUS, DAY, L)['bands']}
assert KF['doing'].get('family') == 20 + 30 + 30 + 20, KF['doing']     # and his show; not the mystery
assert not KF['doing'].get('cook'), KF['doing']                       # cutting apples is quick food, not making           # the apples, the walk, the fort; not lunch, not the game
assert KF['doing'].get('work') == 60, KF['doing']                     # the report stays work
assert KF['being'].get('recreation') == 30 + 20, KF['being']           # both shows; his game is his own
print('ok — caretaking is her focus on them: the apples, the walk, the fort, his show; not her lunch, the report, his game or a show together')

# Four kinds of care, named for what is cared for, and making (28 Oct 2026): quick food is care for whoever it
# fed, cooking she creates is making, and so are building and music.
L4 = dict(L, care={'family': {'rhythms': ['Kid Club'], 'people': ['Pip']}, 'pet': {'names': ['Biscuit']},
                   'home': {'rhythms': ['Hearth']}, 'personal': {'rhythms': ['My Health']}})
CARE4 = NIGHT + [
    row('🍳 lunch prep', '11:00', '11:10', title='a sandwich'),                                       # quick, for her: personal care
    row('🧽 dishes', '11:30', '11:50'),                                                               # home care
    row('🚶‍♀️ walking', '12:00', '12:30', title='walked Biscuit'),                                    # moving, and pet care
    row('⚡ action', '13:00', '13:30', rhythm='Hearth', title='called the plumber'),                  # home care
    row('⚡ action', '14:00', '14:40', rhythm='My Health', title='read my lab results'),              # personal care
    row('🍳 dinner prep', '17:00', '17:50', title='lasagna'),                                         # a routine dinner: family care (31 Oct)
    row('🍳 lunch prep', '16:00', '16:15', title='baked bread from a recipe'),                         # her words: making
    row('🪚 woodworking', '19:00', '20:00', title='a birdhouse'),                                     # making
    row('⚡ action', '15:00', '16:00', rhythm='Kid Club', person=['Pip Plum'], title="Pip's swim class"),  # his class
    row('🚶‍♀️ walking', '15:10', '15:50', title='walked Biscuit by the creek during his class'),        # her walk wins
]
K4 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in day_rings(CARE4, DAY, L4)['bands']}
assert K4['being'].get('personal') == 10 + 40, K4['being']
assert K4['doing'].get('home') == 20 + 30 and K4['doing'].get('pet') == 30 + 40, K4['doing']
assert K4['doing'].get('family') == 60 + 50, K4['doing']               # the class and the walk both count: two lanes; dinner prep is care (31 Oct)
assert K4['doing'].get('cook') == 15 + 60 and not K4['doing'].get('work'), K4['doing']   # making is creative, not long (31 Oct)
print('ok — personal, family, pet and home care, each for what it cares for; making is cooking she creates, and building')

# Dinner prep is care, never professional work (31 Oct 2026, her words: dinner prep is not professional work,
# that is a care task) — even when the row carries a rhythm, which used to paint it as work.
CARE5 = NIGHT + [row('🍳 dinner prep', '17:22', '17:52', rhythm='My Health', person=['Ollie Plum'], title='made the sides for dinner')]
K5 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in day_rings(CARE5, DAY, L4)['bands']}
assert not K5['doing'].get('work') and K5['doing'].get('family') == 30, K5['doing']
print('ok — dinner prep is care: never professional work, even on a rhythm')

# The kinds of care, settled with her 31 Oct 2026: the kitchen after a family meal is family care; caring for people
# beyond the family is community care; time with people beyond the family, like a party, is social recreation.
CARE6 = NIGHT + [
    row('🧽 clean', '19:10', '19:40', title='the dishes after dinner'),                                # family care
    row('🧽 clean', '10:00', '10:20', title='the bathroom'),                                          # still home care
    row('⚡ action', '16:00', '19:00', rhythm='Kid Club', title='hosting the Halloween potluck at our house'),   # community care
    row('🚶‍♀️ walking', '11:00', '11:30', title='walk with the forest school kids'),                    # moving, and community care
    row('🍳 dinner prep', '17:00', '17:30', person=['Ollie Plum'], title='made the sides — baked potato, carrots'),   # family care, not making
    row('⚡ action', '13:00', '13:30', rhythm='Paid Work', title='Tidy the house — the bathrooms'),       # home care, not work
    row('📝 log', '20:00', '22:00', rhythm='Fun', person=['Moss Quill'], title="the Quills' party"),     # social recreation
]
L6 = dict(L4, recreation={'rhythms': ['Fun']}, care=dict(L4['care'], community={'words': ['forest school kids']}))
K6 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in day_rings(CARE6, DAY, L6)['bands']}
assert K6['doing'].get('home') == 20 + 30 and not K6['doing'].get('work') and not K6['doing'].get('cook'), K6['doing']
assert K6['doing'].get('community') == 30 + 180, K6['doing']           # the walk, and the hosting: her words win over the rhythm
assert K6['doing'].get('family') == 30 + 30, K6['doing']               # the kitchen after dinner, and the sides
assert K6['being'].get('social') == 120, K6['being']
print('ok — the kitchen after dinner is family care, the school kids are community care, a party is social recreation')

# 1 Nov 2026: a be•do session whose notes talk about community care is be•do work; 🫧 hygiene is personal care.
CARE7 = NIGHT + [
    row('⚡ action', '09:00', '10:00', rhythm='the system', title='settled the care kinds',
        details='what I did\n· voting is community care; hosting a party is community care\n'
                '· filled every minute: Biscuit the whole time at the park\n———\n[be•do] a session'),
    row('🫧 hygiene', '22:00', '22:20', rhythm='Body Care', title='personal care and my evening routine'),
]
K7 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in day_rings(CARE7, DAY, L6)['bands']}
assert not K7['doing'].get('community') and not K7['doing'].get('pet') and K7['doing'].get('system') == 60, K7['doing']
assert K7['being'].get('personal') == 20 and not K7['doing'].get('work'), (K7['being'], K7['doing'])
print('ok — a session about care (its notes naming community care, or the dog) is still be•do; hygiene is personal care')

# 1 Nov 2026: shared care — the prep and the party were both family and community care, half and half.
CARE8 = NIGHT + [
    row('⚡ action', '13:00', '14:00', rhythm='The Party', title='Clean the kitchen'),                  # both, half each
    row('⚡ action', '17:00', '18:00', rhythm='The Party', title='Make the spaghetti'),                 # not work: both
    row('⚡ action', '16:00', '18:00', rhythm='The Party', title='the potluck at our house'),           # both, half each
    row('🧽 clean', '10:00', '10:20', title='the bathroom'),                                          # still home care
]
L8 = dict(L6, care=dict(L6['care'], shared={'rhythms': ['The Party'], 'kinds': ['family', 'community']}))
R8 = day_rings(CARE8, DAY, L8)
K8 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in R8['bands']}
assert not K8['doing'].get('work') and K8['doing'].get('home') == 20, K8['doing']
assert K8['doing'].get('family') == 90 and K8['doing'].get('community') == 90, K8['doing']   # 3 h of party, half each
lanes = [r for r in next(b for b in R8['bands'] if b['k'] == 'doing')['runs'] if r[0] in ('family', 'community')]
assert all(r[5] == 2 for r in lanes), lanes                                                         # drawn as two lanes
print('ok — shared care is two kinds at once, two lanes, half each in the totals')

# 1 Nov 2026: care, grouped — one kind, each minute once, the kinds that happened named under it.
L9 = dict(L8, care=dict(L8['care'], grouped=True))
R9 = day_rings(CARE8, DAY, L9)
D9 = next(b for b in R9['bands'] if b['k'] == 'doing')
K9 = {k['k']: k for k in D9['kinds']}
assert set(K9) & {'family', 'community', 'pet', 'home'} == set(), list(K9)
assert K9['care']['min'] == 180 + 20, K9['care']                  # the party once, and the bathroom
assert [o[0] for o in K9['care']['of']] == ['family', 'community', 'home'], K9['care']['of']
assert all(r[5] == 1 for r in D9['runs'] if r[0] == 'care'), D9['runs']   # one lane, not two
assert 'the potluck at our house' in [t for r in D9['runs'] if r[0] == 'care' for t in r[3]]
print('ok — care grouped: one kind, each minute once, the kinds named')

# Their day is theirs (28 Oct 2026): an event from their own calendar and their own play go on their strip,
# never on her rainbow; what she did meanwhile is her rows.
import base64 as _b64
def _link(cal):
    return 'https://www.google.com/calendar/event?eid=' + _b64.urlsafe_b64encode(
        ('abc123_20260304T210000Z %s@g' % cal).encode()).decode().rstrip('=')
L5 = dict(L, care={'family': {'rhythms': ['Kid Club'], 'people': ['Pip'], 'calendars': ['kidcal42@group.calendar.google.com']}})
THEIRS = NIGHT + [
    row('⚡ action', '16:00', '17:00', rhythm='Kid Club', person=['Pip Plum'], title='Swim class', event=_link('kidcal42')),
    row('📝 log', '16:00', '16:20', person=['Pip Plum'], title='at swim class with Pip'),         # her 20 minutes there
    row('🚶‍♀️ walking', '16:25', '17:00', title='a walk by the creek'),                          # what she did meanwhile
    row('🎮 game', '19:00', '19:40', person=['Pip Plum'], title='Pip playing blocks'),              # his own play
    row('🍽️ dinner', '17:30', '18:00', person=['Pip Plum'], title="Pip's dinner, a clean plate"),      # his own meal
    row('⚡ action', '10:00', '10:30', rhythm='Kid Club', person=['Pip Plum'], title='Dentist with Pip',
        event=_link('mycal')),                                                                      # her own calendar: hers
]
R5 = day_rings(THEIRS, DAY, L5)
K5 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in R5['bands']}
assert K5['doing'].get('family') == 20 + 30, K5['doing']            # her 20 minutes and the dentist, not his hour
assert not K5['being'].get('recreation'), K5['being']                 # his game is his
assert [(x['who'], x['t']) for x in R5['theirs']] == [('Pip', 'Swim class'), ('Pip', "Pip's dinner, a clean plate"),
                                                     ('Pip', 'Pip playing blocks')], R5['theirs']
assert not K5['being'].get('eat'), K5['being']                      # his dinner is his
print('ok — their day is theirs: his class and his game on his strip; her 20 minutes and the dentist are hers')

# Two things at once draw as two lanes and both count; synergy and competing are read from her words
# (28 Oct 2026: "it would be neat to show that on the graphic").
ONCE = NIGHT + [
    row('🍽️ lunch', '12:00', '12:20', title='lunch outside', details='I felt like there was a lot of synergy with that.'),
    row('📼 video', '12:05', '12:20', title='a weather video'),
    row('🚶‍♀️ walking', '16:00', '16:40', title='walk by the creek with Biscuit',
        details='Walking Biscuit and a podcast is pretty competitive.'),
    row('🎧 podcast', '16:00', '16:40', title='a podcast'),
    row('📒 journal', '18:10', title='journal on the walk', details='This is a wonderful synergy.'),
    row('🚶‍♀️ walking', '18:00', '18:30', title='evening walk'),
    row('🍽️ dinner', '19:00', '19:30', title='dinner', details='Pure synergy, alone with soup.'),   # one thing: no synergy
    row('⚡ action', '13:00', '15:00', rhythm='the system', title='the synergy reader',
        details='what I did\n· synergy is read from what I say'),                                   # the system talking about it
    row('📝 log', '13:00', '15:00', rhythm='Paid Work', title='the report, alongside'),
]
R6 = day_rings(ONCE, DAY, L4)
B6 = {b['k']: b for b in R6['bands']}
lanes = [(r[0], r[1], r[2], r[4], r[5]) for r in B6['being']['runs'] if r[1] == 16 * 60]
assert lanes == [('move', 960, 1000, 0, 2), ('recreation', 960, 1000, 1, 2)], lanes
K6 = {k['k']: k['min'] for k in B6['being']['kinds']}
assert K6['move'] == 40 + 30 and K6['recreation'] == 15 + 40, K6     # both count, every minute of each
S6 = [(s['a'], s['b'], s['ans']) for s in R6['synergy']]
assert S6 == [(720, 740, 'synergizing'), (960, 1000, 'competing'), (1080, 1110, 'synergizing')], S6
print('ok — two at once are two lanes and both count; synergy and competing from her words, never for one thing alone')

# 1 Nov 2026, her pick: how I spent my time is what I did; who was there is a mark on the stretch, not a kind of time.
WITH11 = NIGHT + [
    row('⚡ action', '16:00', '20:00', rhythm='Kid Club', person=['Ollie Plum', 'Pip Plum', 'Moss Quill', '♐Wren Ash'],
        title='the potluck at our house'),
    row('📝 log', '20:00', '22:00', rhythm='Fun', person=['Moss Quill'], title="the Quills' party"),   # recreation, not social
    row('🍽️ lunch', '12:00', '12:10', person=['Moss Quill']),                                          # under 15 minutes: no mark
]
L11 = dict(L6, household=['Ollie', 'Pip'])
R11 = day_rings(WITH11, DAY, L11)
K11 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in R11['bands']}
assert 'social' not in K11['being'] and K11['being'].get('recreation') == 120, K11['being']
assert [(w['a'], w['b'], w['who']) for w in R11['with_others']] == [(960, 1320, ['Moss', 'Wren'])], R11['with_others']
print('ok — who was there is a mark on the stretch: with others, by name; no social kind of time')

# 1 Nov 2026, her pick: who I was with — every waking minute alone (dogs count), family, or social; people by circle.
W12 = NIGHT + [
    row('📝 log', '09:00', '10:00', person=['Pip Plum'], title='breakfast fort with Pip'),          # family
    row('⚡ action', '16:00', '18:00', rhythm='Kid Club', person=['Pip Plum', 'Moss Quill'], title='the potluck',
        mentioned='Moss, Quill Vane, the Thursday group'),                                                      # social
    row('🗨️ text', '12:00', title="a photo from Wren Ash's group text"),                           # at a distance
]
L12 = dict(L6, household=['Ollie', 'Pip'], _circles={'Moss Quill': 'Friends', 'Wren Ash': 'Family'})
WC = day_rings(W12, DAY, L12)['who']
awake = WC['alone'] + WC['family'] + WC['social']
assert (WC['family'], WC['social']) == (60, 120) and awake == 24 * 60 - (7 * 60 + 30), WC   # up 7:30, no bedtime: to midnight
assert [(p['n'], p['min'], p['circle']) for p in WC['people']] == [('Pip Plum', 180, 'Family'), ('Moss Quill', 120, 'Friends')], WC['people']
assert [(c['who'], c['circle']) for c in WC['contacts']] == [(['Wren Ash'], 'Family')], WC['contacts']
assert WC['mentioned'] == ['Quill Vane', 'the Thursday group'], WC['mentioned']          # Moss was there: no mention line
assert {k for k, a, b in WC['strip']} == {'alone', 'family', 'social'}
print('ok — who I was with: alone, family, social; the people by circle; a text by name in its circle; mentioned once')

# 1 Nov 2026: social splits by who — work when everyone outside the family there is from her Work circle.
W13 = NIGHT + [
    row('⚡ action', '10:00', '11:00', rhythm='Paid Work', person=['Fern Oak'], title='the grant meeting'),   # work
    row('⚡ action', '16:00', '17:00', rhythm='Kid Club', person=['Fern Oak', 'Moss Quill'], title='the potluck'),  # social
]
L13 = dict(L12, _circles={'Fern Oak': 'Work', 'Moss Quill': 'Friends'})
WC13 = day_rings(W13, DAY, L13)['who']
assert (WC13['work'], WC13['social']) == (60, 60), WC13
print('ok — social splits by who: all of them from work is work time; friends there makes it social')

# 1 Nov 2026, her pick: balance, the original wheel in plain minutes — each row's wellness kind takes its minutes, a
# moment counts five, sleep and his own rows count nothing; doing on a drive grows, any other doing tends.
E14 = NIGHT + [
    row('🧽 clean', '13:00', '14:00', wellness='🌎 earth', title='the bathrooms'),                      # earth 60, tending
    row('⚡ action', '15:00', '15:30', wellness='💨 air', rhythm='The Report', title='the report'),       # air 30, growing
    row('⚡ action', '16:00', '18:00', wellness='🩷 heart', title='the potluck at our house'),          # heart 120
    row('📌 social', '07:00', '07:30', wellness='🧠 mind', emotion=['🔴 high energy · unpleasant'],
        title='scrolling in bed'),                                                                        # mind 30
    row('🙏 gratitude', '09:55', wellness='💖 spirit', title='a good night'),                           # spirit 5
    row('📝 log', '11:00', '11:20', wellness='🧠 mind', person=['Pip Plum'], title='Pip — his reading'),  # his: nothing
]
EN = day_rings(E14, DAY, dict(L, _growing=['The Report']))['energy']
assert {k: v for k, v in EN['min'].items() if v} == {'earth': 60, 'air': 30, 'heart': 120, 'mind': 30, 'spirit': 5}, EN['min']
assert (EN['be'], EN['tending'], EN['growing']) == (155, 60, 30), EN
assert EN['rows']['heart'] == ['the potluck at our house'], EN['rows']
print('ok — balance: plain minutes by wellness kind; doing on a drive grows, the rest tends; sleep and his rows count nothing')
E15 = NIGHT + [row('⚡ action', '16:00', '18:00', wellness='🩷 heart', title='the potluck'),
               row('📝 log', '17:00', '18:00', wellness='🩷 heart', title='the living room after')]   # inside it: once
assert day_rings(E15, DAY, L)['energy']['min']['heart'] == 120
print('ok — the wheel counts a minute once per kind, however many rows hold it')
