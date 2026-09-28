# -*- coding: utf-8 -*-
"""The one thing a chat reads before a look behind: the day's logged rows, one
short line each, so the lead and the story can be written from the user's own
words without reading the stream.

    python3 day_digest.py --day YYYY-MM-DD --local look_behind_local.json \
        --stream w39.json [--stream w38.json] [--width 160]

Live base first (I15): the first --stream wins a record id seen twice. Plans
(▫️ ⬜ ✖️) are left out; they are not moments. The user's words are the text
above the details divider; the [be•do] block below it is dropped.
"""
import argparse, datetime as dt, json, re

DIVIDERS = ('———', '---')
PLANS = ('▫️potential', '⬜ intention', '✖️ dropped')


def her_words(t):
    t = t or ''
    for d in DIVIDERS:
        i = t.find('\n' + d)
        if i >= 0:
            t = t[:i]
    return re.sub(r'\s+', ' ', t).strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--stream', action='append', required=True)
    ap.add_argument('--width', type=int, default=160)
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    F = L['fields']['stream']
    off = dt.timedelta(hours=L['utc_offset_hours'])
    day = dt.date.fromisoformat(a.day)

    def local(ts):
        return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).replace(tzinfo=None) if ts else None

    seen = {}
    for p in a.stream:
        for r in json.load(open(p, encoding='utf-8'))['records']:
            seen.setdefault(r['id'], r)
    # latest row per key (I5)
    latest = {}
    for r in sorted(seen.values(), key=lambda r: r['createdTime']):
        c = r['cellValuesByFieldId']
        latest[c.get(F['key']) or r['id']] = c
    rows = []
    for c in latest.values():
        t = local(c.get(F['when']))
        if not t or t.date() != day:
            continue
        st = c.get(F['status']) or ''
        st = st.get('name', '') if isinstance(st, dict) else st
        if st in PLANS:
            continue
        e = local(c.get(F['end']))
        span = t.strftime('%H:%M') + (e.strftime('–%H:%M') if e else '')
        words = her_words(c.get(F['details']))
        who = c.get(F['person']) or ''
        line = f"{span:11} {st.split(' ')[0]} {c.get(F['practice']) or ''} · {c.get(F['title']) or ''}"
        if who:
            line += f" [{who}]"
        if F.get('mentioned') and c.get(F['mentioned']):
            line += f" (mentioned: {c.get(F['mentioned'])})"
        if words and words != c.get(F['title']):
            line += ' — ' + words
        rows.append((t, line[:a.width]))
    for _, line in sorted(rows):
        print(line)
    print(f'({len(rows)} rows)')


if __name__ == '__main__':
    main()
