# -*- coding: utf-8 -*-
"""The chat sweep in code (her amendment, 2 Nov 2026; built 5 Nov). At every
dusk close and the weekly close, every open chat is read against its
objective and its row, so the organizing falls to be•do and not to her. Her
words: I really want that organizational work to fall to the system. For
each chat there should be a clear objective; if it wasn't accomplished, it
should be picked up in a new chat; hold me accountable that I'm finishing
the chats and able to archive them.

Each open chat gets one verdict:

  archive    finished (☑️ ✔️ ✖️, or its row done and its objective met) and in
             the record: archive it without asking (her yes, 2 Nov), one line after
  close_row  the chat says done (☑️) but its row is still ▶️: close the row ✅,
             then archive
  carry      finished, but its objective was partly met or not met: its next
             step goes on an open ⚡ row or a new chat, then archive
  entry      no row carries the chat: write its session entry from its
             stretches (session-entry), then run this again
  hold       archiving it would take a side chat with it that isn't ready
  pinned     finished, but pinned: the app won't archive it, so it is hers
  busy       touched in the last few minutes, or working: she may be in it
  keep       in motion and touched this week, or ⏸️ (her on-purpose break,
             never nudged)
  ask        in motion and quiet for more than a week: close, park or keep?
             Her keep sticks: the row takes `chat sweep: kept YYYY-MM-DD`
             (`keep_line`), and the week counts from that day
  routine    a scheduled run: never swept

    python3 bedo_chats.py --sessions mine.json [--sessions other.json] (--live | --rows rows.json) [--now ISO] [--json]

`mine.json` is `list_sessions` (mine) as it came. Another surface's list can
ride along as a second `--sessions`: a cloud session's own list, or claude.ai's
code sessions read with her yes. Rows are the ⚡ rows that carry a chat link,
from this week's base and the one before; `--live` reads them. Exit 0 when
nothing is left for be•do to do, 1 otherwise.
"""
import datetime as dt, json, re, sys

from bedo_close import GLYPH, is_window, lead_glyph, next_step, objective
from bedo_entry import ACTION
from bedo_reader import FACTS, as_rows, load_local
from bedo_stretches import utc

C = FACTS['chats']
DONE, MOVING = '✅ done', '▶️ in motion'
TODO = ('archive', 'close_row', 'carry', 'entry')
ORDER = ('archive', 'close_row', 'carry', 'entry', 'hold', 'pinned', 'busy', 'keep', 'routine', 'ask')


def key_of(sid):
    """The id a chat link carries: local_…, session_… and cse_… all end the same."""
    s = (sid or '').strip()
    for p in ('local_', 'cse_', 'session_'):
        if s.startswith(p):
            return s[len(p):]
    return s


def norm(s):
    """One chat from any list's shape: list_sessions, or claude.ai's code sessions."""
    tags = [t.lower() for t in s.get('tags') or []]
    return {
        'id': s.get('sessionId') or s.get('id') or s.get('uuid') or '',
        'title': s.get('title') or s.get('name') or '',
        'archived': bool(s.get('isArchived') or s.get('status') == 'archived' or s.get('archived_at')),
        'running': bool(s.get('isRunning')),
        'last': s.get('lastActivityAt') or s.get('last_event_at') or s.get('updated_at'),
        'pinned': bool(s.get('pinned')),
        'parent': s.get('startedBy') or s.get('parentSessionId'),
        'routine': bool(s.get('scheduledTaskId') or s.get('trigger')
                        or any(t in tags for t in C['routine_tags'])),
    }


def chats_of(reads):
    """Every chat once, from one or more lists; the first list wins a duplicate."""
    out, seen = [], set()
    for read in reads:
        items = read if isinstance(read, list) else (read or {}).get('data') or (read or {}).get('sessions') or []
        for s in items:
            c = norm(s)
            k = key_of(c['id'])
            if k and k not in seen:
                seen.add(k)
                out.append(c)
    return out


