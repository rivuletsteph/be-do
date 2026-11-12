# -*- coding: utf-8 -*-
"""The weekly drive cleanup: the open rows the split carried, a drive or two
at a time (her amendment, 9 Nov 2026).

Her words, the Monday after a split carried 396 open rows: I noticed over 300
lines got carried to the new week, and that seems like a lot … it needs to
happen on a weekly basis. The monthly ahead-review (J11) sweeps everything by
the 5th; this keeps the pile small in between, as a step of the weekly close,
run on the new week's base right after the split.

What it does, so a chat never builds it by hand:

  big picture  every open row in the live base, counted: ▫️ potentials (the
               season review's), queue-ticked rows (hers), rows waiting on
               someone, fresh rows (14 days or younger) — and what is left,
               the stale ⬜ and ▶️, by drive, with the oldest named
  the pick     rows with no drive always come first (bucketing is be•do's
               call, J12); then the stalest drives, rotating: a drive whose
               rows carry a cleanup line from the last three weeks waits its
               turn, and a row reviewed in the last four weeks isn't asked
               again
  evidence     before she sees anything: a key closed on another row (in any
               base read), a ✅ row in the same drive sharing the open row's
               uncommon words, two open rows that say the same thing (a
               dedupe, the one ✖️ be•do writes, named as one), and reading or
               media that belongs in the stories queue (her rule, 9 Nov)

It proposes; it never writes. Every change goes through the entry check and,
from a branch, to the my day chat. ✖️ dropped, ⏸️ and the queue box stay hers.

    python3 bedo_cleanup.py --live [--drives 2] [--json]
    python3 bedo_cleanup.py --stream live.json --stream last_week.json [--today YYYY-MM-DD]
"""
import datetime as dt, json, re, sys

from bedo_reader import FACTS, as_rows, load_local, merge_live_first, offset_hours

STALE_DAYS = 14          # J11: the ahead-review's line, kept the same
ROTATE_DAYS = 21         # a drive cleaned this recently waits its turn
REVIEWED_DAYS = 28       # a row confirmed this recently isn't asked again
MARK = '[be•do] drive cleanup, '
OPEN = set(FACTS['status']['open'])
CLOSED = set(FACTS['status']['closed'])
DONE = FACTS['status']['actions'][3]           # ✅ done
POTENTIAL, INTENTION, MOTION = FACTS['status']['open']
MEDIA = set(FACTS['practice']['media'])
_MONTHS = {m: i for i, m in enumerate(
    'jan feb mar apr may jun jul aug sep oct nov dec'.split(), 1)}
_WATCH = re.compile(r'^\W*(watch|read|listen to|finish)\b(?! for\b)', re.I)
_MEDIA_WORDS = re.compile(r'\b(article|episode|podcast|recording|video|demo|webinar|newsletter|piece|book|audiobook|essay|post)\b', re.I)
_STOP = set('''a an the and or of to for in on at by with from into my our your their his her its this that
these those is are be it as up out about after before over again just get make do take send ask find
check see look new next more some all any one two three'''.split())


def _status(v):
    return (v or '').strip()


def born(row):
    """When a chain began: its key's YYMMDD when it has one, else its datetime."""
    m = re.match(r'(\d{2})(\d{2})(\d{2})_', row.get('key') or '')
    if m:
        try:
            return dt.date(2000 + int(m[1]), int(m[2]), int(m[3]))
        except ValueError:
            pass
    s = row.get('datetime')
    return dt.date.fromisoformat(s[:10]) if s else None


def cleaned_on(row):
    """The dates this row was reviewed: its cleanup lines ('[be•do] drive cleanup,
    Mon 9 Nov 2026 (…): ⬜ kept, her yes'). A line that only placed the row under a
    drive ('drive set to …') is bucketing, not a review, and doesn't count."""
    out = []
    for m in re.finditer(re.escape(MARK) + r'(?:\w+ )?(\d{1,2}) (\w{3})\w* (\d{4})[^:\n]*:\s*(.{0,14})', row.get('details') or ''):
        if m[4].startswith('drive set to'):
            continue
        mo = _MONTHS.get(m[2].lower()[:3])
        if mo:
            out.append(dt.date(int(m[3]), mo, int(m[1])))
    return out


def words(text):
    """The uncommon words of a title: lowercased, no glyphs, no stop words."""
    return {w for w in re.findall(r"[a-z0-9][a-z0-9'’-]{2,}", (text or '').lower()) if w not in _STOP}


def is_media(row):
    """Reading or media that belongs in the stories queue (her rule, 9 Nov 2026):
    a media practice, or a title that is plainly reading, watching or listening
    to something. 'Watch for …' is keeping an eye out, not media."""
    if (row.get('practice') or '') in MEDIA:
        return True
    t = row.get('title') or ''
    return bool(_WATCH.search(re.sub(r'^\W+', '', t)) and _MEDIA_WORDS.search(t))


