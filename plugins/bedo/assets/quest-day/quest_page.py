# -*- coding: utf-8 -*-
"""The child's quest page for one day, from that day's ⚔️ quest row (2 Nov 2026).

Built only on her word, while she looks back on the day before (her cue: let's build the quest HTML),
never unasked. The row's block holds the realms and the ten mini-quests the way the quest check writes
them:

    🔆 SUPER VITALITY
    · ✓ The Adventure — the lake trail, the dog pulling him on his little bike
    · ✗ The Fuel — …

This reads them, turns each line to him (he → you), counts the points, and fills quest_day.html. The
photos are hers to pick: one trophy for the big win, at most one beside a quest it proves.

    python3 quest_page.py --row quest_row.json --name NAME --day "Sunday · 1 November" \\
        [--trophy photo.jpg --trophy-text "Today's big one: …"] [--photo "The Fuel=snack.jpg"] \\
        [--per-point 0.5] [--foot "…"] --out quest.html

Nothing personal lives here: the name, the lines and the photos come in at build time.
"""
import argparse, base64, io, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
QUEST = re.compile(r'^\s*[·•\-]\s*([✓✔✗✘×])\s*(.+?)(?:\s+[—–-]\s+(.*))?\s*$')
SWAP = [(r"\bhe's\b", "you're"), (r"\bhe is\b", 'you are'), (r"\bhe was\b", 'you were'), (r'\bhimself\b', 'yourself'),
        (r'\bhe\b', 'you'), (r'\bhis\b', 'your'), (r'\bhim\b', 'you'), (r"\bhasn't\b", "haven't"), (r'\bhas\b', 'have'),
        (r"\bdidn't\b", "didn't"), (r"\bdoesn't\b", "don't")]


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
            cur['quests'].append(dict(name=m.group(2).strip(), won=m.group(1) in '✓✔', line=to_him(m.group(3) or '')))
        elif not m and re.match(r'^\W*\s*[A-Z][A-Z \'’&/·-]{3,}$', line):
            words = line.split(maxsplit=1)
            glyph = words[0] if not words[0][:1].isalpha() else ''
            name = (words[1] if glyph and len(words) > 1 else line).title().replace("'S", "'s")
            cur = dict(name=(glyph + ' ' + name).strip(), quests=[])
            out.append(cur)
    return [r for r in out if r['quests']]


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
    ap.add_argument('--row', required=True, help="the day's ⚔️ quest row (logical names, or a stream record)")
    ap.add_argument('--name', required=True)
    ap.add_argument('--day', required=True, help='e.g. "Sunday · 1 November"')
    ap.add_argument('--per-point', type=float, default=0.5)
    ap.add_argument('--trophy'), ap.add_argument('--trophy-text', default='')
    ap.add_argument('--photo', action='append', default=[], help='"Quest name=path": a photo beside the quest it proves')
    ap.add_argument('--foot')
    ap.add_argument('--out', required=True)
    a = ap.parse_args(argv)
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
