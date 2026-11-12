# -*- coding: utf-8 -*-
"""The live read, for a script with a token. The token comes from the
AIRTABLE_PAT env var or a bedo_secrets.json ($BEDO_SECRETS, the working folder,
the folder above, ~/.bedo) — never the repo. In a Claude cloud session
(CLAUDE_CODE_REMOTE=true) none is held: the request goes out bare and the
environment's proxy attaches the credential. Ids come from facts_local.json.

A read pages to the end, so the count it states is its own (I11): records()
returns a dump in the reader's shape, {records, metadata.totalRecordCount}.

Calls cost money (4 Nov 2026: the free plan's monthly allowance ran out, and
the remaining list alone spent ten calls a reply). So what changes slowly is
kept on hand: the base list and table schemas for a day, a read the caller
marks slow (the catalog, the settings row, the amendments, rhythms, people)
for SLOW hours. The stream is never kept unless the caller says so. BEDO_FRESH=1
reads live and refreshes what is kept; BEDO_NO_CACHE=1 keeps nothing. Every
call that reaches Airtable is counted in ~/.bedo/air_calls.tsv (`usage`).
"""
import datetime as dt, hashlib, json, os, sys, time
import urllib.error, urllib.parse, urllib.request

from bedo_reader import die

API = 'https://api.airtable.com/v0/'
META = 24 * 3600     # the base list and table schemas: a day
SLOW = 4 * 3600      # a read the caller marks slow: the catalog, settings, amendments


def _home():
    return os.environ.get('BEDO_HOME') or os.path.join(os.path.expanduser('~'), '.bedo')


def _cache_dir():
    return os.environ.get('BEDO_CACHE') or os.path.join(_home(), 'cache')


def _stem(path):
    """The cache file's prefix: the path made safe, so a write can drop every
    kept read of its table."""
    return path.replace('/', '_')


def _cache_file(path, q):
    h = hashlib.sha1(json.dumps([path, sorted((q or {}).items())], default=str).encode()).hexdigest()[:16]
    return os.path.join(_cache_dir(), f'{_stem(path)}__{h}.json')


def _kept(path, q, ttl):
    if not ttl or os.environ.get('BEDO_NO_CACHE') or os.environ.get('BEDO_FRESH'):
        return None
    f = _cache_file(path, q)
    try:
        if time.time() - os.path.getmtime(f) < ttl:
            with open(f, encoding='utf-8') as fh:
                return json.load(fh)
    except (OSError, ValueError):
        pass
    return None


def _keep(path, q, ttl, d):
    if not ttl or os.environ.get('BEDO_NO_CACHE'):
        return
    try:
        os.makedirs(_cache_dir(), exist_ok=True)
        f = _cache_file(path, q)
        with open(f + '.tmp', 'w', encoding='utf-8') as fh:
            json.dump(d, fh, ensure_ascii=False)
        os.replace(f + '.tmp', f)
    except OSError:
        pass                                     # keeping is a saving, never a reason to stop


def forget(base, table):
    """Drop every kept read of one table, after a write to it."""
    stem = _stem(f'{base}/{table}') + '__'
    try:
        for n in os.listdir(_cache_dir()):
            if n.startswith(stem):
                os.remove(os.path.join(_cache_dir(), n))
    except OSError:
        pass


def _count(method, path):
    """One line per call that reached Airtable: when, which script, what."""
    try:
        os.makedirs(_home(), exist_ok=True)
        with open(os.path.join(_home(), 'air_calls.tsv'), 'a', encoding='utf-8') as fh:
            fh.write(f'{dt.datetime.now(dt.timezone.utc):%Y-%m-%dT%H:%M:%SZ}\t'
                     f'{os.path.basename(sys.argv[0] or "?")}\t{method}\t{path}\n')
    except OSError:
        pass


