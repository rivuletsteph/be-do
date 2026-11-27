# -*- coding: utf-8 -*-
"""Not on today's calendar (19 Nov 2026).

Two things reached Thursday's list that belonged elsewhere: a row whose event
was already on the calendar, because the row's title carried its host, date and
hours and the event's did not; and rows moved to the next Wednesday, because the
list took each drive's pick whatever its date. The list now matches a row to a
calendar card by its words, and leaves off a step set for a later day.

The helpers run in node where it is installed; without it, only the wiring is
checked. Every title below is an obvious invention.

    python3 tests/test_today_list.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ENG = os.path.join(HERE, '..', 'assets', 'flow_engine.html')


def main():
    e = open(ENG, encoding='utf-8').read()
    body = e.split('function intention(blocks){', 1)[1].split('\nfunction ', 1)[0]
    # the list asks the helpers, and no longer an exact-title set
    assert '!laterThan(s.a,D.day)' in body and '!onCalendar(nt(s.a.t),cards)' in body, body[:400]
    assert 'new Set((window.__cards' not in body
    helpers = '\n'.join(l for l in e.splitlines() if re.match(r'function (calKey|onCalendar|laterThan)\(', l))
    assert helpers.count('function ') == 3, helpers

    node = shutil.which('node')
    if not node:
        print('ok — the list is wired to its helpers (node not installed: the helpers themselves not run)')
        return
    cards = [dict(t='⬜🫴 Garden Club Winter Social — Pat Example', summary='⬜🫴 Garden Club Winter Social — Pat Example'),
             dict(t='Gym'), dict(t='✅ Call the vet about the shots')]
    cases = dict(
        party=["onCalendar('Garden Club Winter Social — Pat Example, Thu 19 Nov 4–6', C)", True],
        glyphs=["onCalendar('Call the vet about the shots', C)", True],
        short=["onCalendar('Gym bag to the car', C)", False],      # a card under nine letters matches only itself
        same_short=["onCalendar('gym', C)", True],
        other=["onCalendar('Draft the grant summary', C)", False],
        empty=["onCalendar('', C)", False],
        later=["laterThan({d:'2026-11-25'}, '2026-11-19')", True],
        later_ts=["laterThan({d:'2026-11-25T17:00:00.000Z'}, '2026-11-19')", True],
        today=["laterThan({d:'2026-11-19'}, '2026-11-19')", False],
        past=["laterThan({d:'2026-11-12'}, '2026-11-19')", False],
        undated=["laterThan({}, '2026-11-19')", False])
    js = helpers + f'\nconst C={json.dumps(cards, ensure_ascii=False)};\n' + \
        'console.log(JSON.stringify({' + ','.join(f'{k}:{v[0]}' for k, v in cases.items()) + '}));'
    got = json.loads(subprocess.run([node, '-e', js], capture_output=True, text=True, encoding='utf-8', check=True).stdout)
    for k, (_, want) in cases.items():
        assert got[k] is want, (k, got[k])
    print("ok — a row is on the calendar by its words, a short card matches only itself, a later day's step stays off today")


if __name__ == '__main__':
    main()
