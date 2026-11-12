# -*- coding: utf-8 -*-
"""The child's quest page for one day, from that day's ⚔️ quest row (2 Nov 2026).

Built every morning with the look behind (her word, 4 Nov 2026: build it every morning, and go over it
with him when he's rested — what went great yesterday, where he missed out, so he can correct it). The
look behind build runs it with --from-stream (SKILL.md step 5b); she can still ask for one by hand. The row's block holds the realms and the ten mini-quests the way the quest check writes
them:

    🔆 SUPER VITALITY
    · ✓ The Adventure — the lake trail, the dog pulling him on his little bike
    · ✗ The Fuel — …

This reads them, turns each line to him (he → you), counts the points, and fills quest_day.html. The
photos are hers to pick: one trophy for the big win, at most one beside a quest it proves.

    python3 quest_page.py --row quest_row.json --name NAME --day "Sunday · 1 November" \\
        [--trophy photo.jpg --trophy-text "Today's big one: …"] [--photo "The Fuel=snack.jpg"] \\
        [--per-point 0.5] [--foot "…"] --out quest.html
    python3 quest_page.py --from-stream data/w45.json [--from-stream data/w44.json] --date 2026-11-03 \\
        --local look_behind_local.json --name NAME --out quest.html     # the morning routine's way

Nothing personal lives here: the name, the lines and the photos come in at build time.
"""
import argparse, base64, io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
QUEST = re.compile(r'^\s*[·•\-]\s*([✓✔✗✘×])\s*(.+?)(?:\s+[—–-]\s+(.*))?\s*$')
SWAP = [(r"\bhe's\b", "you're"), (r"\bhe is\b", 'you are'), (r"\bhe was\b", 'you were'), (r'\bhimself\b', 'yourself'),
        (r'\bhe\b', 'you'), (r'\bhis\b', 'your'), (r'\bhim\b', 'you'), (r"\bhasn't\b", "haven't"), (r'\bhas\b', 'have'),
        (r"\bdidn't\b", "didn't"), (r"\bdoesn't\b", "don't")]


# What a scorer writes for her that a child shouldn't read: her notes on where a call came from.
HERS = [re.compile(r'\s*\(?\b(?:her|at her) words?\b\)?:?', re.I)]
SILENT = re.compile(r'^(?:not said|not seen|unobserved|unreported|no word|nothing said)\.?$', re.I)
# A missed quest with nothing to say is a next-time line, never a blank (README: never a mark against him).
NEXT = {'the 10-hour charge': 'next time, lights out a little earlier for the full ten hours',
        'the solo fortress': 'your own fortress is there whenever you want it',
        'the adventure': 'next time, go somewhere new',
        'the fuel': 'next time, eat the Big Four',
        'the training': 'next time, do your lessons',
        'the journey': 'next time, finish both lessons',
        'physical creation': 'next time, build or make something with your hands',
        'digital creation': 'next time, make something of your own on a screen',
        'the party / good sport': 'next time, be a good sport with friends',
        "the hero's service": 'next time, ask how you can help, and do it'}


def tidy(name, line, won):
    """Her notes out, and a missed quest with nothing said becomes its next-time line."""
    for h in HERS:
        line = h.sub('', line)
    line = re.sub(r'\s{2,}', ' ', line).strip(' ,;:')
    if not won and (not line or SILENT.match(line)):
        return NEXT.get(name.lower(), 'next time')
    return line


def to_him(line):
    """Third person to second, the light way: 'he made hot chocolate, his own idea' → 'you made …, your own idea'."""
    out = line
    for a, b in SWAP:
        out = re.sub(a, lambda m: b.capitalize() if m.group(0)[0].isupper() else b, out, flags=re.I)
    return out


def realms(text):
    """[{name, quests: [{name, won, line}]}] from the row's block, in its order."""
    out, cur = [], None
    for raw in (text or '').splitlines():
        line = raw.strip()
        if not line or line.startswith('[be•do]') or line == '———':
            continue
        m = QUEST.match(line)
        if m and cur is not None:
            name, won = m.group(2).strip(), m.group(1) in '✓✔'
            cur['quests'].append(dict(name=name, won=won, line=to_him(tidy(name, m.group(3) or '', won))))
        elif not m and re.match(r'^\W*\s*[A-Z][A-Z \'’&/·-]{3,}$', line):
            words = line.split(maxsplit=1)
            glyph = words[0] if not words[0][:1].isalpha() else ''
            name = (words[1] if glyph and len(words) > 1 else line).title().replace("'S", "'s")
            cur = dict(name=(glyph + ' ' + name).strip(), quests=[])
            out.append(cur)
    return [r for r in out if r['quests']]


def stream_rows(paths, local):
    """[(local date, details)] of every ⚔️ quest row in the stream dumps (bedo_fetch's shape, or the API's)."""
    import datetime as dt
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(local['time_zone'])   # each row's own offset; the number only when no zone can be read
    except Exception:
        tz = dt.timezone(dt.timedelta(hours=local.get('utc_offset_hours') or 0))
    F = local['fields']['stream']
    want = local.get('quest_practice') or '⚔️'
    out = []
    for p in paths:
        for r in json.load(open(p, encoding='utf-8')).get('records', []):
            c = r.get('cellValuesByFieldId') or r.get('fields') or {}
            prac = c.get(F['practice']) or ''
            prac = prac.get('name', '') if isinstance(prac, dict) else str(prac)
            when = c.get(F['when'])
            if want not in prac or not when:
                continue
            t = dt.datetime.fromisoformat(when.replace('Z', '+00:00')).astimezone(tz)
            out.append((t.date(), t, c.get(F['details']) or ''))
    return sorted(out, key=lambda x: x[1])


