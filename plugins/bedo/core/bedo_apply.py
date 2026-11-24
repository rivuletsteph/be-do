# -*- coding: utf-8 -*-
"""Rows written by code, never retyped by a model (24 Nov 2026, her words: I'd
like these practices to run on its own … in a way that conserves tokens).

On 23 Nov 2026 a day's Code steps cost most of their tokens in one place: every
write passed through the model as a hand-typed payload, a row's whole details
sent back to add one line to it. `apply` takes a short file of what should
change, in the names `entry` reads, and does the rest in code:

  a new row      {"title": …, "practice": …, "status": …, "datetime": …, …}
  a change       {"id": "rec…", "status": "✅ done"}          only what changes
  one more line  {"id": "rec…", "append": "[be•do] …"}        added to the end of its details
  her words      {"id": "rec…", "her_words": "… (Mon, 9:00p)"}  added above the divider

It reads each row it will add a line to, so existing text is carried forward
verbatim by code. A new row goes through the entry check; what the check
deduces by itself (a device, a person, a wellness, an end) is filled in and
checked again; a row left with a FIX is not written and is named. Then it
writes, where the Airtable credential may write. Where it may only read, it
says so once and saves the same writes as `connector.json`, in field ids, for
the connector.

    python3 bedo_apply.py ops.json [--base "w48 be•do"] [--chat MMDD] [--dry] [--json]
"""
import argparse, datetime as dt, json, os, re, sys

from bedo_reader import FACTS, load_local

DIVIDER = FACTS['divider']
SPECIAL = ('id', 'append', 'her_words')
_DEDUCED = re.compile(r'^(\w[\w ]*): empty (?:→|— deduced) (.+?)(?: — | \(|;|$)')
_AT_WRITE = re.compile(r'^key: not checked')


def compose(details, append=None, her_words=None):
    """The row's details with her new words above the divider and be•do's new
    lines at the end. Everything already there stays as it is."""
    d = details or ''
    if her_words:
        if DIVIDER in d:
            top, block = d.split(DIVIDER, 1)
            top = top.rstrip('\n')
            d = (top + '\n' if top else '') + her_words.strip() + '\n' + DIVIDER + block
        else:
            d = (d.rstrip('\n') + '\n' if d.strip() else '') + her_words.strip()
    if append:
        if DIVIDER not in d:
            d = (d.rstrip('\n') + '\n' if d.strip() else '') + DIVIDER
        d = d.rstrip('\n') + '\n' + append.strip()
    return d


def to_fields(op, F):
    """An op's own fields by field id. A name the settings don't carry stops the run."""
    out = {}
    for k, v in op.items():
        if k in SPECIAL:
            continue
        if k not in F:
            sys.exit(f'bedo_apply: no field named {k} in the settings (stream_fields)')
        out[F[k]] = v
    return out


def fill_deduced(row, found):
    """Write what the entry check deduced into the row; return the lines it could not settle."""
    left = []
    for p in found:
        m = _DEDUCED.match(p)
        if m and not row.get(m.group(1).strip()):
            row[m.group(1).strip()] = m.group(2).strip()
        elif not _AT_WRITE.match(p):
            left.append(p)
    return left


def plan(ops, current, F, check=None):
    """(creates, updates, refused): creates and updates in field ids, ready to send.
    `current` maps a record id to its details now; `check(row)` returns the entry
    check's lines for a new row."""
    creates, updates, refused = [], [], []
    for op in ops:
        op = dict(op)
        title = op.get('title') or op.get('id') or '?'
        if op.get('id'):
            if op.get('append') or op.get('her_words'):
                if op['id'] not in current:
                    refused.append((title, ['its row could not be read, so nothing was added to it']))
                    continue
                op['details'] = compose(current[op['id']], op.get('append'), op.get('her_words'))
            fields = to_fields(op, F)
            if fields:
                updates.append({'id': op['id'], 'fields': fields})
            continue
        if op.get('append') or op.get('her_words'):
            op['details'] = compose(op.get('details'), op.get('append'), op.get('her_words'))
        left = []
        if check:
            for _ in range(2):                      # once to deduce, once to see it now passes
                left = fill_deduced(op, check(op))
                if not left:
                    break
        if left:
            refused.append((title, left))
        else:
            creates.append(to_fields(op, F))
    return creates, updates, refused


