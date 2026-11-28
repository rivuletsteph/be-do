# -*- coding: utf-8 -*-
"""The chat close in code (her rule, 25 Oct 2026: every chat ends the same
way, in order — QA, then the session entry, then the rename to done).

She starts it by saying *let's end the session*, or plainly that she's done
with the chat. Three checks, in her order:

  qa      a my day chat's day carries the dayqa marker line and the calsync
          marker line (the dusk close writes both; 19 Nov 2026, her words: a lot
          of the items on my calendar have not been checked off even though they
          were things that I did). Any other chat: the session entry passes the entry
          check, and (her rule, 25 Oct 2026) its first line under
          `what I did` names the objective and whether it was met —
          `· objective: <what it was> — met | partly met | not met, <why>` —
          and work not met names its next step under `still open`. A window
          chat takes no objective. A session with gaps (time spent, no end)
          names her stretches in its `[be•do]` block (`stretches: … = …`,
          from `bedo_stretches`) and its time spent is their sum
          (backlog 261024a, 25 Oct 2026: her time, not the session's).
          A session that opened or edited a pull request says its text passed
          the privacy check first: `· privacy: outgoing ok` (12 Nov 2026)
          A session that published a page says where it stands: `· page: built
          from the stream and main`, or where its fix lives, a row or a change in
          the build (23 Nov 2026: never only on the page she is looking at)
  entry   a session entry exists: an ⚡ action row whose `chat` is this chat
  title   the chat's status glyph matches the entry: ✔️ for a window chat,
          ☑️ for ✅ done, ▶️ ⏯️ or ⏸️ for work still in motion. A my day
          chat keeps ▶️ at its dusk close and takes ✔️ the next morning,
          once she has seen its page (J8; her yes, 11 Nov 2026)
  branches a my day chat's day closes only when every branch of that day
          (a chat titled ↳MMDD.n) has written its session entry and closed
          with ☑️ or ✔️ (her words, 18 Nov 2026: all of the branches for Monday
          need to write a session entry and close, and that needs to be
          codified). Pass the chat list with --sessions (list_sessions, mine,
          every page); without it the check says the list is missing

    python3 bedo_close.py --live --chat URL --title "TITLE" [--date YYYY-MM-DD] [--sessions page.json …]
    python3 bedo_close.py --rows rows.json --chat URL --title "TITLE" [--date …] [--sessions page.json …]

`--date` is a my day chat's own day (from its title); without it the check
reads the rows for the chat's entry wherever they are. Exit 0 when all three
pass, 1 when something is left to do; each FIX names the next step.
"""
import datetime as dt, json, re, sys

import bedo_stretches as ST
import bedo_clock  # the one clock
from bedo_entry import ACTION, problems
from bedo_reader import FACTS, as_rows, load_local

GLYPH = FACTS['chat_status']
WINDOWS = FACTS['window_chats']
MARKER = (FACTS['dayqa']['marker'],) + tuple(FACTS['dayqa'].get('old_markers') or ())   # braid shown; dayqa shown before 20 Nov
CAL_MARKER = FACTS['calsync']['marker']
DONE, MOVING = '✅ done', '▶️ in motion'


BRANCH = re.compile(r'↳\d{4}\.')                 # ↳1120.1: a branch of a my day, the preflight's own marker
DRIVE_CODE = re.compile(r'(?<![A-Za-z0-9])[A-Z]\d{1,3}\.\d{1,3}\b')   # D6.79, P03.13: a drive chat and its step


def is_window(title):
    """A window chat (my day, my week …) is read from what the title is, not
    its words: a branch marker or a drive code says it is not one, whatever
    else the title holds (9 and 21 Nov 2026: “My week page · be•do D6.79” and
    “↳1120.1 🏆 Fri 👁️ my day page” were each told to take ✔️)."""
    t = title or ''
    if BRANCH.search(t) or DRIVE_CODE.search(t):
        return False
    return any(w in t.lower() for w in WINDOWS)


def lead_glyph(title):
    """The status glyph the title opens with, or ''."""
    t = (title or '').strip()
    return next((g for g in GLYPH.values() if t.startswith(g)), '')


def still_its_night(day, now):
    """A my day chat's own day, or the small hours after it: its dusk close, not yet the
    morning she sees its page. `now` is the local wall clock; None says it is over."""
    if not (day and now):
        return False
    return (now - dt.timedelta(hours=FACTS['my_day_check']['night_ends_hour'])).date() <= day


def wanted_glyphs(title, entry_status, day=None, now=None):
    """The glyphs a closed chat may carry, given its entry. A my day chat (`day`) keeps its
    open glyph through its own night: the check waits for the next morning (J8)."""
    if is_window(title):
        return [GLYPH['moving']] if still_its_night(day, now) else [GLYPH['window_closed']]
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


OBJECTIVE = re.compile(r'^·\s*objective:\s*(?P<what>.+?)\s+—\s+(?P<verdict>partly met|not met|met)\b[\s,:;—-]*(?P<why>.*)$')
OBJECTIVE_LINE = '`· objective: <what it was> — met | partly met | not met, <why>`'


