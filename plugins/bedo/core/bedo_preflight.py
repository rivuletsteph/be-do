# -*- coding: utf-8 -*-
"""Preflight: what a chat used to have to remember before its first write,
returned instead, so the turn pastes it rather than composes it (A219).

  A8 · A219  the chat-name line, fully formed, is the FIRST line it prints,
             alone: status, date, day emoji, the mark, the week number, the
             kind, and the chat's letter when the day has more than one —
             lowercase, right after the date, so the titles sort and stay one
             width: ▶️🔆1004c ☀️ Sun 𖡎 W41 my day (her word, 4 Oct 2026;
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
             The page is one living URL, so the link alone says nothing about
             which day it shows: preflight reads the look behind's log rows
             (`[be•do] look behind YYYY-MM-DD · final`) and gives the link only
             when yesterday's final is there. Otherwise it says plainly that
             yesterday's page wasn't built, and which day the page still shows
             (27 Oct 2026: Sunday's day behind was offered as Monday's).
             And the day ahead comes first (her amendment, 6 Nov 2026: finish
             the day ahead, make sure you QA it, then do the day behind): while
             yesterday's day ahead has no final line or its dusk close row no
             dayqa line (bedo_daygate, look_behind.day_ahead_first), the line
             offers to finish the day ahead and run the QA — never to build
             the day behind, and never shows one built early as yesterday's.
  due        what the skills schedule (facts skills_schedule) says is due now:
             dawn before noon, dusk after 7 PM, the close on Sunday, the ahead
             review by the 5th (20 Oct 2026: so she doesn't have to remember)
  paper      an active amendment no check in code enforces is named, one line
             each: `rule on paper only` (9 Oct 2026). The map from amendment
             to check is hers, in facts_local (bedo_rules says how).

    python3 bedo_preflight.py --live                  # my day
    python3 bedo_preflight.py --live --kind week      # my week
    python3 bedo_preflight.py --bases names.json --stream w41.json [--amendments amendments.json] \
        [--look-behind log_rows.json]
"""
import datetime as dt, glob, json, re, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, read_dump
import bedo_clock  # noqa: E402  the one clock
from bedo_entry import utc, week_number
import bedo_daygate
import bedo_rules

MARK = chr(int(FACTS['glyph_codepoints']['mark'][2:], 16))
DAY3 = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
WITHIN = FACTS['preflight']['newest_row_within_hours']


def chat_name(day, kind='day', part=None, status=FACTS['chat_status']['moving'], week=None):
    """The fixed-width title line. A day: ▶️🔆1004 ☀️ Sun 𖡎 W41 my day, or
    ▶️🔆1004c ☀️ Sun 𖡎 W41 my day for its third chat. The status leads, then the
    sun, so a my day chat stands out in her list at a glance (her word, 28 Oct 2026).
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
    return f'{status}🔆{day:%m%d}{p} {FACTS["day_emoji"][d3]} {d3} {MARK} W{week_number(day)} my day'


def branch_name(day, n=None, what=None, status=FACTS['chat_status']['moving']):
    """A branch chat's title (12 Nov 2026, her words: we need to start numbering
    the branches): ▶️↳1112.4 🌳 Thu 👁️ my day page. The number is the order the
    branch opened that day and stays with it to its close. It comes from the
    day's session list, never from memory, so with none given the title says so."""
    d3 = DAY3[day.weekday()]
    return f'{status}↳{day:%m%d}.{n if n else "?"} {FACTS["day_emoji"][d3]} {d3} {what or "…"}'


BRANCH_LINES = (
    'writes this branch writes its own rows, each one through `entry --chat {mmdd}` first; '
    'the my day chat gets one line when it closes, never the rows',
    'closes when its objective is met, or at the day\'s dusk close if it is still open: '
    'QA, the session entry, the rename',
)


def clock(local, now=None):
    """(now UTC, now local, offset hours, problems)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    off = offset_hours(local, now)   # from time_zone; the fixed number only when no zone can be read
    out = []
    if bedo_clock.problem(local):
        out.append('clock: ' + bedo_clock.problem(local))
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


def quest_line(local):
    """His quest page, built at the dusk wrap-up and linked on the my day page (her word, 8 Nov 2026): she
    goes over it with him in the morning, once he's rested. `quest_url` in her settings; no line without it."""
    url = local.get('quest_url')
    return (f"quest  his quest page · {url} — linked on yesterday's my day page; go over it with him "
            "once he's rested (the page names its day)") if url else None


