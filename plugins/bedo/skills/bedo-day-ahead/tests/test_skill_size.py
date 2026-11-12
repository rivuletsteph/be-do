"""The day-ahead skill holds the procedure a chat reads every morning; what the
page draws lives in PAGE.md, which a build does not load."""
import os, unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(HERE, name), encoding='utf-8') as f:
        return f.read()


class SkillSize(unittest.TestCase):
    def test_the_skill_stays_procedure_sized(self):
        self.assertLess(len(read('SKILL.md').split()), 6500,
                        'the skill read every morning has grown: what the page draws belongs in PAGE.md')

    def test_the_skill_points_at_the_page_file(self):
        self.assertIn('`PAGE.md`', read('SKILL.md'))
        self.assertIn("Don't read it to build", read('SKILL.md'))

    def test_the_page_file_holds_the_three_sections(self):
        page = read('PAGE.md')
        for head in ('## What the page shows, in order', '## How things flow', '## Saturday and Sunday have their own shape'):
            self.assertIn(head, page)
            self.assertNotIn(head, read('SKILL.md'))


if __name__ == '__main__':
    unittest.main()