def hers(details):
    """The part of the details above the divider: her words."""
    return (details or '').split('———')[0]


def objective(details):
    """(objective, verdict, why) from the first line under `what I did`, or None."""
    lines = [l.strip() for l in hers(details).splitlines()]
    if 'what I did' not in lines:
        return None
    first = next((l for l in lines[lines.index('what I did') + 1:] if l), '')
    m = OBJECTIVE.match(first)
    return (m['what'].strip(), m['verdict'], m['why'].strip()) if m else None


def next_step(details):
    """The first line under `still open`, unless it says none."""
    lines = [l.strip() for l in hers(details).splitlines()]
    if 'still open' not in lines:
        return None
    first = next((l for l in lines[lines.index('still open') + 1:] if l), '')
    return first if first.lstrip('· ').strip().lower() not in ('', 'none') else None


def objective_qa(entry):
    """(ok, why) for the objective: named, judged, and a next step when not met."""
    o = objective(entry.get('details'))
    if not o:
        return False, (f'the entry\'s first line under `what I did` is the objective and whether it was met: '
                       f'{OBJECTIVE_LINE} — the one set at the open, or the one the chat worked toward when none was')
    what, verdict, why = o
    if not why:
        return False, f'say why it was {verdict}, in a clause after the verdict'
    if verdict != 'met' and not next_step(entry.get('details')):
        return False, f'{verdict}: name the next step under `still open`'
    return True, f'objective {verdict} — {what}'


def stretches_qa(entry, offset_hours):
    """None, or what a session with gaps still owes: her stretches named, and
    a time spent that is their sum. One stretch keeps a real start and end."""
    spent, end = entry.get('time_spent'), entry.get('end')
    if end or spent in (None, ''):
        return None
    when = entry.get('datetime')
    anchor = bedo_clock.to_local(offset_hours or 0, when) if when else None   # the settings or a number
    spans = ST.from_details(entry.get('details'), anchor)
    if not spans:
        return ('name her stretches in the `[be•do]` block: run `stretches` on this chat\'s transcript with '
                '`--day` and copy its `stretches:` line — the time spent is their sum, never the envelope')
    named = round(sum((b - a).total_seconds() for a, b in spans) / 60)
    if abs(round(float(spent) / 60) - named) > 1:
        return f'time spent {ST.hm(round(float(spent) / 60))} is not the sum of her stretches, {ST.hm(named)}'
    return None


PULL = re.compile(r'github\.com/[\w.-]+/[\w.-]+/pull/\d+')
PRIVACY_LINE = '`· privacy: outgoing ok`'


def privacy_qa(entry):
    """None, or what a session with a pull request still owes (12 Nov 2026, her words:
    the privacy check only scans repo files, so PR titles, descriptions and commit
    messages slip through): the line saying `outgoing` passed its text before it went."""
    text = ' '.join(str(entry.get(k) or '') for k in ('deliverable', 'details'))
    if not PULL.search(text):
        return None
    if re.search(r'^·\s*privacy:\s*outgoing ok\b', entry.get('details') or '', re.M):
        return None
    return (f'this session has a pull request: run `outgoing` on its title, description, commits and branch '
            f'(fix any hit on GitHub too), then add {PRIVACY_LINE} under `what I did`')


PAGE = re.compile(r'claude\.ai/(?:code/)?artifact/[\w-]+')
PAGE_LINES = ('`· page: built from the stream and main`',
              '`· page: fix in the stream, rec…` and/or `· page: fix in the build, <pull request or commit>`')
_PAGE_OK = re.compile(r'^·\s*page:\s*(built from the stream and main\b'
                      r'|fix in the stream\b.*\brec\w{6,}'
                      r'|fix in the build\b.*(github\.com/\S+|\b[0-9a-f]{7,40}\b))', re.M)


def page_qa(entry):
    """None, or what a session that published a page still owes (23 Nov 2026, her words:
    fixes land in the stream and the stable build, not only on the page I'm looking at).
    A page is only ever the stream drawn by the build on main. So a session with a page
    says which it was: built as is, or fixed, and where the fix lives: the row it wrote
    or the change it pushed. A page patched by hand loses the fix at its next build."""
    text = ' '.join(str(entry.get(k) or '') for k in ('deliverable', 'details'))
    if not PAGE.search(text):
        return None
    if _PAGE_OK.search(entry.get('details') or ''):
        return None
    return (f'this session published a page: say where it stands under `what I did`: {PAGE_LINES[0]}, or, when '
            f'something on it was fixed, {PAGE_LINES[1]}. A fix made only on the page is redone in the row or the '
            f'build, and the page rebuilt, before this closes')


def qa_done(rows, day, marker=MARKER):
    """The dayqa marker for `day` (or another check's `marker`) in any row's details (the dusk close carries it)."""
    want = tuple(f'{m} {day.isoformat()}' for m in ((marker,) if isinstance(marker, str) else marker))
    return next((l.strip() for r in rows for l in (r.get('details') or '').splitlines() if l.strip().startswith(want)),
                None)


