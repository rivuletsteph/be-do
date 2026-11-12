"""The privacy check reads the live names once per run, and a plain branch push
reads none: every Airtable read counts toward the plan."""
import contextlib, io, os, re, sys, tempfile, unittest
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import privacy_check as pc


def fake_git(added=''):
    def git(*a):
        if a[0] == 'diff':
            return '+++ b/some/file\n+' + added + '\n'
        return ''   # no tracked files, no commits: only the added line is read
    return git


def run(args, added='', static='', live=None):
    """Run the check; returns its exit code and how many times the names were read."""
    reads = mock.Mock(return_value=live)
    err, out = io.StringIO(), io.StringIO()
    with mock.patch.object(pc, 'live_terms', reads), mock.patch.object(pc, 'git', fake_git(added)), \
            mock.patch.dict(os.environ, {'BEDO_PRIVATE_TERMS': static}), \
            contextlib.redirect_stderr(err), contextlib.redirect_stdout(out):
        try:
            pc.main(args)
        except SystemExit as e:
            return e.code, reads.call_count, out.getvalue() + err.getvalue()
    raise AssertionError('the check always exits')


class Modes(unittest.TestCase):
    def test_no_argument_checks_the_files(self):
        self.assertEqual(pc.modes([]), (True, None, False))

    def test_diff_alone_checks_only_the_change(self):
        self.assertEqual(pc.modes(['--diff', 'origin/main']), (False, 'origin/main', False))

    def test_files_and_diff_go_together(self):
        self.assertEqual(pc.modes(['--files', '--diff', 'origin/main']), (True, 'origin/main', False))

    def test_an_unknown_argument_stops_the_run(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as e:
            pc.modes(['--fils'])
        self.assertEqual(e.exception.code, 2)


class OneRead(unittest.TestCase):
    def test_files_and_diff_read_the_names_once(self):
        code, reads, _ = run(['--files', '--diff', 'origin/main'], added='a plain line', live={'Quillon Vantrell'})
        self.assertEqual((code, reads), (0, 1))

    def test_a_live_name_in_an_added_line_fails_and_is_masked(self):
        code, _, said = run(['--files', '--diff', 'origin/main'], added='lunch with Quillon Vantrell',
                            live={'Quillon Vantrell'})
        self.assertEqual(code, 1)
        self.assertNotIn('Quillon Vantrell', said)

    def test_a_static_term_fails_with_no_live_source(self):
        code, _, _ = run(['--diff', 'origin/main'], added='a walk at Zennor Hollow', static='Zennor Hollow')
        self.assertEqual(code, 1)

    def test_the_run_says_how_many_calls_it_made(self):
        with mock.patch.object(pc, 'CALLS', 7):
            _, _, said = run([], live={'Quillon Vantrell'})
        self.assertIn('in 7 Airtable calls', said)


class Outgoing(unittest.TestCase):
    """What the public sees is more than the files (12 Nov 2026): a PR's title and
    description, branch names, commit author emails."""

    def test_a_title_with_a_name_fails_and_is_masked(self):
        code, _, said = run(['--title', 'Lunch with Quillon Vantrell'], live={'Quillon Vantrell'})
        self.assertEqual(code, 1)
        self.assertIn('title:1: private term', said)
        self.assertNotIn('Quillon', said)

    def test_a_description_file_is_read(self):
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write('## Summary\n\nA walk at Zennor Hollow\n')
        try:
            code, _, said = run(['--text', f.name], static='Zennor Hollow')
        finally:
            os.unlink(f.name)
        self.assertEqual(code, 1)
        self.assertIn(':3: private term', said)

    def test_a_clean_title_and_description_pass(self):
        code, _, _ = run(['--title', 'The my week page opens quiet'], live={'Quillon Vantrell'})
        self.assertEqual(code, 0)

    def test_a_record_id_in_a_description_fails(self):
        code, _, said = run(['--title', 'lands rec' + 'Ab3dE6gH9jK2mN'])
        self.assertEqual(code, 1)
        self.assertIn('airtable id', said)

    def test_a_branch_name_is_read_as_words(self):
        for b in ('claude/quillon-quest', 'quillon_quest', 'Quillon.notes'):
            code, _, said = run(['--branch', b], live={'Quillon'})
            self.assertEqual(code, 1, b)
            self.assertNotIn('uillon', said, b)
        code, _, _ = run(['--branch', 'claude/privacy-outgoing-text'], live={'Quillon'})
        self.assertEqual(code, 0)

    def test_outgoing_is_files_diff_and_this_branch(self):
        with mock.patch.object(pc, 'current_branch', return_value='claude/some-work'):
            r = pc.parse(['--outgoing', '--title', 'T'])
        self.assertEqual((r.files, r.base, r.branches, r.texts), (True, 'origin/main', ['claude/some-work'], [('title', 'T')]))

    def test_outgoing_keeps_a_named_base(self):
        with mock.patch.object(pc, 'current_branch', return_value=None):
            self.assertEqual(pc.parse(['--outgoing', '--diff', 'origin/dev']).base, 'origin/dev')

    def test_text_alone_does_not_check_the_files(self):
        self.assertFalse(pc.parse(['--title', 'T']).files)

    def test_a_personal_author_email_on_a_new_commit_fails(self):
        def git(*a):
            if a[0] == 'rev-list':
                return 'abc1234def\n'
            if a[:2] == ('log', '-1') and a[2] == '--format=%ae %ce':
                return 'quillon.v' + '@mailhost.net noreply@github.com\n'
            return ''
        err, out = io.StringIO(), io.StringIO()
        with mock.patch.object(pc, 'live_terms', return_value=None), mock.patch.object(pc, 'git', git), \
                mock.patch.dict(os.environ, {'BEDO_PRIVATE_TERMS': ''}), \
                contextlib.redirect_stderr(err), contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as e:
            pc.main(['--diff', 'origin/main'])
        self.assertEqual(e.exception.code, 1)
        self.assertIn('author: email', out.getvalue())
        self.assertNotIn('quillon.v', out.getvalue())

    def test_the_noreply_addresses_pass(self):
        hits = []
        with mock.patch.object(pc, 'git', return_value='1+someone@users.noreply.github.com noreply@anthropic.com'):
            pc.check_people('abc1234', hits)
        self.assertEqual(hits, [])


class PrePushHook(unittest.TestCase):
    def test_the_hook_passes_the_pushed_branch_names(self):
        with open(os.path.join(ROOT, '.githooks', 'pre-push'), encoding='utf-8') as f:
            hook = f.read()
        self.assertIn('refs/heads/', hook)
        self.assertIn('--branch', hook)
        self.assertEqual(hook.count('privacy_check.py'), 1)


class Workflow(unittest.TestCase):
    """The workflow hands the Airtable token only to a pull request and a push to main."""

    def steps(self):
        with open(os.path.join(ROOT, '.github', 'workflows', 'privacy.yml'), encoding='utf-8') as f:
            text = f.read()
        return [s for s in re.split(r'\n      - ', text.split('steps:')[1]) if 'privacy_check.py' in s]

    def test_each_run_calls_the_check_once(self):
        for s in self.steps():
            self.assertEqual(s.count('privacy_check.py'), 1, s)
            self.assertIn('if: github.event_name', s)

    def test_a_branch_push_gets_no_token(self):
        branch = [s for s in self.steps() if "github.ref != 'refs/heads/main'" in s]
        self.assertEqual(len(branch), 1)
        self.assertNotIn('AIRTABLE_READ_TOKEN', branch[0])
        self.assertIn('BEDO_PRIVATE_TERMS', branch[0])

    def test_main_and_pull_requests_read_the_names(self):
        live = [s for s in self.steps() if 'AIRTABLE_READ_TOKEN' in s]
        self.assertEqual(len(live), 2)
        self.assertTrue(any("github.ref == 'refs/heads/main'" in s for s in live))
        self.assertTrue(any("'pull_request'" in s and '--files --diff' in s for s in live))

    def test_a_pull_request_run_reads_its_title_description_and_branch(self):
        pr = [s for s in self.steps() if "'pull_request'" in s][0]
        for want in ('github.event.pull_request.title', 'github.event.pull_request.body', 'github.head_ref',
                     '--text', '--branch'):
            self.assertIn(want, pr)
        # the PR's text reaches the script through the environment, never pasted into it
        run_part = pr.split('run:', 1)[1]
        self.assertNotIn('${{', run_part)

    def test_an_edited_description_runs_the_check_again(self):
        with open(os.path.join(ROOT, '.github', 'workflows', 'privacy.yml'), encoding='utf-8') as f:
            self.assertRegex(f.read(), r'pull_request:\n\s+types: \[[^\]]*\bedited\b')



class Services(unittest.TestCase):
    """Which apps, stores, banks and devices someone uses is a map to their logins
    (12 Nov 2026): a service named in anything new is a hit. Every service below is
    on the generic list, and nothing here says who uses it."""
    def go(self, args, added=''):
        with mock.patch.object(pc, 'live_services', mock.Mock(return_value={'Streamly'})):
            return run(args, added=added)

    def test_a_service_in_an_added_line_is_a_hit(self):
        code, _, out = self.go(['--diff', 'origin/main'], added='open it in Netflix')   # privacy: ok
        self.assertEqual(code, 1)
        self.assertIn('a service someone uses', out)
        self.assertNotIn('Netflix', out.replace('open it in Netflix', ''))   # privacy: ok

    def test_a_service_from_her_settings_is_a_hit(self):
        code, _, out = self.go(['--diff', 'origin/main'], added='the Streamly shelf')
        self.assertEqual(code, 1)

    def test_a_service_in_the_pull_request_text_is_a_hit(self):
        with tempfile.NamedTemporaryFile('w', suffix='.md', delete=False, encoding='utf-8') as f:
            f.write('Shelves for Spotify and Kindle')   # privacy: ok
        try:
            code, _, out = self.go(['--title', 'A page', '--text', f.name])
        finally:
            os.remove(f.name)
        self.assertEqual(code, 1)

    def test_a_service_in_a_branch_name_is_a_hit(self):
        code, _, _ = self.go(['--branch', 'claude/audible-shelf'])   # privacy: ok
        self.assertEqual(code, 1)

    def test_a_capitalised_brand_word_still_counts(self):
        code, _, _ = self.go(['--diff', 'origin/main'], added='the Nest thermostat')   # privacy: ok
        self.assertEqual(code, 1)

    def test_plain_words_are_not_services(self):
        code, _, out = self.go(['--diff', 'origin/main'], added='a calm, discovering walk with a nest of birds')
        self.assertEqual(code, 0, out)

    def test_an_integration_folder_may_name_its_own_service(self):
        hits = []
        S = [('Oura', re.compile(r'(?<![\w])Oura(?![\w+])', re.I))]   # privacy: ok
        pc.check_services('read the Oura API', 'diff+1', S, hits, path='plugins/bedo/skills/bedo-oura/run.sh')   # privacy: ok
        self.assertEqual(hits, [])
        pc.check_services('read the Oura API', 'diff+1', S, hits, path='plugins/bedo/skills/other/run.sh')   # privacy: ok
        self.assertEqual(len(hits), 1)

    def test_existing_files_are_not_reread_for_services(self):
        with mock.patch.object(pc, 'service_terms', mock.Mock(return_value=[])) as st:
            run([])
        st.assert_not_called()

    def test_a_fresh_start_checks_its_message(self):
        def git(*a):
            if a[0] == 'merge-base':
                raise pc.subprocess.CalledProcessError(1, 'git')
            if a[0] == 'rev-list':
                return 'abc1234\n'
            if a[0] == 'log' and any('%B' in x for x in a):
                return 'fresh start, shelves for Hulu'   # privacy: ok
            return ''
        hits = []
        with mock.patch.object(pc, 'git', git), contextlib.redirect_stderr(io.StringIO()):
            pc.check_diff('origin/main', [], hits, [('Hulu', re.compile('Hulu'))])   # privacy: ok
        self.assertTrue(any('a service someone uses' in h for h in hits), hits)

if __name__ == '__main__':
    unittest.main()
