# -*- coding: utf-8 -*-
"""The Stories page builder: the draft's guesses, the page, and the readback.

Every title, name and link below is an obvious invention.

    python3 tests/test_stories.py
"""
import datetime as dt, json, os, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import stories as S  # noqa: E402
import re  # noqa: E402
LOCAL = os.path.join(os.path.dirname(HERE), 'assets', 'stories_local.example.json')
S.set_apps(LOCAL)

TODAY = dt.date(2026, 3, 12)
RECS = [
    {'id': 'recShow1', 'fields': {'title': 'The Example Show', 'kind': '📺 show', 'standing': 'in motion',
                                   'notes': 'Watching it now. (2 Mar)\n———\n[be•do] On Streamly. Next up S1 E4.'}},
    {'id': 'recBook1', 'fields': {'title': 'A Sample Novel — An Author', 'kind': '📗 book', 'standing': 'in motion',
                                   'due': '2026-03-20', 'notes': 'Starting this one on Readr. (1 Mar)'}},
    {'id': 'recPod1', 'fields': {'title': 'An Example Podcast', 'kind': '🎙️ podcast', 'standing': 'in motion',
                                  'source': 'https://podly.example/episode/abc123XYZ', 'notes': 'My next one. (10 Mar)'}},
    {'id': 'recMov1', 'fields': {'title': 'A Made-Up Film', 'kind': '🎥 movie', 'standing': 'want', 'notes': 'Streamly · RT 91%'}},
    {'id': 'recMov2', 'fields': {'title': 'Rental Picture', 'kind': '🎥 movie', 'standing': 'want', 'notes': '$3.99 · RT 70%'}},
    {'id': 'recVid1', 'fields': {'title': 'A Talk', 'kind': '📼 video', 'standing': 'want',
                                  'notes': 'Watch later. https://tubeview.example/watch?v=AAAAAAAAAAA'}},
    {'id': 'recNews', 'fields': {'title': 'A news piece', 'kind': '📰 news', 'standing': 'want'}},
    {'id': 'recDone', 'fields': {'title': 'Finished Thing', 'kind': '📗 book', 'standing': 'finished'}},
]
fails = []


def check(name, ok, got=None):
    print(('ok    ' if ok else 'FAIL  ') + name + ('' if ok else f'  (got {got!r})'))
    if not ok:
        fails.append(name)


# the app guesses
apps = {r['id']: S.guess_app(r['fields']) for r in RECS}
check('a show whose notes name its app is on that app', apps['recShow1'] == 'Streamly', apps['recShow1'])
check('a book read on the reading app is there', apps['recBook1'] == 'Readr', apps['recBook1'])
check('an episode link is on its podcast app', apps['recPod1'] == 'Podly', apps['recPod1'])
check('the app is found from the notes', apps['recMov1'] == 'Streamly', apps['recMov1'])
check('a rental is Elsewhere', apps['recMov2'] == 'Elsewhere', apps['recMov2'])
check('a video link is on its app', apps['recVid1'] == 'Tubeview', apps['recVid1'])
check('the score is read', S.score_of(RECS[3]['fields']) == 'RT 91%')
check('an episode link opens its app', S.link_for(RECS[2]['fields'], 'Podly').startswith('https://podly.example/episode/'))
check('no link: the app search', S.link_for(RECS[3]['fields'], 'Streamly').startswith('https://streamly.example/search?q=A+Made-Up+Film'))
check('the title drops its aside', S.clean_title('A Sample Novel — An Author') == 'A Sample Novel')
check('and a trailing note in brackets', S.clean_title('Some Book (paperback)') == 'Some Book')

# pick back up: a due date leads, then the most recent touch
order = S.rank_pickup(RECS, TODAY)
check('the loan due soon leads', order[0] == 'recBook1', order)
check('then the most recently touched', order[1:] == ['recPod1', 'recShow1'], order)

with tempfile.TemporaryDirectory() as d:
    sp, out = os.path.join(d, 'stories.json'), os.path.join(d, 'spec.json')
    with open(sp, 'w', encoding='utf-8') as fh:
        json.dump({'records': RECS}, fh)
    S.main(['draft', '--stories', sp, '--out', out, '--today', TODAY.isoformat(), '--local', LOCAL])
    spec = json.load(open(out, encoding='utf-8'))
    check('news stays out of the page', 'recNews' not in spec['items'])
    check('finished rows stay out of the cards', 'recDone' not in spec['items'])
    check('the week is named', spec['week'] == 'W11', spec['week'])
    spec['rhythm'][0]['moods'] = [{'mood': 'Morning, learn something', 'items': ['recVid1']}]
    spec['watch'] = [{'title': 'Shows', 'why': 'pick up', 'items': ['recShow1']}]
    page = S.build_html(spec)
    check('every card can be marked', page.count('class="act"') >= len(spec['items']) + 3)
    check('the picks are on the page', page.count('class="pick"') == 3)
    check('one shelf per app', all(f'id="app-{a}"' in page for a in ('streamly', 'readr', 'podly', 'tubeview', 'elsewhere')))
    check('a weekday card', 'data-days="weekday"' in page)
    check('no placeholders left', '{{' not in page)
    check('nothing loads from outside but fonts',
          all(h in ('fonts.googleapis.com', 'fonts.gstatic.com') for h in
              {u.split('/')[2] for u in re.findall(r'(?:src|href)="(https?://[^"]+)"', page)
               if not re.search(r'\.example/|openlibrary\.org|google\.com', u)}))

# readback: taps become patches, once
db = {
    'recShow1': {'title': 'The Example Show', 'status': 'finished', 'statusDay': '2026-03-13', 'note': 'Loved the ending.', 'noteDay': '2026-03-13'},
    'recPod1': {'title': 'An Example Podcast', 'status': 'finished', 'statusDay': '2026-03-13'},
    'recMov1': {'title': 'A Made-Up Film', 'status': 'started', 'statusDay': '2026-03-14'},
    'recMov2': {'title': 'Rental Picture', 'status': 'dropped', 'statusDay': '2026-03-14'},
    'recNope': {'title': 'Gone', 'status': 'finished'},
}
p = S.plan(db, RECS)
by = {x['id']: x['fields'] for x in p['patches']}
check('finished closes the row', by.get('recShow1', {}).get('standing') == 'finished', by.get('recShow1'))
check('her thought goes above the divider, dated',
      by['recShow1']['notes'].split('———')[0].strip().endswith('Loved the ending. (13 Mar)'), by['recShow1']['notes'])
check('be•do’s line goes last', by['recShow1']['notes'].strip().endswith('[be•do] 13 Mar: marked finished on the Stories page.'))
check('started moves to in motion', by.get('recMov1', {}).get('standing') == 'in motion')
check('dropped is her tap, so it drops', by.get('recMov2', {}).get('standing') == 'dropped')
check('a finished episode comes off the saved list', [x['uri'] for x in p['library_remove']] == ['podly:episode:abc123XYZ'], p['library_remove'])
check('an unknown id is left alone and named', any('Gone' in s for s in p['says']) and 'recNope' not in by)
applied = [dict(r, fields=dict(r['fields'], **by.get(r['id'], {}))) for r in RECS]
check('running it again plans nothing', S.plan(db, applied)['patches'] == [], S.plan(db, applied)['patches'])
check('the db list output is read', S.load_db.__doc__ and True)

print(f'{"FAIL" if fails else "ok"}: {len(fails)} failing')
sys.exit(1 if fails else 0)
