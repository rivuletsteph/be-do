#!/usr/bin/env python3
"""day_ahead.py — builds the day ahead page: one file, one DATA object.

Axes (V51 "the pages"): window = day, direction = ahead.
Engine rule: nothing personal lives in this file. Everything about the person
comes from the live reads (stream dumps, rhythms dump, calendar dump) and from
a local settings file (field ids, self name, calendar labels, phrase lists,
clock offset), which is gitignored. See day_ahead_local.example.json for the
shape and the README for the four keys that need a word of explanation.

Usage:
  python3 day_ahead.py --today 2026-09-22 --local day_ahead_local.json \
      --stream w39.json --stream w38.json --rhythms rhythms.json \
      --calendar cal.json --template day_ahead_engine.html --out page.html \
      [--secure "secure" --secure-words "..."] [--draft] [--intention "..." ×3]

Two passes a morning: the DRAFT runs at the look ahead step, before the user's
intention check; the OFFICIAL version runs after it, with their intentions
passed in their own words through --intention. The three stay be•do's either way.

Streams are listed LIVE BASE FIRST (I15). Every dump must be complete (I11):
records returned == totalRecordCount, or the build aborts.
"""
import argparse, json, re, datetime as dt, sys

# The field maps are the base's, not the builder's. main() fills them from the
# local settings file before any read; the KEYS below are the builder's own
# vocabulary and never change, only the ids behind them do.
STREAM_KEYS = ('title', 'key', 'details', 'when', 'end', 'target',
               'status', 'practice', 'person', 'rhythm', 'waiting', 'queue')
RHYTHM_KEYS = ('name', 'code', 'type', 'status', 'target', 'parent',
               'emoji', 'dest', 'goal')
F = {}
RF = {}
OPEN = ('▫️potential', '⬜ intention', '▶️ in motion')
MEDIA = ('🎥', '📗', '📺', '🎧', '📰', '📼')
DIVIDERS = ('———', '---', '——')
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DAYEMO = ['🌕', '🔥', '💧', '🌳', '🏆', '⏳', '☀️']
MARK = chr(0x1684E)  # be•do's mark, by codepoint, never typed
UTC_OFFSET = dt.timedelta(0)  # filled from the local settings file (I12)


def die(msg):
    sys.exit('ABORT: ' + msg)


RHYTHMS_NOTE = {}


def read_dump(path):
    # A saved tool result in a claude.ai chat is wrapped: [{"text": "<the JSON as a string>"}].
    # Accept that as-is, so the chat can pass the saved file straight in.
    d = json.load(open(path, encoding='utf-8'))
    if isinstance(d, list) and d and isinstance(d[0], dict) and 'text' in d[0]:
        d = json.loads(d[0]['text'])
    return d


def complete(path):
    d = read_dump(path)
    RHYTHMS_NOTE[path] = d.get('metadata', {})
    n, tot = len(d['records']), d.get('metadata', {}).get('totalRecordCount')
    if tot is None or n != tot:
        die(f'{path}: {n} of {tot} records — a truncated read is not a read (I11)')
    return d['records'], n


def sv(v):
    return v.get('name') if isinstance(v, dict) else v


def local(ts):
    if not ts:
        return None
    return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + UTC_OFFSET).replace(tzinfo=None)


def her_words(details):
    """The user's words sit above the divider; the [be•do] block below is not."""
    if not details:
        return ''
    for d in DIVIDERS:
        i = details.find('\n' + d)
        if i >= 0 or details.startswith(d):
            return details[:max(i, 0)].strip()
    return details.split('[be•do]')[0].strip()


def load_stream(paths):
    seen, reads = {}, []
    for p in paths:  # live base first (I15)
        recs, n = complete(p)
        reads.append((p, n))
        for r in recs:
            if r['id'] in seen:
                continue
            c = r['cellValuesByFieldId']
            row = {k: sv(c.get(v)) for k, v in F.items()}
            row.update(id=r['id'], created=r['createdTime'])
            seen[r['id']] = row
    rows = list(seen.values())
    chains = {}
    for r in rows:
        chains.setdefault(r['key'] or r['id'], []).append(r)
    for k in chains:
        chains[k].sort(key=lambda r: r['created'])
    latest = {k: ch[-1] for k, ch in chains.items()}  # I5
    return rows, chains, latest, reads


