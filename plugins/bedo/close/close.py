# -*- coding: utf-8 -*-
"""be•do weekly close, by script. Nothing personal lives here: every id comes
from close_local.json (gitignored), the token from the AIRTABLE_PAT env var.

    python3 close.py fetch    --week 39          # stream of w39 + w40 (if cloned) + older weeks to disk
    python3 close.py backup   --week 39          # every table to CSV, with a created column
    python3 close.py check    --week 39          # the self-check numbers, and the quest lines
    python3 close.py export   --week 39          # her words only, md -> docx (pandoc or python-docx)
    python3 close.py audit    --week 39          # every row of the week through the entry check
    python3 close.py plan     --week 39          # the split: carry set + delete set by record id
    python3 close.py verify   --week 39          # after the clear: every open chain is in the new base

The rules are the core's (plugins/bedo/core), not this file's: I11 a read pages
to the end or aborts · I15 dedupe by record id, live base first · I5 a chain's
head is its latest ACTION row · I16 the delete set is built from record ids,
with both asserts · the carry-verify stops on any open chain missing from the
new base that isn't media. This script reads only; the deletes are done from
the plan file with a write-scoped tool, after she says yes.
"""
import argparse, collections, csv, datetime as dt, json, os, re, sys, time
import urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, '..', 'core')):   # copied beside it, or the repo layout
    sys.path.insert(0, os.path.normpath(p))
from bedo_reader import resolve  # noqa: E402
from bedo_entry import problems  # noqa: E402
from bedo_export import clock, hers, write_docx  # noqa: E402
import bedo_split  # noqa: E402

API = 'https://api.airtable.com/v0/'
# the stream's REST field names, as the close reads them
FIELDS = {'key': 'action key', 'status': 'status', 'datetime': 'datetime',
          'practice': 'practice text', 'title': 'action'}


def die(m):
    sys.exit('ABORT: ' + m)


class Air:
    def __init__(self):
        self.pat = os.environ.get('AIRTABLE_PAT') or die('set AIRTABLE_PAT')

    def get(self, path, q=None):
        url = API + path + ('?' + urllib.parse.urlencode(q, doseq=True) if q else '')
        req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + self.pat})
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
        out, q = {}, {}
        while True:
            d = self.get('meta/bases', q)
            out.update({b['name']: b['id'] for b in d['bases']})
            if not d.get('offset'):
                return out
            q = {'offset': d['offset']}

    def table(self, base, table):
        return next(t for t in self.get(f'meta/bases/{base}/tables')['tables'] if t['id'] == table)

    def records(self, base, table):          # I11: paged to the end
        recs, q = [], {'pageSize': 100}
        while True:
            d = self.get(f'{base}/{table}', q)
            recs += d['records']
            if not d.get('offset'):
                return recs
            q['offset'] = d['offset']


def L():
    p = os.environ.get('BEDO_CLOSE_LOCAL', 'close_local.json')
    return json.load(open(p, encoding='utf-8'))


def tz(L):
    return dt.timedelta(hours=L['utc_offset_hours'])


def ts(s, off):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')).replace(tzinfo=None) + off


def week_days(L, n):
    start = dt.date.fromisoformat(L['week_zero_sunday']) + dt.timedelta(weeks=n - L['week_zero_number'])
    return [start + dt.timedelta(d) for d in range(7)]


def wname(L, n):
    return L.get('weekly_name', 'w{n} be•do').format(n=n)


def out_dir(n):
    d = f'w{n}-close'
    os.makedirs(d, exist_ok=True)
    return d


def load(n, name):
    return json.load(open(os.path.join(out_dir(n), name), encoding='utf-8'))


# ── fetch ──────────────────────────────────────────────────────────────────
def fetch(a, L):
    air, names = Air(), None
    names = air.bases()
    d = out_dir(a.week)
    for wk in [a.week + 1, a.week] + [a.week - i for i in range(1, L.get('archive_depth', 3) + 1)]:
        b = names.get(wname(L, wk))
        if not b:
            print(f'w{wk}: no base'); continue
        recs = air.records(b, L['stream_table'])
        # paged to the end, so the count is the read's own (I11)
        json.dump({'base': b, 'records': recs, 'metadata': {'totalRecordCount': len(recs)}},
                  open(f'{d}/w{wk}.json', 'w', encoding='utf-8'), ensure_ascii=False)
        print(f'w{wk}: {len(recs)} rows')


