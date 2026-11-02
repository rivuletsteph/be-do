# -*- coding: utf-8 -*-
"""The categorizing pass: the calls be•do makes on a day's rows, so the day
page is right before she sees it (2 Nov 2026).

Her words, Mon 2 Nov, on Sunday's day behind: *I'm really annoyed that I have
to check all this stuff* and *I don't know what needs to happen to make sure
all these little things aren't falling through the cracks.* Each rule below is
one she caught by hand on Sunday's page, now a call code makes:

  clock     on the day the clocks change, a sleep or wake row an hour off
            Oura's own instant, or a session row an hour off its stretches, is
            set to the instant (a stamp read in the old offset)
  length    a point row whose practice has a usual length (the catalog's
            typical duration, else her own median) gets that length, so it
            covers its minutes
  filler    an estimated 📝 filler row (be•do's own, no words of hers) gives
            way to rows from evidence: it keeps only the longest stretch no
            other row covers, and goes when none is left
  company   at home and in the family bed she is with the household unless a
            row says she was alone; a row inside one that names its company
            takes that company; her words saying alone (on my own, by myself,
            just her and a pet) write her alone, explicitly
  sleep     the sleep row names her too, or the page drops the night
  travel    a family car trip is 🚗 travel (riding, being), not 🚗 driving: the
            household's driver drives almost every time it's all of them; at
            the wheel only when her words say so
  wellness  a row's wellness follows its rhythm: a doing row takes the
            rhythm's element, a being row its pair (earth body, air mind,
            water heart, fire spirit). A rhythm whose rows are all one side
            says so in her settings (`rhythm_side`). Overridden only by her word
  money     Wednesday is money day: an open money step with no date of its
            own is targeted to the coming Wednesday

    changes = run(rows, day, L, ctx)     # [{id, rule, field, old, new, why}]
    rows2 = apply(rows, changes)         # the rows as the page should read them

Rows carry the logical names (datetime, end, time_spent, status, practice,
title, details, person, wellness, rhythm, device, target, chat, waiting_on).
Nothing personal lives here: the household, its driver, the pets, the rhythm
sides and the quiet topics are her settings.
"""
import copy, datetime as dt, re, statistics

from bedo_reader import FACTS, offset_hours

C = FACTS['categorize']
PLANS = set(FACTS['status']['plans'])
NOT_LIVED = PLANS | {FACTS['status']['actions'][4], FACTS['status']['logs'][2]}
DROPPED = FACTS['status']['actions'][4]
DIVIDER = FACTS['divider']
BLOCK = FACTS['be_do_block']
BE, DO = FACTS['wellness']['be'], FACTS['wellness']['do']
PAIR = {d: b for b, d in FACTS['wellness']['pairs']}           # element → its being pair
ACTION = FACTS['practice']['action']
EST = 'ESTIMATED FROM CONTEXT'


def word(practice):
    """'🤸🏻‍♀️ morning movement' → 'morning movement'."""
    return re.sub(r'\s+', ' ', re.sub(r'^[^\w]+', '', (practice or '').strip())).lower()


def utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def z(t):
    return t.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:00.000Z')


def her_words(r):
    return (r.get('details') or '').split(DIVIDER, 1)[0].split(BLOCK, 1)[0].strip()


def said(r):
    """What the row says in its own voice: the title and her words."""
    return ((r.get('title') or '') + ' \n' + her_words(r)).lower()


def people(v):
    return [p.strip() for p in (v or '').split(',') if p.strip()] if isinstance(v, str) else list(v or [])


def span(r):
    a, b = utc(r.get('datetime')), utc(r.get('end'))
    if a and not b and r.get('time_spent'):
        b = a + dt.timedelta(seconds=float(r['time_spent']))
    return (a, b) if a and b and b > a else (a, None)


def lived(r):
    return r.get('status') not in NOT_LIVED