def row_for(chat, rows):
    """The newest ⚡ row that carries this chat's link, in its chat field or its
    [be•do] block (a second surface's link sits there)."""
    k = key_of(chat['id'])
    if not k:
        return None
    mine = [r for r in rows if (r.get('practice') or '').strip() == ACTION
            and (k in (r.get('chat') or '') or k in (r.get('details') or ''))]
    linked = [r for r in mine if k in (r.get('chat') or '')] or mine
    return max(linked, key=lambda r: (r.get('created') or '', r.get('datetime') or ''), default=None)


KEPT = re.compile(re.escape(C['kept_marker']) + r'\s+(\d{4}-\d{2}-\d{2})')


def kept_on(row):
    """The newest day she said keep, from the row's `chat sweep: kept` lines."""
    days = KEPT.findall((row or {}).get('details') or '')
    return max(days) if days else None


def quiet_days(chat, now, row=None):
    """Days since the chat was touched, or since she last said keep."""
    times = [utc(chat['last'])] if chat.get('last') else []
    k = kept_on(row)
    if k:
        times.append(dt.datetime.fromisoformat(k).replace(tzinfo=dt.timezone.utc))
    return (now - max(times)).total_seconds() / 86400 if times else None


def keep_line(day):
    """The line the sweep writes in a row's [be•do] block when she says keep."""
    return f'{C["kept_marker"]} {day.isoformat()}'


def verdict(chat, row, now):
    """(verdict, why, next_step)."""
    if chat['routine']:
        return 'routine', 'a scheduled run', None
    touched = quiet_days(chat, now)
    if chat['running'] or (touched is not None and touched * 1440 < C['busy_minutes']):
        return 'busy', 'working now' if chat['running'] else f'touched {round(touched * 1440)} min ago', None
    q = quiet_days(chat, now, row)
    title, glyph = chat['title'], lead_glyph(chat['title'])
    if glyph == GLYPH['break']:
        return 'keep', 'set down on purpose (⏸️): never nudged', None
    status = (row or {}).get('status')
    o = objective((row or {}).get('details'))
    met = o is None or o[1] == 'met'
    finished = glyph in (GLYPH['done'], GLYPH['window_closed'], GLYPH['dropped'])
    if finished:
        if glyph == GLYPH['dropped']:
            return 'archive', 'dropped (✖️), her call', None
        if is_window(title):
            return 'archive', 'a window chat, closed (✔️)', None
        if not row:
            return 'entry', 'finished, but no row carries it: write its entry, then archive', None
        if status == MOVING:
            return 'close_row', f'the chat says done, its row {row.get("key") or "?"} still says in motion', None
        if not met:
            nxt = next_step(row.get('details'))
            return 'carry', f'objective {o[1]}: {o[0][:60]}', nxt
        return 'archive', f'{row.get("key") or "?"} · {status}' + (f' · objective met' if o else ''), None
    if not row:
        if q is not None and q > C['quiet_days']:
            return 'ask', f'no row, quiet {int(q)} days: close, park or keep?', None
        return 'entry', 'no row carries it yet: write its entry so its time is in the record', None
    if status in C['finished_statuses'] and o and o[1] == 'met':
        return 'archive', f'its row {row.get("key") or "?"} is done and the objective met; the title still says {glyph or "nothing"}', None
    if q is not None and q > C['quiet_days']:
        return 'ask', f'{glyph or "no glyph"} and quiet {int(q)} days: close, park or keep?', None
    return 'keep', 'in motion' + (f', touched {int(q)} days ago' if q else ''), None


def sweep(chats, rows, now):
    """[{id, title, verdict, why, next, row}] for every open chat."""
    out = []
    for c in chats:
        if c['archived']:
            continue
        r = row_for(c, rows)
        v, why, nxt = verdict(c, r, now)
        if v in ('archive', 'carry') and c['pinned']:
            v, why = 'pinned', why + ' · pinned, so the archive is hers'
        out.append({'id': c['id'], 'title': c['title'], 'verdict': v, 'why': why, 'next': nxt,
                    'parent': c['parent'], 'row': {k: r.get(k) for k in ('id', 'key', 'status', 'base')} if r else None})
    # archiving a chat takes its finished side chats with it: wait for them
    for x in out:
        if x['verdict'] != 'archive':
            continue
        kids = [k for k in out if k['parent'] and key_of(k['parent']) == key_of(x['id'])
                and k['verdict'] not in ('archive', 'keep', 'busy', 'routine', 'ask', 'pinned')]
        if kids:
            x['verdict'] = 'hold'
            x['why'] = 'archiving it takes ' + ', '.join(f'“{k["title"][:40]}”' for k in kids) + ' with it: do that one first'
    return sorted(out, key=lambda x: ORDER.index(x['verdict']))


