# -*- coding: utf-8 -*-
"""Drives within drives, end to end through the day ahead (9 Oct 2026).

The clock test's fixture, plus two drives above its example drive — D9 feeds
D8, D8 feeds D7 — and a pair that feed each other. Open work on D9 must count
under D9, D8 and D7; D9 must sit under D8 under D7, never beside them; the
headline counts each row once; the pick's lane runs through D8 and D7 to what
they serve; and the loop is named and does not hang the build.

Every name below is an obvious invention.

    python3 tests/test_feeds.py
"""
import copy, importlib.util, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('test_clock', os.path.join(HERE, 'test_clock.py'))
C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C)

RF = dict(C.RF, feeds='fldRFeeds')
LOCAL = copy.deepcopy(C.LOCAL); LOCAL['fields']['rhythms'] = RF
D9, D8, D7 = 'D9 — Example drive', 'D8 — Example parent', 'D7 — Example grandparent'
LA, LB = 'D5 — Loop one', 'D6 — Loop two'


def rhy(i, name, feeds=(), dest=()):
    return {'id': f'rhy{i:05d}', 'createdTime': C.stamp(C.TODAY, 0, 0),
            'cellValuesByFieldId': {RF['name']: name, RF['type']: '♐ drive', RF['status']: 'active',
                                    RF['emoji']: '🚐' if name == D9 else '·',
                                    RF['dest']: [{'name': d} for d in dest],
                                    RF['feeds']: [{'id': 'x', 'name': f} for f in feeds]}}


RHYTHMS = [rhy(1, D9, [D8], ['an example destination']), rhy(2, D8, [D7]),
           rhy(3, D7, [], ['a far destination']), rhy(4, LA, [LB]), rhy(5, LB, [LA])]
STREAM = C.STREAM + [{
    # a step on D9 that no calendar event owns, so it can be one of the three
    # (since 9 Oct a row an event already holds is never recommended)
    'id': 'rec00000008', 'createdTime': C.stamp(C.TODAY, 6, 8),
    'cellValuesByFieldId': {C.SF['title']: 'Sand the gearbox housing', C.SF['key']: 'k008',
                            C.SF['status']: '▶️ in motion', C.SF['practice']: '⚡ action',
                            C.SF['rhythm']: D9, C.SF['target']: C.stamp(C.TODAY + C.dt.timedelta(days=2), 12, 0)},
}, {
    'id': 'rec00000009', 'createdTime': C.stamp(C.TODAY, 6, 9),
    'cellValuesByFieldId': {C.SF['title']: 'Loop work', C.SF['key']: 'k009',
                            C.SF['status']: '⬜ intention', C.SF['practice']: '⚡ action',
                            C.SF['rhythm']: LA},
}]


def main():
    tmp = tempfile.mkdtemp(prefix='feeds-')

    def w(name, obj):
        p = os.path.join(tmp, name)
        with open(p, 'w', encoding='utf-8') as fh:
            json.dump(obj, fh, ensure_ascii=False)
        return p
    out = os.path.join(tmp, 'page.html')
    r = subprocess.run(
        [sys.executable, C.BUILDER, '--today', C.TODAY.isoformat(),
         '--local', w('local.json', LOCAL), '--stream', w('w39.json', C.dump(STREAM)),
         '--rhythms', w('rhythms.json', C.dump(RHYTHMS)), '--calendar', w('cal.json', C.CAL),
         '--template', C.ENGINE, '--out', out, '--now', '07:15', '--secure', 'secure'],
        capture_output=True, text=True, encoding='utf-8', timeout=60,
        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    P = json.load(open(os.path.join(tmp, 'page.plan.json'), encoding='utf-8'))
    html = open(out, encoding='utf-8').read()
    D = json.loads(html.split('const DATA=', 1)[1].split(';</script>', 1)[0])

    X = P['drives']
    assert X['open'] == 4, X                                   # each row once in the headline
    roots = {n['drive']: n for n in X['tree']}
    assert D7 in roots and D8 not in roots and D9 not in roots, list(roots)
    d7 = roots[D7]
    assert (d7['n'], d7['n_own']) == (3, 0), d7
    d8 = d7['children'][0]
    assert d8['drive'] == D8 and (d8['n'], d8['n_own']) == (3, 0), d8
    d9 = d8['children'][0]
    assert d9['drive'] == D9 and (d9['n'], d9['n_own']) == (3, 3) and not d9['children'], d9
    loop_roots = [n for n in X['tree'] if n['drive'] in (LA, LB)]
    assert len(loop_roots) == 1 and loop_roots[0]['n'] == 1, loop_roots
    assert loop_roots[0]['children'][0]['n'] == 1, loop_roots    # the loop counts its row once per drive
    assert len(X['loops']) == 1 and LA in X['loops'][0] and LB in X['loops'][0], X['loops']
    assert D['drives'] == X

    lane = next(l for l in D['map']['lanes'] if l['drive'] == D9)
    assert lane['via'] == [D7, D8], lane
    assert set(lane['dest']) == {'an example destination', 'a far destination'}, lane
    print('ok — feeds roll up two levels, nest, count once in the total, and a loop ends')


if __name__ == '__main__':
    main()
