"""myday.py — the my day page's two cards, from the morning's read.

One page a day (261028_myday): the day ahead in the morning, republished in
place as the day goes, the day behind at the close. This file builds the two
cards the day ahead carries into it, both from the same read as the rest of
the page — nothing drawn by hand:

  where they lead  card 1 (saved 4 Oct 2026): today's steps under the drive or
                   rhythm they serve, drives first, every step shown with her
                   words, each drive's % progress and the line on to its date
                   and destination.
  the whole map    map v3 (saved 5 Oct 2026): every rhythm, and only the drives
                   with a step this week (the rest fold into +N resting); the
                   past shaded, % progress, today's red boxes, the curves into
                   the destinations, tap to follow.

Everything about the person comes from the rows: the rhythms and drives and
destinations from the rhythms table (order by code, colour by code), the steps
and the ground covered from the stream. The map runs from the first day the
read holds to `map_end` in the settings. `rhythm_colours` in the settings may
name a colour for a rhythm; otherwise its code picks one.

It also works out the page itself: the title, named like that day's my day
chat, and the day's own link when today's look ahead row already carries one.
"""
import datetime as dt, re

# The earthy colours of card 1 and the map (her word, 4 Oct 2026: colours kept).
# A rhythm's code number picks one; the engine defines each for light and dark.
COLOURS = ('moss', 'rose', 'ochre', 'water', 'teal', 'plum', 'plum', 'terra', 'clay')
ACTION = '⚡'
WORKING = ('⬜ intention', '▶️ in motion')          # a step on the card is one of these, or done
DONE = '✅ done'
LIVED = ('✅', '◉', '●')                            # a rhythm was tended that day
DIVIDERS = ('———', '---', '——')
URL = re.compile(r'\[([^\]]+)\]\((https?://[^)\s]+)\)|(https?://[^\s)\]<>"]+)')
LOOK_AHEAD = '👁️ look ahead'


def _words(details):
    """(hers, be•do's): her words above the divider, the [be•do] block below."""
    d = details or ''
    for div in DIVIDERS:
        i = d.find(div)
        if i >= 0:
            return d[:i].strip(), d[i + len(div):].replace('[be•do]', '').strip()
    if '[be•do]' in d:
        a, _, b = d.partition('[be•do]')
        return a.strip(), b.strip()
    return d.strip(), ''


def _trim(s, n):
    s = re.sub(r'\s+', ' ', URL.sub(lambda m: m.group(1) or '', s or '')).strip()
    return s if len(s) <= n else s[:n - 3].rsplit(' ', 1)[0] + '…'


def _links(details, deliverable):
    out = []
    if deliverable:
        out.append(dict(l='the deliverable', u=deliverable))
    for m in URL.finditer(details or ''):
        u = m.group(2) or m.group(3)
        if u in [x['u'] for x in out]:
            continue
        lab = m.group(1) or re.sub(r'^https?://(www\.)?', '', u).split('/')[0]
        out.append(dict(l='the email' if 'mail.google' in u else lab, u=u))
    return out[:4]


def _short(name):
    """GLO2 — Dickinson, Jefferson, Cow & Caney → GLO2: the part before the dash, when long."""
    head = name.split(' — ')[0].strip()
    return head if len(name) > 28 and head != name else name


def _code_n(code):
    m = re.search(r'\d+', code or '')
    return int(m.group()) if m else 99


def buckets(drives, local_settings):
    """Every active rhythm and drive by name: kind, glyph, short name, colour,
    parent rhythm, the drive it feeds, its date and destinations."""
    own = local_settings.get('rhythm_colours') or {}
    rhythms = sorted((r for r in drives.values() if r.get('status') == 'active' and 'rhythm' in (r.get('type') or '')),
                     key=lambda r: (_code_n(r.get('code')), r['name']))
    colour = {r['name']: own.get(r['name']) or COLOURS[(_code_n(r.get('code')) - 1) % len(COLOURS)] for r in rhythms}

    def parent_of(r, seen=()):
        if r.get('parent') in colour:
            return r['parent']
        for up in r.get('feeds') or []:
            u = drives.get(up)
            if u and up not in seen:
                p = parent_of(u, seen + (up,))
                if p:
                    return p
        return ''
    out = {}
    for r in rhythms:
        out[r['name']] = dict(k='rhythm', g=r.get('emoji') or '', short=_short(r['name']), c=colour[r['name']])
    for r in drives.values():
        if r.get('status') != 'active' or 'drive' not in (r.get('type') or ''):
            continue
        p = parent_of(r)
        up = next((u for u in r.get('feeds') or [] if (drives.get(u) or {}).get('status') == 'active'), None)
        out[r['name']] = dict(k='drive', g=r.get('emoji') or '', short=_short(r['name']), c=colour.get(p, 'clay'),
                              parent=p, up=up, date=r.get('target'), dest=list(r.get('dest') or []))
    order = [r['name'] for r in rhythms]
    dest = {r['name']: r.get('emoji') or '' for r in drives.values()
            if 'destination' in (r.get('type') or '') and r.get('status') == 'active'}
    return out, order, dest


def _bucket(name, known):
    """The row's drive or rhythm. An older row may name two, comma-separated: the first known one."""
    name = (name or '').strip()
    if name in known or not name:
        return name
    return next((p.strip() for p in name.split(',') if p.strip() in known), name)


