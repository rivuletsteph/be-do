# -*- coding: utf-8 -*-
"""Run the builder against a fixture written backwards from the canon page.

The canon build (Sun 20 Sep 2026) is the target shape. This writes a stream, a
rhythms read, a practices read, a connections read, a typical-time file and a
settings file that SHOULD produce that page's computed sections, runs
look_behind.py over them, pulls DATA back out of the HTML, and compares.

The fixture is not a reconstruction of anyone's actual Sunday. It is the
smallest set of rows that exercises every computation the page does and lands
on the canon's own numbers, so a wrong answer is a wrong builder and not a
wrong day.

Every NUMBER here is the canon page's — the eight domain shares, the tending
and growing split, the four slices' logged and estimated minutes, the chip, the
week. Every NAME and every sentence is an obvious invention, because this file
ships and the user's own rows do not.

Effort weighs minutes over six, so the row minutes below are the canon's shares
times six: heart 29.0 is 174 minutes, air 24.7 is the 83 and 65 of the two work
items on the canon page itself.

    python3 tests/test_canon.py
"""
import json, os, subprocess, sys, tempfile, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BUILDER = os.path.join(SKILL, 'scripts', 'look_behind.py')
ENGINE = os.path.join(SKILL, 'assets', 'look_behind_engine.html')

DAY = dt.date(2026, 9, 20)
OFFSET_H = 0                       # the fixture's clock, matching the settings below
MARK = chr(0x1684E)

SF = dict(title='fldTitle', key='fldKey', details='fldDetails', when='fldWhen',
          end='fldEnd', status='fldStatus', practice='fldPractice',
          person='fldPerson', rhythm='fldRhythm', wellness='fldWellness',
          deliv='fldDeliv', device='fldDevice')
RFD = dict(name='fldRName', type='fldRType', status='fldRStatus',
           emoji='fldREmoji', dest='fldRDest')
PFD = dict(name='fldPName', band='fldPBand', zero='fldPZero', group='fldPGroup')
CFD = dict(name='fldCName', short='fldCShort', circles='fldCCircles')

DONE, MOTION, LOG = '✅ done', '▶️ in motion', '● log'
SELF = '♋ Self'
US = f'{SELF}, Alex, Blair, Casey'
QUEST_GROUP = "Kid's Quest"        # a catalogue group name, not a person


def iso(minute):
    """A local minute-of-day, as the UTC stamp Airtable would have stored."""
    t = dt.datetime.combine(DAY, dt.time()) + dt.timedelta(minutes=minute)
    return (t - dt.timedelta(hours=OFFSET_H)).strftime('%Y-%m-%dT%H:%M:%S.000Z')


_n = [0]


def row(practice, start, end=None, wellness=None, rhythm=None, status=LOG,
        title=None, person=None, details=None, deliv=None, device=None):
    _n[0] += 1
    c = {SF['title']: title or practice, SF['key']: f'k{_n[0]:03d}',
         SF['practice']: practice, SF['status']: status, SF['when']: iso(start)}
    if end is not None:
        c[SF['end']] = iso(end)
    for fld, v in ((SF['wellness'], wellness), (SF['rhythm'], rhythm),
                   (SF['person'], person), (SF['details'], details),
                   (SF['deliv'], deliv), (SF['device'], device)):
        if v:
            c[fld] = v
    return {'id': f'rec{_n[0]:08d}', 'createdTime': iso(start + _n[0] / 100.0),
            'cellValuesByFieldId': c}


STEPS = ['first example step', 'second example step', 'third example step',
         'fourth example step', 'fifth example step', 'sixth example step',
         'seventh example step']

