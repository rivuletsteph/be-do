#!/usr/bin/env python3
"""look_behind.py — builds The Day Behind page: one file, one DATA object.

Axes (V51 "the pages"): window = day, direction = behind.

Engine rule: nothing personal lives in this file or in the engine. Everything
about the person comes from the saved live reads (stream dumps, rhythms dump,
practices dump, connections dump) and from a local settings file — field ids,
the user's name, the practice-to-slice map, the clock offset — gitignored.
See look_behind_local.example.json for the shape.

Who belongs to which circle is NOT a setting. It is read live from the
connections table, first circle listed wins, because a map kept by hand goes
stale the day the user meets somebody.

Two things on this page are NOT computed. The lead and the story are the
user's, and Claude writes them in the chat from the day's rows. They arrive through
--words; without them the build stops rather than shipping a page with a hole
where the day's own account of itself should be.

Usage:
  python3 look_behind.py --day 2026-09-20 --local look_behind_local.json \\
      --stream w39.json [--stream w38.json] --rhythms rhythms.json \\
      [--practices practices.json] [--connections connections.json] \\
      [--typical typical_time.json] \\
      --words words.json --template look_behind_engine.html --out page.html \\
      [--secure secure] [--baseline-days N] [--usual-min N]

Streams are listed LIVE BASE FIRST (I15) and deduped by record id before any
chain is resolved, so a row that appears in two bases is one row. Every dump
must be complete (I11): records returned == totalRecordCount, or the build
aborts.
"""
import argparse, json, os, re, sys, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bedo_common import complete, die, norm, read_dump, sv, weekno  # noqa: E402
import day_pie  # noqa: E402

# The field maps are the base's, not the builder's. install_local() fills them
# from the local settings file before any read; the KEYS below are the
# builder's own vocabulary and never change, only the ids behind them do.
STREAM_KEYS = ('title', 'key', 'details', 'when', 'end', 'status', 'practice',
               'person', 'rhythm', 'wellness', 'deliv')
OPTIONAL_STREAM_KEYS = ('device', 'mentioned', 'emotion', 'emoword', 'spent')
RHYTHM_KEYS = ('name', 'type', 'status', 'emoji', 'dest')
PRACTICE_KEYS = ('name', 'band', 'zero', 'group')
CONNECTION_KEYS = ('name', 'short', 'circles')
F, RF, PF, CF = {}, {}, {}, {}
UTC_OFFSET = dt.timedelta(0)     # filled from the local settings file (I12)

# The eight, and which half they face. The engine draws them in this vocabulary
# — these are the page's own names, not anyone's, so they live here.
BE = ('heart', 'mind', 'body', 'spirit')
DO = ('water', 'air', 'earth', 'fire')
# Minutes and effort bands share one scale on the wheel: a row with a real span
# weighs its minutes over this, a row that holds no time weighs its catalogue
# band. Six, so an hour weighs ten. The user's amendment; the local file may
# override it.
DIVISOR = 6
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DAYEMO = ['🌕', '🔥', '💧', '🌳', '🏆', '⏳', '☀️']
MARK = chr(0x1684E)              # be•do's mark, by codepoint, never typed
DONE = '✅'                  # ✅ an intention met
CARRIED = '▶️'         # ▶️ an intention carried
DIVIDERS = ('———', '---', '——')
BULLET = re.compile(r'^\s*[-•*✓•]\s+(.+?)\s*$')


# ── reading ───────────────────────────────────────────────────────────────
def install_local(L):
    """Put the person's own values where the module can see them. A missing
    field id is a build error, not a blank column: a silent '' would read every
    row as empty and the page would look calm and be wrong."""
    global UTC_OFFSET
    fields = L.get('fields') or {}
    for name, keys, target in (('stream', STREAM_KEYS, F),
                               ('rhythms', RHYTHM_KEYS, RF),
                               ('practices', PRACTICE_KEYS, PF),
                               ('connections', CONNECTION_KEYS, CF)):
        got = fields.get(name) or {}
        missing = [k for k in keys if not got.get(k)]
        if missing and name not in ('practices', 'connections'):
            die(f"local settings: fields.{name} is missing {', '.join(missing)}")
        target.update({k: got[k] for k in keys if got.get(k)})
        if name == 'stream':
            # the device field arrived later than the rest; a stream without it
            # simply leaves the screen hours to the practice map
            target.update({k: got[k] for k in OPTIONAL_STREAM_KEYS if got.get(k)})
    if 'utc_offset_hours' not in L:
        die('local settings: utc_offset_hours is missing')
    UTC_OFFSET = dt.timedelta(hours=L['utc_offset_hours'])
    for k in ('self_person', 'week_zero_sunday', 'week_zero_number'):
        if L.get(k) in (None, ''):
            die(f'local settings: {k} is missing')


