# -*- coding: utf-8 -*-
"""The chat sweep reaches claude.ai (27 Nov 2026). Her sidebar showed cloud
sessions and plain claude.ai chats the sweep never saw, because the desktop
app's list_sessions holds only the laptop's own Code chats. claude.ai's lists
are read in the browser (chat-sweep/claude_ai_read.js) and ride in as one more
--sessions; the sweep's renames, unpins and archives for them go back the same
way (claude_ai_act.js). Every chat here is invented; the shapes are claude.ai's
as read that day. The two snippets run against a fake claude.ai when node is here.

    python3 plugins/bedo/skills/bedo-checks/tests/test_chats_claude_ai.py
"""
import datetime as dt, json, os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CORE = os.path.join(ROOT, 'core')
SWEEP = os.path.join(ROOT, 'skills', 'chat-sweep')
sys.path.insert(0, CORE)
import bedo_chats as CH  # noqa: E402

LOCAL = {'time_zone': 'America/Chicago', 'utc_offset_hours': -6}
NOW = dt.datetime(2026, 11, 27, 22, 0, tzinfo=dt.timezone.utc)
TODAY = '2026-11-27T16:00:00Z'
LAST_WEEK = '2026-11-18T16:00:00Z'
MINUTES_AGO = '2026-11-27T21:55:00Z'
MET = 'what I did\n· objective: the thing — met, done\n\nstill open\n· none\n———\n[be•do] x'

# claude.ai's own lists, as the browser reads them
CHATS = [   # GET /api/organizations/{ORG}/chat_conversations
    {'uuid': 'c0000000-0000-4000-8000-000000000001', 'name': 'Garden hose question', 'is_starred': False,
     'is_archived': False, 'is_temporary': False, 'updated_at': TODAY, 'created_at': TODAY},
    {'uuid': 'c0000000-0000-4000-8000-000000000002', 'name': '☑️ Bread machine manual', 'is_starred': True,
     'is_archived': False, 'is_temporary': False, 'updated_at': LAST_WEEK, 'created_at': LAST_WEEK},
    {'uuid': 'c0000000-0000-4000-8000-000000000003', 'name': 'Old one', 'is_starred': False,
     'is_archived': True, 'is_temporary': False, 'updated_at': LAST_WEEK, 'created_at': LAST_WEEK},
    {'uuid': 'c0000000-0000-4000-8000-000000000004', 'name': 'Passing question', 'is_starred': False,
     'is_archived': False, 'is_temporary': True, 'updated_at': TODAY, 'created_at': TODAY},
]
CODE = {'data': [   # GET /v1/code/sessions
    {'id': 'cse_01TESTCLOUD0001', 'title': '☑️𖡎D6.87 Chat sweep into the dusk flow', 'status': 'active',
     'status_bucket': 'completed', 'last_event_at': TODAY, 'tags': [], 'trigger_id': None, 'relations': {}},
    {'id': 'cse_01TESTCLOUD0002', 'title': '▶️𖡎D6.86 Dawn flow real page', 'status': 'active',
     'status_bucket': 'working', 'last_event_at': MINUTES_AGO, 'tags': [], 'trigger_id': None, 'relations': {}},
    {'id': 'cse_01TESTCLOUD0003', 'title': '⚡ Nightly run', 'status': 'active', 'status_bucket': 'review_ready',
     'last_event_at': TODAY, 'tags': ['nightly'], 'trigger_id': 'trig_01TEST', 'relations': {}},
    {'id': 'cse_01TESTCLOUD0004', 'title': '☑️ Gone', 'status': 'archived', 'status_bucket': 'completed',
     'last_event_at': LAST_WEEK, 'tags': [], 'trigger_id': None, 'relations': {}},
    {'id': 'cse_01TESTCLOUD0005', 'title': '☑️ Side piece', 'status': 'active', 'status_bucket': 'completed',
     'last_event_at': TODAY, 'tags': ['ui:pinned'], 'trigger_id': None,
     'relations': {'parent_session_id': 'cse_01TESTCLOUD0001'}},
], 'next_cursor': None}
ROWS = [
    {'id': 'rec1', 'created': '2026-11-27T15:00:00.000Z', 'practice': '⚡ action', 'status': '✅ done',
     'key': '261127_1104', 'details': MET, 'chat': 'https://claude.ai/code/session_01TESTCLOUD0001'},
    {'id': 'rec5', 'created': '2026-11-27T15:00:00.000Z', 'practice': '⚡ action', 'status': '✅ done',
     'key': '261127_1200', 'details': MET, 'chat': 'https://claude.ai/code/session_01TESTCLOUD0005'},
    {'id': 'rec2', 'created': '2026-11-18T15:00:00.000Z', 'practice': '⚡ action', 'status': '✅ done',
     'key': '261118_1000', 'details': MET, 'chat': 'https://claude.ai/chat/c0000000-0000-4000-8000-000000000002'},
]