SAY = {
    'archive': 'archive', 'close_row': 'close row', 'carry': 'carry on', 'entry': 'entry',
    'hold': 'hold', 'pinned': 'pinned', 'busy': 'busy', 'keep': 'keep', 'routine': 'routine', 'ask': 'ask',
}


def render(found, now):
    n = len(found)
    out = [f'chats · {n} open · {now.strftime("%Y-%m-%d %H:%MZ")}']
    groups = [('on its own, then one line after:', TODO), ('left alone:', ('hold', 'pinned', 'busy', 'keep', 'routine')),
              ('hers, one short list:', ('ask',))]
    for head, kinds in groups:
        mine = [x for x in found if x['verdict'] in kinds]
        if not mine:
            continue
        out.append(head)
        for x in mine:
            out.append(f'  {SAY[x["verdict"]]:<9} “{x["title"][:60]}” — {x["why"]}')
            if x['next']:
                out.append(f'            next step for the new chat or row: {x["next"].lstrip("· ")}')
    n_arch = sum(x['verdict'] in ('archive', 'close_row', 'carry') for x in found)
    if n_arch:
        out.append(f'after: archived {n_arch} finished chat(s) — reversible with unarchive')
    if not any(x['verdict'] in TODO for x in found):
        out.append('swept: nothing left for be•do')
    return '\n'.join(out)


def live_rows(local, today=None):
    """The ⚡ rows that carry a chat link, this week's base and the one before."""
    import bedo_air
    from bedo_entry import week_number
    air = bedo_air.Air()
    names = air.bases()
    today = today or dt.date.today()
    f, d_ = local['stream_fields']['chat'], local['stream_fields']['details']
    # an older entry carries its link only in the [be•do] block's chat line
    formula = f"OR({{{f}}}!='', FIND('epitaxy/local_', {{{d_}}}), FIND('code/session_', {{{d_}}}), FIND('claude.ai/chat/', {{{d_}}}))"
    rows = []
    for d in (today, today - dt.timedelta(days=7)):
        name = local.get('weekly_name', 'w{n} be•do').format(n=week_number(d))
        base = names.get(name)
        if not base:
            continue
        recs = air.records(base, local['stream_table'], formula=formula, by_id=True)
        for r in as_rows(recs, local['stream_fields']):
            rows.append({**r, 'base': name})
    seen, uniq = set(), []
    for r in rows:
        if r.get('id') not in seen:
            seen.add(r.get('id')); uniq.append(r)
    return uniq


def main():
    import argparse
    ap = argparse.ArgumentParser(description='the chat sweep: every open chat against its objective and its row')
    ap.add_argument('--sessions', action='append', required=True, help='list_sessions as it came; repeat for another surface')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--rows', help='the ⚡ rows with a chat link, as rows (logical names) or a dump')
    ap.add_argument('--now', help='ISO time, for tests')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    local = load_local()
    now = utc(a.now) if a.now else dt.datetime.now(dt.timezone.utc)
    if a.live:
        rows = live_rows(local)
    elif a.rows:
        d = json.load(open(a.rows, encoding='utf-8'))
        recs = d.get('records') if isinstance(d, dict) else d
        rows = as_rows(recs, local['stream_fields']) if recs and 'fields' in recs[0] else (recs or [])
    else:
        sys.exit('give --live, or --rows')
    chats = chats_of([json.load(open(p, encoding='utf-8')) for p in a.sessions])
    found = sweep(chats, rows, now)
    print(json.dumps(found, ensure_ascii=False, indent=1) if a.json else render(found, now))
    sys.exit(1 if any(x['verdict'] in TODO for x in found) else 0)


if __name__ == '__main__':
    main()
