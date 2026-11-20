# -*- coding: utf-8 -*-
"""Drive the my week builder over a small fixture and check what it writes.

Every name, row and event below is an obvious invention.

What it pins:
  · the page is the week's seven days, Sunday to Saturday, from the week number
  · the week's word sits in its own slot, first, and shows candidates only when empty
  · possible paths come out of the day page's own pareto(), never as a queue
  · a day already lived carries its cards; a day still ahead carries its events
  · the two weeks after are there, and only the two
  · base flow stops at today, so the card's "this morning" is a morning that happened
  · every time on the page ends in a lowercase a or p

    python3 tests/test_week.py
"""
import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BEDO = os.path.dirname(os.path.dirname(SKILL))
WEEK_PY = os.path.join(SKILL, 'scripts', 'week.py')
ENGINE = os.path.join(SKILL, 'assets', 'week_engine.html')
DAY_ENGINE = os.path.join(BEDO, 'skills', 'bedo-day-ahead', 'assets', 'flow_engine.html')

F = {'title': 'fldTITLE', 'key': 'fldKEY', 'details': 'fldDET', 'when': 'fldWHEN', 'end': 'fldEND',
     'target': 'fldTGT', 'status': 'fldST', 'practice': 'fldPR', 'person': 'fldPER',
     'rhythm': 'fldRH', 'waiting': 'fldWAIT', 'queue': 'fldQ', 'event': 'fldEV',
     'deliverable': 'fldDEL', 'mentioned': 'fldMEN', 'quickie': 'fldQK', 'wellness': 'fldWEL'}
RF = {'name': 'fldRNAME', 'code': 'fldRCODE', 'type': 'fldRTYPE', 'status': 'fldRST',
      'target': 'fldRTGT', 'parent': 'fldRPAR', 'emoji': 'fldREMO', 'dest': 'fldRDEST',
      'goal': 'fldRGOAL', 'feeds': 'fldRFEED'}

LOCAL = {
    'self_person': 'Rowan', 'self_calendar': 'you', 'other_calendars': ['Wren'],
    'calendar_summaries': {'you': 'my events', 'Wren': "Wren's events"},
    'child_calendar': 'Wren', 'readonly_calendars': [], 'calendar_people': {}, 'event_aliases': {},
    'work_parents': ['Work'], 'tending': ['Home'], 'time_goals': {}, 'time_limits': {},
    'sunday_morning': 'reflection', 'sunday_morning_until': '12:00', 'saturday_lead': '',
    'full_day_hours': 4, 'step_day_hours': 8, 'full_day_events': 4, 'travel_buffer_min': 45,
    'stay_hours': 12, 'prep_lead_days': 1, 'own_practices': [], 'weighing_phrases': ['weighing on me'],
    'hide_drives': [], 'hide_keep': [], 'week_word_title': r"^the week's word: (.+)$",
    'week_zero_sunday': '2026-05-03', 'week_zero_number': 19, 'map_end': '2027-06-01',
    'utc_offset_hours': -6, 'time_zone': 'America/Chicago',
    'rhythms_base': 'appR', 'rhythms_table': 'tblR', 'practices_base': 'appP', 'practices_table': 'tblP',
    'artifact_url': '', 'drive_name_example': 'D1 — Example', 'note_records': {},
    'fields': {'stream': F, 'rhythms': RF, 'practices': {'name': 'fldPN', 'active': 'fldPA', 'cadence': 'fldPC'}},
    'horizon': [], 'horizon_drive_days': 14,
}

SUN = dt.date(2026, 11, 8)          # the Sunday that opens W46
TODAY = dt.date(2026, 11, 9)        # built on the Monday


def utc(day, hh, mm=0):
    """a local wall clock, written back as the UTC the base stores"""
    return (dt.datetime.combine(day, dt.time(hh, mm)) + dt.timedelta(hours=6)).strftime(
        '%Y-%m-%dT%H:%M:00.000Z')


def row(rid, title, **kw):
    c = {F['title']: title, F['status']: kw.pop('status', '● log')}
    for k, v in kw.items():
        if v is not None:
            c[F[k]] = v
    return {'id': rid, 'createdTime': utc(SUN, 6), 'cellValuesByFieldId': c}


def rh(rid, name, code, typ, **kw):
    c = {RF['name']: name, RF['code']: code, RF['type']: typ, RF['status']: 'active'}
    c.update({RF[k]: v for k, v in kw.items()})
    return {'id': rid, 'createdTime': utc(SUN, 6), 'cellValuesByFieldId': c}


