# -*- coding: utf-8 -*-
"""The builders' Airtable reader counts its calls (11 Nov 2026).

core/bedo_air.py logs every call the checks make, and `run_checks.sh usage`
adds them up. bedo_fetch.py, which reads for the my day page and for Oura, is
a reader of its own and logged nothing, so the usage line left out the page
builds altogether. It writes the same line to the same file now.

    python3 tests/test_fetch_count.py
"""
import io, json, os, sys, tempfile, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(HERE))), 'core'))
import bedo_fetch as bf  # noqa: E402
import bedo_air  # noqa: E402


class Page(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def answer(pages):
    it = iter(pages)

    def urlopen(req, timeout=None):
        return Page(json.dumps(next(it)).encode())
    return urlopen


def main():
    bf.SLEEP = 0
    home = tempfile.mkdtemp()
    os.environ['BEDO_HOME'] = home
    log = os.path.join(home, 'air_calls.tsv')

    # a read of two pages is two calls, each on its own line, in the checks' format
    urllib.request.urlopen = answer([{'records': [{'id': 'a'}], 'offset': 'x'}, {'records': [{'id': 'b'}]}])
    recs = bf.Air('a-token').records('appX', 'tblY', ['fld1'])
    assert [r['id'] for r in recs] == ['a', 'b'], recs
    lines = open(log, encoding='utf-8').read().splitlines()
    assert len(lines) == 2, lines
    when, script, method, path = lines[0].split('\t')
    assert when.endswith('Z') and method == 'GET' and path == 'appX/tblY', lines[0]
    assert 'a-token' not in open(log, encoding='utf-8').read()          # the token never reaches the log

    # the checks' own usage reads them: one count, both readers
    out = bedo_air.usage(log=log)
    assert len(out) == 1 and ' 2 calls' in out[0], out

    # a log that can't be written never stops a read
    os.environ['BEDO_HOME'] = os.path.join(log, 'not-a-folder')      # a file where the folder should be
    urllib.request.urlopen = answer([{'bases': [{'name': 'n', 'id': 'i'}]}])
    assert bf.Air('a-token').bases() == {'n': 'i'}
    print('ok: the builders\' reader counts its calls where the checks do')


if __name__ == '__main__':
    main()
