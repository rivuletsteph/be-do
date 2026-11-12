# -*- coding: utf-8 -*-
"""The day-page audit: run before any look behind is shown, so she isn't the
one who catches what the page got wrong (2 Nov 2026).

Her words, Mon 2 Nov: *Why did I not get credit for an adventure? We took a
freaking adventure yesterday and it was awesome.* And: *I'm really annoyed that
I have to check all this stuff.* So the page is checked against the day before
she sees it. Each line is a FIX for be•do to do, or, rarely, one real gap to
ask her — never a pile.

  intention  the day's intention shows where she'd look: its rows carry a
             wellness the balance counts and names, and the story says it
  highlight  the highlight is among the moments, its area counts on the
             balance, and the story says it
  night      a sleep row on the day draws a night (it names her)
  chats      every chat she worked in that day has its time: a session entry,
             or 📲 capture rows for a window chat (2 Nov 2026)
  photos     at most six on the page, never two of the same moment
  company    a long stretch the pass gave the household only by default,
             where nothing but her chats was logged, is asked once: with them,
             or on her own? (the one company question worth her minute)

Quiet topics (her settings, `quiet_topics`) never appear in a line.

    items = audit(rows, day, L, rings, words=…, shown=…, sessions=…, changes=…)
    print(render(items, day))
"""
import datetime as dt, re

from bedo_reader import FACTS, offset_hours

A = FACTS['dayaudit']
WINDOWS = [w.lower() for w in FACTS['window_chats']]
PLANS = set(FACTS['status']['plans'])
NOT_LIVED = PLANS | {FACTS['status']['actions'][4], FACTS['status']['logs'][2]}
STOP = set(A['stop_words'])


def word(practice):
    return re.sub(r'\s+', ' ', re.sub(r'^[^\w]+', '', (practice or '').strip())).lower()


def utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def words_of(text):
    return {w for w in re.findall(r"[a-z][a-z'’]+", (text or '').lower()) if len(w) >= 4 and w not in STOP}


def fix(check, line):
    return dict(check=check, kind='fix', line=line)


def ask(check, line):
    return dict(check=check, kind='ask', line=line)


def story_text(words):
    if not words:
        return None
    return ' '.join([words.get('lead') or ''] + [' '.join(map(str, x)) for x in words.get('story') or []]).lower()


def intention_of(rows):
    """(the intention row, its words): the day's one intention, not the month's or the week's."""
    for r in rows:
        if word(r.get('practice')) != A['intention_practice']:
            continue
        t = re.sub(r'^[^\w]+', '', r.get('title') or '')
        if not t.lower().startswith(A['intention_practice']):
            continue                        # 'Monthly intention — …' carries the practice too
        what = t.split(' — ', 1)[1] if ' — ' in t else ''
        what = re.sub(r'\s*[✅✔️▶️⬜✖️]+\s*$', '', what)
        if what:
            return r, what
    return None, None


def realized_by(rows, what, skip):
    """The day's rows that carry out the intention: they share its uncommon words."""
    want = words_of(what)
    need = 1 if len(want) <= 2 else 2
    out = []
    for r in rows:
        if r is skip or r.get('status') in NOT_LIVED or word(r.get('practice')) in A['not_realizing']:
            continue
        if len(want & words_of(r.get('title'))) >= need:
            out.append(r)
    return out


def area_line(rings, area):
    e = (rings or {}).get('energy') or {}
    k = area.split()[-1].lower() if area else ''
    return k, (e.get('min') or {}).get(k, 0), (e.get('rows') or {}).get(k, [])


def clean(t):
    return re.sub(r'^[^\w]+', '', t or '').split(' — ')[0].strip()


def check_intention(rows, rings, story):
    out = []
    r, what = intention_of(rows)
    if not r:
        return out
    doers = realized_by(rows, what, r)
    if not doers:
        out.append(fix('intention', f'the intention “{what[:60]}” has no row that carries it out: '
                       'name the row that did it, or score it at the action check'))
    for d in doers[:3]:
        if not d.get('wellness'):
            out.append(fix('intention', f'“{clean(d.get("title"))[:50]}” carries out the intention and has no wellness: '
                           'the balance can\'t count it'))
            continue
        k, m, named = area_line(rings, d['wellness'])
        if not m:
            out.append(fix('intention', f'the intention “{what[:50]}” counts 0 min of {k} on the balance'))
    areas = {area_line(rings, d.get('wellness'))[0] for d in doers if d.get('wellness')}
    if doers and areas and not any(clean(d.get('title')) in area_line(rings, d.get('wellness'))[2]
                                   or any(clean(x.get('title')) in area_line(rings, d.get('wellness'))[2] for x in doers)
                                   for d in doers if d.get('wellness')):
        out.append(fix('intention', f'the balance never names the intention (“{what[:50]}”) under '
                       + ' or '.join(sorted(areas)) + ': its rows sit outside the area they belong to'))
    if story is not None and not (words_of(what) & words_of(story)):
        out.append(fix('intention', f'the story doesn\'t say the intention (“{what[:50]}”): one line names it'))
    return out