# closed: done, a window closed, dropped, or handed to a new chat with its next push (⏯️, the work carried on a row)
CLOSED = (GLYPH['done'], GLYPH['window_closed'], GLYPH['dropped'], GLYPH['next_push'])


def session_list(pages):
    """Sessions from list_sessions pages as they came (bare or wrapped as {"ccr": {...}}): [{id, title}]."""
    out = []
    for d in pages or []:
        d = d.get('ccr', d) if isinstance(d, dict) else d
        out += (d.get('data') if isinstance(d, dict) else d) or []
    return out


def branches_qa(rows, day, sessions):
    """[(title, what's missing)] for each branch of `day` (↳MMDD.n) that has not written its session entry
    or not closed (18 Nov 2026: Monday's GLO2 map branch sat open with no entry, and the day page showed
    nothing of her hour of work in it)."""
    tag = re.compile(r'↳' + day.strftime('%m%d') + r'\.\d+')
    chats = ' '.join(r.get('chat') or '' for r in rows)
    out = []
    for x in sessions:
        t = x.get('title') or ''
        if not tag.search(t):
            continue
        sid = (x.get('id') or '').strip()
        miss = ([] if sid and sid in chats else ['its session entry']) + \
               ([] if lead_glyph(t) in CLOSED else ['its close (☑️)'])
        if miss:
            out.append((t, ' and '.join(miss)))
    return out


def findings(rows, chat_url, title, day=None, local=None, now=None, sessions=None):
    """[(ok, what, why)] in her order: qa, entry, title."""
    local = local or {}
    out = []
    entry = session_entry(rows, chat_url)

    if day:
        line, cal = qa_done(rows, day), qa_done(rows, day, CAL_MARKER)
        owed = ([] if line else [f'run the 🔀 braid (`dayqa {day.isoformat()}`), write what she accepts, '
                                 f'and put its last line in the dusk close row']) + \
               ([] if cal else [f'run `calsync {day.isoformat()}`, make its changes on the calendar, '
                                f'and put its marker line in the dusk close row'])
        out.append((not owed, 'QA', '; '.join(owed) or f'{line} · {cal}'))
    elif entry:
        clock = None if bedo_clock.problem(local) else local   # time_zone, per instant; None skips the clock rules
        p = problems(entry, None, clock, local.get('weekly_name', 'w{n} be•do'))
        ok, why = (True, 'the session entry passes the entry check') if is_window(title) else objective_qa(entry)
        gaps = None if is_window(title) else stretches_qa(entry, clock)
        private = privacy_qa(entry)
        paged = None if is_window(title) else page_qa(entry)
        issues = (p + ([] if ok else [why]) + ([gaps] if gaps else []) + ([private] if private else [])
                  + ([paged] if paged else []))
        out.append((not issues, 'QA', '; '.join(issues) or why))
    else:
        out.append((False, 'QA', 'nothing to check yet — the session entry comes next, then this runs on it'))

    if day and is_window(title) and sessions is not None:
        if sessions == 'missing':
            out.append((False, 'branches', 'pass the chat list (--sessions, every page of list_sessions mine) so '
                                           "the day's branches can be checked"))
        else:
            left = branches_qa(rows, day, sessions)
            out.append((not left, 'branches', 'every branch of the day wrote its entry and closed' if not left else
                        '; '.join(f'“{t}” needs {m}' for t, m in left) +
                        ' — message each to write its entry and close, carrying what is still open'))

    if entry:
        out.append((True, 'session entry', f'{entry.get("key") or "?"} · {entry.get("status")} · {entry.get("title")}'))
    else:
        out.append((False, 'session entry', 'write it (the session-entry skill): no ⚡ action row carries this chat'))

    want = wanted_glyphs(title, entry.get('status') if entry else None, day, now)
    tonight = is_window(title) and still_its_night(day, now)
    have = lead_glyph(title)
    if not entry:
        out.append((False, 'title', 'rename once the entry is written'))
    elif have in want:
        out.append((True, 'title', f'{have} — {title}' + (
            f' · it stays {have} tonight and takes {GLYPH["window_closed"]} in the morning, once she has '
            f'seen its page' if tonight else '')))
    elif tonight:
        out.append((False, 'title', f'rename: it opens with {have or "no status glyph"}; a my day chat keeps '
                                    f'{want[0]} at its dusk close — {GLYPH["window_closed"]} is for the '
                                    f'morning, once she has seen its page'))
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
    ap.add_argument('--sessions', action='append', help='a page of list_sessions (mine), as it came; give every page')
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
    # the local clock, for a my day chat: its own night keeps ▶️, the morning after wants ✔️
    now = None if bedo_clock.problem(local) else bedo_clock.now_local(local)
    # a my day chat's close always checks its branches: without the list it says the list is missing
    sessions = (session_list([json.load(open(f, encoding='utf-8')) for f in a.sessions]) if a.sessions
                else 'missing' if day and is_window(a.title) else None)
    found = findings(rows, a.chat, a.title, day, local, now, sessions)
    print(render(a.title, found))
    sys.exit(0 if all(ok for ok, _, _ in found) else 1)


if __name__ == '__main__':
    main()
