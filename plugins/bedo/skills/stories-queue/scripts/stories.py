# -*- coding: utf-8 -*-
"""The weekly Stories page: the stories queue as a page to use, by app.

Four steps, each its own subcommand. Nothing personal lives here: titles, her
words, people and links come from the stories base; **which apps and services
she uses comes only from her settings** (the `stories_local` row of the
settings table, read live, never this repo: a list of someone's services is a
map to their logins); the moods and groups come from the week's spec, which
lives in the scratchpad.

    python3 stories.py draft   --stories stories.json --out spec.json [--today YYYY-MM-DD]
    python3 stories.py images  --spec spec.json --img img/            # fetch, resize, credit
    python3 stories.py build   --spec spec.json --out stories-YYMMDD.html
    python3 stories.py readback --db items.json --stories stories.json --out plan.json

Every step takes `--local stories_local.json`; without it the settings row is
read live (`bedo_settings`), and with neither every card goes to Elsewhere.
Its shape is `assets/stories_local.example.json`.

`stories.json` is the base's records as the REST API or the connector returns
them: a list (or {records: [...]}) of {id, fields: {title, kind, standing,
source, notes, people, due, ...}}, fields by name.

draft    every want and in-motion row (news excluded: short reads stay in the
         Morning Gate) as a card: its app guessed from the source and notes,
         the link that opens that app, a score, why it is on the list (her own
         first line), the image query; the 2 or 3 to pick back up, ranked; and
         empty rhythm and watch groups for the chat to fill.
images   one real image per card: an app's own embed cover or thumbnail when
         its settings name one, else a poster from Wikipedia for a movie,
         TVmaze for a show, Open Library (then Google Books) for a book, then
         the linked page's own preview image. Saved as img/<id>.jpg and
         resized; credits go back into the spec. The artifact's CSP blocks
         outside images, so they ship with it.
build    the page, with its live layer: tap to mark started, finished or
         dropped, and an optional thought, kept in the page's db.
readback the page's db against the base: the patches that close finished rows,
         move started ones to in motion, drop dropped ones and append thoughts,
         and the episodes to take off the podcast app's saved list. Prints the
         plan; the chat writes it through the connectors.
"""
import argparse, datetime as dt, html, io, json, os, re, subprocess, sys, time
import urllib.error, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), 'assets')
UA = 'stories-queue/1.0 (a personal reading and watch list page)'
OPEN = ('want', 'in motion')
SKIP_KINDS = ('📰 news',)

# The apps come from her settings, in page order. Each entry:
#   app, label (the shelf's name), glyph   what the page shows
#   match        a regex that finds the app in a row's source or notes
#   kinds        the fallback: a row of this kind whose notes name no app
#   only_kinds   the app holds only these kinds (a podcast app, a reading app)
#   open         the app's search link, {q} for the title (an https universal link)
#   link_rx      a link that opens this app; only_store: true keeps other links out
#   oembed       an oEmbed endpoint for a link_rx link's cover, {url}
#   id_rx, thumb a video id from a link_rx link and its thumbnail, {id}
#   remove_rx, remove_uri   finished episodes to take off the app's saved list
ELSEWHERE = {'app': 'Elsewhere', 'label': 'Elsewhere', 'glyph': '·', 'match': r'\$\d',
             'kinds': ['🎥 movie', '📺 show', '📼 video'],
             'open': 'https://www.google.com/search?q={q}+where+to+watch',
             'note': 'not on your apps: rent, a free app, or not streaming yet'}
APPS, APP_BY_NAME = [ELSEWHERE], {'Elsewhere': ELSEWHERE}


