# -*- coding: utf-8 -*-
"""The 9 Oct amendment's look-behind rules, each against the way it broke on
the 8 Oct page. Every row, name and drive is invented.

  · people come only from rows that happened
  · a person is found by any name they go by
  · cycling and other exercise are Moving, and Moving wins the minute
  · show, movie, video and game are Play
  · a drive row with a span is Doing, device or not
  · nothing stops the build (9 Oct, later the same day: don't stop the process
    for a little detail): >10% of rows unfilled, a row over 12 h, or dayqa not
    yet shown are named in the QA, and a row over 12 h keeps none of its minutes
  · two things at once both count on the wheel

    python3 tests/test_rules_9oct.py
"""
import json, os, subprocess, sys, tempfile, unittest, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BUILDER = os.path.join(SKILL, 'scripts', 'look_behind.py')
ENGINE = os.path.join(SKILL, 'assets', 'look_behind_engine.html')
DAY = dt.date(2026, 10, 8)
SELF = '♋ Self'

SF = dict(title='fldTitle', key='fldKey', details='fldDetails', when='fldWhen', end='fldEnd',
          status='fldStatus', practice='fldPractice', person='fldPerson', rhythm='fldRhythm',
          wellness='fldWellness', deliv='fldDeliv', device='fldDevice', mentioned='fldMentioned')
RFD = dict(name='fldRName', type='fldRType', status='fldRStatus', emoji='fldREmoji', dest='fldRDest')
CFD = dict(name='fldCName', short='fldCShort', circles='fldCCircles', aliases='fldCAliases')
LOG, DONE, INT = '● log', '✅ done', '⬜ intention'


def iso(minute, day=DAY):
    return (dt.datetime.combine(day, dt.time()) + dt.timedelta(minutes=minute)).strftime('%Y-%m-%dT%H:%M:%S.000Z')


class Fixture:
    def __init__(self):
        self.rows = []

    def row(self, practice, start, end=None, title=None, status=LOG, wellness='🤸‍♀️ body',
            device='🚫 none', **kw):
        c = {SF['title']: title or practice, SF['practice']: practice, SF['status']: status,
             SF['when']: start if isinstance(start, str) else iso(start)}
        if end is not None:
            c[SF['end']] = end if isinstance(end, str) else iso(end)
        for k, v in dict(wellness=wellness, device=device, **kw).items():
            if v:
                c[SF[k]] = v
        n = len(self.rows)
        self.rows.append({'id': f'row{n:05d}', 'createdTime': iso(0), 'cellValuesByFieldId': c})

    def whole_day(self):
        """A day that passes the gate: every row whole, dayqa shown."""
        self.row('😴 sleep', 0, 420)
        self.row('🌄 dusk flow close', 1300, title='close',
                 details='———\n[be•do] dayqa shown 2026-10-08 21:40 · 3 proposed')

    def build(self, local_over=None, connections=()):
        tmp = tempfile.mkdtemp(prefix='lb9-')

        def w(name, obj):
            p = os.path.join(tmp, name)
            with open(p, 'w', encoding='utf-8') as fh:
                fh.write(json.dumps(obj, ensure_ascii=False))
            return p
        dump = lambda recs: {'records': recs, 'metadata': {'totalRecordCount': len(recs)}}
        rhy = [{'id': 'rhy1', 'createdTime': iso(0), 'cellValuesByFieldId':
                {RFD['name']: 'Work drive', RFD['type']: '♐ drive', RFD['status']: 'active'}}]
        con = [{'id': f'con{i}', 'createdTime': iso(0), 'cellValuesByFieldId':
                {k: v for k, v in {CFD['name']: f, CFD['short']: s, CFD['aliases']: al,
                                   CFD['circles']: [{'name': c}]}.items() if v}}
               for i, (f, s, al, c) in enumerate(connections)]
        local = {
            'self_person': SELF, 'week_zero_sunday': '2026-10-04', 'week_zero_number': 41,
            'utc_offset_hours': 0,
            'noscore_statuses': ['▫️potential', INT, '✖️ dropped', '⨂ skipped'],
            'done_statuses': [DONE, '◉ done'], 'motion_statuses': ['▶️ in motion'],
            'circle_order': ['Family', 'Work'],
            'device_slice': 'dev', 'device_off': ['🚫 none'],
            'pie': [
                {'k': 'bed', 'n': 'In bed', 'c': '#27306B', 'practices': ['sleep']},
                {'k': 'move', 'n': 'Moving', 'c': '#2FA39A', 'practices': ['walking']},
                {'k': 'food', 'n': 'Food', 'c': '#E0703E', 'practices': ['lunch']},
                {'k': 'dev', 'n': 'On a device', 'c': '#8E3FCF', 'practices': ['capture', 'show']},
                {'k': 'else', 'n': 'Everything else', 'c': '#B9B5C4', 'rest': True},
            ],
            'fields': {'stream': SF, 'rhythms': RFD, 'connections': CFD},
        }
        local.update(local_over or {})
        args = [sys.executable, BUILDER, '--day', DAY.isoformat(), '--local', w('local.json', local),
                '--stream', w('w41.json', dump(self.rows)), '--rhythms', w('rhythms.json', dump(rhy)),
                '--connections', w('connections.json', dump(con)),
                '--words', w('words.json', {'lead': 'an invented day', 'story': [['🌱', 'invented']]}),
                '--template', ENGINE, '--out', os.path.join(tmp, 'page.html')]
        r = subprocess.run(args, capture_output=True, text=True, encoding='utf-8',
                           env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        if r.returncode:
            return r, None
        with open(os.path.join(tmp, 'page.html'), encoding='utf-8') as fh:
            html = fh.read()
        return r, json.loads(html.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0])


