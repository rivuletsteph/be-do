# -*- coding: utf-8 -*-
"""The dusk audit: the one-pass list, built from a FILTERED READ of the day,
never from what the chat remembers writing (A262). A window chat cannot
remember what a drive chat wrote; a read of the base can.

One pass, in this order (A250, then the gate and the flag):

  1  open intentions whose time has passed — the ⬜ rows the look ahead
     writes from the calendar (they carry the event link), which nothing owned
     closing (three on 2 Oct). A to-do dated when she said it is not one of
     these; its target is the daily flag's business.
  2  an end before its start — a status change moved one and not the other
  3  attention, DERIVED and written, never asked: an end datetime is one
     discrete session, 🌕 full; time spent means it spanned gaps, 🌓 partial
     (A262). Feeling is not asked on work sessions (drop 1, 4 Oct 2026).
  4  every chat of the day has an ⚡ row — the window chat's own entry is
     written by the close, unasked, last before the close row
  5  every working stretch has a 📲 capture row; a window chat's ⚡ row has no
     duration and no drive; a drive chat's time spent is the sum of its
     stretches, never the envelope (A251)
  ·  the gate: the dusk steps still holding the flow open, from the live
     catalog (A149) — one list, not a question per step
  ·  ⚡ rows still carrying a `for my day:` list (V52 › my day finishes them)
  ·  the daily flag: one line, at most five things, or three words
  ·  meals: every meal's prep and eating placed from context, written as
     ESTIMATED FROM CONTEXT, and shown to her as what went in the record
     (the meals amendment, 7 Oct 2026). be•do's job, never in the flag.

An observation, never a score. Nothing here writes unless --write is given,
and then only the derived attention.

    python3 bedo_dusk_audit.py --live [--chats chats.json] [--write]
    python3 bedo_dusk_audit.py --day day.json --catalog practices.json --now 2026-10-03T03:30Z
"""
import datetime as dt, json, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, on_day
from bedo_entry import is_action, overlaps, utc
import bedo_remaining as RL
import bedo_stretches as ST
import bedo_meals as ML

ST_ = FACTS['status']
INTENTION = ST_['plans'][1]
WORKED = {ST_['actions'][2], ST_['actions'][3]}           # ▶️ in motion, ✅ done
OPEN = set(ST_['open'])
FULL, PARTIAL = FACTS['attention']
CAPTURE = FACTS['practice']['capture']
MEDIA = set(FACTS['practice']['media'])
FMD = FACTS['dusk_audit']['for_my_day']
CAP = FACTS['dusk_audit']['daily_flag_cap']


def _clock(t, off):
    t = t + dt.timedelta(hours=off)
    return f'{t.hour % 12 or 12}:{t:%M} {"AM" if t.hour < 12 else "PM"}'


def _name(r):
    return r.get('title') or r.get('practice') or r['id']


def in_play(rows):
    """Queue, media and waiting-on rows are filtered out at the read."""
    return [r for r in rows if not r.get('queue') and not r.get('waiting_on')
            and (r.get('practice') or '') not in MEDIA]


def chat_of(row, chats):
    c = row.get('chat') or ''
    for ch in chats:
        if (ch.get('url') and ch['url'] in c) or (ch.get('id') and ch['id'] in c):
            return ch
    return None


def derive_attention(r, rows=()):
    """🌓 for a row that shared its minutes with another (9 Oct 2026: nothing
    is beaten out, so two things at once are each partial attention); else 🌕
    for a discrete session, 🌓 for one that spanned gaps; None when the row has
    no real span to read it from."""
    if overlaps(r, rows):
        return PARTIAL
    if r.get('end'):
        return FULL
    if r.get('time_spent'):
        return PARTIAL
    return None