# ── backup ─────────────────────────────────────────────────────────────────
def cell(v):
    if isinstance(v, list):
        return '; '.join(x.get('name', x.get('id', '')) if isinstance(x, dict) else str(x) for x in v)
    if isinstance(v, dict):
        return v.get('name', json.dumps(v, ensure_ascii=False))
    return v


def backup(a, L):
    air, d = Air(), out_dir(a.week)
    tables = dict(L['tables'])
    tables[f'w{a.week}-stream'] = [air.bases()[wname(L, a.week)], L['stream_table']]
    stamp = dt.date.today().isoformat()
    for name, (b, t) in tables.items():
        cols = [f['name'] for f in air.table(b, t)['fields']]
        recs = air.records(b, t)
        with open(f'{d}/{stamp}-{name}.csv', 'w', newline='', encoding='utf-8-sig') as fh:
            w = csv.writer(fh)
            w.writerow(['record id', 'created'] + cols)
            for r in recs:
                w.writerow([r['id'], r['createdTime']] + [cell(r['fields'].get(c, '')) for c in cols])
        print(name, len(recs))


# ── the self-check ─────────────────────────────────────────────────────────
def check(a, L):
    off, days = tz(L), week_days(L, a.week)
    R = load(a.week, f'w{a.week}.json')['records']
    air = Air()
    P = air.records(*L['tables']['practices'])
    wk = [dict(r['fields'], _c=r['createdTime'], _id=r['id']) for r in R
          if r['fields'].get('datetime') and ts(r['fields']['datetime'], off).date() in days]
    flows = collections.defaultdict(list)
    for p in P:
        f = p['fields']
        if f.get('group') == 'flow' and f.get('active'):
            flows[f.get('phase')].append(f['practice'])
    done = {'◉ done', '● log', '✅ done'}
    byday = collections.defaultdict(set)
    for f in wk:
        if f.get('status') in done:
            byday[ts(f['datetime'], off).date()].add(f.get('practice text'))
    out = {}
    for ph, lst in flows.items():
        c = [len(set(lst) & byday[d]) for d in days]
        out[f'{ph} coverage'] = f'{sum(c)} of {len(lst) * 7}  {c}'
    for p in L.get('weekly_counts', []):
        out[p] = f"{sum(1 for d in days if p in byday[d])}/7"
    span = lambda f: f.get('end datetime') or f.get('time spent')
    mins = lambda f: f['time spent'] / 60 if f.get('time spent') else \
        (ts(f['end datetime'], off) - ts(f['datetime'], off)).total_seconds() / 60
    acts = [f for f in wk if f.get('practice text') == '⚡ action']
    _, lat = resolve(acts, lambda f: f.get('action key'), lambda f: f.get('status'),
                     lambda f: f['_c'], lambda f: f['_id'])          # I5, action rows only
    act = [f for f in lat.values() if f.get('status') in ('✅ done', '▶️ in motion') and span(f)]
    out['attention'] = f"{sum(1 for f in act if f.get('attention'))} of {len(act)}"
    zero = {p['fields']['practice'] for p in P if p['fields'].get('zero duration')}
    dep = [f for f in wk if span(f) and f.get('practice text') not in zero | {'😴 sleep'}
           and f.get('status') not in ('▫️potential', '⬜ intention', '✖️ dropped')]
    out['depth'] = f"{sum(1 for f in dep if f.get('emotion') or f.get('emotion word'))} of {len(dep)}"
    sys_r = L.get('system_rhythm', 'be•do')
    ov = [f for f in act if sys_r in (f.get('rhythm text') or '')]
    out['overhead'] = f"{round(sum(mins(f) for f in ov))} min over {len(ov)} sessions"
    for k, v in out.items():
        print(f'{k:28} {v}')
    print('— quest')
    for f in sorted(wk, key=lambda f: f['datetime']):
        if 'quest' in (f.get('practice text') or ''):
            m = re.findall(r'\d+/10[^\n]*', f.get('details', ''))
            print(ts(f['datetime'], off).strftime('%a'), f.get('status'), '|',
                  (m[-1] if m else f.get('action', ''))[:90])