def set_apps(local):
    """Load the apps from the settings (a dict, a file path, or None: read live)."""
    global APPS, APP_BY_NAME
    if isinstance(local, str):
        with open(local, encoding='utf-8') as fh:
            local = json.load(fh)
    if local is None:
        try:
            sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'core'))
            import bedo_settings
            local, why = bedo_settings.fetch('stories_local')
            if local is None:
                print(f'settings: no stories_local ({why}); every card goes to Elsewhere', file=sys.stderr)
        except Exception as e:                      # noqa: BLE001 — the build must not stop here
            print(f'settings: stories_local not read ({e}); every card goes to Elsewhere', file=sys.stderr)
    apps = [dict(x) for x in (local or {}).get('apps', []) if x.get('app') and x['app'] != 'Elsewhere']
    extra = (local or {}).get('elsewhere') or {}
    APPS = apps + [dict(ELSEWHERE, **extra)]
    APP_BY_NAME = {x['app']: x for x in APPS}
    return APPS


SHAPE = {'🎥 movie': 'poster', '📺 show': 'poster', '📗 book': 'poster', '🎧 audiobook': 'square',
         '🎙️ podcast': 'wide', '🎧 podcast': 'wide', '📼 video': 'wide'}
STATUS = {'want': 'Want', 'in motion': 'Started', 'finished': 'Finished', 'dropped': 'Dropped'}
MONTHS = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()


# ---------------------------------------------------------------- reading rows
def load_records(path):
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)
    recs = d.get('records', d) if isinstance(d, dict) else d
    out = []
    for r in recs:
        f = r.get('fields') or r.get('cellValuesByFieldId') or {}
        out.append({'id': r['id'], 'fields': {k: _plain(v) for k, v in f.items()}})
    return out


def _plain(v):
    """A connector cell ({name: …} for a select) as the REST API's plain value."""
    if isinstance(v, dict) and 'name' in v:
        return v['name']
    return v


def split_notes(notes):
    """(her words, be•do's words): the notes split at the one divider."""
    t = notes or ''
    m = re.search(r'^\s*(———|---)\s*$', t, flags=re.M)
    if not m:
        return (t.strip(), '') if not t.lstrip().startswith('[be•do]') else ('', t.strip())
    return t[:m.start()].strip(), t[m.end():].strip()


def first_line(text, n=150):
    t = re.sub(r'\s+', ' ', re.sub(r'\[[^\]]*\]\([^)]*\)|https?://\S+', '', text or '')).strip()
    t = re.sub(r'^\[be•do\]\s*', '', t)
    if not t:
        return ''
    cut = re.split(r'(?<=[.!?])\s', t)[0]
    if len(cut) > n:
        cut = cut[:n].rsplit(' ', 1)[0] + '…'
    return cut


def clean_title(t):
    """The title as a person would say it: drop the queue's asides after a dash."""
    t = re.sub(r'\s+\([^)]*\)$', '', t or '')
    return re.split(r'\s+[—–]\s+', t)[0].strip()


def subtitle(t):
    parts = re.split(r'\s+[—–]\s+', t or '', maxsplit=1)
    return parts[1].strip() if len(parts) > 1 else ''


def guess_app(f):
    text = ' '.join(str(f.get(k) or '') for k in ('source', 'notes', 'title')).lower()
    kind = f.get('kind') or ''
    for a in APPS[:-1]:
        if a.get('match') and re.search(a['match'], text, re.I):
            if a.get('only_kinds') and kind not in a['only_kinds']:
                continue
            return a['app']
    if re.search(APPS[-1]['match'], text, re.I):
        return 'Elsewhere'
    for a in APPS:
        if kind in a.get('kinds', []):
            return a['app']
    return 'Elsewhere'


def score_of(f):
    m = re.search(r'\bRT\s*(\d{1,3})%', f.get('notes') or '')
    return f'RT {m.group(1)}%' if m else ''


def row_links(f):
    src = (f.get('source') or '').strip()
    urls = ([src] if src else []) + re.findall(r'https?://[^\s)\]]+', f.get('notes') or '')
    return [u for u in urls if 'mail.google.com' not in u]


def link_for(f, app):
    """The row's own link when it opens the app, else the app's search."""
    a = APP_BY_NAME.get(app, APPS[-1])
    for u in row_links(f):
        if a.get('link_rx'):
            if re.search(a['link_rx'], u):
                return u
            if a.get('only_store'):
                continue                   # a podcast or blog about a book is not the book
        if not any(o.get('only_store') or o.get('oembed') or o.get('thumb')
                   for o in APPS if o.get('link_rx') and re.search(o['link_rx'], u)):
            return u                       # a link that belongs to another app stays with it
    q = urllib.parse.quote_plus(clean_title(f.get('title')))
    return a['open'].format(q=q)


