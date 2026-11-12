#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The my week page — her my day page, applied to a whole week.

Her word, 10 Nov 2026: build a my week page for W46 by applying my day page to
the week. Same look, same parts, made for a whole week. The old week look ahead
is retired.

So this builds nothing of its own that the day page already builds. It imports
the day page's own readers and writers and runs them over seven days instead of
one:

  day_ahead.calendar()      the three calendars, read into day pages
  day_ahead.week_shape()    each day tagged the peak, open, a clash, away
  day_ahead.week_lead()     the week in one line
  day_ahead.pareto()        the rows with pull — here the possible paths
  day_ahead.horizon()       the big things coming, and what prepares them
  flow.schedule_of()        one day's cards: events, what she lived, steps
  flow.wheel_of()           a day's wellness wheel
  flow.evenness()           how evenly a day was shared
  flow.buffer_on()          the space between her and what's due
  flow.kind_of()            which kind of time a row was

and the page's furniture — the shell, the card, the theme button, the wellness
glyphs, the colours of the kinds of time, the a-or-p clock — comes from
plugins/bedo/assets/flow-parts, the same copy the my day page reads. Nothing
here borrows the my day page's stylesheet; both pages are made of those parts.

The page's order is the Monday rules in bedo-weekly-close: the week's word
first, in its own slot, then its candidates when it is still empty, then the
leverage list labelled POSSIBLE PATHS, never a queue — and the Pareto question
last.

    python3 week.py --week 46 --local day_ahead_local.json \
      --stream data/w46.json --stream data/w45.json --rhythms data/rhythms.json \
      --calendar calweek.json --practices data/practices.json \
      --template assets/week_engine.html --day-ahead <a built day-ahead page> \
      --out 2026-W46-myweek.html --now 19:10
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# the day page's own scripts: in the version store they sit in the skill next door; in a working
# folder the runner copies them in beside these, so either layout builds
DAY_DIR = next((d for d in (os.path.join(HERE, '..', '..', 'bedo-day-ahead', 'scripts'),
                            os.path.join(HERE, 'day'), HERE)
                if os.path.exists(os.path.join(d, 'day_ahead.py'))),
               os.path.join(HERE, '..', '..', 'bedo-day-ahead', 'scripts'))
sys.path.insert(0, os.path.abspath(DAY_DIR))

PARTS_DIR = next((d for d in (os.path.join(HERE, '..', '..', '..', 'assets', 'flow-parts'),
                              os.path.join(HERE, '..', 'assets', 'flow-parts'))
                  if os.path.exists(os.path.join(d, 'parts.py'))),
                 os.path.join(HERE, '..', '..', '..', 'assets', 'flow-parts'))
sys.path.insert(0, os.path.abspath(PARTS_DIR))

import day_ahead as DA   # noqa: E402
import flow as FL        # noqa: E402
import bedo_clock       # noqa: E402  the one clock: the offset from time_zone, per instant
import parts             # noqa: E402

DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DOW = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
MARK = '\U0001684E'   # 𖡎 — be•do's mark, by codepoint, never typed from memory
WEEK = 7
AHEAD = 14            # the two weeks after the week itself
OPEN_ST = ('⬜', '▶️', '▫️')


def die(msg):
    sys.stderr.write(f'week: {msg}\n')
    raise SystemExit(2)


def sunday_of(day):
    """The Sunday that opens the week this day falls in — her weeks open on Sunday."""
    return day - dt.timedelta(days=(day.weekday() + 1) % 7)


def week_dates(L, n):
    """The Sunday that opens week n, from her week-zero settings."""
    zero = dt.date.fromisoformat(L['week_zero_sunday'])
    return zero + dt.timedelta(weeks=n - L['week_zero_number'])


def hm(t):
    return t.strftime('%H:%M')


