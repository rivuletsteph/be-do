# -*- coding: utf-8 -*-
"""The dawn page (27 Nov 2026): four lanes, the next three to tap, what's done
in the order done. The order is bedo_remaining's; the page decides what is
done in JavaScript, and that has to agree with what the remaining line counts.

    python3 core/tests/test_dawn_page.py
"""
import json, os, re, shutil, subprocess, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.dirname(HERE)
sys.path.insert(0, CORE)
import bedo_dawn_page as P  # noqa: E402
import bedo_remaining as R  # noqa: E402

DAWN = '🌅 dawn'


def step(p, w, t, group='flow', order=None):
    return {'practice': p, 'active': True, 'phase': DAWN, 'group': group, 'typical_time': t, 'order': order, 'wellness': w}


CAT = [
    step('😶 wake', '🤸‍♀️ body', 'wake+0'),
    step('💭 dream record', '🩷 heart', 'wake+10'),
    step('🪐 morning ring', '🤸‍♀️ body', 'wake+5'),
    step('🗞️ morning gate', '🧠 mind', 'wake+100'),
    step('🌦️ weather check', '🧠 mind', 'wake+101'),
    step('👁️ look ahead', '🧠 mind', 'wake+200'),
    step('☕ coffee', '🤸‍♀️ body', 'wake+60'),
    step('🥤 morning water', '🤸‍♀️ body', 'wake+70'),
    step('🚽 bm', '🤸‍♀️ body', 'wake+65'),
    step('🔅 morning sun', '🤸‍♀️ body', 'wake+80'),
    step('🙏 gratitude', '🩷 heart', 'wake+150'),
    step('📗 morning book', '💖 spirit', 'wake+160'),
    step('📿 morning mantra', '💖 spirit', 'wake+90'),
    step('⚡ intention check', '🧠 mind', 'wake+210'),
    step('🌅 dawn flow close', '💖 spirit', 'wake+300'),
]
LOCAL = {'stream_fields': {k: 'fld' + k for k in ('title', 'practice', 'status', 'datetime', 'details')},
         'stream_table': 'tblX', 'time_zone': 'America/Chicago', 'utc_offset_hours': -6, 'weekly_name': 'w{n} be•do'}


def row(p, t, s='◉ done', title='', d=''):
    return {'id': 'rec' + str(abs(hash((p, t))))[:14], 'practice': p, 'datetime': t, 'status': s, 'title': title, 'details': d}


ROWS = [
    row('😶 wake', '2026-11-28T11:00:00.000Z'),
    row('💭 dream record', '2026-11-28T11:10:00.000Z', title='💭 a long drive', d='I dreamt of a drive.\n———\n[be•do] x'),
    row('☕ coffee', '2026-11-28T12:05:00.000Z', title='☕ coffee'),
    row('📗 book', '2026-11-28T12:30:00.000Z'),                     # same kind: the morning book
    row('🌅 dawn flow close', '2026-11-28T12:31:00.000Z', s='▶️ in motion'),   # an open close row closes nothing
]


class Steps(unittest.TestCase):
    def test_the_page_draws_her_steps_in_the_remaining_order(self):
        got = [s['p'] for s in P.steps(CAT)]
        want = [r['practice'] for r in R.flow_steps(CAT, 'dawn')
                if r['practice'] not in ('😶 wake', '🪐 morning ring', '🌦️ weather check', '🌅 dawn flow close')]
        self.assertEqual(got, want)

    def test_code_steps_are_marked_and_bm_is_quiet(self):
        by = {s['p']: s for s in P.steps(CAT)}
        self.assertTrue(by['🗞️ morning gate']['code'] and by['👁️ look ahead']['code'])
        self.assertFalse(by['☕ coffee']['code'])
        self.assertTrue(by['🚽 bm']['quiet'])
        self.assertTrue(by['🔅 morning sun']['sun'])

    def test_lanes_follow_the_wheel_pairs(self):
        self.assertEqual(P.lane('🩷 heart'), 'heart')
        self.assertEqual(P.lane('🌊 water'), 'heart')
        self.assertEqual(P.lane('🤸‍♀️ body'), 'body')
        self.assertEqual(P.lane('💨 air'), 'mind')
        self.assertEqual(P.lane('💖 spirit'), 'spirit')