def _checker(L, base_name, chat):
    from bedo_entry import problems
    import bedo_clock, bedo_fill as FL
    clock = L if (bedo_clock.zone(L) is not None or L.get('utc_offset_hours') is not None) else None

    def check(row):
        fill = FL.Context(day_rows=[row], local=L)
        return problems(row, base_name, clock, L.get('weekly_name', 'w{n} be•do'), chat, fill,
                        (L.get('people') or {}).get('self'))
    return check


def main(argv=None):
    ap = argparse.ArgumentParser(description='write rows from a short file of changes, in code')
    ap.add_argument('ops')
    ap.add_argument('--base', help='the weekly base by name; the live week when left out')
    ap.add_argument('--chat', help="a day chat's MMDD, for the entry check")
    ap.add_argument('--dry', action='store_true', help='check and show, write nothing')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    F = dict(L.get('stream_fields') or {})
    for k in ('photo', 'photo_links'):
        v = ((L.get('fields') or {}).get('stream') or {}).get(k)
        if v and k not in F:
            F[k] = v
    ops = json.load(open(a.ops, encoding='utf-8'))
    ops = ops if isinstance(ops, list) else [ops]
    import bedo_air, bedo_clock
    from bedo_entry import week_number
    air = bedo_air.Air()
    name = a.base or L.get('weekly_name', 'w{n} be•do').format(n=week_number(bedo_clock.now_local(L).date()))
    base = air.bases().get(name) or sys.exit(f'bedo_apply: no base named {name}')
    table = L['stream_table']
    need = sorted({o['id'] for o in ops if o.get('id') and (o.get('append') or o.get('her_words'))})
    current = {}
    for i in range(0, len(need), 40):
        f = 'OR(' + ', '.join(f"RECORD_ID()='{x}'" for x in need[i:i + 40]) + ')'
        for r in air.records(base, table, formula=f, by_id=True):
            current[r['id']] = (r.get('fields') or {}).get(F['details']) or ''
    chat = None
    if a.chat:
        chat = dt.date(bedo_clock.now_local(L).year, int(a.chat[:2]), int(a.chat[2:4]))
    creates, updates, refused = plan(ops, current, F, _checker(L, name, chat))
    out = dict(base=name, created=len(creates), updated=len(updates),
               refused=[dict(title=t, fix=p) for t, p in refused], wrote=False)
    if not a.dry and (creates or updates):
        try:
            if creates:
                out['ids'] = air.create(base, table, creates)
            if updates:
                air.patch(base, table, updates)
            out['wrote'] = True
        except SystemExit as e:                      # the cloud credential may only read (J10)
            path = os.path.join(os.path.dirname(os.path.abspath(a.ops)), 'connector.json')
            json.dump(dict(baseId=base, tableId=table, create=creates, update=updates),
                      open(path, 'w', encoding='utf-8'), ensure_ascii=False)
            out['connector'] = path
            out['why'] = str(e)
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        said = ('checked, nothing written (--dry)' if a.dry else 'written' if out['wrote'] else
                f"NOT written: the credential here only reads. The same writes are in {out.get('connector')}: "
                'send them through the connector, typecast off' if out.get('connector') else 'nothing to write')
        print(f"apply  {name}: {len(creates)} new, {len(updates)} changed · {said}")
        for t, p in refused:
            print(f'  FIX   {t[:70]}')
            for x in p:
                print(f'      · {x}')
    sys.exit(1 if refused else 3 if out.get('connector') else 0)


if __name__ == '__main__':
    main()
