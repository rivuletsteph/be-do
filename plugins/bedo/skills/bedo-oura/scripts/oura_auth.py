# -*- coding: utf-8 -*-
"""Oura's sign-in, done once by the user, and its renewal after, done by itself.

Oura ended personal access tokens at the end of 2025; the API now takes only an app's
sign-in (OAuth2). The user registers a small app of her own once, approves it in her
Oura account, and from then on this file keeps the sign-in alive: an access token lasts
about 30 days, and each renewal hands back a new single-use refresh token, which is
saved before anything else happens. Lose the latest one and the sign-in is done again.

    python oura_auth.py            # sign in: asks for the app's id and secret the first
                                   # time, opens the Oura page, catches the answer
    python oura_auth.py --check    # who is signed in and until when; renews if near the end
    python oura_auth.py --cloud    # renews now and puts the key on the clipboard, never the
                                   # screen, for the cloud environment's Oura credential

Where things live, outside the repo, never shipped:
  bedo_secrets.json   oura_client_id, oura_client_secret (beside airtable_pat)
  oura_tokens.json    the access and refresh tokens and when they end
both in ~/.bedo, or BEDO_SECRETS and OURA_TOKENS pointing elsewhere.

The app's redirect URI must be registered as exactly http://localhost:8765/callback.
"""
import argparse, getpass, subprocess, http.server, json, os, secrets, sys, time, urllib.error, urllib.parse, urllib.request, webbrowser

AUTH = 'https://cloud.ouraring.com/oauth/authorize'
TOKEN = 'https://api.ouraring.com/oauth/token'
SCOPES = 'email personal daily heartrate workout tag session spo2 stress heart_health'   # as the portal names them
PORT = 8765
REDIRECT = f'http://localhost:{PORT}/callback'
HOME = os.path.join(os.path.expanduser('~'), '.bedo')
SECRETS = os.environ.get('BEDO_SECRETS') or os.path.join(HOME, 'bedo_secrets.json')
TOKENS = os.environ.get('OURA_TOKENS') or os.path.join(HOME, 'oura_tokens.json')
RENEW_WITHIN = 2 * 86400          # renew when under two days are left


def die(m):
    sys.exit('ABORT: ' + m)


def _read(p):
    return json.load(open(p, encoding='utf-8')) if os.path.exists(p) else {}


def _write(p, d):
    """Whole file or nothing: a refresh token half-written is a sign-in lost."""
    os.makedirs(os.path.dirname(p) or '.', exist_ok=True)
    tmp = p + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=1)
    os.replace(tmp, p)


def undouble(v):
    """A Windows terminal can paste twice (right-click, then Ctrl+V); 22 Oct 2026 it did."""
    h = len(v) // 2
    return v[:h] if len(v) % 2 == 0 and h and v[:h] == v[h:] else v


def app(ask=False):
    s = _read(SECRETS)
    cid, sec = s.get('oura_client_id'), s.get('oura_client_secret')
    if cid and sec:
        return cid, sec
    if not ask:
        die(f'no Oura app in {SECRETS} — run oura_auth.py once to sign in')
    print('The Oura app\'s Client ID and Client Secret, from developer.ouraring.com/applications.')
    cid = undouble(input('Client ID: ').strip())
    sec = undouble(getpass.getpass('Client Secret (not shown): ').strip())
    if not (cid and sec):
        die('both are needed')
    s.update(oura_client_id=cid, oura_client_secret=sec)
    _write(SECRETS, s)
    return cid, sec


