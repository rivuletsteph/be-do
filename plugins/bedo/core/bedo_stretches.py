# -*- coding: utf-8 -*-
"""A chat's time is the sum of its stretches, never its envelope (A250, A251).

A stretch is a run of her own message timestamps with no gap over
`minutes.stretch_gap` (15) between neighbours; Claude's turns are not her time. The 3 Oct evening was counted as
one 5h 30m block and was really five stretches, 4h 04m; this file is what
stops that happening by hand.

  · 📲 capture rows carry the minutes; every stretch should have one
  · a window chat's ⚡ action row carries no time spent, no end and no drive —
    the minutes are already on its captures, and pooling both drew 8h 13m of
    doing for a day with 4h 04m of it
  · a drive chat's ⚡ row keeps its span; its time spent should equal the sum

    python3 bedo_stretches.py times.json            # a list of ISO stamps
    python3 bedo_stretches.py conversation.json     # a claude.ai chat read
    python3 bedo_stretches.py session.jsonl         # a Claude Code transcript
"""
import datetime as dt, json, os, re

from bedo_reader import FACTS

GAP = FACTS['minutes']['stretch_gap']


def utc(s):
    if isinstance(s, dt.datetime):
        return s if s.tzinfo else s.replace(tzinfo=dt.timezone.utc)
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))


def stretches(times, gap=GAP):
    """[(start, end)] in time order. A gap OVER `gap` minutes splits; a gap of
    exactly `gap` does not. A lone message is a stretch of no length — it is
    shown, never padded, since padding is an invented number."""
    ts = sorted(utc(t) for t in times if t)
    out = []
    for t in ts:
        if out and (t - out[-1][1]) <= dt.timedelta(minutes=gap):
            out[-1][1] = t
        else:
            out.append([t, t])
    return [tuple(s) for s in out]


def minutes(spans):
    return round(sum((b - a).total_seconds() for a, b in spans) / 60)


def hm(m):
    return f'{m // 60}h {m % 60:02d}m' if m >= 60 else f'{m}m'


def _clock(t):
    return f'{t.hour % 12 or 12}:{t:%M}'


def named(spans, offset_hours):
    """The stretches as the [be•do] block names them, so the number can be
    checked rather than trusted: 5:31–5:41 · 7:39–8:52 = 1h 23m."""
    off = dt.timedelta(hours=offset_hours)
    parts = [f'{_clock(a + off)}–{_clock(b + off)}' for a, b in spans]
    return ' · '.join(parts) + f' = {hm(minutes(spans))}'


LINE = 'stretches:'
_NAMED = re.compile(r'^\s*(?:\[be•do\]\s*)?stretches:\s*(?P<spans>.+?)\s*=\s*[^=]*$', re.M)
_SPAN = re.compile(r'(\d{1,2}):(\d{2})\s*[–-]\s*(\d{1,2}):(\d{2})')


def block_line(spans, offset_hours):
    """The line a session row's `[be•do]` block carries, so the day behind can
    draw her stretches rather than the envelope: `stretches: 3:19–3:21 · … = 18m`."""
    return f'{LINE} {named(spans, offset_hours)}'


def on_day(spans, day, offset_hours):
    """The stretches that start on her local `day` — a chat that runs across
    days logs each day's work on that day's row."""
    off = dt.timedelta(hours=offset_hours)
    return [(a, b) for a, b in spans if (a + off).date() == day]


def row_times(spans):
    """A session row's clock, from her stretches: one stretch keeps a real
    start and end; several keep the first start and the sum as time spent (in
    seconds), with no end — the envelope is never the row's span."""
    if not spans:
        return {}
    iso = lambda t: t.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    if len(spans) == 1:
        return {'datetime': iso(spans[0][0]), 'end': iso(spans[0][1])}
    return {'datetime': iso(spans[0][0]), 'time_spent': minutes(spans) * 60}


def from_details(details, anchor):
    """[(start, end)] as local naive datetimes, read back from a row's
    `stretches:` line; None when it names none. The clock is 12-hour, so each
    time is read as the one nearest the row's own start (`anchor`, local) and
    then forward in order."""
    m = _NAMED.search(details or '')
    if not m or anchor is None:
        return None
    out, prev = [], None
    for h1, m1, h2, m2 in _SPAN.findall(m['spans']):
        pair = []
        for h, mi in ((h1, m1), (h2, m2)):
            base = anchor.replace(hour=0, minute=0, second=0, microsecond=0)
            cands = [base + dt.timedelta(days=d, hours=int(h) % 12 + half, minutes=int(mi))
                     for d in (0, 1) for half in (0, 12)]
            if prev is None:
                t = min(cands, key=lambda c: abs(c - anchor))
            else:
                later = [c for c in cands if c >= prev]
                t = min(later) if later else prev
            pair.append(t)
            prev = t
        out.append(tuple(pair))
    return out or None


def uncaptured(spans, captures):
    """Stretches no 📲 capture row overlaps. `captures` are (start, end) pairs;
    a capture with no end is a moment and covers the stretch it falls in."""
    caps = [(utc(a), utc(b) if b else utc(a)) for a, b in captures]
    return [(a, b) for a, b in spans if not any(ca <= b and cb >= a for ca, cb in caps)]