def audit(rows, now, off, steps=None, chats=(), day=None, people=()):
    """The one pass. `rows` are the day's rows under logical names; `steps` the
    dusk flow's catalog steps; `chats` [{title, url|id, times}]. Returns a dict
    of findings, the attention writes, and the flag line."""
    every = rows                 # a show that happened overlaps like anything else
    rows = in_play(rows)
    acts = [r for r in rows if is_action(r)]
    window_rows = {r['id'] for r in acts if ST.is_window(_name(r))}
    for ch in chats:
        if ST.is_window(ch.get('title')):
            window_rows |= {r['id'] for r in acts if chat_of(r, [ch])}
    f = {k: [] for k in ('open_past', 'end_before_start', 'attention', 'no_attention', 'chat_no_entry',
                         'uncaptured', 'action_row', 'gate', 'for_my_day', 'no_rhythm', 'no_duration',
                         'no_person', 'target_today', 'meals')}

    for r in rows:                                                    # 1
        if (r.get('status') == INTENTION and r.get('calendar_event') and r.get('datetime')
                and utc(r['datetime']) <= now):
            f['open_past'].append(f'{_name(r)} ({_clock(utc(r["datetime"]), off)})')
    for r in rows:                                                    # 2
        if r.get('end') and r.get('datetime') and utc(r['end']) < utc(r['datetime']):
            f['end_before_start'].append(f'{_name(r)} — end {_clock(utc(r["end"]), off)}, '
                                         f'start {_clock(utc(r["datetime"]), off)}')
    writes = []
    for r in acts:                                                    # 3
        if r.get('status') in WORKED and not r.get('attention') and r['id'] not in window_rows:
            a = derive_attention(r, every)
            if a:
                writes.append({'id': r['id'], 'attention': a})
                f['attention'].append(f'{_name(r)} → {a}')
            else:
                f['no_attention'].append(_name(r))
    for ch in chats:                                                  # 4, 5
        mine = [r for r in acts if chat_of(r, [ch])]
        if not mine:
            f['chat_no_entry'].append(ch.get('title') or ch.get('url') or ch.get('id'))
        spans = ST.stretches(ch.get('times') or [])
        caps = [(r['datetime'], r.get('end')) for r in rows
                if r.get('practice') == CAPTURE and r.get('datetime')]
        for a, b in ST.uncaptured(spans, caps):
            f['uncaptured'].append(f'{ch.get("title", "a chat")}: {ST.named([(a, b)], off)}')
        for r in mine:
            for p in ST.action_row_problems(r, ch.get('title'), ST.minutes(spans) if spans else None):
                f['action_row'].append(f'{_name(r)} — {p}')
    for r in acts:
        if r['id'] in window_rows and not any(chat_of(r, [c]) for c in chats):
            for p in ST.action_row_problems(r, _name(r)):
                f['action_row'].append(f'{_name(r)} — {p}')
    if steps is not None:                                             # the gate
        f['gate'] = RL.holds_open(steps, rows, 'dusk')
    for r in acts:
        d = r.get('details') or ''
        if FMD in d:
            listed = (d.split(FMD, 1)[1].strip().splitlines() or [''])[0]
            f['for_my_day'].append(f'{_name(r)} — {listed}'.rstrip(' —'))
        if r['id'] in window_rows or r.get('status') not in WORKED:
            continue
        if not r.get('rhythm'):
            f['no_rhythm'].append(_name(r))
        if not r.get('end') and not r.get('time_spent'):
            f['no_duration'].append(_name(r))
    for r in rows:
        if not r.get('person') and r.get('practice') != CAPTURE and r.get('status') not in set(ST_['plans']):
            f['no_person'].append(_name(r))
        if is_action(r) and r.get('status') in OPEN and r.get('target') and day \
                and (utc(r['target']) + dt.timedelta(hours=off)).date() == day:
            f['target_today'].append(_name(r))
    meals = ML.propose(rows, off, people)
    f['meals'] = [m['line'] for m in meals]
    return {'findings': f, 'writes': writes, 'flag': flag(f), 'meals': meals}