LOG_FIELDS = ('datetime', 'details', 'deliverable', 'practice', 'title')
LOG_HEAD = re.compile(r'^\[be\u2022do\] look behind (\d{4}-\d{2}-\d{2})(?:\s*\u00b7\s*(draft|final))?\s*$', re.M)


def built_pages(rows):
    """{day: (draft | final, link)} from the look behind's log rows — the newest
    row for a day wins, as in look_behind_log."""
    out = {}
    for r in sorted(rows, key=lambda r: (r.get('created') or '', r.get('datetime') or '')):
        m = LOG_HEAD.search(r.get('details') or '')
        if m:
            out[m.group(1)] = (m.group(2) or 'draft', (r.get('deliverable') or '').strip() or None)
    return out


GATE_TODO = {
    'day ahead': "finish yesterday's day ahead — its my day page rebuilt to the whole day as lived (her keeper "
                 "photos, the stream through bedtime), republished, then `run_day_ahead.sh final {y}` and its "
                 "line on the 👁️ look ahead row",
    'dayqa': "run its QA — `run_checks.sh dayqa {y}` against the finished day, its last line in the dusk close row",
}
GATE_MISSING = {'day ahead': "its day ahead isn't final", 'dayqa': "its dayqa isn't in the dusk close row"}


def day_page_link(rows, y):
    """The my day page's link, from the row carrying its final day ahead line."""
    for r in sorted(rows, key=lambda r: (r.get('created') or '', r.get('datetime') or ''), reverse=True):
        for m in bedo_daygate.HEAD.finditer(r.get('details') or ''):
            if m.group(1) == y.isoformat() and m.group(2) == 'final' and (r.get('deliverable') or '').strip():
                return r['deliverable'].strip()
    return None


def yesterday_line(day, url=None, built=None, log_rows=None):
    """What the morning chat shows first: yesterday's my day page, and the title
    yesterday's chat takes once she has seen it. The day behind is retired (her
    word, 8 Nov 2026): a day is done when its my day page is final and its dayqa
    recorded. `log_rows` are the look ahead and dusk close rows; None when they
    could not be read, and then nothing may be said about the day (it was said
    wrongly twice on 8 Nov). `url` and `built` are no longer used."""
    y = day - dt.timedelta(days=1)
    seen = chat_name(y, status=FACTS['chat_status']['window_closed'])
    if log_rows is None:
        return (f'first  yesterday\'s my day page — not checked: its rows were not read, so say nothing about '
                f'whether {y:%a %d %b} is finished until they are')
    left = [what for ok, what, _ in bedo_daygate.findings(log_rows, y) if not ok]
    if left:
        return (f'first  yesterday\'s my day page isn\'t finished: {y:%a %d %b} '
                f'({" and ".join(GATE_MISSING[w] for w in left)}).\n'
                f'       Offer to {", then ".join(GATE_TODO[w].format(y=y.isoformat()) for w in left)}. '
                f'{seen} waits until she has seen it')
    link = day_page_link(log_rows, y)
    return (f'first  yesterday\'s my day page is final and QA\'d · {link or "no link on its look ahead row"}\n'
            f'       once she has seen it, yesterday\'s chat becomes {seen}')


def read_log_rows(air, names, day, local):
    """The look behind's log rows from the bases in play, dated from four days
    before `day` — and the rows the day ahead first gate reads: a final day
    ahead line (the 👁️ look ahead row) and a dayqa line (the dusk close row).
    A handful of rows, details, deliverable, practice and title only."""
    sf = local['stream_fields']
    f, d = sf['datetime'], sf['details']
    since = (day - dt.timedelta(days=4)).isoformat()
    finds = ', '.join(f"FIND('{t}', {{{d}}})" for t in ('[be\u2022do] look behind ', bedo_daygate.G['head'] + ' ',
                                                       bedo_daygate.QA_MARK + ' '))
    formula = (f"AND(OR({finds}), "
               f"NOT(IS_BEFORE({{{f}}}, DATETIME_PARSE('{since}'))))")
    fields = {k: sf[k] for k in LOG_FIELDS if sf.get(k)}
    rows = []
    for name in bases_in_play(day, local):
        if name in names:
            src = air.dump(names[name], local['stream_table'], by_id=True, formula=formula)
            rows += as_rows(src['records'], fields)
    return rows