def is_window(title, facts=FACTS):
    """my day · my week · my month · my season · my year — the chats whose own
    ⚡ row carries no duration and no drive."""
    t = (title or '').lower()
    return any(w in t for w in facts['window_chats'])


def action_row_problems(row, title, capture_minutes=None):
    """A251 for a window chat's ⚡ row; the sum check for a drive chat's."""
    out = []
    if is_window(title):
        if row.get('time_spent') or row.get('end'):
            out.append('a window chat\'s ⚡ row carries no duration — its 📲 captures hold the minutes')
        if row.get('rhythm'):
            out.append('a window chat\'s ⚡ row carries no drive — be•do time is tending, not drive work')
    elif capture_minutes is not None and row.get('time_spent') not in (None, ''):
        spent = round(float(row['time_spent']) / 60)        # a duration field is seconds
        if abs(spent - capture_minutes) > 1:
            out.append(f'time spent {hm(spent)} is not the sum of its captures, {hm(capture_minutes)} — one of them is an envelope')
    return out


def _hers(turn):
    """A turn she typed, spoke or shared. Claude's turns, tool results, skill
    text, subagents and compaction summaries are not her time: a session
    building on its own takes a turn every few seconds, and counting them drew
    an afternoon out on 24 Oct as 1h 42m on the phone when her messages were
    3:20, 3:53 and 4:47–5:00 (her amendment, 25 Oct 2026: device time is only
    as long as the data shows)."""
    if any(turn.get(k) for k in ('isMeta', 'isSynthetic', 'isSidechain', 'isCompactSummary')):
        return False
    origin = turn.get('origin')
    if isinstance(origin, dict) and origin.get('kind') not in (None, 'human'):
        return False
    content = (turn.get('message') or {}).get('content')
    if isinstance(content, list) and any(isinstance(c, dict) and c.get('type') == 'tool_result' for c in content):
        return False
    return True


def _parse(text):
    """One JSON document; a list_events read saved as the tool gave it (inside
    its wrapper text, or as [{"type": "text", "text": …}]); or one object a
    line, where a live transcript can end mid-line."""
    try:
        d = json.loads(text)
    except json.JSONDecodeError:
        d = None
    if isinstance(d, list) and d and isinstance(d[0], dict) and d[0].get('type') == 'text':
        text, d = ''.join(x.get('text', '') for x in d), None
    if d is None and '{"ccr"' in text:
        d, _ = json.JSONDecoder().raw_decode(text[text.index('{"ccr"'):])
    if d is None:
        d = []
        for l in text.splitlines():
            try:
                d.append(json.loads(l))
            except json.JSONDecodeError:
                pass
    return d


def times_from(src):
    """Her message timestamps from what a chat can hand over: a plain list of
    stamps; a claude.ai conversation read (chat_messages[].created_at, her
    side only); a Claude Code transcript, one JSON object a line; or a cloud
    session's event read (list_events, saved as it came). Only her turns count
    (`_hers`) — the time a session ran is not the time she was on a device."""
    if isinstance(src, (str, os.PathLike)):
        with open(src, encoding='utf-8') as fh:
            d = _parse(fh.read())
    else:
        d = src
    if isinstance(d, dict) and 'chat_messages' in d:
        return [m['created_at'] for m in d['chat_messages']
                if m.get('created_at') and m.get('sender', 'human') == 'human']
    if isinstance(d, dict) and 'data' in d.get('ccr', d):     # list_events: {"ccr": {"data": [...]}}
        out = []
        for e in d.get('ccr', d)['data']:
            u = e.get('user')
            if isinstance(u, dict) and e.get('created_at') and _hers(u.get('internal_anthropic_catchall', u)):
                out.append(e['created_at'])
        return out
    if isinstance(d, list) and d and isinstance(d[0], dict):
        return [e['timestamp'] for e in d if e.get('type') == 'user' and e.get('timestamp') and _hers(e)]
    return list(d)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='a chat\'s time as the sum of its stretches')
    ap.add_argument('src')
    ap.add_argument('--offset', type=float, default=None, help='local UTC offset in hours')
    ap.add_argument('--gap', type=int, default=GAP)
    ap.add_argument('--day', help='only the stretches that start on this local day, YYYY-MM-DD')
    ap.add_argument('--json', action='store_true', help='the row\'s times and its stretches line, as JSON')
    a = ap.parse_args(argv)
    off = a.offset
    if off is None:
        from bedo_reader import load_local
        off = load_local(required=False).get('utc_offset_hours', 0)
    spans = stretches(times_from(a.src), a.gap)
    if a.day:
        spans = on_day(spans, dt.date.fromisoformat(a.day), off)
    if a.json:
        print(json.dumps(dict(row_times(spans), line=block_line(spans, off), minutes=minutes(spans)),
                         ensure_ascii=False))
        return
    print(f'{len(spans)} stretch{"es" if len(spans) != 1 else ""}: {named(spans, off)}')
    print(f'for the row\'s [be•do] block: {block_line(spans, off)}')


if __name__ == '__main__':
    main()