def pie(D):
    return {p['k']: p['logged'] for p in D['pie']}


class People(unittest.TestCase):
    def test_a_plan_puts_nobody_in_the_day(self):
        f = Fixture(); f.whole_day()
        f.row('🗣️ face-to-face', 600, 660, person=f'{SELF}, Robin', wellness='🩷 heart')
        f.row('⚡ action', 700, title='dinner with Sam and Lee on Friday', status=INT,
              person='Sam, Lee', wellness='🩷 heart', device='')
        r, D = f.build()
        self.assertIsNotNone(D, r.stderr)
        self.assertEqual([p['name'] for p in D['who']], ['Robin'])

    def test_any_alias_finds_the_circle(self):
        f = Fixture(); f.whole_day()
        f.row('🗣️ face-to-face', 600, 660, person=f'{SELF}, Marigold, Pat Example, Coz',
              wellness='🩷 heart')
        r, D = f.build(connections=[
            ('Marigold Example', 'mum', None, 'Family'),        # the stream writes the first name
            ('Pat', 'pop', None, 'Family'),                     # the stream writes first and last
            ('Corisande Example', 'Cori', 'Coz, C', 'Work'),    # a third form, from the aliases
        ])
        self.assertIsNotNone(D, r.stderr)
        self.assertEqual({p['name']: p['circle'] for p in D['who']},
                         {'Marigold': 'Family', 'Pat Example': 'Family', 'Coz': 'Work'})

    def test_one_person_however_written_and_a_mention_hung_once(self):
        # 10 Oct 2026: "<her> · <a colleague>" drew as one person, a name with its glyph
        # and without drew as two, and the person remembered at a gathering hung off everyone
        f = Fixture(); f.whole_day()
        f.row('🗣️ face-to-face', 600, 660, person=f'{SELF} · Robin Example', wellness='🩷 heart')
        f.row('⚡ action', 700, 720, title='a game with Kit', person='🐢Kit', status=DONE,
              wellness='🩷 heart')
        f.row('⚡ action', 730, 750, title='more of the game', person='Kit', status=DONE,
              wellness='🩷 heart')
        f.row('🗣️ face-to-face', 1100, 1200, person='🐢Kit, Ash, Bo', mentioned='Remembered One',
              wellness='🩷 heart')
        r, D = f.build()
        self.assertIsNotNone(D, r.stderr)
        who = {p['name']: p for p in D['who']}
        self.assertEqual(sorted(who), ['Ash', 'Bo', 'Robin Example', '🐢Kit'])
        self.assertEqual(who['🐢Kit']['n'], 3)
        self.assertEqual([p.get('via') for p in D['who'] if p.get('via')], [['Remembered One']])