def week_line(rows, day, per_point):
    """The page's foot from the week's scored rows up to that day (Sunday to Saturday)."""
    import datetime as dt
    start = day - dt.timedelta(days=(day.weekday() + 1) % 7)
    pts, days = 0, set()
    for d, _, text in rows:
        if start <= d <= day:
            rs = realms(text)
            if rs:
                days.add(d)
                pts += sum(q['won'] for r in rs for q in r['quests'])
    n = len(days)
    return (f"Day {n} of this week's quest: {pts} points so far, ${pts * per_point:.2f}. Payday is Sunday."
            if n else '')


def data_uri(path, side=640):
    raw = open(path, 'rb').read()
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(raw)).convert('RGB')
        im.thumbnail((side, side))
        buf = io.BytesIO()
        im.save(buf, 'JPEG', quality=82)
        raw = buf.getvalue()
    except Exception:
        pass
    return 'data:image/jpeg;base64,' + base64.b64encode(raw).decode()


def build(row, name, day, per_point=0.5, trophy=None, photos=None, foot=None):
    rs = realms(row.get('details') or '')
    if not rs:
        raise SystemExit('no realms in the quest row: it needs the scored lines (· ✓ Quest — what he did)')
    for r in rs:                                  # the wins first in each realm: it reads better for him
        r['quests'].sort(key=lambda q: not q['won'])
        for q in r['quests']:
            if photos and q['name'] in photos:
                q['img'], q['alt'] = data_uri(photos[q['name']]), q['name']
    d = dict(name=name, day=day, per_point=per_point, realms=rs, foot=foot or '')
    if trophy:
        d['trophy'] = dict(img=data_uri(trophy[0]) if trophy[0] else '', alt=trophy[1], text=trophy[1])
    tpl = open(os.path.join(HERE, 'quest_day.html'), encoding='utf-8').read()
    return tpl.replace('/*TITLE*/', f"{name}'s Quest · {day.split('·')[0].strip()}").replace(
        '/*DATA*/', json.dumps(d, ensure_ascii=False).replace('</', '<\\/')), d


def main(argv=None):
    ap = argparse.ArgumentParser(description="the child's quest page for one day, on her word")
    ap.add_argument('--row', help="the day's ⚔️ quest row (logical names, or a stream record)")
    ap.add_argument('--from-stream', action='append', default=[], help="stream dumps to find the day's ⚔️ row in")
    ap.add_argument('--date', help='YYYY-MM-DD, with --from-stream')
    ap.add_argument('--local', help='look_behind_local.json, with --from-stream')
    ap.add_argument('--name', required=True)
    ap.add_argument('--day', help='e.g. "Sunday · 1 November" (with --from-stream, made from --date)')
    ap.add_argument('--per-point', type=float, default=0.5)
    ap.add_argument('--trophy'), ap.add_argument('--trophy-text', default='')
    ap.add_argument('--photo', action='append', default=[], help='"Quest name=path": a photo beside the quest it proves')
    ap.add_argument('--foot')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
    if a.from_stream:
        import datetime as dt
        if not (a.date and a.local):
            raise SystemExit('--from-stream needs --date and --local')
        day = dt.date.fromisoformat(a.date)
        rows = stream_rows(a.from_stream, json.load(open(a.local, encoding='utf-8')))
        mine = [r for r in rows if r[0] == day]
        if not mine or not realms(mine[-1][2]):
            print(json.dumps(dict(out=None, date=a.date, why='no scored ⚔️ quest row that day: nothing built'),
                             ensure_ascii=False))
            raise SystemExit(4)
        row = dict(details=mine[-1][2])
        if a.row:                                 # the same block with lines reworded to him, for the rebuild
            row = json.load(open(a.row, encoding='utf-8'))
            row = row.get('fields', row) if isinstance(row, dict) else row
        a.day = a.day or f'{day:%A} · {day.day} {day:%B}'
        a.foot = a.foot or week_line(rows, day, a.per_point)
    else:
        if not (a.row and a.day):
            raise SystemExit('give --row and --day, or --from-stream with --date and --local')
        row = json.load(open(a.row, encoding='utf-8'))
        row = row.get('fields', row) if isinstance(row, dict) else row
    photos = dict(p.split('=', 1) for p in a.photo)
    if len(photos) > 1:
        raise SystemExit('at most one photo beside a quest (the trophy is the other)')
    html, d = build(row, a.name, a.day, a.per_point, (a.trophy, a.trophy_text) if a.trophy or a.trophy_text else None,
                    photos, a.foot)
    open(a.out, 'w', encoding='utf-8').write(html)
    won = sum(q['won'] for r in d['realms'] for q in r['quests'])
    print(json.dumps(dict(out=a.out, won=won, of=sum(len(r['quests']) for r in d['realms']),
                          money=f'${won * a.per_point:.2f}',
                          read_first='read every line before she sees it: the turn to him is mechanical'), ensure_ascii=False))


if __name__ == '__main__':
    main()
