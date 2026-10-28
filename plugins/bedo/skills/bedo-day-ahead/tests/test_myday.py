# -*- coding: utf-8 -*-
"""The my day page's two cards and its name (261028_myday, 28 Oct 2026).

Card 1 holds the day only — today's steps, carried-in ones from the last week,
and the ones finished today — drives first, then rhythms, each drive with its %
progress. The whole map holds every rhythm in code order, each drive under its
rhythm (or under the drive it feeds), its open steps and the ground covered.
Today's look ahead row says the day's own link; the old living page is not one.

Every name below is an obvious invention.

    python3 tests/test_myday.py
"""
import datetime as dt, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import myday  # noqa: E402

TODAY = dt.date(2026, 3, 4)
local = lambda ts: dt.datetime.fromisoformat(ts.replace('Z', '+00:00')).replace(tzinfo=None)
DRIVES = {
    'Rhythm Two': dict(name='Rhythm Two', type='♒ rhythm', status='active', code='R2', emoji='🌿', feeds=[]),
    'Rhythm One': dict(name='Rhythm One', type='♒ rhythm', status='active', code='R1', emoji='🌊', feeds=[]),
    'Drive A — the long part of its name': dict(name='Drive A — the long part of its name', type='♐ drive', status='active',
                                                code='D1', emoji='🚐', parent='Rhythm One', dest=['a far place'],
                                                target='2026-06-01', feeds=[]),
    'Drive B': dict(name='Drive B', type='♐ drive', status='active', code='D2', emoji='', parent=None, dest=[],
                    target=None, feeds=['Drive A — the long part of its name']),
    'a far place': dict(name='a far place', type='♎ destination', status='active', emoji='🏔️', feeds=[]),
}
A = 'Drive A — the long part of its name'
n = [0]


def row(title, rhythm, status='⬜ intention', practice='⚡ action', target=None, created='2026-03-04T09:00:00Z',
        when=None, end=None, key=None, details='', deliverable=None, queue=None, waiting=None):
    n[0] += 1
    return dict(id=f'rec{n[0]:05d}', key=key or f'2603{n[0]:02d}_0900', title=title, rhythm=rhythm, status=status,
                practice=practice, target=target, created=created, when=when, end=end, details=details, person='',
                deliverable=deliverable, queue=queue, waiting=waiting)


ROWS = [
    row('⚡ a step for today', A, target='2026-03-04T15:00:00Z', details='my own words\n———\n[be•do] a note'),
    row('⚡ carried from Monday', A, target='2026-03-02T15:00:00Z'),
    row('⚡ too old to carry', A, target='2026-02-20T15:00:00Z'),
    row('⚡ finished this morning', A, status='✅ done', end='2026-03-04T08:00:00Z'),
    row('⚡ finished last week', A, status='✅ done', end='2026-02-25T08:00:00Z', created='2026-02-25T08:00:00Z'),
    row('⚡ a rhythm step', 'Rhythm Two', target='2026-03-04T15:00:00Z'),
    row('⚡ next month', 'Drive B', target='2026-04-10T15:00:00Z', created='2026-03-01T09:00:00Z'),
    row('⚡ in the queue', A, target='2026-03-04T15:00:00Z', queue='later'),
    row('a walk', 'Rhythm Two', status='● log', practice='🚶 walk', when='2026-03-03T08:00:00Z', created='2026-03-03T08:00:00Z'),
    row('look ahead — the day ahead', '', status='◉ done', practice='👁️ look ahead', deliverable='https://example.invalid/living'),
]
LATEST = {r['id']: r for r in ROWS}
OPEN_IDS = {r['id'] for r in ROWS if r['status'] in myday.WORKING and not r['queue']}


def main():
    card, whole = myday.build(ROWS, LATEST, OPEN_IDS, lambda r: False, TODAY, DRIVES, {'map_end': '2026-12-31'}, local,
                              lambda r: r['key'])
    titles = [s['t'] for s in card['steps']]
    assert titles[0] == 'carried from Monday', titles
    assert set(titles) == {'carried from Monday', 'a step for today', 'finished this morning', 'a rhythm step'}, titles
    today = next(s for s in card['steps'] if s['t'] == 'a step for today')
    assert today['det'] == 'my own words' and today['mine'], today
    assert card['prog'][A] == dict(done=2, open=3, since='2026-02-25'), card['prog'][A]
    assert card['drives'][A]['short'] == 'Drive A' and card['drives']['Drive B']['c'] == card['drives'][A]['c']
    assert card['hist']['ev']['Rhythm Two'] == ['2026-03-03'], card['hist']
    assert whole['order'] == ['Rhythm One', 'Rhythm Two'], whole['order']
    assert whole['dest'] == {'a far place': '🏔️'}
    b = next(d for d in whole['drives'] if d['n'] == 'Drive B')
    assert b['parent'] == 'Rhythm One' and b['up'] == A and whole['feeds'] == [['Drive B', A]], b
    assert [a['t'] for a in b['acts']] == ['next month'] and not b['acts'][0]['today']
    a = next(d for d in whole['drives'] if d['n'] == A)
    assert 'in the queue' not in [x['t'] for x in a['acts']] and a['past'] == ['2026-02-25', '2026-03-04'], a
    assert whole['begin'] == '2026-02-25' and whole['end'] == '2026-12-31'
    # the day's own link: none while the row carries the living page, then the day's
    assert myday.today_link(ROWS, TODAY, local, 'https://example.invalid/living') == dict(url=None, row=ROWS[-1]['id'])
    ROWS[-1]['deliverable'] = 'https://example.invalid/the-day'
    assert myday.today_link(ROWS, TODAY, local, 'https://example.invalid/living')['url'] == 'https://example.invalid/the-day'
    assert myday.today_link(ROWS, TODAY + dt.timedelta(days=1), local) == dict(url=None, row=None)
    print('ok — card 1 holds the day, drives carry their progress, the map orders rhythms by code, the day names its link')


if __name__ == '__main__':
    main()