class Page(unittest.TestCase):
    def setUp(self):
        import datetime as dt
        self.data = P.plan(CAT, ROWS, LOCAL, dt.date(2026, 11, 28), 'base-under-test', 'w49 be•do')

    def test_data_goes_in_with_every_lt_escaped(self):
        self.data['rows'][0]['d'] = '</script><b>'
        html = P.render(self.data)
        self.assertNotIn('</script><b>', html)
        self.assertIn('\\u003c/script>', html)

    def test_it_never_polls(self):
        src = open(P.TEMPLATE, encoding='utf-8').read()
        for word in ('setInterval', 'refetchInterval', 'watchTool'):
            self.assertNotIn(word, src, f'{word}: the page reads only when opened, returned to, or asked')

    def test_a_tap_writes_with_typecast_off(self):
        self.assertIn('typecast: false', open(P.TEMPLATE, encoding='utf-8').read())

    def test_the_manifest_names_every_tool_the_page_calls(self):
        src = open(P.TEMPLATE, encoding='utf-8').read()
        called = set(re.findall(r'callTool\("Airtable", "(\w+)"', src))
        self.assertEqual(called, set(P.CAPABILITIES['mcp']['servers'][0]['tools']))

    @unittest.skipUnless(shutil.which('node'), 'node not installed')
    def test_the_page_counts_what_the_remaining_line_counts(self):
        src = open(P.TEMPLATE, encoding='utf-8').read()
        logic = src.split('/*LOGIC*/')[1].split('/*END LOGIC*/')[0]
        rows = self.data['rows']

        def run(now):
            js = logic + f'\nconst D = {json.dumps(self.data)};\n' + \
                'console.log(JSON.stringify(dawnState(D, D.rows, process.argv[1])));'
            out = subprocess.run(['node', '-e', js, now], capture_output=True, text=True, check=True).stdout
            return json.loads(out)
        st = run('2026-11-28T12:40:00.000Z')                       # 6:40 AM
        have = R.logged([{'practice': r['p'], 'status': r['s'], 'datetime': r['t']} for r in rows], LOCAL)
        done = {s['p'] for s in st['steps'] if s['row']}
        self.assertEqual(done, {s['p'] for s in P.steps(CAT) if R.norm(s['p']) in have})
        self.assertEqual(done, {'💭 dream record', '☕ coffee', '📗 morning book'})
        self.assertEqual([s['p'] for s in st['next']], ['🥤 morning water', '🔅 morning sun', '📿 morning mantra'])
        self.assertEqual([x['p'] for x in st['list']], ['💭 dream record', '☕ coffee', '📗 morning book'])
        self.assertEqual(st['list'][0]['line'], 'a long drive')
        self.assertIsNone(st['close'])
        # bm is asked only once all else of hers is in
        for p in ('🥤 morning water', '🔅 morning sun', '📿 morning mantra', '🙏 gratitude', '⚡ intention check'):
            rows.append({'id': 'r' + p, 'p': p, 't': '2026-11-28T13:00:00.000Z', 's': '◉ done', 'title': p, 'd': ''})
        self.assertEqual([s['p'] for s in run('2026-11-28T13:10:00.000Z')['next']], ['🚽 bm'])


DUSK = '🌄 dusk'


def dstep(p, w, t, group='flow'):
    return {'practice': p, 'active': True, 'phase': DUSK, 'group': group, 'typical_time': t, 'order': None, 'wellness': w}


DCAT = [
    dstep('🔅 evening sun', '🤸‍♀️ body', '17:14'),
    dstep('🪐 evening ring', '🤸‍♀️ body', '21:39'),
    dstep('🗺️ map check', '🧠 mind', '21:42'),
    dstep('💊 bp meds', '🤸‍♀️ body', '20:44'),
    dstep('🌈 supplements', '🤸‍♀️ body', '20:49'),
    dstep('🫖 evening tea', '🤸‍♀️ body', '21:02'),
    dstep('⭐ highlight', '💖 spirit', '17:30'),
    dstep('🔀 braid', '🧠 mind', '22:28'),
    dstep('🌬️ evening breaths', '🤸‍♀️ body', '22:20'),
    dstep('🌌 evening blessing', '💖 spirit', '22:28'),
    dstep('🌄 dusk flow close', '💖 spirit', '23:50'),
]