def usage(days=7, log=None):
    """Calls that reached Airtable, by day and by script, newest day first."""
    log = log or os.path.join(_home(), 'air_calls.tsv')
    by = {}
    try:
        with open(log, encoding='utf-8') as fh:
            for line in fh:
                t, script, *_ = line.rstrip('\n').split('\t')
                by.setdefault(t[:10], {}).setdefault(script, 0)
                by[t[:10]][script] += 1
    except OSError:
        return ['no calls counted here yet']
    out = []
    for d in sorted(by, reverse=True)[:days]:
        out.append(f'{d}  {sum(by[d].values()):>4} calls  · ' +
                   ' · '.join(f'{k} {v}' for k, v in sorted(by[d].items(), key=lambda x: -x[1])))
    return out


def _spent(e):
    """True when a 429 is the plan's monthly allowance, not the per-second limit:
    waiting won't bring it back, and each retry is one more refused call."""
    try:
        body = e.read().decode('utf-8', 'replace')
    except Exception:                            # noqa: BLE001
        return False
    return 'BILLING' in body.upper() or 'billing plan limit' in body


def find_token():
    """The token, or None when there is none here."""
    if os.environ.get('AIRTABLE_PAT'):
        return os.environ['AIRTABLE_PAT']
    for p in [os.environ.get('BEDO_SECRETS'), 'bedo_secrets.json', os.path.join('..', 'bedo_secrets.json'),
              os.path.join(os.path.expanduser('~'), '.bedo', 'bedo_secrets.json')]:
        if p and os.path.exists(p):
            with open(p, encoding='utf-8') as fh:
                return json.load(fh).get('airtable_pat')
    return None


def can_read():
    """True only when Airtable will actually answer. A token here is enough. A
    session that only looks like a cloud one is asked once: Cowork sets the
    same flag but carries no credential, and its proxy's request comes back 401."""
    if find_token():
        return True
    if os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        return False
    try:
        with urllib.request.urlopen(urllib.request.Request(API + 'meta/bases'), timeout=20):
            return True
    except (urllib.error.URLError, OSError):
        return False


class Air:
    def __init__(self, pat=None):
        self.pat = pat or find_token()
        if not self.pat and os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
            die('no Airtable token here — set AIRTABLE_PAT or BEDO_SECRETS, or read through the connector and pass files')

    def _headers(self, extra=None):
        h = {'Authorization': 'Bearer ' + self.pat} if self.pat else {}
        return {**h, **(extra or {})}

    def get(self, path, q=None, ttl=None):
        """One call, or none when a kept copy is fresh. The base list and schemas
        are kept a day by default; anything else only when `ttl` says so."""
        if ttl is None and path.startswith('meta/'):
            ttl = META
        d = _kept(path, q, ttl)
        if d is not None:
            return d
        url = API + path + ('?' + urllib.parse.urlencode(q, doseq=True) if q else '')
        req = urllib.request.Request(url, headers=self._headers())
        for n in range(4):
            try:
                _count('GET', path)
                with urllib.request.urlopen(req, timeout=60) as r:
                    time.sleep(.22)
                    d = json.load(r)
                    _keep(path, q, ttl, d)
                    return d
            except urllib.error.HTTPError as e:
                if e.code == 429 and _spent(e):
                    die("Airtable's monthly API allowance is spent: every call is refused until it "
                        'resets or the plan changes. Nothing was read; no retry.')
                if e.code == 429 and n < 3:
                    time.sleep(30); continue
                if e.code in (401, 403) and not self.pat:
                    die('NO TOKEN HERE: Airtable refused this session — read through the connector and pass files')
                die(f'{path}: HTTP {e.code}')

    def bases(self):
        """Every base this token sees, by NAME (I2: never an id from memory)."""
        out, q = {}, {}
        while True:
            d = self.get('meta/bases', q)
            out.update({b['name']: b['id'] for b in d['bases']})
            if not d.get('offset'):
                return out
            q = {'offset': d['offset']}

    def table(self, base, table):
        return next(t for t in self.get(f'meta/bases/{base}/tables')['tables'] if t['id'] == table)

    def records(self, base, table, formula=None, by_id=False, ttl=None, **extra):
        """Every record, paged to the end. `formula` is a filterByFormula;
        by_id keys cells by field id, the way facts_local names them; `ttl`
        keeps the read that many seconds (SLOW for a table that rarely changes)."""
        recs, q = [], {'pageSize': 100, **extra}
        if formula:
            q['filterByFormula'] = formula
        if by_id:
            q['returnFieldsByFieldId'] = 'true'
        path = f'{base}/{table}'
        kept = _kept(path, q, ttl)               # the whole read is kept, never a page of it
        if kept is not None:
            return kept
        key = dict(q)
        while True:
            d = self.get(path, q)
            recs += d['records']
            if not d.get('offset'):
                _keep(path, key, ttl, recs)
                return recs
            q['offset'] = d['offset']

    def patch(self, base, table, updates):
        """Update fields in place, ten records a call (Airtable's limit)."""
        for i in range(0, len(updates), 10):
            body = json.dumps({'records': updates[i:i + 10]}).encode()
            req = urllib.request.Request(API + f'{base}/{table}', data=body, method='PATCH',
                                         headers=self._headers({'Content-Type': 'application/json'}))
            forget(base, table)
            _count('PATCH', f'{base}/{table}')
            try:
                with urllib.request.urlopen(req, timeout=60):
                    time.sleep(.22)
            except urllib.error.HTTPError as e:
                die(f'{base}/{table}: PATCH HTTP {e.code}')

    def dump(self, base, table, **kw):
        recs = self.records(base, table, **kw)
        return {'records': recs, 'metadata': {'totalRecordCount': len(recs)}}