def _post(form):
    req = urllib.request.Request(TOKEN, data=urllib.parse.urlencode(form).encode(),
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8', 'replace')[:200]
        die(f'Oura refused the sign-in ({e.code}: {body}) — run oura_auth.py to sign in again')
    except (urllib.error.URLError, OSError) as e:
        die(f'Oura unreachable ({e})')


def _save(tok):
    tok['expires_at'] = int(time.time()) + int(tok.get('expires_in') or 0)
    _write(TOKENS, tok)
    return tok


def sign_in():
    cid, sec = app(ask=True)
    state = secrets.token_urlsafe(16)
    got = {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            got.update({k: v[0] for k, v in q.items()})
            ok = got.get('state') == state and 'code' in got
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(('<p>Oura is connected to be•do. You can close this tab.</p>' if ok else
                              f'<p>Oura did not connect: {got.get("error", "no answer")}.</p>').encode())

        def log_message(self, *a):
            pass

    url = AUTH + '?' + urllib.parse.urlencode(dict(response_type='code', client_id=cid, redirect_uri=REDIRECT,
                                                   scope=SCOPES, state=state))
    srv = http.server.HTTPServer(('localhost', PORT), H)
    print('Opening Oura to approve be•do. If no browser opens, go to:\n' + url)
    webbrowser.open(url)
    srv.timeout = 300
    srv.handle_request()
    srv.server_close()
    if got.get('state') != state or 'code' not in got:
        die(f'no approval came back ({got.get("error") or "timed out"})')
    tok = _save(_post(dict(grant_type='authorization_code', code=got['code'], redirect_uri=REDIRECT,
                           client_id=cid, client_secret=sec)))
    print(f'Signed in. Scopes: {tok.get("scope")}. Renews by itself; next renewal by '
          f'{time.strftime("%d %b %Y", time.localtime(tok["expires_at"] - RENEW_WITHIN))}.')


def access_token(force=False):
    """A live access token, renewed first when near its end (or now, with force); None
    when never signed in."""
    tok = _read(TOKENS)
    if not tok.get('access_token'):
        return None
    if not force and tok.get('expires_at', 0) - time.time() > RENEW_WITHIN:
        return tok['access_token']
    if not tok.get('refresh_token'):
        die('the Oura sign-in has ended and cannot renew — run oura_auth.py to sign in again')
    cid, sec = app()
    new = _post(dict(grant_type='refresh_token', refresh_token=tok['refresh_token'], client_id=cid, client_secret=sec))
    new.setdefault('refresh_token', tok['refresh_token'])
    return _save(new)['access_token']


def cloud():
    """The cloud can't keep a renewing sign-in, so it carries a copy of the key, pasted
    into its environment by the user, about monthly (her choice, 23 Oct 2026). The laptop
    renews two days before the key ends, which may retire the copy, so the paste is due
    by then; renewing here starts both clocks again."""
    t = access_token(force=True)
    if not t:
        die('not signed in — run oura_auth.py')
    copy = {'win32': ['clip'], 'darwin': ['pbcopy']}.get(sys.platform, ['xclip', '-selection', 'clipboard'])
    try:
        subprocess.run(copy, input=t.encode('ascii'), check=True)
    except (OSError, subprocess.CalledProcessError) as e:
        die(f'could not reach the clipboard ({e})')
    due = _read(TOKENS)['expires_at'] - RENEW_WITHIN
    print('The Oura key is on the clipboard. Paste it as the cloud environment credential for api.ouraring.com.')
    print(f'Paste a fresh one by {time.strftime("%a %d %b %Y", time.localtime(due))}: python oura_auth.py --cloud')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--cloud', action='store_true')
    a = ap.parse_args()
    if a.cloud:
        return cloud()
    if not a.check:
        return sign_in()
    t = access_token()
    if not t:
        die('not signed in — run oura_auth.py')
    tok = _read(TOKENS)
    req = urllib.request.Request('https://api.ouraring.com/v2/usercollection/personal_info',
                                 headers={'Authorization': 'Bearer ' + t})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            json.load(r)
    except urllib.error.HTTPError as e:
        die(f'Oura said {e.code} — run oura_auth.py to sign in again')
    print(f'Signed in to Oura until {time.strftime("%d %b %Y", time.localtime(tok["expires_at"]))}; renews by itself.')


if __name__ == '__main__':
    main()
