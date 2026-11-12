# -*- coding: utf-8 -*-
"""The chat close in code (her rule, 25 Oct 2026: every chat ends the same
way, in order — QA, then the session entry, then the rename to done).

She starts it by saying *let's end the session*, or plainly that she's done
with the chat. Three checks, in her order:

  qa      a my day chat's day carries the dayqa marker line (the dusk close
          writes it). Any other chat: the session entry passes the entry
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
  entry   a session entry exists: an ⚡ action row whose `chat` is this chat
  title   the chat's status glyph matches the entry: ✔️ for a window chat,
          ☑️ for ✅ done, ▶️ ⏯️ or ⏸️ for work still in motion. A my day
          chat keeps ▶️ at its dusk close and takes ✔️ the next morning,
          once she has seen its page (J8; her yes, 11 Nov 2026)

    python3 bedo_close.py --live --chat URL --title "TITLE" [--date YYYY-MM-DD]
    python3 bedo_close.py --rows rows.json --chat URL --title "TITLE" [--date …]

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
MARKER = FACTS['dayqa']['marker']
DONE, MOVING = '✅ done', '▶️ in motion'


def is_window(title):
    t = (title or '').lower()
    return any(w in t for w in WINDOWS)


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


def qa_done(rows, day):
    """The dayqa marker for `day` in any row's details (the dusk close carries it)."""
    want = f'{MARKER} {day.isoformat()}'
    return next((l.strip() for r in rows for l in (r.get('details') or '').splitlines() if l.strip().startswith(want)),
                None)


def findings(rows, chat_url, title, day=None, local=None, now=None):
    """[(ok, what, why)] in her order: qa, entry, title."""
    local = local or {}
    out = []
    entry = session_entry(rows, chat_url)

    if day:
        line = qa_done(rows, day)
        out.append((bool(line), 'QA', line or f'run `dayqa {day.isoformat()}`, write what she accepts, '
                                               f'and put its last line in the dusk close row'))
    elif entry:
        clock = None if bedo_clock.problem(local) else local   # time_zone, per instant; None skips the clock rules
        p = problems(entry, None, clock, local.get('weekly_name', 'w{n} be•do'))
        ok, why = (True, 'the session entry passes the entry check') if is_window(title) else objective_qa(entry)
        gaps = None if is_window(title) else stretches_qa(entry, clock)
        private = privacy_qa(entry)
        issues = p + ([] if ok else [why]) + ([gaps] if gaps else []) + ([private] if private else [])
        out.append((not issues, 'QA', '; '.join(issues) or why))
    else:
        out.append((False, 'QA', 'nothing to check yet — the session entry comes next, then this runs on it'))

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
    found = findings(rows, a.chat, a.title, day, local, now)
    print(render(a.title, found))
    sys.exit(0 if all(ok for ok, _, _ in found) else 1)


if __name__ == '__main__':
    main()