STREAM = [
    row('rec01', "the week's word: Flowing", status='● log', when=utc(SUN, 7),
        details='Flowing is what I want this week.'),
    row('rec02', 'morning oura — readiness 80', practice='morning oura', when=utc(SUN, 6),
        end=utc(SUN, 6, 20), wellness='🌿 body'),
    row('rec03', 'morning oura — readiness 74', practice='morning oura', when=utc(TODAY, 6),
        end=utc(TODAY, 6, 20), wellness='🌿 body'),
    row('rec04', 'a long walk by the river', practice='walk', when=utc(SUN, 9),
        end=utc(SUN, 10, 30), wellness='🌿 body', rhythm='Home'),
    row('rec05', 'wrote up the gauge notes', practice='action', when=utc(TODAY, 13),
        end=utc(TODAY, 15), wellness='🜁 air', rhythm='Gauge notes'),
    row('rec06', '⚡ send Marlowe the gauge table', status='⬜ intention', rhythm='Gauge notes',
        target=utc(dt.date(2026, 11, 4), 9), mentioned='Marlowe',
        details='Next: attach the table to the thread and send it.'),
    row('rec07', '⚡ book the van service', status='▶️ in motion', rhythm='Home',
        target=utc(dt.date(2026, 11, 12), 9)),
    row('rec08', '⚡ the loft shelves, weighing on me', status='⬜ intention', rhythm='Home',
        target=utc(dt.date(2026, 11, 13), 9), details='weighing on me since the summer.'),
    # A PLAN NAMES ITS PEOPLE IN `mentioned`, NEVER IN `person`. This row is the one the first
    # W46 page missed: due tomorrow, two colleagues waiting, and it scored nothing at all.
    row('rec09', '⚡ the shelter drawings, in front of Wren and Marlowe', status='⬜ intention',
        rhythm='Shelter plan', target=utc(dt.date(2026, 11, 10), 17), mentioned='Wren, Marlowe',
        details='Next: send the drawings to the group for pre-approval.'),
    row('rec10', '⚡ price the roof panels', status='▶️ in motion', rhythm='Shelter plan',
        target=utc(dt.date(2026, 11, 12), 9)),
    # a maybe is not an action, however loudly it is worded
    row('rec11', '⚡ a new chair for the loft, if the old one still bothers me',
        status='▫️potential', rhythm='Shelter plan'),
    # a drive with nothing dated anywhere: people waiting is a nag, not a deadline
    row('rec12', '⚡ ask Marlowe about the old survey', status='▶️ in motion',
        rhythm='Sundries', mentioned='Marlowe'),
    row('rec13', '⚡ chase the second survey', status='▶️ in motion', rhythm='Sundries',
        mentioned='Wren'),
    # `person` is who was WITH her, and it is filled with the household by default: it must never
    # read as somebody waiting on her
    row('rec14', '⚡ sort the shelter photos', status='▶️ in motion', rhythm='Shelter plan',
        person='Rowan, Wren'),
]
RHYTHMS = [
    rh('recR1', 'Home', 'R1', '♒ rhythm', emoji='🏠', goal='A house that works. Nothing fancy.'),
    rh('recR2', 'Work', 'R2', '♒ rhythm', emoji='🏢', goal='Water that people can drink.'),
    rh('recD1', 'Gauge notes', 'D1', '♐ drive', parent='Work', goal='Get the gauge notes out.'),
    rh('recD2', 'Shelter plan', 'D2', '♐ drive', parent='Home', emoji='🏕️',
       target='2026-11-30', goal='A shelter the dogs can winter in.'),
    rh('recD3', 'Sundries', 'D3', '♐ drive', parent='Work', goal='Odds and ends.'),
]


