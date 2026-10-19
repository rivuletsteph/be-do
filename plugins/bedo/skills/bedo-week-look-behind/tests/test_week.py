# -*- coding: utf-8 -*-
"""The week look behind, by drive, end to end over an invented week.

A two-level chain (D12 feeds D11 feeds D10) and two drives that feed each other
(D20, D21). Time, closed and open each count under the row's own drive and every
drive above it; the child sits nested under its parent; the headline counts each
row once; the loop is named and counts nothing twice. Also: a row outside the
week is not counted, and an action closed after the week is still open in it.

Every name below is an obvious invention.

    python3 tests/test_week.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BUILDER = os.path.join(SKILL, 'scripts', 'week_look_behind.py')
ENGINE = os.path.join(SKILL, 'assets', 'week_look_behind_engine.html')

SF = dict(title='fT', key='fK', when='fW', end='fE', status='fS', rhythm='fR', deliv='fD', target='fG')
RF = dict(name='rN', emoji='rE', feeds='rF')
LOCAL = {'utc_offset_hours': 0, 'week_zero_sunday': '2026-09-13', 'week_zero_number': 38,
         'fields': {'stream': SF, 'rhythms': RF}}
TOP, MID, LEAF, LA, LB = 'D10 — School year', 'D11 — Robot club', 'D12 — Robot arm', 'D20 — Garden', 'D21 — Compost'
DONE, INT, MOT, LOG = '✅ done', '⬜ intention', '▶️ in motion', '● log'

n = 0


def row(title, drive, status, when, end=None, key=None, created=None):
    global n
    n += 1
    c = {SF['title']: title, SF['rhythm']: drive, SF['status']: status, SF['when']: when}
    if end:
        c[SF['end']] = end
    if key:
        c[SF['key']] = key
    return {'id': f'rec{n:05d}', 'createdTime': created or when, 'cellValuesByFieldId': c}


T = '2026-09-29T{}:00.000Z'   # Tuesday of W40 (Sun 27 Sep – Sat 3 Oct)
STREAM = [
    row('arm work', LEAF, DONE, T.format('09:00'), T.format('10:00')),                 # 60 min, a one-row action
    row('club log', MID, LOG, T.format('11:00'), T.format('11:30')),                   # 30 min, not an action
    row('school plan', TOP, INT, T.format('12:00'), key='k1'),                          # open
    row('arm next', LEAF, INT, T.format('13:00'), key='k2'),                            # open, closed after the week
    row('arm next', LEAF, DONE, '2026-10-05T09:00:00.000Z', '2026-10-05T09:30:00.000Z', key='k2'),
    row('garden dig', LA, DONE, T.format('14:00'), T.format('14:20')),                  # 20 min on the loop
    row('old arm work', LEAF, DONE, '2026-09-20T09:00:00.000Z', '2026-09-20T10:00:00.000Z'),  # the week before
    row('nap', '', LOG, T.format('15:00'), T.format('15:45')),                          # no drive
]
RHYTHMS = [{'id': f'rhy{i}', 'createdTime': T.format('00:00'), 'cellValuesByFieldId': {
    RF['name']: name, RF['feeds']: [{'id': 'x', 'name': f} for f in feeds]}}
    for i, (name, feeds) in enumerate([(TOP, []), (MID, [TOP]), (LEAF, [MID]), (LA, [LB]), (LB, [LA])])]


def dump(recs):
    return {'records': recs, 'metadata': {'totalRecordCount': len(recs)}}


def main():
    tmp = tempfile.mkdtemp(prefix='week-')

    def w(name, obj):
        p = os.path.join(tmp, name)
        open(p, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False))
        return p
    out = os.path.join(tmp, 'week.html')
    r = subprocess.run([sys.executable, BUILDER, '--week', '2026-09-30', '--local', w('local.json', LOCAL),
                        '--stream', w('w40.json', dump(STREAM)), '--rhythms', w('rhythms.json', dump(RHYTHMS)),
                        '--template', ENGINE, '--out', out],
                       capture_output=True, text=True, encoding='utf-8', timeout=60,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    html = open(out, encoding='utf-8').read()
    D = json.loads(html.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])

    assert D['week'] == 'W40' and D['range'] == 'Sun 27 Sep – Sat 3 Oct', (D['week'], D['range'])
    T_ = D['totals']
    # each row once: 60 + 30 + 20 on drives; arm work closed + garden dig closed; two open
    assert (T_['min'], T_['min_no_drive'], T_['closed'], T_['open']) == (110, 45, 2, 2), T_
    roots = {x['drive']: x for x in D['drives']}
    assert MID not in roots and LEAF not in roots, list(roots)
    top = roots[TOP]
    assert (top['min'], top['own_min'], top['closed'], top['open'], top['open_own']) == (90, 0, 1, 2, 1), top
    mid = top['children'][0]
    assert mid['drive'] == MID and (mid['min'], mid['own_min'], mid['closed'], mid['open']) == (90, 30, 1, 1), mid
    leaf = mid['children'][0]
    assert leaf['drive'] == LEAF and (leaf['min'], leaf['closed'], leaf['open']) == (60, 1, 1), leaf
    assert [d['t'] for d in leaf['done']] == ['arm work'] and [s['t'] for s in leaf['still']] == ['arm next'], leaf
    loop = [x for x in D['drives'] if x['drive'] in (LA, LB)]
    assert len(loop) == 1 and loop[0]['min'] == 20 and loop[0]['children'][0]['min'] == 20, loop
    assert len(D['loops']) == 1 and LA in D['loops'][0], D['loops']
    print('ok — the week rolls up two levels, nests, counts once, keeps to its window, and a loop ends')
    readings(w, out)


def readings(w, out):
    """Her Sun 18 Oct build notes: time by area, what moved, rest as a reset, and
    the needs on the secure base. Sleep is in bed and never an area; a night
    belongs to its morning; somebody else's night is theirs; readiness comes from
    the Oura row's own words; a day with no ⏏️ row is secure, and says so."""
    sf = dict(SF, practice='fP', wellness='fL', person='fN', details='fX')
    loc = dict(LOCAL, fields={'stream': sf, 'rhythms': RF}, self_person='♋ Me', growing_types=['♐ drive'],
               pie=[{'k': 'play', 'practices': ['show']}])

    def r(title, pr, well, when, end=None, person=None, details=None, status=LOG, drive=''):
        x = row(title, drive, status, when, end)
        c = x['cellValuesByFieldId']
        c.update({sf['practice']: pr, sf['wellness']: well})
        if person:
            c[sf['person']] = person
        if details:
            c[sf['details']] = details
        return x
    D = '2026-09-{}T{}:00.000Z'
    rows = [
        r('sleep', '😴 sleep', '🤸\u200d♀️ body', D.format(28, '22:00'), D.format(29, '06:00')),     # 480, Tue's night
        r('kid sleep', '😴 sleep', '🤸\u200d♀️ body', D.format(28, '20:00'), D.format(29, '07:00'), person='♑ Kid'),
        r('walk', '🚶\u200d♀️ walking', '🤸\u200d♀️ body', D.format(29, '07:00'), D.format(29, '08:00')),   # 60 deficiency
        r('a phone call', '☎️ phone', '🩷 heart', D.format(29, '09:00'), D.format(29, '09:30')),      # 30 deficiency
        r('read', '📗 book', '🧠 mind', D.format(29, '10:00'), D.format(29, '10:45')),                # 45 growth
        r('a show', '📺 show', '🔥 fire', D.format(29, '20:00'), D.format(29, '21:00')),              # 60 growth, play
        r('checked Oura — readiness 84, sleep 77', '🪐 morning oura', '🤸\u200d♀️ body', D.format(29, '06:10'),
          details='7 h 35 asleep of 8 h'),
        r('not secure — a hard call', '⏏️ secure base', '💖 spirit', D.format(30, '08:00')),
        r('a plan', '⚡ action', '🌎 earth', D.format(30, '09:00'), D.format(30, '10:00'), status=INT),  # never lived
    ]
    o = out.replace('week.html', 'week2.html')
    rr = subprocess.run([sys.executable, BUILDER, '--week', '2026-09-30', '--local', w('local2.json', loc),
                         '--stream', w('w40b.json', dump(rows)), '--rhythms', w('rhythms2.json', dump(RHYTHMS)),
                         '--template', ENGINE, '--out', o],
                        capture_output=True, text=True, encoding='utf-8', timeout=60,
                        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    if rr.returncode:
        sys.exit(rr.stdout + rr.stderr)
    html = open(o, encoding='utf-8').read()
    X = json.loads(html.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])
    tue, wed = X['days'][2], X['days'][3]
    assert (tue['bed'], tue['readiness'], tue['sleep_score'], tue['play']) == (480, 84, 77, 60), tue
    assert (tue['deficiency'], tue['growth'], tue['be']) == (90, 105, 135), tue
    assert X['time']['bed'] == 480 and X['time']['be'] == 135 and X['time']['tend'] == 60, X['time']
    assert X['rest'] == {'bed': 480, 'play': 60, 'nights': 1, 'readiness': [84]}, X['rest']
    assert [g['min'] for g in X['needs']['deficiency']] == [60, 30], X['needs']
    assert [g['min'] for g in X['needs']['growth']] == [45, 60], X['needs']
    assert wed['secure'] == 'not secure — a hard call' and not wed['assumed'], wed
    assert tue['secure'] == 'secure' and tue['assumed'] and X['secure_days'] == 6 and X['secure_assumed'] == 6, X
    print('ok — time by area, rest and readiness, and the needs on the secure base')


if __name__ == '__main__':
    main()