class Ctx:
    """What the calls read, all optional: the rhythms (name → element), the
    catalog (practice → its wellness and typical minutes), her usual lengths
    from other weeks, Oura's sleep periods, the day's chats with their
    stretches, and the people away that day."""

    def __init__(self, rhythms=None, catalog=None, history=(), sleep=None, sessions=None, away=()):
        self.rhythms = {k.strip(): v for k, v in (rhythms or {}).items() if k}
        self.catalog = {word(k): v for k, v in (catalog or {}).items()}
        self.sleep = sleep or []
        self.sessions = sessions or []
        self.away = set(away)
        lens = {}
        for r in history:
            a, b = span(r)
            if b and lived(r) and b - a <= dt.timedelta(hours=3):
                lens.setdefault(word(r.get('practice')), []).append((b - a).total_seconds() / 60)
        self.usual = {p: round(statistics.median(v)) for p, v in lens.items() if len(v) >= C['usual_min_rows']}


def settings(L):
    """Her half: the household (person choices), who drives, the pets, the rhythm sides."""
    ppl = L.get('people') or {}
    me = L.get('self_person') or ppl.get('self') or ''
    house = list(L.get('household_people') or [v for k, v in ppl.items() if k != 'self' and v] or L.get('household') or [])
    driver = L.get('driver') or ppl.get('partner') or ''
    pets = list(((L.get('care') or {}).get('pet') or {}).get('names') or L.get('pets') or [])
    return me, house, driver, pets


def change(r, rule, field, new, why):
    return dict(id=r.get('id'), rule=rule, field=field, old=r.get(field), new=new, why=why,
                title=(r.get('title') or r.get('practice') or '?')[:70])


# ── the calls ────────────────────────────────────────────────────────────
def dst_day(day, L):
    a = dt.datetime.combine(day, dt.time(4), dt.timezone.utc)
    return offset_hours(L, a) != offset_hours(L, a + dt.timedelta(hours=24))


def an_hour_off(t, ref):
    return t and ref and abs(abs((t - ref).total_seconds()) - 3600) <= C['clock_slack_seconds']


def clock(rows, day, L, ctx):
    """On the day the clocks change, a stamp an hour off its source (9, 2 Nov 2026)."""
    if not dst_day(day, L):
        return []
    out = []
    ends = [(utc(p.get('start')), utc(p.get('end'))) for p in ctx.sleep if p.get('end')]
    for r in rows:
        p = word(r.get('practice'))
        if p in C['sleep_practices'] and ends:
            a, b = utc(r.get('datetime')), utc(r.get('end'))
            for s, e in ends:
                if an_hour_off(b, e) and (not a or abs((a - s).total_seconds()) < 4 * 3600):
                    out.append(change(r, 'clock', 'end', z(e), "an hour off Oura's own end on the day the clocks changed"))
                if an_hour_off(a, s) and b and abs((b - e).total_seconds()) < 4 * 3600:
                    out.append(change(r, 'clock', 'datetime', z(s), "an hour off Oura's own start on the day the clocks changed"))
        if p in C['wake_practices'] and ends:
            a = utc(r.get('datetime'))
            for _, e in ends:
                if an_hour_off(a, e):
                    out.append(change(r, 'clock', 'datetime', z(e), "an hour off Oura's wake on the day the clocks changed"))
        for s in ctx.sessions:
            if s.get('url') and s['url'] in (r.get('chat') or '') and s.get('stretches'):
                first, last = utc(s['stretches'][0][0]), utc(s['stretches'][-1][1])
                if an_hour_off(utc(r.get('datetime')), first):
                    out.append(change(r, 'clock', 'datetime', z(first), "an hour off the chat's own first turn"))
                if r.get('end') and an_hour_off(utc(r.get('end')), last):
                    out.append(change(r, 'clock', 'end', z(last), "an hour off the chat's own last turn"))
    return out


def lengths(rows, ctx):
    """A point row with a usual length gets it (7, 2 Nov 2026)."""
    out = []
    for r in rows:
        p = word(r.get('practice'))
        if not lived(r) or r.get('end') or r.get('time_spent') or not r.get('datetime'):
            continue
        cat = ctx.catalog.get(p) or {}
        if cat.get('zero') or p in C['never_lengthen']:
            continue
        m, src = cat.get('typical'), 'the catalog\'s typical duration'
        if not m and p in C['usual_length_practices']:
            m, src = ctx.usual.get(p), 'her usual length, from her other weeks'
            if not m:
                m, src = C['usual_minutes'].get(p), "a first guess (no typical duration in the catalog yet)"
        if m:
            out.append(change(r, 'length', 'end', z(utc(r['datetime']) + dt.timedelta(minutes=m)),
                              f'a point row covers its minutes: {m} min, {src}'))
    return out


