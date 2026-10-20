# -*- coding: utf-8 -*-
"""Photos into a manifest, over a few tiny invented pictures. A camera shot with an EXIF time
and a position south and west of the origin; its byte-identical copy "x (1).jpg" is
dropped and the plain name kept; two near-identical shots seconds apart become one group;
Pixel and Screenshot names with no EXIF take their time from the name (Pixel is UTC);
screenshots minutes apart become one series; a place is named within 150 m and not beyond;
a picture from another day is listed, not dropped.

    python3 tests/test_photos.py
"""
import csv, datetime as dt, json, os, random, shutil, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import photos  # noqa: E402
from PIL import Image  # noqa: E402

TZ = dt.timezone(dt.timedelta(hours=-5))


def noise(seed, size=(48, 48)):
    r = random.Random(seed)
    im = Image.new('RGB', size)
    im.putdata([(r.randrange(256), r.randrange(256), r.randrange(256)) for _ in range(size[0] * size[1])])
    return im


def exif_for(when, lat=None, lon=None, make=None):
    ex = Image.Exif()
    if make:
        ex[0x010F] = make
    ex[0x8769] = {0x9003: when, 0x9011: '-05:00'}
    if lat is not None:
        ex[0x8825] = {1: 'S' if lat < 0 else 'N', 2: (abs(lat), 0.0, 0.0),
                      3: 'W' if lon < 0 else 'E', 4: (abs(lon), 0.0, 0.0)}
    return ex


def main():
    tmp = tempfile.mkdtemp()
    src, out = os.path.join(tmp, 'in'), os.path.join(tmp, 'out')
    os.makedirs(src)
    p = lambda n: os.path.join(src, n)
    a = noise(1)
    a.save(p('x.jpg'), exif=exif_for('2026:10:20 09:15:00', -10.0, -20.0, 'Acme'))
    shutil.copy(p('x.jpg'), p('x (1).jpg'))
    # the same picture shared twice: the suffixed copy has a location, so it is kept
    noise(4).save(p('IMG_7.jpg'), exif=exif_for('2026:10:20 11:00:00'))
    noise(4, (49, 48)).save(p('IMG_7 (1).jpg'), exif=exif_for('2026:10:20 11:00:00', -10.0, -20.0))
    b = noise(2)
    b.save(p('PXL_20261020_143524840.jpg'))
    b2 = b.copy()
    b2.putpixel((0, 0), (0, 0, 0))
    b2.save(p('PXL_20261020_143540100.jpg'))
    for i, n in enumerate(['Screenshot_20261020-081651.png', 'Screenshot_20261020-081800.png']):
        noise(10 + i).save(p(n))
    noise(20).save(p('Screenshot_20261020-120000.png'))
    noise(3).save(p('PXL_20261019_130000000.jpg'))
    mtime = noise(30)
    mtime.save(p('plain.jpg'))
    near, far = (10.0, 20.0), (10.01, 20.0)
    places = os.path.join(tmp, 'places.csv')
    with open(places, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        w.writerow(['place_id', 'name', 'lat', 'lng'])
        w.writerow(['p1', 'Test Cafe', near[0], near[1]])
        w.writerow(['p2', 'Far Park', far[0], far[1]])
    before = sorted(os.listdir(src))

    m = photos.build(src, out, '2026-10-20', places, TZ)
    by = {f['name']: f for f in m['files']}

    x = by['x.jpg']
    assert x['local_time'] == '2026-10-20T09:15:00-05:00' and x['time_source'] == 'exif', x
    assert (x['lat'], x['lon']) == (-10.0, -20.0) and x['kind'] == 'camera', x
    assert 'x (1).jpg' not in by and {'name': 'x (1).jpg', 'why': 'exact duplicate of x.jpg'} in m['dropped'], m['dropped']
    assert x['place'] is None, x          # south-west of the invented places

    assert 'IMG_7.jpg' not in by and by['IMG_7 (1).jpg']['lat'] == -10.0, by.keys()
    assert {'name': 'IMG_7.jpg', 'why': 'same picture, kept IMG_7 (1).jpg (has location)'} in m['dropped'], m['dropped']

    pxl = by['PXL_20261020_143524840.jpg']
    assert pxl['local_time'] == '2026-10-20T09:35:24-05:00' and pxl['time_source'] == 'filename_utc', pxl
    assert pxl['lat'] is None and pxl['kind'] == 'camera'
    assert len(m['groups']) == 1 and sorted(m['groups'][0]['files']) == \
        ['PXL_20261020_143524840.jpg', 'PXL_20261020_143540100.jpg'], m['groups']
    assert pxl['group'] == 'g1' and by['x.jpg']['group'] is None

    s1 = by['Screenshot_20261020-081651.png']
    assert s1['local_time'] == '2026-10-20T08:16:51-05:00' and s1['time_source'] == 'filename_local', s1
    assert s1['kind'] == 'screenshot' and len(m['series']) == 1 and len(m['series'][0]['files']) == 2, m['series']
    assert by['Screenshot_20261020-120000.png']['series'] is None

    assert by['plain.jpg']['time_source'] == 'file_mtime' and by['plain.jpg']['kind'] == 'other'
    assert m['other_days'] == [{'name': 'PXL_20261019_130000000.jpg', 'date': '2026-10-19'}], m['other_days']

    look = m['needs_look']
    assert 'thumbs/x.jpg' in look and 'thumbs/s1.jpg' in look and 'thumbs/Screenshot_20261020-120000.jpg' in look, look
    assert 'thumbs/Screenshot_20261020-081651.jpg' not in look
    for t in look:
        assert os.path.exists(os.path.join(out, t)), t
    assert sorted(os.listdir(src)) == before, 'the folder was touched'

    # place: 100 m north of the cafe is named, 300 m is not
    for lat, want in ((10.0009, 'Test Cafe'), (10.003, None)):
        d = os.path.join(tmp, 'g')
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        noise(5).save(os.path.join(d, 'g.jpg'), exif=exif_for('2026:10:20 10:00:00', lat, 20.0))
        f = photos.build(d, os.path.join(tmp, 'gout'), None, places, TZ)['files'][0]
        assert f['place'] == want and (want is None) == (f['place_m'] is None), (lat, f)
        assert want is None or 90 < f['place_m'] < 110, f

    json.dumps(m)
    shutil.rmtree(tmp, ignore_errors=True)
    print('ok — times from exif and names, signed gps, duplicate dropped, burst and series grouped, places within 150 m, other days listed')


if __name__ == '__main__':
    main()
