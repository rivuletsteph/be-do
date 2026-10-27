# -*- coding: utf-8 -*-
"""The calendar check: what an event write must satisfy before a chat calls
it done. Run it on the arguments of every create or update, and again with
the read-back.

  named    every calendar write names its calendar — hers, her son's or the
           dropped one — never the tool default (6 Oct 2026: four events
           landed on a calendar that wasn't on her account, invisible)
  read back  after writing, the event is read back from the calendar it was
           named to; until it comes back there it isn't done, and the chat
           says so in the same reply
  purple   every work event is purple, colorId 3, her employer's colour (9 Oct
           2026). Work is a drive under her work parents, or a title that
           names her work (calendar.work_words); a series is coloured on the
           series

Her calendars, work parents and work words live in facts_local under
`calendar`, never here:

    "calendar": {"calendars": {"hers": "…", "her son's": "…", "dropped": "…"},
                 "work_parents": ["…"], "work_words": ["…"]}

    python3 bedo_calendar.py event.json [--readback read.json --from CALENDAR_ID] [--rhythms rhythms.json]

`event.json` is the create_event / update_event arguments as sent, plus the
row's `drive` when it has one. Exit 0 when it passes, 1 when there is a FIX.
"""
import json, sys

from bedo_reader import FACTS, cells, complete, load_local, read_dump, sv

CAL = FACTS['calendar']


def _settings(local):
    return local.get('calendar') or {}


def is_work(event, local, parents=None):
    """A drive whose parent chain reaches one of her work parents, or a title
    naming her work. `parents` maps drive → parent name."""
    c = _settings(local)
    want = set(c.get('work_parents') or [])
    d, seen = (event.get('drive') or '').strip(), set()
    while d and d not in seen and parents:
        if d in want:
            return True
        seen.add(d)
        d = (parents.get(d) or '').strip()
    if d in want:
        return True
    t = (event.get('summary') or '').lower()
    return any(w.lower() in t for w in c.get('work_words') or [])


def _events(read):
    if isinstance(read, list):
        return read
    if isinstance(read, dict):
        for k in ('events', 'items', 'results'):
            if isinstance(read.get(k), list):
                return read[k]
        return [read.get('event') or read]
    return []


def problems(event, local, readback=None, read_from=None, parents=None):
    """(problems, the read-back line or None)."""
    c = _settings(local)
    cals = c.get('calendars') or {}
    names = {v: k for k, v in cals.items()}
    out = []
    cid = (event.get('calendarId') or '').strip()
    if not cid:
        out.append('calendar: name it — ' + (', '.join(f'{k} ({v})' for k, v in cals.items())
                                             or 'her calendars are not in facts_local yet')
                   + ' — never the tool default')
    elif cals and cid not in names:
        out.append(f'calendar: {cid} is not one of hers — ' + ', '.join(cals) + '; a write there is invisible to her')
    if is_work(event, local, parents) and str(event.get('colorId') or '') != CAL['work_color']:
        out.append(f'colour: a work event is purple — colorId {CAL["work_color"]}'
                   + (' (on the series)' if event.get('recurrenceData') else ''))
    if readback is None:
        return out, (f'read it back from {names.get(cid, cid or "the named calendar")} before calling it done; '
                     'if it does not come back there, say so in this reply')
    if read_from and cid and read_from != cid:
        out.append(f'read back from {names.get(read_from, read_from)}, not the calendar it was written to '
                   f'({names.get(cid, cid)}) — read it from there')
    want_id, want_t = event.get('eventId') or event.get('id'), (event.get('summary') or '').strip().lower()
    hit = [e for e in _events(readback) if isinstance(e, dict) and
           ((want_id and e.get('id') == want_id) or (want_t and (e.get('summary') or '').strip().lower() == want_t))]
    if not hit:
        out.append(f'read back: “{event.get("summary") or want_id}” did not come back from '
                   f'{names.get(read_from or cid, read_from or cid)} — not done; say so in this reply')
    return out, None


def drive_parents(recs, local):
    rf = local.get('rhythms_fields') or {}
    out = {}
    for r in recs:
        x = cells(r)
        n = sv(x.get(rf.get('name', 'name'), x.get('name')))
        if n:
            out[n] = sv(x.get(rf.get('parent', 'parent name'), x.get('parent name'))) or ''
    return out


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the calendar check: named, read back, work in purple')
    ap.add_argument('event')
    ap.add_argument('--readback', help='the get_event or list_events result read after the write')
    ap.add_argument('--from', dest='read_from', help='the calendar id the read-back was read from')
    ap.add_argument('--rhythms', help='a read of the rhythms table (name and parent), for work drives')
    a = ap.parse_args(argv)
    L = load_local()
    evs = json.load(open(a.event, encoding='utf-8'))
    evs = evs if isinstance(evs, list) else [evs]
    rb = read_dump(a.readback) if a.readback else None
    parents = drive_parents(complete(a.rhythms, 'rhythms'), L) if a.rhythms else None
    bad = 0
    for e in evs:
        p, line = problems(e, L, rb, a.read_from, parents)
        print(('ok    ' if not p else 'FIX   ') + (e.get('summary') or '?'))
        for x in p:
            print('      · ' + x)
        if line:
            print('      next: ' + line)
        bad += bool(p)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
