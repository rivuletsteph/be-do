#!/usr/bin/env python3
"""calendar_sync.py — the dusk close mirrors the stream onto the calendar.

The stream is the record of what HAPPENED; the calendar is the record of what
was SCHEDULED, and mirrors the stream once the day is lived. A stream row tied
to an event carries the event's link in its `event` field. At the dusk close,
each linked event takes the row's status as its title prefix (⬜ → ✔️ / ✖️) and,
(✔️, the plain check, never ✅: her word, 4 Nov 2026 — a bunch of green checks on
her calendar throws her off; the day page draws ✔️ as ✅ done)
when the row holds a real span, the row's real times.

It lives in the core since 11 Nov 2026 (her yes: keep the calendar's done
marks): the day behind that carried this step is retired, and a chat that
obeyed "retired" skipped it. The checks run it: `run_checks.sh calsync DAY`.

It never writes the calendar itself. Two steps, both printing JSON:

  1. --list    which linked events the day touches, so the chat can fetch each
               one fresh with get_event (never from a kept copy):
     python3 calendar_sync.py --list --day 2026-09-23 --local look_behind_local.json \
         --stream w39.json [--stream w38.json]

  2. --plan    what to change, given the fetched events and the calendar list:
     python3 calendar_sync.py --plan --day 2026-09-23 --local look_behind_local.json \
         --stream w39.json [--stream w38.json] --events events.json --calendars calendars.json

  --live     in place of --local and --stream: the settings row and the rows are
             read from Airtable here (the day's rows and the week's rows that
             carry an event link: two or three calls, never the whole week).

The chat then makes each change with update_event, notificationLevel NONE, and
nothing else: only the summary, and the times where the plan names them.

Rules it keeps (V51 + the 23 Sep calendar amendment):
  · only events on a calendar named in `sync_calendars`, and only events the
    user organises — an invitation from someone else is theirs, not hers
  · guest notifications off, always
  · an all-day event keeps its dates; only its prefix follows the row
  · times follow the row only when the row carries a real span (an end, or a
    time spent); a row with a start and nothing else leaves the times alone
  · streams are read live base first and deduped by record id (I15), then the
    latest row per key wins (I5); every read must be complete (I11)
Nothing personal lives in this file.
"""
import argparse, base64, json, re, sys, datetime as dt

# The one reader (I11, I15, I5) sits beside this file, in the core.
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import bedo_reader  # noqa: E402
import bedo_clock  # noqa: E402  the one clock: the offset from time_zone, per instant

KEYS = ('title', 'key', 'when', 'end', 'target', 'status', 'event', 'spent')
# the status → calendar prefix map. A plan row is ⬜ until it happens.
PREFIX = {'✅ done': '✔️', '◉ done': '✔️', '● log': '✔️',
          '✖️ dropped': '✖️', '⨂ skipped': '✖️',
          '⬜ intention': '⬜', '▶️ in motion': '⬜', '▫️potential': '▫️'}
# every prefix the calendar already carries, so one is replaced, never stacked
KNOWN = ('❔', '▫️', '▫', '⬜', '◻️', '◻', '✔️', '✔', '✅', '✖️', '✖', '▶️', '▶')
SHORT = {'m': 'gmail.com', 'g': 'group.calendar.google.com',
         'v': 'group.v.calendar.google.com', 'i': 'import.calendar.google.com'}


def die(msg):
    sys.exit('ABORT: ' + msg)


def read_dump(path):
    d = json.load(open(path, encoding='utf-8'))
    if isinstance(d, list) and d and isinstance(d[0], dict) and 'text' in d[0]:
        d = json.loads(d[0]['text'])
    return d


def sv(v):
    return v.get('name') if isinstance(v, dict) else v


def decode_link(url):
    """An event link's eid is base64 of '<event id> <calendar id>', the calendar
    shortened to '@m' for gmail.com and '@g' for a group calendar."""
    m = re.search(r'[?&]eid=([^&#]+)', url or '')
    if not m:
        return None
    raw = m.group(1)
    try:
        txt = base64.urlsafe_b64decode(raw + '=' * (-len(raw) % 4)).decode('utf-8')
    except Exception:
        return None
    ev, _, cal = txt.partition(' ')
    if '@' in cal:
        user, _, dom = cal.partition('@')
        cal = f"{user}@{SHORT.get(dom, dom)}"
    return dict(eid=raw, event_id=ev, calendar_id=cal)


# what the checks' settings call the three fields this file names differently
FACTS_NAMES = {'when': 'datetime', 'event': 'calendar_event', 'spent': 'time_spent'}


def fields_from_facts(local):
    """This file's field map from the checks' own settings (facts_local stream_fields)."""
    sf = local.get('stream_fields') or {}
    F = {k: sf.get(FACTS_NAMES.get(k, k)) for k in KEYS}
    missing = [FACTS_NAMES.get(k, k) for k in KEYS if not F[k]]
    if missing:
        die(f"facts_local stream_fields is missing {', '.join(missing)}")
    return F


