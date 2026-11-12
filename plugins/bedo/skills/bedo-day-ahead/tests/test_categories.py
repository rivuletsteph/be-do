#!/usr/bin/env python3
"""The page sorts her time with the day QA's own categories, in the runner's
folder too. Until 11 Nov 2026 prep never copied day_rings.py, so flow.py fell
back, without a word, to a short list of its own: in the repo (where the tests
ran) the real sets loaded, and in her working folder they didn't.

    PYTHONUTF8=1 python3 tests/test_categories.py
"""
import glob, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BEDO = os.path.dirname(os.path.dirname(SKILL))
RINGS = os.path.join(BEDO, 'skills', 'bedo-week-look-behind', 'scripts', 'day_rings.py')


def runner_folder(with_rings):
    """The working folder as `prep` lays it out: scripts/ holds this skill's scripts, the core and
    day_rings.py; assets/ beside it holds the shared asset folders (base-flow, and any that join it)."""
    d = tempfile.mkdtemp()
    scripts = os.path.join(d, 'scripts')
    os.makedirs(scripts)
    for f in glob.glob(os.path.join(SKILL, 'scripts', '*.py')) + glob.glob(os.path.join(BEDO, 'core', '*.py'))             + [os.path.join(BEDO, 'core', 'facts.json')] + ([RINGS] if with_rings else []):
        shutil.copy(f, scripts)
    for a in glob.glob(os.path.join(BEDO, 'assets', '*', '')):
        shutil.copytree(a, os.path.join(d, 'assets', os.path.basename(os.path.dirname(a))))
    return scripts


def load(folder):
    code = ('import flow, sys; n = sys.modules.get("day_rings"); '
            'print("same" if n and flow.PERSONAL is n.PERSONAL and flow.RECREATION is n.RECREATION else "fallback")')
    return subprocess.run([sys.executable, '-c', code], cwd=folder, capture_output=True, text=True, encoding='utf-8',
                          env=dict(os.environ, PYTHONUTF8='1'))


def main():
    # prep copies the file, and loudly: no `|| true` on that line
    sh = open(os.path.join(SKILL, 'run_day_ahead.sh'), encoding='utf-8').read()
    line = next((l for l in sh.splitlines() if re.match(r'\s*cp .*day_rings\.py scripts/', l)), None)
    assert line, 'prep does not copy day_rings.py into scripts/'
    assert '|| true' not in line, 'a failed copy of day_rings.py must stop prep'

    # in the runner's folder the page reads the QA's own sets, and says nothing
    r = load(runner_folder(True))
    assert r.stdout.strip() == 'same', (r.stdout, r.stderr[-400:])
    assert 'WARNING' not in r.stderr, r.stderr

    # without the file it still builds, on the short list, and says so
    r = load(runner_folder(False))
    assert r.stdout.strip() == 'fallback', (r.stdout, r.stderr[-400:])
    assert 'WARNING: day_rings.py could not be loaded' in r.stderr, r.stderr
    print('ok: the page sorts time with the day QA\'s categories; a missing copy is said out loud')


if __name__ == '__main__':
    main()