STREAM = [
    # ── the pie's four slices. Sleep is the case that splits in two: it scores
    #    zero on the wheel and its 459 minutes are logged all the same.
    row('🛌 sleep', 0, 459, wellness='🤸‍♀️ body', title='example night'),
    row('📱 capture', 480, 520, title='example capture on a phone'),
    # the screen slice from the DEVICE field, for a row no practice map places
    row('⚡ action', 525, 568, device='💻 laptop', title='example row on a laptop'),
    # and a row that says plainly there was no screen: it must stay out of it
    row('⚡ action', 570, 600, device='🚫 none', title='example row with no screen'),
    row('🍽️ lunch', 660, 743, title='example lunch'),
    row('🚶 walking', 750, 760, title='example walk'),
    row('🚶 long walk', 780, title='example outing'),           # no end → estimated
    row('🍽️ snack', 1200, title='example snack'),              # no end → estimated
    row('📱 logging', 1260, title='example logging'),           # no end → estimated

    # ── the eight, at minutes ÷ 6. Every span stays under four hours so nothing
    #    trips the container rule; body is split for that reason alone.
    row('⚡ action', 470, 590, wellness='🤸‍♀️ body', person=US, title='example body stretch one'),
    row('⚡ action', 600, 720, wellness='🤸‍♀️ body', person=US, title='example body stretch two'),
    row('⚡ action', 730, 846, wellness='🤸‍♀️ body', person=US, title='example body stretch three'),
    row('⚡ action', 850, 976, wellness='💖 spirit', person=US, title='example spirit stretch'),
    row('⚡ action', 1150, 1324, wellness='🩷 heart', person=US, title='example heart stretch'),
    row('📗 book', 980, 1016, wellness='🧠 mind', title='example mind stretch'),
    row('⚡ presence', 0, wellness='🌊 water', rhythm='be•do drive',
        person=f'{SELF}, Quinn', title='example moment with Quinn'),  # a moment, band 1
    row('⚡ tidy', 1020, 1044, wellness='🌎 earth', rhythm='the floor',
        title='example earth row on a rhythm'),
    # a doing row on NO bucket at all — it must land in tending, not nowhere
    row('⚡ tidy', 1050, 1068, wellness='🌎 earth', title='example earth row with no bucket'),
    row('⚡ play', 1070, 1094, wellness='🔥 fire', rhythm='be•do drive',
        title='example fire row on a drive'),
    row('⚡ cooking', 1100, 1142, wellness='🔥 fire', rhythm='the floor',
        title='example fire row on a rhythm'),

    # ── what moved a destination forward. These two ARE the canon's air total.
    row('⚡ action', 570, 653, wellness='💨 air', rhythm='be•do drive', status=DONE,
        title='First example piece of work',
        deliv='https://example.invalid/one'),
    row('⚡ action', 780, 845, wellness='💨 air', rhythm='be•do drive', status=DONE,
        title='Second example piece of work on the same drive',
        deliv='https://example.invalid/two'),
    row('⚡ action', 900, rhythm='D9 — Example drive', status=DONE,
        title='Third example piece of work',
        details='\n'.join('- ' + s for s in STEPS)
                + "\n———\n[be•do] a block that is not the user's words"),

    # ── highlights, and the two intentions set at 8:40a
    row('⭐ highlight', 1140, title='An example highlight'),
    row('✨ glimmer', 1230, title='An example glimmer'),
    row('⚡ intention check', 520, status=DONE, title='First example intention'),
    row('⚡ intention check', 520, status=MOTION,
        title='Second example intention',
        details='left: example step one · example step two · example step three'
                + "\n———\n[be•do] a block that is not the user's",
        deliv='https://example.invalid/one'),

    # ── four rows that must score nothing, each by a different rule
    row('⚡ action', 600, 780, wellness='🔥 fire', status='⬜ intention',
        title='a plan, never lived'),                            # a plan
    row('🛌 sleep', 400, 560, wellness='🤸‍♀️ body', person='Alex',
        title='someone else — sleep'),                           # not the user's row
    row('🌙 dream record', 1330, 1360, wellness='💖 spirit',
        title='a dream'),                                        # named zero
    row('⚔️ quest step', 1360, 1420, wellness='🔥 fire',
        title='a quest step'),                                   # a whole zero group
    row('🗺️ map check', 1150, 1210, wellness='🧠 mind',
        title='a catalogue zero'),                               # the catalogue's own flag

    # ── a fifth person, in a later circle, appearing early. They must still
    #    sort last, because the circle order decides before the clock does.
    row('⚡ action', 100, 130, person=f'{SELF}, Dana', title='example row before dawn'),
]

