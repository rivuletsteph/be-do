"""saturday.py — the things she might want to do on a Saturday (7 Nov 2026).

Her words, looking at Saturday's my day page: *I really want you to try harder to pull up all the
things that I might want to do on Saturday, because this is a very short list.* And the steps that
were on the clock *aren't — it's not work. Those are just tasks.*

So a Saturday page carries a generous list, with no clock on any of it, drawn from four places:

  the stream     her ▫️ potentials and open rows under the fun rhythms (adventure, connection,
                 stories — `saturday_fun` in the settings, else every rhythm whose name says so)
                 and the drives that grow out of them; the tending rhythms (`tending`) and rows
                 with no rhythm only when the words are fun ones, never a chore
  again          the trails and parks she has been to in the last two weeks, with the dogs when
                 they came too
  the stories    the queue's `want` and `in motion` rows, by the moods the Morning Gate's Off the
                 clock groups them in (her words, 7 Nov: in the morning something educational, with
                 her son a sitcom or a Ghibli film, on her own a fun romantic comedy …)
  the places     the places table's `want to go` rows

Each idea keeps its way in (its links, a map for a place) and the one date it has, said in words,
never placed on the clock. Fun and low effort lead: at home first, then off the clock, then out for
a bit. Far trips are kept, folded at the end.

Every name the rules lean on (the fun rhythms, the far words) has a default here and can be set in
the settings (`saturday_fun`, `saturday_far`).
"""
import datetime as dt, re, urllib.parse


def _day(d):
    """Sat 7 Nov on every platform: '%-d' is glibc-only, and Windows refuses it."""
    return f'{d:%a} {d.day} {d:%b}'


# a rhythm whose name is fun on its own: every open row under it is a candidate (less the chores)
FUN_NAME = re.compile(r'(?i)adventur|creativ|connect|stor(y|ies)|spirit|\bplay|\bfun\b|communit')
OPEN = ('▫️potential', '▫️ potential', '⬜ intention', '▶️ in motion')
LIVED = ('● log', '◉ done', '✅ done')
CHORE = re.compile(
    r"(?i)\b(buy|purchase|pay|cancel|renew|return|returns|mail|fix|order|research|watch for|keep an eye|gift|rsvp|"
    r"invite|form|confirm|clean|talk to|ask|schedule|book|decide|check|look into|find out|appointment|vet|exam|"
    r"oil change|registration|tire|refund|homework|portal|shopping|sunglasses|glasses|hats?|basket|vacuum|"
    r"microwave|leak|faucet|lights|sticker|inbox|purge|reward|sell|shopping list|share|resend|dig up|recommend|"
    r"enroll|sponsor|permit|irb|paper|abstracts?|taxes|finances|haircut|hair cut|groceries|set up the table|sale|glue|"
    r"passports?|request|payment|invoice|plan the|nail down|decide what|html|transcript|obituary|reach out to|"
    r"update|expired|recap|categori[sz]e|budget)\b")
FUNWORD = re.compile(
    r"(?i)\b(fun|play|games?|cards?|puzzle|soup|cook|bake|make|moon cakes|trails?|hike|walk|ride|zoo|ranch|"
    r"museum|park|lake|zipline|camp|camping|picnic|movie|show|watch|danc\w*|music|guitar|paint|craft|garden|swim|"
    r"urban air|adventure|visit|catch up|coffee|library|church|festival|fair|christmasville|train|theat\w+|"
    r"concert|wheels|scooter|ninja|creations|sledding|trip|cruise|snorkel\w*|ski\w*|canoes?)\b|\b[A-Z][a-z]+ day\b")
FAR_T = re.compile(r"(?i)\b(trip|next time|someday|teenager|license|road trip|winter week|when we're through)\b")
FAR = re.compile(
    r"(?i)\b(Montana|Colorado|New Mexico|NM|Idaho|Utah|Wyoming|Alabama|Louisiana|Oklahoma|Arkansas|Japan|Mexico|"
    r"(?:\d+|two|three|four|five|six|seven|eight) hours?)\b")
