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
  (pinned)   a finished chat that is pinned keeps its verdict and carries
             `unpin`: unpin it, then archive (her rule, 11 Nov 2026)
  unpin      pinned, not finished, and not touched today in her time zone:
             unpin it, on its own (her amendment, 12 Nov
             2026: pinned needs to be what I'm actively working on that day).
             A my day chat is never unpinned this way. A pinned chat with
             another verdict (entry, hold, ask) that wasn't touched today
             carries `unpin` too
  busy       touched in the last few minutes, or working: she may be in it
  keep       in motion and touched this week, or ⏸️ (her on-purpose break,
             never nudged)
  ask        in motion and quiet for more than a week: close, park or keep?
             Her keep sticks: the row takes `chat sweep: kept YYYY-MM-DD`
             (`keep_line`), and the week counts from that day
  routine    a scheduled run: never swept

Duet's tasks are not swept (23 Nov 2026). No session list this sweep can read
shows them: not the cloud list (mine, with or without a tag filter) and not the
desktop one, and their rows carry no chat link. A Duet task is a branch that
closes itself and sends Duet one line (J17), so the sweep says once that they
are Duet's and never counts one as open or finished.

Rename (her yes, 16 Nov 2026): a chat to archive that isn't in the be•do form
is renamed first, and an open one with no be•do title gets ▶️ (it is not
archived, nothing is sent into it). The line carries `rename → <title>` and
the JSON a `rename` field. Never for a busy or scheduled chat, or today's my
day chat. The scheduled evening sweep never renames another chat (22 Nov
2026): it runs with `--no-rename`.

    python3 bedo_chats.py --sessions mine.json [--sessions other.json] (--live | --rows rows.json) [--now ISO] [--json] [--no-rename]

`mine.json` is `list_sessions` (mine) as it came, in either shape: the
desktop app's (`sessionId`, `isArchived`, `pinned`) or the cloud's
(`session_status`, `status_bucket`, `parent_session_id`, the `ui:pinned` tag),
bare or wrapped as `{"ccr": {"data": [...]}}`. A list with `has_more` is read
page by page (`after_id` = `last_id`), each page its own `--sessions`. Another surface's list
rides along as one more `--sessions`: a cloud session's own list, or claude.ai
read in the browser with her yes (chat-sweep/claude_ai_read.js: her plain
chats, cloud Code sessions and Cowork tasks, saved as `{"claude_ai": {"read":
[...], "data": [...]}}`). Each chat carries its surface (local, cloud, chat), and
a kind of chat no list covered gets a `not in this sweep:` line (27 Nov 2026). Rows are the ⚡ rows that carry a chat link,
from this week's base and the one before; `--live` reads them. Exit 2 when no
page given ends the list (read the next one), else exit 0 when
nothing is left for be•do to do, 1 otherwise.
"""
import datetime as dt, json, re, sys

from bedo_close import DRIVE_CODE, GLYPH, is_window, lead_glyph, next_step, objective
from bedo_entry import ACTION
from bedo_reader import FACTS, as_rows, load_local
from bedo_stretches import utc
import bedo_clock

C = FACTS['chats']
DONE, MOVING = '✅ done', '▶️ in motion'
TODO = ('archive', 'close_row', 'carry', 'entry', 'unpin')
ORDER = ('archive', 'close_row', 'carry', 'entry', 'unpin', 'hold', 'pinned', 'busy', 'keep', 'routine', 'ask')


def key_of(sid):
    """The id a chat link carries: local_…, session_… and cse_… all end the same."""
    s = (sid or '').strip()
    for p in ('local_', 'cse_', 'session_'):
        if s.startswith(p):
            return s[len(p):]
    return s


CLOUD = 'SESSION_STATUS_'
BUCKET = 'SESSION_STATUS_BUCKET_'


def surface_of(s):
    """Where a chat lives, which says how it is renamed, unpinned and archived:
    `local` (the desktop app's own sessions: its tools, nowhere else), `cloud`
    (a cloud Code or Cowork session: claude-code-remote's tools, or the browser
    on claude.ai), `chat` (a plain claude.ai chat: the browser only)."""
    if s.get('surface') in ('local', 'cloud', 'chat'):
        return s['surface']
    sid = str(s.get('sessionId') or s.get('id') or '')
    if s.get('sessionId') or sid.startswith('local_'):
        return 'local'
    if not sid and s.get('uuid'):
        return 'chat'
    return 'cloud'


def norm(s):
    """One chat from any list's shape: the desktop app's list_sessions, the
    cloud's (claude-code-remote), or claude.ai's own lists read in the browser
    (`chat_conversations`: uuid, name, is_starred, is_archived; `/v1/code/sessions`:
    status, a lower-case status_bucket, trigger_id, relations.parent_session_id)."""
    raw_tags = [str(t) for t in s.get('tags') or []]
    tags = [t.lower() for t in raw_tags]
    status = str(s.get('session_status') or '').upper()
    bucket = str(s.get('status_bucket') or '').upper()
    bucket = bucket[len(BUCKET):] if bucket.startswith(BUCKET) else bucket
    rel = s.get('relations') if isinstance(s.get('relations'), dict) else {}
    return {
        'id': s.get('sessionId') or s.get('id') or s.get('uuid') or '',
        'title': s.get('title') or s.get('name') or '',
        'surface': surface_of(s),
        # a temporary claude.ai chat is gone when she leaves it: nothing to sweep
        'archived': bool(s.get('isArchived') or s.get('is_archived') or s.get('is_temporary')
                         or s.get('status') == 'archived' or s.get('archived_at') or status == CLOUD + 'ARCHIVED'),
        'running': bool(s.get('isRunning') or status == CLOUD + 'RUNNING' or bucket == 'WORKING'),
        'bucket': bucket.lower() or None,
        'last': (s.get('lastActivityAt') or s.get('last_activity_at') or s.get('last_event_at')
                 or s.get('updated_at') or s.get('created_at')),
        'pinned': bool(s.get('pinned') or s.get('isPinned') or s.get('is_starred') or C['pin_tag'] in tags),
        'parent': (s.get('startedBy') or s.get('parentSessionId') or s.get('parent_session_id')
                   or rel.get('parent_session_id')),
        'routine': bool(s.get('scheduledTaskId') or s.get('trigger') or s.get('trigger_id')
                        or any(t in tags for t in C['routine_tags'])),
    }


def items_of(read):
    """The sessions in one saved list: a bare list, `.data` / `.sessions`, or
    the cloud tool's result wrapped as {"ccr": {"data": [...], "has_more", …}}."""
    if isinstance(read, list):
        return read
    if not isinstance(read, dict):
        return []
    for k in ('data', 'sessions'):
        if isinstance(read.get(k), list):
            return read[k]
    for v in read.values():   # one wrapper key, whatever the server is called
        if isinstance(v, (dict, list)):
            got = items_of(v)
            if got:
                return got
    return []


PAGING = ('has_more', 'next_cursor')


def page_of(read):
    """The paging part of one saved list ({has_more, last_id, …} from the
    session tools, {next_cursor} from claude.ai's /v1/code/sessions), or None."""
    r = read
    while isinstance(r, dict) and not any(k in r for k in PAGING) and len(r) == 1:
        r = next(iter(r.values()))
    return r if isinstance(r, dict) and any(k in r for k in PAGING) else None


def list_goes_on(reads):
    """Where to read on from when a list isn't whole, else None. Each kind of
    paging is its own list: the session tools' pages (has_more, last_id) end
    when one given says has_more false, and the last_id is returned; a claude.ai
    page with a next_cursor always has one more, returned as `cursor …`."""
    pages = [p for p in map(page_of, reads) if p is not None]
    tools = [p for p in pages if 'has_more' in p]
    if tools and all(p.get('has_more') for p in tools):
        return tools[-1].get('last_id') or '?'
    cur = [p['next_cursor'] for p in pages if 'has_more' not in p and p.get('next_cursor')]
    if cur:
        return 'cursor ' + str(cur[-1])
    return None


def chats_of(reads):
    """Every chat once, from one or more lists; the first list wins a duplicate."""
    out, seen = [], set()
    for read in reads:
        for s in items_of(read):
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


def local_day(t, local):
    """The day an instant falls on in her time zone."""
    t = utc(t) if isinstance(t, str) else t
    return (t + bedo_clock.offset(local, t)).date()


def touched_today(chat, now, local):
    return bool(chat.get('last')) and local_day(chat['last'], local) == local_day(now, local)


def never_unpinned(chat):
    t = (chat['title'] or '').lower()
    return any(w in t for w in C['never_unpin'])


def be_do_title(title, glyph, row=None):
    """The be•do form of a title: the glyph, a drive code only when the title or
    its row already shows one, then the title's own words. Never a guessed code."""
    words = (title or '').strip()
    marks = tuple(GLYPH.values())
    while words.startswith(marks):
        words = next(words[len(g):] for g in marks if words.startswith(g)).strip()
    words = words or 'untitled'
    m = None if DRIVE_CODE.search(words) else DRIVE_CODE.search((row or {}).get('title') or '')
    return f'{glyph} {m.group(0)} {words}' if m else f'{glyph} {words}'


def rename_for(chat, row, v, now, local):
    """The be•do title this chat should take before the sweep goes on, or None.
    Finished chats (to archive) take their closing glyph; an open chat with no
    status glyph takes ▶️. Never a busy or scheduled chat, today's my day chat,
    or one already in the form."""
    if v in ('busy', 'routine'):
        return None
    t, have = chat['title'], lead_glyph(chat['title'])
    if v in ('archive', 'close_row', 'carry'):
        if have in (GLYPH['done'], GLYPH['window_closed'], GLYPH['dropped']):
            return None
        if is_window(t):
            want = GLYPH['window_closed']
        elif (row or {}).get('status') == '✖️ dropped':
            want = GLYPH['dropped']
        else:
            want = GLYPH['done']
    else:
        if have or (never_unpinned(chat) and touched_today(chat, now, local)):
            return None
        want = GLYPH['moving']
    return be_do_title(t, want, row)


def sweep(chats, rows, now, local=None, rename=True):
    """[{id, title, verdict, why, next, row}] for every open chat. `local` is
    her settings, for the day in her time zone (the unpin rule)."""
    out = []
    for c in chats:
        if c['archived']:
            continue
        r = row_for(c, rows)
        v, why, nxt = verdict(c, r, now)
        unpin = c['pinned'] and v in ('archive', 'close_row', 'carry')
        if unpin:
            why += ' · pinned: unpin it, then archive'
        elif (c['pinned'] and v not in ('busy', 'routine') and not never_unpinned(c)
              and not touched_today(c, now, local)):
            # her amendment, 12 Nov 2026: pinned is what she's on today
            unpin = True
            if v == 'keep':
                v, why = 'unpin', 'pinned, not touched today: unpin it; it stays open in recents'
            else:
                why += ' · pinned, not touched today: unpin it'
        out.append({'id': c['id'], 'title': c['title'], 'surface': c['surface'], 'verdict': v, 'why': why,
                    'next': nxt, 'unpin': unpin,
                    'rename': rename_for(c, r, v, now, local) if rename else None,
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
    'archive': 'archive', 'close_row': 'close row', 'carry': 'carry on', 'entry': 'entry', 'unpin': 'unpin',
    'hold': 'hold', 'pinned': 'pinned', 'busy': 'busy', 'keep': 'keep', 'routine': 'routine', 'ask': 'ask',
}


MISSING = {
    'local': "the desktop app's own Code chats (only a Code-tab chat on the laptop reads them: list_sessions)",
    'cloud': 'cloud Code and Cowork sessions (claude.ai in the browser, her yes that turn: chat-sweep/claude_ai_read.js)',
    'chat': 'claude.ai chats (claude.ai in the browser, her yes that turn: chat-sweep/claude_ai_read.js)',
}


def surfaces_read(reads):
    """The surfaces the lists given cover: each chat's own, and any a saved read
    says it covered (claude_ai_read.js writes `read`, so a surface with nothing
    open still counts as read)."""
    got = set()
    def walk(r):
        if isinstance(r, dict):
            if isinstance(r.get('read'), list):
                got.update(str(x) for x in r['read'])
            for v in r.values():
                if isinstance(v, (dict, list)):
                    walk(v)
    for r in reads:
        walk(r)
        got.update(norm(s)['surface'] for s in items_of(r))
    return got


def render(found, now, given=None):
    """The sweep as she reads it. `given` is the surfaces the lists covered;
    each one missing gets a line saying where its chats are read."""
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
            out.append(f'  {SAY[x["verdict"]]:<9} “{x["title"][:60]}” — {x["why"]}'
                       + (f' · rename → {x["rename"]}' if x.get('rename') else ''))
            if x['next']:
                out.append(f'            next step for the new chat or row: {x["next"].lstrip("· ")}')
    n_arch = sum(x['verdict'] in ('archive', 'close_row', 'carry') for x in found)
    if n_arch:
        out.append(f'after: archived {n_arch} finished chat(s) — reversible with unarchive')
    pins = [x for x in found if x['unpin']]
    if pins:
        # a cloud chat's pin is its tag: set_session_tags remove it (tried and seen, 12 Nov 2026)
        out.append(f'unpin: {len(pins)} chat(s) — '
                   + ', '.join(f'“{x["title"][:40]}”' for x in pins))
        out.append(f'  cloud: set_session_tags remove ["{C["pin_tag"]}"] on '
                   + ' '.join(x['id'] for x in pins) + ' · desktop: set_pinned false')
    # 27 Nov 2026: claude.ai's chats and cloud sessions read in the browser are acted on there too
    web = [x for x in found if x.get('surface') in ('chat', 'cloud')
           and (x.get('rename') or x['unpin'] or x['verdict'] == 'archive')]
    if web:
        n = {k: sum(x['surface'] == k for x in web) for k in ('chat', 'cloud')}
        out.append(f'in the browser: {n["chat"]} claude.ai chat(s), {n["cloud"]} cloud session(s) to rename, unpin '
                   'or archive — chat-sweep/claude_ai_act.js with this sweep run again with --json '
                   '(or claude-code-remote\'s tools for a cloud session, where this chat has them)')
    # her sidebar holds all three (27 Nov 2026): a sweep of one is said to be one
    if given is not None:
        for k in ('local', 'cloud', 'chat'):
            if k not in given:
                out.append(f'not in this sweep: {MISSING[k]}')
    if not any(x['verdict'] in TODO for x in found):
        out.append('swept: nothing left for be•do')
    out.append(DUET_LINE)
    return '\n'.join(out)


DUET_LINE = "Duet's tasks: not in any session list here; each closes itself and tells Duet (J17)"


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
    ap.add_argument('--no-rename', action='store_true', help='the scheduled evening sweep: never renames another chat')
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
    reads = [json.load(open(p, encoding='utf-8')) for p in a.sessions]
    chats = chats_of(reads)
    found = sweep(chats, rows, now, local, rename=not a.no_rename)
    print(json.dumps(found, ensure_ascii=False, indent=1) if a.json else render(found, now, surfaces_read(reads)))
    # no page given ends the list (has_more false): it isn't whole, so the sweep isn't either
    left = list_goes_on(reads)
    if left:
        print(f'⚠ the list goes on: read the next page ({left if left.startswith('cursor ') else 'after_id ' + left}) and run again with it as another --sessions',
              file=sys.stderr)
        sys.exit(2)
    sys.exit(1 if any(x['verdict'] in TODO for x in found) else 0)


if __name__ == '__main__':
    main()
