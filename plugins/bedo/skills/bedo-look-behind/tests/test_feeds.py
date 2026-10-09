# -*- coding: utf-8 -*-
"""Drives within drives, end to end through the look behind (9 Oct 2026).

The canon fixture, with its two drives fed upward: 'be•do drive' and D9 both
feed D8, and D8 feeds D7. Plus two drives that feed each other. What moved must
show D7 → D8 → (be•do drive, D9) nested, each parent's minutes including its
children's, the headline counting each step once, D7's destination reached
through the chain, and the loop named in QA without hanging the build.

Every name below is an obvious invention.

    python3 tests/test_feeds.py
"""
import importlib.util, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('test_canon', os.path.join(HERE, 'test_canon.py'))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

RFD = dict(C.RFD, feeds='fldRFeeds')
D9, D8, D7, BD = 'D9 — Example drive', 'D8 — Example parent', 'D7 — Example grandparent', 'be•do drive'
LA, LB = 'D5 — Loop one', 'D6 — Loop two'
FEEDS = {BD: [D8], D9: [D8], D8: [D7], LA: [LB], LB: [LA]}
RHYTHMS = C.RHYTHMS + [(D8, '♐ drive', '', []), (D7, '♐ drive', '', ['a far destination']),
                       (LA, '♐ drive', '', []), (LB, '♐ drive', '', [])]


def main():
    tmp = tempfile.mkdtemp(prefix='lb-feeds-')

    def w(name, obj):
        p = os.path.join(tmp, name)
        open(p, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False))
        return p
    local = json.loads(json.dumps(C.LOCAL)); local['fields']['rhythms'] = RFD
    p_rhy = w('rhythms.json', C.dump(C.ref_records(
        [(n, t, 'active', e, [{'name': d} for d in ds], [{'id': 'x', 'name': f} for f in FEEDS.get(n, [])])
         for n, t, e, ds in RHYTHMS],
        (RFD['name'], RFD['type'], RFD['status'], RFD['emoji'], RFD['dest'], RFD['feeds']), 'rhy')))
    out = os.path.join(tmp, 'page.html')
    r = subprocess.run([sys.executable, C.BUILDER, '--day', C.DAY.isoformat(),
                        '--local', w('local.json', local), '--stream', w('w39.json', C.dump(C.STREAM)),
                        '--rhythms', p_rhy, '--template', C.ENGINE, '--out', out, '--secure', 'secure', '--allow-unwritten'],
                       capture_output=True, text=True, encoding='utf-8', timeout=60,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    log = json.loads(r.stdout)
    html = open(out, encoding='utf-8').read()
    D = json.loads(html.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])
    E = D['effectiveness']

    roots = E['drives']
    assert [n['drive'] for n in roots] == [D7], [n['drive'] for n in roots]   # nested, not peers
    d7 = roots[0]
    d8 = d7['children'][0]
    assert d8['drive'] == D8 and not d8['items'], d8
    kids = {next(n for n in (BD, D9) if c['drive'].endswith(n)): c for c in d8['children']}
    assert set(kids) == {BD, D9}, list(kids)
    own = kids[BD]['min'] + kids[D9]['min']
    assert own == 148 and d8['min'] == own and d7['min'] == own and d7['own_min'] == 0, (d7, d8)
    assert d7['n'] == 3 and kids[BD]['n'] == 2, (d7['n'], kids[BD]['n'])
    assert E['min'] == 148                                                   # each step once
    assert 'a far destination' in [d['name'] for d in E['destinations']], E['destinations']
    assert len(log['qa']['feeds_loops']) == 1 and LA in log['qa']['feeds_loops'][0], log['qa']
    print('ok — moved work rolls up two levels, nests, counts once, reaches the far destination; the loop is named')


if __name__ == '__main__':
    main()
