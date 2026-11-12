# -*- coding: utf-8 -*-
"""The day ahead's scripts across the 1 Nov 2026 clock change (10 Nov 2026: the
branch had to patch its own day_ahead_local.json from -5 to -6 again). Each
reads time_zone for the instant or day in hand; the settings below keep the
stale summer number on purpose, so a script still reading it fails here.

    python3 tests/test_clock_change.py
"""
import datetime as dt, io, json, os, subprocess, sys, tempfile, unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), 'scripts')
sys.path.insert(0, SCRIPTS)
import day_ahead as da  # noqa: E402
import bedo_cal  # noqa: E402
import ledger  # noqa: E402
import day_heart  # noqa: E402
import bedo_clock  # noqa: E402

UTC = dt.timezone.utc
L = {'time_zone': 'America/Chicago', 'utc_offset_hours': -5}


class DayAhead(unittest.TestCase):
    def setUp(self):
        da.CLOCK.clear()
        da.CLOCK.update(L)

    def test_local_on_each_side(self):
        self.assertEqual(da.local('2026-10-31T14:00:00.000Z'), dt.datetime(2026, 10, 31, 9))
        self.assertEqual(da.local('2026-11-02T15:00:00.000Z'), dt.datetime(2026, 11, 2, 9))

    def test_a_today_row_written_back_in_utc(self):
        self.assertEqual(da.to_utc(dt.datetime(2026, 10, 31, 9)), '2026-10-31T14:00:00.000Z')
        self.assertEqual(da.to_utc(dt.datetime(2026, 11, 2, 9)), '2026-11-02T15:00:00.000Z')

    def test_no_offset_check_left_to_tell_her_to_edit_a_number(self):
        self.assertFalse(hasattr(da, 'offset_check'))


class Calendar(unittest.TestCase):
    def test_a_window_across_the_change_has_each_ends_offset(self):
        start, end, off = bedo_cal.window(L, dt.date(2026, 10, 25), 14)
        self.assertEqual((start, end), (dt.datetime(2026, 10, 25), dt.datetime(2026, 11, 8)))
        self.assertEqual(off, ('-05:00', '-06:00'))

    def test_a_window_after_the_change(self):
        self.assertEqual(bedo_cal.window(L, dt.date(2026, 11, 10), 14)[2], ('-06:00', '-06:00'))


class Ledger(unittest.TestCase):
    def test_a_csv_time_on_each_side(self):
        off = bedo_clock.Offset(L)
        self.assertEqual(ledger.utc('October 31, 2026 9:00am', off), '2026-10-31T14:00:00.000Z')
        self.assertEqual(ledger.utc('November 2, 2026 9:00am', off), '2026-11-02T15:00:00.000Z')


class Heart(unittest.TestCase):
    def _window(self, day):
        seen = []

        def fake(req, timeout=None):
            seen.append(req.full_url)
            return io.BytesIO(b'{"data": []}')
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, 'local.json')
            json.dump(L, open(p, 'w'))
            with mock.patch.object(day_heart.urllib.request, 'urlopen', fake), \
                    mock.patch.object(sys, 'argv', ['day_heart', '--day', day, '--local', p,
                                                     '--out', os.path.join(d, 'o.json')]):
                day_heart.main()
        q = dict(x.split('=') for x in seen[0].split('?')[1].split('&'))
        return q['start_datetime'].replace('%3A', ':'), q['end_datetime'].replace('%3A', ':')

    def test_the_local_day_on_each_side(self):
        self.assertEqual(self._window('2026-10-31'), ('2026-10-31T05:00:00Z', '2026-11-01T05:00:00Z'))
        self.assertEqual(self._window('2026-11-01'), ('2026-11-01T05:00:00Z', '2026-11-02T06:00:00Z'))
        self.assertEqual(self._window('2026-11-02'), ('2026-11-02T06:00:00Z', '2026-11-03T06:00:00Z'))


class Digest(unittest.TestCase):
    def test_the_digest_reads_each_day_on_its_own_clock(self):
        F = dict(title='fT', key='fK', when='fW', end='fE', status='fS', practice='fP', details='fD', person='fPe')
        recs = [{'id': 'r1', 'createdTime': '2026-11-02T15:00:00.000Z',
                 'cellValuesByFieldId': {'fT': 'tea', 'fW': '2026-11-02T15:00:00.000Z', 'fS': '● lived',
                                         'fP': '🍵 tea'}},
                {'id': 'r2', 'createdTime': '2026-10-31T14:00:00.000Z',
                 'cellValuesByFieldId': {'fT': 'coffee', 'fW': '2026-10-31T14:00:00.000Z', 'fS': '● lived',
                                         'fP': '☕ coffee'}}]
        with tempfile.TemporaryDirectory() as d:
            lp, sp = os.path.join(d, 'local.json'), os.path.join(d, 'stream.json')
            json.dump(dict(L, fields={'stream': F}), open(lp, 'w'))
            json.dump({'records': recs, 'metadata': {'totalRecordCount': 2}}, open(sp, 'w'))
            run = lambda day: subprocess.run(  # noqa: E731
                [sys.executable, os.path.join(SCRIPTS, 'day_digest.py'), '--day', day, '--local', lp, '--stream', sp],
                capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, PYTHONUTF8='1')).stdout
            self.assertIn('09:00', run('2026-10-31'))
            self.assertIn('coffee', run('2026-10-31'))
            self.assertIn('09:00', run('2026-11-02'))
            self.assertIn('tea', run('2026-11-02'))


if __name__ == '__main__':
    unittest.main()