DATE_RX = re.compile(r'\((\d{1,2}) (' + '|'.join(MONTHS) + r')\)|\b(\d{1,2}) (' + '|'.join(MONTHS)
                     + r')\b|\b(' + '|'.join(MONTHS) + r') (\d{1,2})\b')


def last_touch(f, year):
    """The latest date the notes mention: the best sign of when it was last picked up."""
    best = None
    for m in DATE_RX.finditer(f.get('notes') or ''):
        g = m.groups()
        day, mon = (g[0], g[1]) if g[0] else (g[2], g[3]) if g[2] else (g[5], g[4])
        try:
            d = dt.date(year, MONTHS.index(mon) + 1, int(day))
        except ValueError:
            continue
        best = max(best, d) if best else d
    return best


def rank_pickup(recs, today):
    """In-motion rows, most worth picking back up first: a due date coming
    (a library loan) leads, then the most recently touched."""
    rows = []
    for r in recs:
        f = r['fields']
        if f.get('standing') != 'in motion' or f.get('kind') in SKIP_KINDS:
            continue
        due = f.get('due')
        due_d = dt.date.fromisoformat(due[:10]) if due else None
        touch = last_touch(f, today.year)
        if touch and touch > today:
            touch = touch.replace(year=today.year - 1)
        soon = due_d is not None and 0 <= (due_d - today).days <= 21
        rows.append((0 if soon else 1, -(touch or dt.date(2000, 1, 1)).toordinal(), r['id']))
    return [i for *_, i in sorted(rows)]


def card_of(r, today):
    f = r['fields']
    app = guess_app(f)
    hers, ours = split_notes(f.get('notes'))
    kind = f.get('kind') or ''
    return {
        'title': clean_title(f.get('title')),
        'sub': subtitle(f.get('title')),
        'kind': kind,
        'standing': f.get('standing'),
        'app': app,
        'link': link_for(f, app),
        'score': score_of(f),
        'why': first_line(hers) or '',
        'what': '',
        'meta': '',
        'people': f.get('people') or '',
        'due': (f.get('due') or '')[:10],
        'shape': SHAPE.get(kind, 'poster'),
        'image': '',
        'image_q': {'title': clean_title(f.get('title')), 'author': subtitle(f.get('title')),
                    'kind': kind, 'source': f.get('source') or ''},
        'credit': '',
        'about': first_line(ours, 220),
    }


def cmd_draft(a):
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    recs = load_records(a.stories)
    items, finished = {}, []
    for r in recs:
        f = r['fields']
        if f.get('kind') in SKIP_KINDS:
            continue
        if f.get('standing') in OPEN:
            items[r['id']] = card_of(r, today)
        elif f.get('standing') == 'finished':
            finished.append(r['id'])
    iso = today.isocalendar()
    start = today - dt.timedelta(days=(today.weekday() + 1) % 7)       # the week runs Sunday to Saturday
    end = start + dt.timedelta(days=6)
    spec = {
        'week': f'W{iso[1]}',
        'dates': f'{start.day} {MONTHS[start.month - 1]} – {end.day} {MONTHS[end.month - 1]}',
        'made': today.isoformat(),
        'items': items,
        'pickup': rank_pickup(recs, today)[:3],
        'rhythm': [{'days': 'weekday', 'label': 'a weekday', 'moods': []},
                   {'days': 'sat', 'label': 'Saturday', 'moods': []},
                   {'days': 'sun', 'label': 'Sunday', 'moods': []}],
        'watch': [],
        'finished': finished[-8:],
    }
    with open(a.out, 'w', encoding='utf-8') as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    by = {}
    for i in items.values():
        by[i['app']] = by.get(i['app'], 0) + 1
    print(f'{len(items)} cards · ' + ' · '.join(f'{k} {v}' for k, v in by.items()))
    print('pick back up: ' + ' · '.join(items[i]['title'] for i in spec['pickup']))
    print('next: check each app (a guess from the notes), write `what`, fill `rhythm` and `watch`, then `images`')


