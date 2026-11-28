# -*- coding: utf-8 -*-
"""The heading on a day page (19 Nov 2026).

On the day page the date had the week's word after it, behind a dash and in
italics. Her intention now sits under the date in plain words, her first one.
Where she hasn't given one yet the line stays blank, never the week's word in
its place (20 Nov 2026, her words: it's my job to say what my intention is
today). A page with no intentions at all (the week page) keeps the dash and
the word.

The heading runs in node where it is installed; without it, only the wiring is
checked. Every word below is an obvious invention.

    python3 tests/test_heading.py
"""
import json, os, re, shutil, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.dirname(HERE)


def main():
    b = open(os.path.join(PARTS, 'basics.js'), encoding='utf-8').read()
    css = open(os.path.join(PARTS, 'shell.css'), encoding='utf-8').read()
    m = re.search(r"\{ const h=document\.getElementById\('h1'\).*?\}\n", b + '\n', re.S)
    assert m, 'the heading block is not in basics.js'
    block = m.group(0)
    assert 'Array.isArray(D.intentions)' in block and 'say1' in block, block
    rule = re.search(r'h1 \.say1\{([^}]*)\}', css)
    assert rule and 'display:block' in rule.group(1) and 'font-style:normal' in rule.group(1), 'h1 .say1 style'

    node = shutil.which('node')
    if not node:
        print('test_heading: wiring ok (node not found, heading not run)')
        return
    esc = re.search(r"^const esc=.*$", b, re.M).group(0)
    cases = [
        (dict(label='Thu 3 Mar', word='Rising', intentions=['moving like a kite']), 'moving like a kite', False),
        (dict(label='Thu 3 Mar', word='Rising', intentions=[]), None, False),          # none yet: blank
        (dict(label='Thu 3 Mar', word='Rising', intentions=[None, '']), None, False),
        (dict(label='Thu 3 Mar', word=None, intentions=[None]), None, False),
        (dict(label='Week 9', word='Rising'), None, True),
    ]
    js = esc + "\nconst out=[];\n"
    for D, _, _ in cases:
        js += ("{ const D=%s; const el={innerHTML:''}; const document={getElementById:()=>el};\n%s\nout.push(el.innerHTML); }\n"
               % (json.dumps(D), block))
    js += "console.log(JSON.stringify(out));"
    r = subprocess.run([node, '-e', js], capture_output=True, text=True, encoding='utf-8')
    assert r.returncode == 0, r.stderr
    got = json.loads(r.stdout)
    for (D, say, dash), h in zip(cases, got):
        assert h.startswith(D['label']), h
        if say:
            assert h == D['label'] + '<span class="say1">%s</span>' % say, h
        if dash:
            assert '— Rising' in h and 'say1' not in h, h
        if not say and not dash:
            assert h == D['label'], h
        assert ('—' in h) == dash, h
        assert dash or 'Rising' not in h, h                                       # the week's word never stands in
    print('test_heading: %d headings ok' % len(got))


if __name__ == '__main__':
    main()
