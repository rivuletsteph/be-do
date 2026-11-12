"""The checks skill stays short, and every command it names has its notes.

The skill file is read at every chat's start; each command's notes
(commands/NAME.md) are read only before that command's first run, with
`run_checks.sh how NAME`."""
import os, re, shutil, subprocess, unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(HERE, 'SKILL.md')
NOTES = os.path.join(HERE, 'commands')
RUNNER = os.path.join(HERE, 'run_checks.sh')


def read(p):
    with open(p, encoding='utf-8') as f:
        return f.read()


def working_bash():
    """A bash that really runs: on a Windows machine the first `bash` can be the
    WSL launcher, which exists and runs nothing when no distro is installed."""
    if not shutil.which('bash'):
        return False
    try:
        r = subprocess.run(['bash', '-c', 'echo ok'], capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.SubprocessError):
        return False
    return r.returncode == 0 and r.stdout.strip() == 'ok'


def table_commands():
    """The command name in every row of the skill's tables."""
    out = []
    for line in read(SKILL).split('\n'):
        cells = line.strip().strip('|').split(' | ', 2)
        if line.startswith('| ') and len(cells) == 3:
            m = re.match(r'`(\w+)', cells[1].strip())
            if m:
                out.append(m.group(1))
    return out


class Notes(unittest.TestCase):
    def test_the_always_read_file_stays_short(self):
        self.assertLess(len(read(SKILL).split()), 1600, 'the skill file every chat reads has grown: '
                        "a command's detail belongs in commands/NAME.md")

    def test_every_command_in_the_tables_has_its_notes(self):
        names = table_commands()
        self.assertGreaterEqual(len(names), 17)
        for n in names:
            self.assertTrue(os.path.exists(os.path.join(NOTES, n + '.md')), f'no notes for {n}')

    def test_every_notes_file_is_a_command_the_runner_knows(self):
        runner = read(RUNNER)
        for f in os.listdir(NOTES):
            n = f[:-3]
            if n == 'no-token':
                continue
            self.assertRegex(runner, r'\n  (?:\w+\|)*' + n + r'(?:\|\w+)*\)', f'{n} has notes but the runner has no such command')

    def test_the_runner_points_a_command_at_its_notes(self):
        runner = read(RUNNER)
        self.assertIn('how $CMD', runner)
        self.assertIn('how no-token', runner)

    @unittest.skipUnless(working_bash(), 'no working bash here')
    def test_how_prints_the_notes_and_refuses_an_unknown_name(self):
        def how(*a):
            return subprocess.run(['bash', 'run_checks.sh', 'how', *a], cwd=HERE, capture_output=True,
                                  text=True, encoding='utf-8')
        r = how('order')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), read(os.path.join(NOTES, 'order.md')).strip())
        r = how('no-such-command')
        self.assertEqual(r.returncode, 1)
        self.assertIn('dayqa', r.stdout)


if __name__ == '__main__':
    unittest.main()