def by_title(found):
    return {x['title']: x for x in found}


class Shapes(unittest.TestCase):
    def setUp(self):
        self.chats = CH.chats_of([CHATS, CODE])
        self.found = by_title(CH.sweep(self.chats, ROWS, NOW, LOCAL))

    def test_surfaces(self):
        s = {c['title']: c['surface'] for c in self.chats}
        self.assertEqual(s['Garden hose question'], 'chat')
        self.assertEqual(s['⚡ Nightly run'], 'cloud')
        self.assertEqual(CH.norm({'sessionId': 'local_abc', 'title': 'x'})['surface'], 'local')
        self.assertEqual(CH.norm({'id': 'local_abc', 'title': 'x'})['surface'], 'local')

    def test_archived_and_temporary_are_not_swept(self):
        for t in ('Old one', 'Passing question', '☑️ Gone'):
            self.assertNotIn(t, self.found)

    def test_a_scheduled_run_is_routine(self):
        self.assertEqual(self.found['⚡ Nightly run']['verdict'], 'routine')

    def test_working_in_lower_case_is_busy(self):
        self.assertEqual(self.found['▶️𖡎D6.86 Dawn flow real page']['verdict'], 'busy')

    def test_a_starred_chat_is_pinned(self):
        x = self.found['☑️ Bread machine manual']
        self.assertEqual(x['verdict'], 'archive')
        self.assertTrue(x['unpin'])

    def test_the_parent_comes_from_relations(self):
        self.assertEqual(self.found['☑️ Side piece']['parent'], 'cse_01TESTCLOUD0001')

    def test_a_cse_id_finds_its_session_row(self):
        self.assertEqual(self.found['☑️𖡎D6.87 Chat sweep into the dusk flow']['row']['key'], '261127_1104')

    def test_a_plain_chat_with_no_row_is_renamed_open(self):
        self.assertEqual(self.found['Garden hose question']['rename'], '▶️ Garden hose question')

    def test_a_next_cursor_means_the_list_goes_on(self):
        self.assertEqual(CH.list_goes_on([{**CODE, 'next_cursor': 'abc'}]), 'cursor abc')
        self.assertIsNone(CH.list_goes_on([CODE]))
        # the desktop app's pages end on their own terms, whatever claude.ai's say
        self.assertEqual(CH.list_goes_on([{'has_more': True, 'last_id': 'local_x', 'data': []}, CODE]), 'local_x')

    def test_a_sweep_of_one_surface_says_so(self):
        text = CH.render(list(self.found.values()), NOW, CH.surfaces_read([CHATS, CODE]))
        self.assertIn("not in this sweep: the desktop app's own Code chats", text)
        self.assertNotIn('not in this sweep: claude.ai chats', text)
        self.assertIn('in the browser: 2 claude.ai chat(s)', text)
        local_only = CH.render([], NOW, CH.surfaces_read([{'sessions': [{'sessionId': 'local_a', 'title': 'x'}]}]))
        self.assertIn('not in this sweep: cloud Code and Cowork sessions', local_only)
        self.assertIn('not in this sweep: claude.ai chats', local_only)

    def test_a_read_with_nothing_open_still_counts(self):
        self.assertEqual(CH.surfaces_read([{'claude_ai': {'read': ['chat', 'cloud'], 'data': []}}]), {'chat', 'cloud'})


def node():
    return shutil.which('node')