def check_highlight(rows, rings, story, day, L):
    out = []
    moments = {(m.get('p'), m.get('t')) for m in (rings or {}).get('moments') or []}
    for r in rows:
        if word(r.get('practice')) != A['highlight_practice'] or r.get('status') in NOT_LIVED:
            continue
        t = clean(r.get('title'))
        if rings is not None and ('highlight', t) not in moments:
            out.append(fix('highlight', f'the highlight “{t[:50]}” is not among the moments'))
        if r.get('wellness'):
            k, m, _ = area_line(rings, r['wellness'])
            if rings is not None and not m:
                out.append(fix('highlight', f'the highlight “{t[:50]}” counts 0 min of {k} on the balance'))
        if story is not None and not (words_of(t) & words_of(story)):
            out.append(fix('highlight', f'the story doesn\'t say the highlight (“{t[:50]}”)'))
    return out


def check_night(rows, rings, L):
    me = L.get('self_person') or (L.get('people') or {}).get('self') or ''
    out = []
    for r in rows:
        if word(r.get('practice')) not in FACTS['categorize']['sleep_practices'] or r.get('status') in NOT_LIVED:
            continue
        ps = r.get('person') or ''
        if me and ps and me not in ps:
            out.append(fix('night', f'the sleep row names {ps} and not her: the page drops the night — add her'))
    if rings is not None and any(word(r.get('practice')) in FACTS['categorize']['sleep_practices'] for r in rows) \
            and not rings.get('inbed_day'):
        out.append(fix('night', 'a sleep row is on the day and the page draws no night'))
    return out


def is_window(title):
    t = (title or '').lower()
    return any(w in t for w in WINDOWS)


