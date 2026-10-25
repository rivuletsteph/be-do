# -*- coding: utf-8 -*-
"""What a 401 means depends on whether a token was sent (9 Oct 2026).

A Cowork day chat sent no token, nothing attached one, and the fetch said
"token revoked or rotated?" — a hunt for a bad token that did not exist. With
no token sent, a 401 means this surface has no Airtable access: exit 3, the
runners' no-token path. With a token sent, it is still an abort.

    python3 tests/test_fetch_auth.py
"""
import contextlib, io, os, sys, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import bedo_fetch as bf  # noqa: E402


def refuse(code):
    def urlopen(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, code, 'no', {}, io.BytesIO(b'{}'))
    return urlopen


def run(pat, code):
    urllib.request.urlopen = refuse(code)
    err = io.StringIO()
    try:
        with contextlib.redirect_stderr(err):
            bf.Air(pat).get('meta/bases')
    except SystemExit as ex:
        return ex.code, err.getvalue()
    raise AssertionError('no exit')


def main():
    for code in (401, 403):
        rc, err = run(None, code)
        assert rc == 3, rc
        assert 'NO AIRTABLE ACCESS HERE' in err and 'revoked' not in err, err
        rc, _ = run('a-token', code)
        assert isinstance(rc, str) and rc.startswith('ABORT:') and 'revoked or rotated' in rc, rc
        assert 'sent the token it was given' in rc, rc
    print('ok — no token sent: no access here, exit 3; a token sent: revoked or rotated')


if __name__ == '__main__':
    main()