def build(rows, latest, open_ids, hidden, today, drives, L, local, chain_key):
    """rows: every row read; latest: the newest row of each chain; open_ids: the
    ids the page's read filter kept (queue, waiting, media, quickies, hidden
    drives set aside); hidden(row): the page's hidden-drive test; local(ts):
    the local clock; chain_key(row): the chain a row belongs to."""
    B, order, dest = buckets(drives, L)
    day = today.isoformat()
    lday = lambda ts: local(ts).date().isoformat() if ts else None

    # the ground covered, from every row read: a finished ⚡ step per chain on a drive,
    # and each day a rhythm or drive was tended (lived, not planned)
    first = min((lday(r['created']) for r in rows), default=day)
    done, tended, since = {}, {}, {}
    for r in rows:
        b = _bucket(r['rhythm'], B)
        if not b:
            continue
        d = lday(r['end'] or r['when'] or r['created'])
        since[b] = min(since.get(b, d), d)
        st = r['status'] or ''
        if st.startswith(LIVED):
            tended.setdefault(b, set()).add((chain_key(r), d))
        if st == DONE and (r['practice'] or '').startswith(ACTION):
            done[(b, chain_key(r))] = d
    opened = {}
    for r in latest.values():
        if r['status'] in WORKING and (r['practice'] or '').startswith(ACTION) and not r['queue']:
            b = _bucket(r['rhythm'], B)
            opened[b] = opened.get(b, 0) + 1
    ndone = {}
    for (b, _), d in done.items():
        ndone[b] = ndone.get(b, 0) + 1
    prog = {b: dict(done=ndone.get(b, 0), open=opened.get(b, 0), since=since.get(b) or first)
            for b in set(ndone) | set(opened)}
    hist = {b: sorted(d for _, d in v) for b, v in tended.items()}
    past = {}
    for (b, _), d in done.items():
        past.setdefault(b, []).append(d)

    # card 1 — today's steps: open ⚡ steps due today, carried in from the last week, or set
    # this morning with no date of their own; and the ones finished today
    steps = []
    for r in latest.values():
        if not (r['practice'] or '').startswith(ACTION) or r['queue'] or r['waiting'] or hidden(r):
            continue
        if r['status'] in WORKING and r['id'] in open_ids:
            if r['target']:
                d = lday(r['target'])
                if d != day and not (d < day and (today - dt.date.fromisoformat(d)).days <= 7):
                    continue
            elif lday(r['created']) == day:
                d = day
            else:
                continue
            s = 'open'
        elif r['status'] == DONE and lday(r['end'] or r['when'] or r['created']) == day:
            d, s = day, 'done'
        else:
            continue
        her, bedo = _words(r['details'])
        steps.append(dict(t=re.sub(r'^⚡\s*', '', r['title'] or '').strip(), rd=_bucket(r['rhythm'], B) or 'no drive',
                          d=d, s=s, det=_trim(her or bedo, 200), mine=bool(her), g=ACTION))
    steps.sort(key=lambda z: (z['d'], z['s'] != 'done', z['t']))

    # the whole map — every open ⚡ step under its drive or rhythm
    acts = {}
    for r in latest.values():
        if r['status'] not in WORKING or not (r['practice'] or '').startswith(ACTION) or r['queue']:
            continue
        d = lday(r['target'])
        her, bedo = _words(r['details'])
        k = r['key'] or ''
        acts.setdefault(_bucket(r['rhythm'], B) or 'no drive', []).append(dict(
            t=re.sub(r'^⚡\s*', '', r['title'] or '').strip(), d=d, w=r['waiting'] or '',
            today=bool((d and d <= day) or (not d and lday(r['created']) == day)), mo=r['status'] == '▶️ in motion',
            add=f'20{k[:2]}-{k[2:4]}-{k[4:6]}' if re.match(r'\d{6}', k) else lday(r['created']),
            her=_trim(her, 280), bedo=_trim(bedo, 280) if not her else '', links=_links(r['details'], r.get('deliverable')),
            per=r['person'] or ''))
    for v in acts.values():
        v.sort(key=lambda a: (not a['today'], a['d'] is None, a['d'] or '', a['t']))
    mdrives = [dict(n=n, g=o['g'], short=o['short'], c=o['c'], date=o['date'], dest=o['dest'], parent=o['parent'],
                    up=o['up'], acts=acts.get(n, []), prog=prog.get(n, {}), past=sorted(past.get(n, [])))
               for n, o in B.items() if o['k'] == 'drive']
    mrhythms = [dict(n=n, g=B[n]['g'], short=B[n]['short'], c=B[n]['c'], acts=acts.get(n, []), past=hist.get(n, []))
                for n in order]
    feeds = [[n, o['up']] for n, o in B.items() if o['k'] == 'drive' and o['up']]
    card = dict(steps=steps, prog=prog, hist=dict(begin=first, ev=hist),
                drives={n: {k: o.get(k) for k in ('g', 'k', 'c', 'short', 'dest', 'date')} for n, o in B.items()},
                dest=dest)
    whole = dict(day=day, begin=first, end=L.get('map_end') or f'{today.year}-12-31', order=order,
                 drives=mdrives, rhythms=mrhythms, feeds=feeds, dest=dest)
    return card, whole


def today_link(rows, today, local, living=''):
    """The day's own page, when today's look ahead row already carries it in
    `deliverable` — the link the day ahead republishes to, and the pieces after
    it (the day's rows and photos, the close). The old living page is not a day's
    own. `row` is today's look ahead row, where a new link is written; None
    before the row exists."""
    url = row = None
    for r in sorted(rows, key=lambda r: r['created']):
        if not (r['practice'] or '').startswith(LOOK_AHEAD) or local(r['created']).date() != today:
            continue
        row = r['id']
        u = (r.get('deliverable') or '').strip()
        if u and u != living:
            url = u
    return dict(url=url, row=row)