def picture(rows, today):
    """Every open row, sorted into what the cleanup leaves alone and what it looks at."""
    out = dict(open=[], potential=[], queue=[], waiting=[], fresh=[], stale=[])
    for r in rows:
        s = _status(r.get('status'))
        if s not in OPEN:
            continue
        out['open'].append(r)
        b = born(r)
        r['age'] = (today - b).days if b else None
        if s == POTENTIAL:
            out['potential'].append(r)
        elif r.get('queue'):
            out['queue'].append(r)
        elif r.get('waiting_on'):
            out['waiting'].append(r)
        elif r['age'] is not None and r['age'] <= STALE_DAYS:
            out['fresh'].append(r)
        else:
            out['stale'].append(r)
    return out


def by_drive(rows):
    d = {}
    for r in rows:
        d.setdefault((r.get('rhythm') or '').strip(), []).append(r)
    return d


def pick(stale, today, n=2):
    """This week's drives: the undriven first, then the n stalest drives not
    cleaned in the last ROTATE_DAYS. Stalest = most stale rows, then the oldest."""
    groups = by_drive(stale)
    undriven = groups.pop('', [])
    def cleaned_lately(rs):
        """Most of the drive's stale rows were reviewed in the last ROTATE_DAYS."""
        hit = sum(1 for r in rs if any((today - d).days < ROTATE_DAYS for d in cleaned_on(r)))
        return hit * 2 >= len(rs)
    ready = [(k, rs) for k, rs in groups.items() if not cleaned_lately(rs)]
    ready.sort(key=lambda kv: (-len(kv[1]), -max((r['age'] or 0) for r in kv[1]), kv[0]))
    return undriven, ready[:n], [k for k, rs in groups.items() if (k, rs) not in ready]


def evidence(row, everything, drive_rows):
    """Why be•do would close or fold this row, from the record. Returns a list of
    (kind, text, other_id): 'done' — its key closed elsewhere, or a ✅ in its drive
    sharing its uncommon words since it began; 'dedupe' — another open row in the
    drive saying the same thing; 'media' — reading or watching for the stories queue."""
    out = []
    key, me = row.get('key'), row['id']
    b = born(row)
    for o in everything:
        if o['id'] == me:
            continue
        if key and o.get('key') == key and _status(o.get('status')) in CLOSED:
            out.append(('done', f"its key is closed {_status(o.get('status'))} on “{(o.get('title') or '')[:60]}”", o['id']))
    mine = words(row.get('title'))
    if len(mine) >= 2:
        for o in everything:
            if o['id'] == me or _status(o.get('status')) != DONE:
                continue
            if (o.get('rhythm') or '') != (row.get('rhythm') or ''):
                continue
            ob = born(o)
            if b and ob and ob < b:
                continue
            shared = mine & words(o.get('title'))
            if len(shared) >= 2 and len(shared) >= len(mine) / 2:
                out.append(('done', f"a ✅ in its drive shares {', '.join(sorted(shared))}: “{(o.get('title') or '')[:60]}”", o['id']))
        for o in drive_rows:
            if o['id'] == me or o['id'] < me:
                continue          # each pair once
            theirs = words(o.get('title'))
            shared = mine & theirs
            if len(shared) >= 3 and len(shared) >= 0.6 * min(len(mine), len(theirs)):
                out.append(('dedupe', f"says the same as “{(o.get('title') or '')[:60]}”", o['id']))
    if is_media(row):
        out.append(('media', 'reading or media: a stories row (want), its stream row closed as moved', None))
    return out


def recently_reviewed(row, today):
    return any((today - d).days < REVIEWED_DAYS for d in cleaned_on(row))


def run(rows, today, n=2):
    """The whole report as data: the picture, the pick, and per row the evidence."""
    pic = picture(rows, today)
    undriven, drives, waiting_turn = pick(pic['stale'], today, n)
    def card(r, drive_rows):
        return dict(id=r['id'], key=r.get('key'), title=r.get('title'), status=_status(r.get('status')),
                    age=r.get('age'), drive=r.get('rhythm') or '',
                    evidence=[dict(kind=k, why=w, other=o) for k, w, o in evidence(r, rows, drive_rows)])
    week = []
    if undriven:
        week.append(dict(drive='', rows=[card(r, undriven) for r in sorted(undriven, key=lambda r: -(r['age'] or 0))]))
    for k, rs in drives:
        keep = [r for r in rs if not recently_reviewed(r, today)]
        if keep:
            week.append(dict(drive=k, rows=[card(r, rs) for r in sorted(keep, key=lambda r: -(r['age'] or 0))]))
    counts = sorted(((k or '(no drive)', len(v)) for k, v in by_drive(pic['stale']).items()), key=lambda kv: (-kv[1], kv[0]))
    oldest = sorted(pic['stale'], key=lambda r: -(r['age'] or 0))[:3]
    return dict(today=str(today),
                counts={k: len(v) for k, v in pic.items()},
                by_drive=counts,
                oldest=[dict(id=r['id'], title=r.get('title'), age=r.get('age'), drive=r.get('rhythm') or '') for r in oldest],
                waiting_turn=sorted(waiting_turn),
                week=week)