def live_sources(local, day):
    """The rows a day's sync needs, read here: the day's own rows, and the week's rows that
    carry an event link (the link may sit on an earlier row of a chain). Never the whole week."""
    import bedo_air
    from bedo_entry import week_number
    air = bedo_air.Air()
    names = air.bases()
    today, want = bedo_air.read_day(air, local, day, names)
    f = local['stream_fields']['calendar_event']
    linked = air.dump(names[want], local['stream_table'], formula=f'LEN({{{f}}}&"")>0', by_id=True)
    return [today, linked]


def load(paths, F, offset):
    seen = {}
    for n, p in enumerate(paths):  # live base first (I15); a path, or a read already in hand
        label = p if isinstance(p, str) else f'live read {n + 1}'
        for r in bedo_reader.complete(read_dump(p) if isinstance(p, str) else p, label):  # I11, the one reader
            if r['id'] in seen:
                continue
            c = r.get('cellValuesByFieldId') or r.get('fields') or {}   # the connector's shape, or the API's
            row = {k: sv(c.get(v)) for k, v in F.items()}
            row.update(id=r['id'], created=r['createdTime'])
            seen[r['id']] = row
    chains = {}
    for r in seen.values():
        chains.setdefault(bedo_reader.chain_key(r['key'], r['status'], r['id']), []).append(r)
    latest = {}
    for k, ch in chains.items():
        ch.sort(key=lambda r: r['created'])
        head = ch[-1]
        if not head['event']:  # the link may sit on an earlier row of the chain
            head = dict(head, event=next((r['event'] for r in reversed(ch) if r['event']), None))
        latest[k] = head
    return latest


def utc(ts):
    return dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) if ts else None


def linked_for_day(latest, day, offset):
    out = []
    for r in latest.values():
        if not r['event']:
            continue
        dates = [(utc(r[x]) + offset).date() for x in ('when', 'end') if r.get(x)]
        if day in dates:
            out.append(r)
    return out


def span(r):
    a = utc(r['when'])
    if not a:
        return None
    if r.get('end'):
        return a, utc(r['end'])
    if r.get('spent'):
        return a, a + dt.timedelta(seconds=float(r['spent']))
    return None


def reprefix(summary, glyph):
    """Swap the status prefix, keeping the drive glyph and any spacing as it was.
    An event already carrying the right prefix comes back untouched."""
    s, had, changed = summary or '', [], True
    while changed:
        changed = False
        for g in KNOWN:
            if s.startswith(g):
                had.append(g); s = s[len(g):]; changed = True
    bare = lambda x: x.replace('\ufe0f', '')
    if len(had) == 1 and bare(had[0]) == bare(glyph):
        return summary
    gap = ' ' if s.startswith(' ') else ''
    return glyph + gap + s.lstrip(' ')


