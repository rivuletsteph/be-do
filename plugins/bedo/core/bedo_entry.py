# -*- coding: utf-8 -*-
"""The entry check in code: what a stream row must satisfy before it is
written. A writer calls problems(row) and writes only when the list is empty;
the close calls it over the week to find rows that already broke a rule.

Each check is a rule a chat used to have to remember:

  I4   every select value is a full labelled choice, exactly as the base has it
  key  only an ⚡ action row with an action status carries an action key, and
       such a row always has one (a log sharing the minute is not the chain)
  span `time spent` only when there is no end; an end never before the start
  I12  datetimes are stored UTC, with the Z
  two voices  her words, then ONE divider line of three em dashes, then the
       [be•do] block, last
  week a row goes in the base whose week contains its own datetime
  gratitude one bullet per thing, her words, so she sees whether she reached three
  milestone a 🪨 milestone always names the drive (or drives) it moved
  day  a my day chat holds one day: waking on a later date, or any row past
       noon the next day, means a new day has started and needs its own chat
       (8 Oct 2026: a Wednesday chat carried Thursday's morning flow)
  practice  every row carries one (8 Oct 2026)

From the 9 Oct amendment (the 8 Oct look behind read 680 minutes on a device):

  whole  device and wellness are filled at write time, deduced by the rules in
         bedo_fill; a value that can't be deduced is asked, never left empty.
         A plan (▫️ ⬜) isn't done yet, so it carries no device
  one day  datetime and end fall on the same local day and span at most 12 h:
         closing an old row sets its datetime to the act, never a span from its
         first date (a 26 Sep row closed with an 8 Oct end drew 545 minutes).
         A night's sleep is the one row that crosses midnight
  person  people she was with or in direct contact with. A plan names them in
         mentioned until it happens

Overlap (her words, 9 Oct 2026): *I don't think anything should be beaten out
… everything like that should be recorded and then you've got partial
attention.* Two things at once are two rows, each with all its minutes; each
row that shares minutes with another carries 🌓 partial attention. Attention
belongs on any row, not only an ⚡ action. overlaps() names what a row shares.

`row` uses the logical names in facts_local.example.json's stream_fields:
datetime, end, time_spent, status, practice, key, details, phase, wellness,
emotion (a list), attention, device, rhythm.
"""
import datetime as dt, re

from bedo_reader import ACTION_STATUSES, FACTS
import bedo_fill

ALL_STATUSES = frozenset(FACTS['status']['logs'] + FACTS['status']['actions'])
KEY = re.compile(FACTS['key']['pattern'])
DIVIDER = FACTS['divider']
BLOCK = FACTS['be_do_block']
ACTION = FACTS['practice']['action']
CHOICES = {
    'phase': set(FACTS['phase']),
    'wellness': set(FACTS['wellness']['be'] + FACTS['wellness']['do']),
    'attention': set(FACTS['attention']),
    'device': set(FACTS['device']),
}
PLANS = set(FACTS['status']['plans'])
RULES = FACTS['entry_rules']
OVERNIGHT = {bedo_fill.word(p) for p in RULES['overnight_practices']}


def utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))


def week_number(day, facts=FACTS):
    """Weeks open on Sunday; the number is derived from the date, never copied
    forward."""
    w = facts['week']
    return w['anchor_number'] + (day - dt.date.fromisoformat(w['anchor_sunday'])).days // 7


def base_for(datetime_utc, utc_offset_hours, weekly_name='w{n} be•do'):
    """The weekly base a row belongs in: the week of its OWN local date."""
    local = utc(datetime_utc) + dt.timedelta(hours=utc_offset_hours)
    return weekly_name.format(n=week_number(local.date()))


def is_action(row):
    return (row.get('practice') or '').strip() == ACTION


def details_problems(d):
    if not d or BLOCK not in d:
        return []
    out = []
    lines = d.splitlines()
    divs = [i for i, l in enumerate(lines) if l.strip() == DIVIDER]
    legacy = [i for i, l in enumerate(lines) if l.strip() in FACTS['legacy_dividers']]
    if legacy:
        out.append(f'details: the divider is {DIVIDER} (three em dashes), not ---')
    if len(divs) > 1:
        out.append('details: one divider, not several')
    first_block = next(i for i, l in enumerate(lines) if BLOCK in l)
    hers = '\n'.join(lines[:first_block]).strip()
    if hers and not divs and not legacy:
        out.append(f'details: her words and the {BLOCK} block need the divider between them')
    if divs and divs[0] > first_block:
        out.append(f'details: the {BLOCK} block comes after the divider, last')
    return out


def chat_day_problem(row, chat_day, utc_offset_hours):
    """A my day chat is for one day: the date in its title. A row that shows
    the next day has begun — waking, or anything past noon the day after —
    belongs in a new chat. Noon is the dawn flow's backup close."""
    start = row.get('datetime')
    if not (chat_day and start and start.endswith('Z') and utc_offset_hours is not None):
        return None
    local = utc(start) + dt.timedelta(hours=utc_offset_hours)
    if local.date() <= chat_day:
        return None
    woke = (row.get('practice') or '').strip() == FACTS['flows']['wake']
    noon_next = dt.datetime.combine(chat_day + dt.timedelta(days=1), dt.time(12), local.tzinfo)
    if woke or local >= noon_next:
        why = 'she woke' if woke else 'this row is'
        return (f'new day: this chat is for {chat_day:%a %d %b}, and {why} on {local:%a %d %b} — '
                f'stop and ask her to open a new my day chat; write this row there, not here')
    return None


PARTIAL = FACTS['attention'][1]
NOT_LIVED = set(FACTS['status']['plans']) | {FACTS['status']['actions'][4], FACTS['status']['logs'][2]}
NOT_ACTIVITY = {bedo_fill.word(p) for p in RULES['not_activities']}


