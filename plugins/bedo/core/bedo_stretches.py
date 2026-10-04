# -*- coding: utf-8 -*-
"""A chat's time is the sum of its stretches, never its envelope (A250, A251).

A stretch is a run of message and write timestamps with no gap over
`minutes.stretch_gap` (15) between neighbours. The 3 Oct evening was counted as
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
import datetime as dt, json, os

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


def times_from(src):
    """Message timestamps from what a chat can hand over: a plain list of
    stamps; a claude.ai conversation read (chat_messages[].created_at); or a
    Claude Code transcript, one JSON object a line, user and assistant turns."""
    if isinstance(src, (str, os.PathLike)):
        with open(src, encoding='utf-8') as fh:
            text = fh.read()
        try:
            d = json.loads(text)
        except json.JSONDecodeError:              # one object a line; a live
            d = []                                # transcript can end mid-line
            for l in text.splitlines():
                try:
                    d.append(json.loads(l))
                except json.JSONDecodeError:
                    pass
    else:
        d = src
    if isinstance(d, dict) and 'chat_messages' in d:
        return [m['created_at'] for m in d['chat_messages'] if m.get('created_at')]
    if isinstance(d, list) and d and isinstance(d[0], dict):
        return [e['timestamp'] for e in d if e.get('type') in ('user', 'assistant') and e.get('timestamp')]
    return list(d)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='a chat\'s time as the sum of its stretches')
    ap.add_argument('src')
    ap.add_argument('--offset', type=float, default=None, help='local UTC offset in hours')
    ap.add_argument('--gap', type=int, default=GAP)
    a = ap.parse_args(argv)
    off = a.offset
    if off is None:
        from bedo_reader import load_local
        off = load_local(required=False).get('utc_offset_hours', 0)
    spans = stretches(times_from(a.src), a.gap)
    print(f'{len(spans)} stretch{"es" if len(spans) != 1 else ""}: {named(spans, off)}')


if __name__ == '__main__':
    main()
