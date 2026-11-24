# -*- coding: utf-8 -*-
"""The asks check: what Duet has handed to Code, read from the stream.

She is never the messenger between Duet and Code (J17). Duet writes an ask as
an ordinary ⚡ action row in the live weekly base, and its details carry two
lines after her own words:

    for code: one sentence, what the session is for
    done when: what finished looks like, something you could check

A Code session reads the open ones here, at its first reply, with no prompt
pasted (23 Nov 2026, her words: so I don't relay prompts between Duet and
Code). One filtered read of each weekly base in play, this week's and last
week's when it is still there, so an ask written on Saturday is seen on Sunday.

What the session then owes the row, through the connector, each write through
`entry` first:
  picked up   status ▶️ in motion, and its own chat link on the row
  finished    one `code:` line under the [be•do] divider saying what was done
              and where (the page, the pull request), then ✅ done
  can't       one `code:` line saying what blocks it; the row stays open

    python3 bedo_asks.py --live
    python3 bedo_asks.py --rows rows.json        # a read of the ⚡ rows, for a test or a chat with no token
"""
import argparse, datetime as dt, json, re, sys

from bedo_reader import FACTS, as_rows, load_local, read_dump

MARK = 'for code:'
OPEN = tuple(FACTS['status']['open'])
_P = r'(?im)^\W*(?:\[be•do\]\W*)?'      # a line may open with be•do's own mark
_FOR = re.compile(_P + r'for code:\s*(.+)$')
_DONE = re.compile(_P + r'done when:\s*(.+)$')
_CODE = re.compile(_P + r'code:\s*(.+)$')
FIELDS = ('title', 'status', 'details', 'datetime', 'rhythm')


def asks(rows):
    """The open asks among `rows`, oldest first: each with its objective, its
    done-when (None when Duet left it out) and what Code last said on it."""
    out = []
    for r in rows:
        d = r.get('details') or ''
        m = _FOR.search(d)
        if not m or (r.get('status') or '') not in OPEN:
            continue
        dw = _DONE.search(d)
        said = _CODE.findall(d)
        out.append(dict(id=r['id'], title=re.sub(r'^\W+', '', r.get('title') or '').strip(), status=r.get('status'),
                        objective=m.group(1).strip(), done_when=dw.group(1).strip() if dw else None,
                        said=said[-1].strip() if said else None, drive=r.get('rhythm') or '',
                        at=r.get('datetime') or r.get('created') or '', base=r.get('_base')))
    return sorted(out, key=lambda x: x['at'])


def report(found, bases=()):
    if not found:
        return ['asks   none open' + (f' in {", ".join(bases)}' if bases else '')]
    out = [f'asks   {len(found)} open from Duet. Read each back in the first reply, oldest first:']
    for x in found:
        out.append(f'  {x["status"].split()[0]} {x["title"]} · {x["id"]}' + (f' · {x["base"]}' if x.get('base') else ''))
        out.append(f'      objective: {x["objective"]}')
        out.append('      done when: ' + (x['done_when'] or 'NOT GIVEN. Draft one and get her yes before building'))
        if x['said']:
            out.append(f'      code said: {x["said"]}')
    out.append('       each one: ▶️ in motion with this chat\'s link when picked up; a `code:` line and ✅ done when finished')
    return out


def read_live(L, now=None):
    from bedo_air import Air
    from bedo_entry import week_number
    from bedo_reader import offset_hours
    air = Air()
    names = air.bases()
    now = now or dt.datetime.now(dt.timezone.utc)
    today = (now + dt.timedelta(hours=offset_hours(L, now))).date()
    name = L.get('weekly_name', 'w{n} be•do')
    want = []
    for d in (today, today - dt.timedelta(days=7)):          # the live base first
        n = name.format(n=week_number(d))
        if n in names and n not in want:
            want.append(n)
    sf = L.get('stream_fields') or {}
    fields = {k: sf.get(k, k) for k in FIELDS}
    det, st = fields['details'], fields['status']
    formula = (f"AND(FIND('{MARK}', LOWER({{{det}}} & '')) > 0, "
               f"OR({', '.join(f'{{{st}}} = ' + repr(s).replace(chr(92), '') for s in OPEN)}))")
    rows = []
    for n in want:
        src = air.dump(names[n], L['stream_table'], by_id=True, formula=formula)
        rows += [dict(r, _base=n) for r in as_rows(src['records'], fields)]
    return rows, want


def main(argv=None):
    ap = argparse.ArgumentParser(description='the asks check: what Duet handed to Code, read from the stream')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--rows', help='a read of the stream\'s ⚡ rows')
    ap.add_argument('--json', action='store_true', help='print the asks as JSON')
    a = ap.parse_args(argv)
    L = load_local()
    bases = ()
    if a.live:
        rows, bases = read_live(L)
    elif a.rows:
        sf = L.get('stream_fields') or {}
        rows = as_rows(read_dump(a.rows)['records'], {k: sf.get(k, k) for k in FIELDS})
    else:
        sys.exit('give --live or --rows FILE')
    found = asks(rows)
    print(json.dumps(found, ensure_ascii=False, indent=1) if a.json else '\n'.join(report(found, bases)))


if __name__ == '__main__':
    main()