RHYTHMS = [
    ('be•do drive', '♐ drive', MARK, ['be•do']),
    ('be•do', '♎ destination', MARK, []),
    ('D9 — Example drive', '♐ drive', '🚐', ['an example destination']),
    ('an example destination', '♎ destination', '🏕️', []),
    ('the floor', '♒ rhythm', '', []),
]

# practice → band, catalogue zero, group
PRACTICES = [
    ('⚡ presence', '1', False, None),
    ('⚡ action', '1', False, None),
    ('⚡ tidy', '1', False, None),
    ('⚡ play', '1', False, None),
    ('⚡ cooking', '1', False, None),
    ('📗 book', '1', False, None),
    ('🛌 sleep', '1', False, None),
    ('🌙 dream record', '1', False, None),
    ('⚔️ quest step', '1', False, QUEST_GROUP),
    ('🗺️ map check', '1', True, None),
]

# full name, short name, circles — the FIRST one listed is the grouping circle
CONNECTIONS = [
    ('Quinn Placeholder', 'Quinn', ['Family', 'Friends']),
    ('Alex Placeholder', 'Alex', ['Family']),
    ('Blair Placeholder', 'Blair', ['Family']),
    ('Casey Placeholder', 'Casey', ['Family']),
    ('Dana Placeholder', 'Dana', ['Friends', 'Family']),
]

LOCAL = {
    'self_person': SELF,
    'week_zero_sunday': '2026-09-13', 'week_zero_number': 38,
    'utc_offset_hours': OFFSET_H,
    'noscore_statuses': ['▫️potential', '⬜ intention', '✖️ dropped', '⨂ skipped'],
    'done_statuses': [DONE], 'motion_statuses': [MOTION],
    'zero_practices': ['sleep', 'dream record'],
    'zero_practice_groups': [QUEST_GROUP],
    'zero_when_person_excludes_self': True,
    'zero_note': 'Sleep, plans and other people’s own rows count zero.',
    # six, and a default band of three so a band that came from the catalogue
    # can be told apart from one that fell back
    'effort_minute_divisor': 6, 'default_effort_band': 3,
    'tending_types': ['♒ rhythm'], 'growing_types': ['♐ drive'],
    'highlight_glyphs': {'highlight': '⭐', 'glimmer': '🌟'},
    'intention_practices': ['intention check'],
    'slots_max': 3, 'baseline_days': 0, 'baseline_needed': 14,
    'all_day_minutes': 480,
    'circle_order': ['Family', 'Friends'],
    'device_slice': 'dev', 'device_off': ['🚫 none'],
    'pie': [
        {'k': 'bed',  'e': '\U0001F6CC\U0001F3FB', 'n': 'In bed', 'c': '#27306B',
         'practices': ['sleep'], 'w': 'a fixed phrase, not the row titles'},
        {'k': 'move', 'e': '\U0001F6B6\U0001F3FB‍♀️‍➡️',
         'n': 'Moving', 'c': '#2FA39A', 'practices': ['walking', 'long walk']},
        {'k': 'food', 'e': '\U0001F37D️', 'n': 'Food', 'c': '#E0703E',
         'practices': ['lunch', 'snack']},
        {'k': 'dev',  'e': '\U0001F4F1', 'n': 'On a device', 'c': '#8E3FCF',
         'practices': ['capture', 'logging']},
        {'k': 'else', 'e': '', 'n': 'Everything else', 'c': '#B9B5C4', 'rest': True},
    ],
    'fields': {'stream': SF, 'rhythms': RFD, 'practices': PFD, 'connections': CFD},
}

TYPICAL = {'practices': {'long walk': {'median_min': 130, 'n': 6},
                         'snack': {'median_min': 75, 'n': 9},
                         'logging': {'median_min': 89, 'n': 22}}}