HOME = re.compile(r"(?i)\b(art|soup|cook|bake|make|cards?|games?|puzzle|guitar|paint|craft|watch|read|movie|moon cakes|"
                  r"creations|garden)\b")
PEOPLE = re.compile(r"(?i)\b(call|catch up|coffee|reach back out|get together|library)\b")
PLAN = re.compile(r"(?i)\b(choose|pick|picks|find|map|identify|learn|look for|third option|next steps)\b")
DAY = re.compile(r"\b[A-Z][a-z]+ day\b|(?i:\burban air\b)")
DATED = re.compile(r"\b(Mon|Tue|Wed|Thu|Fri|Sat|Sun)\w* \d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)")
PLACE = re.compile(r"\b((?:[A-Z][\w'’]+ ){1,4}(?:Trails?|Park|Lake|Ranch|Falls|Preserve|Gardens?|River|Museum|Lodge))\b"
                   r"|\b(Lake (?:[A-Z][\w'’]+ ?){1,3})")
URL = re.compile(r'https?://[^\s)\]>"]+')
GROUPS = (('home', 'easy, at home'),
          ('stories', 'off the clock'),
          ('out', 'out for a bit, close to home'),
          ('soon', 'coming up'),
          ('people', 'people'),
          ('day', 'a day out'),
          ('plan', 'fun to plan'),
          ('far', 'farther off, to dream on'))
MOODS = (('kid', 'with {kid}'), ('learn', 'learn something'), ('evening', 'on your own, something fun'),
         ('listen', 'for a drive or a walk'), ('read', 'to read'))


def _name(v):
    return v.get('name') if isinstance(v, dict) else v


def _words(t):
    return {w.lower().rstrip('s') for w in re.findall(r'[A-Za-z]{3,}', t or '') if w.lower() not in ('and', 'the')}


def _clean(t):
    return re.sub(r'^[\W_]*(?:⚡|🖼️)?\s*', '', (t or '').strip()).replace('⚡ ', '').strip()


def _her(d):
    """Her words: what sits above the [be•do] divider (none when the row opens with be•do's own)."""
    h = re.split(r'\n?(?:———|---|——)\n?', d or '', maxsplit=1)[0].strip()
    return '' if h.startswith('[be•do]') else h


