# -*- coding: utf-8 -*-
"""The chat sweep on the cloud's session list (12 Nov 2026). On 12 Nov the
sweep read claude-code-remote's `list_sessions` as if it were the desktop
app's: it counted 100 open and asked to archive 75 chats already archived,
and the second page (has_more) was never read. Every chat here is invented;
the shape is the cloud tool's, saved as it came.

    python3 plugins/bedo/skills/bedo-checks/tests/test_chats_cloud.py
"""
import datetime as dt, json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
CORE = os.path.join(ROOT, 'core')
sys.path.insert(0, CORE)
import bedo_chats as CH  # noqa: E402

LOCAL = {'time_zone': 'America/Chicago', 'utc_offset_hours': -6}
NOW = dt.datetime(2026, 11, 12, 20, 0, tzinfo=dt.timezone.utc)   # 2:00p in Chicago
TODAY = '2026-11-12T15:30:00Z'       # 9:30a her time
YESTERDAY = '2026-11-11T22:00:00Z'   # 4:00p the day before
LATE_YESTERDAY = '2026-11-12T05:30:00Z'   # 11:30p on the 11th her time: not today, though the UTC date is
MET = 'what I did\n· objective: the thing — met, done\n\nstill open\n· none\n———\n[be•do] x'


def s(n, title, status='IDLE', bucket='REVIEW_READY', last=YESTERDAY, tags=(), parent=None):
    out = {'id': f'session_01CLOUD{n:04d}', 'title': title,
           'session_status': f'SESSION_STATUS_{status}', 'status_bucket': f'SESSION_STATUS_BUCKET_{bucket}',
           'updated_at': last, 'created_at': '2026-11-01T12:00:00Z', 'tags': list(tags)}
    if parent:
        out['parent_session_id'] = parent
    return out


def row(n, status='✅ done', details=MET):
    return {'id': f'rec{n}', 'created': '2026-11-11T15:00:00.000Z', 'practice': '⚡ action', 'status': status,
            'key': f'261111_{n:04d}', 'details': details,
            'chat': f'https://claude.ai/code/session_01CLOUD{n:04d}'}


PIN = 'ui:pinned'
PAGE1 = {'ccr': {'data': [
    s(1, '☑️ Old finished work', status='ARCHIVED', bucket='COMPLETED'),
    s(2, '▶️ Running now', status='RUNNING', bucket='WORKING', last=TODAY),
    s(3, '▶️ Idle in motion', last=YESTERDAY),
    s(4, '▶️ Pinned and stale', tags=[PIN], last=YESTERDAY),
    s(5, '▶️ Pinned and touched today', tags=[PIN], last=TODAY),
    s(6, '▶️ Pinned, late last night', tags=[PIN], last=LATE_YESTERDAY),
    s(7, '▶️🔆1112 🌳 Thu 𖡎 W46 my day', tags=[PIN], last=YESTERDAY),
    s(8, '☑️ Parent work', last=YESTERDAY),
    s(9, '☑️ Side work', last=YESTERDAY, parent='session_01CLOUD0008'),
], 'has_more': True, 'first_id': 'session_01CLOUD0001', 'last_id': 'session_01CLOUD0009'}}
PAGE2 = {'ccr': {'data': [
    s(10, '▶️ On the second page', last=TODAY),
], 'has_more': False, 'first_id': 'session_01CLOUD0010', 'last_id': 'session_01CLOUD0010'}}
ROWS = [row(3, status='▶️ in motion'), row(4, status='▶️ in motion'), row(5, status='▶️ in motion'),
        row(6, status='▶️ in motion'), row(7, status='▶️ in motion'), row(8), row(10, status='▶️ in motion')]


def sweep(*pages):
    return {x['title']: x for x in CH.sweep(CH.chats_of(list(pages)), ROWS, NOW, LOCAL)}


class CloudShape(unittest.TestCase):
    def setUp(self):
        self.got = sweep(PAGE1, PAGE2)

    def test_the_wrapped_list_is_read(self):
        self.assertEqual(len(CH.chats_of([PAGE1])), 9)

    def test_archived_is_not_swept(self):
        self.assertNotIn('☑️ Old finished work', self.got)

    def test_running_is_busy(self):
        self.assertEqual(self.got['▶️ Running now']['verdict'], 'busy')

    def test_idle_in_motion_is_kept(self):
        self.assertEqual(self.got['▶️ Idle in motion']['verdict'], 'keep')
        self.assertFalse(self.got['▶️ Idle in motion']['unpin'])

    def test_pinned_by_tag_and_stale_is_unpinned(self):
        x = self.got['▶️ Pinned and stale']
        self.assertEqual((x['verdict'], x['unpin']), ('unpin', True))

    def test_pinned_and_touched_today_stays(self):
        x = self.got['▶️ Pinned and touched today']
        self.assertEqual((x['verdict'], x['unpin']), ('keep', False))

    def test_today_is_her_day_not_utc(self):
        self.assertEqual(self.got['▶️ Pinned, late last night']['verdict'], 'unpin')

    def test_the_my_day_chat_is_never_unpinned(self):
        x = self.got['▶️🔆1112 🌳 Thu 𖡎 W46 my day']
        self.assertEqual((x['verdict'], x['unpin']), ('keep', False))

    def test_a_child_holds_its_parent(self):
        self.assertEqual(self.got['☑️ Side work']['verdict'], 'entry')
        self.assertEqual(self.got['☑️ Parent work']['verdict'], 'hold')
        self.assertEqual(self.got['☑️ Side work']['parent'], 'session_01CLOUD0008')

    def test_the_second_page_counts(self):
        self.assertEqual(self.got['▶️ On the second page']['verdict'], 'keep')
        self.assertEqual(len(self.got), 9)

    def test_paging_is_whole_only_when_a_page_ends_it(self):
        self.assertEqual(CH.list_goes_on([PAGE1]), 'session_01CLOUD0009')
        self.assertIsNone(CH.list_goes_on([PAGE1, PAGE2]))

    def test_render_names_the_unpins_in_one_line(self):
        text = CH.render(list(self.got.values()), NOW)
        line = next(l for l in text.splitlines() if l.startswith('unpin:'))
        self.assertIn('Pinned and stale', line)
        self.assertNotIn('my day', line)
        cloud = next(l for l in text.splitlines() if l.strip().startswith('cloud:'))
        self.assertIn('set_session_tags remove ["ui:pinned"]', cloud)
        self.assertIn('session_01CLOUD0004', cloud)
        self.assertNotIn('session_01CLOUD0007', cloud)


class Command(unittest.TestCase):
    def test_one_page_alone_says_read_the_next(self):
        d = tempfile.mkdtemp()
        p1, rows, facts = (os.path.join(d, n) for n in ('p1.json', 'rows.json', 'facts.json'))
        for p, v in ((p1, PAGE1), (rows, ROWS), (facts, {**LOCAL, 'stream_fields': {}})):
            with open(p, 'w', encoding='utf-8') as f:
                json.dump(v, f)
        env = {**os.environ, 'BEDO_FACTS_LOCAL': facts, 'PYTHONIOENCODING': 'utf-8'}
        r = subprocess.run([sys.executable, os.path.join(CORE, 'bedo_chats.py'), '--sessions', p1,
                            '--rows', rows, '--now', NOW.isoformat()], capture_output=True, text=True,
                           env=env, encoding='utf-8')
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn('after_id session_01CLOUD0009', r.stderr)


if __name__ == '__main__':
    unittest.main()
