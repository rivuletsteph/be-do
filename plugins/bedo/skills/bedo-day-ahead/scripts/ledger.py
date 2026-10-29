"""ledger.py — how far each drive has come, kept past the two-week read.

The morning read holds the live week and the week before, so a drive whose
work was done a month ago read as 0% on the my day page (28 Oct 2026, her
words: "there's no way that [the class talk] is 0% done"). The ledger keeps
every finished ⚡ step and every lived row on a rhythm or drive, from the
older reads and the weekly CSV backups, in one small file the builder reads
beside the live week. Nothing is read from Airtable to make it.

    python3 ledger.py --local day_ahead_local.json --out history/ledger.json \
        [--alias aliases.json] SOURCE...

A SOURCE is an older read (data/w##.json, the Airtable shape) or a weekly
backup CSV. A row is kept once, by record id, the first source winning, so
pass the newest first. `--alias` is a JSON object of old drive names to the
current ones; a CSV row may name two drives, comma-separated, and each part
is renamed. The file is the person's, so it stays in the working folder, out
of the repo.
"""
import argparse, csv, datetime as dt, hashlib, json, os, sys

KEEP = ('✅', '◉', '●')   # a finished step, a done flow step, a log: the ground covered
COLS = dict(title=('action', 'title'), status=('status',), practice=('practice text', 'practice'),
            rhythm=('rhythm text', 'rhythm'), end=('end datetime',), when=('datetime',),
            key=('action key', 'key'), id=('record id',), created=('created',))
FMT = ('%B %d, %Y %I:%M%p', '%B %d, %Y %H:%M', '%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ')


def utc(s, offset):
    """A CSV time is local ("September 15, 2026 5:16pm"); the read is UTC."""
    s = (s or '').strip()
    if not s:
        return None
    for f in FMT:
        try:
            t = dt.datetime.strptime(s, f)
        except ValueError:
            continue
        if f.endswith('Z'):
            return t.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        return (t - offset).strftime('%Y-%m-%dT%H:%M:%S.000Z')
    return None


def renamed(name, alias):
    parts = [p.strip() for p in (name or '').split(',') if p.strip()] if name not in alias else [name]
    whole = alias.get(name)
    if whole:
        return whole
    return ', '.join(alias.get(p, p) for p in parts)


def from_csv(path, offset):
    with open(path, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            g = lambda k: next((r[c] for c in COLS[k] if r.get(c)), '')
            when = utc(g('when'), offset)
            row = dict(title=g('title'), status=g('status'), practice=g('practice'), rhythm=g('rhythm'),
                       end=utc(g('end'), offset), when=when, key=g('key'))
            rid = g('id') or 'csv' + hashlib.sha1(json.dumps(row, sort_keys=True).encode()).hexdigest()[:14]
            yield rid, utc(g('created'), offset) or when, row


def from_read(path, F, offset):
    """An older read: by field id (the builder's reads) or by field name (the close's)."""
    d = json.load(open(path, encoding='utf-8'))
    back = {v: k for k, v in F.items()}
    for r in d.get('records', d if isinstance(d, list) else []):
        c = r.get('cellValuesByFieldId')
        if c is not None:
            row = {back[f]: (v.get('name') if isinstance(v, dict) else v) for f, v in c.items() if f in back}
        else:
            c = r.get('fields') or {}
            g = lambda k: next((c[n] for n in COLS[k] if c.get(n)), '')
            row = {k: g(k) for k in ('title', 'status', 'practice', 'rhythm', 'end', 'when', 'key')}
            row.update(end=utc(row['end'], offset), when=utc(row['when'], offset))
        yield r['id'], r['createdTime'], row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--local', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--alias')
    ap.add_argument('source', nargs='+')
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    F = {k: L['fields']['stream'][k] for k in ('title', 'key', 'when', 'end', 'status', 'practice', 'rhythm')}
    offset = dt.timedelta(hours=L['utc_offset_hours'])
    alias = json.load(open(a.alias, encoding='utf-8')) if a.alias else {}
    seen, out, per = set(), [], {}
    for p in a.source:
        rows = from_csv(p, offset) if p.lower().endswith('.csv') else from_read(p, F, offset)
        n = 0
        for rid, created, row in rows:
            if rid in seen or not (row.get('rhythm') or '').strip() or not (row.get('status') or '').startswith(KEEP):
                continue
            seen.add(rid)
            row['rhythm'] = renamed(row['rhythm'].strip(), alias)
            out.append(dict(id=rid, createdTime=created,
                            cellValuesByFieldId={F[k]: v for k, v in row.items() if v and k in F}))
            n += 1
        per[os.path.relpath(p)] = n
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(dict(records=out, metadata=dict(totalRecordCount=len(out), sources=per)),
              open(a.out, 'w', encoding='utf-8'), ensure_ascii=False)
    print(json.dumps(dict(kept=len(out), sources=per), ensure_ascii=False))


if __name__ == '__main__':
    sys.exit(main())