def gist(her, t):
    """One short line of her words, or none when it only says the title again (her words: less wordy)."""
    s = re.sub(r'https?://\S+', '', (her or '').split('\n')[0]).strip()
    m = re.match(r'^.{12,110}?[.!?](\s|$)', s)
    s = m.group(0).strip() if m else (s[:100].rsplit(' ', 1)[0] + '…' if len(s) > 100 else s)
    w = _words(s)
    return s if w and len(w - _words(t)) >= max(2, len(w) // 2) else None


def maps(q):
    return 'https://www.google.com/maps/search/?api=1&query=' + urllib.parse.quote(q)


def place_of(t):
    m = PLACE.search(t or '')
    return (m.group(1) or m.group(2)).strip() if m else None


def _key(t):
    """What two ideas share when they are one idea: the named place, else the title's words."""
    p = place_of(t)
    return (p.lower(), True) if p else (' '.join(sorted(_words(t))), False)


def fun_rhythms(rhythms_read, RF, L):
    """{rhythm or drive: (its rhythm, whole)} — whole when every open row under it is a candidate, else only rows whose
    words are fun. The fun rhythms are `saturday_fun` in the settings, else every rhythm whose name says fun; the
    tending rhythms (`tending`) count only for their fun rows. A drive counts through its parent, however the parent
    spells its name (the same words in another order)."""
    names, parents = [], {}
    for r in rhythms_read or []:
        c = r.get('cellValuesByFieldId') or {}
        n = c.get(RF.get('name'))
        if not n:
            continue
        p = c.get(RF.get('parent')) if RF.get('parent') else None
        if p:
            parents[n] = p
        elif 'rhythm' in str(c.get(RF.get('type')) or '') or not RF.get('type'):
            names.append(n)
    whole = list(L.get('saturday_fun') or [n for n in names if FUN_NAME.search(n)])
    part = [t for t in (L.get('tending') or []) if t not in whole]
    norm = lambda n: frozenset(_words(n))
    keys = {norm(f): (f, True) for f in whole} | {norm(f): (f, False) for f in part}
    out = {f: v for f, v in ((k[0], k) for k in keys.values())}
    for n, p in parents.items():
        if norm(p) in keys:
            out[n] = keys[norm(p)]
    out.update(keys)                              # a rhythm found by its words, however a row spells it
    return out


def ideas(today, rows, F, off, rhythms_read, RF, L, stories=None, places=None, intentions=()):
    """The Saturday list: groups of ideas, each {t, why, links, when, also, group}. No clock on any of them."""
    to = lambda ts: dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off
    fun = fun_rhythms(rhythms_read, RF, L)
    work = work_lanes(rhythms_read, RF, L) | set(L.get('hide_drives') or [])
    far = re.compile(FAR.pattern + ('|' + '|'.join(map(re.escape, L['saturday_far'])) if L.get('saturday_far') else ''), re.I)
    said = {' '.join(sorted(_words(i))) for i in intentions or [] if i}
    order = []
    add = order.append

    # ── the stream ──
    for r in rows:
        c = r['cellValuesByFieldId']
        st = _name(c.get(F['status'])) or ''
        if st not in OPEN:
            continue
        title = (c.get(F['title']) or '').strip()
        t = _clean(title)
        rh = (c.get(F['rhythm']) or '').strip()
        top, whole = fun.get(rh) or fun.get(frozenset(_words(rh))) or (None, False)
        d = c.get(F['details']) or ''
        her = _her(d)
        pr = str(c.get(F['practice']) or '')
        if pr and 'action' not in pr and not st.startswith('▫️'):
            continue                                   # a practice's own step (the Sunday reflection) is no idea
        if ' '.join(sorted(_words(t))) in said or re.match(r'(?i)^have fun\b', t):
            continue                                   # her intention itself
        if CHORE.search(t) and not (DATED.search(t) and top):
            continue
        if len(_words(t)) < 2:
            continue
        if not ((whole and _words(rh) == _words(top)) or ((top or not rh) and FUNWORD.search(t))
                or (rh not in work and STRONG.search(t))):
            continue
        tg = c.get(F['target'])
        when = None
        if tg:
            td = to(tg)
            if td.date() < today and st.startswith('▫️'):
                continue                               # a maybe whose day has gone
            days = (td.date() - today).days
            if days >= 0 and (DATED.search(t) or c.get(F['event'] if F.get('event') else '')) and days <= 28:
                h = f"{td.hour % 12 or 12}:{td.minute:02d} {'AM' if td.hour < 12 else 'PM'}"
                when = ('today' if days == 0 else 'tomorrow' if days == 1 else _day(td)) \
                    + (f' {h}' if (td.hour, td.minute) != (0, 0) else '') + (' · a maybe' if st.startswith('▫️') else '')
        links = [dict(l='map' if 'maps' in u else 'link', u=u) for u in URL.findall(her)]
        if F.get('deliverable'):
            links += [dict(l='deliverable', u=u) for u in URL.findall(c.get(F['deliverable']) or '')]
        ev = c.get(F['event']) if F.get('event') else None
        if ev:
            links.append(dict(l='calendar event', u=ev))
        if when:
            g = 'soon'
        elif FAR_T.search(t) or far.search(t) or far.search(her[:300]) or 'trip' in rh.lower():
            g = 'far'
        elif DAY.search(t):
            g = 'day'
        elif HOME.search(t) and not place_of(t):
            g = 'home'
        elif _words(rh) != _words(top or '') or PLAN.search(t):
            g = 'plan'
        elif PEOPLE.search(t) and not place_of(t):
            g = 'people'
        else:
            g = 'out'
        p = place_of(t)
        if p and g in ('out', 'day', 'soon') and not any(l['l'] == 'map' for l in links):
            links.append(dict(l='map', u=maps(p)))
        who = c.get(F['mentioned']) if F.get('mentioned') else ''
        made = c.get(F['when']) or r.get('createdTime') or ''
        order_key = (0 if made and to(made).date() == today else 1, 0 if st == '▶️ in motion' else 1 if st == '⬜ intention' else 2)
        add(dict(t=t, why=gist(her, t), links=links, when=when,
                 also=[], group=g, rid=r['id'], who=who or None, rank=order_key, made=made, due=(tg or '')[:16] or None))

    # ── again: the trails and parks of the last two weeks ──
    seen = {}
    for r in rows:
        c = r['cellValuesByFieldId']
        if (_name(c.get(F['status'])) or '') not in LIVED or not c.get(F['when']):
            continue
        a = to(c[F['when']])
        if not (0 < (today - a.date()).days <= 14):
            continue
        t = c.get(F['title']) or ''
        if not re.search(r'(?i)\b(walk\w*|hik\w*|trail|park|rode|riding)\b', t):
            continue
        p = place_of(t)
        if not p or re.search(r'(?i)taphouse|brewery|bar\b', p):
            continue
        s = seen.setdefault(p, dict(dogs=False, last=a))
        s['dogs'] |= bool(re.search(r'(?i)\bdogs?\b|\bwalking (?!the)[A-Z]\w+ on\b', t + ' ' + (c.get(F['details']) or '')))
        s['last'] = max(s['last'], a)
    for p, s in sorted(seen.items(), key=lambda kv: kv[1]['last'], reverse=True):
        p0 = re.sub(r'^(The|the) ', '', p)
        add(dict(t=f"the {p0}" + (' — with the dogs' if s['dogs'] else '') if not p0.startswith('Lake') else p0 + (' — with the dogs' if s['dogs'] else ''),
                 why=f"again · you were there {_day(s['last'])}", links=[dict(l='map', u=maps(p))],
                 when=None, also=[], group='out?', rid=None, who=None, rank=(1, 1), made=s['last'].isoformat()))

    # ── the places she wants to go ──
    for r in (places or []):
        f = r.get('fields') or {}
        if (f.get('standing') or '') != 'want to go' or not f.get('place'):
            continue
        where = f.get('where') or ''
        g = 'far' if (far.search(where) or far.search(f['place'])) else 'out?'
        links = [dict(l='map', u=maps(f['place'] + (' ' + where if where and not far.search(where) else '')))]
        if f.get('source'):
            links.insert(0, dict(l='link', u=f['source']))
        add(dict(t=f['place'], why=where or None, links=links, when=None, also=[], group=g, rid=r.get('id'), who=None,
                 rank=(1, 2), made=f.get('added') or ''))

    order = merged(order)
    out = []
    for g, label in GROUPS:
        if g == 'stories':
            st = stories_by_mood(stories, re.sub(r'^\W+', '', str(L.get('child_calendar') or '')))
            if st:
                out.append(dict(g=g, label=label, moods=st))
            continue
        its = sorted([x for x in order if x['group'] == g],
                     key=lambda x: (x['when'] is None, x['rank'], -_ts(x['made'])))
        if g == 'soon':
            its.sort(key=lambda x: x.get('due') or '')
        if its:
            out.append(dict(g=g, label=label, items=[{k: v for k, v in x.items() if k not in ('rank', 'made', 'group')}
                                                    for x in its]))
    return out


PRIO = ('soon', 'out', 'day', 'home', 'people', 'plan', 'far')


def merged(items):
    """One idea, said several ways, is one card (High Hope Ranch was four rows): the same named place, or one title's
    words inside another's. The card is the freshest of them, said most plainly; the rest ride under it as `also`.
    A place read with nothing about how far it is (a places row, a trail she walked) takes the group the stream gave it."""
    groups = []
    for it in items:
        k, named = _key(it['t'])
        w = _words(it['t'])
        hit = next((g for g in groups if any((named and (k in kk or kk in k)) or (not named and not nn and (w <= ww or ww <= w))
                                            for kk, nn, ww in g['keys'])), None)
        if hit is None:
            groups.append(dict(keys=[(k, named, w)], items=[it]))
        else:
            hit['keys'].append((k, named, w)); hit['items'].append(it)
    out = []
    for g in groups:
        xs = sorted(g['items'], key=lambda x: (x['rank'], -_ts(x['made'])))
        host = dict(xs[0])
        strong = [x['group'] for x in xs if not x['group'].endswith('?')]
        near = [p for p in strong if p != 'far']
        host['group'] = (min(near, key=PRIO.index) if near else 'far' if strong else xs[0]['group'].rstrip('?'))
        host['also'] = [x['t'] for x in xs[1:]]
        host['links'] = [l for i, x in enumerate(xs) for l in x['links'] if l not in [m for y in xs[:i] for m in y['links']]]
        host['links'] = [l for i, l in enumerate(host['links']) if l not in host['links'][:i]]
        host['when'] = next((x['when'] for x in xs if x['when']), None)
        host['due'] = next((x.get('due') for x in xs if x.get('when')), None)
        host['why'] = host['why'] or next((x['why'] for x in xs[1:] if x['why']), None)
        out.append(host)
    return out


def _ts(s):
    try:
        return dt.datetime.fromisoformat(str(s).replace('Z', '+00:00')).timestamp()
    except ValueError:
        try:
            return dt.datetime.fromisoformat(str(s)[:10]).timestamp()
        except ValueError:
            return 0


def mood_of(f, kid=''):
    t = ' '.join(str(f.get(k) or '') for k in ('title', 'notes', 'people'))
    kind = f.get('kind') or ''
    watch = bool(re.search(r'🎥|📺|📼', kind))
    k = re.escape(kid) if kid else None
    if ((k and (re.search(k, str(f.get('people') or ''), re.I) or (watch and re.search(r'with ' + k, t, re.I))))
            or re.search(r'(?i)ghibli|kiki|ponyo|totoro|young sheldon|family movie', t)):
        return 'kid'
    if re.search(r'(?i)nature|documentar|pbs|science|history|planet|voyage of time|earth|learn', t) and '📗' not in kind:
        return 'learn'
    if '🎧' in kind or '🎙' in kind:   # 🎧 audiobook; 🎙️ podcast (since 10 Nov 2026)
        return 'listen'
    if '📗' in kind:
        return 'read'
    if watch:
        return 'evening'
    return None


def stories_by_mood(stories, kid=''):
    """The stories queue by mood, what she has started first; news is the Morning Gate's, not a Saturday's."""
    got = {m: [] for m, _ in MOODS}
    for r in stories or []:
        f = r.get('fields') or {}
        if (f.get('standing') or '') not in ('want', 'in motion') or not f.get('title') or '📰' in (f.get('kind') or ''):
            continue
        m = mood_of(f, kid)
        if not m:
            continue
        t = _clean(f['title'])
        u = f.get('source') or ('https://www.google.com/search?q=' + urllib.parse.quote(t + ' where to watch'
                                                                                         if not re.search(r'🎧|🎙|📗', f.get('kind') or '') else t))
        note = gist(_her(f.get('notes') or ''), t)
        got[m].append(dict(t=t, kind=(f.get('kind') or '').split(' ')[0], on=f.get('standing') == 'in motion',
                           who=f.get('people') or None, links=[dict(l='link', u=u)], why=note, added=f.get('added') or ''))
    out = []
    for m, label in MOODS:
        xs = sorted(got[m], key=lambda x: (not x['on'], -_ts(x['added'])))
        if xs:
            out.append(dict(m=m, label=label.format(kid=kid or 'your kid'), items=[{k: v for k, v in x.items() if k != 'added'} for x in xs]))
    return out


# words fun enough that a row counts from any drive that is not work (a homeschool drive's "Try Neuro Art")
STRONG = re.compile(r"(?i)\b(art|paint\w*|craft\w*|games?|zoo|trails?|hike|museum|ranch|picnic|campfire)\b")


def work_lanes(rhythms_read, RF, L):
    """Every rhythm and drive under the work parents (`work_parents`), and the work parents themselves."""
    wp = set(L.get('work_parents') or [])
    out = set(wp)
    for r in rhythms_read or []:
        c = r.get('cellValuesByFieldId') or {}
        if RF.get('parent') and c.get(RF['parent']) in wp and c.get(RF.get('name')):
            out.add(c[RF['name']])
    return out


MONEY = re.compile(r'(?i)\b(grant|nifa|proposal|resubmission|budget|invoice|payment|reimburse\w*|funding)\b|\$\d')
DEADLINE = re.compile(r'(?i)\b(due|by|before|deadline|end of day)\b')


def feel(today, rows, F, off, L, rhythms_read=None, RF=None, n=3):
    """If you feel like it (7 Nov 2026, her words: I know I have more actions that are priority that are out there, but I
    forget them): at most three open actions with the most pull — someone waiting on her, a date close ahead, money —
    never on the clock and never a chore list. One per drive; nothing she is blocked on (the row's waiting field), no
    calendar event's own row, no quickie, no build work, nothing from the fun list, nothing more than a day past its date."""
    to = lambda ts: dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off
    fun = fun_rhythms(rhythms_read, RF or {}, L) if rhythms_read is not None else {}
    me = L.get('self_person') or ''
    hidden = set(L.get('hide_drives') or [])
    got = []
    for r in rows:
        c = r['cellValuesByFieldId']
        st = _name(c.get(F['status'])) or ''
        if st not in ('⬜ intention', '▶️ in motion') or not c.get(F['target']):
            continue
        t = _clean(c.get(F['title']) or '')
        rh = (c.get(F['rhythm']) or '').strip()
        pr = str(c.get(F['practice']) or '')
        if (rh in hidden or (F.get('event') and c.get(F['event'])) or (F.get('quickie') and c.get(F['quickie']))
                or (F.get('waiting') and c.get(F['waiting'])) or (pr and 'action' not in pr)):
            continue
        top, whole = fun.get(rh) or fun.get(frozenset(_words(rh))) or (None, False)
        if ((whole and _words(rh) == _words(top)) or (top and FUNWORD.search(t))) and not CHORE.search(t):
            continue                                   # it is on the fun list already
        td = to(c[F['target']])
        days = (td.date() - today).days
        if not -1 <= days <= 4:
            continue
        who = [p.strip() for f in ('person', 'mentioned') if F.get(f)
               for p in str(c.get(F[f]) or '').split(',') if p.strip() and p.strip() != me]
        who = [p for p in dict.fromkeys(who) if not re.match(r'^\W', p)]   # people with a sign are family, not waiting
        score = (3 if who else 0) + (3 if MONEY.search(t) else 0) + (1 if DEADLINE.search(t) else 0) \
            + {-1: 2.5, 0: 3, 1: 2.5, 2: 2, 3: 1.5, 4: 1}[days]
        due = ('due today' if days == 0 else 'due tomorrow' if days == 1 else 'a day past its date' if days < 0
               else f"due {_day(td)}")
        her = _her(c.get(F['details']) or '')
        links = [dict(l='link', u=u) for u in URL.findall(her)]
        if F.get('deliverable'):
            links += [dict(l='deliverable', u=u) for u in URL.findall(c.get(F['deliverable']) or '')]
        got.append(dict(t=t, why=' · '.join(([', '.join(who[:2])] if who else []) + [due]), links=links,
                        lane=top or rh or t, score=score, rid=r['id']))
    out, lanes = [], set()
    for x in sorted(got, key=lambda x: -x['score']):
        if x['lane'] in lanes:
            continue
        lanes.add(x['lane'])
        out.append({k: v for k, v in x.items() if k not in ('lane', 'score')})
        if len(out) == n:
            break
    return out
