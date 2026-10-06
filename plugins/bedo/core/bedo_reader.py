# -*- coding: utf-8 -*-
"""The one reader. Every builder and the close read the stream through this.

Three invariants live here, so no builder carries its own copy:

  I11  a truncated read is not a read — records returned must equal
       totalRecordCount, or the run stops before it concludes anything
  I15  several bases read together are deduped by RECORD ID, live base first,
       BEFORE any chain is resolved — a clone keeps record ids, and the live
       copy carries the corrections
  I5   a chain's head is its latest ACTION row (▫️ ⬜ ▶️ ✅ ✖️). A key is a
       minute, so a capture, a highlight or a drive logged in the same minute
       can share it; such a row is its own chain, never the action's head.
       (The W39 split read logs as heads and dropped two open actions.)

Nothing personal lives here. Choice strings come from facts.json.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))


def die(msg):
    sys.exit('ABORT: ' + msg)


def load_facts(path=None):
    for p in [path, os.path.join(HERE, 'facts.json')]:
        if p and os.path.exists(p):
            with open(p, encoding='utf-8') as fh:
                return json.load(fh)
    die('facts.json not found beside the reader')


FACTS = load_facts()


def load_local(path=None, required=True):
    """Her half of the facts: ids, offset, names. Never ships. Looked for at
    `path`, $BEDO_FACTS_LOCAL, beside the core, then ~/.bedo."""
    for p in [path, os.environ.get('BEDO_FACTS_LOCAL'), os.path.join(HERE, 'facts_local.json'),
              os.path.join(os.path.expanduser('~'), '.bedo', 'facts_local.json')]:
        if p and os.path.exists(p):
            with open(p, encoding='utf-8') as fh:
                return json.load(fh)
    if required:
        die('facts_local.json not found — copy facts_local.example.json and fill it in')
    return {}


def offset_hours(local, when_utc):
    """The local UTC offset at an instant, from the time zone when it can be
    read, else from facts_local's fixed offset (I12)."""
    tz = local.get('time_zone')
    if tz:
        try:
            from zoneinfo import ZoneInfo
            return when_utc.astimezone(ZoneInfo(tz)).utcoffset().total_seconds() / 3600
        except Exception:
            pass
    return local.get('utc_offset_hours', 0)
ACTION_STATUSES = frozenset(FACTS['status']['actions'])
OPEN_STATUSES = frozenset(FACTS['status']['open'])


def sv(v):
    """A select cell arrives as {"name": …}; everything else as itself."""
    return v.get('name') if isinstance(v, dict) else v


def cells(r):
    """MCP records carry cellValuesByFieldId; REST records carry fields."""
    return r.get('cellValuesByFieldId', r.get('fields')) or {}


def _cell(v):
    v = v.strip()
    if v.lower() in ('true', 'false'):
        return v.lower() == 'true'
    try:
        return int(v) if v.lstrip('-').isdigit() else float(v) if v.replace('.', '', 1).lstrip('-').isdigit() else v
    except ValueError:
        return v


def read_tsv(text):
    """The compact form a Cowork chat writes, where every cell read is a cell
    it writes out again (6 Oct). Line one is `total N` — the connector's own
    count — then any `name=value` every row shares, tab-separated; line two
    names the columns by their logical names; then one row per record. Blank
    cells are left out. A record count that is not the total stops as any
    short read does (I11)."""
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines or not lines[0].startswith('total '):
        die('a .tsv read starts with `total N`, the count the connector gave')
    first = lines[0].split('\t')
    total = int(first[0].split()[1])
    shared = dict(x.split('=', 1) for x in first[1:] if '=' in x)
    cols = [c.strip() for c in lines[1].split('\t')] if len(lines) > 1 else []
    recs = []
    for i, line in enumerate(lines[2:]):
        f = {k: _cell(v) for k, v in shared.items()}
        f.update({c: _cell(v) for c, v in zip(cols, line.split('\t')) if v.strip()})
        recs.append({'id': f'tsv{i}', 'createdTime': '', 'fields': f})
    return {'records': recs, 'metadata': {'totalRecordCount': total}}


