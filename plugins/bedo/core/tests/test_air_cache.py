# -*- coding: utf-8 -*-
"""What the Airtable calls cost (4 Nov 2026). The free plan's month ran out
on the 4th: the remaining list spent ten calls a reply re-reading the catalog,
the settings row and the base list, and a spent allowance was retried three
more times. Each test is one of those. Every row is invented.

    python3 plugins/bedo/core/tests/test_air_cache.py
"""
import io, json, os, sys, tempfile, unittest, urllib.error
from unittest import mock

CORE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CORE)
import bedo_air as A  # noqa: E402


class Reply(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def answers(*pages):
    """A fake urlopen that hands out these pages in order and counts the calls."""
    calls = []

    def urlopen(req, timeout=None):
        calls.append(req.full_url)
        return Reply(json.dumps(pages[min(len(calls), len(pages)) - 1]).encode())
    return urlopen, calls


class Home(unittest.TestCase):
    def setUp(self):
        self.env = mock.patch.dict(os.environ, {'BEDO_HOME': tempfile.mkdtemp(), 'CLAUDE_CODE_REMOTE': 'true'})
        self.env.start()
        for k in ('BEDO_FRESH', 'BEDO_NO_CACHE', 'BEDO_CACHE'):
            os.environ.pop(k, None)
        self.sleep = mock.patch('time.sleep')
        self.sleep.start()

    def tearDown(self):
        self.sleep.stop()
        self.env.stop()


class Kept(Home):
    def test_the_base_list_is_read_once_a_day(self):
        # remaining asked for meta/bases three times in one run
        urlopen, calls = answers({'bases': [{'name': 'w45 be•do', 'id': 'appX'}]})
        with mock.patch('urllib.request.urlopen', urlopen), mock.patch.object(A, 'find_token', return_value=None):
            for _ in range(3):
                self.assertEqual(A.Air().bases(), {'w45 be•do': 'appX'})
        self.assertEqual(len(calls), 1)

    def test_a_slow_read_is_kept_whole_and_the_stream_never(self):
        page1 = {'records': [{'id': 'rec1'}], 'offset': 'o1'}
        page2 = {'records': [{'id': 'rec2'}]}
        urlopen, calls = answers(page1, page2, page1, page2, page1, page2)
        with mock.patch('urllib.request.urlopen', urlopen), mock.patch.object(A, 'find_token', return_value=None):
            air = A.Air()
            for _ in range(2):    # the catalog, every reply: both pages once
                self.assertEqual([r['id'] for r in air.records('appC', 'tblCat', ttl=A.SLOW)], ['rec1', 'rec2'])
            self.assertEqual(len(calls), 2)
            for _ in range(2):    # today's stream: live every time
                air.records('appW', 'tblStream')
            self.assertEqual(len(calls), 6)

    def test_fresh_reads_live_and_a_write_forgets_its_table(self):
        urlopen, calls = answers({'records': [{'id': 'rec1'}]})
        with mock.patch('urllib.request.urlopen', urlopen), mock.patch.object(A, 'find_token', return_value=None):
            air = A.Air()
            air.records('appC', 'tblCat', ttl=A.SLOW)
            with mock.patch.dict(os.environ, {'BEDO_FRESH': '1'}):
                air.records('appC', 'tblCat', ttl=A.SLOW)
            self.assertEqual(len(calls), 2)
            air.records('appC', 'tblCat', ttl=A.SLOW)          # refreshed above: kept
            self.assertEqual(len(calls), 2)
            air.patch('appC', 'tblCat', [{'id': 'rec1', 'fields': {}}])
            air.records('appC', 'tblCat', ttl=A.SLOW)          # written since: read again
            self.assertEqual(len(calls), 4)

    def test_every_call_that_reaches_airtable_is_counted(self):
        urlopen, _ = answers({'bases': []})
        with mock.patch('urllib.request.urlopen', urlopen), mock.patch.object(A, 'find_token', return_value=None):
            A.Air().bases()
            A.Air().bases()                                     # kept: not a call
        lines = A.usage()
        self.assertEqual(len(lines), 1)
        self.assertIn('   1 calls', lines[0])


class Spent(Home):
    def test_a_spent_month_stops_at_once(self):
        body = b'{"errors":[{"error":"PUBLIC_API_BILLING_LIMIT_EXCEEDED","message":"billing plan limit exceeded"}]}'
        calls = []

        def refused(req, timeout=None):
            calls.append(1)
            raise urllib.error.HTTPError(req.full_url, 429, 'Too Many Requests', {}, io.BytesIO(body))
        with mock.patch('urllib.request.urlopen', refused), mock.patch.object(A, 'find_token', return_value=None):
            with self.assertRaises(SystemExit) as e:
                A.Air().get('appW/tblStream')
        self.assertEqual(len(calls), 1)
        self.assertIn('monthly API allowance', str(e.exception))

    def test_the_per_second_limit_still_waits_and_retries(self):
        calls = []

        def busy(req, timeout=None):
            calls.append(1)
            if len(calls) == 1:
                raise urllib.error.HTTPError(req.full_url, 429, 'Too Many Requests', {},
                                             io.BytesIO(b'{"errors":[{"error":"RATE_LIMIT_REACHED"}]}'))
            return Reply(b'{"records": []}')
        with mock.patch('urllib.request.urlopen', busy), mock.patch.object(A, 'find_token', return_value=None):
            self.assertEqual(A.Air().get('appW/tblStream'), {'records': []})
        self.assertEqual(len(calls), 2)


if __name__ == '__main__':
    unittest.main()
