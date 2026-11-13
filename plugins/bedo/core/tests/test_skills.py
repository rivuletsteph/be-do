# -*- coding: utf-8 -*-
"""Installed skills in step with the version store (12 Nov 2026).

    python3 core/tests/test_skills.py
"""
import os, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import bedo_skills as S  # noqa: E402

LOADER = '# x — loader\ncurl -sSL -o b.tgz https://codeload.github.com/someone/repo/tar.gz/refs/heads/main\n'
FULL = '# x\nThe whole procedure, step by step, for be•do.\n'
REPO = {'checks': {'loader': False}, 'close': {'loader': True}, 'news': {'loader': False}, 'weather': {'loader': False},
        'behind': {'loader': False}}


def tree(skills):
    d = tempfile.mkdtemp()
    for name, text in skills.items():
        os.makedirs(os.path.join(d, 'synced', 'abc', name))
        with open(os.path.join(d, 'synced', 'abc', name, 'SKILL.md'), 'w', encoding='utf-8') as f:
            f.write(text)
    return d


class Skills(unittest.TestCase):
    def setUp(self):
        self.have = S.installed(tree({'checks': LOADER, 'close': FULL, 'news': FULL, 'money': FULL,
                                      'spreadsheets': '# someone else\'s skill\n'}))
        self.st = S.states(self.have, REPO, retired=['behind'])

    def test_installed_skills_are_found_at_any_depth(self):
        self.assertEqual(sorted(self.have), ['checks', 'close', 'money', 'news', 'spreadsheets'])

    def test_a_loader_is_in_step(self):
        self.assertEqual(self.st['loader'], ['checks'])

    def test_a_full_copy_beside_a_repo_skill_is_an_older_copy(self):
        self.assertEqual(self.st['older copy'], ['close', 'news'])

    def test_one_of_ours_nowhere_in_the_repo_is_installed_only(self):
        self.assertEqual(self.st['installed only'], ['money'])

    def test_someone_elses_skill_is_not_looked_at(self):
        self.assertNotIn('spreadsheets', sum(self.st.values(), []))

    def test_not_installed_is_said_and_a_retired_skill_is_left_out(self):
        self.assertEqual(self.st['not installed'], ['weather'])

    def test_the_report_names_the_file_to_install(self):
        text = S.report(self.st, REPO)
        self.assertIn('1 of 4 installed', text)
        self.assertIn('close — replace it with plugins/bedo/skills/close/loader/SKILL.md', text)
        self.assertIn('news — no loader in the repo yet', text)
        self.assertNotIn('all in step', text)

    def test_all_loaders_is_all_in_step(self):
        st = S.states({'checks': LOADER}, {'checks': {'loader': False}})
        self.assertIn('all in step', S.report(st, {}))

    def test_the_real_repo_every_loader_names_its_own_skill(self):
        skills = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'bedo', 'skills')
        repo = S.repo_skills(skills)
        self.assertIn('bedo-checks', repo)
        for name, r in repo.items():
            if r['loader']:
                with open(os.path.join(skills, name, 'loader', 'SKILL.md'), encoding='utf-8') as f:
                    text = f.read()
                self.assertTrue(S.is_loader(text), name)
                self.assertIn(f'skills/{name}/SKILL.md', text, name)


if __name__ == '__main__':
    unittest.main(verbosity=1)