def local(ts):
    if not ts:
        return None
    return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + UTC_OFFSET).replace(tzinfo=None)


def load_stream(paths):
    """Deduped by record id FIRST, live base first (I15), and only then
    resolved into chains. The other order counts a row twice."""
    seen, reads = {}, []
    for p in paths:
        recs, n, _ = complete(p)
        reads.append((os.path.basename(p).rsplit('.', 1)[0], n))
        for r in recs:
            if r['id'] in seen:
                continue
            c = r.get('cellValuesByFieldId') or {}
            row = {k: sv(c.get(v)) for k, v in F.items()}
            row.update(id=r['id'], created=r.get('createdTime'))
            seen[r['id']] = row
    rows = list(seen.values())
    chains = {}
    for r in rows:
        chains.setdefault(r['key'] or r['id'], []).append(r)
    for k in chains:
        chains[k].sort(key=lambda r: r['created'] or '')
    latest = {k: ch[-1] for k, ch in chains.items()}              # I5
    return rows, chains, latest, reads


def load_rhythms(path):
    recs, n, _ = complete(path)
    by_name = {}
    for r in recs:
        c = r.get('cellValuesByFieldId') or {}
        row = {k: (c.get(v) if k == 'dest' else sv(c.get(v))) for k, v in RF.items()}
        row['dest'] = [sv(x) for x in (row.get('dest') or [])]
        row['id'] = r['id']
        if row.get('name'):
            by_name[row['name']] = row
    return by_name, n


def load_practices(path, L):
    """Effort band, the zero flag and the group, per practice. Optional:
    without it every practice carries the default band and nothing is zeroed by
    catalogue."""
    if not path:
        return {}
    if not PF.get('name'):
        die('local settings: fields.practices.name is needed to read a practices dump')
    recs, _, _ = complete(path)
    out = {}
    for r in recs:
        c = r.get('cellValuesByFieldId') or {}
        nm = norm(sv(c.get(PF['name'])))
        if not nm:
            continue
        band = sv(c.get(PF.get('band'))) if PF.get('band') else None
        zero = sv(c.get(PF.get('zero'))) if PF.get('zero') else None
        try:
            band = int(re.sub(r'\D', '', str(band))) if band not in (None, '') else None
        except ValueError:
            band = None
        out[nm] = {'band': band or L.get('default_effort_band', 1),
                   'zero': bool(zero),
                   'group': sv(c.get(PF.get('group'))) if PF.get('group') else None}
    return out


def load_connections(path):
    """Who belongs to which circle, read live. A person carries several circles
    and THE FIRST ONE LISTED is the one they are grouped by. Keyed on both the
    full name and the short one, because the stream's person field carries
    whichever one the user typed, sometimes with a glyph in front of it."""
    if not path:
        return {}
    if not CF.get('name') or not CF.get('circles'):
        die('local settings: fields.connections needs name and circles to read '
            'a connections dump')
    recs, _, _ = complete(path)
    out = {}
    for r in recs:
        c = r.get('cellValuesByFieldId') or {}
        circles = c.get(CF['circles']) or []
        if isinstance(circles, (str, dict)):
            circles = [circles]
        first = sv(circles[0]) if circles else None
        if not first:
            continue
        for key in (sv(c.get(CF['name'])), sv(c.get(CF.get('short')))):
            if key:
                out[norm(key)] = first
    return out


# ── small shapes ──────────────────────────────────────────────────────────
def her_words(details):
    """The user's words sit above the divider; the [be•do] block below is not."""
    if not details:
        return ''
    for d in DIVIDERS:
        i = details.find('\n' + d)
        if i >= 0 or details.startswith(d):
            return details[:max(i, 0)].strip()
    return details.split('[be•do]')[0].strip()


def sub_steps(details):
    """The ✓ list under a row: the user's own bullet lines, above the divider."""
    return [m.group(1) for m in (BULLET.match(x) for x in her_words(details).splitlines()) if m]