# ---------------------------------------------------------------- images
def _get(url, as_json=True, tries=3):
    for n in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': '*/*'})
            with urllib.request.urlopen(req, timeout=12) as r:
                b = r.read()
            return json.loads(b) if as_json else b
        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and n + 1 < tries:
                time.sleep(3 + 2 * n)
                continue
            return None
        except (urllib.error.URLError, TimeoutError, ValueError):
            if n + 1 < tries:
                time.sleep(1)
                continue
            return None


def app_image(u):
    """(image url, credit) from an app's own embed or thumbnail, as her settings name them."""
    for a in APPS:
        if not a.get('link_rx') or not re.search(a['link_rx'], u):
            continue
        if a.get('oembed'):
            d = _get(a['oembed'].format(url=urllib.parse.quote(u, safe=':/')))
            if d and d.get('thumbnail_url'):
                return d['thumbnail_url'], a.get('label') or a['app']
        if a.get('thumb') and a.get('id_rx'):
            m = re.search(a['id_rx'], u)
            if m:
                for size in a.get('thumb_sizes') or ['']:
                    img = a['thumb'].format(id=m.group(1), size=size)
                    b = _get(img, as_json=False, tries=1)
                    if b and len(b) > 5000:
                        return img, a.get('label') or a['app']
    return None, ''


def find_image(q, override=None):
    """(image url, credit) for one card, or (None, why)."""
    if override:
        return override, ''
    src, kind, title = q.get('source', ''), q.get('kind', ''), q.get('title', '')
    for u in [src, q.get('link', '')] + re.findall(r'https?://\S+', q.get('notes', '')):
        if u:
            img, credit = app_image(u)
            if img:
                return img, credit
    if kind == '📺 show' and not q.get('wiki'):
        d = _get('https://api.tvmaze.com/singlesearch/shows?q=' + urllib.parse.quote(title))
        if d and d.get('image'):
            return d['image'].get('original') or d['image'].get('medium'), 'TVmaze'
    if kind in ('🎥 movie', '📺 show', '📼 video'):
        for t in ([q['wiki']] if q.get('wiki') else []) + [f'{title} (film)', title, f'{title} (TV series)']:
            d = _get('https://en.wikipedia.org/api/rest_v1/page/summary/' + urllib.parse.quote(t.replace(' ', '_')))
            time.sleep(0.4)
            if not d or d.get('type') == 'disambiguation':
                continue
            desc = (d.get('description') or '') + ' ' + (d.get('extract') or '')[:200]
            if not re.search(r'film|movie|documentary|series|television|sitcom', desc, re.I):
                continue
            img = (d.get('originalimage') or d.get('thumbnail') or {}).get('source')
            if img:
                return img, 'Wikipedia'
    if kind in ('📗 book', '🎧 audiobook'):
        qq = title + (' ' + q['author'] if q.get('author') else '')
        d = _get('https://openlibrary.org/search.json?limit=5&fields=title,author_name,cover_i&q='
                 + urllib.parse.quote(qq))
        for doc in (d or {}).get('docs', []):
            if doc.get('cover_i'):
                return f'https://covers.openlibrary.org/b/id/{doc["cover_i"]}-L.jpg', 'Open Library'
        d = _get('https://www.googleapis.com/books/v1/volumes?maxResults=3&q=' + urllib.parse.quote(qq))
        for v in (d or {}).get('items', []):
            il = v.get('volumeInfo', {}).get('imageLinks', {})
            u = il.get('thumbnail') or il.get('smallThumbnail')
            if u:
                return u.replace('http://', 'https://').replace('&edge=curl', ''), 'Google Books'
    page = q.get('link') or ''
    if page and not re.search(r'/search|google\.com|facebook\.com|mail\.google', page):
        raw = _get(page, as_json=False, tries=1)
        m = re.search(rb'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', raw or b'') or \
            re.search(rb'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image', raw or b'')
        if m:
            return html.unescape(m.group(1).decode('utf-8', 'replace')), urllib.parse.urlparse(page).hostname.replace('www.', '')
    return None, 'no image found'


def save_jpeg(raw, path, shape):
    """Resize to what the card shows and save as JPEG (Pillow, else ImageMagick)."""
    width = {'poster': 360, 'square': 400, 'wide': 640}.get(shape, 400)
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        if im.width > width:
            im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        im.save(path, 'JPEG', quality=80, optimize=True, progressive=True)
        return True
    except Exception:                                   # noqa: BLE001 — try the other tool
        tmp = path + '.src'
        with open(tmp, 'wb') as fh:
            fh.write(raw)
        ok = subprocess.run(['convert', tmp + '[0]', '-resize', f'{width}x>', '-quality', '80', path]).returncode == 0
        os.remove(tmp)
        return ok


def _one(k, it, img_dir, refresh):
    path = os.path.join(img_dir, f'{k}.jpg')
    if os.path.exists(path) and not refresh:
        return k, f'img/{k}.jpg', it.get('credit') or ''
    url, credit = find_image(dict(it.get('image_q') or {}, link=it.get('link', '')), it.get('image_url'))
    raw = _get(url, as_json=False) if url else None
    if raw and save_jpeg(raw, path, it.get('shape')):
        return k, f'img/{k}.jpg', it.get('credit') or credit
    return k, '', ''


def cmd_images(a):
    from concurrent.futures import ThreadPoolExecutor
    with open(a.spec, encoding='utf-8') as fh:
        spec = json.load(fh)
    os.makedirs(a.img, exist_ok=True)
    todo = list(spec['items'].items())
    with ThreadPoolExecutor(max_workers=a.workers) as ex:   # a few at a time: the image hosts throttle
        for k, image, credit in ex.map(lambda kv: _one(kv[0], kv[1], a.img, a.refresh), todo):
            spec['items'][k]['image'] = image
            if credit:
                spec['items'][k]['credit'] = credit
    with open(a.spec, 'w', encoding='utf-8') as fh:
        json.dump(spec, fh, ensure_ascii=False, indent=1)
    missing = [i['title'] for i in spec['items'].values() if not i.get('image')]
    have = len(spec['items']) - len(missing)
    print(f'{have} of {len(spec["items"])} cards have an image in {a.img}')
    if missing:
        print('no image yet (set image_url, or image_q.wiki, and run again): ' + ' · '.join(missing))
    if a.sheet and have:
        files = [os.path.join(a.img, f'{k}.jpg') for k, i in spec['items'].items() if i.get('image')]
        subprocess.run(['montage'] + files + ['-geometry', '120x160+4+4', '-tile', '10x', a.sheet])
        print(f'contact sheet: {a.sheet}  (look at it before publishing)')


# ---------------------------------------------------------------- the page
E = lambda s: html.escape(str(s or ''), quote=True)   # noqa: E731


def status_label(it):
    if it.get('standing') == 'in motion':
        return 'Started'
    return ''


def meta_line(it, with_app=True):
    bits = []
    st = status_label(it)
    if st:
        bits.append(f'<b>{st}</b>')
    if it.get('meta'):
        bits.append(E(it['meta']))
    if with_app and it.get('app') and it['app'] != 'Elsewhere':
        bits.append(E(it['app']))
    if it.get('score'):
        bits.append(E(it['score']))
    return ' · '.join(bits)


def cover(k, it, cls='cover'):
    shape = it.get('shape') or 'poster'
    if it.get('image'):
        alt = {'poster': 'Poster', 'square': 'Cover', 'wide': 'Thumbnail'}[shape] if shape in ('poster', 'square', 'wide') else 'Image'
        if it['kind'] in ('📗 book', '🎧 audiobook'):
            alt = 'Cover'
        img = f'<img src="{E(it["image"])}" alt="{alt}: {E(it["title"])}" loading="lazy">'
    else:
        img = f'<span class="ph" aria-hidden="true">{E(it["kind"][:2])}</span>'
    return f'<a class="{cls} {shape}" href="{E(it["link"])}" tabindex="-1" aria-hidden="true">{img}</a>'


def open_btn(it):
    app = it.get('app') if it.get('app') != 'Elsewhere' else 'where it plays'
    return f'<a class="open" href="{E(it["link"])}">Open in {E(app)} <span aria-hidden="true">↗</span></a>'


def pick_card(k, it):
    why = f'<p class="why">{E(it["why"])}</p>' if it.get('why') else ''
    what = f'<p class="what">{E(it["what"])}</p>' if it.get('what') else ''
    return (f'<article class="pick" data-k="{E(k)}" data-t="{E(it["title"])}" data-kind="{E(it["kind"])}">'
            f'{cover(k, it)}<div class="body"><span class="kind">{E(it["kind"])}</span>'
            f'<a href="{E(it["link"])}"><h3>{E(it["title"])}</h3></a>{what}{why}'
            f'<p class="meta">{meta_line(it)}</p><div class="row">{open_btn(it)}'
            f'<button class="act" type="button" aria-label="Mark or add a thought: {E(it["title"])}">+</button></div></div></article>')


def row_card(k, it, with_app=True):
    what = f'<p class="what">{E(it["what"])}</p>' if it.get('what') else ''
    why = f'<p class="why">{E(it["why"])}</p>' if it.get('why') else ''
    return (f'<div class="w" data-k="{E(k)}" data-t="{E(it["title"])}" data-kind="{E(it["kind"])}">'
            f'{cover(k, it, "thumb")}<div class="body"><a href="{E(it["link"])}"><h4>{E(it["title"])}</h4></a>'
            f'{what}{why}<p class="meta">{meta_line(it, with_app)}</p></div>'
            f'<button class="act" type="button" aria-label="Mark or add a thought: {E(it["title"])}">+</button></div>')


def tile(k, it):
    sub = it.get('meta') or (it.get('sub') if it['kind'] in ('📗 book', '🎧 audiobook') else '') or ''
    line = ' · '.join(x for x in [status_label(it), sub, it.get('score')] if x)
    return (f'<div class="tile {E(it.get("shape") or "poster")}" data-k="{E(k)}" data-t="{E(it["title"])}" data-kind="{E(it["kind"])}">'
            f'{cover(k, it)}<a class="tt" href="{E(it["link"])}"><h4>{E(it["title"])}</h4></a>'
            f'<p class="meta">{E(line)}</p>'
            f'<button class="act" type="button" aria-label="Mark or add a thought: {E(it["title"])}">+</button></div>')


def _ids(spec, ids):
    return [(k, spec['items'][k]) for k in ids if k in spec['items']]


def build_html(spec):
    items = spec['items']
    out = []
    # pick back up
    picks = _ids(spec, spec.get('pickup', [])[:3])
    out.append('<section class="part" id="pickup"><div class="head"><h2>Pick back up</h2>'
               '<span class="n">started, and waiting where you left off</span></div>'
               '<div class="picks">' + ''.join(pick_card(k, it) for k, it in picks) + '</div></section>')
    # the rhythm card: every day type is in the page; the script shows today's
    rh = []
    for day in spec.get('rhythm', []):
        moods = ''.join(f'<div class="mood"><h3>{E(m["mood"])}</h3>' + ''.join(row_card(k, it) for k, it in _ids(spec, m.get('items', [])))
                        + '</div>' for m in day.get('moods', []) if m.get('items'))
        if moods:
            rh.append(f'<div class="rday" data-days="{E(day["days"])}" hidden><p class="rlabel"><span class="dname"></span> · {E(day["label"])}</p>'
                      f'<p class="rline">{E(" · ".join(m["mood"] for m in day["moods"] if m.get("items")))}</p><div class="moods">{moods}</div></div>')
    if rh:
        out.append('<section class="part" id="today"><div class="card rhythm">' + ''.join(rh) + '</div></section>')
    # watch: by who and mood
    if spec.get('watch'):
        cols = ''.join(f'<div class="wcol"><h3>{E(g["title"])}</h3>' + (f'<p class="gwhy">{E(g["why"])}</p>' if g.get('why') else '')
                       + ''.join(row_card(k, it) for k, it in _ids(spec, g.get('items', []))) + '</div>' for g in spec['watch'])
        out.append('<section class="part" id="watch"><div class="head"><h2>Watch</h2><span class="n">by who it’s for and the mood</span></div>'
                   f'<div class="wl">{cols}</div></section>')
    # by app
    shelves = []
    for a in APPS:
        ks = [(k, it) for k, it in items.items() if it.get('app') == a['app']]
        if not ks:
            continue
        ks.sort(key=lambda kv: (kv[1].get('standing') != 'in motion', kv[1].get('order', 99)))
        name = a.get('label') or a['app']
        note = a.get('note') or ''
        shelves.append(f'<div class="shelf" id="app-{re.sub(r"[^a-z]+", "-", a["app"].lower()).strip("-")}">'
                       f'<header><span class="glyph" aria-hidden="true">{E(a["glyph"])}</span><h3>{E(name)}</h3>'
                       f'<span class="n">{len(ks)}</span>' + (f'<span class="note">{E(note)}</span>' if note else '')
                       + '</header><div class="rail" tabindex="0" aria-label="' + E(name) + '">'
                       + ''.join(tile(k, it) for k, it in ks) + '</div></div>')
    out.append('<section class="part" id="apps"><div class="head"><h2>By app</h2><span class="n">where each one plays · started first</span></div>'
               + ''.join(shelves) + '</section>')
    # done this week: filled live from the taps
    out.append('<section class="part" id="done"><div class="card donecard"><div class="head"><h2>Done this week</h2>'
               '<span class="n" id="doneN"></span></div><div id="doneList"><p class="empty">Nothing marked yet. Tap + on anything you start, finish or drop, and it lands here.</p></div></div></section>')
    credits = sorted({i.get('credit') for i in items.values() if i.get('credit')})
    foot = ('From your stories queue, ' + E(spec.get('made', '')) + '. Images: ' + E(', '.join(credits)) + '.') if credits else 'From your stories queue.'
    with open(os.path.join(ASSETS, 'page.html'), encoding='utf-8') as fh:
        page = fh.read()
    nav = [('pickup', 'Pick up'), ('today', 'Today'), ('watch', 'Watch'), ('apps', 'By app'), ('done', 'Done')]
    nav = ''.join(f'<a href="#{i}">{t}</a>' for i, t in nav if i != 'today' or rh if i != 'watch' or spec.get('watch'))
    return (page.replace('{{TITLE}}', E(f'Stories · {spec.get("week", "")}'))
                .replace('{{WEEK}}', E(spec.get('week', '')))
                .replace('{{DATES}}', E(spec.get('dates', '')))
                .replace('{{NAV}}', nav)
                .replace('{{MAIN}}', '\n'.join(out))
                .replace('{{FOOT}}', foot)
                .replace('{{MADE}}', E(spec.get('made', ''))))


def cmd_build(a):
    with open(a.spec, encoding='utf-8') as fh:
        spec = json.load(fh)
    bad = [i['title'] for i in spec['items'].values() if not i.get('image')]
    with open(a.out, 'w', encoding='utf-8') as fh:
        fh.write(build_html(spec))
    print(f'wrote {a.out} · {len(spec["items"])} cards · {len(spec.get("pickup", []))} to pick back up')
    if bad:
        print(f'{len(bad)} card(s) without an image: ' + ' · '.join(bad))


# ---------------------------------------------------------------- reading the taps back
def fmt_day(iso):
    d = dt.date.fromisoformat(iso[:10])
    return f'{d.day} {MONTHS[d.month - 1]}'


def add_note(notes, hers=None, ours=None):
    """Her words go above the divider, be•do's below it, last (J5)."""
    top, bottom = split_notes(notes)
    if hers and hers not in top:
        top = (top + '\n' if top else '') + hers
    if ours and ours not in bottom:
        bottom = (bottom + '\n' if bottom else '') + ours
    return top + ('\n———\n' + bottom if bottom else '')


def plan(db_items, recs):
    """The writes the page's taps call for, against the base as it is now.
    Idempotent: a mark the base already shows, or a thought already in its
    notes, plans nothing."""
    by_id = {r['id']: r['fields'] for r in recs}
    patches, removals, says = [], [], []
    to_standing = {'started': 'in motion', 'finished': 'finished', 'dropped': 'dropped'}
    for k, d in sorted(db_items.items()):
        f = by_id.get(k)
        if f is None:
            if d.get('status') or d.get('note'):
                says.append(f'{d.get("title") or k}: no stories row with this id; left alone')
            continue
        fields, notes = {}, f.get('notes') or ''
        new = to_standing.get(d.get('status'))
        if new and f.get('standing') != new:
            fields['standing'] = new
            day = fmt_day(d.get('statusDay') or d.get('updated') or dt.date.today().isoformat())
            word = {'in motion': 'started', 'finished': 'finished', 'dropped': 'dropped'}[new]
            notes = add_note(notes, ours=f'[be•do] {day}: marked {word} on the Stories page.')
        if d.get('note'):
            day = fmt_day(d.get('noteDay') or d.get('updated') or dt.date.today().isoformat())
            line = f'{d["note"].strip()} ({day})'
            if d['note'].strip() not in notes:
                notes = add_note(notes, hers=line)
        if notes != (f.get('notes') or ''):
            fields['notes'] = notes
        if fields:
            patches.append({'id': k, 'title': f.get('title'), 'fields': fields})
            says.append(f'{f.get("title")}: ' + ', '.join(
                (f'{f.get("standing")} → {fields["standing"]}' if x == 'standing' else 'a thought added' if d.get('note') and d['note'].strip() not in (f.get('notes') or '') else 'note')
                for x in fields))
        if new in ('finished', 'dropped'):
            u = ' '.join([f.get('source') or '', f.get('notes') or ''])
            for a in APPS:
                m = a.get('remove_rx') and re.search(a['remove_rx'], u)
                if m:
                    removals.append({'id': k, 'title': f.get('title'), 'app': a['app'],
                                     'uri': a['remove_uri'].format(id=m.group(1))})
                    break
    return {'patches': patches, 'library_remove': removals, 'says': says}


def load_db(path):
    """The page's items collection as {id: data}. Takes ArtifactData's list
    output ({documents: [{id, data}]}) or a plain {id: data}."""
    with open(path, encoding='utf-8') as fh:
        d = json.load(fh)
    docs = d.get('documents') or d.get('docs') or d.get('items') if isinstance(d, dict) else d
    if isinstance(docs, list):
        return {x.get('id', '').split('/')[-1]: x.get('data', x) for x in docs}
    return d


def cmd_readback(a):
    out = plan(load_db(a.db), load_records(a.stories))
    with open(a.out, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
    print(f'{len(out["patches"])} row(s) to update · {len(out["library_remove"])} episode(s) off the saved list')
    for s in out['says']:
        print('  ' + s)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='cmd', required=True)
    d = sub.add_parser('draft'); d.add_argument('--stories', required=True); d.add_argument('--out', required=True); d.add_argument('--today')
    i = sub.add_parser('images'); i.add_argument('--spec', required=True); i.add_argument('--img', required=True)
    i.add_argument('--sheet'); i.add_argument('--refresh', action='store_true'); i.add_argument('--workers', type=int, default=4)
    b = sub.add_parser('build'); b.add_argument('--spec', required=True); b.add_argument('--out', required=True)
    r = sub.add_parser('readback'); r.add_argument('--db', required=True); r.add_argument('--stories', required=True); r.add_argument('--out', required=True)
    for s in (d, i, b, r):
        s.add_argument('--local', help='stories_local.json; without it the settings row is read live')
    a = p.parse_args(argv)
    set_apps(a.local)
    {'draft': cmd_draft, 'images': cmd_images, 'build': cmd_build, 'readback': cmd_readback}[a.cmd](a)


if __name__ == '__main__':
    main()
