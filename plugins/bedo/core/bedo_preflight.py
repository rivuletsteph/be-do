# -*- coding: utf-8 -*-
"""Preflight: what a chat used to have to remember before its first write,
returned instead, so the turn pastes it rather than composes it (A219).

  A8 · A219  the chat-name line, fully formed, is the FIRST line it prints,
             alone: status, date, day emoji, the mark, the week number, the
             kind, and the chat's letter when the day has more than one —
             lowercase, right after the date, so the titles sort and stay one
             width: ▶️1004c ☀️ Sun 𖡎 W41 🔆 my day (her word, 4 Oct 2026;
             replaces P1 P2 at the end).
             Week number and day emoji are derived, never copied forward —
             seven daily titles once carried a wrong week.
  I12 · A83  the clock: a chat's sense of the date is a memory of when it
             STARTED. The stamp here is the machine's, and the offset in
             facts_local is checked against the time zone on the day.
  I2         the base is resolved BY NAME from the date, never an id from
             memory; its newest row must be within ~36 h, or it is the wrong
             base and the run stops.
  I14        when yesterday sits in the previous week, that base is named too.
  A37        a handoff, when given, must name the same base.
  J8         a my day chat opens on yesterday's look behind: the link, built at
             03:00 by the routine (bedo-look-behind/MORNING.md), and the title
             yesterday's chat takes once she says she has seen it — a my day
             chat is ✔️ complete once its look behind has been seen (her word,
             8 Oct 2026).
  paper      an active amendment no check in code enforces is named, one line
             each: `rule on paper only` (9 Oct 2026). The map from amendment
             to check is hers, in facts_local (bedo_rules says how).

    python3 bedo_preflight.py --live                  # my day
    python3 bedo_preflight.py --live --kind week      # my week
    python3 bedo_preflight.py --bases names.json --stream w41.json [--amendments amendments.json]
"""
import datetime as dt, glob, json, re, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, read_dump
from bedo_entry import utc, week_number
import bedo_rules

MARK = chr(int(FACTS['glyph_codepoints']['mark'][2:], 16))
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
WITHIN = FACTS['preflight']['newest_row_within_hours']


def chat_name(day, kind='day', part=None, status=FACTS['chat_status']['moving'], week=None):
    """The fixed-width title line. A day: ▶️1004 ☀️ Sun 𖡎 W41 🔆 my day, or
    ▶️1004c ☀️ Sun 𖡎 W41 🔆 my day for its third chat.
    A week: ▶️𖡎 my week W40 — titled by the week under review, so give
    `week` when the close runs in the next one. `part` is the chat's letter
    when its day or week has more than one; a number is turned into one."""
    if isinstance(part, int):
        part = chr(ord('A') + part - 1)
    if kind == 'week':
        p = f' {part.upper()}' if part else ''      # a week keeps its letter at the end until she says otherwise
        return f'{status}{MARK} my week W{week or week_number(day)}{p}'
    d3 = DAY3[day.weekday()]
    p = part.lower() if part else ''
    return f'{status}{day:%m%d}{p} {FACTS["day_emoji"][d3]} {d3} {MARK} W{week_number(day)} 🔆 my day'


def clock(local, now=None):
    """(now UTC, now local, offset hours, problems)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    off = offset_hours(local, now)
    out = []
    fixed = local.get('utc_offset_hours')
    if fixed is not None and local.get('time_zone') and fixed != off:
        out.append(f'clock: facts_local says UTC{fixed:+g} but {local["time_zone"]} is UTC{off:+g} today — '
                   'update utc_offset_hours')
    return now, now + dt.timedelta(hours=off), off, out


def bases_in_play(day, local):
    """The weekly base for today and, when yesterday is in another week, that
    one too (I14) — live base first."""
    name = local.get('weekly_name', 'w{n} be•do')
    weeks = [week_number(day)]
    if week_number(day - dt.timedelta(days=1)) != weeks[0]:
        weeks.append(weeks[0] - 1)
    return [name.format(n=n) for n in weeks]


def newest(rows, now):
    """The newest stream datetime that is not in the future — a row written
    ahead from the calendar proves nothing about whether the base is live."""
    ts = [utc(r['datetime']) for r in rows if r.get('datetime')]
    ts = [t for t in ts if t <= now]
    return max(ts) if ts else None


def stream_rows(src, fields):
    """The stream rows preflight judges the base by. Preflight asks one thing,
    the newest row, so a read sorted newest first answers it in five records:
    in Cowork every record read is a record the chat writes out again, and a
    full read cost 125 rows (6 Oct). A short read that is not newest first
    could hide the newest row, so it stops (I11)."""
    d = read_dump(src)
    recs = d.get('records') if isinstance(d, dict) else None
    tot = (d.get('metadata') or {}).get('totalRecordCount') if isinstance(d, dict) else None
    if recs is not None and tot is not None and len(recs) == tot:
        return as_rows(recs, fields)
    rows = as_rows(recs or [], fields)
    ts = [r.get('datetime') or '' for r in rows]
    if rows and all(ts) and ts == sorted(ts, reverse=True):
        return rows
    return as_rows(complete(src, 'stream'), fields)   # stops, and says why


def check_base(names, rows, now, day, local, handoff=None):
    """(base name, problems, stop). `names` maps base name → id."""
    want = bases_in_play(day, local)
    out, stop = [], False
    if want[0] not in names:
        out.append(f'base: no base named {want[0]} — the close may not have cloned it yet')
        stop = True
    if len(want) > 1 and want[1] not in names:
        out.append(f'base: yesterday sits in {want[1]}, and no base has that name')
    t = newest(rows, now)
    if t is None:
        out.append(f'base: {want[0]} has no row dated before now — wrong base, or an empty one')
        stop = True
    elif now - t > dt.timedelta(hours=WITHIN):
        h = (now - t).total_seconds() / 3600
        out.append(f'base: the newest row in {want[0]} is {h:.0f} h old, over {WITHIN} h — wrong base (I2)')
        stop = True
    if handoff:
        named = set(re.findall(r'w\d+ be•do', handoff))
        if named and want[0] not in named:
            out.append(f'handoff names {", ".join(sorted(named))}, the date says {want[0]} — read the handoff again')
    return want, out, stop


def look_behind_url(local):
    """The living page the 03:00 routine publishes to: facts_local's
    `look_behind_url`, else the look behind's own settings in the synced skill."""
    if local.get('look_behind_url'):
        return local['look_behind_url']
    for p in glob.glob('/root/.claude/skills/synced/*/bedo-look-behind/assets/look_behind_local.json'):
        try:
            return json.load(open(p, encoding='utf-8')).get('artifact_url')
        except (OSError, ValueError):
            pass
    return None