def ev_time(x):
    if 'dateTime' in x:
        return dt.datetime.fromisoformat(x['dateTime'].replace('Z', '+00:00'))
    return None


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--list', action='store_true')
    g.add_argument('--plan', action='store_true')
    ap.add_argument('--day', required=True)
    ap.add_argument('--local', help='look_behind_local.json: the field ids and the calendars to sync')
    ap.add_argument('--stream', action='append', help='the week read, live base first')
    ap.add_argument('--live', action='store_true', help='read the settings row and the rows from Airtable')
    ap.add_argument('--events')
    ap.add_argument('--calendars')
    ap.add_argument('--out')
    a = ap.parse_args()
    day = dt.date.fromisoformat(a.day)
    if a.live:
        # the checks' own settings give the field ids and the clock; the calendars to sync are
        # in the look_behind_local settings row (kept four hours, like every settings read)
        facts = bedo_reader.load_local()
        if a.local:
            L = json.load(open(a.local, encoding='utf-8'))
        else:
            from bedo_settings import fetch
            L, why = fetch('look_behind_local')
            if not L:
                die(f'the look_behind_local settings row could not be read ({why}) — pass --local FILE')
        F = fields_from_facts(facts)
        clock, sources = facts, live_sources(facts, day)
    else:
        if not (a.local and a.stream):
            die('give --live, or --local and --stream')
        L = json.load(open(a.local, encoding='utf-8'))
        fs = (L.get('fields') or {}).get('stream') or {}
        missing = [k for k in KEYS if not fs.get(k)]
        if missing:
            die(f"local settings: fields.stream is missing {', '.join(missing)}")
        F = {k: fs[k] for k in KEYS}
        clock, sources = L, a.stream
    if not L.get('sync_calendars') or not L.get('calendar_summaries'):
        die('local settings: sync_calendars and calendar_summaries are both needed')
    offset = bedo_clock.Offset(clock)   # per instant: an event across a change keeps each end's own clock
    rows = linked_for_day(load(sources, F, offset), day, offset)

    if a.list:
        fetch, bad = [], []
        for r in rows:
            d = decode_link(r['event'])
            (fetch if d else bad).append(dict(key=r['key'], title=r['title'], **(d or {'link': r['event']})))
        print(json.dumps(dict(day=a.day, fetch=fetch, unreadable_links=bad), ensure_ascii=False, indent=1))
        return

    if not (a.events and a.calendars):
        die('--plan needs --events (the fetched events) and --calendars (list_calendars)')
    cals = read_dump(a.calendars)
    cals = cals.get('calendars', cals) if isinstance(cals, dict) else cals
    by_summary = {c['summary']: c['id'] for c in cals}
    allowed = {}
    for label in L['sync_calendars']:
        s = L['calendar_summaries'].get(label)
        if s not in by_summary:
            die(f'calendar "{label}" ({s}) is not in the calendar list — read it from list_calendars, never from memory')
        allowed[by_summary[s]] = label
    # the user's ✖️ calendar, where a dropped event goes: a row's event found there
    # has already been moved, and a dropped one still on a synced calendar is listed
    # for the user to move (the connector can't move an event between calendars)
    dropped_name = L.get('dropped_calendar')
    dropped_id = by_summary.get(dropped_name) if dropped_name else None
    evs = read_dump(a.events)
    evs = evs.get('events', evs) if isinstance(evs, dict) else evs
    by_id = {(e.get('calendarId'), e['id']): e for e in evs}

    per_event = {}
    for r in rows:
        d = decode_link(r['event'])
        if d:
            per_event.setdefault((d['calendar_id'], d['event_id']), []).append(r)

    changes, left, to_move = [], [], []
    for (cal, eid), rs in per_event.items():
        e = by_id.get((cal, eid))
        name = (rs[0]['title'] or '').strip()
        if not e and dropped_id and by_id.get((dropped_id, eid)):
            left.append(dict(row=name, why=f'already on {dropped_name}')); continue
        if cal not in allowed:
            left.append(dict(row=name, why='not on a calendar be•do syncs')); continue
        if not e:
            left.append(dict(row=name, why='event not fetched — fetch it, or it was deleted')); continue
        if not (e.get('organizer') or {}).get('self'):
            left.append(dict(row=name, why='someone else organises it')); continue
        # only the event's OWN row moves it: one timed to the event. A row ABOUT the
        # event — rescheduling it, preparing for it — links it too, and closing that
        # row must not mark the event itself done.
        ea0, eb0 = ev_time(e['start']), ev_time(e['end'])
        if ea0:
            own = [x for x in rs if any(abs((utc(x[k]) - ea0).total_seconds()) <= 3600
                                        for k in ('when', 'target') if x.get(k))
                   or (utc(x['when']) and ea0 - dt.timedelta(hours=1) <= utc(x['when']) <= eb0)]
            if not own:
                left.append(dict(row=name, why='linked, but not timed to the event — a row about it, not its own')); continue
            rs = own
        glyphs = {PREFIX.get(r['status']) for r in rs} - {None}
        if len(glyphs) > 1:
            left.append(dict(row=name, why='two rows link this event and disagree: ' + ' / '.join(
                f"{r['key']} {r['status']}" for r in rs))); continue
        if not glyphs:
            left.append(dict(row=name, why=f"status {rs[0]['status']} has no calendar prefix")); continue
        glyph = glyphs.pop()
        r = rs[0]
        want = dict(calendarId=cal, eventId=eid, notificationLevel='NONE')
        why = []
        new_summary = reprefix(e.get('summary', ''), glyph)
        if new_summary != e.get('summary'):
            want['summary'] = new_summary; why.append(f"prefix → {glyph}")
        sp = span(r) if glyph == '✔️' else None
        ea, eb = ev_time(e['start']), ev_time(e['end'])
        if sp and ea and eb:
            ra, rb = sp
            if abs((ra - ea).total_seconds()) > 60 or abs((rb - eb).total_seconds()) > 60:
                loc = lambda t: (t + offset).replace(tzinfo=None).isoformat(timespec='minutes')
                tz = e['start'].get('timeZone') or L.get('time_zone')
                want.update(startTime=loc(ra), endTime=loc(rb))
                if tz:
                    want['timeZone'] = tz
                why.append(f"times → {loc(ra)[11:]}–{loc(rb)[11:]} (was {loc(ea.astimezone(dt.timezone.utc))[11:]}–{loc(eb.astimezone(dt.timezone.utc))[11:]})")
        if len(want) > 3:
            changes.append(dict(row=name, key=r['key'], calendar=allowed[cal], why='; '.join(why), update=want))
        else:
            left.append(dict(row=name, why='already matches'))
        if glyph == '✖️' and dropped_id:
            to_move.append(dict(row=name, key=r['key'], event=new_summary, calendar=allowed[cal],
                                link=e.get('htmlLink') or r['event']))
    out = dict(day=a.day, changes=changes, unchanged=left, to_move=to_move)
    if a.out:
        open(a.out, 'w', encoding='utf-8').write(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