def is_filler(r):
    p = word(r.get('practice'))
    return p in C['filler_practices'] and EST in (r.get('details') or '') and not her_words(r)


def filler(rows):
    """Estimated filler gives way to evidence (8, 2 Nov 2026)."""
    out = []
    ev = [span(r) for r in rows if lived(r) and not is_filler(r) and span(r)[1]]
    for r in rows:
        if not (lived(r) and is_filler(r)):
            continue
        a, b = span(r)
        if not b:
            continue
        n = int((b - a).total_seconds() // 60)
        free = [not any(x <= a + dt.timedelta(minutes=i) < y for x, y in ev) for i in range(n)]
        best, i = (0, 0), 0
        while i < n:
            if free[i]:
                j = i
                while j < n and free[j]:
                    j += 1
                if j - i > best[1] - best[0]:
                    best = (i, j)
                i = j
            else:
                i += 1
        if best == (0, n):
            continue                                  # nothing from evidence inside it: it stands
        if best[1] - best[0] < C['filler_min_minutes']:
            out.append(change(r, 'filler', 'status', DROPPED,
                              "be•do's own estimate, wholly covered now by rows from evidence (a dedupe of its own)"))
        else:
            na, nb = a + dt.timedelta(minutes=best[0]), a + dt.timedelta(minutes=best[1])
            if best[0]:
                out.append(change(r, 'filler', 'datetime', z(na), 'gives way to the rows from evidence before it'))
            if best[1] != n:
                out.append(change(r, 'filler', 'end', z(nb), 'gives way to the rows from evidence after it'))
    return out


ALONE = re.compile(C['alone_pattern'], re.I)
NOT_ALONE = re.compile(C['not_alone_pattern'], re.I)


def says_alone(r, pets, house_words):
    t = said(r)
    if NOT_ALONE.search(t):
        return False
    if ALONE.search(t):
        return True
    # just her and a pet: 'Buddy and I are walking' (the dogs count as alone, 1 Nov 2026)
    if pets and re.search(r'\b(?:%s)\b(?: and (?:i|me)\b)' % '|'.join(map(re.escape, (p.lower() for p in pets))), t):
        return not any(w in t for w in house_words)
    return False


def company(rows, L, ctx):
    """With family by default (1, 2 Nov 2026): a row says alone, or she is with them."""
    me, house, _, pets = settings(L)
    if not house:
        return []
    house = as_written(rows, house, ctx)
    house_words = [re.sub(r'^[^\w]+', '', h).lower() for h in house]
    skip = set(C['company_skip_practices'])
    cand = [r for r in rows if lived(r) and r.get('datetime') and word(r.get('practice')) not in skip
            and word(r.get('practice')) not in C['sleep_practices']]
    out, decided = [], {}
    for r in cand:                                   # what each row says of itself first
        ps = people(r.get('person'))
        if ps:
            decided[id(r)] = ps
        elif says_alone(r, pets, house_words) and me:
            decided[id(r)] = [me]
            out.append(change(r, 'company', 'person', me, 'her words say she was on her own: written alone, explicitly'))
    for r in cand:
        if id(r) in decided:
            continue
        a, b = span(r)
        holders = []
        for o in cand:
            oa, ob = span(o)
            if o is r or id(o) not in decided or not ob or ob - oa > dt.timedelta(hours=C['company_cover_hours']):
                continue
            if oa <= a and (b or a) <= ob:
                holders.append((ob - oa, o))
        if holders:
            o = min(holders, key=lambda x: x[0])[1]
            got, why = decided[id(o)], f'inside “{(o.get("title") or "?")[:40]}”, which names its company'
        else:
            got, why = house, 'at home with the household by default: alone only when a row says so'
        decided[id(r)] = got
        out.append(change(r, 'company', 'person', ', '.join(got), why))
    return out


def as_written(rows, house, ctx):
    """The household as the person field writes them ('Kid' → its person choice), less anyone away."""
    seen = [p for r in rows for p in people(r.get('person'))]
    house = [next((p for p in seen if h in p), h) for h in house]
    return list(dict.fromkeys(h for h in house if h not in ctx.away and not any(h in a for a in ctx.away)))


def sleep_names_her(rows, L, ctx):
    """The sleep row names her too, or the night drops (1, 2 Nov 2026)."""
    me, house, _, _ = settings(L)
    out = []
    for r in rows:
        if word(r.get('practice')) not in C['sleep_practices'] or not lived(r) or not me:
            continue
        ps = people(r.get('person'))
        if me in ps:
            continue
        hw = [re.sub(r'^[^\w]+', '', h).lower() for h in house]
        family_bed = not ps or (hw and all(any(h in p.lower() for p in ps) for h in hw))
        if not family_bed or re.sub(r'^[^\w]+', '', r.get('title') or '').split(' — ')[0].strip().lower() not in C['sleep_practices']:
            continue                    # someone's own sleep row ('his sleep', just him) stays his
        got = [me] + (ps or ([] if ALONE.search(said(r)) else as_written(rows, house, ctx)))
        out.append(change(r, 'sleep', 'person', ', '.join(got), 'a sleep row names her, the family bed with her'))
    return out


AT_WHEEL = re.compile(C['at_wheel_pattern'], re.I)


def travel(rows, L, persons):
    """Riding, not driving, when the household's driver is along (2, 2 Nov 2026)."""
    _, house, driver, _ = settings(L)
    out = []
    dw = re.sub(r'^[^\w]+', '', driver).lower()
    for r in rows:
        if word(r.get('practice')) != word(C['driving_practice']) or not lived(r):
            continue
        t = said(r)
        if AT_WHEEL.search(t):
            continue
        ps = people(persons.get(id(r), r.get('person')))
        along = (driver and any(driver in p or p in driver for p in ps)) or (
            house and all(any(h in p or p in h for p in ps) for h in house))      # all of them: the driver drives
        if along or (dw and re.search(r'\b%s\b (?:was )?driv' % re.escape(dw), t)):
            out.append(change(r, 'travel', 'practice', C['travel_practice'],
                              'a family car trip: riding, not at the wheel — the household\'s driver drives when all of them go'))
    return out


def side_of(r, cat_well, sides):
    s = sides.get((r.get('rhythm') or '').split(',')[0].strip())
    if s in ('being', 'doing'):
        return s
    p = word(r.get('practice'))
    if (r.get('practice') or '').strip() == ACTION or p in C['doing_practices']:
        return 'doing'
    w = r.get('wellness') or cat_well
    return 'being' if w in BE else 'doing'


HER_WELL = re.compile(C['her_wellness_pattern'], re.I)


def wellness(rows, L, ctx):
    """A row's wellness follows its rhythm (3, 2 Nov 2026). Two tiers:

    - a rhythm she has named (`rhythm_wellness` in her settings, e.g. her
      stories rhythm is spirit, her adventures fire) gives every row on it that
      wellness, whatever the activity's habit; a feed scrolled under it keeps
      its own (`rhythm_keeps`: a feed is the feed, not the story)
    - any other rhythm fills an empty wellness by its element: a doing row the
      element, a being row its pair. A value already there is left to the
      entry check's being/doing rule, so the formula never overrules a call
      already made (Sunday's family moments stay heart)
    """
    named = L.get('rhythm_wellness') or {}
    sides = L.get('rhythm_side') or {}
    keeps = set(L.get('rhythm_keeps') or C['rhythm_keeps'])
    out = []
    for r in rows:
        if HER_WELL.search(r.get('details') or ''):
            continue
        rh = (r.get('rhythm') or '').split(',')[0].strip()
        p = word(r.get('practice'))
        if rh in named and p not in keeps:
            want, why = named[rh], f'her rule: rows on {rh} take {named[rh]}'
        else:
            el = ctx.rhythms.get(rh)
            if r.get('wellness') or el not in PAIR:
                continue
            cat = (ctx.catalog.get(p) or {}).get('wellness')
            being = side_of(r, cat, sides) == 'being'
            want = PAIR[el] if being else el
            why = f'its rhythm is {el}: ' + ('a being row takes the pair' if being else 'a doing row takes the element')
        if r.get('wellness') != want:
            out.append(change(r, 'wellness', 'wellness', want, why))
    return out


MONEY = re.compile(C['money_pattern'], re.I)


def next_wednesday(t, off):
    loc = t + dt.timedelta(hours=off)
    d = loc.date() + dt.timedelta(days=(2 - loc.weekday()) % 7)
    return dt.datetime.combine(d, dt.time(12), dt.timezone.utc) - dt.timedelta(hours=off)


def money(rows, L, now=None):
    """Wednesday is money day (1 Nov 2026): an open money step with no date of its own."""
    out = []
    mr = set(L.get('money_rhythms') or ())
    for r in rows:
        if (r.get('practice') or '').strip() != ACTION or r.get('status') not in C['money_statuses']:
            continue
        if r.get('target') or r.get('waiting_on'):
            continue
        rh = {x.strip() for x in (r.get('rhythm') or '').split(',')}
        if not (rh & mr or MONEY.search(r.get('title') or '')):
            continue
        t = utc(r.get('datetime')) or now or dt.datetime.now(dt.timezone.utc)
        w = next_wednesday(max(t, now) if now else t, offset_hours(L, t))
        out.append(change(r, 'money', 'target', z(w), 'money work that isn\'t time-critical goes to Wednesday, batched'))
    return out


# ── the pass ─────────────────────────────────────────────────────────────
def run(rows, day, L, ctx=None, now=None):
    """Every call, in order; each later call sees the earlier ones applied."""
    ctx = ctx or Ctx()
    out = []

    def step(fn, *a):
        nonlocal rows
        got = fn(rows, *a)
        out.extend(got)
        rows = apply(rows, got)
    step(clock, day, L, ctx)
    step(lengths, ctx)
    step(filler)
    step(sleep_names_her, L, ctx)
    step(company, L, ctx)
    step(lambda rs: travel(rs, L, {}))
    step(lambda rs: wellness(rs, L, ctx))
    step(lambda rs: money(rs, L, now))
    return out


def apply(rows, changes):
    by = {}
    for c in changes:
        by.setdefault(c['id'], []).append(c)
    out = []
    for r in rows:
        cs = by.get(r.get('id'))
        if cs:
            r = copy.copy(r)
            for c in cs:
                r[c['field']] = c['new']
        out.append(r)
    return out


def patches(changes):
    """One patch per row, logical field → value, for the writer (through `entry`)."""
    by = {}
    for c in changes:
        by.setdefault(c['id'], {})[c['field']] = c['new']
    return [dict(id=k, fields=v) for k, v in by.items()]


def lines(changes):
    """The calls, one line each, for the QA's own work."""
    return [f'{c["rule"]} · “{c["title"]}”: {c["field"]} {c["old"] or "—"} → {c["new"]} ({c["why"]})' for c in changes]


def row_calls(row, L, ctx=None, day_rows=()):
    """The entry check's half: what the pass would change on this one row as it is written."""
    rows = [r for r in day_rows if r is not row] + [dict(row, id=row.get('id') or '_new')]
    a = utc(row.get('datetime'))
    day = (a + dt.timedelta(hours=offset_hours(L, a))).date() if a else dt.date.today()
    return [c for c in run(rows, day, L, ctx) if c['id'] == (row.get('id') or '_new')]


# ── reads ────────────────────────────────────────────────────────────────
def catalog_from(recs, L):
    """practice → {wellness, typical, zero}, from a practices dump."""
    from bedo_reader import cells, sv
    pf = L.get('practices_fields') or {}
    out = {}
    for r in recs:
        c = cells(r)
        name = sv(c.get(pf.get('practice', 'practice'), c.get('practice')))
        if not name:
            continue
        t = c.get(pf.get('typical_duration', 'typical duration'), c.get('typical duration'))
        out[name] = dict(wellness=sv(c.get(pf.get('wellness', 'wellness'), c.get('wellness'))),
                         typical=int(t) if isinstance(t, (int, float)) and t > 0 else None,
                         zero=bool(c.get(pf.get('zero_duration', 'zero duration'), c.get('zero duration'))))
    return out