WORDS = {
    'lead': 'An example day, invented for the fixture',
    'story': [
        ['\U0001F4BB', 'An example stretch of work in the morning'],
        ['\U0001F9F3', 'An example stretch of getting ready'],
        ['\U0001F697', 'An example stretch on the road'],
        ['\U0001F319', 'An example stretch in the evening'],
    ],
}

# ── what the canon page says these sections are ──────────────────────────
EXPECT = {
    'chip': f'✔️0920 ☀️ Sun {MARK} W39 \U0001F506 my day',
    'date': 'Sunday, 20 September',
    'title': WORDS['lead'],
    'story': [list(x) for x in WORDS['story']],
    # the canon's four, in the canon's order, plus one that proves the circle
    # order decides before the clock does
    'who': [{'name': 'Quinn', 'when': ''}, {'name': 'Alex', 'when': 'all day'},
            {'name': 'Blair', 'when': 'all day'}, {'name': 'Casey', 'when': 'all day'},
            {'name': 'Dana', 'when': '1:40a–2:10a'}],
    'highlights': [{'glyph': '⭐', 'text': 'An example highlight'},
                   {'glyph': '🌟', 'text': 'An example glimmer'}],
    'photos': [],
    'intentions': [
        {'set': 'First example intention', 'glyph': '✅', 'at': '8:40a'},
        {'set': 'Second example intention', 'glyph': '▶️', 'at': '8:40a',
         'sub': 'left: example step one · example step two · example step three',
         'url': 'https://example.invalid/one'},
    ],
    'slotsMax': 3,
    'balance': {
        'domains': {'heart': 29.0, 'mind': 6.0, 'body': 59.3, 'spirit': 21.0,
                    'water': 1.0, 'air': 24.7, 'earth': 7.0, 'fire': 11.0},
        'tending': 14.0, 'growing': 29.7,
        'note': 'Sleep, plans and other people’s own rows count zero. '
                'Weighted by effort; rows with a real span count their minutes.',
    },
    'pie_minutes': {'bed': (459, 0), 'move': (10, 130), 'food': (83, 75), 'dev': (83, 89)},
    'destinations': [
        {'name': 'be•do', 'glyph': MARK, 'work': [
            {'drive': f'{MARK} be•do drive',
             'text': 'First example piece of work', 'min': 83,
             'url': 'https://example.invalid/one'},
            {'drive': f'{MARK} be•do drive',
             'text': 'Second example piece of work on the same drive', 'min': 65,
             'url': 'https://example.invalid/two'},
        ]},
        {'name': 'an example destination', 'glyph': '🏕️', 'work': [
            {'drive': '🚐 D9 — Example drive',
             'text': 'Third example piece of work', 'min': None, 'url': None,
             'done': STEPS},
        ]},
    ],
    'read': 'w39 · 33/33',
}


def dump(records):
    return {'records': records, 'metadata': {'totalRecordCount': len(records)}}


def ref_records(rows, flds, prefix):
    out = []
    for i, vals in enumerate(rows):
        c = {}
        for fld, v in zip(flds, vals):
            if v is not None and v != '' and v is not False:
                c[fld] = v
        out.append({'id': f'{prefix}{i:05d}', 'createdTime': iso(0),
                    'cellValuesByFieldId': c})
    return out


