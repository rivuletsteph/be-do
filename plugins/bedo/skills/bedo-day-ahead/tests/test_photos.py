# -*- coding: utf-8 -*-
"""Her keeper photos on the my day page's cards (5 Nov 2026): a photo goes on the row whose photo links name
it, else the row at that minute; a photo linked to an info row stays off; only keepers are drawn.
Every name is an invention.

    python3 tests/test_photos.py
"""
import datetime as dt, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'core'))
import flow  # noqa: E402

F = dict(title='t', when='wh', end='en', status='st', practice='pr', person='pe', photo='ph', photo_links='pl',
         details='de')
DAY = dt.date(2026, 3, 4)
OFF = dt.timedelta(hours=-6)
import bedo_photos  # noqa: E402
link = bedo_photos.link


def row(rid, title, a, b, **c):
    v = dict(t=title, wh=a, en=b, st='● log', **c)
    return dict(id=rid, cellValuesByFieldId=v)


def main():
    d = tempfile.mkdtemp()
    names = {'PXL_20260304_143100000.jpg': 'fidMorning0001', 'PXL_20260304_231500000.jpg': 'fidOutside0001',
             'PXL_20260304_232900000.jpg': 'fidTable000001'}
    for n in names:
        open(os.path.join(d, n), 'wb').write(b'\xff\xd8\xff')     # a stand-in; only its name and bytes matter
    json.dump({n: f for n, f in names.items()}, open(os.path.join(d, 'index.json'), 'w'))
    rows = [row('r1', '✨ sun on the patio', '2026-03-04T14:30:00.000Z', '2026-03-04T14:40:00.000Z',
                pr='✨ glimmer', ph='keeper', pl=link('fidMorning0001')),
            row('r2', '🔅 evening sun', '2026-03-04T23:11:00.000Z', '2026-03-04T23:14:00.000Z',
                pr='🔅 evening sun', ph='info', pl=link('fidOutside0001')),
            row('r3', '⭐ dinner out', '2026-03-04T23:14:00.000Z', '2026-03-04T23:57:00.000Z',
                pr='⭐ highlight', ph='keeper', pl=link('fidTable000001'), pe='a guest')]
    items = [dict(k='lived', t='sun', a='08:30', b='08:40', rid='r1'),
             dict(k='lived', t='evening sun', a='17:11', b='17:14', rid='r2'),
             dict(k='event', t='Dinner', a='17:10', b='18:00', rids=['r3'])]
    n = flow.photos_onto(items, DAY, rows, F, OFF, d, me='me')
    got = {x['t']: [p['url'] for p in x.get('photos') or []] for x in items}
    assert got['sun'] == [link('fidMorning0001')], got
    assert got['evening sun'] == [], got                      # linked to an info row: off the page
    assert got['Dinner'] == [link('fidTable000001')], got           # folded into its event, the photo follows
    assert n == 2
    # an unlinked photo taken during a row that links another stays off it
    open(os.path.join(d, 'PXL_20260304_232000000.jpg'), 'wb').write(b'\xff\xd8\xff')
    items2 = [dict(k='lived', t='dinner', a='17:14', b='17:57', rid='r3')]
    flow.photos_onto(items2, DAY, rows, F, OFF, d, me='me')
    assert [p['url'] for p in items2[0]['photos']] == [link('fidTable000001')], items2
    assert flow.photos_onto(items, DAY, rows, F, OFF, None) == 0
    print('ok — a keeper photo lands on its row by link, an info photo stays off, an event carries its rows\' photos')
    own_row()


def own_row():
    """An event's own row, folded onto its event card, passes its photos on (found 6 Nov 2026, the morning Thursday's
    day ahead was finished: the card never listed the row's id in its rids, so its keeper never reached the page)."""
    FF = dict(F, rhythm='rh', event='ev', key='k', target='tg')
    d = tempfile.mkdtemp()
    open(os.path.join(d, 'PXL_20260304_231000000.jpg'), 'wb').write(b'\xff\xd8\xff')
    json.dump({'PXL_20260304_231000000.jpg': 'fidGame0000001'}, open(os.path.join(d, 'index.json'), 'w'))
    rows = [row('r9', '🏀 the game', '2026-03-04T23:00:00.000Z', '2026-03-05T00:30:00.000Z',
                pr='🗓️ calendar event', ph='keeper', pl=link('fidGame0000001'))]
    page = {'events': [{'sort': '2026-03-04T17:00:00', 'when': '5p', 'end': '6:30p', 'title': '🏀 the game',
                        'match': '🏀 the game', 'link': 'https://calendar.example.invalid/event?eid=ZXhhbXBsZQ'}]}
    items = flow.schedule_of(DAY, rows, page, FF, OFF, set())
    card = next(x for x in items if x['k'] == 'event')
    assert not [x for x in items if x['k'] == 'lived'], items           # the row is the event, drawn once
    assert 'r9' in (card.get('rids') or []), card                     # and the card holds its id
    assert flow.photos_onto(items, DAY, rows, FF, OFF, d, me='me') == 1
    assert [p['url'] for p in card['photos']] == [link('fidGame0000001')], card
    print('ok — an event\'s own row, folded onto its card, brings its keeper photo with it')


if __name__ == '__main__':
    main()
