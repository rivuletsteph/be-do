# -*- coding: utf-8 -*-
"""A folder of pictures into a manifest: when each was taken, where, what kind it is, which
are the same picture twice, which are one burst or one run of screenshots, and a small
thumbnail of each so the reader looks at 768 pixels, not 4000. It never judges what a
picture shows; that is for whoever reads the thumbnails. Nothing is moved, renamed or
deleted: the folder is only read.

    python3 photos.py --dir <folder> --out <outdir> [--date 2026-10-20] [--places places.csv]
                      [--tz America/Chicago] [--utc-offset -5]

Per picture:
  time     EXIF DateTimeOriginal (with OffsetTimeOriginal when there is one), else the file
           name: PXL_YYYYMMDD_HHMMSSmmm is UTC, Screenshot_YYYYMMDD-HHMMSS is already local,
           else the file's modified time. time_source says which.
  place    EXIF GPS, decimal degrees to 5 places. With --places (a csv with name, lat and
           lng columns) the nearest place within 150 m is named.
  kind     camera (PXL_ or a camera make and model), screenshot, or other.
  sha256 and a 64-bit difference hash, for sameness.

Sameness:
  duplicate  identical bytes: the one without a " (1)" suffix is kept, the rest are dropped.
  same       same name once " (n)" is stripped and same second: one picture shared twice;
             the copy with a location is kept, else the unsuffixed name.
  group      camera shots within 90 seconds of each other that look alike (hash distance
             12 or less). Nothing is dropped; the reader picks one.
  series     screenshots each within 3 minutes of the one before. Same: nothing dropped.

--date keeps one local day; pictures from other days are listed under other_days, not dropped.
Writes <outdir>/photos.json and <outdir>/thumbs/. needs_look is what to view: every kept
camera photo, a contact sheet for each screenshot series, and each lone screenshot.
"""
import argparse, csv, datetime as dt, hashlib, json, math, os, re, sys

EXTS = ('.jpg', '.jpeg', '.png', '.heic', '.webp')
BURST_SECONDS, BURST_BITS, SERIES_SECONDS, PLACE_METERS = 90, 12, 180, 150
THUMB, SHEET = 768, 1400


def die(m):
    sys.exit('ABORT: ' + m)


def pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        die('Pillow is needed: pip install pillow')
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
    except ImportError:
        pass
    return Image, ImageOps


def zone(name, utc_offset):
    """The named zone, or a fixed offset when this machine has no tz database."""
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(name)
    except Exception:
        return dt.timezone(dt.timedelta(hours=utc_offset))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def dhash(img):
    """64 bits: is each pixel of a 9x8 grayscale darker than its right neighbour."""
    from PIL import Image
    px = list(img.convert('L').resize((9, 8), Image.LANCZOS).tobytes())
    bits = 0
    for y in range(8):
        for x in range(8):
            bits = (bits << 1) | (px[y * 9 + x] < px[y * 9 + x + 1])
    return '%016x' % bits