def main():
    tmp = tempfile.mkdtemp(prefix='lookbehind-')

    def w(name, obj):
        path = os.path.join(tmp, name)
        open(path, 'w', encoding='utf-8').write(json.dumps(obj, ensure_ascii=False))
        return path

    # the stream arrives wrapped, the way a saved tool result does
    p_stream = os.path.join(tmp, 'w39.json')
    open(p_stream, 'w', encoding='utf-8').write(
        json.dumps([{'text': json.dumps(dump(STREAM), ensure_ascii=False)}], ensure_ascii=False))
    p_rhy = w('rhythms.json', dump(ref_records(
        [(n, t, 'active', e, [{'name': d} for d in ds]) for n, t, e, ds in RHYTHMS],
        (RFD['name'], RFD['type'], RFD['status'], RFD['emoji'], RFD['dest']), 'rhy')))
    p_pra = w('practices.json', dump(ref_records(
        PRACTICES, (PFD['name'], PFD['band'], PFD['zero'], PFD['group']), 'pra')))
    p_con = w('connections.json', dump(ref_records(
        [(f, s, [{'name': x} for x in cs]) for f, s, cs in CONNECTIONS],
        (CFD['name'], CFD['short'], CFD['circles']), 'con')))
    p_typ = w('typical_time.json', TYPICAL)
    p_loc = w('look_behind_local.json', LOCAL)
    p_wor = w('words.json', WORDS)
    out = os.path.join(tmp, 'page.html')

    r = subprocess.run([sys.executable, BUILDER, '--day', DAY.isoformat(),
                        '--local', p_loc, '--stream', p_stream, '--rhythms', p_rhy,
                        '--practices', p_pra, '--connections', p_con,
                        '--typical', p_typ, '--words', p_wor,
                        '--template', ENGINE, '--out', out, '--secure', 'secure'],
                       capture_output=True, text=True, encoding='utf-8',
                       env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    print(r.stdout or '', r.stderr or '')
    if r.returncode:
        sys.exit('builder failed')

    html = open(out, encoding='utf-8').read()
    D = json.loads(html.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])

    fails = []

    def check(name, got, want):
        if got != want:
            fails.append(f'{name}\n     got  {got!r}\n     want {want!r}')
        else:
            print(f'  ok   {name}')

    for k in ('chip', 'date', 'title', 'story', 'who', 'highlights', 'photos',
              'intentions', 'slotsMax', 'read'):
        check(k, D[k], EXPECT[k])
    check('balance.domains', D['balance']['domains'], EXPECT['balance']['domains'])
    check('balance.tending', D['balance']['tending'], EXPECT['balance']['tending'])
    check('balance.growing', D['balance']['growing'], EXPECT['balance']['growing'])
    check('balance.note', D['balance']['note'], EXPECT['balance']['note'])
    check('pie minutes',
          {p['k']: (p['logged'], p['est']) for p in D['pie'] if not p.get('rest')},
          EXPECT['pie_minutes'])
    check('pie slices', [p['k'] for p in D['pie']], ['bed', 'move', 'food', 'dev', 'else'])
    check('pie rest slice', [p for p in D['pie'] if p.get('rest')][0]['n'], 'Everything else')
    check('effectiveness.destinations', D['effectiveness']['destinations'],
          EXPECT['destinations'])
    check('effectiveness.secure', D['effectiveness']['secure'], 'secure')
    check('effectiveness.baseline', (D['effectiveness']['baselineDays'],
                                     D['effectiveness']['baselineNeeded']), (0, 14))
    check('effectiveness.usualMin', D['effectiveness']['usualMin'], None)

    # every doing row lands in tending or growing, so the engine is never left
    # with a remainder to draw. This is the balance bar's whole contract.
    b = D['balance']
    do_total = round(sum(b['domains'][k] for k in ('water', 'air', 'earth', 'fire')), 1)
    check('tending + growing == the whole doing side',
          round(b['tending'] + b['growing'], 1), do_total)

    # the day is a day
    check('pie fits in 24 h', sum(p['logged'] + p['est'] for p in D['pie']) <= 1440, True)

    # the engine declares its encoding, or the glyphs come back as mojibake and
    # the follow-through count silently reads zero
    check('engine declares utf-8', '<meta charset="utf-8">' in html, True)

    # the pie's accessible name is filled from DATA at runtime. It used to be
    # carved into the engine as the weekday the canon happened to fall on, so
    # every page since said Sunday.
    check('pie title is not a hardcoded weekday',
          any(f'<title id="pieT">{d}' in html for d in
              ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
               'Saturday', 'Sunday')), False)

    print()
    if fails:
        print(f'{len(fails)} section(s) do not match the canon:')
        for f in fails:
            print('  FAIL ' + f)
        sys.exit(1)
    print(f'all sections match the canon. page: {out}')


if __name__ == '__main__':
    main()
