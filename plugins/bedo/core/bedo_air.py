# -*- coding: utf-8 -*-
"""The live read, for a script with a token. The token comes from the
AIRTABLE_PAT env var or a bedo_secrets.json ($BEDO_SECRETS, the working folder,
the folder above, ~/.bedo) — never the repo. In a Claude cloud session
(CLAUDE_CODE_REMOTE=true) none is held: the request goes out bare and the
environment's proxy attaches the credential. Ids come from facts_local.json.

A read pages to the end, so the count it states is its own (I11): records()
returns a dump in the reader's shape, {records, metadata.totalRecordCount}.
"""
import datetime as dt, json, os, time
import urllib.error, urllib.parse, urllib.request

from bedo_reader import die

API = 'https://api.airtable.com/v0/'


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
    return bool(find_token()) or os.environ.get('CLAUDE_CODE_REMOTE') == 'true'


class Air:
    def __init__(self, pat=None):
        self.pat = pat or find_token()
        if not self.pat and os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
            die('no Airtable token here — set AIRTABLE_PAT or BEDO_SECRETS, or read through the connector and pass files')

    def _headers(self, extra=None):
        h = {'Authorization': 'Bearer ' + self.pat} if self.pat else {}
        return {**h, **(extra or {})}

    def get(self, path, q=None):
        url = API + path + ('?' + urllib.parse.urlencode(q, doseq=True) if q else '')
        req = urllib.request.Request(url, headers=self._headers())
        for n in range(4):
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    time.sleep(.22)
                    return json.load(r)
            except urllib.error.HTTPError as e:
                if e.code == 429 and n < 3:
                    time.sleep(30); continue
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

    def records(self, base, table, formula=None, by_id=False, **extra):
        """Every record, paged to the end. `formula` is a filterByFormula;
        by_id keys cells by field id, the way facts_local names them."""
        recs, q = [], {'pageSize': 100, **extra}
        if formula:
            q['filterByFormula'] = formula
        if by_id:
            q['returnFieldsByFieldId'] = 'true'
        while True:
            d = self.get(f'{base}/{table}', q)
            recs += d['records']
            if not d.get('offset'):
                return recs
            q['offset'] = d['offset']

    def patch(self, base, table, updates):
        """Update fields in place, ten records a call (Airtable's limit)."""
        for i in range(0, len(updates), 10):
            body = json.dumps({'records': updates[i:i + 10]}).encode()
            req = urllib.request.Request(API + f'{base}/{table}', data=body, method='PATCH',
                                         headers=self._headers({'Content-Type': 'application/json'}))
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


def read_day(air, local, day, names=None):
    """The filtered read of one local day's stream rows, from the base whose
    week holds that day, resolved by name. Returns (dump, base name)."""
    from bedo_entry import week_number
    names = names or air.bases()
    want = local.get('weekly_name', 'w{n} be•do').format(n=week_number(day))
    base = names.get(want) or die(f'no base named {want}')
    a, b = day_bounds(local, day)
    f = local['stream_fields']['datetime']
    formula = (f"AND(NOT(IS_BEFORE({{{f}}}, DATETIME_PARSE('{_z(a)}'))), "
               f"IS_BEFORE({{{f}}}, DATETIME_PARSE('{_z(b)}')))")
    return air.dump(base, local['stream_table'], formula=formula, by_id=True), want


def read_catalog(air, local):
    base, table = local['bases']['practices']
    return air.dump(base, table)