def mins_between(a, b):
    return max(0, int((b - a).total_seconds() // 60))


# ------------------------------------------------------------------ her slots
def word_slot(rows, L, start, end, given=None):
    """The week's word, first and in its own slot (the Monday rules). Hers: read from her own row
    in the week being planned, or passed in from the chat; candidates below it only while the slot
    is still empty, carry-over first."""
    pat = L.get('week_word_title') or r'^.*word.*?:\s*(.+)$'
    found, carry = None, None
    for r in sorted(rows, key=lambda r: r.get('created') or '', reverse=True):
        m = re.match(pat, r.get('title') or '')
        if not m:
            continue
        when = r.get('target') or r.get('when')
        d = DA.local(when).date() if when else None
        hit = dict(word=m.group(1).strip(),
                   words=DA.sentence_with(DA.her_words(r.get('details') or ''), [m.group(1)]) or '')
        if d and start <= d <= end and not found:
            found = hit
        elif not carry:
            carry = hit
    word = (dict(word=given, words='') if given else None) or found
    cands = []
    if not word:
        if carry:
            cands.append(dict(word=carry['word'], why='last week’s word · a carry-over is valid'))
        cands.append(dict(word='', why='or a new one, in your words'))
    return dict(word=(word or {}).get('word'), words=(word or {}).get('words') or '', candidates=cands)


def focus_practice(rows, raw, L, start, end, given=None):
    """Her one focus practice for the week (her rule, 25 Oct 2026: one, from either flow), and the
    days of this week a row already carries it — so the page says how it is going, never scores her."""
    F = L['fields']['stream']
    name = given
    if not name:
        for r in sorted(rows, key=lambda r: r.get('created') or '', reverse=True):
            m = re.match(r'(?i)^.*focus practice.*?:\s*(.+)$', r.get('title') or '')
            if m:
                name = m.group(1).strip()
                break
    if not name:
        return None
    key = FL.low(name)
    want = [w for w in key.split() if len(w) > 3]
    seen = set()
    for r in raw:
        c = r.get('cellValuesByFieldId') or {}
        pr = FL.low(DA.sv(c.get(F['practice'])) or '')
        words = ((c.get(F['title']) or '') + ' ' + (c.get(F['details']) or '')).lower()
        when = c.get(F['when'])
        if not when:
            continue
        d = DA.local(when).date()
        if not (start <= d <= end):
            continue
        if (pr and key in pr) or (want and all(w in words for w in want)):
            seen.add(d)
    days = [dict(d=(start + dt.timedelta(days=i)).isoformat(),
                 label=DAY3[(start + dt.timedelta(days=i)).weekday()],
                 done=(start + dt.timedelta(days=i)) in seen) for i in range(WEEK)]
    return dict(name=name, days=days, n=len(seen), of=WEEK)


# ------------------------------------------------------------------ the week
def day_cards(day, raw, day_page, L, C, flows, picks):
    """One day of the week, as the my day page draws a day: its calendar events, what she lived,
    and any step set for a time that day. flow.schedule_of does all of it."""
    F = L['fields']['stream']
    off = bedo_clock.Offset(L)   # per instant: a week across a clock change reads each day right
    hidden = set(L.get('hide_drives') or ())
    return FL.schedule_of(day, raw, day_page, F, off, hidden, flows, C, picks)


def paths_of(open_rows, chains, rhythms, today, L, calendared, cap=10, skip=frozenset(),
             leads=False):
    """THE REST OF WHAT'S OPEN THIS WEEK — the short folded list under the push.

    Until 9 Nov 2026 this section led with the day page's own pareto() picks. It picked a meeting
    that had already happened, a credit-card chore and a conditional chiropractor visit, and the
    four things she actually cared about were nowhere (her words: that algorithm or whatever that's
    trying to pick the top three needs some work). The leverage list is now week_push(), drive by
    drive; what is left here is the rest, with the pushed rows taken out, and nothing leads.
    `leads=True` puts the old picks back for anyone comparing the two."""
    picks, nxt, more = DA.pareto(open_rows, chains, rhythms, today, L, calendared)
    out = []
    if leads:
        for p in picks:
            r = p['row']
            mv = DA.next_move(r, chains.get(r['id']) or [], None, L['self_person'])
            out.append(dict(t=DA.clean_title(r['title']), key=r.get('key') or '', id=r['id'],
                            drive=r['rhythm'] or '', kind=p['kind'], why=p['why'],
                            st=(r['status'] or '')[:2], step=mv['step'], who=mv['who'],
                            links=mv['links'], waiting=mv['waiting'],
                            date=DA.local(r['target']).date().isoformat() if r['target'] else None,
                            lead=True))
    for m in more:
        if m['id'] in skip or len(out) >= cap:
            continue
        out.append(dict(t=m['title'], key='', id=m['id'], drive=m['drive'], kind=m['kind'],
                        why=m['due'], st=m['st'], step=None, who=None, links=[], waiting=None,
                        date=m['date'], lead=False))
    return out, nxt


# ---------------------------------------------------------------- what to push this week
# Her words on the first W46 page, 9 Nov 2026: that algorithm or whatever that's trying to pick the
# top three needs some work … help me pick like the top whatever drives that actually I can push
# forward this week, and then the actions in those drives that are the Pareto 3.
#
# So the week's unit is the DRIVE, not the row. A day asks which row to do next; a week asks which
# stretches of trail it can actually move. Three things she named as wrong, and the rule each became:
#
#   "there is no econ team meeting, that was last week"   -> a row that IS a calendar event is not an
#        action. A meeting that did not happen is still a meeting; it belongs in past its date.
#   a credit-card chore she called annoying              -> a row hanging straight off a RHYTHM is
#        rhythm activity, not drive work. Her own test: a rhythm is the country, ongoing; a drive is
#        a stretch of trail with a start and an end. Only an active drive can lead a week.
#   "my side isn't really bothering me that much anymore" -> a potential row is a maybe, not an
#        action, and a conditional one says so in its own words.
#
# And why none of the four things she actually named came up: the pull she feels is somebody waiting
# on her and a date arriving — and a PLAN names its people in `mentioned`, never in `person` (the day
# page's own note at MENTIONED_KEY). The day page's pareto() reads `person` only, so a plan due
# tomorrow with two colleagues named on it scored nothing at all. Here both fields count, and a
# date inside the week — or just behind it, still open — is the strongest pull there is.
#
# Every number below is said on the page in words, because a picker that got it wrong once has to
# show its working.
PUSH_DRIVES = 4          # the few drives — 80/20, her words: the top whatever drives
PUSH_ACTIONS = 3         # the few actions inside each
PUSH_SOON = 14           # a date this far beyond the week still pulls: it is prepared this week
PUSH_STALE = 28          # a date longer behind than this is not this week's pull
PUSH_LEAD = 60           # a date further out than this does not reach back into this week

# A DRIVE WITHOUT A DATE IS NOT THIS WEEK'S PUSH. The four things she named on the first W46 page —
# a trip to decide on, a slide for next week's meeting, a draft in front of her colleagues
# tomorrow, word out to a group waiting on her — have one thing in common: each has a hard date
# bearing down on it, and somebody else is affected by it. The rows that crowded them out had
# people on them and no date anywhere: an undated ask from a colleague is a nag, not a deadline.
# So a date somewhere on the drive is the entry fee, people raise it, and extra rows add less and
# less, because one urgent thing is a bigger push than three vague ones.
PUSH_URGENCY = ((0, 5), (14, 4), (30, 3), (PUSH_LEAD, 2))


def _people_on(r, self_name):
    """Who is waiting. A plan names its people in `mentioned`; only a logged row uses `person`."""
    out = []
    for f in ('person', DA.MENTIONED_KEY):
        for p in str(r.get(f) or '').split(','):
            p = p.strip().strip('·')
            if p and p != self_name and p not in out:
                out.append(p)
    return out


def _say_people(ps, cap=3):
    ps = ps[:cap]
    if not ps:
        return ''
    if len(ps) == 1:
        return ps[0]
    return ', '.join(ps[:-1]) + ' and ' + ps[-1]


def week_push(open_rows, chains, rhythms_read, calendared, L, today, start, end,
              pins=(), drives=PUSH_DRIVES, actions=PUSH_ACTIONS):
    """WHAT I COULD PUSH THIS WEEK — the few drives, then the few actions in each. Never a queue."""
    RF = L['fields']['rhythms']
    self_name = L.get('self_person') or ''
    hidden = set(L.get('hide_drives') or ())
    index = {}
    for c in (r['cellValuesByFieldId'] for r in rhythms_read):
        nm = c.get(RF['name']) or ''
        if nm and nm not in index:
            index[nm] = c

    def is_drive(nm):
        c = index.get(nm)
        return bool(c) and c.get(RF['status']) == 'active' \
            and str(c.get(RF['type']) or '').endswith('drive') and nm not in hidden

    def tgt(r):
        return DA.local(r['target']).date() if r['target'] else None

    left = dict(event=0, maybe=0, rhythm=0, nopull=0)
    pool = []
    for r in open_rows:
        nm = r['rhythm'] or ''
        if r['id'] in calendared:
            left['event'] += 1          # the row is the meeting, not a way to move anything
        elif (r['status'] or '').startswith('▫'):
            left['maybe'] += 1          # a maybe
        elif not is_drive(nm):
            left['rhythm'] += 1         # rhythm activity, or a drive that has finished
        else:
            pool.append(r)

    def pull(r):
        """What makes a row pull this week, and the words for why."""
        pts, why, t = 0, [], tgt(r)
        if t:
            n = (t - today).days
            if start <= t <= end and t >= today:
                pts += 5
                why.append('due today' if n == 0 else 'due tomorrow' if n == 1
                           else f'due {DA.fmt_day(t)}')
            elif t < today and (today - t).days <= PUSH_STALE:
                pts += 4
                why.append(f'was due {DA.fmt_day(t)}, still open')
            elif t > end and n <= WEEK + PUSH_SOON:
                pts += 3
                why.append(f'due {DA.fmt_day(t)} — prepared this week')
        ps = _people_on(r, self_name)
        if ps:
            pts += 3
            why.append(f'{_say_people(ps)} waiting')
        if (r['status'] or '').startswith('▶'):
            pts += 2
            why.append('already moving')
        mv = DA.next_move(r, chains.get(r['id']) or [], None, self_name)
        if mv['step']:
            pts += 1
        if mv['links']:
            pts += 1
        return pts, why, mv, t, ps

    by_drive = {}
    for r in pool:
        pts, why, mv, t, ps = pull(r)
        if pts <= 0:
            left['nopull'] += 1
            continue
        by_drive.setdefault(r['rhythm'] or '', []).append(dict(
            t=DA.clean_title(r['title']), id=r['id'], key=r.get('key') or '',
            st=(r['status'] or '')[:2], why=' · '.join(why[:2]), pull=pts,
            date=t.isoformat() if t else None, who=ps, step=mv['step'], links=mv['links'],
            waiting=(r.get('waiting') or '').strip() or None))

    def urgency(days):
        for limit, pts in PUSH_URGENCY:
            if days <= limit:
                return pts
        return 0

    lanes = []
    for nm, rs in by_drive.items():
        c = index[nm]
        rs.sort(key=lambda x: (-x['pull'], x['date'] or '9999'))
        dates = [dt.date.fromisoformat(x['date']) for x in rs if x['date']]
        dt_ = c.get(RF['target'])
        near = None
        if dt_:
            d = dt.date.fromisoformat(dt_[:10])
            dates.append(d)
            if 0 <= (d - today).days <= PUSH_LEAD:
                near = DA.fmt_day(d)
        # the nearest date on the drive, counting one just behind it as if it were today
        ahead_ = [max(0, (d - today).days) for d in dates if (today - d).days <= PUSH_STALE]
        score = urgency(min(ahead_)) if ahead_ else 0
        waiting = list(dict.fromkeys(p for x in rs[:actions] for p in x['who']))
        if score and waiting:
            score += 2
        if score and any(x['st'].startswith('▶') for x in rs[:actions]):
            score += 1
        # the rows after the first add less and less: one urgent thing beats three vague ones.
        # Nothing is added to a drive that scored nothing: no date anywhere means no lead, and a
        # pile of undated rows must never creep over that line.
        if score:
            for i, x in enumerate(rs[1:actions], start=2):
                score += x['pull'] / (i * 4)
        # why this drive, this week: the strongest two things its own rows say
        dated = [x for x in rs[:actions] if x['date'] and x['date'] <= end.isoformat()]
        say = []
        if dated:
            say.append('1 thing with a date this week' if len(dated) == 1
                       else f'{len(dated)} things with a date this week')
        if waiting:
            say.append(f'{_say_people(waiting)} waiting on you')
        if near:
            say.append(f'the drive itself is due {near}')
        if not say:
            say.append('already moving, no date on it')
        lanes.append(dict(n=nm, code=c.get(RF['code']) or '', emoji=c.get(RF['emoji']) or '',
                          parent=c.get(RF['parent']) or '',
                          goal=FL.first_sentence(c.get(RF['goal'])),
                          why=' · '.join(say[:2]), own=near, score=round(score, 2), pin=None,
                          acts=rs[:actions], more=max(0, len(rs) - actions)))
    lanes.sort(key=lambda x: (-x['score'], x['n']))

    # HER OWN PINS COME FIRST. The rule reads the rows; it cannot read what she decided this
    # morning. --push "<drive or code>::<why>" puts a drive at the top in her words, dated or not,
    # and the rule fills whatever slots are left (her words, 9 Nov 2026: help me pick — not pick
    # for me). A drive with no date at all can only get here by her hand.
    pinned, out = [], []
    for want, why in pins:
        key = want.strip().lower()
        hit = next((x for x in lanes if key in (x['n'].lower(), x['code'].lower())), None)
        if not hit:
            hit = next((x for x in lanes if key and key in x['n'].lower()), None)
        if hit and hit not in pinned:
            hit['pin'] = why.strip() or 'your pick this week'
            pinned.append(hit)
    out += pinned
    for x in lanes:
        if len(out) >= drives:
            break
        if x not in out and x['score'] > 0:
            out.append(x)
    rest = [dict(n=x['n'], code=x['code'], why=x['why'], score=x['score'])
            for x in lanes if x not in out and x['score'] > 0]
    nodate = [dict(n=x['n'], code=x['code']) for x in lanes if x['score'] <= 0]
    return dict(lanes=out, rest=rest[:6], nodate=nodate[:8], left=left, drives=len(by_drive))


def rhythm_blocks(rhythms_read, open_rows, L, today, start, end):
    """The rhythms, with their drives — the my day page's own block, over the week: tend first, then
    grow, each drive with its goal in her words and the steps open on it this week."""
    RF = L['fields']['rhythms']
    hidden = set(L.get('hide_drives') or ())
    tending = set(L.get('tending') or ())
    rows = [r['cellValuesByFieldId'] for r in rhythms_read]
    rh = [c for c in rows if (c.get(RF['status']) == 'active'
                              and str(c.get(RF['type']) or '').endswith('rhythm'))]
    drives = [c for c in rows if (c.get(RF['status']) == 'active'
                                  and str(c.get(RF['type']) or '').endswith('drive'))]
    by_rhythm = {}
    for r in open_rows:
        by_rhythm.setdefault(r['rhythm'] or '', []).append(r)
    out = []
    for c in sorted(rh, key=lambda c: str(c.get(RF['code']) or '')):
        name = c.get(RF['name']) or ''
        if name in hidden:
            continue
        kids = [d for d in drives if (d.get(RF['parent']) or '') == name
                and (d.get(RF['name']) or '') not in hidden]
        ds = []
        for d in kids:
            dn = d.get(RF['name']) or ''
            steps = [dict(t=DA.clean_title(r['title']), st=(r['status'] or '')[:2],
                          date=DA.local(r['target']).date().isoformat() if r['target'] else None,
                          dl=bool(r.get('deliverable')), mo=(r['status'] or '').startswith('▶'))
                     for r in by_rhythm.get(dn, [])]
            steps.sort(key=lambda s: (s['date'] or '9999', not s['mo']))
            if steps or d.get(RF['goal']):
                ds.append(dict(n=dn, goal=FL.first_sentence(d.get(RF['goal'])), steps=steps[:4],
                               more=max(0, len(by_rhythm.get(dn, [])) - 4)))
        own = [dict(t=DA.clean_title(r['title']), st=(r['status'] or '')[:2],
                    date=DA.local(r['target']).date().isoformat() if r['target'] else None)
               for r in by_rhythm.get(name, [])][:4]
        if ds or own:
            out.append(dict(n=name, code=c.get(RF['code']) or '', emoji=c.get(RF['emoji']) or '',
                            goal=FL.first_sentence(c.get(RF['goal'])), tend=name in tending,
                            own=own, drives=ds))
    return out


def base_flow(rows, rhythms_read, L, start, behind_dir, upto=None):
    """The week's base flow, morning by morning — the my day page's own card, run over this week's
    mornings instead of the last seven. Body, balance, buffer, in equal shares.

    It runs from the week's Sunday to `upto` (today, while the week is still going), never past it:
    the card's own words say *this morning* of the morning on its right, and a morning that has not
    happened yet is not one."""
    F = L['fields']['stream']
    RF = L['fields']['rhythms']
    off = bedo_clock.Offset(L)   # per instant: a week across a clock change reads each day right
    local = lambda ts: (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).date()
    practice = L.get('readiness_practice', 'morning oura')
    ready = {}
    for r in rows:
        c = r['cellValuesByFieldId']
        m = re.search(r'readiness (\d+)', c.get(F['title']) or '')
        if m and practice in (c.get(F['practice']) or ''):
            ready[local(c.get(F['when']) or r['createdTime'])] = int(m.group(1))
    names = {c.get(RF['name']) for c in (x['cellValuesByFieldId'] for x in rhythms_read)
             if str(c.get(RF['type']) or '').endswith('rhythm')}
    hidden = set(L.get('hide_drives') or ())
    week = []
    for i in range(WEEK):
        m = start + dt.timedelta(days=i)
        if upto and m > upto:
            break
        y = m - dt.timedelta(days=1)
        w = dict(day=m.isoformat(), label=m.strftime('%a'), yday=y.strftime('%A'),
                 body=ready.get(m), balance=None)
        bp = os.path.join(behind_dir, f'{y.isoformat()}-day-behind.html') if behind_dir else ''
        if bp and os.path.exists(bp) and 'balance' in FL.page_data(bp)[1]:
            w['balance'] = FL.evenness(FL.page_data(bp)[1]['balance']['domains'])
        else:
            dom = FL.wheel_of(y, rows, F, off)
            w['balance'] = FL.evenness(dom) if dom else None
        b = FL.buffer_on(m, rows, F, names, hidden, local)
        w['effectiveness'], w['late'] = b['value'], [b['tend'], b['grow']]
        week.append(w)
    keys = ('body', 'balance', 'effectiveness')
    live = [w for w in week if any(w[k] is not None for k in keys)]
    t = live[-1] if live else week[0]
    return dict(week=week, parts=[dict(name=k, value=t[k]) for k in keys if t[k] is not None],
                missing=[k for k in keys if t[k] is None])


def week_wheel(rows, L, start, end):
    """This week's wellness wheel, so far — the my day page's own wheel, every day of the week
    added into it. It grows with each rebuild, as the day's does through a day."""
    F = L['fields']['stream']
    off = bedo_clock.Offset(L)   # per instant: a week across a clock change reads each day right
    total, ents = {}, []
    for i in range(WEEK):
        d = start + dt.timedelta(days=i)
        if d > end:
            break
        day_ents = []
        dom = FL.wheel_of(d, rows, F, off, day_ents) or {}
        for k, v in dom.items():
            total[k] = total.get(k, 0) + v
        for e in day_ents:
            ents.append(dict(e, d=d.isoformat()))
    tot = sum(total.values())
    if not tot:
        return None
    # `v` is the wheel's own weight, as the look behind weighs it: a span's minutes over six, a
    # moment one. Not minutes, so the page shows each element's share, never an hour count.
    doms = [dict(k=k, v=round(v, 1), share=round(100 * v / tot)) for k, v in
            sorted(total.items(), key=lambda kv: -kv[1]) if v > 0]
    return dict(domains=doms, entries=ents[:400], evenness=FL.evenness(total)) if doms else None


def overdue_of(open_rows, today, L, chains):
    """Past its date — every open row past its target, oldest first, never folded away (her word,
    1 Oct 2026). The my day page's own section, over the week."""
    out = []
    for r in open_rows:
        if not r['target']:
            continue
        d = DA.local(r['target']).date()
        if d >= today:
            continue
        mv = DA.next_move(r, chains.get(r['id']) or [], None, L['self_person'])
        out.append(dict(t=DA.clean_title(r['title']), drive=r['rhythm'] or '', date=d.isoformat(),
                        days=(today - d).days, st=(r['status'] or '')[:2], step=mv['step'],
                        who=mv['who'], links=mv['links'], waiting=mv['waiting']))
    out.sort(key=lambda x: -x['days'])
    return out


# ------------------------------------------------------------------ the build
def build(a, L):
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    n = a.week if a.week is not None else (
        L['week_zero_number'] + (sunday_of(today) - dt.date.fromisoformat(L['week_zero_sunday'])).days // 7)
    start = week_dates(L, n)
    end = start + dt.timedelta(days=WEEK - 1)
    bad = bedo_clock.problem(L)
    if bad:
        die('local settings: ' + bad)

    rows, chains, latest, reads = DA.load_stream(a.stream)
    rhythms, _ = DA.load_rhythms(a.rhythms)
    open_rows, dropped = DA.filtered_open(latest)
    cal = json.load(open(a.calendar, encoding='utf-8'))
    raw = []
    seen = set()
    for p in a.stream:
        for r in json.load(open(p, encoding='utf-8'))['records']:
            if r['id'] not in seen:
                seen.add(r['id'])
                raw.append(r)

    # the three calendars, read into one day page each — the day page's own reader, over 21 days
    days, gaps, clashes, away, evs, conflicts = DA.calendar(cal, rows, open_rows, start, WEEK + AHEAD, L)
    shape = DA.week_shape(days[:WEEK], evs, conflicts, L, cap=WEEK)
    lead = DA.week_lead(shape)

    C = FL.with_drives(FL.care_settings(L), dict(drives=[
        dict(n=c.get(L['fields']['rhythms']['name']), parent=c.get(L['fields']['rhythms']['parent']))
        for c in (r['cellValuesByFieldId'] for r in json.load(open(a.rhythms, encoding='utf-8'))['records'])]), L)
    flows = frozenset(L.get('_flows') or ())
    picks = dict((p.split('::', 1) + [''])[:2] for p in a.pick)

    # a calendar event's own row is the event, never a path to recommend (J9)
    calendared = {e['match_row']['id'] for e in evs if e.get('match_row')}
    calendared |= {r['id'] for e in evs for r in (e.get('maybe') or [])}
    rh_recs = json.load(open(a.rhythms, encoding='utf-8'))['records']
    push = week_push(open_rows, chains, rh_recs, calendared, L, today, start, end,
                     pins=[(p.split('::', 1) + [''])[:2] for p in (a.push or [])])
    pushed = {x['id'] for ln in push['lanes'] for x in ln['acts']}
    paths, nxt = paths_of(open_rows, chains, rhythms, today, L, calendared, cap=a.paths,
                          skip=pushed)

    out_days = []
    for i in range(WEEK):
        d = start + dt.timedelta(days=i)
        page = next((x for x in days if x.get('date') == d.isoformat()), None)
        cards = day_cards(d, raw, page, L, C, flows, picks)
        sh = next((w for w in shape if w['date'] == d.isoformat()), {})
        out_days.append(dict(d=d.isoformat(), label=DA.fmt_day(d), dow=DOW[d.weekday()],
                             day3=DAY3[d.weekday()], weekend=d.weekday() >= 5,
                             today=d == today, past=d < today,
                             tags=sh.get('tags') or [], notes=sh.get('notes') or [],
                             hours=sh.get('hours'), n=sh.get('n'), bands=(page or {}).get('bands') or [],
                             cards=cards))

    ahead = []
    for w in range(1, 3):
        s = start + dt.timedelta(weeks=w)
        ds = []
        for i in range(WEEK):
            d = s + dt.timedelta(days=i)
            page = next((x for x in days if x.get('date') == d.isoformat()), None)
            if not page:
                continue
            ds.append(dict(d=d.isoformat(), label=DA.fmt_day(d), day3=DAY3[d.weekday()],
                           events=page.get('events') or [], due=page.get('due') or [],
                           bands=page.get('bands') or []))
        ahead.append(dict(n=n + w, label=f'W{n + w}', span=f'{DA.fmt_day(s)} – {DA.fmt_day(s + dt.timedelta(days=6))}',
                          days=ds))

    mv = lambda r, step=None: DA.next_move(r, chains.get(r['id']) or [], step, L['self_person'])
    hz = DA.horizon(open_rows, start, L, mv)

    word = word_slot(rows, L, start, end, a.word)
    data = dict(
        week=n, start=start.isoformat(), end=end.isoformat(),
        chip=f'▶️{MARK} my week W{n}',
        label=f'Week {n}',
        word=word['word'],
        span=f'{DA.fmt_day(start)} – {DA.fmt_day(end)}',
        now=a.now or None, today=today.isoformat(),
        lead=lead, wordslot=word,
        focus=focus_practice(rows, raw, L, start, end, a.focus),
        days=out_days, push=push, paths=paths, next_in_line=nxt,
        pareto=dict(q=a.pareto or ('Of these, which one — done this week — would make the rest of '
                                   'the week flow?'),
                    pick=(max((x for ln in push['lanes'] for x in ln['acts']),
                              key=lambda x: x['pull'], default={}).get('t'))),
        # how the time is going is drawn from the cards themselves, by the same kinds.js the my day
        # page colours them with, so the two pages can never disagree about what a kind of time is
        spent=dict(of=WEEK * 24 * 60, goals=L.get('time_goals') or {},
                   limits=L.get('time_limits') or {}),
        wheel=week_wheel(raw, L, start, min(end, today)),
        ahead=ahead, horizon=hz,
        rhythms=rhythm_blocks(rh_recs, open_rows, L, today, start, end),
        overdue=overdue_of(open_rows, today, L, chains),
        baseflow=base_flow(raw, rh_recs, L, start, a.behind, min(end, today)),
        calcolors=L.get('calendar_colors') or {},
        hidden=list(L.get('hide_drives') or ()),
        me=L.get('self_person') or '',
        read=dict(rows=len(rows), open=len(open_rows), events=sum(len(d.get('events') or []) for d in days),
                  gaps=gaps, clashes=clashes, dropped=len(dropped)),
    )
    return data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--week', type=int, help='the week being planned; by default the week today falls in')
    ap.add_argument('--today', help='the day this is built on, YYYY-MM-DD; default today')
    ap.add_argument('--now', help='the local clock at the write, HH:MM (I12)')
    ap.add_argument('--local', required=True)
    ap.add_argument('--stream', action='append', required=True)
    ap.add_argument('--rhythms', required=True)
    ap.add_argument('--calendar', required=True, help='the week and the two weeks after, from bedo_cal.py --build')
    ap.add_argument('--practices')
    ap.add_argument('--day-ahead', help='a built day-ahead page, for the palette its :root carries')
    ap.add_argument('--template', required=True)
    ap.add_argument('--behind', help="a folder of the week's day behinds, for balance")
    ap.add_argument('--word', help="the week's word, hers, when the chat has it and the row does not")
    ap.add_argument('--focus', help='her one focus practice for the week')
    ap.add_argument('--pareto', help='the Pareto question, in her words')
    ap.add_argument('--paths', type=int, default=10, help='how many possible paths at most')
    ap.add_argument('--push', action='append', default=[], metavar='DRIVE::WHY',
                    help='a drive she names herself, put at the top of the push in her words; '
                         'the code or the name, repeatable')
    ap.add_argument('--pick', action='append', default=[],
                    help='"<row key or record id>::<why>" — the paths as weighed in the chat')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()

    L = json.load(open(a.local, encoding='utf-8'))
    DA.install_local(L)
    if a.practices and os.path.exists(a.practices):
        L['_practices'] = a.practices
    data = build(a, L)

    page = open(a.template, encoding='utf-8').read()
    # the palette is generated, not written: it comes off a built day-ahead page's own :root, the
    # one the my day page uses, so the two pages are the same colours
    src = a.day_ahead or next(iter(sorted(glob.glob(os.path.join(
        os.path.dirname(os.path.abspath(a.local)), '*-day-ahead.html')), reverse=True)), '')
    if not src or not os.path.exists(src):
        die('no day-ahead page to take the palette from: pass --day-ahead')
    h = open(src, encoding='utf-8').read()
    root = re.search(r':root\{[^}]*--c-moss[^}]*\}', h)
    night = re.search(r'html\[data-bedo="night"\]\{[^}]*\}', h)
    if not root or not night:
        die(f'{src} carries no palette')
    page = parts.fill(page.replace('/*ROOT*/', root.group(0)).replace('/*NIGHT*/', night.group(0)))
    page = page.replace('/*DATA*/', json.dumps(data, ensure_ascii=False).replace('</', '<\\/'))
    esc = lambda t: t.replace('&', '&amp;').replace('<', '&lt;')
    page = page.replace('<title>My week</title>', f'<title>{esc(data["chip"])}</title>', 1)
    open(a.out, 'w', encoding='utf-8').write(page)
    json.dump(data, open(a.out + '.plan.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(dict(out=a.out, week=data['week'], span=data['span'], word=data['word'],
                          paths=len(data['paths']), overdue=len(data['overdue']),
                          read=data['read']), ensure_ascii=False))


if __name__ == '__main__':
    main()
