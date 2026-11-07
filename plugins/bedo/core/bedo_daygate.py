# -*- coding: utf-8 -*-
"""look_behind.day_ahead_first — the day ahead first, then its QA, then the day
behind (her amendment of 6 Nov 2026).

Her words: *I very much want an amendment that makes it clear that finishing
the day ahead first is a gate to doing the day behind.* And: *Finish the day
ahead. Make sure you QA it, then do the day behind.* On Thu 5 Nov a look behind
was built at 03:00 before the record was complete, and she caught it.

The gate, for every day:

  1. the day ahead is final  the day's one my day page has been rebuilt to the
     whole day as lived — her keeper photos on it, the stream through bedtime —
     and a row's `[be•do]` block says so in one line:

         [be•do] day ahead YYYY-MM-DD · final · v7

     It goes on the day's 👁️ look ahead row, the row whose deliverable is the
     page, the same way `[be•do] look behind YYYY-MM-DD · final` marks the look
     behind's log row. Anything after `final` (the version, a note) is free.
     `· draft` does not count, and the date the line names is the day it
     stands for, whichever row carries it. `run_day_ahead.sh final YYYY-MM-DD`
     checks the page is whole and prints the line (`final` below).
  2. the day is QA'd  the dusk close row (🌄 dusk flow close) carries the
     day's `dayqa shown YYYY-MM-DD …` line in its `[be•do]` block — the last
     line `run_checks.sh dayqa` prints. The same line on any other row is
     named, and still refuses: the close row is where the QA is recorded.
  3. only then is the day behind built.

Nothing builds the day behind while 1 or 2 is open: not the 03:00 routine
(MORNING.md), not preflight's morning `first` line, not a branch, not a chat.
The builders call `refusal()` themselves (week_look_behind.py --day,
look_behind.py), so no caller can skip it.

    python3 bedo_daygate.py check --date YYYY-MM-DD --live
    python3 bedo_daygate.py check --date YYYY-MM-DD --rows day.json
    python3 bedo_daygate.py check --date YYYY-MM-DD --local look_behind_local.json --stream data/w45.json …
    python3 bedo_daygate.py final --date YYYY-MM-DD --local day_ahead_local.json --stream data/w45.json … \\
        --page YYYY-MM-DD-myday.html [--version 7]

`check` exits 0 when the gate is open, 1 when it is closed (each FIX names the
next step). `final` exits 0 and prints the line to write when the page is
whole, 1 with what is still missing.
"""
import datetime as dt, json, os, re, sys

from bedo_reader import FACTS, cells, complete, offset_hours, read_dump, sv

# an older facts.json beside the core (an overlay copies only the .py files) still gets the gate
G = {'head': '[be\u2022do] day ahead', 'bedtime_from': '18:00', 'bedtime_until': '12:00', **(FACTS.get('day_ahead_first') or {})}
QA_MARK = FACTS['dayqa']['marker']                     # dayqa shown
DUSK_CLOSE = FACTS['flows']['close']['dusk']           # 🌄 dusk flow close
SLEEP = FACTS['practice']['sleep']                     # 😴 sleep
NOT_LIVED = set(FACTS['status']['plans']) | {FACTS['status']['actions'][4], FACTS['status']['logs'][2]}
HEAD = re.compile(r'^\s*' + re.escape(G['head']) + r' (\d{4}-\d{2}-\d{2})\s*·\s*(draft|final)\b(.*)$', re.M)
CHECK = 'look_behind.day_ahead_first'


def _word(p):
    """A practice by its words, whatever its glyph: '🌄 dusk flow close' → 'dusk flow close'."""
    return re.sub(r'\s+', ' ', re.sub(r'^[^\w]+', '', (sv(p) or '').strip())).lower()


def line(day, version=None, note=''):
    """The record that the day ahead reached its final version."""
    v = f' · v{version}' if version not in (None, '') else ''
    return f'{G["head"]} {day.isoformat()} · final{v}' + (f' · {note}' if note else '')


def day_ahead_final(rows, day):
    """The `[be•do] day ahead DAY · final` line, from whichever row carries it, or None."""
    want = day.isoformat()
    for r in rows:
        for m in HEAD.finditer(r.get('details') or ''):
            if m.group(1) == want and m.group(2) == 'final':
                return m.group(0).strip()
    return None


def _qa_lines(r, day):
    want = f'{QA_MARK} {day.isoformat()}'
    out = []
    for ln in (r.get('details') or '').splitlines():
        s = re.sub(r'^\[be•do\]\s*', '', ln.strip())
        if s.startswith(want):
            out.append(s)
    return out


def dayqa_shown(rows, day):
    """(the dusk close row's `dayqa shown DAY …` line or None, the line found on another row or None)."""
    close = elsewhere = None
    for r in rows:
        got = _qa_lines(r, day)
        if not got:
            continue
        if _word(r.get('practice')) == _word(DUSK_CLOSE):
            close = close or got[0]
        else:
            elsewhere = elsewhere or (got[0], (r.get('title') or r.get('practice') or r.get('id') or '?'))
    return close, elsewhere