def plainly_media(r):
    p, t = r['practice'] or '', r['title'] or ''
    return p.startswith(MEDIA) or (p.startswith('⚡') and t.lstrip('⚡ ').startswith(MEDIA))


def filtered_open(latest):
    """Filtered at the READ, before anything is shown."""
    out, dropped = [], dict(queue=0, waiting=0, media=0)
    for r in latest.values():
        if r['status'] not in OPEN:
            continue
        if r['queue']:
            dropped['queue'] += 1; continue
        if r['waiting']:
            dropped['waiting'] += 1; continue
        if plainly_media(r):
            dropped['media'] += 1; continue
        out.append(r)
    return out, dropped


def load_rhythms(path):
    recs, n = complete(path)
    by_name, by_id = {}, {}
    for r in recs:
        c = r['cellValuesByFieldId']
        row = {k: sv(c.get(v)) if k != 'dest' else c.get(v) for k, v in RF.items()}
        row['dest'] = [sv(x) for x in (row['dest'] or [])]
        row['id'] = r['id']
        by_id[r['id']] = row
        if row['status'] == 'active':
            by_name[row['name']] = row
    return by_name, n


def clean_title(t):
    t = re.sub(r'^[✅✖️⬜▶️▫️\s]+', '', t or '')
    return re.sub(r'^⚡\s*', '', t).strip()


def fmt_day(d):
    return f'{DAY3[d.weekday()]} {d.day} {d.strftime("%b")}'


# Clocks are formatted by hand. glibc's '%-I' and '%-d' drop the leading zero,
# but they are a GNU extension: on Windows strftime raises on them outright, so
# a builder that used them ran on the laptop and nowhere else.
def hour12(t):
    return (t.hour % 12) or 12


def ampm(t):
    return 'am' if t.hour < 12 else 'pm'


def sentence_with(text, pats):
    for s in re.split(r'(?<=[.!?])\s+', text):
        if any(re.search(p, s, re.I) for p in pats):
            return s.strip()
    return None


# ---------------------------------------------------------------- pareto three
def pareto(open_rows, chains, rhythms, today, L):
    self_name = L['self_person']

    def drive_of(r):
        return rhythms.get(r['rhythm'] or '')

    def lane(r):
        d = drive_of(r)
        return (d or {}).get('parent') or r['rhythm'] or '—'

    def tgt(r):
        return local(r['target']).date() if r['target'] else None

    # 1 · in motion — the ▶️ row whose target sits closest to today
    motion = [r for r in open_rows if r['status'] == '▶️ in motion' and tgt(r) and drive_of(r)]
    motion.sort(key=lambda r: abs((tgt(r) - today).days))
    # 2 · someone waiting — another person on the row, due within three days
    def others(r):
        ps = [p.strip() for p in (r['person'] or '').split(',') if p.strip()]
        return [p for p in ps if p != self_name]
    waiting = [r for r in open_rows if others(r) and tgt(r) and -1 <= (tgt(r) - today).days <= 3]
    waiting.sort(key=lambda r: tgt(r))
    # 3 · named as weighing — the user's own words anywhere in the chain
    weigh = []
    for r in open_rows:
        for link in reversed(chains[r['key'] or r['id']]):
            s = sentence_with(her_words(link['details']), L['weighing_phrases'])
            if s:
                weigh.append((r, s, link['created'])); break
    weigh.sort(key=lambda x: x[2], reverse=True)  # most recently said first

    picks, used, lanes = [], set(), {}
    def take(kind, cands, why):
        for c in cands:
            r = c[0] if isinstance(c, tuple) else c
            if r['id'] in used or lanes.get(lane(r), 0) >= 2:
                continue
            used.add(r['id']); lanes[lane(r)] = lanes.get(lane(r), 0) + 1
            picks.append(dict(kind=kind, row=r, why=why(c)))
            return
    def due_phrase(r):
        t = tgt(r)
        if not t:
            return 'no date on it'
        n = (t - today).days
        return ('due today' if n == 0 else 'due tomorrow' if n == 1 else
                f'due {fmt_day(t)}' if n > 0 else f'target passed {fmt_day(t)}')
    take('in motion', motion, lambda r: f'already moving · {due_phrase(r)} · retargeted {len(chains[r["key"]]) - 1}×')
    take('someone waiting', waiting, lambda r: f'{", ".join(others(r))} is waiting · {due_phrase(r)}')
    take('weighing on you', weigh, lambda c: f'your words: “{c[1]}” · {due_phrase(c[0])}')
    # the next candidate in line for each slot, named quietly, not rendered as a list
    nxt = []
    for kind, cands in (('in motion', motion), ('someone waiting', waiting), ('weighing on you', weigh)):
        for c in cands:
            r = c[0] if isinstance(c, tuple) else c
            if r['id'] not in used:
                nxt.append(dict(kind=kind, title=clean_title(r['title']))); break
    return picks, nxt