class Pie(unittest.TestCase):
    def test_cycling_is_moving_and_moving_wins_the_minute(self):
        f = Fixture(); f.whole_day()
        f.row('🍽️ lunch', 720, 780)
        f.row('🚴‍♀️ cycling', 750, 810)                    # half over lunch
        f.row('💪 strength training', 900, 930)
        # food listed before Moving in the settings, as an older file might have it
        food_first = [{'k': 'food', 'n': 'Food', 'c': '#E0703E', 'practices': ['lunch']},
                      {'k': 'move', 'n': 'Moving', 'c': '#2FA39A', 'practices': ['walking']},
                      {'k': 'dev', 'n': 'On a device', 'c': '#8E3FCF', 'practices': []},
                      {'k': 'else', 'n': 'Everything else', 'c': '#B9B5C4', 'rest': True}]
        r, D = f.build({'pie': food_first})
        self.assertIsNotNone(D, r.stderr)
        self.assertEqual(pie(D)['move'], 60 + 30)
        self.assertEqual(pie(D)['food'], 30)
        self.assertEqual([p['k'] for p in D['pie']][:2], ['food', 'move'])   # drawn in her order

    def test_shows_are_play_never_a_drive_slice(self):
        f = Fixture(); f.whole_day()
        f.row('📺 show', 1200, 1260, wellness='🔥 fire', device='📺 tv')
        f.row('🎮 game', 1260, 1290, wellness='🔥 fire', device='📱 phone')
        r, D = f.build()
        self.assertIsNotNone(D, r.stderr)
        self.assertEqual(pie(D)['play'], 90)
        self.assertEqual(pie(D)['dev'], 0)
        self.assertEqual([p['k'] for p in D['pie']][-3:], ['play', 'log', 'else'])

    def test_drive_work_in_person_is_doing(self):
        f = Fixture(); f.whole_day()
        f.row('⚡ action', 540, 660, title='a meeting in person', rhythm='Work drive',
              wellness='💨 air', device='🚫 none', status=DONE)
        r, D = f.build()
        self.assertIsNotNone(D, r.stderr)
        self.assertEqual(pie(D)['dev'], 120)
        self.assertEqual([p['n'] for p in D['pie'] if p['k'] == 'dev'], ['Doing · work and drives'])


class Gate(unittest.TestCase):
    def test_a_whole_day_builds(self):
        f = Fixture(); f.whole_day()
        r, D = f.build()
        self.assertEqual(r.returncode, 0, r.stderr)

    def qa(self, r):
        return ' '.join(json.loads(r.stdout[r.stdout.index('{'):])['qa'].get('not_yet_whole', []))

    def test_more_than_a_tenth_unfilled_builds_and_is_named(self):
        f = Fixture(); f.whole_day()
        for i in range(8):
            f.row('📝 log', 500 + i, wellness='🧠 mind', device='📱 phone')
        f.row('📝 log', 520, device='')                            # 1 of 11: under the line
        r, _ = f.build()
        self.assertNotIn('lack device or wellness', self.qa(r))
        f.row('📝 log', 530, wellness='')                          # 2 of 12: 17%
        r, D = f.build()
        self.assertIsNotNone(D, r.stderr)
        self.assertIn('lack device or wellness', self.qa(r))

    def test_a_row_over_twelve_hours_keeps_none_of_its_minutes(self):
        f = Fixture(); f.whole_day()
        f.row('⚡ action', iso(0, DAY - dt.timedelta(days=12)), 600, title='closed from its first date',
              rhythm='Work drive', wellness='💨 air', status=DONE)
        r, D = f.build()
        self.assertIsNotNone(D, r.stderr)
        self.assertIn('over 12 h', self.qa(r))
        self.assertEqual(pie(D)['dev'], 0)
        self.assertEqual(D['balance']['domains']['air'], 1.0)      # its band, not 600 minutes

    def test_the_page_builds_before_dayqa_and_says_so(self):
        f = Fixture()
        f.row('😴 sleep', 0, 420)
        r, D = f.build()
        self.assertIsNotNone(D, r.stderr)
        self.assertIn('dayqa has not been shown', self.qa(r))


class Wheel(unittest.TestCase):
    def test_walking_and_journaling_both_count(self):
        f = Fixture(); f.whole_day()
        f.row('🚶‍♀️ walking', 600, 660, wellness='🤸‍♀️ body')
        _, alone = f.build()
        f.row('📒 journal', 600, 660, wellness='🧠 mind')
        r, both = f.build()
        self.assertIsNotNone(both, r.stderr)
        self.assertEqual(both['balance']['domains']['body'], alone['balance']['domains']['body'])  # the walk keeps all 60
        self.assertEqual(both['balance']['domains']['mind'], 10.0)                                  # and the journal its 60


if __name__ == '__main__':
    unittest.main()