def findings(rows, day):
    """[(ok, what, why)], in her order: the day ahead, then its QA."""
    out = []
    fin = day_ahead_final(rows, day)
    if fin:
        out.append((True, 'day ahead', fin))
    else:
        drafts = [m.group(0).strip() for r in rows for m in HEAD.finditer(r.get('details') or '')
                  if m.group(1) == day.isoformat()]
        had = f' (only `{drafts[-1]}`)' if drafts else ''
        out.append((False, 'day ahead',
                    f'no final day ahead for {day:%a %d %b}{had}: finish the my day page first — fetch, build it '
                    f'to the whole day as lived (her keeper photos, the stream through bedtime), republish it to '
                    f'its link, then `run_day_ahead.sh final {day.isoformat()}` and write the line it prints '
                    f'(`{line(day)} · vN`) in the 👁️ look ahead row\'s [be•do] block'))
    close, other = dayqa_shown(rows, day)
    if close:
        out.append((True, 'dayqa', close))
    elif other:
        out.append((False, 'dayqa', f'`{other[0]}` is on {str(other[1])[:40]}, not the dusk close row: '
                                    f'put it in the {DUSK_CLOSE} row\'s [be•do] block (write the close row if '
                                    f'there is none)'))
    else:
        out.append((False, 'dayqa', f'no `{QA_MARK} {day.isoformat()}` line in the dusk close row: run '
                                    f'`run_checks.sh dayqa {day.isoformat()}` against the finished day, write '
                                    f'what she accepts, then put its last line in the {DUSK_CLOSE} row\'s '
                                    f'[be•do] block'))
    return out


def is_open(rows, day):
    return all(ok for ok, _, _ in findings(rows, day))


def refusal(rows, day):
    """None when the day behind may be built; else the one message a builder dies with."""
    left = [f'{what}: {why}' for ok, what, why in findings(rows, day) if not ok]
    if not left:
        return None
    return (f'{CHECK} — the day behind for {day:%a %d %b} waits until the day ahead is finished and QA\'d '
            '(her amendment, 6 Nov 2026: finish the day ahead, make sure you QA it, then do the day behind). '
            + ' · '.join(left))


def render(day, found):
    out = [f'{CHECK} · {day:%a %d %b %Y}']
    out += [f'{"ok " if ok else "FIX"}   {what} — {why}' for ok, what, why in found]
    out.append('open: the day behind may be built' if all(ok for ok, _, _ in found)
               else 'closed: finish the day ahead, QA it, then the day behind — nothing builds it until then')
    return '\n'.join(out)


# ── is the day ahead whole enough to call final? ──────────────────────────
def _local(ts, local):
    if not ts:
        return None
    t = dt.datetime.fromisoformat(str(ts).replace('Z', '+00:00'))
    return (t + dt.timedelta(hours=offset_hours(local, t))).replace(tzinfo=None)


def bedtime(rows, day, local):
    """The night's sleep row: one that starts on the evening of `day` or before noon the next morning."""
    a = dt.datetime.combine(day, dt.time(*map(int, G['bedtime_from'].split(':'))))
    b = dt.datetime.combine(day + dt.timedelta(days=1), dt.time(*map(int, G['bedtime_until'].split(':'))))
    for r in rows:
        if _word(r.get('practice')) != _word(SLEEP) or sv(r.get('status')) in NOT_LIVED:
            continue
        t = _local(r.get('datetime') or r.get('when'), local)
        if t and a <= t < b:
            return r
    return None


def keepers(rows, day, local):
    """The day's rows she holds a keeper photo on."""
    out = []
    for r in rows:
        t = _local(r.get('datetime') or r.get('when'), local)
        if t and t.date() == day and 'keeper' in str(sv(r.get('photo')) or '').lower():
            out.append(r)
    return out


def page_photos(page):
    """How many photos the built my day page draws on its cards."""
    with open(page, encoding='utf-8') as fh:
        h = fh.read()
    return h.count('"src": "data:image') + h.count('"src":"data:image')