# ---------------------------------------------------------------- calendar
STOP = set('the and with for from meeting weekly monthly session study check-in check in stay a of to at on'.split())


def words(s):
    s = re.sub(r'[^\w&\s-]', ' ', s.lower())
    return {w for w in re.split(r'[\s\-|]+', s) if len(w) >= 3 and w not in STOP}


def ev_span(e):
    s, en = e['start'], e['end']
    if 'date' in s:
        # the calendar tool returns all-day dates as '2026-09-20T00:00:00Z'; keep the date only
        a = dt.datetime.fromisoformat(s['date'][:10]); b = dt.datetime.fromisoformat(en['date'][:10])
        return a, b, True
    a = dt.datetime.fromisoformat(s['dateTime']).replace(tzinfo=None)
    b = dt.datetime.fromisoformat(en['dateTime']).replace(tzinfo=None)
    return a, b, False


def strip_prefix(summary):
    return re.sub(r'^[\W_]+', '', summary, flags=re.UNICODE).strip() or summary


def calendar(cal, rows, open_rows, today, days, L):
    start = dt.datetime.combine(today, dt.time())
    stop = start + dt.timedelta(days=days)
    evs = []
    for c in cal['calendars']:
        for e in c['events']:
            a, b, allday = ev_span(e)
            if b <= start or a >= stop:
                continue
            evs.append(dict(who=c['who'], title=strip_prefix(e['summary']), a=a, b=b, allday=allday,
                            recurring=e.get('recurring', False), multi=(b - a) >= dt.timedelta(days=2)))
    # match each event to a stream row — be•do's own look-ahead rows do not count
    pool = [r for r in rows if not (r['practice'] or '').startswith(tuple(L['own_practices']))]
    for e in evs:
        ew = words(e['title']); hit = None
        for r in pool:
            txt = (r['title'] or '') + ' ' + her_words(r['details'])
            rw = words(txt); common = ew & rw
            if not common:
                continue
            dates = [local(x) for x in (r['when'], r['target']) if x]
            dated = any(e['a'] - dt.timedelta(days=1) <= d < e['b'] + dt.timedelta(days=1) for d in dates)
            if (dated and common) or (e['multi'] and len(common) >= 2):
                hit = r; break
        if not hit and not e['allday']:  # a row targeted at the event's own time is its row
            for r in pool:
                t = local(r['target'])
                if t and abs((t - e['a']).total_seconds()) <= 45 * 60:
                    hit = r; break
        e['match'] = (hit or {}).get('title')
        e['row'] = bool(hit)
    # clashes
    mine = [e for e in evs if e['who'] == L['self_calendar']]
    away = [e for e in mine if e['allday'] and e['multi']]
    for e in evs:
        e['clash'] = []
    for e in evs:
        for w in away:
            if e is w or not (e['a'] < w['b'] and w['a'] < e['b']):
                continue
            if words(e['title']) & words(w['title']):
                continue
            if e['who'] == L['self_calendar'] and e['allday']:
                continue
            e['clash'].append(w['title'])
    timed = [e for e in mine if not e['allday']]
    for i, x in enumerate(timed):
        for y in timed[i + 1:]:
            if x['a'] < y['b'] and y['a'] < x['b']:
                x['clash'].append(y['title']); y['clash'].append(x['title'])
    # due actions by day
    due = {}
    for r in open_rows:
        if r['target']:
            d = local(r['target']).date()
            if today <= d < today + dt.timedelta(days=days):
                due.setdefault(d, []).append(clean_title(r['title']))
    out = []
    for i in range(days):
        d = today + dt.timedelta(days=i)
        ds = dt.datetime.combine(d, dt.time()); de = ds + dt.timedelta(days=1)
        items = []
        for e in evs:
            if not (e['a'] < de and ds < e['b']):
                continue
            first, last = e['a'].date() == d, (e['b'] - dt.timedelta(seconds=1)).date() == d
            if e['multi'] and not first and not last:
                continue  # a long stay is drawn as a band, named on its first and last day
            when = ('' if e['allday'] else f"{hour12(e['a'])}:{e['a'].minute:02d}".replace(':00', '') + ampm(e['a'])[0]) if first else ('ends ' + (f"{hour12(e['b'])}{ampm(e['b'])}" if not e['allday'] else 'today'))
            if e['multi'] and first:
                when = f'through {fmt_day((e["b"] - dt.timedelta(seconds=1)).date())}'
            items.append(dict(who=e['who'], title=e['title'], when=when, gap=not e['row'], match=e.get('match'),
                              clash=e['clash'] if first else [], sort=e['a'].isoformat()))
        items.sort(key=lambda x: x['sort'])
        bands = [e['title'] for e in evs if e['multi'] and e['a'].date() < d < (e['b'] - dt.timedelta(seconds=1)).date()]
        out.append(dict(date=d.isoformat(), label=fmt_day(d), today=i == 0, weekend=d.weekday() >= 5,
                        events=items, due=due.get(d, []), bands=bands))
    gaps = sum(1 for e in evs if not e['row'])
    clashes = sum(1 for e in evs if e['clash'])
    away_bands = [dict(title=w['title'], a=w['a'].date().isoformat(), b=(w['b'] - dt.timedelta(seconds=1)).date().isoformat()) for w in away]
    return out, gaps, clashes, away_bands


