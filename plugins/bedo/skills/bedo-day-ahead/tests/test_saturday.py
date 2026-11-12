# -*- coding: utf-8 -*-
"""A Saturday's my day page (7 Nov 2026): no task on the clock, an empty afternoon folded, and a real list of things
she might want to do — fun and low effort first, each with its way in, none with a time.

Every name below is an obvious invention.

    python3 tests/test_saturday.py
"""
import datetime as dt, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import saturday  # noqa: E402

F = dict(title='t', target='tg', status='st', end='en', rhythm='rh', details='d', when='wh', practice='pr', event='ev',
         mentioned='mn', deliverable='dl')
RF = dict(name='n', parent='p', type='ty')
OFF = dt.timedelta(hours=-6)
DAY = dt.date(2030, 3, 9)            # a Saturday
n = [0]


def row(title, rhythm='Kites & Wanders', status='▫️potential', d='', when='2030-03-01T15:00:00Z', pr='⚡ action', **extra):
    n[0] += 1
    c = dict(t=title, rh=rhythm, st=status, d=d, wh=when, pr=pr, **extra)
    return dict(id=f'rec{n[0]:05d}', cellValuesByFieldId={k: v for k, v in c.items() if v})


def every(out):
    return [(g['g'], x) for g in out for x in g.get('items') or []]


