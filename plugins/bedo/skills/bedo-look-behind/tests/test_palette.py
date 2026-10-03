# -*- coding: utf-8 -*-
"""Both pages wear be•do's now palette, day and night, and can't drift from it.

plugins/bedo/assets/now-palette.css is the one source (3 Oct 2026). This checks the
shared roles in each engine against it: background, text, secondary text, lines,
links, and brick where each page uses it for work.

    python3 tests/test_palette.py
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.dirname(os.path.dirname(HERE))
PALETTE = os.path.join(os.path.dirname(SKILLS), 'assets', 'now-palette.css')
ENGINES = {'day behind': os.path.join(SKILLS, 'bedo-look-behind', 'assets', 'look_behind_engine.html'),
           'day ahead': os.path.join(SKILLS, 'bedo-day-ahead', 'assets', 'day_ahead_engine.html')}


def block_vars(text, selector):
    i = text.index(selector)
    body = text[text.index('{', i) + 1:text.index('}', i)]
    return {k: v.strip().upper() for k, v in re.findall(r'--([\w-]+)\s*:\s*([^;]+);', body)}


def main():
    css = open(PALETTE, encoding='utf-8').read()
    pal = {'day': block_vars(css, ':root'), 'night': {**block_vars(css, ':root'), **block_vars(css, '[data-theme="night"]')}}
    # the page's own name for a role → the palette's name for it
    shared = {'ground': 'bg', 'ink': 'text', 'muted': 'soft', 'rule': 'line'}
    per = {'day behind': {'link': 'link', 'grow': 'main'}, 'day ahead': {'dest': 'link', 'card': 'card'}}
    fails = []
    for name, path in ENGINES.items():
        html = open(path, encoding='utf-8').read()
        modes = {'day': block_vars(html, ':root{'), 'night': block_vars(html, 'html[data-bedo="night"]')}
        if 'prefers-color-scheme' not in html or 'data-bedo' not in html:
            fails.append(f'{name}: light or dark does not follow the phone')
        for mode, have in modes.items():
            for mine, theirs in {**shared, **per[name]}.items():
                if mine == 'card' and mode == 'night':
                    continue
                want = pal[mode].get(theirs)
                if have.get(mine) != want:
                    fails.append(f'{name} {mode}: --{mine} is {have.get(mine)}, the palette says {want}')
        print(f'  ok   {name}' if not any(f.startswith(name) for f in fails) else f'  FAIL {name}')
    print()
    if fails:
        print(f'{len(fails)} failed:'); [print('  FAIL ' + f) for f in fails]; sys.exit(1)
    print('both pages wear the now palette, day and night.')


if __name__ == '__main__':
    main()