# ── export ──────────────────────────────────────────────────────────────────
def export(a, L):
    off, days = tz(L), week_days(L, a.week)
    R = load(a.week, f'w{a.week}.json')['records']
    rows = [r['fields'] for r in R if r['fields'].get('datetime')
            and ts(r['fields']['datetime'], off).date() in days
            and r['fields'].get('status') not in ('▫️potential', '⬜ intention')]
    ph = {'🌄': 0, '🔆': 1, '🌅': 2}
    title = f"W{a.week} be•do — {days[0]:%b} {days[0].day}–{days[-1]:%b} {days[-1].day}"
    md = [f'# {title}', '', f'{len(rows)} rows. Her words only.', '']
    for d in days:
        md += [f'## {d:%A} {d.day} {d:%B}', '']
        dr = sorted([f for f in rows if ts(f['datetime'], off).date() == d],
                    key=lambda f: (ph.get((f.get('phase') or '🔆')[:1], 1),
                                   -ts(f['datetime'], off).timestamp()))
        for f in dr:
            md.append(f"**{clock(ts(f['datetime'], off))} · {f.get('status', '')} "
                      f"{f.get('action', '').strip()}**")
            h = hers(f.get('details'))
            if h:
                md += ['', h]
            md.append('')
    src = os.path.join(out_dir(a.week), f'W{a.week}.md')
    open(src, 'w', encoding='utf-8').write('\n'.join(md))
    dst = os.path.join(out_dir(a.week), f'{title}.docx')
    how = write_docx(src, dst)
    print(dst, len(rows), f'({how})')


# ── the audit: the week's rows through the entry check ─────────────────────
REST_ROW = {'datetime': 'datetime', 'end': 'end datetime', 'time_spent': 'time spent',
            'status': 'status', 'practice': 'practice text', 'key': 'action key',
            'details': 'details', 'phase': 'phase', 'wellness': 'wellness area',
            'emotion': 'emotion', 'attention': 'attention', 'device': 'device'}


def audit(a, L):
    """Rows of the week that already broke a written rule, counted by rule.
    An observation: nothing is changed here."""
    off, days = tz(L), week_days(L, a.week)
    R = load(a.week, f'w{a.week}.json')['records']
    by, examples = collections.Counter(), {}
    for r in R:
        f = r['fields']
        if not f.get('datetime') or ts(f['datetime'], off).date() not in days:
            continue
        row = {k: f.get(v) for k, v in REST_ROW.items()}
        for msg in problems(row, base_name=wname(L, a.week), utc_offset_hours=L['utc_offset_hours'],
                            weekly_name=L.get('weekly_name', 'w{n} be•do')):
            rule = msg.split(':')[0]
            by[rule] += 1
            examples.setdefault(rule, (r['id'], msg))
    for rule, n in by.most_common():
        print(f'{n:5}  {rule:12} e.g. {examples[rule][1]}')
    print(f'{sum(by.values())} problem(s) across the week' if by else 'every row passes the entry check')


# ── the split plan ─────────────────────────────────────────────────────────
def _reads(a, L, weeks):
    out = []
    for wk in weeks:
        p = os.path.join(out_dir(a.week), f'w{wk}.json')
        if os.path.exists(p):
            out.append(p)
    return out


def plan(a, L):
    new = a.week + 1
    first_new = week_days(L, new)[0]
    archives = _reads(a, L, [a.week - i for i in range(1, L.get('archive_depth', 3) + 1)])
    res = bedo_split.plan(os.path.join(out_dir(a.week), f'w{new}.json'),
                          os.path.join(out_dir(a.week), f'w{a.week}.json'),
                          archives, FIELDS, first_new, L['utc_offset_hours'], a.clone)
    json.dump(res, open(os.path.join(out_dir(a.week), 'split_plan.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    summary = {k: (len(v) if isinstance(v, list) and k != 'reads' else v) for k, v in res.items()}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if res['carry_elsewhere']:
        print(f"{len(res['carry_elsewhere'])} open head(s) live only in an older base — re-carry "
              'them into the new base (details verbatim, key kept), then run verify')


def verify(a, L):
    """After the clear: re-fetch, then every open chain across every base must
    have an open row in the new base. Any non-media gap stops the close."""
    new = a.week + 1
    allb = _reads(a, L, [new, a.week] + [a.week - i for i in range(1, L.get('archive_depth', 3) + 1)])
    gaps = bedo_split.verify_carry(os.path.join(out_dir(a.week), f'w{new}.json'), allb, FIELDS)
    media = [g for g in gaps if g['media']]
    print(f'carry-verify: every open chain is in w{new}'
          + (f' ({len(media)} media row(s) left behind, by rule)' if media else ''))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('step', choices=['fetch', 'backup', 'check', 'export', 'audit', 'plan', 'verify'])
    ap.add_argument('--week', type=int, required=True, help='the week being CLOSED')
    ap.add_argument('--clone', help='ISO time the new base was cloned; defaults to its newest row')
    a = ap.parse_args()
    globals()[a.step](a, L())


if __name__ == '__main__':
    main()