class Dusk(unittest.TestCase):
    def setUp(self):
        import datetime as dt
        self.local = {**LOCAL, 'evening_pills': {'default': {'💊 bp meds': ['a pill'], '🌈 supplements': ['a mineral']}}}
        rows = [row('🔅 evening sun', '2026-11-28T23:30:00.000Z'),
                row('💊 bp meds', '2026-11-29T03:00:00.000Z'),
                row('🫖 evening tea', '2026-11-29T06:20:00.000Z'),          # 12:20 AM: still that evening
                row('🌄 dusk flow close', '2026-11-29T03:10:00.000Z', s='▶️ in motion')]
        self.data = P.plan(DCAT, rows, self.local, dt.date(2026, 11, 28), 'base-under-test', 'w49 be•do', 'dusk')

    def test_pills_are_one_step_and_code_steps_are_marked(self):
        by = {s['p']: s for s in self.data['steps']}
        self.assertEqual(by['💊 evening pills']['members'], ['💊 bp meds', '🌈 supplements'])
        self.assertNotIn('💊 bp meds', by)
        self.assertTrue(by['🔀 braid']['code'] and by['🗺️ map check']['code'] and by['🪐 evening ring']['code'])
        self.assertTrue(by['⭐ highlight']['words'])
        self.assertTrue(by['🌌 evening blessing']['pattern'])
        self.assertNotIn('🌄 dusk flow close', by)
        self.assertIn('a pill', self.data['member_lines']['💊 bp meds'])
        self.assertEqual(self.data['title'], 'Dusk flow')
        self.assertIn('<title>Dusk flow</title>', P.render(self.data))

    @unittest.skipUnless(shutil.which('node'), 'node not installed')
    def test_the_evening_runs_past_midnight_and_pills_wait_for_both(self):
        src = open(P.TEMPLATE, encoding='utf-8').read()
        logic = src.split('/*LOGIC*/')[1].split('/*END LOGIC*/')[0]
        self.data['rows'].append({'id': 'x', 'p': '🫖 evening tea', 't': '2026-11-29T06:20:00.000Z', 's': '◉ done', 'title': '', 'd': ''})
        js = logic + f'\nconst D = {json.dumps(self.data)};\n' + \
            'console.log(JSON.stringify(dawnState(D, D.rows, process.argv[1])));'
        st = json.loads(subprocess.run(['node', '-e', js, '2026-11-29T06:30:00.000Z'],
                                       capture_output=True, text=True, check=True).stdout)
        self.assertEqual(st['date'], '2026-11-28')
        done = {s['p'] for s in st['steps'] if s['row']}
        self.assertEqual(done, {'🔅 evening sun', '🫖 evening tea'})      # pills wait for both; an open close closes nothing
        pills = next(s for s in st['steps'] if s['p'] == '💊 evening pills')
        self.assertEqual(pills['todo'], ['🌈 supplements'])
        self.assertNotIn('🌬️ evening breaths', [s['p'] for s in st['next']])
        self.assertNotIn('🔀 braid', [s['p'] for s in st['next']])
        # the batch is one card (her words, 27 Nov 2026: I normally do those all at once)
        cards = [s for s in st['next'] if s.get('batch')]
        self.assertEqual(len(cards), 1)
        self.assertEqual([m['p'] for m in cards[0]['members']], ['🪐 evening ring', '🗺️ map check'])

    @unittest.skipUnless(shutil.which('node'), 'node not installed')
    def test_batch_toggles_decide_the_batch(self):
        src = open(P.TEMPLATE, encoding='utf-8').read()
        logic = src.split('/*LOGIC*/')[1].split('/*END LOGIC*/')[0]

        def run(saved):
            js = logic + f'\nconst D = {json.dumps(self.data)};\n' + \
                f'console.log(JSON.stringify(dawnState(D, D.rows, "2026-11-29T03:30:00.000Z", {json.dumps(saved)})));'
            return json.loads(subprocess.run(['node', '-e', js], capture_output=True, text=True, check=True).stdout)
        st = run({})
        self.assertEqual([i['key'] for i in st['items']], ['timeline', 'stress', 'recordings', 'wellbeing', 'photos'])
        self.assertTrue(any(s.get('batch') for s in st['next']))
        self.assertEqual(next(i for i in st['items'] if i['key'] == 'timeline')['choices'], ['up', 'stayed home'])
        everything = {k: {'state': 'up'} for k in ('timeline', 'stress', 'recordings', 'wellbeing', 'photos')}
        self.assertFalse(any(s.get('batch') for s in run(everything)['next']))   # all marked: off the next list
        self.assertIn('db', P.capabilities('dusk'))
        self.assertNotIn('db', P.capabilities('dawn'))

    def test_batch_steps_are_marked(self):
        by = {s['p']: s for s in self.data['steps']}
        self.assertTrue(by['🗺️ map check']['batch'] and by['🪐 evening ring']['batch'])
        self.assertFalse(by['🫖 evening tea']['batch'])
        self.assertEqual(self.data['batch']['label'], 'batch')


if __name__ == '__main__':
    unittest.main()
