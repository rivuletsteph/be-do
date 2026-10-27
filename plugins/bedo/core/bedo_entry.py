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
         bedo_fill. A value nothing deduces is a note, never a refusal: the row
         is written (later the same day: don't stop for a little detail).
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

From the amendments of 6 to 26 Oct 2026:

  bucket  every row that happened sits in a flow, or under a rhythm or a
          drive: deduced like wellness (a story is her stories rhythm, a window
          chat's row the system drive), else asked in passing (20, 26 Oct)
  open device  an open ⚡ action (▫️ ⬜) carries the device it will be done on
          (8 Oct): the laptop when the title says so, the phone for a quickie
          or a phone task, else asked in passing
  being/doing  an ⚡ action on a drive takes the drive's element, never a being
          area; passive rest (a show, a movie) is never a doing element (24 Oct)
  appointment  an appointment still ahead carries its calendar event link: it
          goes on her calendar, not just in the stream (6 Oct)
  weather  a sun practice the weather took is 🌥️ weather, never ⨂ skipped;
          until the base carries that choice the row is held (26 Oct)
  in the moment  a row that shares minutes with another: synergy or competition
          is read from what she says about it; when her words don't say, it is
          asked right then, once — never a day late, when she has forgotten
          (23 and 27 Oct). A note, never a refusal

`row` uses the logical names in facts_local.example.json's stream_fields:
datetime, end, time_spent, status, practice, key, details, phase, wellness,
emotion (a list), attention, device, rhythm, person, target, quickie,
calendar_event.
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
NOT_LIVED = set(FACTS['status']['plans']) | {FACTS['status']['actions'][4], FACTS['status']['logs'][2],
                                             FACTS['weather_status']['status']}
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
    """An empty device or wellness that can be deduced: the value to write."""
    got, _ = bedo_fill.deduce(row, fill or bedo_fill.Context())
    return [f'{f}: empty — deduced {v} ({why}); write it with the row' for f, (v, why) in got.items()]


def notes(row, fill=None):
    """What the row is missing that nothing can deduce. Never a refusal (her
    words, 9 Oct 2026: don't stop the process because it's missing some little
    detail): the row is written, and the chat may ask in passing."""
    ctx = fill or bedo_fill.Context()
    _, ask = bedo_fill.deduce(row, ctx)
    out = [f'{f} left empty — nothing deduces it; ask in passing if it matters: '
           + bedo_fill.ask_line(row, f, ctx) for f in ask]
    t = (row.get('title') or row.get('practice') or '?')[:60]
    b = bedo_fill.bucket(row, ctx)
    if b and not b[0]:
        out.append(f'rhythm left empty — every row sits in a flow, a rhythm or a drive; ask in passing: '
                   f'which rhythm or drive for “{t}”?')
    d = bedo_fill.open_device(row, ctx)
    if d and not d[0]:
        out.append(f'device left empty on an open action — ask in passing: laptop or phone for “{t}”?')
    out += synergy_now(row, ctx)
    return out


SY = FACTS['synergy']


def her_words(row):
    return (row.get('details') or '').split(DIVIDER, 1)[0].split(BLOCK, 1)[0]


def synergy_from(text):
    """(answer, the words it rests on) read from what she says about two things
    at once, or (None, None). Her own word first (synergy, competing), then the
    cues; both kinds in one row read as both (27 Oct 2026: deduce it from what
    I say, never ask)."""
    low = (text or '').lower()
    found = {}
    for kind in ('her_words', 'cues'):
        for ans, cues in SY.get(kind, {}).items():
            hit = next((c for c in cues if c in low), None)
            if hit and ans not in found:
                found[ans] = hit
        if found:
            break
    if len(found) > 1:
        return 'both', ' and '.join(found.values())
    return next(iter(found.items()), (None, None))


def synergy_now(row, ctx):
    """Two things at once, as she logs them: synergy or competition is read
    from what she says about it and written with the row. When her words don't
    say, ask in that same reply, once — her words, 27 Oct 2026: not that I
    never want to be asked, but when it's a day late I will have forgotten."""
    mine = her_words(row)
    if 'overlap —' in mine:
        return []
    others = overlaps(row, ctx.day_rows)
    if not others:
        return []
    o = others[0]
    ans, cue = synergy_from(mine)
    if not ans:
        ans, cue = synergy_from(her_words(o))
    who = (o.get('title') or o.get('practice') or '?')[:50]
    if not ans:
        return [f'two things at once with “{who}” and her words don\'t say how they went together — ask in this '
                f'reply, once, while it\'s fresh: did they help each other, get in each other\'s way, both, or '
                f'neither? No answer is fine; never ask it later. Her answer goes at the end of her words: '
                + SY['note'].format(answer='<answer>', partner=o.get('key') or who)]
    note = SY['note'].format(answer=ans, partner=o.get('key') or who)
    return [f'two things at once with “{who}” — her words say {ans} (“{cue}”): add the line “{note}” at the end '
            f'of her words, above the divider; she corrects in passing']


BD = FACTS['being_doing']
BEING = set(FACTS['wellness']['be'])
DOING = set(FACTS['wellness']['do'])
AP = FACTS['appointments']
WS = FACTS['weather_status']
SKIPPED = FACTS['status']['logs'][2]


def bucket_problems(row, fill=None):
    ctx = fill or bedo_fill.Context()
    out = []
    b = bedo_fill.bucket(row, ctx)
    if b and b[0]:
        out.append(f'rhythm: empty — deduced {b[0]} ({b[1]}); every row sits in a flow, a rhythm or a drive — '
                   'write it with the row')
    d = bedo_fill.open_device(row, ctx)
    if d and d[0]:
        out.append(f'device: an open action carries the device it will be done on — deduced {d[0]} ({d[1]}); '
                   'write it with the row')
    return out


def being_doing_problems(row, fill=None):
    """24 Oct 2026: being and doing stay distinct."""
    ctx = fill or bedo_fill.Context()
    w, p, out = row.get('wellness'), bedo_fill.word(row.get('practice')), []
    if is_action(row) and w in BEING and row.get('rhythm'):
        el = next((ctx.drives[d.strip()] for d in row['rhythm'].split(',') if ctx.drives.get(d.strip())), None)
        if el in DOING:
            out.append(f'wellness: work on {row["rhythm"]} takes its element {el} (doing), not {w}')
    if p in {bedo_fill.word(x) for x in BD['passive_rest']} and w in DOING:
        out.append(f'wellness: passive rest is being, never {w} — 🩷 heart with people, else what she says')
    return out


def appointment_problems(row, now=None):
    """6 Oct 2026: an appointment she shares goes on her calendar."""
    if row.get('calendar_event') or row.get('status') in NOT_LIVED - PLANS:
        return []
    p, t = bedo_fill.word(row.get('practice')), (row.get('title') or '').lower()
    named = p in {bedo_fill.word(x) for x in AP['practices']}
    if not named:
        if is_action(row) and any(t.lstrip('⚡ ').startswith(b) for b in AP['booking_words']):
            return []                                       # a to-do to book one is not the appointment
        if not any(w in t for w in AP['words']):
            return []
        when = row.get('target') or row.get('datetime')
        now = now or dt.datetime.now(dt.timezone.utc)
        if not (row.get('status') in PLANS or (when and when.endswith('Z') and utc(when) > now)):
            return []                                       # one that already happened is a log, not a booking
    return ['calendar event: an appointment goes on her calendar, not just in the stream — write the event '
            '(the calendar named, read back) and put its link on this row']


def weather_problems(row):
    """26 Oct 2026: a sun practice the weather took is neither done nor missed."""
    st, p = row.get('status'), bedo_fill.word(row.get('practice'))
    sun = p in {bedo_fill.word(x) for x in WS['practices']}
    out = []
    if st == WS['status']:
        if not sun:
            out.append(f'status: {WS["status"]} is for a sun practice the weather took, not {row.get("practice")!r}')
        elif not WS['in_base']:
            out.append(f'status: {WS["status"]} is not a choice in the base yet — hers to add in the status field; '
                       'hold this row until it is, and never write it as ⨂ skipped')
    elif sun and st == SKIPPED and any(w in (row.get('details') or '').lower() + (row.get('title') or '').lower()
                                       for w in WS['words']):
        out.append(f'status: the weather took the sun — that is {WS["status"]}, neither done nor missed, not ⨂ skipped'
                   + ('' if WS['in_base'] else '; the choice is hers to add, so hold the row until it is there'))
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
             self_name=None, now=None):
    """`fill` is a bedo_fill.Context; without one the device rules still run and
    wellness, which needs the catalog, is asked. `self_name` is hers: her own
    name on her own plan is not someone she hasn't met yet."""
    out = []
    nd = chat_day_problem(row, chat_day, utc_offset_hours)
    if nd:
        out.append(nd)
    st, key = row.get('status'), (row.get('key') or '').strip()
    if st not in ALL_STATUSES and st != WS['status']:
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
    out += bucket_problems(row, fill)
    out += being_doing_problems(row, fill)
    out += appointment_problems(row, now)
    out += weather_problems(row)
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
