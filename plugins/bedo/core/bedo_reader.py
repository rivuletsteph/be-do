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
ACTION_STATUSES = frozenset(FACTS['status']['actions'])
OPEN_STATUSES = frozenset(FACTS['status']['open'])


def sv(v):
    """A select cell arrives as {"name": …}; everything else as itself."""
    return v.get('name') if isinstance(v, dict) else v


def cells(r):
    """MCP records carry cellValuesByFieldId; REST records carry fields."""
    return r.get('cellValuesByFieldId', r.get('fields')) or {}


def read_dump(src):
    """A path, or an already-loaded dump. A saved tool result in a claude.ai
    chat is wrapped as [{"text": "<json>"}]; accept that as-is."""
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


def stream_rows(sources, fields):
    """The common case, in one call: read every base live first, dedupe by
    record id, map field ids to names, resolve the chains. `fields` maps a name
    to a field id (or, for REST reads, to a field name). Each row also carries
    id and created."""
    recs, reads = merge_live_first(sources)
    rows = []
    for r in recs:
        c = cells(r)
        row = {k: sv(c.get(v)) for k, v in fields.items()}
        row.update(id=r['id'], created=r['createdTime'])
        rows.append(row)
    chains, latest = resolve(rows, lambda r: r.get('key'), lambda r: r.get('status'),
                             lambda r: r['created'], lambda r: r['id'])
    return rows, chains, latest, reads