def clean_title(t):
    t = re.sub(r'^[✅✖️⬜▶️▫️◉●⨂⚡\s]+', '', t or '')
    return t.strip()


def to_you(t):
    """be•do's account of a day, turned to speak to her (the page speaks TO
    her). Sentences about be•do's own bookkeeping are dropped."""
    sents = [x for x in re.split(r'(?<=[.!?])\s+', t.strip())
             if x and 'be\u2022do' not in x and not re.search(r'\b(?:written|corrected|marked)\b', x)]
    t = ' '.join(sents)
    for a, b in (('She ', 'You '), (' she ', ' you '), (' herself', ' yourself'),
                 (' her ', ' your '), (' hers', ' yours'), (' her.', ' you.'), (' her,', ' you,')):
        t = t.replace(a, b)
    t = re.sub(r'\bCARRIED, your word\.?\s*', '', t).strip()
    return t[:1].upper() + t[1:]


def clock(m):
    """8:40a — minutes from midnight, the way the user writes a time."""
    h, r = divmod(int(m), 60)
    return f"{(h % 12) or 12}:{r:02d}{'a' if h % 24 < 12 else 'p'}"


def clock_short(m):
    h, r = divmod(int(m), 60)
    suf = 'a' if h % 24 < 12 else 'p'
    return f"{(h % 12) or 12}{suf}" if r == 0 else f"{(h % 12) or 12}:{r:02d}{suf}"


