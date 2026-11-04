# -*- coding: utf-8 -*-
"""The quest page from a quest row (2 Nov 2026): realms and quests read, turned to him, points counted.
The row is invented.

    python3 plugins/bedo/assets/quest-day/tests/test_quest_page.py
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import quest_page as Q  # noqa: E402

ROW = dict(details='''He was a really good sport with the dog.

🛌 POWER REST
· ✗ The 10-Hour Charge — in bed late after the party
· ✗ The Solo Fortress — the family bed
🔆 SUPER VITALITY
· ✓ The Adventure — the lake trail, the dog pulling him on his little bike
· ✓ The Fuel — the Big Four
🪄 MASTER CREATOR
· ✓ Physical Creation — he made hot chocolate, his own idea
· ✗ Digital Creation — he hasn't built anything yet

You earned 3 out of 6 today.
———
[be•do] Scored at her word.''')
html, d = Q.build(ROW, 'Kid', 'Sunday · 1 November')
assert [r['name'] for r in d['realms']] == ['🛌 Power Rest', '🔆 Super Vitality', '🪄 Master Creator'], d['realms']
won = sum(q['won'] for r in d['realms'] for q in r['quests'])
assert won == 3, won
mc = d['realms'][2]['quests']
assert mc[0]['line'] == 'you made hot chocolate, your own idea' and mc[1]['line'] == "you haven't built anything yet", mc
assert d['realms'][1]['quests'][0]['line'].endswith('pulling you on your little bike'), d['realms'][1]
assert "<title>Kid's Quest · Sunday</title>" in html and '/*DATA*/' not in html
assert json.loads(html.split('type="application/json">', 1)[1].split('</script>', 1)[0])['name'] == 'Kid'
print('ok — the quest row becomes his page: realms in order, wins counted, every line said to him')

# her notes come out, and a missed quest with nothing said is a next-time line (4 Nov 2026)
_, d = Q.build(dict(details='''🪄 MASTER CREATOR
· ✗ Physical Creation — not said
· ✓ Digital Creation — close, her word: he coded a game'''), 'Kid', 'Tuesday · 3 November')
q = {x['name']: x['line'] for x in d['realms'][0]['quests']}
assert q['Physical Creation'].startswith('next time'), q
assert 'her word' not in q['Digital Creation'] and q['Digital Creation'].endswith('you coded a game'), q

# the morning routine's way: the day's ⚔️ row found in the stream, the week line counted (4 Nov 2026)
import datetime as dt, tempfile
LOCAL = dict(time_zone='America/Chicago', fields=dict(stream=dict(practice='p', when='w', details='d')),
             quest_practice="⚔️ kid's quest")
def rec(when, text, prac="⚔️ kid's quest"):
    return dict(id='r', cellValuesByFieldId=dict(p=prac, w=when, d=text))
dump = dict(records=[rec('2026-11-02T02:19:00.000Z', ROW['details']),         # Sun 1 Nov, evening: 3 points
                     rec('2026-11-04T03:45:00.000Z', ROW['details']),         # Tue 3 Nov, evening: 3 points
                     rec('2026-11-04T04:00:00.000Z', 'not a quest', '🌌 evening blessing'),
                     rec('2026-10-31T03:00:00.000Z', ROW['details'])])        # last week: not counted
f = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False); json.dump(dump, f); f.close()
rows = Q.stream_rows([f.name], LOCAL)
assert [r[0] for r in rows] == [dt.date(2026, 10, 30), dt.date(2026, 11, 1), dt.date(2026, 11, 3)], rows
assert Q.week_line(rows, dt.date(2026, 11, 3), 0.5) == \
    "Day 2 of this week's quest: 6 points so far, $3.00. Payday is Sunday.", Q.week_line(rows, dt.date(2026, 11, 3), 0.5)
lf = tempfile.NamedTemporaryFile('w', suffix='.json', delete=False); json.dump(LOCAL, lf); lf.close()
out = tempfile.mktemp(suffix='.html')
Q.main(['--from-stream', f.name, '--date', '2026-11-03', '--local', lf.name, '--name', 'Kid', '--out', out])
assert "<title>Kid's Quest · Tuesday</title>" in open(out, encoding='utf-8').read()
try:
    Q.main(['--from-stream', f.name, '--date', '2026-11-02', '--local', lf.name, '--name', 'Kid', '--out', out])
    raise AssertionError('a day with no quest row built a page')
except SystemExit as e:
    assert e.code == 4, e.code
print('ok — the morning way: the day found in the stream, the week counted, her notes kept off his page')
