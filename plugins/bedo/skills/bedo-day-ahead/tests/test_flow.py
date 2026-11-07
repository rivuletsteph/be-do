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
    # the wheel at the bottom, built through the day (3 Nov 2026): the rows that made it, each with its element
    ents = []
    flow.wheel_of(dt.date(2026, 3, 4), day_rows, W, zero, ents)
    assert [(e['k'], e['at']) for e in ents] == [('body', '09:00'), ('mind', '11:00')], ents

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
    # a session: small steps of one kind batched at one time, its top first, picks and other drives left alone
    S = flow.session_arg('🪙 money hour::16:00-17:00::Money|Taxes')
    assert (S['name'], S['a'], S['b'], S['drives']) == ('🪙 money hour', '16:00', '17:00', {'Money', 'Taxes'})
    st = lambda t, d, key, **kw: dict(k='step', t=t, a='09:00', b='10:00', drive=d, key=key, rid='r' + key, **kw)
    items = [st('pay the water bill', 'Money', 'k1'), st('file the receipt', 'Taxes', 'k2'),
             st('call the bank', 'Money', 'k3', pick=True), st('walk the dog', 'Pets', 'k4'),
             dict(k='event', t='dentist', a='14:00', b='15:00')]
    out = flow.sessions_of(items, [dict(S, top=[('k2', 'due Friday')])])
    sess = [x for x in out if x.get('session')]
    assert len(sess) == 1 and (sess[0]['a'], sess[0]['b']) == ('16:00', '17:00'), sess
    assert [o['t'] for o in sess[0]['list']] == ['file the receipt', 'pay the water bill']
    assert sess[0]['list'][0]['top'] and sess[0]['list'][0]['why'] == 'due Friday' and not sess[0]['list'][1]['top']
    assert all(o['sz'] == flow.SESSION_MIN for o in sess[0]['list'])
    assert {x['t'] for x in out if not x.get('session')} == {'call the bank', 'walk the dog', 'dentist'}
    assert flow.sessions_of(items, []) == sorted(items, key=lambda x: (x['a'], x['k'] != 'event'))
    # an event is drawn once: its own row and what happened inside it fold in, other calendars and moments do not
    ev = lambda t, a, b, who='you': dict(k='event', t=t, a=a, b=b, who=who)
    lv = lambda t, a, b, cat='move', links=None: dict(k='lived', t=t, a=a, b=b, cat=cat, links=links)
    note = [dict(l='notes', u='https://example.org/notes')]
    items = [ev('Yoga class', '09:00', '09:45'), lv('stretches, in yoga', '09:00', '09:45'),
             lv('a glimmer at yoga', '09:05', '09:06', cat='moment'),
             ev('Team call', '10:00', '10:45'), lv('🌱 team CALL', '10:00', '11:00', cat='work', links=note),
             ev('Grandparents day', '08:30', '15:30', who='Kid'), lv('sun on the patio', '08:30', '08:40'),
             lv('lunch', '12:00', '12:30', cat='eat')]
    out = flow.fold_into_events(items)
    yoga, call = out[0], out[3 - 1]
    booked = flow.fold_into_events([ev('Massage', '14:20', '15:20'),
                                    dict(lv('book the massage', '14:20', '14:30', cat='personal'), act=True)])
    assert len(booked) == 1 and 'covers' not in booked[0], booked
    assert yoga['covers'] == ['stretches, in yoga'] and yoga['done'], yoga
    assert call['t'] == 'Team call' and 'covers' not in call and call['links'] == note, call
    assert {x['t'] for x in out} == {'Yoga class', 'a glimmer at yoga', 'Team call', 'Grandparents day',
                                     'sun on the patio', 'lunch'}, [x['t'] for x in out]
    # a row on a work drive is work, even with the family about (7 Nov 2026); without the drive, they make it family care
    K = dict(F, person='pe')
    C = flow.with_drives(dict(care=dict(family=dict(rhythms=['Kid'], people=['Kid']))),
                         dict(drives=[dict(n='Data Hub', parent='Work Rhythm'), dict(n='Home Drive', parent='Home')]),
                         dict(work_parents=['Work Rhythm']))
    cell = lambda rh: dict(t='⚡ posted the update', pr='⚡ action', rh=rh, pe='Kid, Partner')
    assert flow.kind_of(cell('Data Hub'), K, frozenset(), C) == 'work'
    assert flow.kind_of(cell('Work Rhythm'), K, frozenset(), C) == 'work'
    assert flow.kind_of(cell('Home Drive'), K, frozenset(), C) == 'family'
    assert flow.kind_of(dict(cell('Data Hub'), pr='🍽️ lunch'), K, frozenset(), C) == 'eat'

    # a long stretch done whenever nothing else was going on is one running column (7 Nov 2026)
    L_ = lambda t, a, b, **k: dict(dict(k='lived', t=t, a=a, b=b, cat='work', pt=False), **k)
    out = flow.fill_between([L_('long work', '15:40', '20:05'), L_('📝 evening work', '20:05', '22:00'),
                             L_('supper', '17:20', '17:50', cat='eat'), L_('a walk', '10:00', '11:50', cat='move')])
    assert [x['t'] for x in out if x.get('column')] == ['long work', '📝 evening work'], out

    # a plan closed by what happened is drawn once (7 Nov 2026)
    out = flow.fold_done_plans([dict(k='lived', t='pizza for supper, delivered', a='17:12', b='17:22', act=True, pt=True, links=[1]),
                                dict(k='lived', t='early supper, pizza delivered', a='17:21', b='17:51', cat='eat', pt=False),
                                dict(k='lived', t='text: pizza tonight', a='11:25', b='11:35', act=True, pt=True)])
    assert [x['t'] for x in out] == ['early supper, pizza delivered', 'text: pizza tonight'], out
    assert out[0]['done'] and out[0]['links'] == [1]

    # every day page carries the download button (261106_download): the viewer's save prompt, else a Blob download
    for eng in (os.path.join(HERE, '..', 'assets', 'flow_engine.html'),
                os.path.join(HERE, '..', '..', 'bedo-week-look-behind', 'assets', 'week_look_behind_engine.html')):
        e = open(eng, encoding='utf-8').read()
        assert "id='bedo-dl'" in e and "c.use('downloads')" in e and 'new Blob(' in e, eng

    print('ok — balance is evenness, a goal is her first sentence, buffer counts what is late that morning, '
          'the day holds her free hours, a size is a guess off the words, a session batches one kind at its time, '
          'an event is drawn once with what it covered, a work drive is work, every day page can download itself, a long stretch is one column, a closed plan folds into what happened')


if __name__ == '__main__':
    main()