def day_bounds(local, day):
    """The UTC instants a local day runs between, from the zone on that day."""
    from bedo_reader import offset_hours
    noon = dt.datetime(day.year, day.month, day.day, 12, tzinfo=dt.timezone.utc)
    start = dt.datetime(day.year, day.month, day.day, tzinfo=dt.timezone.utc) - dt.timedelta(hours=offset_hours(local, noon))
    return start, start + dt.timedelta(days=1)


def _z(t):
    return t.strftime('%Y-%m-%dT%H:%M:%S.000Z')


def read_day(air, local, day, names=None, ttl=None):
    """The filtered read of one local day's stream rows, from the base whose
    week holds that day, resolved by name. Returns (dump, base name). Never
    kept unless `ttl` says so: today's rows change every reply."""
    from bedo_entry import week_number
    names = names or air.bases()
    want = local.get('weekly_name', 'w{n} be•do').format(n=week_number(day))
    base = names.get(want) or die(f'no base named {want}')
    a, b = day_bounds(local, day)
    f = local['stream_fields']['datetime']
    formula = (f"AND(NOT(IS_BEFORE({{{f}}}, DATETIME_PARSE('{_z(a)}'))), "
               f"IS_BEFORE({{{f}}}, DATETIME_PARSE('{_z(b)}')))")
    return air.dump(base, local['stream_table'], formula=formula, by_id=True, ttl=ttl), want


def read_catalog(air, local):
    """The practices catalog, keyed the way facts_local names its fields: by id
    when it lists practices_fields (as a connector read is), else by name.
    Kept SLOW hours: the remaining list reads it every reply, and it changes
    only when she adds or moves a practice (BEDO_FRESH=1 after that)."""
    base, table = local['bases']['practices']
    return air.dump(base, table, by_id=bool(local.get('practices_fields')), ttl=SLOW)


def read_week_links(air, local, day, names=None):
    """The week's stream rows whose photo links are filled, from the base whose
    week holds that day: what the photo dedupe keeps (28 Oct 2026)."""
    from bedo_entry import week_number
    names = names or air.bases()
    want = local.get('weekly_name', 'w{n} be•do').format(n=week_number(day))
    base = names.get(want) or die(f'no base named {want}')
    f = local['stream_fields'].get('photo_links') or die('facts_local stream_fields has no photo_links id')
    return air.dump(base, local['stream_table'], formula=f'LEN({{{f}}}&"")>0', by_id=True)


if __name__ == '__main__':
    # python3 bedo_air.py usage [days] — the calls that reached Airtable from here
    if len(sys.argv) > 1 and sys.argv[1] == 'usage':
        print('\n'.join(usage(int(sys.argv[2]) if len(sys.argv) > 2 else 7)))
    else:
        sys.exit('usage: bedo_air.py usage [days]')