def flag(f):
    """One short line naming only what didn't get captured. In V52's order,
    only when true; more than five → say that instead of listing them."""
    parts = [(len(f['gate']), 'flow steps not captured'),
             (len(f['no_attention']), '⚡ actions missing attention'),
             (len(f['no_rhythm']), '⚡ actions missing a rhythm'),
             (len(f['no_duration']), '⚡ actions with no time'),
             (len(f['no_person']), 'rows with no person'),
             (len(f['target_today']), 'targets today unresolved'),
             (len(f['chat_no_entry']), 'sessions that didn\'t log themselves')]
    parts = [f'{n} {what}' for n, what in parts if n]
    if not parts:
        return 'Nothing went uncaptured.'
    if len(parts) > CAP:
        return f'{len(parts)} kinds of thing went uncaptured today — more than five; the list is above.'
    return ' · '.join(parts)


TITLES = [('open_past', '1 open, time passed — close from the day\'s rows, or ask'),
          ('end_before_start', '2 end before start'),
          ('attention', '3 attention derived'),
          ('no_attention', '3 ⚡ done with no span to read attention from'),
          ('chat_no_entry', '4 chats with no ⚡ row — the close writes the window chat\'s, unasked'),
          ('uncaptured', '5 stretches with no 📲 capture'),
          ('action_row', '5 ⚡ row against its stretches'),
          ('gate', 'gate — still to capture before the close'),
          ('for_my_day', 'for my day, still listed'),
          ('meals', 'meals — write these ESTIMATED FROM CONTEXT, then show her what went in the record')]


def render(res, label):
    out = [label]
    for k, t in TITLES:
        items = res['findings'][k]
        if items:
            out.append(f'{t} ({len(items)})')
            out += ['  · ' + i for i in items]
    if len(out) == 1:
        out.append('every check passes')
    out.append('flag: ' + res['flag'])
    return '\n'.join(out)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the dusk audit: the one-pass list from a filtered read')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--day', help='a complete read of the day\'s rows')
    ap.add_argument('--catalog', help='a complete read of the practices catalog')
    ap.add_argument('--chats', help='JSON [{title, url|id, times | transcript}] for the day\'s chats')
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--now', help='an ISO instant, default the clock')
    ap.add_argument('--write', action='store_true', help='write the derived attention (live only)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    now = utc(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    off = offset_hours(L, now)
    day = dt.date.fromisoformat(a.date) if a.date else (now + dt.timedelta(hours=off)).date()
    names = ('datetime', 'end', 'time_spent', 'status', 'title', 'details', 'attention', 'key', 'practice',
             'person', 'rhythm', 'waiting_on', 'queue', 'chat', 'target', 'calendar_event')
    fields = {**{k: k for k in names}, **{k: v for k, v in L.get('stream_fields', {}).items() if k in names}}
    if a.live:
        from bedo_air import Air, read_day, read_catalog
        air = Air()
        names_by = air.bases()
        day_src, base = read_day(air, L, day, names_by)
        cat_src = read_catalog(air, L)
    else:
        if not a.day:
            sys.exit('give --live, or --day (and --catalog for the gate)')
        day_src, cat_src, base = a.day, a.catalog, None
    rows = on_day(as_rows(complete(day_src, 'day'), fields), day, L)
    steps = RL.flow_steps(RL.catalog(cat_src, L.get('practices_fields')), 'dusk') if cat_src else None
    chats = []
    if a.chats:
        for ch in json.load(open(a.chats, encoding='utf-8')):
            if 'transcript' in ch:
                ch['times'] = ST.times_from(ch.pop('transcript'))
            chats.append(ch)
    res = audit(rows, now, off, steps, chats, day, (L.get('people') or {}).values())
    if a.json:
        print(json.dumps(res, ensure_ascii=False, indent=1))
    else:
        print(render(res, f'dusk audit · {day:%a %d %b} · {len(rows)} rows read'))
    if a.write and res['writes']:
        if not a.live:
            sys.exit('--write needs --live')
        att = L['stream_fields']['attention']
        air.patch(names_by[base], L['stream_table'],
                  [{'id': w['id'], 'fields': {att: w['attention']}} for w in res['writes']])
        print(f'wrote attention on {len(res["writes"])} rows')


if __name__ == '__main__':
    main()