def cal():
    """cal.json in the shape bedo_cal.py --build writes it: one block per calendar, each event
    as Google returned it."""
    def e(eid, summary, start, end, where='', color=None):
        return {'id': eid, 'summary': summary, 'status': 'confirmed',
                'start': {'dateTime': start, 'timeZone': 'America/Chicago'},
                'end': {'dateTime': end, 'timeZone': 'America/Chicago'},
                'htmlLink': f'https://example.test/{eid}', 'location': where,
                'recurring': False, 'meet': False, **({'colorId': color} if color else {})}
    return {'calendars': [
        {'who': 'you', 'events': [
            e('e1', '⬜ the choir rehearsal', f'{SUN}T19:00:00-06:00', f'{SUN}T20:30:00-06:00', 'the hall'),
            e('e2', '⬜ the water meeting', '2026-11-10T10:00:00-06:00',
              '2026-11-10T11:00:00-06:00', 'my office', '3'),
            e('e4', '⬜ the county fair', '2026-11-21T09:00:00-06:00',
              '2026-11-21T12:00:00-06:00', 'the fairground'),
            # called off: its own title opens with the mark
            e('e5', '✖️ the budget meeting — called off', '2026-11-11T10:00:00-06:00',
              '2026-11-11T11:00:00-06:00', 'my office'),
            # one morning on two calendars: hers, and the child's own entry for the same thing
            e('e6', '⬜ helping at the orchard school', '2026-11-13T10:00:00-06:00',
              '2026-11-13T13:00:00-06:00', 'the orchard'),
        ]},
        {'who': 'Wren', 'events': [
            e('e3', '⬜ swimming', '2026-11-12T16:00:00-06:00', '2026-11-12T17:00:00-06:00', 'the pool'),
            e('e7', '⬜ orchard school — Rowan is helping', '2026-11-13T10:00:00-06:00',
              '2026-11-13T14:00:00-06:00', 'the orchard'),
        ]},
    ], 'read': {'window': 'Sun 8 Nov – Sat 28 Nov', 'you': 3, 'Wren': 1}}


