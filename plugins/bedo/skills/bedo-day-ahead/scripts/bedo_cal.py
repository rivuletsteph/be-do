# -*- coding: utf-8 -*-
"""bedo_cal.py — the day ahead's calendar reader, in two halves.

The Airtable token cannot read Google Calendar, so the calendars still come
through the chat's Calendar connector: one list_calendars and one list_events
per calendar, a few thousand tokens for fourteen days. This script does
everything around those calls that used to be done by hand, and refuses
anything short of a complete read of the right calendars over the right
window — a cal.json that parses but is subtly wrong gives a page that looks
calm and is wrong.

    python3 bedo_cal.py --plan  --today YYYY-MM-DD --local day_ahead_local.json [--dir cal]
    python3 bedo_cal.py --build --today YYYY-MM-DD --local day_ahead_local.json [--dir cal] [--out cal.json]

  --plan   prints what to fetch: the window, each calendar's name, the exact
           list_events arguments (with ids once cal/calendars.json exists),
           and the file each result is saved to.
  --build  reads the saved results, checks them, writes cal.json in the shape
           day_ahead.py reads, and prints one line per event so the read can
           be checked against the real calendar before anything is built.

What --build refuses (each is a way a wrong page has been built before):
  · a calendar named in the settings but not in calendars.json
  · a saved result whose "summary" is not that calendar's name — the wrong id
  · a last page that still carries nextPageToken — a short read (I11)
  · an event outside the window — the read used the wrong times
  · an event with no htmlLink — an event and its row find each other by it

Nothing personal lives here: the labels and calendar names come from the local
settings file (self_calendar, other_calendars, calendar_summaries, time_zone,
utc_offset_hours).
"""
import argparse, base64, datetime as dt, json, os, re, sys

MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
# the event keys the builder reads, and what a saved result may be trimmed to
KEEP = ('id', 'summary', 'status', 'start', 'end', 'htmlLink', 'location',
        'recurringEventId', 'transparency')
NEED = ('summary', 'start', 'end', 'htmlLink')


def die(msg):
    sys.exit('ABORT: ' + msg)


def read_dump(path):
    # a saved tool result in a claude.ai chat is wrapped [{"text": "<json>"}]; accept that as-is
    d = json.load(open(path, encoding='utf-8'))
    if isinstance(d, list) and d and isinstance(d[0], dict) and 'text' in d[0]:
        d = json.loads(d[0]['text'])
    return d


def offset_str(hours):
    sign = '-' if hours < 0 else '+'
    h = abs(hours)
    return f'{sign}{int(h):02d}:{int(round((h % 1) * 60)):02d}'


def fmt_day(d):
    return f'{DAY3[d.weekday()]} {d.day} {MON[d.month - 1]}'


def hm(t):
    return f'{t.hour:02d}:{t.minute:02d}'


def labels(L):
    if not L.get('self_calendar'):
        die('local settings: self_calendar is missing')
    labs = [L['self_calendar']] + [x for x in (L.get('other_calendars') or []) if x != L['self_calendar']]
    summ = L.get('calendar_summaries') or {}
    missing = [x for x in labs if not summ.get(x)]
    if missing:
        die(f'local settings: calendar_summaries has no name for {missing} — '
            'add the name exactly as list_calendars shows it')
    return labs, summ


def window(L, today, days):
    if 'utc_offset_hours' not in L:
        die('local settings: utc_offset_hours is missing')
    start = dt.datetime.combine(today, dt.time())
    return start, start + dt.timedelta(days=days), offset_str(L['utc_offset_hours'])


def span(e):
    s, en = e['start'], e['end']
    if 'date' in s:  # the connector gives all-day dates as '2026-09-20T00:00:00Z'; the date is what counts
        return dt.datetime.fromisoformat(s['date'][:10]), dt.datetime.fromisoformat(en['date'][:10]), True
    a = dt.datetime.fromisoformat(s['dateTime']).replace(tzinfo=None)
    b = dt.datetime.fromisoformat(en['dateTime']).replace(tzinfo=None)
    return a, b, False


def link_names(url, event_id):
    """An event link's eid is base64 of '<event id> <calendar>'. True when the
    link names this event — the one check that catches a hand-copied file
    whose ids and links drifted apart. A link with no readable eid passes."""
    m = re.search(r'[?&]eid=([^&#]+)', url or '')
    if not m:
        return True
    raw = m.group(1)
    try:
        txt = base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)).decode('utf-8')
    except Exception:
        return True
    return txt.startswith(event_id + ' ')


def calendars_file(cal_dir):
    p = os.path.join(cal_dir, 'calendars.json')
    if not os.path.exists(p):
        return None
    cals = read_dump(p)
    cals = cals.get('calendars', cals) if isinstance(cals, dict) else cals
    return {c['summary']: c['id'] for c in cals}


