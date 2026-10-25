# -*- coding: utf-8 -*-
"""The day behind's photo strip (25 Oct 2026): the day's keepers first, the rest
she shared after, a photo on an info row left out, at most five. Every row and
photo is invented.

    python3 plugins/bedo/skills/bedo-look-behind/tests/test_photo_strip.py
"""
import datetime as dt, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import look_behind as LB  # noqa: E402

LB.UTC_OFFSET = dt.timedelta(hours=-5)
DAY = dt.date(2026, 10, 25)


def z(h, m=0):
    return f'2026-10-25T{h + 5:02d}:{m:02d}:00.000Z'


def pxl(h, m):
    return f'PXL_20261025_{h + 5:02d}{m:02d}00123.jpg'


def main():
    tmp = tempfile.mkdtemp()
    fid = '1aBcD3fGhIjKlMnOpQrStUvWxYz012345'
    names = {pxl(9, 12): None,     # breakfast, info: left out
             pxl(15, 0): None,     # nothing near it: shared, so it shows after the keepers
             pxl(17, 1): fid}      # the glimmer, linked at dusk though logged at 6:45
    for n in names:
        open(os.path.join(tmp, n), 'wb').write(b'\xff\xd8 not really a jpeg')
    json.dump({n: i for n, i in names.items() if i}, open(os.path.join(tmp, 'index.json'), 'w'))
    rows = [{'id': 'r1', 'when': z(9, 15), 'practice': '🍽️ breakfast', 'title': '🍽️ toast', 'photo': 'info'},
            {'id': 'r2', 'when': z(18, 45), 'practice': '✨ glimmer', 'title': '✨ Care Bears glass',
             'photo': 'keeper', 'photo_links': LB.bedo_photos.link(fid)},
            {'id': 'r3', 'when': z(9, 0), 'status': '⬜ intention', 'practice': '✨ glimmer', 'title': 'plan'}]
    strip, n = LB.day_photos(tmp, rows, DAY, 'Self', 5)
    assert n == {'read': 3, 'keepers': 1, 'no_row': 1, 'left_out': 1, 'not_drawn': 0}, n
    assert [p['alt'] for p in strip] == ['Care Bears glass', ''], strip
    assert strip[0]['url'] == LB.bedo_photos.link(fid) and strip[0]['thumb'].startswith('data:image/jpeg'), strip[0]
    strip, n = LB.day_photos(tmp, rows, DAY, 'Self', 1)
    assert len(strip) == 1 and n['not_drawn'] == 1, n
    assert LB.day_photos(None, rows, DAY, 'Self', 5)[0] == []
    print('ok — the strip: keepers first, the rest after, info left out, at most five')


if __name__ == '__main__':
    main()