def hamming(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count('1')


def degrees(vals, ref):
    d = sum(float(v) / 60 ** i for i, v in enumerate(vals))
    return -d if ref in ('S', 'W') else d


def gps(exif):
    g = exif.get_ifd(0x8825) if exif else {}
    try:
        lat, lon = degrees(g[2], g[1]), degrees(g[4], g[3])
    except (KeyError, TypeError, ValueError, ZeroDivisionError):
        return None, None
    # a phone that withholds the position leaves the tags there, blank: not a place
    if g[1] not in ('N', 'S') or g[3] not in ('E', 'W') or not (math.isfinite(lat) and math.isfinite(lon)):
        return None, None
    return round(lat, 5), round(lon, 5)


def offset_of(text):
    m = re.fullmatch(r'([+-])(\d\d):(\d\d)', (text or '').strip())
    if not m:
        return None
    mins = int(m.group(2)) * 60 + int(m.group(3))
    return dt.timezone(dt.timedelta(minutes=-mins if m.group(1) == '-' else mins))


def exif_time(exif, tz):
    sub = exif.get_ifd(0x8769) if exif else {}
    raw = sub.get(0x9003) or (exif.get(0x0132) if exif else None)
    try:
        t = dt.datetime.strptime(str(raw).strip(), '%Y:%m:%d %H:%M:%S')
    except ValueError:
        return None
    return t.replace(tzinfo=offset_of(sub.get(0x9011)) or tz).astimezone(tz)


def name_time(name, tz):
    m = re.match(r'PXL_(\d{8})_(\d{6})', name)
    if m:
        t = dt.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')
        return t.replace(tzinfo=dt.timezone.utc).astimezone(tz), 'filename_utc'
    m = re.match(r'Screenshot_(\d{8})-(\d{6})', name)
    if m:
        t = dt.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')
        return t.replace(tzinfo=tz), 'filename_local'
    return None, None


def kind_of(name, ext, exif):
    if name.startswith('Screenshot_'):
        return 'screenshot'
    if name.startswith('PXL_') or (exif and (exif.get(0x010F) or exif.get(0x0110))):
        return 'camera'
    return 'screenshot' if ext == '.png' else 'other'


def read_places(path):
    """Named places from a csv with name, lat and lng columns (lon and longitude also do)."""
    out = []
    with open(path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            try:
                lat = float(r.get('lat') or r.get('latitude'))
                lon = float(r.get('lng') or r.get('lon') or r.get('longitude'))
            except (TypeError, ValueError):
                continue
            out.append((r.get('name') or r.get('google_name') or '', lat, lon))
    return out


def meters(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2)
    return 2 * 6371000 * math.asin(math.sqrt(a))


def nearest(lat, lon, places):
    best = min(((meters(lat, lon, la, lo), n) for n, la, lo in places), default=None)
    return (best[1], round(best[0])) if best and best[0] <= PLACE_METERS else (None, None)


def inspect(path, tz):
    """One picture's facts, or None when Pillow cannot open it."""
    Image, ImageOps = pillow()
    name = os.path.basename(path)
    ext = os.path.splitext(name)[1].lower()
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            size = im.size
            small = ImageOps.exif_transpose(im).convert('RGB')
            small.thumbnail((256, 256))
            hsh = dhash(small)
    except Exception:
        return None
    t, src = exif_time(exif, tz), 'exif'
    if not t:
        t, src = name_time(name, tz)
    if not t:
        t, src = dt.datetime.fromtimestamp(os.path.getmtime(path), tz), 'file_mtime'
    lat, lon = gps(exif)
    return dict(name=name, local_time=t.isoformat(timespec='seconds'), date=t.date().isoformat(),
                time_source=src, lat=lat, lon=lon, kind=kind_of(name, ext, exif),
                sha256=sha256(path), dhash=hsh, width=size[0], height=size[1],
                bytes=os.path.getsize(path), place=None, place_m=None, group=None, series=None)


def dedupe(files):
    """Identical bytes: keep the name with no ' (1)' suffix, else the earliest name."""
    keep, dropped, by = [], [], {}
    for f in sorted(files, key=lambda f: f['name']):
        by.setdefault(f['sha256'], []).append(f)
    for same in by.values():
        plain = [f for f in same if not re.search(r' \(\d+\)$', os.path.splitext(f['name'])[0])]
        first = (plain or same)[0]
        keep.append(first)
        dropped += [dict(name=f['name'], why='exact duplicate of ' + first['name']) for f in same if f is not first]
    return keep, dropped


def same_picture(files):
    """Same name bar a ' (n)' suffix and same second: keep the one with GPS, else the plain name."""
    keep, dropped, by = [], [], {}
    for f in files:
        base = re.sub(r' \(\d+\)$', '', os.path.splitext(f['name'])[0]).lower()
        by.setdefault((base, f['local_time']), []).append(f)
    for same in by.values():
        pick = sorted(same, key=lambda f: (f['lat'] is None, bool(re.search(r' \(\d+\)\.\w+$', f['name'])), f['name']))[0]
        keep.append(pick)
        why = 'has location' if pick['lat'] is not None and any(f['lat'] is None for f in same) else 'original name'
        dropped += [dict(name=f['name'], why=f"same picture, kept {pick['name']} ({why})") for f in same if f is not pick]
    return keep, dropped


def chains(items, joined):
    """Runs of items (in time order) where each is joined to the one before."""
    runs = []
    for f in sorted(items, key=lambda f: f['local_time']):
        if runs and joined(runs[-1][-1], f):
            runs[-1].append(f)
        else:
            runs.append([f])
    return runs


def seconds(a, b):
    return abs((dt.datetime.fromisoformat(b['local_time']) - dt.datetime.fromisoformat(a['local_time'])).total_seconds())


def bursts(files):
    cams = [f for f in files if f['kind'] == 'camera']
    runs = chains(cams, lambda a, b: seconds(a, b) <= BURST_SECONDS and hamming(a['dhash'], b['dhash']) <= BURST_BITS)
    return [r for r in runs if len(r) > 1]


def serieses(files):
    shots = [f for f in files if f['kind'] == 'screenshot']
    return [r for r in chains(shots, lambda a, b: seconds(a, b) <= SERIES_SECONDS) if len(r) > 1]


def thumb(src, dst, edge):
    Image, ImageOps = pillow()
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        im.thumbnail((edge, edge))
        im.save(dst, 'JPEG', quality=80)


def sheet(paths, dst):
    """Members tiled in a square-ish grid, long edge about SHEET."""
    Image, _ = pillow()
    cols = math.ceil(math.sqrt(len(paths)))
    rows = math.ceil(len(paths) / cols)
    cw, ch = SHEET // cols, SHEET // max(cols, rows)
    canvas = Image.new('RGB', (cw * cols, ch * rows), 'white')
    for i, p in enumerate(paths):
        with Image.open(p) as im:
            im = im.convert('RGB')
            im.thumbnail((cw - 4, ch - 4))
            canvas.paste(im, ((i % cols) * cw + 2, (i // cols) * ch + 2))
    canvas.save(dst, 'JPEG', quality=80)


def build(folder, out, date=None, places=None, tz=None):
    tz = tz or zone('America/Chicago', -5)
    names = [n for n in sorted(os.listdir(folder))
             if n.lower().endswith(EXTS) and os.path.isfile(os.path.join(folder, n))]
    found = [inspect(os.path.join(folder, n), tz) for n in names]
    files, dropped = dedupe([f for f in found if f])
    files, again = same_picture(files)
    dropped += again
    dropped += [dict(name=n, why='unreadable') for n, f in zip(names, found) if f is None]
    other = [dict(name=f['name'], date=f['date']) for f in files if date and f['date'] != date]
    files = sorted([f for f in files if not date or f['date'] == date], key=lambda f: f['local_time'])
    pl = read_places(places) if places else []
    for f in files:
        if f['lat'] is not None and pl:
            f['place'], f['place_m'] = nearest(f['lat'], f['lon'], pl)
    groups = [dict(id='g%d' % i, files=[f['name'] for f in r]) for i, r in enumerate(bursts(files), 1)]
    series = [dict(id='s%d' % i, files=[f['name'] for f in r]) for i, r in enumerate(serieses(files), 1)]
    by = {f['name']: f for f in files}
    for g in groups + series:
        for n in g['files']:
            by[n]['group' if g['id'][0] == 'g' else 'series'] = g['id']
    os.makedirs(os.path.join(out, 'thumbs'), exist_ok=True)
    for f in files:
        f['thumb'] = 'thumbs/' + os.path.splitext(f['name'])[0] + '.jpg'
        thumb(os.path.join(folder, f['name']), os.path.join(out, f['thumb']), THUMB)
    for g in groups + series:
        g['sheet'] = 'thumbs/' + g['id'] + '.jpg'
        sheet([os.path.join(out, by[n]['thumb']) for n in g['files']], os.path.join(out, g['sheet']))
    look = [f['thumb'] for f in files if f['kind'] == 'camera']
    look += [s['sheet'] for s in series]
    look += [f['thumb'] for f in files if f['kind'] == 'screenshot' and not f['series']]
    return dict(date=date, tz=str(tz), folder=folder, files=files, groups=groups, series=series,
                dropped=dropped, other_days=other, needs_look=look)


def summary(m):
    lines = [f"{len(m['files'])} kept, {len(m['dropped'])} dropped, {len(m['other_days'])} from other days; "
             f"{len(m['groups'])} bursts, {len(m['series'])} screenshot series; {len(m['needs_look'])} to look at"]
    for f in m['files']:
        where = f['place'] or (f"{f['lat']}, {f['lon']}" if f['lat'] is not None else 'no gps')
        lines.append(f"{f['local_time'][11:]}  {f['kind']:<10} {where:<24} {f['group'] or f['series'] or '-':<3} {f['name']}")
    lines += [f"dropped {d['name']}: {d['why']}" for d in m['dropped']]
    lines += [f"other day {o['date']}: {o['name']}" for o in m['other_days']]
    return '\n'.join(lines)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dir', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--date')
    ap.add_argument('--places')
    ap.add_argument('--tz', default='America/Chicago')
    ap.add_argument('--utc-offset', type=float, default=-5, help='hours, when the tz database is missing')
    a = ap.parse_args()
    if not os.path.isdir(a.dir):
        die('no such folder: ' + a.dir)
    m = build(a.dir, a.out, a.date, a.places, zone(a.tz, a.utc_offset))
    with open(os.path.join(a.out, 'photos.json'), 'w', encoding='utf-8') as f:
        json.dump(m, f, indent=1, ensure_ascii=False)
    print(summary(m))


if __name__ == '__main__':
    main()