FAKE = r"""
const state = JSON.parse(process.env.FAKE_STATE);
const calls = [];
const json = (b, s = 200) => ({ ok: s < 400, status: s, json: async () => b, text: async () => JSON.stringify(b) });
globalThis.setTimeout = f => f();
globalThis.fetch = async (u, o = {}) => {
  const m = (o.method || 'GET');
  calls.push([m, u, o.body ? JSON.parse(o.body) : null, (o.headers || {})['anthropic-version'] || null]);
  if (u === '/api/organizations') return json([{ uuid: 'org1', capabilities: ['chat'] }]);
  let r;
  if ((r = u.match(/^\/api\/organizations\/org1\/chat_conversations\?limit=400&offset=(\d+)/)))
    return json(+r[1] ? [] : state.chats);
  if ((r = u.match(/^\/api\/organizations\/org1\/chat_conversations\/([^?]+)$/))) {
    const c = state.chats.find(x => x.uuid === r[1]);
    if (m === 'PUT') Object.assign(c, JSON.parse(o.body));
    return json(c, m === 'PUT' ? 202 : 200);
  }
  if (u.startsWith('/v1/code/sessions?')) {
    if (!(o.headers || {})['anthropic-version']) return json({}, 400);
    return json(u.includes('cowork-remote') ? { data: [], next_cursor: null } : state.code);
  }
  if ((r = u.match(/^\/v1\/code\/sessions\/([^/]+)(\/archive)?$/))) {
    const s = state.code.data.find(x => x.id === r[1]);
    if (r[2]) s.status = 'archived';
    else if (m === 'PUT') Object.assign(s, JSON.parse(o.body));
    return json(s);
  }
  return json({}, 404);
};
const __r = """


def run_js(path, state, found=None):
    with open(path, encoding='utf-8') as f:
        src = f.read()
    if found is not None:
        src = src.replace('__FOUND__', json.dumps(found, ensure_ascii=False))
    d = tempfile.mkdtemp()
    try:
        p = os.path.join(d, 'run.mjs')
        with open(p, 'w', encoding='utf-8') as f:
            f.write(FAKE + src + ';\nconsole.log(JSON.stringify({ out: JSON.parse(__r), calls }));\n')
        r = subprocess.run([node(), p], capture_output=True, text=True, encoding='utf-8', timeout=60,
                           env=dict(os.environ, FAKE_STATE=json.dumps(state, ensure_ascii=False)))
        if r.returncode:
            raise AssertionError(r.stderr)
        return json.loads(r.stdout)
    finally:
        shutil.rmtree(d, ignore_errors=True)


@unittest.skipUnless(node(), 'no node here')
class Snippets(unittest.TestCase):
    def test_the_read_rides_in_as_sessions(self):
        got = run_js(os.path.join(SWEEP, 'claude_ai_read.js'), {'chats': CHATS, 'code': CODE})
        saved = got['out']
        titles = {c['title'] for c in CH.chats_of([saved])}
        self.assertEqual(titles, {'Garden hose question', '☑️ Bread machine manual',
                                  '☑️𖡎D6.87 Chat sweep into the dusk flow', '▶️𖡎D6.86 Dawn flow real page',
                                  '☑️ Side piece'})
        self.assertEqual(CH.surfaces_read([saved]), {'chat', 'cloud'})
        self.assertTrue(all(c[0] == 'GET' for c in got['calls']), 'the read changes nothing')
        self.assertTrue(all(c[3] for c in got['calls'] if c[1].startswith('/v1/code')))

    def test_the_act_renames_before_it_archives_and_leaves_busy_alone(self):
        state = {'chats': json.loads(json.dumps(CHATS)), 'code': json.loads(json.dumps(CODE))}
        found = CH.sweep(CH.chats_of([CHATS, CODE]), ROWS, NOW, LOCAL)
        got = run_js(os.path.join(SWEEP, 'claude_ai_act.js'), state, found)
        out, calls = got['out'], got['calls']
        self.assertEqual(out['failed'], [])
        writes = [(m, u, b) for m, u, b, _ in calls if m != 'GET']
        self.assertIn(('PUT', '/api/organizations/org1/chat_conversations/c0000000-0000-4000-8000-000000000001',
                       {'name': '▶️ Garden hose question'}), writes)
        food = [b for m, u, b in writes if u.endswith('-000000000002')]
        self.assertEqual(food, [{'is_starred': False}, {'is_archived': True}])
        self.assertIn(('POST', '/v1/code/sessions/cse_01TESTCLOUD0005/archive', {}), writes)
        self.assertIn(('PUT', '/v1/code/sessions/cse_01TESTCLOUD0005', {'tags': []}), writes)
        self.assertFalse([u for m, u, b in writes if 'CLOUD0002' in u or 'CLOUD0003' in u], 'busy and routine untouched')
        # a finished side chat doesn't hold its finished parent: both go
        self.assertIn(('POST', '/v1/code/sessions/cse_01TESTCLOUD0001/archive', {}), writes)
        self.assertIsNone(out['next'])


if __name__ == '__main__':
    unittest.main()
