#!/usr/bin/env python3
"""Every test in the repo, one command. Each test file runs on its own, the
way it was written to; this only finds them and says which failed.

    PYTHONUTF8=1 python tools/run_tests.py
"""
import glob, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = sorted(glob.glob(os.path.join(ROOT, 'plugins', 'bedo', '**', 'tests', 'test_*.py'), recursive=True))
failed = []
for f in files:
    p = subprocess.run([sys.executable, f], capture_output=True, text=True, encoding='utf-8',
                       env=dict(os.environ, PYTHONUTF8='1'))
    name = os.path.relpath(f, ROOT)
    print(('ok    ' if p.returncode == 0 else 'FAIL  ') + name)
    if p.returncode:
        failed.append(name)
        print('\n'.join((p.stdout + p.stderr).splitlines()[-20:]))
print(f'{len(files) - len(failed)} of {len(files)} test files pass')
sys.exit(1 if failed else 0)