def due(now_local):
    """What the skills schedule says is due at this hour, as one line, or None."""
    S, F = FACTS['skills_schedule'], FACTS['flows']
    t = now_local.time()
    out = []
    if t < dt.time(*map(int, F['backup_close']['dawn'].split(':'))):
        out += S['dawn']
    if t >= dt.time(*map(int, F['dusk_opens_after'].split(':'))):
        out += S['dusk']
    if now_local.weekday() == 6:
        out += S['sunday']
    if now_local.day <= S['monthly_by_day']:
        out += S['monthly']
    return 'due    ' + ' · '.join(out) if out else None


def report(local, names, rows, now=None, kind='day', part=None, week=None, handoff=None, amendments=None,
           built=None, log_rows=None, n=None, what=None):
    now, now_local, off, probs = clock(local, now)
    day = now_local.date()
    want, bprobs, stop = check_base(names, rows, now, day, local, handoff)
    lines = [branch_name(day, n, what) if kind == 'branch' else chat_name(day, kind, part, week=week),
             f'clock  {now:%Y-%m-%dT%H:%M}Z · {now_local:%a %d %b %H:%M} local (UTC{off:+g})',
             f'base   {want[0]}' + (f' · and {want[1]} for yesterday' if len(want) > 1 else '')]
    t = newest(rows, now)
    if t:
        lines.append(f'newest {(now - t).total_seconds() / 3600:.1f} h ago')
    if kind == 'day':
        lines.append(yesterday_line(day, look_behind_url(local), built, log_rows))
        if quest_line(local):
            lines.append(quest_line(local))
    if kind == 'branch':
        # a branch does one job: no morning line, no list of what the day owes, no rules on paper
        if not n:
            lines.append("number count today's sessions tagged bedo:%s, this one included, and run again with --n"
                         % day.strftime('%m%d'))
        lines += [b.format(mmdd=day.strftime('%m%d')) for b in BRANCH_LINES]
    d = due(now_local) if kind != 'branch' else None
    if d:
        lines.append(d)
    lines += ['⚠ ' + p for p in probs + bprobs]
    if amendments is not None and kind != 'branch':
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
    ap.add_argument('--kind', choices=['day', 'week', 'branch'], default='day')
    ap.add_argument('--n', type=int, help="a branch's number: the order it opened today, from the day's session list")
    ap.add_argument('--what', help="a branch's glyph and what it does, for its title")
    ap.add_argument('--part', help="the chat's letter when the day has more than one: a, b, c…")
    ap.add_argument('--week', type=int, help='the week under review, for a my week chat')
    ap.add_argument('--handoff', help='the week\'s handoff file')
    ap.add_argument('--amendments', help='a read of the amendments table')
    ap.add_argument('--look-behind', help="a read of the look behind's log rows, with the look ahead and dusk close "
                                          "rows of the last days (details, deliverable, practice): read_log_rows' formula")
    a = ap.parse_args(argv)
    L = load_local()
    fields = {'datetime': L.get('stream_fields', {}).get('datetime', 'datetime')}
    now, now_local, _, _ = clock(L)
    if a.live:
        from bedo_air import Air, SLOW
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
        log_rows = read_log_rows(air, names, now_local.date(), L) if a.kind == 'day' else None
        built = built_pages(log_rows) if log_rows is not None else None
        amend = (L.get('bases') or {}).get('amendments') if a.kind != 'branch' else None   # a branch reads no rule list
        st = (L.get('amendments_fields') or {}).get('status', 'status')
        amendments = (bedo_rules.active(air.records(*amend, by_id=bool(L.get('amendments_fields')), ttl=SLOW,
                                                    formula=f"{{{st}}}='active'"), L)   # the active ones: one page, not four
                      if amend else None)
    else:
        if not (a.bases and a.stream):
            sys.exit('give --live, or both --bases and --stream')
        names = json.load(open(a.bases, encoding='utf-8'))
        rows = stream_rows(a.stream, fields)
        amendments = bedo_rules.active(complete(a.amendments, 'amendments'), L) if a.amendments else None
        sf = L.get('stream_fields') or {}
        log_rows = (as_rows(complete(a.look_behind, 'look behind log rows'), {k: sf.get(k, k) for k in LOG_FIELDS})
                    if a.look_behind else None)
        built = built_pages(log_rows) if log_rows is not None else None
    handoff = open(a.handoff, encoding='utf-8').read() if a.handoff else None
    text, stop = report(L, names, rows, now, a.kind, a.part, a.week, handoff, amendments, built, log_rows,
                        n=a.n, what=a.what)
    print(text)
    sys.exit(1 if stop else 0)


if __name__ == '__main__':
    main()
