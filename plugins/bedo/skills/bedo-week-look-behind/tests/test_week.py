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
    args = [sys.executable, BUILDER, '--week', '2026-09-30', '--local', w('local.json', LOCAL),
            '--stream', w('w40.json', dump(STREAM)), '--rhythms', w('rhythms.json', dump(RHYTHMS)),
            '--template', ENGINE, '--out', out]
    # 19 Oct 2026: a week is QA'd day by day before its look behind — no dayqa, no build
    r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', timeout=60,
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    assert r.returncode and 'no dayqa for Sun 27 Sep' in r.stderr and 'Sat 03 Oct' in r.stderr, r.stderr
    r = subprocess.run(args + ['--qa-anyway'], capture_output=True, text=True, encoding='utf-8', timeout=60,
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
    assert 'no_dayqa' in json.loads(r.stdout)['qa'], r.stdout        # built as it is, and says so
    print('ok — the week rolls up two levels, nests, counts once, keeps to its window, and a loop ends')
    readings(w, out)


def readings(w, out):
    """Her Sun 18 Oct build notes: time by area, what moved, rest as a reset, and
    the needs on the secure base. Sleep is in bed and never an area; a night
    belongs to its morning; somebody else's night is theirs; readiness comes from
    the Oura row's own words; a day with no ⏏️ row is secure, and says so."""
    sf = dict(SF, practice='fP', wellness='fL', person='fN', details='fX')
    pf = dict(name='pN', group='pG')
    loc = dict(LOCAL, fields={'stream': sf, 'rhythms': RF, 'practices': pf}, self_person='♋ Me', growing_types=['♐ drive'],
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
        r('lunch out with the kid', '🍽️ lunch', '🤸\u200d♀️ body', D.format(29, '12:00'), D.format(29, '12:40'),
          person='♑ Kid'),                                          # 40 body AND 40 heart: time with somebody
        r('read', '📗 book', '🧠 mind', D.format(29, '10:00'), D.format(29, '10:45')),                # 45 growth
        r('a show', '📺 show', '🔥 fire', D.format(29, '20:00'), D.format(29, '21:00')),              # 60 growth, play
        r('checked Oura — readiness 84, sleep 77, activity 91', '🪐 morning oura', '🤸\u200d♀️ body', D.format(29, '06:10'),
          details='7 h 35 asleep of 8 h'),
        r('not secure — a hard call', '⏏️ secure base', '💖 spirit', D.format(30, '08:00')),
        r('a plan', '⚡ action', '🌎 earth', D.format(30, '09:00'), D.format(30, '10:00'), status=INT,  # never lived
          details='\n'.join(f'[be•do] dayqa shown 2026-{d} 21:40 · 0 proposed'      # every day QA'd: it builds
                            for d in ('09-27', '09-28', '09-29', '09-30', '10-01', '10-02', '10-03'))),
    ]
    fc = r('forecast: the garden fence is up by Thursday', '💡 insight', '🧠 mind', '2026-09-20T09:00:00.000Z')
    fc['cellValuesByFieldId'][SF['target']] = D.format(30, '17:00')               # due this week (20 Oct 2026)
    late = r('forecast: snow by January', '💡 insight', '🧠 mind', '2026-09-20T09:00:00.000Z')
    late['cellValuesByFieldId'][SF['target']] = '2027-01-29T17:00:00.000Z'
    rows += [fc, late]
    rows += [r('the river day', '⭐ highlight', '💖 spirit', D.format(30, '18:00'), person='♑ Kid',
               details='The rope swing, swimming, and the hike we did five years ago. Even more wonderful with them.'),
             r('the river day', "🌟 kid's highlight", '💖 spirit', D.format(30, '18:00'), person='♑ Kid'),
             r('a quiet glimmer', '✨ glimmer', '💖 spirit', D.format(30, '19:00'))]
    # the flows: two dawn practices and its close on Tue, one dusk practice left open on Wed
    rows += [r('coffee', '☕ coffee', '🤸\u200d♀️ body', D.format(29, '06:30')),
             r('water', '🥤 morning water', '🤸\u200d♀️ body', D.format(29, '06:35')),
             r('dawn close', '🌅 dawn flow close', '💖 spirit', D.format(29, '08:30')),
             r('tea', '🫖 tea', '🤸\u200d♀️ body', D.format(30, '20:30'))]
    cat = dump([{'id': f'recP{i}', 'createdTime': '2026-09-01T00:00:00.000Z',
                 'cellValuesByFieldId': {'pN': p, 'pG': 'flow'}} for i, p in enumerate(['☕ coffee', '🥤 morning water', '🫖 tea'])])
    # an original left behind in the older base after a move is the same row twice
    orig = r('a walk, moved', '🚶\u200d♀️ walking', '🤸\u200d♀️ body', D.format(29, '07:00'), D.format(29, '08:00'))
    rows[2]['cellValuesByFieldId'][sf['details']] = f"[be•do] moved from w39 ({orig['id']}) on 30 Sep"
    rows.append(orig)
    o = out.replace('week.html', 'week2.html')
    rr = subprocess.run([sys.executable, BUILDER, '--week', '2026-09-30', '--local', w('local2.json', loc),
                         '--stream', w('w40b.json', dump(rows)), '--rhythms', w('rhythms2.json', dump(RHYTHMS)),
                         '--practices', w('practices2.json', cat), '--template', ENGINE, '--out', o],
                        capture_output=True, text=True, encoding='utf-8', timeout=60,
                        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    if rr.returncode:
        sys.exit(rr.stdout + rr.stderr)
    html = open(o, encoding='utf-8').read()
    X = json.loads(html.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])
    tue, wed = X['days'][2], X['days'][3]
    assert (tue['bed'], tue['readiness'], tue['sleep_score'], tue['play']) == (480, 84, 77, 60), tue
    assert (tue['deficiency'], tue['growth'], tue['be'], tue['people']) == (170, 105, 175, 40), tue
    assert X['time']['bed'] == 480 and X['time']['be'] == 175 and X['time']['tend'] == 60, X['time']
    assert X['rest'] == {'bed': 480, 'play': 60, 'nights': 1, 'readiness': [84], 'activity': [91]}, X['rest']
    assert [g['min'] for g in X['needs']['deficiency']] == [100, 70], X['needs']
    assert tue['logged'] == 235 and tue['awake'] == 960, (tue['logged'], tue['awake'])   # 7–8, 9–9:30, 10–10:45, 12–12:40, 20–21
    assert [g['min'] for g in X['needs']['growth']] == [45, 60], X['needs']
    assert wed['secure'] == 'not secure — a hard call' and not wed['assumed'], wed
    assert tue['secure'] == 'secure' and tue['assumed'] and X['secure_days'] == 6 and X['secure_assumed'] == 6, X
    # the garden: a marked moment is a flower; her highlight and the kid's own at the same
    # minute are one flower, marked as theirs too; her words add areas, a memory and synergy
    g = X['garden']
    assert [m['t'] for m in g] == ['the river day', 'a quiet glimmer'], [m['t'] for m in g]
    day = g[0]
    assert day['both'] == 'kid' and day['memory'] and day['synergy'], day
    assert {'body', 'heart', 'fire', 'spirit'} <= set(day['areas']), day['areas']
    assert g[1]['layers'] == 1 and not g[1]['memory'], g[1]
    # the stream: the river day is one stone (her highlight and the kid's, one minute),
    # named by what it was, not by the mark; the quiet glimmer is a stone too
    st = [m for d in X['stream']['days'] for m in d['stones']]
    river = next(m for m in st if m['t'] == 'the river day')
    assert river['theirs'] == ['kid'] and river['memory'] and river['synergy'] and river['g'] != '', river
    assert any(m['t'] == 'a quiet glimmer' for m in st), st
    # the being side: the flows are practices, counted day by day, apart from where moments lived
    be = X['stream']['be']
    assert be[2]['dawn']['n'] == 2 and be[2]['dawn']['closed'] and be[2]['dusk']['n'] == 0, be[2]
    assert be[3]['dusk'] == dict(n=1, closed=False, g=['🫖']) and be[3]['dawn']['n'] == 0, be[3]
    fl = X['stream']['flowed']   # each place it reached opens to its moments
    assert all(x['at'] for t in fl for x in t['moments']), fl
    assert X['forecasts'] == [{'t': 'forecast: the garden fence is up by Thursday'}], X['forecasts']
    assert 'how it turned out' in ' '.join(json.loads(rr.stdout)['qa']['forecasts_due'])
    print('ok — time by area, rest and readiness, the needs on the secure base, the garden and the stream')
    print('ok — the week builds once every day has its dayqa, and lists the forecasts due in it')
    one_day(w, out, loc, rows)


def one_day(w, out, loc, rows):
    """--day: the same page for a single day (20 Oct 2026), its own words on top. The
    night that ended that morning counts whole; words written for another day are refused."""
    o = out.replace('week.html', 'day.html')

    def run(words):
        return subprocess.run([sys.executable, BUILDER, '--day', '2026-09-29', '--words', w('words.json', words),
                               '--local', w('local3.json', loc), '--stream', w('w40c.json', dump(rows)),
                               '--rhythms', w('rhythms3.json', dump(RHYTHMS)), '--template', ENGINE, '--out', o],
                              capture_output=True, text=True, encoding='utf-8', timeout=60,
                              env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    rr = run({'day': '2026-09-29', 'lead': 'a walk and a show', 'story': [['🚶', 'the walk'], ['📺', 'the show']]})
    if rr.returncode:
        sys.exit(rr.stdout + rr.stderr)
    html = open(o, encoding='utf-8').read()
    X = json.loads(html.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])
    assert '<title>The Day Behind</title>' in html and X['span'] == 'day' and X['range'] == 'Tue 29 Sep', X['range']
    assert len(X['days']) == 1 and X['days'][0]['bed'] == 480 and X['days'][0]['play'] == 60, X['days']
    assert X['stream']['days'][0]['lead'] == 'a walk and a show' and X['story'][1] == ['📺', 'the show'], X['story']
    # the day behind's own keys, for words.py (25 Oct 2026): the day, the lead as title, what is still a draft
    assert (X['day'], X['title'], X['draft']) == ('2026-09-29', 'a walk and a show', {'lead': False, 'story': False}), X['draft']
    assert not [m for d in X['stream']['days'] for m in d['stones']], 'Wednesday\'s moments are not Tuesday\'s'
    assert run({'day': '2026-09-30', 'lead': 'x', 'story': []}).returncode, 'words for another day must be refused'
    print('ok — one day: its own window, the whole night before, its own words, and no one else\'s')
    photos(w, out, loc, rows)


def photos(w, out, loc, rows):
    """day_photos.py shrinks the day's photos (named by the phone, in UTC) and the builder
    places each by its time: in the row it falls in, left out when the row is a routine
    check (an Oura screen), and in the day's pictures when nothing is near it."""
    try:
        from PIL import Image
    except ImportError:
        print('skipped — photos (no PIL here)')
        return
    tmp = os.path.dirname(out)
    orig, small = os.path.join(tmp, 'originals'), os.path.join(tmp, 'small')
    os.makedirs(orig, exist_ok=True)
    for n in ('PXL_20260929_073000123.jpg',    # inside the walk, 07:00–08:00
              'PXL_20260929_061000456.jpg',    # the Oura check at 06:10: left out
              'PXL_20260929_230000789.jpg',    # nothing near it
              'PXL_20260930_120000000.jpg'):   # another day
        Image.new('RGB', (3000, 4000), (90, 140, 120)).save(os.path.join(orig, n))
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    dp = os.path.join(SKILL, 'scripts', 'day_photos.py')
    r = subprocess.run([sys.executable, dp, '--day', '2026-09-29', '--local', w('local4.json', loc), '--out', small,
                        '--from', orig], capture_output=True, text=True, encoding='utf-8', timeout=60, env=env)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    got = sorted(os.listdir(small))
    assert len(got) == 3 and max(Image.open(os.path.join(small, n)).size[1] for n in got) <= 900, got
    o = out.replace('week.html', 'day-photos.html')
    r = subprocess.run([sys.executable, BUILDER, '--day', '2026-09-29', '--photos', small, '--local', w('local4.json', loc),
                        '--stream', w('w40d.json', dump(rows)), '--rhythms', w('rhythms4.json', dump(RHYTHMS)),
                        '--template', ENGINE, '--out', o], capture_output=True, text=True, encoding='utf-8',
                       timeout=60, env=env)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    assert json.loads(r.stdout)['photos'] == {'read': 3, 'on_moments': 0, 'in_pictures': 2, 'left_out': 1}, r.stdout
    X = json.loads(open(o, encoding='utf-8').read().split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])
    pics = X['stream']['days'][0]['pictures']
    assert [p['t'] for p in pics] == ['walk', ''] and pics[0]['src'].startswith('data:image/jpeg;base64,'), pics
    # a photo taken at a moment's minute sits inside that moment
    wed = os.path.join(tmp, 'small-wed')
    os.makedirs(wed, exist_ok=True)
    Image.new('RGB', (40, 50), (1, 2, 3)).save(os.path.join(wed, 'PXL_20260930_190100000.jpg'))
    r = subprocess.run([sys.executable, BUILDER, '--day', '2026-09-30', '--photos', wed, '--local', w('local4.json', loc),
                        '--stream', w('w40d.json', dump(rows)), '--rhythms', w('rhythms4.json', dump(RHYTHMS)),
                        '--template', ENGINE, '--out', o], capture_output=True, text=True, encoding='utf-8',
                       timeout=60, env=env)
    assert json.loads(r.stdout)['photos']['on_moments'] == 1, r.stdout + r.stderr
    print('ok — photos: made small, placed by the time they were taken, routine checks left out')


if __name__ == '__main__':
    main()
