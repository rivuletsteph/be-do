# -*- coding: utf-8 -*-
"""Photos: which kind a row's photo is, which file in the week's folder is its
photo, and where each photo sits on a page (25 Oct 2026, her words: the photos
she shares are keepers or information, and the keepers show on the look behind).

Two kinds, in the stream's `photo` field:

  keeper  a moment she wants to capture and hold on to — shown on the pages
  info    the photo only carried what the row needed (food on its own, a pill,
          a screen, a receipt) — the row keeps the information, the pages
          leave the photo out

A row from before the field carries the old checkbox (`photo_checked`) or says
*from her photo* in its details; it is sorted by rule (`rule_kind`). The chat
that logs a photo sets the kind itself, and her word overrides either way.

The phone names every photo by the moment it was taken, in UTC
(PXL_20261020_182005466.jpg). She shares the day's photos into the week's
`W## photos` folder; at dusk `match` gives each photo row its file (written to
`photo_links`), so a page can place the photo on its row even when she shared
it in the chat long after she took it. A file no row links falls back to its
time (`place`). Before that, `dedupe` finds the same photo shared twice (one
name, one size) and names the extra copies for the Drive trash.

Rows carry logical names: practice, title, person, details, photo,
photo_checked, photo_links, and `_a` / `_b` (local start and end datetimes)
for matching and placing.
"""
import datetime as dt, re

from bedo_reader import FACTS

P = FACTS['photos']
KEEPER, INFO = P['kinds']['keeper'], P['kinds']['info']
FOOD = set(P['food_practices'])
INFO_PRACTICES = set(P['info_practices']) | set(FACTS['garden'].get('photo_skip_practices') or [])
INFO_RX = re.compile(P['info_pattern'])
FOOD_KEEPER_RX = re.compile(P['food_keeper_pattern'], re.I)
FROM_PHOTO = re.compile(r'[Ff]rom (?:her|the same) photo')
NAME = re.compile(P['phone_name'], re.I)
SCREEN = re.compile(P.get('screen_name') or r'^Screenshot_(\d{8})-(\d{6}).*\.(jpe?g|png)$', re.I)
LINK_ID = re.compile(r'/d/([\w-]{10,})|[?&]id=([\w-]{10,})')
MAX_SPAN = dt.timedelta(hours=FACTS['entry_rules']['max_span_hours'])


def word(practice):
    """'🍽️ breakfast' → 'breakfast'."""
    return re.sub(r'\s+', ' ', re.sub(r'^[^\w]+', '', (practice or '').strip())).lower()


def taken(name, off):
    """Local capture time from the phone's file name, or None."""
    m = NAME.match(name or '')
    if m:
        return dt.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S') + dt.timedelta(hours=off)
    m = SCREEN.match(name or '')      # a screenshot is named in her own clock, not UTC (30 Oct 2026)
    if m:
        return dt.datetime.strptime(m.group(1) + m.group(2), '%Y%m%d%H%M%S')
    return None


def is_screenshot(name):
    return bool(SCREEN.match(name or ''))


def has_photo(r):
    k = r.get('photo')
    return bool(k) or bool(r.get('photo_checked')) or bool(FROM_PHOTO.search(r.get('details') or ''))


def rule_kind(r, me=''):
    """The kind a row's photo would be given by rule, when nobody set it."""
    pr = word(r.get('practice'))
    if pr in INFO_PRACTICES or INFO_RX.search(pr):
        return INFO
    if pr in FOOD:
        others = [p.strip() for p in (r.get('person') or '').split(',') if p.strip() and p.strip() != me]
        return KEEPER if others or FOOD_KEEPER_RX.search(r.get('title') or '') else INFO
    return KEEPER


def kind(r, me=''):
    """keeper, info, or None when the row was not read from a photo."""
    k = r.get('photo')
    if k in (KEEPER, INFO):
        return k
    return rule_kind(r, me) if has_photo(r) else None


def link(file_id):
    return 'https://' + P['drive_host'] + P['drive_path'].format(id=file_id)


def linked(r):
    """The Drive file ids in a row's photo links, in order."""
    return [a or b for a, b in LINK_ID.findall(r.get('photo_links') or '')]


def files_from(listing):
    """A folder listing as [{id, name}]: a list, {"files": […]}, or a Drive
    connector result (whose name may arrive as `title`). A file's size and the
    time it reached Drive ride along as `size` and `created` when the listing
    has them (dedupe needs both)."""
    if isinstance(listing, dict):
        listing = listing.get('files') or listing.get('items') or listing.get('results') or []
    out = []
    for f in listing or []:
        name = f.get('name') or f.get('title') or ''
        fid = f.get('id') or f.get('fileId') or ''
        if name and fid:
            x = {'id': fid, 'name': name}
            size = f.get('size', f.get('fileSize'))
            if size not in (None, ''):
                x['size'] = int(size)
            created = f.get('created') or f.get('createdTime')
            if created:
                x['created'] = created
            out.append(x)
    return out


def _created(f):
    return dt.datetime.fromisoformat(f['created'].replace('Z', '+00:00'))


