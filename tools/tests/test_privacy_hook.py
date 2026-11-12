"""The privacy hook refuses a GitHub write that would put a name or an id in
public: a PR's title or description, a comment, a branch, a file from the API
(12 Nov 2026). Every name here is invented."""
import contextlib, io, json, os, re, sys, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import privacy_check as pc
import privacy_hook as ph

NAME = 'Quillon Vantrell'


def call(tool, **tool_input):
    """Run the hook on one tool call; its exit code and what it said."""
    err = io.StringIO()
    stdin = io.StringIO(json.dumps({'tool_name': tool, 'tool_input': tool_input}))
    with mock.patch.object(pc, 'live_terms', return_value={NAME}), \
            mock.patch.dict(os.environ, {'BEDO_PRIVATE_TERMS': 'Zennor Hollow'}), contextlib.redirect_stderr(err):
        code = ph.main(stdin)
    return code, err.getvalue()


class Refuses(unittest.TestCase):
    def test_a_name_in_a_pull_request_description(self):
        code, said = call('mcp__github__create_pull_request', owner='o', repo='r', head='claude/x', base='main',
                          title='The week page', body='## Summary\nfor ' + NAME)
        self.assertEqual(code, 2)
        self.assertIn('body:2: private term', said)
        self.assertNotIn('Quillon', said)
        self.assertNotIn('Vantrell', said)

    def test_a_name_in_a_title_edit(self):
        code, said = call('mcp__github__update_pull_request', owner='o', repo='r', pullNumber=3,
                          title='Lunch with ' + NAME.split()[0] + ' ' + NAME.split()[1])
        self.assertEqual(code, 2)
        self.assertIn('title:1', said)

    def test_a_place_in_a_comment(self):
        code, _ = call('mcp__github__add_issue_comment', owner='o', repo='r', issue_number=3,
                       body='walked to zennor hollow')
        self.assertEqual(code, 2)

    def test_a_name_in_a_branch_made_from_the_api(self):
        code, said = call('mcp__github__create_branch', owner='o', repo='r', branch='claude/quillon_vantrell-notes',
                          from_branch='main')
        self.assertEqual(code, 2)
        self.assertIn('branch', said)

    def test_a_name_in_a_file_pushed_from_the_api(self):
        code, said = call('mcp__github__push_files', owner='o', repo='r', branch='claude/x', message='docs',
                          files=[{'path': 'docs/a.md', 'content': 'ok'}, {'path': 'docs/b.md', 'content': NAME}])
        self.assertEqual(code, 2)
        self.assertIn('files[1].content', said)

    def test_a_record_id_in_a_description(self):
        code, said = call('mcp__github__create_pull_request', owner='o', repo='r', head='h', base='main',
                          title='t', body='lands rec' + 'Ab3dE6gH9jK2mN')
        self.assertEqual(code, 2)
        self.assertIn('airtable id', said)


class Passes(unittest.TestCase):
    def test_a_clean_pull_request(self):
        code, said = call('mcp__github__create_pull_request', owner='o', repo='r', head='claude/privacy-outgoing',
                          base='main', title='The privacy check reads what the public sees',
                          body='## Summary\nfor her son and a neighbour, named by role')
        self.assertEqual(code, 0)
        self.assertNotIn('refused', said)

    def test_pointers_are_not_read(self):
        # an owner or repo that happens to match a name is where the call goes, not what it writes
        code, _ = call('mcp__github__add_issue_comment', owner='quillon', repo=NAME, issue_number=1, body='fine')
        self.assertEqual(code, 0)

    def test_not_a_tool_call(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(ph.main(io.StringIO('not json')), 0)


class Settings(unittest.TestCase):
    """The repo's own Claude Code settings run the hook before every GitHub write."""

    def test_every_github_write_is_matched(self):
        with open(os.path.join(ROOT, '.claude', 'settings.json'), encoding='utf-8') as f:
            s = json.load(f)
        pre = s['hooks']['PreToolUse']
        hooked = [h for h in pre if any('privacy_hook.py' in x['command'] for x in h['hooks'])]
        self.assertEqual(len(hooked), 1)
        rx = re.compile('^(?:' + hooked[0]['matcher'] + ')$')
        for tool in ('create_pull_request', 'update_pull_request', 'add_issue_comment', 'update_issue_comment',
                     'issue_write', 'add_reply_to_pull_request_comment', 'add_comment_to_pending_review',
                     'pull_request_review_write', 'create_branch', 'push_files', 'create_or_update_file'):
            self.assertTrue(rx.match('mcp__github__' + tool), tool)
        for tool in ('pull_request_read', 'list_branches', 'get_file_contents'):
            self.assertFalse(rx.match('mcp__github__' + tool), tool)


if __name__ == '__main__':
    unittest.main()