def yesterday_line(day, url):
    """What the morning chat shows first: yesterday's look behind, and the
    title yesterday's chat takes once she has seen it."""
    y = day - dt.timedelta(days=1)
    seen = chat_name(y, status=FACTS['chat_status']['window_closed'])
    return (f'first  yesterday\'s look behind · {url or "the look behind page (no link in the settings)"}\n'
            f'       once she has seen it, yesterday\'s chat becomes {seen}')


def report(local, names, rows, now=None, kind='day', part=None, week=None, handoff=None, amendments=None):
    now, now_local, off, probs = clock(local, now)
    day = now_local.date()
    want, bprobs, stop = check_base(names, rows, now, day, local, handoff)
    lines = [chat_name(day, kind, part, week=week),
             f'clock  {now:%Y-%m-%dT%H:%M}Z · {now_local:%a %d %b %H:%M} local (UTC{off:+g})',
             f'base   {want[0]}' + (f' · and {want[1]} for yesterday' if len(want) > 1 else '')]
    t = newest(rows, now)
    if t:
        lines.append(f'newest {(now - t).total_seconds() / 3600:.1f} h ago')
    if kind == 'day':
        lines.append(yesterday_line(day, look_behind_url(local)))
    lines += ['⚠ ' + p for p in probs + bprobs]
    if amendments is not None:
        lines += ['⚠ ' + p for p in bedo_rules.lines(amendments, local.get('amendment_checks'))]
    if stop:
        lines.append('STOP: verify the base before any read or write (I2)')
    return '\n'.join(lines), stop


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='preflight: the chat-name line, the clock, the base')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--bases', help='a JSON map of base name to id')
    ap.add_argument('--stream', help='a complete read of the live base\'s stream')
    ap.add_argument('--kind', choices=['day', 'week'], default='day')
    ap.add_argument('--part', help="the chat's letter when the day has more than one: a, b, c…")
    ap.add_argument('--week', type=int, help='the week under review, for a my week chat')
    ap.add_argument('--handoff', help='the week\'s handoff file')
    ap.add_argument('--amendments', help='a read of the amendments table')
    a = ap.parse_args(argv)
    L = load_local()
    fields = {'datetime': L.get('stream_fields', {}).get('datetime', 'datetime')}
    now, now_local, _, _ = clock(L)
    if a.live:
        from bedo_air import Air
        air = Air()
        names = air.bases()
        want = bases_in_play(now_local.date(), L)[0]
        rows = []
        if want in names:
            f = fields['datetime']
            src = air.dump(names[want], L['stream_table'], by_id=True, maxRecords=5,
                           formula=f"IS_BEFORE({{{f}}}, NOW())",
                           **{'sort[0][field]': f, 'sort[0][direction]': 'desc'})
            rows = as_rows(src['records'], fields)
        amend = (L.get('bases') or {}).get('amendments')
        amendments = bedo_rules.active(air.records(*amend, by_id=bool(L.get('amendments_fields'))), L) if amend else None
    else:
        if not (a.bases and a.stream):
            sys.exit('give --live, or both --bases and --stream')
        names = json.load(open(a.bases, encoding='utf-8'))
        rows = stream_rows(a.stream, fields)
        amendments = bedo_rules.active(complete(a.amendments, 'amendments'), L) if a.amendments else None
    handoff = open(a.handoff, encoding='utf-8').read() if a.handoff else None
    text, stop = report(L, names, rows, now, a.kind, a.part, a.week, handoff, amendments)
    print(text)
    sys.exit(1 if stop else 0)


if __name__ == '__main__':
    main()