def dedupe(files, linked_ids=()):
    """The same photo in the folder twice (28 Oct 2026: a re-upload doubles
    the week): copies with one name and one size are one photo. The copy a
    stream row links to is kept — every linked copy, so no link breaks — else
    the oldest; the rest are extra. A file the listing gives no size is never
    grouped, and a group with no link and no upload times is left alone.

    Returns {'files': the listing without the extras, in its order,
    'groups': [{name, size, keep: [files], trash: [files], why}],
    'trash': [files], 'unsure': [groups]}. Nothing is trashed here; the chat
    trashes `trash` with the Drive connector on her yes."""
    linked_ids = set(linked_ids)
    listing = files_from(files)
    by = {}
    for f in listing:
        if 'size' in f:
            by.setdefault((f['name'], f['size']), []).append(f)
    out = {'groups': [], 'trash': [], 'unsure': []}
    for (name, size), copies in by.items():
        if len(copies) < 2:
            continue
        keep = [f for f in copies if f['id'] in linked_ids]
        why = 'linked'
        if not keep:
            if not all(f.get('created') for f in copies):
                out['unsure'].append({'name': name, 'size': size, 'copies': copies})
                continue
            keep, why = [min(copies, key=_created)], 'oldest'
        trash = [f for f in copies if f not in keep]
        out['groups'].append({'name': name, 'size': size, 'keep': keep, 'trash': trash, 'why': why})
        out['trash'] += trash
    gone = {f['id'] for f in out['trash']}
    out['files'] = [f for f in listing if f['id'] not in gone]
    out['groups'].sort(key=lambda g: g['name'])
    return out


def near(rows, t, seconds=None):
    """Rows logged within a few minutes of t, or spanning it (at most 12 h)."""
    s = P['near_seconds'] if seconds is None else seconds
    return [r for r in rows if r.get('_a') and r['_a'].date() == t.date()
            and (abs((r['_a'] - t).total_seconds()) <= s
                 or (r.get('_b') and r['_a'] <= t <= r['_b'] and r['_b'] - r['_a'] <= MAX_SPAN))]


def match(rows, files, off, me=''):
    """Dusk: each photo row with no link gets the file taken nearest before its
    time (match_before_minutes back, match_after_minutes ahead), each file once.

    Returns {'links': [...], 'kinds': [...], 'missing': [...], 'unlogged': [...]}:
    links to write (row id, file id, name, the link), kinds to write for rows
    sorted by rule, keepers with no file in the folder yet, and folder photos
    no row explains (a clue for the day's QA)."""
    before = dt.timedelta(minutes=P['match_before_minutes'])
    after = dt.timedelta(minutes=P['match_after_minutes'])
    pics = sorted(({'id': f['id'], 'name': f['name'], 't': taken(f['name'], off)} for f in files_from(files)),
                  key=lambda f: f['t'] or dt.datetime.min)
    pics = [f for f in pics if f['t']]
    seen, uniq = set(), []
    for f in pics:                                   # the same photo synced twice is one photo
        if f['name'] not in seen:
            seen.add(f['name'])
            uniq.append(f)
    pics = uniq
    claimed = {i for r in rows for i in linked(r)}
    out = {'links': [], 'kinds': [], 'missing': [], 'unlogged': []}
    for r in sorted((r for r in rows if r.get('_a') and has_photo(r)), key=lambda r: r['_a']):
        k = kind(r, me)
        if r.get('photo') not in (KEEPER, INFO):
            out['kinds'].append({'id': r['id'], 'title': r.get('title') or '', 'kind': k})
        if linked(r):
            continue
        cands = [f for f in pics if f['id'] not in claimed and -after <= r['_a'] - f['t'] <= before]
        if not cands:
            if k == KEEPER:
                out['missing'].append({'id': r['id'], 'title': r.get('title') or '', 'at': r['_a']})
            continue
        f = min(cands, key=lambda f: (f['t'] > r['_a'], abs((r['_a'] - f['t']).total_seconds())))
        claimed.add(f['id'])
        out['links'].append({'id': r['id'], 'title': r.get('title') or '', 'kind': k, 'file': f['id'],
                             'name': f['name'], 'taken': f['t'], 'url': link(f['id'])})
    lived = [r for r in rows if r.get('_a')]
    for f in pics:
        if f['id'] not in claimed and not near(lived, f['t']):
            out['unlogged'].append({'file': f['id'], 'name': f['name'], 'taken': f['t']})
    return out


def place(rows, photos, me='', prefer=None):
    """Each photo onto its row: the row whose photo links name its file, else
    the row logged at that minute or spanning it (`prefer` orders the
    candidates, called with the row and the photo's time; nearest first by
    default). A photo whose row is info — set so,
    or by rule for a row that never said — is left out. photos: [(taken,
    file_id or None, src)].

    Returns (placed, left_out): placed is [{t, src, file, row, keeper}] in the order
    given, row None when no row explains the photo, keeper True when its row
    holds it as a keeper."""
    by_file = {i: r for r in rows for i in linked(r)}
    placed, left = [], 0
    for t, fid, src in photos:
        best = by_file.get(fid) if fid else None
        if best is None:
            cands = near(rows, t)
            key = (lambda r: prefer(r, t)) if prefer else (lambda r: abs((r['_a'] - t).total_seconds()))  # noqa: E731
            best = min(cands, key=key) if cands else None
        k = (kind(best, me) or rule_kind(best, me)) if best is not None else None
        if k == INFO:
            left += 1
            continue
        placed.append({'t': t, 'src': src, 'file': fid, 'row': best, 'keeper': best is not None and kind(best, me) == KEEPER})
    return placed, left