def main():
    rhythms = [dict(cellValuesByFieldId=dict(n='Wanders & Kites', ty='♒ rhythm')),   # spelled its own way
               dict(cellValuesByFieldId=dict(n='House Upkeep', ty='♒ rhythm')),
               dict(cellValuesByFieldId=dict(n='Tales & Quiet', ty='♒ rhythm')),
               dict(cellValuesByFieldId=dict(n='Kite Club', p='Wanders & Kites')),
               dict(cellValuesByFieldId=dict(n='Paid Work', p='Water Mission')),
               dict(cellValuesByFieldId=dict(n='Ledger Cleanup', p='Money & Forms'))]
    rows = [
        row('⚡ Zephyr Hollow Nature Trails — might be fun', d='Looks fun.\n\nhttps://maps.app.goo.gl/abc\n———\n[be•do] note',
            when='2030-03-09T14:00:00Z'),
        row('⚡ a big pot of soup this weekend', rhythm='House Upkeep', status='⬜ intention'),
        row('⚡ Pay the water bill', rhythm='House Upkeep', status='⬜ intention'),          # a chore: never an idea
        row('⚡ Update the expired card on the payment site', status='⬜ intention'),     # 7 Nov: 'card' read as fun
        row('⚡ Weekly budget recap — make it a weekly read', status='⬜ intention'),     # 7 Nov: 'make' read as fun
        row('⚡ Teach Quill card games', status='⬜ intention'),
        row('⚡ Lantern walk with Quill — Sun 10 Mar, 2:00', tg='2030-03-10T20:00:00Z', ev='https://cal/e1'),
        row('⚡ Old festival — Sat 2 Mar', tg='2030-03-02T15:00:00Z', ev='https://cal/e2'),   # a maybe whose day has gone
        row('⚡ go to Brightwater Ranch — I always want to'),
        row('⚡ Brightwater Ranch with Quill — this week', status='⬜ intention'),             # the same place: one card
        row('⚡ a Marlow day — the bookshop and the noodle place'),
        row('⚡ Choose wheels for the club cart', rhythm='Kite Club', status='⬜ intention'),        # a fun drive's step
        row('⚡ Sort the receipts', rhythm='Ledger Cleanup', status='⬜ intention'),           # not a fun drive
        row('Japan trip — when Quill is a teenager'),
        row('Try Neuro Art for Quill', rhythm='Quill School', status='⬜ intention'),           # fun from a non-work drive
        row('⚡ Draft the soil paper chart games', rhythm='Paid Work', status='⬜ intention'),   # a work drive: never
        row('🚶 walked the Willow Creek Trail — 2 mi', status='◉ done', when='2030-03-04T22:00:00Z',
            d='walking Biscuit on the trail'),
        row('⚡ have fun today', status='⬜ intention'),                                       # her intention itself
        row('📜 Sunday reflection — still to do', rhythm='Tales & Quiet', status='⬜ intention', pr='📜 reflection'),
    ]
    stories = [dict(id='s1', fields=dict(title='Ponyo', kind='🎥 movie', standing='want', added='2030-01-01')),
               dict(id='s2', fields=dict(title='A slow nature film', kind='📺 show', standing='in motion')),
               dict(id='s3', fields=dict(title='Morning headlines', kind='📰 news', standing='want'))]
    places = [dict(id='p1', fields=dict(place='Heron Lake boardwalk', standing='want to go', where='half an hour west')),
              dict(id='p2', fields=dict(place='Summit Ridge', standing='want to go', where='Montana')),
              dict(id='p3', fields=dict(place='Old office', standing='been'))]
    L = dict(saturday_fun=['Wanders & Kites', 'Tales & Quiet'], tending=['House Upkeep'], child_calendar='Quill', work_parents=['Water Mission'])
    out = saturday.ideas(DAY, rows, F, OFF, rhythms, RF, L, stories, places, ['I just want to have fun'])
    groups = [g['g'] for g in out]
    assert next(g for g in out if g['g'] == 'stories')['moods'][0]['label'] == 'with Quill'
    assert groups.index('home') < groups.index('stories') < groups.index('out'), groups   # easy first
    got = every(out)
    titles = [x['t'] for _, x in got]
    by = {x['t']: (g, x) for g, x in got}

    assert not any('water bill' in t or 'receipts' in t or 'Old festival' in t or 'have fun' in t or 'reflection' in t
                   for t in titles), titles
    assert by['a big pot of soup this weekend'][0] == 'home'
    assert by['Teach Quill card games'][0] == 'home'
    z = next(x for t, (g, x) in by.items() if t.startswith('Zephyr'))
    assert by[z['t']][0] == 'out' and z['links'][0] == dict(l='map', u='https://maps.app.goo.gl/abc')
    lw = next(x for g, x in got if x['t'].startswith('Lantern'))
    assert lw['when'] == 'tomorrow 2:00 PM · a maybe', lw['when']
    assert dict(l='calendar event', u='https://cal/e1') in lw['links']
    ranch = [x for g, x in got if 'Brightwater' in x['t']]
    assert len(ranch) == 1 and len(ranch[0]['also']) == 1, ranch
    assert any(l['l'] == 'map' for l in ranch[0]['links'])
    assert by['a Marlow day — the bookshop and the noodle place'][0] == 'day'
    assert by['Choose wheels for the club cart'][0] == 'plan'
    assert by['Japan trip — when Quill is a teenager'][0] == 'far'
    assert by['Try Neuro Art for Quill'][0] == 'home'
    assert not any('soil paper' in t for t in titles)
    assert not any('expired card' in t or 'budget recap' in t for t in titles), titles
    assert by['the Willow Creek Trail — with the dogs'][0] == 'out'
    assert by['Heron Lake boardwalk'][0] == 'out' and by['Summit Ridge'][0] == 'far'
    assert 'Old office' not in titles
    assert not any(x.get('when') for g, x in got if g != 'soon')          # no clock on any idea but its own date

    st = next(g for g in out if g['g'] == 'stories')['moods']
    moods = {m['m']: [i['t'] for i in m['items']] for m in st}
    assert moods['kid'] == ['Ponyo'] and moods['learn'] == ['A slow nature film'], moods
    assert not any('headlines' in t for ts in moods.values() for t in ts)

    # if you feel like it: the pull of someone waiting, a near date, money; one per drive; never blocked, never fun
    pull = [
        row('⚡ Grant resubmission due Tue 12 Mar', rhythm='Paid Work', status='⬜ intention', tg='2030-03-12T23:00:00Z', mn='Pat Rowan'),
        row('⚡ Grant budget V3 — before 2:00', rhythm='Paid Work', status='⬜ intention', tg='2030-03-10T20:00:00Z',
            mn='Pat Rowan', waiting='Pat — feedback'),                                            # blocked on Pat
        row('⚡ Invite the Moss family to dinner', rhythm='Hosting', status='⬜ intention', tg='2030-03-09T23:00:00Z',
            mn='Robin Moss'),
        row('⚡ Map draft ready for review — end of day Monday', rhythm='Map Work', status='⬜ intention',
            tg='2030-03-11T23:00:00Z', mn='Jo'),
        row('⚡ Map legend tweak', rhythm='Map Work', status='⬜ intention', tg='2030-03-11T20:00:00Z'),   # same drive
        row('⚡ Old report', rhythm='Paid Work', status='⬜ intention', tg='2030-03-01T20:00:00Z'),   # long past
        row('⚡ Call the clinic', rhythm='House Upkeep', status='⬜ intention', tg='2030-03-09T18:00:00Z', ev='https://cal/x'),
        row('⚡ Brightwater Ranch picnic', status='⬜ intention', tg='2030-03-09T18:00:00Z'),         # on the fun list
    ]
    F2 = dict(F, person='pe', waiting='waiting', quickie='qk')
    for r in pull:
        r['cellValuesByFieldId']['waiting'] = r['cellValuesByFieldId'].pop('waiting', None)
    got = saturday.feel(DAY, pull, F2, OFF, dict(L, self_person='Me'), rhythms, RF)
    assert [x['t'] for x in got] == ['Grant resubmission due Tue 12 Mar', 'Invite the Moss family to dinner',
                                     'Map draft ready for review — end of day Monday'], [x['t'] for x in got]
    assert got[1]['why'] == 'Robin Moss · due today'

    # a weekend's open steps leave the clock for a list (flow.build's own rule, checked on its data shape)
    import flow
    sched = [dict(k='event', t='Party', a='15:00', b='17:00'), dict(k='lived', t='walk', a='08:00', b='08:30', done=True),
             dict(k='step', t='Fold laundry', a='13:00', b='13:30', drive='Home', done=False),
             dict(k='step', t='Done step', a='09:00', b='09:15', done=True)]
    clock, tasks = flow.off_the_clock(sched)
    assert [x['t'] for x in clock] == ['Party', 'walk', 'Done step']
    assert [(x['t'], x['drive']) for x in tasks] == [('Fold laundry', 'Home')]
    # a podcast is 🎙️ (10 Nov 2026), an audiobook 🎧: both are listening, neither gets a "where to watch" link
    assert saturday.mood_of({'title': 'An episode', 'kind': '🎙️ podcast'}) == 'listen'
    assert saturday.mood_of({'title': 'A long book', 'kind': '🎧 audiobook'}) == 'listen'
    print('saturday: ok')


if __name__ == '__main__':
    main()