# ---------------------------------------------------------------- main
def install_local(L):
    """Put the person's own values where the module can see them. Missing a
    field id is a build error, not a blank column: a silent '' would read every
    row as empty and the page would look calm and be wrong."""
    global F, RF, UTC_OFFSET
    fields = L.get('fields') or {}
    for name, keys, target in (('stream', STREAM_KEYS, F), ('rhythms', RHYTHM_KEYS, RF)):
        got = fields.get(name) or {}
        missing = [k for k in keys if not got.get(k)]
        if missing:
            die(f"local settings: fields.{name} is missing {', '.join(missing)}")
        target.update({k: got[k] for k in keys})
    if 'utc_offset_hours' not in L:
        die('local settings: utc_offset_hours is missing')
    UTC_OFFSET = dt.timedelta(hours=L['utc_offset_hours'])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--today', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--stream', action='append', required=True)
    ap.add_argument('--rhythms', required=True)
    ap.add_argument('--calendar', required=True)
    ap.add_argument('--template', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--secure')
    ap.add_argument('--secure-words')
    ap.add_argument('--days', type=int, default=14)
    ap.add_argument('--draft', action='store_true')
    ap.add_argument('--intention', action='append', default=[])
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    install_local(L)
    today = dt.date.fromisoformat(a.today)

    rows, chains, latest, reads = load_stream(a.stream)
    rhythms, nrh = load_rhythms(a.rhythms)
    open_rows, dropped = filtered_open(latest)
    cal = json.load(open(a.calendar, encoding='utf-8'))

    # chip — derived from the date, never copied forward
    wk = L['week_zero_number'] + (today - dt.date.fromisoformat(L['week_zero_sunday'])).days // 7
    chip = f'▶️{today:%m%d} {DAYEMO[today.weekday()]} {DAY3[today.weekday()]} {MARK} W{wk} 🔆 my day'

    # the week's word — the user's row, the user's words
    word = None
    for r in sorted(rows, key=lambda r: r['created'], reverse=True):
        m = re.match(L['week_word_title'], r['title'] or '')
        if m:
            word = dict(word=m.group(1).strip(), words=sentence_with(her_words(r['details']), [m.group(1)]) or ''); break

    picks, nxt = pareto(open_rows, chains, rhythms, today, L)
    days, gaps, clashes, away = calendar(cal, rows, open_rows, today, a.days, L)

    # map forward — each pick's drive running to what it serves
    lanes, dests = [], {}
    for p in picks:
        r = p['row']; d = rhythms.get(r['rhythm'] or '') or {}
        t = local(r['target']).date().isoformat() if r['target'] else None
        lanes.append(dict(kind=p['kind'], drive=r['rhythm'], emoji=d.get('emoji') or '·',
                          step=t, drive_target=d.get('target'), dest=d.get('dest') or []))
        for dn in d.get('dest') or []:
            if dn not in dests:
                dr = next((x for x in rhythms.values() if x['name'].endswith(dn) or x['name'] == dn), {})
                feeders = [x['name'] for x in rhythms.values() if x['type'] == '♐ drive' and dn in (x['dest'] or [])]
                dests[dn] = dict(name=dn, emoji=dr.get('emoji') or '♎', target=dr.get('target'), feeders=len(feeders))

    # today and soon — dated work, the next three days visible; the rest a count
    soon, overdue = [], []
    for r in open_rows:
        if not r['target']:
            continue
        t = local(r['target']).date(); n = (t - today).days
        item = dict(title=clean_title(r['title']), drive=r['rhythm'] or '', date=t.isoformat(), label=fmt_day(t), st=r['status'][:2])
        if 0 <= n <= 3:
            soon.append(item)
        elif n < 0:
            overdue.append(item)
    soon.sort(key=lambda x: x['date']); overdue.sort(key=lambda x: x['date'], reverse=True)

    # quick sweep — five oldest ▶️, none on Sunday
    sweep = []
    picked = {p['row']['id'] for p in picks}
    if today.weekday() != 6:
        mot = [r for r in open_rows if r['status'] == '▶️ in motion' and r['id'] not in picked
               and (r['practice'] or '⚡ action') == '⚡ action']
        mot.sort(key=lambda r: chains[r['key'] or r['id']][0]['created'])
        sweep = [dict(title=clean_title(r['title']), since=local(chains[r['key'] or r['id']][0]['created']).date().isoformat())
                 for r in mot[:5]]

    # the lead — one line, spoken to the user
    first = days[0]
    ends = [e['title'] for e in first['events'] if e['when'].startswith('ends')]
    tmr = next((p for p in picks if p['row']['target'] and (local(p['row']['target']).date() - today).days == 1), None)
    parts = []
    if ends:
        parts.append(re.sub(r'^Stay at ', '', ends[0].split(' | ')[0]) + ' wraps up this morning.')
    if tmr:
        t = clean_title(tmr['row']['title']).split(' — ')[0]
        parts.append('Tomorrow: ' + t[0].lower() + t[1:] + '.')
    lead = ' '.join(parts) if parts else 'A clear day ahead.'
    # open work targeted inside an away stretch, even past the window
    inside = []
    for w in away:
        a0, b0 = dt.date.fromisoformat(w['a']), dt.date.fromisoformat(w['b'])
        if b0 < today:
            continue
        for r in open_rows:
            if r['target'] and a0 <= local(r['target']).date() <= b0 and local(r['target']).date() >= today + dt.timedelta(days=a.days):
                inside.append(dict(title=clean_title(r['title']), label=fmt_day(local(r['target']).date()), away=w['title']))

    DATA = dict(
        chip=chip, date=today.isoformat(), dateLabel=f'{today:%A} {today.day} {today:%B}', lead=lead,
        word=word,
        secure=dict(state=a.secure, words=a.secure_words) if a.secure else None,
        pareto=[dict(kind=p['kind'], title=clean_title(p['row']['title']), drive=p['row']['rhythm'] or '',
                     emoji=(rhythms.get(p['row']['rhythm'] or '') or {}).get('emoji') or '·', why=p['why']) for p in picks],
        next=nxt,
        intentions=(a.intention + [None, None, None])[:3], draft=a.draft,
        map=dict(start=today.isoformat(), end=L['map_end'], lanes=lanes, dests=list(dests.values()), away=away),
        soon=soon, overdue=overdue,
        days=days, gaps=gaps, clashes=clashes,
        sweep=sweep, sunday=today.weekday() == 6, inside=inside,
        prov=dict(reads=[f'{p.split("/")[-1].replace(".json", "")} {n}/{n}' for p, n in reads],
                  rhythms=(f"{RHYTHMS_NOTE[a.rhythms]['read_total']}/{RHYTHMS_NOTE[a.rhythms]['read_total']} ({nrh} active rows used)"
                           if RHYTHMS_NOTE.get(a.rhythms, {}).get('read_total') else f'{nrh}/{nrh}'), calendar=cal.get('read', {}),
                  unique=len(rows), keys=len(latest), open=len(open_rows), dropped=dropped),
    )
    tpl = open(a.template, encoding='utf-8').read()
    html = tpl.replace('/*__DATA__*/null', json.dumps(DATA, ensure_ascii=False))
    open(a.out, 'w', encoding='utf-8').write(html)
    print(json.dumps(dict(picks=[(p['kind'], clean_title(p['row']['title'])) for p in picks], next=nxt,
                          soon=len(soon), overdue=len(overdue), gaps=gaps, clashes=clashes, sweep=len(sweep)),
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
