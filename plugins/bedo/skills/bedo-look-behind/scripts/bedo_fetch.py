# -*- coding: utf-8 -*-
"""Read the be•do bases straight from Airtable and save them as the dump files
the builders already read. Nothing personal lives here: every id comes from the
local settings file, and the token from a secrets file that never ships.

    python3 bedo_fetch.py --day YYYY-MM-DD --local look_behind_local.json \
        [--secrets bedo_secrets.json] --out .

Writes w##.json (the day's week), w##.json (the week before, when its base
exists), rhythms.json, practices.json, connections.json. Prints one line per
file. Nothing about the rows passes through a chat.

Where the token comes from, in this order:
  AIRTABLE_PAT            the environment variable, when set
  --secrets FILE          {"airtable_pat": "…"}, when the file exists
  the proxy credential    in a Claude cloud session (CLAUDE_CODE_REMOTE=true)
                          the environment carries the read-only token as an
                          API credential for api.airtable.com, and the agent
                          proxy attaches it after the request has left the
                          VM. The request goes out with NO Authorization
                          header, and the token never reaches this script,
                          the chat, or a log. BEDO_PROXY_AUTH=1 asks for the
                          same behaviour anywhere else that has such a proxy.
Nothing else: with none of the three, the run aborts before it reads.

Rules it keeps:
  I11  a read is paged to the end or the run aborts; a partial file is never
       written, so a short read cannot reach the builder.
  I13  read live on every run; no copy kept between runs.
  I14  the previous week's base is read too, and passed after the live one so
       the builder dedupes live-first (I15).
The output mirrors the Airtable MCP shape — records carry id, createdTime and
cellValuesByFieldId — so the builders need no change.
"""
import argparse, datetime as dt, json, os, sys, time, urllib.parse, urllib.request

API = 'https://api.airtable.com/v0/'
SLEEP = 0.22                      # Airtable allows five requests a second per base


def die(msg):
    sys.exit('ABORT: ' + msg)


def credential(secrets_path):
    """The token, and where it came from — or None when the proxy will attach
    it. The source is printed; the token never is."""
    pat = os.environ.get('AIRTABLE_PAT')
    if pat:
        return pat, 'AIRTABLE_PAT'
    if secrets_path and os.path.exists(secrets_path):
        try:
            return json.load(open(secrets_path, encoding='utf-8'))['airtable_pat'], secrets_path
        except (ValueError, KeyError) as ex:
            die(f'{secrets_path}: not a secrets file ({ex}) — expected {{"airtable_pat": "…"}}')
    if os.environ.get('CLAUDE_CODE_REMOTE') == 'true' or os.environ.get('BEDO_PROXY_AUTH'):
        return None, 'the environment API credential, attached by the proxy'
    die('no token in hand: set AIRTABLE_PAT, pass --secrets <file>, or run in a '
        'Claude cloud session whose environment carries the credential for api.airtable.com')


class Air:
    def __init__(self, pat):
        self.pat = pat            # None: send no Authorization header; the proxy adds one

    def get(self, path, params=None):
        url = API + path + ('?' + urllib.parse.urlencode(params, doseq=True) if params else '')
        headers = {'Authorization': 'Bearer ' + self.pat} if self.pat else {}
        req = urllib.request.Request(url, headers=headers)
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    time.sleep(SLEEP)
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:
                    time.sleep(30)
                    continue
                if e.code in (401, 403) and not self.pat:
                    # 9 Oct 2026: a Cowork day chat sent no token, nothing attached one, and the
                    # old message said "revoked or rotated?" — a hunt for a bad token that did
                    # not exist. No token sent means this surface has no Airtable access at all.
                    print(f'NO AIRTABLE ACCESS HERE: {path} came back HTTP {e.code} to a request '
                          'sent with no token, and nothing on this surface attached one (Cowork '
                          'and a plain claude.ai chat have none; a Claude Code cloud session whose '
                          'environment carries the credential does). Nothing is wrong with the '
                          'token: build here through the Airtable connector, or in Claude Code.',
                          file=sys.stderr)
                    sys.exit(3)
                if e.code in (401, 403):
                    die(f'{path}: HTTP {e.code} — token revoked or rotated? Every place that '
                        'holds it has to change together: the environment API credential, '
                        'bedo_secrets.json on each laptop, AIRTABLE_PAT where it is set. '
                        + '(this run sent the token it was given)')
                die(f'{path}: HTTP {e.code} {e.read()[:200]!r}')
            except urllib.error.URLError as e:
                die(f'{path}: cannot reach Airtable ({e.reason}) — is api.airtable.com '
                    'on the allowed domains list?')

    def bases(self):
        out, params = {}, {}
        while True:
            d = self.get('meta/bases', params)
            out.update({b['name']: b['id'] for b in d['bases']})
            if not d.get('offset'):
                return out
            params = {'offset': d['offset']}

    def tables(self, base):
        return self.get(f'meta/bases/{base}/tables')['tables']

    def records(self, base, table, field_ids):
        recs, params = [], {'pageSize': 100, 'returnFieldsByFieldId': 'true',
                            'fields[]': list(field_ids)}
        while True:
            d = self.get(f'{base}/{table}', params)
            recs += d['records']
            if not d.get('offset'):
                return recs
            params['offset'] = d['offset']


