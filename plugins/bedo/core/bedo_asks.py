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

One ask per chat (24 Nov 2026, her words: show what's in progress so asks
don't pile into one chat). An ask already ▶️ in motion carries the link of the
chat working it, so another chat skips it and says where it is. Of the asks
still waiting, a chat takes the oldest, one only; the rest wait for the next
`run asks` chat. A chat that already holds an ask (its own link on the row)
carries on with that one and takes no other.

What the session then owes the row, through the connector, each write through
`entry` first:
  picked up   status ▶️ in motion, and its own chat link on the row
  finished    one `code:` line under the [be•do] divider saying what was done
              and where (the page, the pull request), then ✅ done
  can't       one `code:` line saying what blocks it; the row stays open

    python3 bedo_asks.py --live                  # this chat's link from the session, else --chat URL
    python3 bedo_asks.py --rows rows.json        # a read of the ⚡ rows, for a test or a chat with no token
"""
import argparse, datetime as dt, json, os, re, sys

from bedo_reader import FACTS, as_rows, load_local, read_dump

MARK = 'for code:'
OPEN = tuple(FACTS['status']['open'])
_P = r'(?im)^\W*(?:\[be•do\]\W*)?'      # a line may open with be•do's own mark
_FOR = re.compile(_P + r'for code:\s*(.+)$')
_DONE = re.compile(_P + r'done when:\s*(.+)$')
_CODE = re.compile(_P + r'code:\s*(.+)$')
FIELDS = ('title', 'status', 'details', 'datetime', 'rhythm', 'chat')
MOVING = '▶️ in motion'
_ID = re.compile(r'session_[A-Za-z0-9]+|[0-9a-f]{8}-[0-9a-f-]{27,}')


def this_chat():
    """This session's own link, from the cloud session it runs in; None elsewhere."""
    sid = os.environ.get('CLAUDE_CODE_REMOTE_SESSION_ID') or ''
    return 'https://claude.ai/code/session_' + sid.split('_', 1)[1] if sid.startswith('cse_') else None


def _same_chat(a, b):
    ia, ib = _ID.search(a or ''), _ID.search(b or '')
    return bool(ia and ib and ia.group(0) == ib.group(0))


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
                        at=r.get('datetime') or r.get('created') or '', base=r.get('_base'),
                        chat=(r.get('chat') or '').strip() or None))
    return sorted(out, key=lambda x: x['at'])


def plan(found, chat=None):
    """Split the open asks for one chat: the one it works (`held` already
    or `take`n now), those in motion in other chats, and those left waiting."""
    held = [x for x in found if chat and _same_chat(x['chat'], chat)]
    elsewhere = [x for x in found if x not in held and x['status'] == MOVING]
    waiting = [x for x in found if x not in held and x not in elsewhere]
    take = None if held else (waiting[0] if waiting else None)
    return dict(held=held, take=take, elsewhere=elsewhere,
                left=[x for x in waiting if x is not take])


def _ask(x, out):
    out.append(f'      objective: {x["objective"]}')
    out.append('      done when: ' + (x['done_when'] or 'NOT GIVEN. Draft one and get her yes before building'))
    if x['said']:
        out.append(f'      code said: {x["said"]}')


def report(found, bases=(), chat=None):
    if not found:
        return ['asks   none open' + (f' in {", ".join(bases)}' if bases else '')]
    p = plan(found, chat)
    where = lambda x: f'{x["title"]} · {x["id"]}' + (f' · {x["base"]}' if x.get('base') else '')
    out = [f'asks   {len(found)} open from Duet: {len(p["elsewhere"])} in motion in another chat, '
           f'{len(p["left"]) + (1 if p["take"] else 0)} waiting. One ask per chat:']
    if p['held']:
        for x in p['held']:
            out.append(f'  this chat holds: {where(x)}')
            _ask(x, out)
        out.append('      carry on with it; take no other ask here')
    elif p['take']:
        x = p['take']
        out.append(f'  take: {where(x)}')
        _ask(x, out)
        out.append(f'      read it back, then: apply [{{"id": "{x["id"]}", "status": "{MOVING}", "chat": "{chat or "<this chat>"}"}}]')
    else:
        out.append('  nothing waiting for this chat')
    for x in p['elsewhere']:
        out.append(f'  skip, ▶️ in another chat: {where(x)} · ' + (x['chat'] or 'NO CHAT LINK on the row, ask her where it is'))
        if x['said']:
            out.append(f'      code said: {x["said"]}')
    for x in p['left']:
        out.append(f'  waits for the next run asks chat: {where(x)}')
    out.append('       the one taken: ▶️ in motion with this chat\'s link; a `code:` line and ✅ done when finished')
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
    ap.add_argument('--chat', help="this chat's link (default: the cloud session's own)")
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
    chat = a.chat or this_chat()
    print(json.dumps(dict(plan(found, chat), chat=chat), ensure_ascii=False, indent=1) if a.json
          else '\n'.join(report(found, bases, chat)))


if __name__ == '__main__':
    main()
