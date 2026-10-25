# -*- coding: utf-8 -*-
"""The chat close in code (her rule, 25 Oct 2026: every chat ends the same
way, in order — QA, then the session entry, then the rename to done).

She starts it by saying *let's end the session*, or plainly that she's done
with the chat. Three checks, in her order:

  qa      a my day chat's day carries the dayqa marker line (the dusk close
          writes it); any other chat's session entry passes the entry check,
          the best QA such a chat allows
  entry   a session entry exists: an ⚡ action row whose `chat` is this chat
  title   the chat's status glyph matches the entry: ✔️ for a window chat,
          ☑️ for ✅ done, ▶️ ⏯️ or ⏸️ for work still in motion

    python3 bedo_close.py --live --chat URL --title "TITLE" [--date YYYY-MM-DD]
    python3 bedo_close.py --rows rows.json --chat URL --title "TITLE" [--date …]

`--date` is a my day chat's own day (from its title); without it the check
reads the rows for the chat's entry wherever they are. Exit 0 when all three
pass, 1 when something is left to do; each FIX names the next step.
"""
import datetime as dt, json, sys

from bedo_entry import ACTION, problems
from bedo_reader import FACTS, as_rows, load_local

GLYPH = FACTS['chat_status']
WINDOWS = FACTS['window_chats']
MARKER = FACTS['dayqa']['marker']
DONE, MOVING = '✅ done', '▶️ in motion'


def is_window(title):
    t = (title or '').lower()
    return any(w in t for w in WINDOWS)


def lead_glyph(title):
    """The status glyph the title opens with, or ''."""
    t = (title or '').strip()
    return next((g for g in GLYPH.values() if t.startswith(g)), '')


def wanted_glyphs(title, entry_status):
    """The glyphs a closed chat may carry, given its entry."""
    if is_window(title):
        return [GLYPH['window_closed']]
    if entry_status == DONE:
        return [GLYPH['done']]
    if entry_status == MOVING:
        return [GLYPH['moving'], GLYPH['next_push'], GLYPH['break']]
    return [GLYPH['dropped']] if entry_status == '✖️ dropped' else []


def session_entry(rows, chat_url):
    """The newest ⚡ action row that carries this chat's link."""
    mine = [r for r in rows if (r.get('practice') or '').strip() == ACTION
            and chat_url and chat_url.rstrip('/') == (r.get('chat') or '').strip().rstrip('/')]
    return max(mine, key=lambda r: r.get('created') or '', default=None)


def qa_done(rows, day):
    """The dayqa marker for `day` in any row's details (the dusk close carries it)."""
    want = f'{MARKER} {day.isoformat()}'
    return next((l.strip() for r in rows for l in (r.get('details') or '').splitlines() if l.strip().startswith(want)),
                None)


def findings(rows, chat_url, title, day=None, local=None):
    """[(ok, what, why)] in her order: qa, entry, title."""
    local = local or {}
    out = []
    entry = session_entry(rows, chat_url)

    if day:
        line = qa_done(rows, day)
        out.append((bool(line), 'QA', line or f'run `dayqa {day.isoformat()}`, write what she accepts, '
                                               f'and put its last line in the dusk close row'))
    elif entry:
        p = problems(entry, None, local.get('utc_offset_hours'), local.get('weekly_name', 'w{n} be•do'))
        out.append((not p, 'QA', 'the session entry passes the entry check' if not p else '; '.join(p)))
    else:
        out.append((False, 'QA', 'nothing to check yet — the session entry comes next, then this runs on it'))

    if entry:
        out.append((True, 'session entry', f'{entry.get("key") or "?"} · {entry.get("status")} · {entry.get("title")}'))
    else:
        out.append((False, 'session entry', 'write it (the session-entry skill): no ⚡ action row carries this chat'))

    want = wanted_glyphs(title, entry.get('status') if entry else None)
    have = lead_glyph(title)
    if not entry:
        out.append((False, 'title', 'rename once the entry is written'))
    elif have in want:
        out.append((True, 'title', f'{have} — {title}'))
    else:
        out.append((False, 'title', f'rename: it opens with {have or "no status glyph"}; '
                                    f'a {"window chat" if is_window(title) else entry.get("status")} '
                                    f'wants {" or ".join(want) or "a status glyph"}'))
    return out


def render(title, found):
    lines = [f'close · {title}']
    lines += [f'{"ok " if ok else "FIX"}   {what} — {why}' for ok, what, why in found]
    left = [what for ok, what, _ in found if not ok]
    lines.append('closed: QA, entry, title' if not left else f'still to do, in order: {", ".join(left)}')
    return '\n'.join(lines)


def live_rows(local, chat_url, day):
    """The rows that can answer: the chat's day (for the QA marker) and every
    ⚡ row carrying its link, from this week's base and the one before."""
    import bedo_air
    from bedo_entry import week_number
    air = bedo_air.Air()
    names = air.bases()
    recs = []
    if day:
        recs += bedo_air.read_day(air, local, day, names)[0]['records']
    today = dt.date.today()
    f = local['stream_fields']['chat']
    for d in {today, today - dt.timedelta(days=7)} | ({day} if day else set()):
        base = names.get(local.get('weekly_name', 'w{n} be•do').format(n=week_number(d)))
        if base:
            recs += air.records(base, local['stream_table'], formula=f'FIND("{chat_url}", {{{f}}})', by_id=True)
    seen, uniq = set(), []
    for r in recs:
        if r['id'] not in seen:
            seen.add(r['id']); uniq.append(r)
    return as_rows(uniq, local['stream_fields'])


def main():
    import argparse
    ap = argparse.ArgumentParser(description='the chat close: QA, session entry, title')
    ap.add_argument('--chat', required=True, help="the chat's URL, as the entry's chat field carries it")
    ap.add_argument('--title', required=True, help="the chat's title now")
    ap.add_argument('--date', help="a my day chat's own day, YYYY-MM-DD")
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--rows', help='a read of the rows, as rows (logical names) or a dump')
    a = ap.parse_args()
    local = load_local()
    day = dt.date.fromisoformat(a.date) if a.date else None
    if a.live:
        rows = live_rows(local, a.chat, day)
    elif a.rows:
        d = json.load(open(a.rows, encoding='utf-8'))
        recs = d.get('records') if isinstance(d, dict) else d
        rows = as_rows(recs, local['stream_fields']) if recs and 'fields' in recs[0] else recs
    else:
        sys.exit('give --live, or --rows')
    found = findings(rows, a.chat, a.title, day, local)
    print(render(a.title, found))
    sys.exit(0 if all(ok for ok, _, _ in found) else 1)


if __name__ == '__main__':
    main()