class TheWeekPage(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.dir = tempfile.mkdtemp(prefix='bedo-week-')
        d = cls.dir
        w = lambda n, o: json.dump(o, open(os.path.join(d, n), 'w', encoding='utf-8'), ensure_ascii=False)
        os.makedirs(os.path.join(d, 'data'), exist_ok=True)
        w('day_ahead_local.json', LOCAL)
        json.dump({'records': STREAM, 'metadata': {'totalRecordCount': len(STREAM)}},
                  open(os.path.join(d, 'data', 'w46.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump({'records': RHYTHMS, 'metadata': {'totalRecordCount': len(RHYTHMS)}},
                  open(os.path.join(d, 'data', 'rhythms.json'), 'w', encoding='utf-8'), ensure_ascii=False)
        # the calendar as bedo_cal.py --build writes it
        w('cal.json', cal())
        # a day-ahead page is only read for its palette
        pal = open(DAY_ENGINE, encoding='utf-8').read()
        open(os.path.join(d, 'fake-day-ahead.html'), 'w', encoding='utf-8').write(
            '<style>:root{--c-moss:#6b705c;--ground:#fff;--ink:#222;--card:#fff;--rule:#ddd;'
            '--accent:#a33;--muted:#666;--faint:#999;--card2:#eee;--dest:#2a7;--dest-soft:#def;'
            "--sans:sans-serif;--serif:serif;--mono:monospace}\n"
            'html[data-bedo="night"]{--ground:#111;--ink:#eee;--card:#1a1a1a;--rule:#333;'
            '--accent:#e88;--muted:#aaa;--faint:#777;--card2:#222}</style>' + pal[:0])
        cls.out = os.path.join(d, 'week.html')
        r = subprocess.run([sys.executable, WEEK_PY,
                            '--week', '46', '--today', TODAY.isoformat(), '--now', '19:10',
                            '--local', os.path.join(d, 'day_ahead_local.json'),
                            '--stream', os.path.join(d, 'data', 'w46.json'),
                            '--rhythms', os.path.join(d, 'data', 'rhythms.json'),
                            '--calendar', os.path.join(d, 'cal.json'),
                            '--template', ENGINE,
                            '--day-ahead', os.path.join(d, 'fake-day-ahead.html'),
                            '--word', 'Flowing', '--focus', 'moving while journaling',
                            '--push', 'D3::my word this morning',
                            '--out', cls.out],
                           capture_output=True, text=True, encoding='utf-8')
        if r.returncode:
            raise AssertionError(f'the builder failed:\n{r.stdout}\n{r.stderr}')
        cls.said = json.loads(r.stdout.strip().split('\n')[-1])
        cls.page = open(cls.out, encoding='utf-8').read()
        cls.plan = json.load(open(cls.out + '.plan.json', encoding='utf-8'))

    def test_it_is_the_week_sunday_to_saturday(self):
        self.assertEqual(self.plan['week'], 46)
        self.assertEqual(self.plan['start'], '2026-11-08')
        self.assertEqual(self.plan['end'], '2026-11-14')
        self.assertEqual([d['day3'] for d in self.plan['days']],
                         ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'])

    def test_the_word_has_its_own_slot_and_no_candidates_once_it_is_set(self):
        self.assertEqual(self.plan['wordslot']['word'], 'Flowing')
        self.assertEqual(self.plan['wordslot']['candidates'], [])

    def test_an_empty_slot_offers_candidates_carry_over_first(self):
        import importlib
        sys.path.insert(0, os.path.join(SKILL, 'scripts'))
        week = importlib.import_module('week')
        week.DA.install_local(LOCAL)
        rows, _, _, _ = week.DA.load_stream([os.path.join(self.dir, 'data', 'w46.json')])
        # ask for a week the word row does not fall in: the row becomes the carry-over
        slot = week.word_slot(rows, LOCAL, dt.date(2026, 11, 15), dt.date(2026, 11, 21))
        self.assertIsNone(slot['word'])
        self.assertTrue(slot['candidates'])
        self.assertEqual(slot['candidates'][0]['word'], 'Flowing')
        self.assertIn('carry-over', slot['candidates'][0]['why'])

    def test_her_focus_practice_is_counted_never_scored(self):
        f = self.plan['focus']
        self.assertEqual(f['name'], 'moving while journaling')
        self.assertEqual(f['of'], 7)
        self.assertEqual(len(f['days']), 7)
        self.assertNotIn('score', json.dumps(f))

    # ---------------------------------------------------------------- what to push this week
    # Her words on the first W46 page, 9 Nov 2026: that algorithm or whatever that's trying to pick
    # the top three needs some work. Each test below is one of the things she said was wrong.

    def _lane(self, code):
        return next((x for x in self.plan['push']['lanes'] if x['code'] == code), None)

    def test_a_drive_leads_the_week_with_its_few_actions_under_it(self):
        lanes = self.plan['push']['lanes']
        self.assertTrue(lanes, 'the week pushes nothing at all')
        self.assertTrue(all(x['code'] and x['n'] for x in lanes))
        self.assertTrue(all(1 <= len(x['acts']) <= 3 for x in lanes))
        self.assertIn('what I could push this week', self.page)
        self.assertIn('Paths, not a queue', self.page)

    def test_a_plan_names_its_people_in_mentioned_and_is_seen(self):
        # the exact miss on the first W46 page: due tomorrow, two colleagues waiting, scored nothing
        ln = self._lane('D2')
        self.assertIsNotNone(ln, 'the drive with a date tomorrow did not lead the week')
        a = next(x for x in ln['acts'] if 'shelter drawings' in x['t'])
        self.assertEqual(a['who'], ['Wren', 'Marlowe'])
        self.assertIn('due tomorrow', a['why'])
        self.assertEqual(a['step'], 'send the drawings to the group for pre-approval')

    def test_a_row_on_a_rhythm_never_leads_the_week(self):
        # the credit-card chore she called annoying. A rhythm is the country, a drive is a
        # stretch of trail — only a drive is something a week can push.
        ts = [a['t'] for ln in self.plan['push']['lanes'] for a in ln['acts']]
        self.assertNotIn('book the van service', ts)
        self.assertNotIn('the loft shelves, weighing on me', ts)
        self.assertGreater(self.plan['push']['left']['rhythm'], 0)

    def test_a_maybe_is_not_an_action(self):
        # her words: my side isn't really bothering me that much anymore
        ts = [a['t'] for ln in self.plan['push']['lanes'] for a in ln['acts']]
        self.assertFalse([t for t in ts if 'new chair for the loft' in t])
        self.assertGreater(self.plan['push']['left']['maybe'], 0)

    def test_a_drive_with_no_date_anywhere_does_not_lead_on_its_own(self):
        # her words: there is no econ team meeting, that was last week. People waiting with nothing
        # dated is a nag, not a deadline — D3 only gets in because she pinned it herself.
        d3 = self._lane('D3')
        self.assertIsNotNone(d3, 'her own pin was dropped')
        self.assertEqual(d3['pin'], 'my word this morning')
        self.assertEqual(self.plan['push']['lanes'][0]['code'], 'D3', 'her pin is not first')
        self.assertEqual(d3['score'], 0, 'a drive with no date anywhere scored on its own')

    def test_the_household_on_person_is_not_somebody_waiting(self):
        # `person` is who was with her, filled with the household by default. Reading it as
        # waiting put a journal note about her own family near the top of the week.
        rs = [a for ln in self.plan['push']['lanes'] for a in ln['acts']]
        a = next((x for x in rs if 'shelter photos' in x['t']), None)
        if a:
            self.assertEqual(a['who'], [])
        self.assertFalse([w for x in rs for w in x['who'] if w in ('Rowan', 'Wren')
                          and 'shelter photos' in x['t']])

    def test_it_says_what_it_left_out_and_why(self):
        left = self.plan['push']['left']
        self.assertEqual(set(left), {'event', 'maybe', 'rhythm', 'nopull'})
        self.assertIn('left out of the', self.page)

    def test_the_rest_of_what_has_a_date_this_week_does_not_lead(self):
        self.assertFalse([p for p in self.plan['paths'] if p['lead']])
        self.assertIn('the rest of what has a date this week', self.page)

    def test_a_pick_carries_its_one_next_step(self):
        a = next(a for ln in self.plan['push']['lanes'] for a in ln['acts']
                 if a['t'] == 'send Marlowe the gauge table')
        self.assertEqual(a['step'], 'attach the table to the thread and send it')
        self.assertEqual(a['who'], ['Marlowe'])

    def test_the_page_opens_quiet_and_says_what_else_is_there(self):
        # her words, 12 Nov 2026: it's over-freaking-whelming … when it just throws everything at
        # me, it stresses me out. The word, her focus, the push and the question are the page;
        # everything else is built, named and one tap away.
        self.assertIn("let QUIET = true", self.page)
        self.assertIn('also here, when you want it', self.page)
        self.assertIn('show me everything', self.page)
        held = re.search(r"const HUSH = \[(.+?)\]", self.page).group(1)
        for id_ in ('week', 'spent', 'wheel', 'ahead', 'rhythms', 'overdue'):
            self.assertIn(f"'{id_}'", held)
        for id_ in ('word', 'focus', 'push', 'pareto'):
            self.assertNotIn(f"'{id_}'", held)

    def test_the_two_weeks_after_are_an_agenda_of_the_pages_own_cards(self):
        # her words: it needs to look like the schedule in my calendar … I can see the emojis and
        # the open squares and what I've committed to
        days = [d for w in self.plan['ahead'] for d in w['days']]
        self.assertTrue(days)
        self.assertTrue(all('cards' in d for d in days))
        self.assertTrue(any(d['cards'] for d in days), 'no card in the two weeks after')
        self.assertIn('dayBody(d, d.cards', self.page)

    # ---- the calendar, by weight (her words, 12 Nov 2026: drop only what is not happening, and
    # fix the crowding with weight: mine first and full, theirs quieter but plainly there)
    def _events(self, iso):
        day = next(d for d in self.plan['days'] if d['d'] == iso)
        return day, [x for x in day['cards'] if x['k'] == 'event']

    def test_an_event_marked_off_is_left_off_and_said(self):
        day, evs = self._events('2026-11-11')
        self.assertFalse([x for x in evs if 'budget' in x['t']])
        self.assertIn('off', [l['why'] for l in day['left'] if 'budget' in l['t']])
        self.assertEqual(self.plan['read']['off'], 1)

    def test_one_thing_on_two_calendars_is_shown_once_as_hers(self):
        day, evs = self._events('2026-11-13')
        self.assertEqual([x['t'] for x in evs], ['helping at the orchard school'])
        self.assertTrue(evs[0]['mine'])
        self.assertEqual([(o['who'], o['b']) for o in evs[0]['also']], [('Wren', '14:00')])
        self.assertIn('twice', [l['why'] for l in day['left']])
        self.assertNotIn('clash', day['tags'], 'her helping at his school is not a clash')

    def test_a_family_event_stays_and_is_marked_theirs(self):
        # the answer is not to take things out: she wants to see them, to prepare for them
        day, evs = self._events('2026-11-12')
        swim = [x for x in evs if x['t'] == 'swimming']
        self.assertEqual(len(swim), 1)
        self.assertFalse(swim[0]['mine'])
        self.assertEqual(swim[0]['who'], 'Wren')
        # drawn as a quiet line, never with a check or a strike
        self.assertIn('function famLine(', self.page)

    def test_a_day_gone_folds_by_the_my_day_pages_own_highlights_rule(self):
        # the rule is read out of the my day engine at the build, not copied into this one
        engine = open(ENGINE, encoding='utf-8').read()
        self.assertIn('/*DAYSIX*/', engine)
        self.assertNotIn('function sixOf(', engine)
        self.assertNotIn('/*DAYSIX*/', self.page)
        self.assertIn('function sixOf(', self.page)
        self.assertIn('highlights(day, cards)', self.page)

    def test_every_script_on_the_built_page_parses(self):
        import shutil
        node = shutil.which('node')
        if not node:
            self.skipTest('no node here')
        for i, js in enumerate(re.findall(r'<script>(.*?)</script>', self.page, flags=re.S)):
            f = os.path.join(self.dir, f'block{i}.js')
            open(f, 'w', encoding='utf-8').write(js)
            r = subprocess.run([node, '--check', f], capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(r.returncode, 0, r.stderr[:600])

    def test_a_day_that_has_not_happened_has_nothing_struck_through(self):
        # a recurring event whose series row has been closed comes back done on every repeat
        self.assertIn("x.done && day && (day.past || day.today)", self.page)

    def test_the_colours_are_lifted_on_night_sight_never_repainted(self):
        # her words: I can't see the colors very well because I've got it kind of on night sight
        engine = open(ENGINE, encoding='utf-8').read()
        self.assertIn('const kc =', engine)
        self.assertIn("dataset.bedo !== 'night'", engine)
        # every chart colour the page draws goes through kc(); none reads the palette raw
        self.assertNotIn('||PICK_DEFAULT.admin)[0]', engine)

    def test_a_day_lived_carries_its_cards_and_a_day_ahead_its_events(self):
        sun = self.plan['days'][0]
        self.assertTrue(any('walk' in c['t'] for c in sun['cards']))
        self.assertTrue(any(c['k'] == 'event' and 'choir' in c['t'] for c in sun['cards']))
        thu = self.plan['days'][4]
        self.assertTrue(any('swimming' in c['t'] for c in thu['cards']))

    def test_the_two_weeks_after_are_there_and_only_two(self):
        self.assertEqual([w['label'] for w in self.plan['ahead']], ['W47', 'W48'])
        fair = json.dumps(self.plan['ahead'], ensure_ascii=False)
        self.assertIn('county fair', fair)

    def test_base_flow_stops_at_today(self):
        days = [w['day'] for w in self.plan['baseflow']['week']]
        self.assertEqual(days, ['2026-11-08', '2026-11-09'])
        self.assertEqual(self.plan['baseflow']['week'][0]['body'], 80)
        self.assertEqual(self.plan['baseflow']['week'][1]['body'], 74)

    def test_past_its_date_holds_the_late_row(self):
        self.assertTrue(any(o['t'] == 'send Marlowe the gauge table' for o in self.plan['overdue']))
        self.assertEqual(next(o for o in self.plan['overdue']
                              if o['t'] == 'send Marlowe the gauge table')['days'], 5)

    def test_the_rhythms_carry_their_drives(self):
        work = next(r for r in self.plan['rhythms'] if r['n'] == 'Work')
        self.assertIn('Gauge notes', [d['n'] for d in work['drives']])

    def test_the_pareto_question_reads_the_push(self):
        pick = self.plan['pareto']['pick']
        self.assertTrue(pick)
        self.assertIn(pick, [a['t'] for ln in self.plan['push']['lanes'] for a in ln['acts']])

    def test_the_pareto_question_is_last(self):
        self.assertLess(self.page.index('possible paths'), self.page.rindex('id="pareto"'))
        self.assertIn('would make the rest of', self.plan['pareto']['q'])

    def test_every_time_ends_in_a_or_p(self):
        """Her amendment of 9 Nov 2026 on the clock. The page writes its times through clock.js, so what
        this checks is that no builder-written time slipped onto the page in another shape."""
        bad = re.findall(r'\b\d{1,2}:\d\d\s?[AP]\.?M\.?\b', self.page)
        self.assertEqual(bad, [], f'times that do not end in a or p: {bad[:5]}')
        self.assertIn('const wt=', self.page)

    def test_the_page_carries_the_shared_parts_not_a_copy_of_the_day_stylesheet(self):
        for bit in ('.wordbox', '.dcol'):                      # the week's own
            self.assertIn(bit, self.page)
        for bit in ('.rb{', '.why span{', '.rv h2{'):           # lifted in from flow-parts
            self.assertIn(bit, self.page)
        self.assertNotIn('/*SHELLCSS*/', self.page)
        self.assertNotIn('/*DATA*/', self.page)

    def test_it_says_what_it_read(self):
        self.assertEqual(self.said['week'], 46)
        self.assertEqual(self.said['word'], 'Flowing')
        self.assertGreater(self.said['read']['rows'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