def render(rep, base=''):
    c = rep['counts']
    lines = [f"cleanup {base} · {c['open']} open: {c['potential']} ▫️ for the season review · {c['queue']} queue (hers) · "
             f"{c['waiting']} waiting on someone · {c['fresh']} fresh (≤{STALE_DAYS} d) → {c['stale']} stale ⬜/▶️",
             'by drive: ' + ' · '.join(f'{n} {k}' for k, n in rep['by_drive'][:12])
             + (f" · +{len(rep['by_drive']) - 12} more" if len(rep['by_drive']) > 12 else ''),
             'oldest: ' + ' · '.join(f"{(o['title'] or '')[:50]} ({o['age']} d)" for o in rep['oldest'])]
    if rep['waiting_turn']:
        lines.append('cleaned in the last 3 weeks, waiting their turn: ' + ' · '.join(rep['waiting_turn']))
    lines.append('this week: ' + (' · '.join(f"{g['drive'] or 'no drive (be•do places these)'} ({len(g['rows'])})" for g in rep['week']) or 'nothing stale'))
    for g in rep['week']:
        lines.append('')
        lines.append(f"  {g['drive'] or 'no drive'}")
        for r in g['rows']:
            tag = ', '.join(sorted({e['kind'] for e in r['evidence']})) or 'call'
            lines.append(f"    {r['status'][:2]} {r['age'] if r['age'] is not None else '?':>3} d  [{tag}]  {(r['title'] or '')[:70]}  · {r['id']}")
            for e in r['evidence']:
                lines.append(f"           {e['kind']}: {e['why']}")
    lines.append('')
    lines.append("Next: make the call on each row (done · keep · ▫️ · fold · to stories), show her one drive at a time, "
                 "write only what she confirms, each row through `entry`. ✖️ and ⏸️ are hers.")
    return '\n'.join(lines)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the weekly drive cleanup: what the split carried, a drive or two at a time')
    ap.add_argument('--live', action='store_true', help='read the live weekly base and the one before it')
    ap.add_argument('--stream', action='append', default=[], help='a complete read of a weekly base, live first')
    ap.add_argument('--today', help='YYYY-MM-DD, her local date (default: now)')
    ap.add_argument('--drives', type=int, default=2, help='how many drives this week, besides the undriven')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    fields = {**{k: k for k in ('datetime', 'status', 'title', 'key', 'practice', 'rhythm',
                                'details', 'queue', 'waiting_on')},
              **{k: v for k, v in L.get('stream_fields', {}).items()
                 if k in ('datetime', 'status', 'title', 'key', 'practice', 'rhythm', 'details', 'queue', 'waiting_on')}}
    now = dt.datetime.now(dt.timezone.utc)
    today = dt.date.fromisoformat(a.today) if a.today else (now + dt.timedelta(hours=offset_hours(L, now))).date()
    base = ''
    if a.live:
        from bedo_air import Air
        from bedo_entry import week_number
        air = Air()
        names = air.bases()
        n = week_number(today)
        wanted = [L.get('weekly_name', 'w{n} be•do').format(n=k) for k in (n, n - 1)]
        sources = [air.dump(names[w], L['stream_table'], by_id=True) for w in wanted if w in names]
        base = wanted[0]
        if not sources:
            sys.exit(f'no weekly base named {wanted[0]}')
    else:
        if not a.stream:
            sys.exit('give --live, or --stream (the live base first, then older ones for evidence)')
        sources = a.stream
    recs, reads = merge_live_first(sources)
    every = as_rows(recs, fields)
    live_ids = {r['id'] for r in merge_live_first(sources[:1])[0]}
    for r in every:
        r['queue'] = r.get('queue') in (True, 'true', 'True', '1', 1, '✓', 'checked')
    live = [r for r in every if r['id'] in live_ids]
    rep = run(live, today, a.drives)
    # evidence reads every base given, not only the live one
    pic_ids = {c['id'] for g in rep['week'] for c in g['rows']}
    if len(sources) > 1:
        by_id = {r['id']: r for r in live}
        groups = by_drive([by_id[i] for i in pic_ids])
        for g in rep['week']:
            for c in g['rows']:
                r = by_id[c['id']]
                c['evidence'] = [dict(kind=k, why=w, other=o) for k, w, o in evidence(r, every, groups.get(r.get('rhythm') or '', []))]
    if a.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1))
    else:
        print(render(rep, base))


if __name__ == '__main__':
    main()
