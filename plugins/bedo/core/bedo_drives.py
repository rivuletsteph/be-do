# -*- coding: utf-8 -*-
"""Drives within drives: a row rolls up through `feeds` (9 Oct 2026).

A drive can feed another — the rhythms field `feeds`, e.g. D12 Robot arm →
D11 Robot club, which feeds D10 School year. Every builder that counts
time, completions or open items by drive follows the same four rules, so they
live here once:

  · a row counts under its own drive AND under every drive it feeds, following
    the chain upward (a drive feeding two counts under both lines, once each)
  · the child is shown nested under its parent (D26 → D52), never as a peer
  · a grand total counts each row once; the roll-up is for the per-drive view
  · a loop in `feeds` ends the walk where it closes — it never spins, and it
    never counts a row twice under one drive

Nothing here knows a field id. A rhythm is a dict with at least 'name' and,
when the base carries it, 'feeds' (a list of names, or one name); 'code' and
'emoji' are used when present.
"""


def feeds_of(rec):
    """The names a rhythm feeds, as a list, whatever shape the cell arrived in."""
    v = (rec or {}).get('feeds')
    if not v:
        return []
    if not isinstance(v, (list, tuple)):
        v = [v]
    out = []
    for x in v:
        x = x.get('name') if isinstance(x, dict) else x
        if x and str(x).strip():
            out.append(str(x).strip())
    return out


def resolve(name, rhythms):
    """The rhythms key a `feeds` value names: the name itself, a code (D26), or
    a name the value ends — the same leniency the destinations get."""
    if not name:
        return None
    if name in rhythms:
        return name
    for k, r in rhythms.items():
        if (r.get('code') or '') == name:
            return k
    for k in rhythms:
        if k.endswith(name) or name.endswith(k):
            return k
    return None


def parents(name, rhythms):
    """The drives this one feeds directly, resolved; unknown names dropped."""
    out = []
    for f in feeds_of(rhythms.get(name)):
        k = resolve(f, rhythms)
        if k and k != name and k not in out:
            out.append(k)
    return out


def chain(name, rhythms):
    """The drive and every drive above it, nearest first, each once. A loop
    stops the walk where it closes."""
    if not name:
        return []
    seen, out, todo = {name}, [name], [name]
    while todo:
        cur = todo.pop(0)
        for p in parents(cur, rhythms):
            if p not in seen:
                seen.add(p); out.append(p); todo.append(p)
    return out


def loops(rhythms):
    """Every `feeds` loop, each named once as the drives on it — for the QA
    block, so the base gets fixed rather than quietly tolerated."""
    found, keyset = [], set()
    for start in rhythms:
        path, at = [start], start
        while True:
            ps = parents(at, rhythms)
            if not ps:
                break
            at = ps[0]
            if at in path:
                cyc = path[path.index(at):]
                k = frozenset(cyc)
                if k not in keyset:
                    keyset.add(k); found.append(cyc)
                break
            path.append(at)
    for start in rhythms:          # loops reached only through a second parent
        for p in parents(start, rhythms)[1:]:
            if start in chain(p, rhythms):
                k = frozenset((start, p))
                if not any(k <= s for s in keyset):
                    keyset.add(k); found.append([start, p])
    return found


def roll_up(items, rhythms, drive=lambda x: x.get('drive'), weight=lambda x: 1):
    """Per-drive totals. Each item counts under its own drive and every drive
    above it. Returns {drive: {'own': w, 'total': w, 'n_own': n, 'n': n,
    'items': [own items]}} — 'own' is the drive's rows alone, 'total' with every
    drive that feeds it. Items with no drive are left out."""
    out = {}
    for it in items:
        d = drive(it)
        if not d:
            continue
        w = weight(it) or 0
        for i, k in enumerate(chain(d, rhythms)):
            g = out.setdefault(k, dict(own=0, total=0, n_own=0, n=0, items=[]))
            g['total'] += w; g['n'] += 1
            if i == 0:
                g['own'] += w; g['n_own'] += 1; g['items'].append(it)
    return out


def grand_total(items, weight=lambda x: 1):
    """Each item once, whatever drives it rolls up through."""
    return sum(weight(it) or 0 for it in items)


def tree(rolled, rhythms, key=None):
    """The rolled-up drives as a forest: each drive under its first parent that
    is also on the page, children nested as 'children'. A drive whose parent
    would close a loop is shown as a root. Siblings sort by `key` (default:
    heaviest total first, then name)."""
    names = list(rolled)
    key = key or (lambda n: (-rolled[n]['total'], n))
    up = {}
    for n in sorted(names, key=key):
        p = next((p for p in parents(n, rhythms) if p in rolled), None)
        a = p
        while a is not None and a != n:            # would attaching close a loop?
            a = up.get(a)
        if p is not None and a is None:
            up[n] = p
    nodes = {n: dict(name=n, **{k: v for k, v in rolled[n].items()}, children=[]) for n in names}
    roots = []
    for n in sorted(names, key=key):
        (nodes[up[n]]['children'] if n in up else roots).append(nodes[n])
    return roots


def flatten(forest, depth=0):
    """The forest in reading order, each node with its depth — parent first,
    then its children indented under it."""
    for n in forest:
        yield depth, n
        yield from flatten(n['children'], depth + 1)
