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

`row` uses the logical names in facts_local.example.json's stream_fields:
datetime, end, time_spent, status, practice, key, details, phase, wellness,
emotion (a list), attention, device, rhythm.
"""
import datetime as dt, re

from bedo_reader import ACTION_STATUSES, FACTS

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


def problems(row, base_name=None, utc_offset_hours=None, weekly_name='w{n} be•do'):
    out = []
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
    if row.get('attention') and not is_action(row):
        out.append('attention: set on ⚡ action rows only')

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

    out += details_problems(row.get('details'))
    prac = (row.get('practice') or '').strip()
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
