# -*- coding: utf-8 -*-
"""The day page's story with its photos, end to end over an invented day (4 Nov 2026, her words: integrate the
photos into the summary of my day in a beautiful way; the pictures are too big on what mattered; the cottonwoods
and lunch at the ditch being repeated; the pictures at the ditch, those three should be grouped together; a
little image of what the deliverable was).

  · a highlight told at dusk about an earlier moment is that moment, starred, never a second card
  · photos taken close together are one group, on the group's best moment
  · each group sits under the line of her story it belongs to
  · a photo her rows link comes before one placed only by its time
  · a deliverable's picture rides on its closed action

Every name below is an obvious invention. Times are UTC; the day is UTC+0.

    python3 tests/test_day_story.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BUILDER = os.path.join(SKILL, 'scripts', 'week_look_behind.py')
THUMBS = os.path.join(SKILL, 'scripts', 'deliverable_thumbs.py')
ENGINE = os.path.join(SKILL, 'assets', 'week_look_behind_engine.html')

try:
    from PIL import Image
except ImportError:
    print('skipped — the day story (no PIL here)')
    sys.exit(0)

F = dict(title='fT', key='fK', when='fW', end='fE', status='fS', rhythm='fR', deliv='fD', practice='fP',
         details='fX', person='fPe', photo='fPh', photo_links='fL')
LOCAL = {'utc_offset_hours': 0, 'week_zero_sunday': '2026-09-13', 'week_zero_number': 38, 'self_person': '♋ Me',
         'fields': {'stream': F, 'rhythms': dict(name='rN', emoji='rE')}}
DAY = '2026-10-06'
n = 0


def row(practice, title, at, end=None, **kw):
    global n
    n += 1
    c = {F['practice']: practice, F['title']: title, F['when']: f'{DAY}T{at}:00.000Z', F['status']: kw.pop('status', '● log')}
    if end:
        c[F['end']] = f'{DAY}T{end}:00.000Z'
    for k, v in kw.items():
        c[F[k]] = v
    return {'id': f'rec{n:05d}', 'createdTime': c[F['when']], 'cellValuesByFieldId': c}


def link(fid):
    return f'https://drive.google.com/file/d/{fid}/view'


ROWS = [
    row('✨ glimmer', '✨ Pip and the dog at the swing', '08:30', person='♑Pip', photo='keeper', photo_links=link('fileSwing0001')),
    row('📝 log', 'Pip up at eight', '08:00', person='♑Pip', photo='keeper', photo_links=link('fileBed00001')),
    row('🔅 sunshine', '🔅 sunshine on the bench by the creek', '12:40', '13:15', photo='keeper', photo_links=link('fileCreek002')),
    row('✨ glimmer', '✨ the sycamores by the creek, from the bench', '13:00', photo='keeper', photo_links=link('fileCreek001')),
    row('⭐ highlight', '⭐ lunch by the creek, sitting with the sycamores', '21:50', photo='keeper', photo_links=link('fileCreek003'),
        details='The highlight of my day was lunch by the creek with the sycamores.'),
    row('⚡ action', 'the site report', '15:00', '16:00', status='✅ done', rhythm='Paid Work', deliv='https://example.org/report'),
]
PHOTOS = {'PXL_20261006_081400000.jpg': 'fileBed00001', 'PXL_20261006_083000000.jpg': 'fileSwing0001',
          'PXL_20261006_083100000.jpg': None,      # beside the swing, linked by no row: placed only by its time
          'PXL_20261006_130100000.jpg': 'fileCreek001', 'PXL_20261006_131200000.jpg': 'fileCreek002',
          'PXL_20261006_131500000.jpg': 'fileCreek003'}
STORY = [['☕', 'up early; coffee'], ['🤸', 'out back with Pip and the dog at the swing'],
         ['🌳', 'lunch on the bench by the creek: the sycamores in the sun'], ['💼', 'the site report']]


def main():
    tmp = tempfile.mkdtemp()
    w = lambda name, obj: (json.dump(obj, open(os.path.join(tmp, name), 'w', encoding='utf-8')), os.path.join(tmp, name))[1]  # noqa: E731
    pics = os.path.join(tmp, 'pics')
    os.makedirs(pics)
    for i, nm in enumerate(PHOTOS):
        Image.new('RGB', (40, 50), (10 * i, 80, 120)).save(os.path.join(pics, nm))
    json.dump({k: v for k, v in PHOTOS.items() if v}, open(os.path.join(pics, 'index.json'), 'w'))
    # the deliverable's picture: an image passed as the page is only made small
    shot = os.path.join(tmp, 'report.png')
    Image.new('RGB', (1440, 960), (200, 210, 220)).save(shot)
    thumbs = os.path.join(tmp, 'thumbs')
    r = subprocess.run([sys.executable, THUMBS, '--page', 'https://example.org/report', shot, '--out', thumbs],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and json.loads(r.stdout)['made'] == 1, r.stdout + r.stderr
    out = os.path.join(tmp, 'day.html')
    r = subprocess.run([sys.executable, BUILDER, '--day', DAY, '--words', w('words.json', dict(day=DAY, lead='a day by the creek', story=STORY)),
                        '--local', w('local.json', LOCAL), '--stream', w('w.json', {'records': ROWS, 'metadata': {'totalRecordCount': len(ROWS)}}),
                        '--rhythms', w('rh.json', {'records': [], 'metadata': {'totalRecordCount': 0}}), '--template', ENGINE,
                        '--photos', pics, '--thumbs', thumbs, '--out', out],
                       capture_output=True, text=True, encoding='utf-8', timeout=60, env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    X = json.loads(open(out, encoding='utf-8').read().split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])
    day = X['stream']['days'][0]
    titles = [m['t'] for m in day['stones']]
    # the dusk highlight is a star on the sycamores, not its own card
    assert not any('lunch by the creek' in t for t in titles), titles
    syc = next(m for m in day['stones'] if 'sycamores by the creek' in m['t'])
    assert [s['g'] for s in syc['stars']] == ['⭐'] and 'highlight of my day' in syc['stars'][0]['words'], syc
    # the creek's three photos are one group on the starred moment; the morning's on the glimmer
    assert len(syc['photos']) == 3 and syc['photo_at'][0].endswith('13:01:00'), syc.get('photo_at')
    swing = next(m for m in day['stones'] if 'swing' in m['t'])
    assert [a[11:16] for a in swing['photo_at']] == ['08:14', '08:30'], swing['photo_at']   # 08:31: a near-copy of 08:30, linked by nothing
    assert not day['pictures'], day['pictures']
    # each group under its line of the story
    assert [len(x) for x in day['story_pics']] == [0, 2, 3, 0], [len(x) for x in day['story_pics']]
    # the deliverable's picture on its closed action
    rep = next(c for c in X['moved']['closed'] if c['t'] == 'the site report')
    assert rep.get('thumb', '').startswith('data:image/jpeg;base64,'), rep
    print('ok — the story carries its photos, grouped; a dusk highlight stars its moment; the deliverable has its picture')
    # the six-photo cap: a linked keeper before an unlinked photo beside a moment with people
    sys.path[:0] = [os.path.join(SKILL, '..', '..', 'core')]
    import datetime as dt
    import bedo_photos as PH
    t0 = dt.datetime(2026, 10, 6, 8)
    kid = dict(practice='✨ glimmer', person='♑Pip')
    placed = [dict(t=t0 + dt.timedelta(minutes=10 * i), src=str(i), row=kid, keeper=True, linked=False) for i in range(6)] + \
             [dict(t=t0 + dt.timedelta(hours=5), src='creek', row=dict(practice='🔅 sunshine'), keeper=True, linked=True)]
    chosen, _ = PH.select(placed, '♋ Me')
    assert 'creek' in [p['src'] for p in chosen], [p['src'] for p in chosen]
    print('ok — at most six: a photo her rows link comes before one placed only by its time')


if __name__ == '__main__':
    main()
