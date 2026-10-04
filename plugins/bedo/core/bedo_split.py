# -*- coding: utf-8 -*-
"""The weekly split, as a plan and a check. Nothing here deletes or writes;
the plan is a list of record ids a write-scoped tool acts on after her yes.

  I16  the delete set is built from RECORD IDS, never dates: (ids present in
       the outgoing base) minus (the carry set) minus (rows dated in the new
       week). Two asserts before the first delete: no row created after the
       clone, no row dated in the new week. Both must pass; neither replaces
       the id rule.
  I5 + I15  the carry set is the open HEAD of every chain, resolved across
       every base read, live first, reading action rows only.
  carry-verify  every open chain, across all bases, has a row in the new base.
       A gap that is not media stops the close: that is how the W39 split lost
       two open actions without anyone seeing.
"""
import datetime as dt

from bedo_reader import FACTS, OPEN_STATUSES, cells, complete, die, merge_live_first, resolve, sv

MEDIA = frozenset(FACTS['practice']['media'])


def _get(fields):
    def g(r, name):
        return sv(cells(r).get(fields[name]))
    return g


def heads_across(sources, fields):
    """Every chain's head across the bases in `sources` (live first)."""
    recs, reads = merge_live_first(sources)
    g = _get(fields)
    chains, heads = resolve(recs, lambda r: g(r, 'key'), lambda r: g(r, 'status'),
                            lambda r: r['createdTime'], lambda r: r['id'])
    return recs, chains, heads, reads


def local_date(s, offset_hours):
    return (dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
            + dt.timedelta(hours=offset_hours)).date()


def plan(new_base, outgoing, archives, fields, first_new_day, offset_hours, clone_time=None):
    """new_base, outgoing: a read of each (path or dump). archives: older bases,
    newest first. The new base is a clone of the outgoing one, so their record
    ids must match exactly before anything is planned."""
    g = _get(fields)
    W = {r['id']: r for r in complete(new_base, 'new base')}
    old = {r['id'] for r in complete(outgoing, 'outgoing base')}
    if set(W) != old:
        die(f'record-id diff is not clean: {len(set(W) - old)} only in the new base, '
            f'{len(old - set(W))} only in the outgoing one — patch, verify, then plan')
    _, _, heads, reads = heads_across([new_base, outgoing] + list(archives), fields)
    carry = {h['id'] for h in heads.values() if g(h, 'status') in OPEN_STATUSES}

    def in_new_week(r):
        s = g(r, 'datetime')
        return bool(s) and local_date(s, offset_hours) >= first_new_day

    keep = {i for i, r in W.items() if in_new_week(r)}
    delete = sorted(set(W) - carry - keep)                                  # I16
    clone = clone_time or max(r['createdTime'] for r in W.values())
    late = [i for i in delete if W[i]['createdTime'] > clone]
    if late:
        die(f'{len(late)} row(s) in the delete set were created after the clone (I16)')
    dated = [i for i in delete if in_new_week(W[i])]
    if dated:
        die(f'{len(dated)} row(s) in the delete set are dated in the new week (I16)')
    return {
        'delete_ids': delete,
        'carry_ids': sorted(carry & set(W)),
        'carry_elsewhere': sorted(carry - set(W)),
        'keep_new_week': len(keep),
        'after': len(W) - len(delete),
        'reads': [(str(p), n) for p, n in reads],
    }


def carry_gaps(new_base, all_sources, fields):
    """Open chains (across every base, live first) with no row in the new base.
    Matched by KEY, since a re-carried row is a new record with the old key.
    The new base's own head for that chain must be open too — an older closed
    row there does not carry an open chain. Returns the gaps, media and not."""
    g = _get(fields)
    _, _, here, _ = heads_across([new_base], fields)
    _, _, heads, _ = heads_across(all_sources, fields)
    gaps = []
    for k, h in heads.items():
        if g(h, 'status') not in OPEN_STATUSES:
            continue
        if k in here and g(here[k], 'status') in OPEN_STATUSES:
            continue
        gaps.append({'chain': k, 'id': h['id'], 'status': g(h, 'status'),
                     'title': g(h, 'title') if 'title' in fields else None,
                     'media': g(h, 'practice') in MEDIA})
    return gaps


def verify_carry(new_base, all_sources, fields):
    """Stop on any open head missing from the new base that isn't media."""
    gaps = carry_gaps(new_base, all_sources, fields)
    real = [x for x in gaps if not x['media']]
    if real:
        die(f'carry-verify: {len(real)} open chain(s) are not in the new base: '
            + ', '.join(x['chain'] for x in real[:12]) + (' …' if len(real) > 12 else ''))
    return gaps
