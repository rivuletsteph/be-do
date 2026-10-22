# -*- coding: utf-8 -*-
"""The day's photos, fetched from Drive and made small enough to sit in a page
(22 Oct 2026, her word: photos that piece the day together).

Her phone names every photo by the moment it was taken, in UTC:
PXL_20261020_182005466.jpg is 18:20:05 UTC, 1:20 PM in Texas. The photos sync to
the week's folder, `W## photos` inside the week folder. This reads that folder,
keeps the photos taken on the day (local), and writes each one as a small JPEG
into --out under its own name, so the builder can place it by its time
(week_look_behind.py --photos).

    python3 day_photos.py --day 2026-10-20 --local look_behind_local.json --out photos/
    python3 day_photos.py --day 2026-10-20 --local look_behind_local.json --out photos/ --from originals/

Drive is read with a service account the photo folders are shared with: its JSON
key in BEDO_DRIVE_SA (the key itself) or BEDO_DRIVE_SA_FILE (a path to it). The
key never leaves the session; nothing passes through the chat. --from reads
originals from a local folder instead (the laptop, and the tests).
"""
import argparse, base64, datetime as dt, io, json, os, re, sys, time, urllib.parse, urllib.request

NAME = re.compile(r'^PXL_(\d{8})_(\d{6})\d*.*\.(jpe?g|png)$', re.I)
SIDE, QUALITY = 900, 72          # long side in px; about 100 KB a photo


def taken(name, off):
    """Local capture time from the phone's file name, or None."""
    m = NAME.match(name)
    if not m:
        return None
    t = dt.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')
    return t + dt.timedelta(hours=off)


def small(raw):
    from PIL import Image, ImageOps
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(raw))).convert('RGB')
    im.thumbnail((SIDE, SIDE))
    b = io.BytesIO()
    im.save(b, 'JPEG', quality=QUALITY, optimize=True, progressive=True)
    return b.getvalue()


def token(key):
    """An access token for drive.readonly, signed with the service account's key."""
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    b64 = lambda b: base64.urlsafe_b64encode(b).rstrip(b'=')  # noqa: E731
    now = int(time.time())
    head = b64(json.dumps({'alg': 'RS256', 'typ': 'JWT'}).encode())
    body = b64(json.dumps({'iss': key['client_email'], 'scope': 'https://www.googleapis.com/auth/drive.readonly',
                           'aud': key['token_uri'], 'iat': now, 'exp': now + 3600}).encode())
    pk = serialization.load_pem_private_key(key['private_key'].encode(), password=None)
    sig = b64(pk.sign(head + b'.' + body, padding.PKCS1v15(), hashes.SHA256()))
    data = urllib.parse.urlencode({'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
                                   'assertion': (head + b'.' + body + b'.' + sig).decode()}).encode()
    return json.load(urllib.request.urlopen(key['token_uri'], data, timeout=30))['access_token']


def drive(tok, path, params=None, raw=False):
    url = 'https://www.googleapis.com/drive/v3/' + path + ('?' + urllib.parse.urlencode(params) if params else '')
    r = urllib.request.urlopen(urllib.request.Request(url, headers={'Authorization': 'Bearer ' + tok}), timeout=60)
    return r.read() if raw else json.load(r)


def listing(tok, q):
    out, page = [], None
    while True:
        p = {'q': q, 'fields': 'nextPageToken,files(id,name)', 'pageSize': 1000,
             'supportsAllDrives': 'true', 'includeItemsFromAllDrives': 'true'}
        if page:
            p['pageToken'] = page
        got = drive(tok, 'files', p)
        out += got.get('files', [])
        page = got.get('nextPageToken')
        if not page:
            return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--from', dest='src', help='a local folder of originals, instead of Drive')
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    off, day = L['utc_offset_hours'], dt.date.fromisoformat(a.day)
    os.makedirs(a.out, exist_ok=True)
    keep = lambda n: (taken(n, off) or dt.datetime.min).date() == day  # noqa: E731
    seen, kept = set(), []
    if a.src:
        for n in sorted(os.listdir(a.src)):
            if keep(n) and n not in seen:
                seen.add(n)
                kept.append((n, open(os.path.join(a.src, n), 'rb').read()))
    else:
        raw = os.environ.get('BEDO_DRIVE_SA') or (open(os.environ['BEDO_DRIVE_SA_FILE']).read()
                                                   if os.environ.get('BEDO_DRIVE_SA_FILE') else None)
        if not raw:
            print('NO DRIVE KEY HERE: set BEDO_DRIVE_SA (the service account key) or BEDO_DRIVE_SA_FILE; '
                  'the page builds without photos')
            sys.exit(3)
        tok = token(json.loads(raw))
        sun = day - dt.timedelta(days=(day.weekday() + 1) % 7)
        wk = L['week_zero_number'] + (sun - dt.date.fromisoformat(L['week_zero_sunday'])).days // 7
        folder = (L.get('photos_folder') or 'W{n} photos').format(n=wk)
        found = listing(tok, f"name = '{folder}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false")
        if not found:
            print(f'no folder named {folder!r} shared with the service account; the page builds without photos')
            sys.exit(3)
        for f in listing(tok, f"'{found[0]['id']}' in parents and trashed = false and mimeType contains 'image/'"):
            if keep(f['name']) and f['name'] not in seen:      # the same photo synced twice is one photo
                seen.add(f['name'])
                kept.append((f['name'], drive(tok, 'files/' + f['id'], {'alt': 'media'}, raw=True)))
    for n, b in kept:
        open(os.path.join(a.out, re.sub(r'\.\w+$', '.jpg', n)), 'wb').write(small(b))
    print(json.dumps({'day': a.day, 'photos': len(kept), 'out': a.out}))


if __name__ == '__main__':
    main()