def weekno(day, zero_sunday, zero_number):
    return zero_number + (day - dt.date.fromisoformat(zero_sunday)).days // 7


def shape(recs, links=None):
    """REST records → the MCP shape the builders read. A linked field comes
    back from REST as bare ids; the MCP gives {id, name}, so names are filled
    in from `links` (id → name)."""
    out = []
    for r in recs:
        c = dict(r.get('fields') or {})
        for fid in (links or {}).get('fields', []):
            if fid in c:
                c[fid] = [{'id': x, 'name': links['names'].get(x, '')} for x in c[fid]]
        out.append({'id': r['id'], 'createdTime': r['createdTime'], 'cellValuesByFieldId': c})
    return {'records': out, 'metadata': {'totalRecordCount': len(out), 'source': 'bedo_fetch'}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--secrets', help='{"airtable_pat": "…"}; optional where AIRTABLE_PAT or '
                    'the proxy credential is in place')
    ap.add_argument('--out', default='.')
    ap.add_argument('--weekly-name', default='w{n} be•do',
                    help='how a weekly base is named; {n} is the week number')
    a = ap.parse_args()

    L = json.load(open(a.local, encoding='utf-8'))
    pat, source = credential(a.secrets)
    air = Air(pat)
    F = L['fields']
    day = dt.date.fromisoformat(a.day)
    n = weekno(day, L['week_zero_sunday'], L['week_zero_number'])
    names = air.bases()

    files = {}
    # ── the stream: this week's base, then last week's (I14), live first ──
    sf = list(dict.fromkeys(F['stream'].values()))
    for wk in (n, n - 1):
        bname = a.weekly_name.format(n=wk)
        base = names.get(bname)
        if not base:
            if wk == n:
                die(f'no base named "{bname}" — the token cannot see it, or it is not cloned yet')
            continue
        # the live week must carry every field; an older week was cloned before
        # some fields existed, so it is read for the ones it has (the key and
        # datetime at minimum), and the rest arrive empty, as they would via MCP
        tabs = air.tables(base)
        need = set(sf) if wk == n else {F['stream']['key'], F['stream']['when']}
        tab = [t for t in tabs if need <= {f['id'] for f in t['fields']}]
        if not tab:
            die(f'{bname}: no table carries the stream field ids in the local settings')
        have = [f for f in sf if f in {x['id'] for x in tab[0]['fields']}]
        files[f'w{wk}.json'] = shape(air.records(base, tab[0]['id'], have))

    # ── the reference tables ──
    for name in ('rhythms', 'practices', 'connections'):
        base, table = L.get(f'{name}_base'), L.get(f'{name}_table')
        if not (base and table):
            continue
        fids = list(dict.fromkeys(F[name].values()))
        tmeta = next((t for t in air.tables(base) if t['id'] == table), None)
        if not tmeta:
            die(f'{name}: table {table} not found in base {base}')
        types = {f['id']: f for f in tmeta['fields']}
        missing = [f for f in fids if f not in types]
        if missing:
            die(f'{name}: field ids not in the table: {missing}')
        recs = air.records(base, table, fids)
        link_f = [f for f in fids if types[f]['type'] == 'multipleRecordLinks']
        links = None
        if link_f:
            names_by_id = {}
            prim = tmeta['primaryFieldId']
            for f in link_f:
                lt = types[f]['options']['linkedTableId']
                if lt == table and prim in fids:
                    names_by_id.update({r['id']: r['fields'].get(prim, '') for r in recs})
                else:
                    ltm = next(t for t in air.tables(base) if t['id'] == lt)
                    for r in air.records(base, lt, [ltm['primaryFieldId']]):
                        names_by_id[r['id']] = r['fields'].get(ltm['primaryFieldId'], '')
            links = {'fields': link_f, 'names': names_by_id}
        files[f'{name}.json'] = shape(recs, links)

    # ── write only once every read has finished (I11) ──
    os.makedirs(a.out, exist_ok=True)
    for fn, d in files.items():
        with open(os.path.join(a.out, fn), 'w', encoding='utf-8') as fh:
            json.dump(d, fh, ensure_ascii=False)
    print(json.dumps({'day': a.day, 'week': n, 'auth': source,
                      'read': {fn.rsplit('.', 1)[0]: d['metadata']['totalRecordCount']
                               for fn, d in files.items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