def plan(a, L):
    labs, summ = labels(L)
    start, end, off = window(L, dt.date.fromisoformat(a.today), a.days)
    ids = calendars_file(a.dir) or {}
    tz = L.get('time_zone')
    args = dict(startTime=start.isoformat() + off, endTime=end.isoformat() + off,
                pageSize=250, orderBy='startTime')
    if tz:
        args['timeZone'] = tz
    save = {f'{a.dir}/calendars.json': 'list_calendars — the whole result, as returned'
            + (' (already there)' if ids else '')}
    for x in labs:
        name = summ[x]
        save[f'{a.dir}/{x}.json'] = dict(
            calendar=name,
            list_events=dict(calendarId=ids.get(name) or f'<the id of "{name}" in {a.dir}/calendars.json>', **args))
    print(json.dumps(dict(
        today=a.today, window=f'{fmt_day(start)} – {fmt_day(end - dt.timedelta(days=1))}',
        save=save,
        keep='each result as returned, or trimmed to summary, nextPageToken and, per event, ' + ', '.join(KEEP)
             + '. A result that carries nextPageToken is not finished: fetch the next page and save every page as a list.',
        then=f'python3 bedo_cal.py --build --today {a.today} --local <settings> --dir {a.dir}'),
        ensure_ascii=False, indent=1))


def pages_of(d, path):
    if isinstance(d, dict):
        d = [d]
    if not (isinstance(d, list) and d and all(isinstance(p, dict) and 'summary' in p for p in d)):
        die(f'{path}: expected a list_events result (or a list of its pages), each carrying the calendar "summary"')
    for p in d:
        # a calendar with nothing in the window comes back with no "events" key at all
        # (a partner's read-only calendar, 28 Sep 2026); that is a real read of nothing
        if p.get('events') is None:
            p['events'] = []
        elif not isinstance(p['events'], list):
            die(f'{path}: "events" is not a list')
    return d


def build(a, L):
    labs, summ = labels(L)
    today = dt.date.fromisoformat(a.today)
    start, end, _ = window(L, today, a.days)
    by_name = calendars_file(a.dir)
    if by_name is None:
        die(f'{a.dir}/calendars.json is missing — save list_calendars there; the ids are read from it every run, never from memory')
    out_cals, lines = [], []
    read = {'window': f'{fmt_day(start)} – {fmt_day(end - dt.timedelta(days=1))}'}
    for x in labs:
        name = summ[x]
        if name not in by_name:
            die(f'calendar "{x}" ({name}) is not in {a.dir}/calendars.json — '
                'the name in calendar_summaries must match list_calendars exactly')
        p = os.path.join(a.dir, f'{x}.json')
        if not os.path.exists(p):
            die(f'{p} is missing — save the list_events result for "{name}" there')
        pages = pages_of(read_dump(p), p)
        for i, pg in enumerate(pages):
            s = pg.get('summary')
            if s is None:
                die(f'{p}: page {i + 1} carries no "summary" — keep it; it is how the read proves it hit "{name}"')
            if s != name:
                die(f'{p}: this is a read of "{s}", not "{name}" — the wrong calendar id was passed')
            if pg.get('nextPageToken') and i == len(pages) - 1:
                die(f'{p}: the last page still carries nextPageToken — fetch the next page and save every page as a list (I11)')
        kept = []
        for e in (e for pg in pages for e in pg['events']):
            if e.get('status') == 'cancelled':
                continue
            miss = [k for k in NEED if not e.get(k)]
            if miss:
                die(f'{p}: event {e.get("id") or e.get("summary")!r} is missing {miss}')
            if e.get('id') and not link_names(e['htmlLink'], e['id']):
                die(f'{p}: the link on "{e["summary"]}" does not carry its own id {e["id"]} — '
                    'a mistranscribed event; save the result as the connector returned it')
            try:
                ea, eb, allday = span(e)
            except (KeyError, ValueError) as ex:
                die(f'{p}: cannot read the times of {e.get("summary")!r}: {ex}')
            if eb <= start or ea >= end:
                die(f'{p}: "{e["summary"]}" ({ea.date()}) lies outside {start.date()} → {end.date()} — the read used the wrong times')
            k = {key: e[key] for key in KEEP if key in e}
            k['recurring'] = bool(e.get('recurringEventId'))
            if e.get('transparency') == 'transparent':
                k['transparent'] = True
            kept.append(k)
            when = 'all day' if allday else f'{hm(ea)}–{hm(eb)}'
            if allday and (eb - ea).days > 1:
                when = f'{fmt_day(ea)} → {fmt_day(eb - dt.timedelta(days=1))}'
            loc = e.get('location') or ''
            lines.append((ea, f'{fmt_day(ea)}  {when:14} {x + ":":9} {e["summary"]}'
                          + (' ↻' if k['recurring'] else '') + (' (free)' if k.get('transparent') else '')
                          + (f'  @ {loc}' if loc and not loc.startswith('http') else '')))
        out_cals.append({'who': x, 'events': kept})
        read[x] = f'{len(kept)}/{len(kept)}'
    with open(a.out, 'w', encoding='utf-8') as fh:
        json.dump({'calendars': out_cals, 'read': read}, fh, ensure_ascii=False)
    for _, line in sorted(lines, key=lambda t: t[0]):
        print(line)
    print(f'{a.out} written: ' + ' · '.join(f'{x} {read[x]}' for x in labs) + f' · {read["window"]}')


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--plan', action='store_true')
    g.add_argument('--build', action='store_true')
    ap.add_argument('--today', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--dir', default='cal', help='where the saved connector results live')
    ap.add_argument('--out', default='cal.json')
    ap.add_argument('--days', type=int, default=14)
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    (plan if a.plan else build)(a, L)


if __name__ == '__main__':
    main()