def spans(row, day):
    """(start, end) in minutes from midnight, clipped to the day. end is None
    when the row carries no end — a moment, or a stretch nobody closed."""
    a, b = local(row.get('when')), local(row.get('end'))
    if not a:
        return None, None
    lo = dt.datetime.combine(day, dt.time())
    hi = lo + dt.timedelta(days=1)
    if b and b > a:
        s, e = max(a, lo), min(b, hi)
        if e <= s:
            return None, None
        return int((s - lo).total_seconds() // 60), int((e - lo).total_seconds() // 60)
    if not (lo <= a < hi):
        return None, None
    return int((a - lo).total_seconds() // 60), None


# ── the eight, and the bar ────────────────────────────────────────────────
def effort(rows, L):
    """Weighted by effort; rows with a real span count their minutes.

    A row that holds no time contributes its practice's effort band. A row with
    a measured span contributes its minutes over `effort_minute_divisor`, so a
    long stretch outweighs a moment without swamping the wheel. The divisor is
    a setting because it is a scale, not a fact."""
    div = L.get('effort_minute_divisor') or DIVISOR
    dom = {k: 0.0 for k in BE + DO}
    for r in rows:
        k = norm(r.get('wellness'))
        if k not in dom:
            continue
        dom[k] += (r['_mins'] / div) if r['_mins'] else float(r['_band'])
    return {k: round(v, 1) for k, v in dom.items()}


def split_do(rows, rhythms, L):
    """The doing half, cut in two. A row worked against a drive is growing —
    it moves something toward a goal. Everything else on the doing side is
    tending: a row against a standing rhythm, and a row carrying no bucket at
    all, because an unnamed doing hour was the floor being held up.

    Tending is therefore the default, not a category a row has to earn. That
    is what makes the bar add up: every doing row lands in one of the two, so
    the engine is never left with an unbucketed remainder to draw."""
    tend_t = set(L.get('tending_types') or [])
    grow_t = set(L.get('growing_types') or [])
    div = L.get('effort_minute_divisor') or DIVISOR
    tending = growing = 0.0
    for r in rows:
        if norm(r.get('wellness')) not in DO:
            continue
        v = (r['_mins'] / div) if r['_mins'] else float(r['_band'])
        t = (rhythms.get(r.get('rhythm') or '') or {}).get('type')
        if t in grow_t:
            growing += v
        else:                       # a rhythm, an unlisted type, or no bucket
            tending += v
    return round(tending, 1), round(growing, 1)


# ── main ──────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--stream', action='append', required=True)
    ap.add_argument('--rhythms', required=True)
    ap.add_argument('--practices')
    ap.add_argument('--connections')
    ap.add_argument('--typical')
    ap.add_argument('--words', help='JSON: {"lead": "...", "story": [[glyph, text], ...]}')
    ap.add_argument('--lead')
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--secure', default='')
    ap.add_argument('--baseline-days', type=int)
    ap.add_argument('--usual-min', type=int)
    ap.add_argument('--allow-unwritten', action='store_true',
                    help='build with the lead and the story empty — for a shape check only')
    a = ap.parse_args()

    L = json.load(open(a.local, encoding='utf-8'))
    install_local(L)
    day = dt.date.fromisoformat(a.day)

    # the user's words, written in the chat, not computed here
    W = json.load(open(a.words, encoding='utf-8')) if a.words else {}
    lead = a.lead or W.get('lead') or ''
    story = [list(x) for x in (W.get('story') or [])]
    if not a.allow_unwritten and (not lead or not story):
        die("the lead and the story are the user's and are written in the chat. "
            'Pass them with --words (see SKILL.md), or --allow-unwritten for a shape check.')

    rows, chains, latest, reads = load_stream(a.stream)
    rhythms, nrh = load_rhythms(a.rhythms)
    practices = load_practices(a.practices, L)
    circles = load_connections(a.connections)
    typical = {}
    if a.typical and os.path.exists(a.typical):
        typical = (read_dump(a.typical) or {}).get('practices', {})

    self_name = L['self_person']
    noscore = set(L.get('noscore_statuses') or [])
    done_st = set(L.get('done_statuses') or [])
    zero_pr = {norm(x) for x in (L.get('zero_practices') or [])}
    zero_grp = {norm(x) for x in (L.get('zero_practice_groups') or [])}

    # ── the day's rows, and what each one is worth ────────────────────────
    day_rows = []
    for r in latest.values():
        s, e = spans(r, day)
        if s is None:
            continue
        pr = norm(r.get('practice'))
        cat = practices.get(pr) or {}
        people = [p.strip() for p in (r.get('person') or '').split(',') if p.strip()]
        # person = with her or in direct contact; mentioned = came up in that
        # contact (amendment [id]). Older rows carry no mentioned.
        ment = [p.strip() for p in (r.get('mentioned') or '').split(',') if p.strip()]
        r = dict(r, _s=s, _e=e, _mins=(e - s) if e else 0, _pr=pr,
                 _people=people, _mentioned=ment, _title=clean_title(r.get('title')))
        r['_band'] = cat.get('band') or L.get('default_effort_band', 1)
        # Two different questions, and they get different answers.
        #
        # _notmine — the row is not an hour of the user's day at all: a plan,
        # never lived, or somebody else's own row kept in their stream. It
        # is out of everything.
        #
        # _zero — the row is an hour of their day but not effort: sleep is
        # the case that matters. It scores nothing on the wheel and its minutes
        # are still logged on the pie, because the hours happened. Collapsing
        # these two into one flag is what loses the night.
        r['_notmine'] = bool(r.get('status') in noscore
                             or (L.get('zero_when_person_excludes_self') and people
                                 and self_name not in people))
        r['_zero'] = bool(r['_notmine'] or cat.get('zero') or pr in zero_pr
                          or norm(cat.get('group')) in zero_grp)
        day_rows.append(r)
    day_rows.sort(key=lambda r: (r['_s'], r['created'] or ''))

    # a container holds other rows; it is an envelope, not an activity.
    # V51: A CONTAINER IS NEVER AN ⚡ ACTION — a long stretch of work is the
    # work, not a frame around it, so actions are kept out of the test.
    _act = {norm(x) for x in (L.get('action_practices') or ['action'])}
    _, held = day_pie.containers([dict(r, s=r['_s'], e=r['_e'])
                                  for r in day_rows if r['_pr'] not in _act])
    held_ids = {r['id'] for r in held}
    for r in day_rows:
        if r['id'] in held_ids:
            r['_notmine'] = r['_zero'] = True
    scoring = [r for r in day_rows if not r['_zero']]
    lived = [r for r in day_rows if not r['_notmine']]

    # ── the day, entry by entry ─────────────────────────────────────────
    # NOTHING RISES UNLESS IT IS A NAMED KIND OF SIGNAL (26 Sep 2026). The
    # earlier rule rose anything that wasn't routine, and a day where nearly
    # every row carries her words rose nearly every row. The kinds that rise
    # are the ones her system already uses to mark what mattered — they live
    # in the local settings, so the list is hers to move.
    #
    # A CLOSE WITH NO SPAN AND AN OLDER KEY IS BOOKKEEPING, not today. It
    # leaves the entries and what moved, and is named once as a count.
    # (V51 already says what moved reads a real span; this applies the same
    # test to the entries.)
    rises = {norm(x) for x in (L.get('entry_card_practices') or [])}
    act_pr = {norm(x) for x in (L.get('action_practices') or ['action'])}
    moving_st = set(L.get('motion_statuses') or [])

    def key_day(r):
        """The day a chain was opened, from its key. No key reads as today."""
        m = re.match(r'(\d{2})(\d{2})(\d{2})_', r.get('key') or '')
        if not m:
            return day
        try:
            return dt.date(2000 + int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            return day

    def real_span(r):
        return bool(r['_e'] or r.get('spent'))

    def bookkeeping(r):
        return (r.get('status') in done_st or r.get('status') in moving_st) \
            and not real_span(r) and key_day(r) < day

    books = [r for r in lived if bookkeeping(r)]
    entries = []
    for r in lived:
        if bookkeeping(r):
            continue
        pr = r['_pr']
        card = pr in rises or (pr in act_pr and (real_span(r) or key_day(r) == day))
        m = re.match(r'^([^\w\s]+)', (r.get('practice') or '').strip())
        e = {'at': clock(r['_s']), 'g': m.group(1) if m else '', 'p': pr,
             'wd': norm(r.get('wellness'))}
        if card:
            words = '\n'.join(ln for ln in her_words(r.get('details')).splitlines()
                              if not ln.lstrip().startswith('>'))
            words = re.sub(r'\s+', ' ', words).strip()
            title = re.sub(r'^[^\w]+', '', r['_title'])
            emo = r.get('emotion')
            emo = (emo[0] if isinstance(emo, list) and emo else emo) or ''
            e.update(card=True, st=(r.get('status') or '').split(' ')[0], t=title,
                     w=(words[:240].rsplit(' ', 1)[0] + ' \u2026') if len(words) > 240 else
                       ('' if words == title else words),
                     rh=r.get('rhythm') or '', emo=(sv(emo) or '')[:1], ew=r.get('emoword') or '',
                     url=r.get('deliv') or '')
        entries.append(e)
    ages = sorted((day - key_day(r)).days for r in books)
    booked = {'n': len(books), 'oldest': ages[-1] if ages else 0}

    # ── balance ──────────────────────────────────────────────────────────
    domains = effort(scoring, L)
    # what sits under each domain, heaviest first, so the wheel can be opened
    # and read (25 Sep 2026). Same weight as effort(): minutes over the divisor
    # for a real span, the practice's band otherwise.
    div = L.get('effort_minute_divisor') or DIVISOR
    dom_rows = {k: [] for k in BE + DO}
    for r in scoring:
        k = norm(r.get('wellness'))
        if k in dom_rows:
            w = (r['_mins'] / div) if r['_mins'] else float(r['_band'])
            dom_rows[k].append({'t': re.sub(r'^[^\w]+', '', r['_title']),
                                'w': round(w, 1), 'min': r['_mins'] or None})
    for k in dom_rows:
        dom_rows[k].sort(key=lambda x: -x['w'])
    tending, growing = split_do(scoring, rhythms, L)
    note = ' '.join(x for x in (L.get('zero_note') or '',
                                'Weighted by effort; rows with a real span count their minutes.') if x)

    # ── the pie ──────────────────────────────────────────────────────────
    cats = L.get('pie') or []
    if not cats:
        die('local settings: pie is empty — the five slices and their practices live there')
    cat_of = {}
    for c in cats:
        for p in c.get('practices') or []:
            cat_of[norm(p)] = c['k']
    # A screen is a property of the row, not of the practice — the same action
    # is on a laptop one hour and on nothing the next. So the device field
    # decides the screen slice, and only for rows the practice map didn't
    # already place: eating in front of the television is still eating.
    dev_slice = L.get('device_slice')
    dev_off = {norm(x) for x in (L.get('device_off') or [])}
    prows = []
    for r in lived:
        est = None
        if not r['_e']:
            t = typical.get(r['_pr'])
            est = t['median_min'] if t else None
        cat = cat_of.get(r['_pr'])
        if not cat and dev_slice and r.get('device') and norm(r['device']) not in dev_off:
            cat = dev_slice
        prows.append(dict(cat=cat, s=r['_s'], e=r['_e'], est=est, title=r['_title']))
    pie, trimmed = day_pie.build(prows, cats, max_titles=L.get('pie_max_titles', 4))

    # ── who was in your day ──────────────────────────────────────────────
    order = L.get('circle_order') or sorted(set(circles.values()))
    covered, first = {}, {}
    for r in day_rows:          # already in time order, so the chips are too
        for p in r['_people']:
            if p == self_name:
                continue
            first.setdefault(p, r['_s'])
            first[p] = min(first[p], r['_s'])
            covered.setdefault(p, [])
            if r['_e']:
                covered[p].append((r['_s'], r['_e']))
    all_day = L.get('all_day_minutes', 480)

    def when_of(p):
        sp = covered.get(p) or []
        if not sp:
            return ''
        merged, total = [], 0
        for s, e in sorted(sp):
            if merged and s <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], e))
            else:
                merged.append((s, e))
        total = sum(e - s for s, e in merged)
        if total >= all_day:
            return 'all day'
        return f'{clock_short(merged[0][0])}–{clock_short(merged[-1][1])}'

    def circle_rank(p):
        c = circles.get(norm(p))
        return order.index(c) if c in order else len(order)
    # the outer ring: people who came up, hung off whoever they came up with.
    # A mentioned name with no one but her in person on its row is not drawn.
    via = {}
    for r in day_rows:
        direct = [p for p in r['_people'] if p != self_name]
        for m in r.get('_mentioned') or []:
            if m == self_name or m in first:
                continue
            for p in direct:
                via.setdefault(p, [])
                if m not in via[p]:
                    via[p].append(m)
    # grouped by first circle, sized by how many of the day's rows were shared,
    # as the person text writes them (25 Sep)
    shared = {p: sum(1 for r in day_rows if p in r['_people']) for p in first}
    who = [dict({'name': p, 'when': when_of(p),
                 'circle': circles.get(norm(p)) or '', 'n': shared[p]},
                **({'via': via[p]} if via.get(p) else {}))
           for p in sorted(first, key=lambda p: (circle_rank(p), -shared[p], first[p]))]

    # ── highlights ───────────────────────────────────────────────────────
    hg = {norm(k): v for k, v in (L.get('highlight_glyphs') or {}).items()}
    # one glyph: the practice's own, and the title's leading glyph stripped
    highlights = [{'glyph': hg[r['_pr']], 'text': re.sub(r'^[^\w]+', '', r['_title'])}
                  for r in day_rows if r['_pr'] in hg]

    # ── intentions, and the follow-through ───────────────────────────────
    ip = {norm(x) for x in (L.get('intention_practices') or [])}
    motion = set(L.get('motion_statuses') or [])
    # One intention check row carries up to three intentions, joined with ' · '
    # in its title and numbered in her words. Each is its own line on the page
    # (25 Sep 2026). Each one's outcome is read from the day's ⚡ action check
    # row, whose title carries a status glyph per intention in the same order;
    # with no action check, an intention shows no glyph rather than a guess.
    acp = {norm(x) for x in (L.get('action_check_practices') or ['action check'])}
    OUTCOME = ('\u2705', '\u25b6\ufe0f', '\u2716\ufe0f', '\u2b1c')   # ✅ ▶️ ✖️ ⬜
    checks, happened = [], []
    for r in day_rows:
        if r['_pr'] in acp:
            tail = r['_title'].split('\u2014', 1)[-1]
            checks = [next((g for g in OUTCOME if part.strip().startswith(g)), '')
                      for part in tail.split('\u00b7')]
            # a line per intention in the details, glyph first or after an arrow:
            #   ✅ Show up at the meeting — the check-in ran 10:30 to 11:30 …
            #   ⚡ movement and the dogs → ✅ met — barre 9:06–9:48 …
            happened = []
            for ln in (r.get('details') or '').splitlines():
                g = next((g for g in OUTCOME if g in ln[:80]), None)
                if not g or ln.strip().startswith('['):
                    continue
                what = ln.split(' \u2014 ', 1)[1] if ' \u2014 ' in ln else ''
                happened.append((g, to_you(what)))
    intentions = []
    for r in (r for r in day_rows if r['_pr'] in ip):
        st = r.get('status')
        own = DONE if st in done_st else CARRIED if st in motion else ''
        words = her_words(r.get('details'))
        items = [t.strip() for t in r['_title'].split('\u00b7') if t.strip()]
        numbered = [re.sub(r'^\s*\d+[.)]\s*', '', ln).strip()
                    for ln in re.split(r'(?:^|\s)(?=\d+[.)]\s)', words) if ln.strip()]
        subs = numbered if len(numbered) == len(items) else []
        for n, text in enumerate(items):
            it = {'set': text,
                  'glyph': (happened[n][0] if len(happened) == len(items) else
                            checks[n] if len(checks) == len(items) else
                            own if len(items) == 1 else ''),
                  'at': clock(r['_s'])}
            if len(happened) == len(items) and happened[n][1]:
                it['happened'] = happened[n][1]
            if subs and subs[n] != text:
                it['sub'] = subs[n][:120]
            if r.get('deliv'):
                it['url'] = r['deliv']
            intentions.append(it)

    # ── what moved a destination forward ─────────────────────────────────
    dests = {}
    for r in lived:
        # ✅ done and ▶️ in motion both moved something (V51, what moved); an
        # in-motion step is marked so the page can say it isn't finished.
        # A close with no span and an older key is bookkeeping and stays out.
        if r.get('status') not in done_st and r.get('status') not in motion:
            continue
        if bookkeeping(r):
            continue
        dr = rhythms.get(r.get('rhythm') or '')
        if not dr:
            continue
        for dn in (dr.get('dest') or []):
            d = dests.setdefault(dn, {'name': dn, 'glyph': '', 'work': []})
            drec = rhythms.get(dn) or next(
                (x for x in rhythms.values() if (x.get('name') or '').endswith(dn)), {})
            d['glyph'] = d['glyph'] or drec.get('emoji') or ''
            item = {'drive': f"{dr.get('emoji') or ''} {dr.get('name') or ''}".strip(),
                    'text': re.sub(r'^[^\w]+', '', r['_title']),
                    'min': r['_mins'] or None,
                    'url': r.get('deliv') or None}
            if r.get('status') in motion:
                item['motion'] = True
            steps = sub_steps(r.get('details'))
            if steps:
                item['done'] = steps
            d['work'].append(item)

    # ── the page's own labels ────────────────────────────────────────────
    wk = weekno(day, L['week_zero_sunday'], L['week_zero_number'])
    wd = day.weekday()
    chip = f'✔️{day:%m%d} {DAYEMO[wd]} {DAY3[wd]} {MARK} W{wk} \U0001F506 my day'

    DATA = {
        'chip': chip,
        'date': f'{day:%A}, {day.day} {day:%B}',
        'title': lead,
        'story': story,
        'who': who,
        'highlights': highlights,
        'photos': [],          # no attachment field in the read — see SKILL.md
        'intentions': intentions,
        'entries': entries,
        'books': booked,
        'circleOrder': L.get('circle_order') or [],
        'balance': {'domains': domains, 'tending': tending, 'growing': growing,
                    'note': note, 'rows': dom_rows},
        'effectiveness': {
            'secure': a.secure,
            'baselineDays': a.baseline_days if a.baseline_days is not None
            else L.get('baseline_days', 0),
            'baselineNeeded': L.get('baseline_needed', 14),
            'usualMin': a.usual_min,
            'destinations': list(dests.values()),
        },
        'pie': pie,
        'slotsMax': L.get('slots_max', 3),
        'read': ' · '.join(f'{name} · {n}/{n}' for name, n in reads),
    }

    tpl = open(a.template, encoding='utf-8').read()
    if '/*__DATA__*/null' not in tpl:
        die(f'{a.template}: no /*__DATA__*/null placeholder — is this the engine?')
    open(a.out, 'w', encoding='utf-8').write(
        tpl.replace('/*__DATA__*/null', json.dumps(DATA, ensure_ascii=False)))

    est_total = sum(p['est'] for p in pie if not p.get('rest'))
    print(json.dumps({
        'out': a.out, 'rows_on_the_day': len(day_rows), 'scoring': len(scoring),
        'containers_set_aside': len(held), 'rhythms': nrh,
        'logged_min': sum(p['logged'] for p in pie), 'estimated_min': est_total,
        'estimates_trimmed_min': trimmed,
        'who': len(who), 'circles_read': len(circles),
        'highlights': len(highlights), 'intentions': len(intentions),
        'destinations': [d['name'] for d in dests.values()],
        'photos': 'none — no attachment field is read',
        'lead_and_story': 'written' if (lead and story) else 'UNWRITTEN',
    }, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