def read_dump(src):
    """A path, or an already-loaded dump. A saved tool result in a claude.ai
    chat is wrapped as [{"text": "<json>"}]; accept that as-is. A .tsv path is
    the compact form (read_tsv)."""
    if isinstance(src, (str, os.PathLike)) and str(src).endswith('.tsv'):
        with open(src, encoding='utf-8') as fh:
            return read_tsv(fh.read())
    if isinstance(src, (str, os.PathLike)):
        with open(src, encoding='utf-8') as fh:
            d = json.load(fh)
    else:
        d = src
    if isinstance(d, list) and d and isinstance(d[0], dict) and 'text' in d[0]:
        d = json.loads(d[0]['text'])
    return d


def complete(src, label=None):
    """Records from one read, or stop (I11). The count must be stated by the
    source — a read that cannot say how many records exist proves nothing."""
    d = read_dump(src)
    label = label or (str(src) if isinstance(src, (str, os.PathLike)) else 'read')
    recs = d.get('records') if isinstance(d, dict) else None
    if recs is None:
        die(f'{label}: no records key — is this an Airtable read?')
    tot = (d.get('metadata') or {}).get('totalRecordCount')
    if tot is None or len(recs) != tot:
        die(f'{label}: {len(recs)} of {tot} records — a truncated read is not a read (I11)')
    return recs


def merge_live_first(sources):
    """Records from several bases, live base FIRST, each record id once (I15).
    Returns (records, reads) where reads names each source and its count, so a
    count can always say what it rests on."""
    seen, reads = {}, []
    for src in sources:
        recs = complete(src)
        reads.append((src if isinstance(src, (str, os.PathLike)) else 'read', len(recs)))
        for r in recs:
            seen.setdefault(r['id'], r)
    return list(seen.values()), reads


def chain_key(key, status, rid):
    """The chain a row belongs to. Only an action row joins its key's chain;
    every other row is a chain of one, keyed by its record id."""
    return key if key and status in ACTION_STATUSES else rid


def resolve(rows, key_of, status_of, created_of, id_of):
    """Chains and their heads (I5), after the rows were deduped (I15).
    Ties on createdTime keep the order the rows arrived in, which is live first."""
    chains = {}
    for r in rows:
        chains.setdefault(chain_key(key_of(r), status_of(r), id_of(r)), []).append(r)
    for ch in chains.values():
        ch.sort(key=lambda r: created_of(r) or '')
    return chains, {k: ch[-1] for k, ch in chains.items()}


def as_rows(recs, fields):
    """Records to rows under logical names, each carrying id and created."""
    rows = []
    for r in recs:
        c = cells(r)
        row = {k: sv(c.get(v, c.get(k))) for k, v in fields.items()}   # a .tsv names cells by logical name
        row.update(id=r['id'], created=r['createdTime'])
        rows.append(row)
    return rows


def on_day(rows, day, local):
    """Rows whose own datetime falls on a local day — so a file holding a whole
    week reads the same as the filtered read of one day."""
    import datetime as dt
    out = []
    for r in rows:
        s = r.get('datetime')
        if not s:
            continue
        t = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
        if (t + dt.timedelta(hours=offset_hours(local, t))).date() == day:
            out.append(r)
    return out


def stream_rows(sources, fields):
    """The common case, in one call: read every base live first, dedupe by
    record id, map field ids to names, resolve the chains. `fields` maps a name
    to a field id (or, for REST reads, to a field name). Each row also carries
    id and created."""
    recs, reads = merge_live_first(sources)
    rows = as_rows(recs, fields)
    chains, latest = resolve(rows, lambda r: r.get('key'), lambda r: r.get('status'),
                             lambda r: r['created'], lambda r: r['id'])
    return rows, chains, latest, reads
