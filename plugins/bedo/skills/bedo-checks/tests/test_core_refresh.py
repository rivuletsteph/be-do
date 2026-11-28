# -*- coding: utf-8 -*-
"""The core kept in ~/bedo-checks is main's, or it is downloaded again (27 Nov
2026). On the laptop that day `entry` crashed with `problems() got an
unexpected keyword argument 'existing'`: the runner fetched the core only when
the folder was missing, so a weeks-old copy kept running. Here the version
store is a tarball made on the spot and main's commit is given, so nothing
touches the network.

    python3 plugins/bedo/skills/bedo-checks/tests/test_core_refresh.py
"""
import io, os, pathlib, shutil, subprocess, sys, tarfile, tempfile, unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_skill_notes import working_bash  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def tarball(path, marker):
    """A version store holding only a core with one marker file."""
    with tarfile.open(path, 'w:gz') as t:
        data = marker.encode()
        info = tarfile.TarInfo('be-do-main/plugins/bedo/core/marker.txt')
        info.size = len(data)
        t.addfile(info, io.BytesIO(data))


@unittest.skipUnless(working_bash(), 'no working bash here')
class CoreRefresh(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.w = os.path.join(self.tmp, 'bedo-checks')
        self.tgz = os.path.join(self.tmp, 'b.tgz')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_core(self, sha, url=None):
        env = {k: v for k, v in os.environ.items() if k not in ('BC_CORE_SRC',)}
        env.update(BC_DIR=self.w, BC_MAIN_SHA=sha,
                   BC_STORE_URL=url or pathlib.Path(self.tgz).as_uri())
        return subprocess.run(['bash', 'run_checks.sh', 'core'], cwd=HERE, env=env,
                              capture_output=True, text=True, encoding='utf-8', timeout=120)

    def marker(self):
        with open(os.path.join(self.w, 'core', 'marker.txt'), encoding='utf-8') as f:
            return f.read()

    def stale(self, record=None):
        """A copy left from an older download, as the laptop had."""
        os.makedirs(os.path.join(self.w, 'core'))
        with open(os.path.join(self.w, 'core', 'marker.txt'), 'w', encoding='utf-8') as f:
            f.write('old')
        if record:
            with open(os.path.join(self.w, 'core', '.main_sha'), 'w', encoding='utf-8') as f:
                f.write(record)

    def test_an_old_copy_with_no_record_is_replaced(self):
        self.stale()
        tarball(self.tgz, 'new')
        r = self.run_core('a' * 40)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.marker(), 'new')
        self.assertIn('a' * 40, r.stdout)

    def test_main_moved_so_the_copy_is_replaced(self):
        self.stale(record='b' * 40)
        tarball(self.tgz, 'new')
        r = self.run_core('c' * 40)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.marker(), 'new')
        self.assertIn('refreshed bbbbbbb → ccccccc', r.stderr)

    def test_the_copy_on_main_is_kept_without_a_download(self):
        self.stale(record='d' * 40)
        r = self.run_core('d' * 40, url=pathlib.Path(self.tmp, 'missing.tgz').as_uri())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.marker(), 'old')

    def test_a_failed_download_keeps_the_copy_and_says_so(self):
        self.stale(record='e' * 40)
        r = self.run_core('f' * 40, url=pathlib.Path(self.tmp, 'missing.tgz').as_uri())
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertEqual(self.marker(), 'old')
        self.assertIn('download failed', r.stderr)

    def test_no_copy_and_no_download_stops(self):
        r = self.run_core('f' * 40, url=pathlib.Path(self.tmp, 'missing.tgz').as_uri())
        self.assertNotEqual(r.returncode, 0)

    def test_no_command_checks_only_for_the_folder(self):
        with open(os.path.join(HERE, 'run_checks.sh'), encoding='utf-8') as f:
            src = f.read()
        self.assertNotIn('[ -d "$W/core" ] || fetch_core', src)


if __name__ == '__main__':
    unittest.main()