def _span(r):
    if not (r.get('datetime') and r.get('end')):
        return None
    a, b = utc(r['datetime']), utc(r['end'])
    return (a, b) if b > a else None


def overlaps(row, rows):
    """The other rows that happened and share minutes with this one. A plan,
    a dropped or skipped row, and a 📍 place (it says where, never what) share
    nothing."""
    def counts(r):
        return r.get('status') not in NOT_LIVED and bedo_fill.word(r.get('practice')) not in NOT_ACTIVITY
    me = _span(row)
    if not me or not counts(row):
        return []
    out = []
    for o in rows:
        sp = _span(o)
        if o is row or (o.get('id') and o.get('id') == row.get('id')) or not sp or not counts(o):
            continue
        if sp[0] < me[1] and me[0] < sp[1]:
            out.append(o)
    return out


def whole_problems(row, fill=None):
    """Device and wellness, or the value to write, or the question to ask."""
    ctx = fill or bedo_fill.Context()
    got, ask = bedo_fill.deduce(row, ctx)
    out = []
    for f, (v, why) in got.items():
        out.append(f'{f}: empty — deduced {v} ({why}); write it with the row')
    for f in ask:
        out.append(f'{f}: empty and not deducible — ASK her in this reply: ' + bedo_fill.ask_line(row, f, ctx))
    return out


def span_problems(row, utc_offset_hours=None):
    start, end = row.get('datetime'), row.get('end')
    if not (start and end and start.endswith('Z') and end.endswith('Z')):
        return []
    a, b = utc(start), utc(end)
    out = []
    if b - a > dt.timedelta(hours=RULES['max_span_hours']):
        out.append(f'span: {(b - a).total_seconds() / 3600:.0f} h, over {RULES["max_span_hours"]} h — '
                   'closing an old row sets its datetime to the act, never a span from its first date')
    if utc_offset_hours is not None and bedo_fill.word(row.get('practice')) not in OVERNIGHT:
        off = dt.timedelta(hours=utc_offset_hours)
        if (a + off).date() != (b + off).date():
            out.append(f'span: starts {(a + off):%a %d %b} and ends {(b + off):%a %d %b} — one row, one day; '
                       'set the datetime to the act, or split it at midnight')
    return out


def problems(row, base_name=None, utc_offset_hours=None, weekly_name='w{n} be•do', chat_day=None, fill=None,
             self_name=None):
    """`fill` is a bedo_fill.Context; without one the device rules still run and
    wellness, which needs the catalog, is asked. `self_name` is hers: her own
    name on her own plan is not someone she hasn't met yet."""
    out = []
    nd = chat_day_problem(row, chat_day, utc_offset_hours)
    if nd:
        out.append(nd)
    st, key = row.get('status'), (row.get('key') or '').strip()
    if st not in ALL_STATUSES:
        out.append(f'status: {st!r} is not one of the eight choices (I4)')
    for f, ok in CHOICES.items():
        v = row.get(f)
        if v and v not in ok:
            out.append(f'{f}: {v!r} is not a choice the base carries (I4)')
    for v in row.get('emotion') or []:
        if v not in FACTS['emotion']:
            out.append(f'emotion: {v!r} is not one of the five colours (I4)')

    if key:
        if not is_action(row):
            out.append(f'key: only an {ACTION} row carries an action key — this row is '
                       f'{row.get("practice")!r}, so it is its own row, not the chain')
        elif st not in ACTION_STATUSES:
            out.append(f'key: an action key goes with an action status, not {st!r}')
        if not KEY.match(key):
            out.append(f'key: {key!r} is not YYMMDD_HHMM (with a letter on collision)')
    elif is_action(row) and st in ACTION_STATUSES:
        out.append('key: an ⚡ action row needs its key — the first entry\'s YYMMDD_HHMM')

    start, end = row.get('datetime'), row.get('end')
    for f in ('datetime', 'end'):
        v = row.get(f)
        if v and not v.endswith('Z'):
            out.append(f'{f}: store UTC with a Z, not a local time (I12)')
    if not start:
        out.append('datetime: every row gets a time — an estimate, flagged, beats none')
    if end and row.get('time_spent'):
        out.append('time spent is written only when there is no end datetime — never both')
    if start and end and end.endswith('Z') and start.endswith('Z') and utc(end) < utc(start):
        out.append('end is before the start — a status change moved one without the other')

    out += span_problems(row, utc_offset_hours)
    out += details_problems(row.get('details'))
    prac = (row.get('practice') or '').strip()
    if not prac:
        out.append('practice: every row carries one — name it, or ask her which')
    out += whole_problems(row, fill)
    if row.get('status') in PLANS and [p for p in (row.get('person') or '').split(',')
                                         if p.strip() and p.strip() != self_name]:
        out.append(f'person: {row.get("status")} is a plan — the people go in mentioned until it happens')
    if prac == FACTS['practice']['gratitude']:
        mine = (row.get('details') or '').split(DIVIDER)[0].split(BLOCK)[0]
        lines = [l.strip() for l in mine.splitlines() if l.strip()]
        if lines and not all(l[:1] in '•-*' for l in lines):
            out.append('gratitude: one bullet per thing, in her words')
    if prac == FACTS['practice']['milestone'] and not (row.get('rhythm') or '').strip():
        out.append('milestone: names the drive it moved — ask which, never leave it bare')

    if base_name and start and utc_offset_hours is not None and start.endswith('Z'):
        want = base_for(start, utc_offset_hours, weekly_name)
        if want != base_name:
            out.append(f'base: this row\'s own date belongs in {want}, not {base_name}')
    return out