def whole(rows, day, local, page=None, streams=()):
    """[(ok, what, why)]: what the day ahead still lacks before it is the day's final version."""
    out = []
    s = bedtime(rows, day, local)
    if s:
        out.append((True, 'bedtime', f'the stream reaches the night: {(s.get("title") or SLEEP)[:40]} '
                                     f'from {_local(s.get("datetime") or s.get("when"), local):%a %H:%M}'))
    else:
        lived = [t for t in (_local(r.get('datetime') or r.get('when'), local) for r in rows
                             if sv(r.get('status')) not in NOT_LIVED) if t and t.date() == day]
        last = f' (the last row is at {max(lived):%H:%M})' if lived else ''
        out.append((False, 'bedtime', f'the stream stops before bedtime{last}: no {SLEEP} row for the night of '
                                      f'{day:%a %d %b} — write it from the morning Oura row, fetch, build again'))
    if page is None or not os.path.exists(page):
        out.append((False, 'page', f'no built my day page to check: `run_day_ahead.sh build {day.isoformat()}` first'))
        return out
    newest = max((os.path.getmtime(p) for p in streams if os.path.exists(p)), default=0)
    if os.path.getmtime(page) < newest:
        out.append((False, 'page', 'the page was built before the last fetch: build it again so it holds every row'))
    else:
        out.append((True, 'page', f'{os.path.basename(page)}, built from the last fetch'))
    k, n = keepers(rows, day, local), page_photos(page)
    if k and not n:
        out.append((False, 'photos', f'{len(k)} row(s) hold a keeper photo and the page shows none: build with the '
                                     f'Drive key here (BEDO_DRIVE_SA) so photos-{day.isoformat()} is read'))
    else:
        out.append((True, 'photos', f'{n} on the page · {len(k)} keeper row(s)'))
    return out


# ── reads ─────────────────────────────────────────────────────────────────
def field_map(L):
    """Logical name → field id, from facts_local (stream_fields) or a builder's settings (fields.stream)."""
    if L.get('stream_fields'):
        m = dict(L['stream_fields'])
        m.setdefault('when', m.get('datetime'))
        return {k: v for k, v in m.items() if v}
    m = dict((L.get('fields') or {}).get('stream') or {})
    m.setdefault('datetime', m.get('when'))
    return {k: v for k, v in m.items() if v}


def rows_of(recs, m):
    out = []
    for r in recs:
        c = cells(r)
        row = {k: sv(c.get(v, c.get(k))) for k, v in m.items()}
        row.update(id=r.get('id'), created=r.get('createdTime') or '')
        out.append(row)
    return out


def from_files(paths, L):
    seen, out = set(), []
    for p in paths:
        for row in rows_of(complete(p), field_map(L)):
            if row['id'] not in seen:
                seen.add(row['id']); out.append(row)
    return out


def from_rows_file(path, L):
    d = read_dump(path)
    recs = d.get('records') if isinstance(d, dict) else d
    if recs and isinstance(recs[0], dict) and ('fields' in recs[0] or 'cellValuesByFieldId' in recs[0]):
        return rows_of(recs, field_map(L))
    return list(recs or [])


def live_rows(L, day):
    """The day's rows and the next morning's (a dusk close after midnight, a final written the next day)."""
    import bedo_air
    air = bedo_air.Air()
    names = air.bases()
    recs = []
    for d in (day, day + dt.timedelta(days=1)):
        try:
            recs += bedo_air.read_day(air, L, d, names)[0]['records']
        except SystemExit:
            if d == day:
                raise
    seen, uniq = set(), []
    for r in recs:
        if r['id'] not in seen:
            seen.add(r['id']); uniq.append(r)
    return rows_of(uniq, field_map(L))


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the day ahead first, then its QA, then the day behind')
    ap.add_argument('mode', choices=['check', 'final'])
    ap.add_argument('--date', required=True)
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--rows', help='a read of the rows: logical names, or a dump')
    ap.add_argument('--stream', action='append', default=[], help="a builder's saved week reads (data/w##.json)")
    ap.add_argument('--local', help="a builder's settings file; facts_local otherwise")
    ap.add_argument('--page', help='with final: the built my day page (YYYY-MM-DD-myday.html)')
    ap.add_argument('--version', help="with final: the page's version, as the Artifact tool gave it")
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    day = dt.date.fromisoformat(a.date)
    if a.local:
        L = json.load(open(a.local, encoding='utf-8'))
    else:
        from bedo_reader import load_local
        L = load_local()
    if a.live:
        rows = live_rows(L, day)
    elif a.stream:
        rows = from_files(a.stream, L)
    elif a.rows:
        rows = from_rows_file(a.rows, L)
    else:
        sys.exit('give --live, --stream FILE …, or --rows FILE')
    if a.mode == 'check':
        found = findings(rows, day)
        print(json.dumps(dict(open=all(ok for ok, _, _ in found), found=found), ensure_ascii=False)
              if a.json else render(day, found))
        return 0 if all(ok for ok, _, _ in found) else 1
    found = whole(rows, day, L, a.page, a.stream)
    print(f'day ahead final? · {day:%a %d %b %Y}')
    for ok, what, why in found:
        print(f'{"ok " if ok else "FIX"}   {what} — {why}')
    if not all(ok for ok, _, _ in found):
        print('not final yet: fix the above, then run final again')
        return 1
    print('write this line in the 👁️ look ahead row\'s [be•do] block (page.row), then run dayqa:')
    print(line(day, a.version))
    return 0


if __name__ == '__main__':
    sys.exit(main())