def check_chats(rows, sessions, day, L):
    """Every chat she worked in that day has its time (2 Nov 2026)."""
    out = []
    off = offset_hours(L, dt.datetime.combine(day, dt.time(12), dt.timezone.utc))
    s0 = dt.datetime.combine(day, dt.time(), dt.timezone.utc) - dt.timedelta(hours=off)
    e0 = s0 + dt.timedelta(days=1)
    for s in sessions or []:
        mine = [(utc(a), utc(b)) for a, b in s.get('stretches') or [] if utc(a) < e0 and utc(b) > s0]
        mins = sum(int((min(b, e0) - max(a, s0)).total_seconds() // 60) for a, b in mine)
        if not mins:
            continue
        key = s.get('id') or s.get('url') or ''
        url = s.get('url') or key
        theirs = [r for r in rows if key and (key in (r.get('chat') or '') or url in (r.get('chat') or ''))]
        name = (s.get('title') or url)[:50]
        if is_window(s.get('title')):
            caps = [r for r in theirs if word(r.get('practice')) == A['capture_practice'] and r.get('end')]
            got = sum(int((utc(r['end']) - utc(r['datetime'])).total_seconds() // 60) for r in caps)
            if got + A['chat_slack_minutes'] < mins:
                out.append(fix('chats', f'“{name}” (a window chat): {mins} min of her turns, {got} in 📲 capture rows — '
                               'write capture rows for its stretches'))
        elif not theirs:
            out.append(fix('chats', f'“{name}”: {mins} min of her turns and no session entry — write it from its '
                           'stretches (session-entry)'))
        else:
            r = theirs[0]
            got = (r.get('time_spent') and int(float(r['time_spent']) // 60)) or (
                r.get('end') and int((utc(r['end']) - utc(r['datetime'])).total_seconds() // 60)) or 0
            if abs(got - mins) > A['chat_slack_minutes'] and 'stretches:' not in (r.get('details') or ''):
                out.append(fix('chats', f'“{name}”: the row says {got} min, her turns {mins} — set it to its stretches'))
    return out


def check_photos(shown):
    """At most six, never two of the same moment (2 Nov 2026)."""
    if shown is None:
        return []
    out = []
    ts = sorted(shown)
    if len(ts) > A['photos_max']:
        out.append(fix('photos', f'{len(ts)} photos on the page: at most {A["photos_max"]}, the highlights'))
    near = [(a, b) for a, b in zip(ts, ts[1:]) if (b - a).total_seconds() <= A['burst_seconds']]
    if near:
        out.append(fix('photos', f'{len(near)} near-duplicate(s) on the page (the same moment seconds apart): keep one each'))
    return out


def check_company(changes, rows, L):
    """One question, only for a long stretch given the household by default where only her chats were logged."""
    by_id = {r.get('id'): r for r in rows}
    def chat_of(r):         # one chat's rows: by its link, else the window its title names, else the title
        t = (r.get('title') or '').lower()
        return r.get('chat') or next((w for w in WINDOWS if w in t), None) or clean(r.get('title'))
    runs = []
    for c in sorted((c for c in changes or [] if c['rule'] == 'company' and 'by default' in c['why'] and c['id'] in by_id),
                    key=lambda c: by_id[c['id']].get('datetime') or ''):
        r = by_id.get(c['id'])
        if not r or word(r.get('practice')) not in A['chat_practices'] or not r.get('end'):
            continue
        a, b = utc(r['datetime']), utc(r['end'])
        if runs and a - runs[-1][1] <= dt.timedelta(minutes=A['company_join_minutes']) and chat_of(r) == chat_of(runs[-1][2][0]):
            runs[-1][1] = max(runs[-1][1], b)
            runs[-1][2].append(r)
        else:
            runs.append([a, b, [r]])
    out = []
    me = L.get('self_person') or (L.get('people') or {}).get('self') or ''
    for a, b, rs in runs:
        if (b - a) >= dt.timedelta(minutes=A['company_ask_minutes']):
            off = offset_hours(L, a)
            def hm(t):                      # by hand: '%-I' is glibc-only, and Windows refuses it
                t = t + dt.timedelta(hours=off)
                return f'{t.hour % 12 or 12}:{t.minute:02d}'
            name = re.sub(r'^[^\w]+', '', max(rs, key=lambda r: utc(r['end']) - utc(r['datetime'])).get('title') or '')
            it = ask('company', f'{hm(a)}–{hm(b)}, while you were in “{name[:40]}”: with them, or on your own? '
                     '(with them unless you say)')
            # on her answer “on my own”, the stretch is written as one row of hers, so the page counts it alone
            it['if_alone'] = dict(practice=A['alone_row_practice'], status=FACTS['status']['logs'][0],
                                  datetime=a.strftime('%Y-%m-%dT%H:%M:00.000Z'), end=b.strftime('%Y-%m-%dT%H:%M:00.000Z'),
                                  title=A['alone_row_title'], person=me)
            # and the chat rows the pass gave the household inside it are hers alone too
            inside = [c['id'] for c in changes if c['rule'] == 'company' and c['id'] in by_id
                      and word(by_id[c['id']].get('practice')) in A['chat_practices']
                      and a <= utc(by_id[c['id']]['datetime']) <= b and chat_of(by_id[c['id']]) == chat_of(rs[0])]
            it['if_alone_patch'] = [dict(id=i, fields=dict(person=me)) for i in dict.fromkeys(inside)]
            out.append(it)
    return out


def audit(rows, day, L, rings=None, words=None, shown=None, sessions=None, changes=None):
    story = story_text(words)
    items = (check_intention(rows, rings, story) + check_highlight(rows, rings, story, day, L)
             + check_night(rows, rings, L) + check_chats(rows, sessions, day, L) + check_photos(shown)
             + check_company(changes, rows, L))
    quiet = [q.lower() for q in L.get('quiet_topics') or []]
    return [i for i in items if not any(q in i['line'].lower() for q in quiet)]


def render(items, day):
    fixes = [i for i in items if i['kind'] == 'fix']
    asks = [i for i in items if i['kind'] == 'ask']
    lines = [f'page audit · {day:%a %d %b} — ' + (f'{len(fixes)} to fix before she sees it' if fixes else 'nothing to fix')]
    lines += [f'  FIX {i["check"]} · {i["line"]}' for i in fixes]
    if asks:
        lines.append('  one list for her, only if it matters:')
        lines += [f'  {n}. {i["line"]}' for n, i in enumerate(asks, 1)]
    return '\n'.join(lines)
