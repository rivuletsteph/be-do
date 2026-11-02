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
