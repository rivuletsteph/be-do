# -*- coding: utf-8 -*-
"""The drive check: everything she puts real effort into has a drive, and every
drive has a goal and a timeline (her words, 10 Nov 2026).

Her words, Tue 10 Nov 2026: my goal here is to make sure everything I'm putting
significant effort into has a drive associated with it, and it's clear what the
goal is and what the timeline is.

Two flags, read from the rhythms base and the stream, never from memory:

  undriven   effort carrying only a rhythm (one of the eight ♒), where a drive
             belongs:
               · a work or build row of about 30 minutes or more (WORK_MIN) —
                 an ⚡ action, or any lived row under the work rhythm
               · rows that come back toward one end: three or more rows under
                 the same rhythm sharing an uncommon word (RECUR_N)
             Tending is left alone — upkeep that comes around (email, dishes, a
             bill, an everyday meal) belongs on a rhythm by her rule. A row whose
             `how` says tend is never flagged; once rows carry `how`, a grow row
             on a bare rhythm always is.
  unfinished an active ♐ drive with no goal (nothing above the divider), or no
             target date unless its open-ended box is ticked (open-ended only
             when she says so). Each comes with what its rows say: open rows,
             the last thing done, and the latest target among its open rows —
             the timeline be•do proposes when it has one.

Also named, so the base gets fixed rather than quietly tolerated: rows whose
rhythm/drive names nothing active (a renamed bucket, a typo).

It proposes; it never writes. A goal or a date is hers: she accepts or adjusts
the list, and only then is the rhythms row written.

    python3 bedo_drive_check.py --rhythms rhythms.json --stream live.json [--stream older.json] [--today YYYY-MM-DD] [--json]
"""
import datetime as dt, json, re, sys

from bedo_reader import FACTS, cells, sv, complete, merge_live_first, load_local, offset_hours

WORK_MIN = 30            # her "about 30 min"
RECUR_N = 3              # rows sharing a word under one rhythm before it reads as one end
MAX_SPAN = 6 * 60        # a longer span is a plan or a left-open row, not six hours of effort
LIVED = {'● log', '◉ done', '✅ done', '▶️ in motion'}
OPEN = set(FACTS['status']['open'])
# the rhythms base: her settings' rhythms_fields map these names to field ids; a REST read names them
RF_NAMES = dict(name='name', code='code', type='type', status='status', goal='goal', target='target date',
                parent='parent name', open_ended='open-ended')
RF = dict(RF_NAMES)
DRIVE, RHYTHM = '♐ drive', '♒ rhythm'
# upkeep that comes around: a rhythm by her rule (10 Nov 2026), never flagged
TEND = re.compile(r'\b(e-?mail|inbox|gmail|dish(es)?|laundry|tidy|clean(ing|ed)?|vacuum|groceries|grocery|bills?|pay(ing|ment)?|'
                  r'feed(ing)?|walk(ing)? the dogs|oil change|trash|errands?|weekly (check|plan)|weather check)\b', re.I)
_STOP = set('''a an the and or of to for in on at by with from into my our your their his her its this that
these those is are be it as up out about after before over again just get make do take send ask find
check see look new next more some all any one two three week weekly today tomorrow monday tuesday wednesday
thursday friday saturday sunday morning evening night work session meeting time back first last'''.split())


def _f(c, k):
    return c.get(RF[k], c.get(RF_NAMES[k]))


def goal_text(goal):
    """Her goal: what sits above the divider and the [be•do] block."""
    return (goal or '').split('———')[0].split('[be•do]')[0].strip()


def buckets(recs):
    """name → dict(type, code, goal, target, open_ended, parent) for every ACTIVE row."""
    out = {}
    for r in recs:
        c = cells(r)
        if (sv(_f(c, 'status')) or '') != 'active':
            continue
        n = (sv(_f(c, 'name')) or '').strip()
        if n:
            out[n] = dict(id=r.get('id'), name=n, type=sv(_f(c, 'type')) or '', code=sv(_f(c, 'code')) or '',
                          goal=goal_text(_f(c, 'goal')), target=(_f(c, 'target') or '')[:10] or None,
                          open_ended=bool(_f(c, 'open_ended')), parent=sv(_f(c, 'parent')) or '')
    return out


def resolve(name, B):
    """The active bucket a row's text names — exactly, or by its code ('D6 be•do')."""
    n = (name or '').strip()
    if not n:
        return None
    if n in B:
        return n
    m = re.match(r'^([A-Z]\d+)\b\s*(.*)$', n)
    if m:
        for k, b in B.items():
            if b['code'] == m[1] or (m[2] and k == m[2].strip()):
                return k
    return None


def words(t):
    t = re.sub(r'^[^\w]+', '', t or '').lower()
    return {w for w in re.findall(r"[a-z][a-z'’-]{3,}", t) if w not in _STOP}


def minutes(row, off):
    """A row's span: end − start, else its time spent (seconds in an MCP read)."""
    a, b = row.get('datetime'), row.get('end')
    if a and b:
        p = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
        m = (p(b) - p(a)).total_seconds() / 60
        return m if 0 < m <= MAX_SPAN else 0
    s = row.get('time_spent')
    if not isinstance(s, (int, float)) or isinstance(s, bool):
        return 0
    m = s / 60                              # Airtable keeps a duration in seconds
    return m if 0 < m <= MAX_SPAN else 0


def undriven(rows, B, work=(), skip=frozenset()):
    """Effort carrying only a rhythm: long work and build rows, and rows coming back toward one end.
    `work` names the work rhythm(s) (her settings' work_parents).
    `skip` holds words that recur for no end of their own (the household's names, the pets').
    A recurring word that is in an active drive's name names that drive as the likely home."""
    long_rows, by_rh = [], {}
    for r in rows:
        rh = resolve(r.get('rhythm'), B)
        if not rh or B[rh]['type'] != RHYTHM:
            continue
        how = (r.get('how') or '').lower()
        title = r.get('title') or ''
        if 'tend' in how or (not how and TEND.search(title)):
            continue
        st = (r.get('status') or '').strip()
        action = (r.get('practice') or '').strip().endswith('action') or title.lstrip().startswith('⚡')
        grow = 'grow' in how or 'build' in how
        if st in LIVED and (grow or action or rh in work) and r['min'] >= WORK_MIN:
            long_rows.append(dict(r, bucket=rh))
        if st in LIVED or st in OPEN:
            by_rh.setdefault(rh, []).append(r)
    recurring = []
    for rh, rs in by_rh.items():
        seen = {}
        for r in rs:
            if not ((r.get('practice') or '').strip().endswith('action') or (r.get('title') or '').lstrip().startswith('⚡')):
                continue
            for w in words(r.get('title')) - skip:
                seen.setdefault(w, []).append(r)
        taken = set()
        for w, hit in sorted(seen.items(), key=lambda kv: (-len(kv[1]), kv[0])):
            ids = {x['id'] for x in hit}
            if len(ids) >= RECUR_N and not ids <= taken:
                home = next((k for k, b in B.items() if b['type'] == DRIVE and w in words(k)), None)
                recurring.append(dict(bucket=rh, word=w, rows=hit, drive=home))
                taken |= ids
    return long_rows, recurring


def unfinished(B, rows, today):
    """Active drives missing a goal or a target date, with what their rows say."""
    mine = {}
    for r in rows:
        k = resolve(r.get('rhythm'), B)
        if k:
            mine.setdefault(k, []).append(r)
    out = []
    for k, b in sorted(B.items(), key=lambda kv: kv[1]['code'] or kv[0]):
        if b['type'] != DRIVE:
            continue
        no_goal, no_date = not b['goal'], not b['target'] and not b['open_ended']
        late = bool(b['target']) and b['target'] < today.isoformat()
        if not (no_goal or no_date or late):
            continue
        rs = mine.get(k, [])
        opn = [r for r in rs if (r.get('status') or '').strip() in OPEN]
        done = sorted((r for r in rs if (r.get('status') or '').strip() in ('✅ done', '◉ done')),
                      key=lambda r: r.get('datetime') or '')
        tg = sorted((r.get('target') or '')[:10] for r in opn if r.get('target'))
        tg = [t for t in tg if t >= today.isoformat()]
        out.append(dict(drive=k, code=b['code'], parent=b['parent'], goal=b['goal'], target=b['target'],
                        no_goal=no_goal, no_date=no_date, past_date=late, open=len(opn), rows=len(rs),
                        last_done=(done[-1].get('title') if done else None),
                        last_done_on=((done[-1].get('datetime') or '')[:10] if done else None),
                        latest_open_target=(tg[-1] if tg else None),
                        open_titles=[r.get('title') for r in opn][:4]))
    return out


def unknown(rows, B):
    """Rhythm/drive text on a row that names nothing active."""
    c = {}
    for r in rows:
        n = (r.get('rhythm') or '').strip()
        if n and not resolve(n, B):
            c[n] = c.get(n, 0) + 1
    return sorted(c.items(), key=lambda kv: -kv[1])


def run(rhythm_recs, rows, today, skip=frozenset(), work=()):
    B = buckets(rhythm_recs)
    long_rows, recurring = undriven(rows, B, work=work, skip=skip)
    un = unfinished(B, rows, today)
    drives = [b for b in B.values() if b['type'] == DRIVE]
    return dict(today=today.isoformat(), drives=len(drives),
                no_goal=sum(1 for x in un if x['no_goal']), no_date=sum(1 for x in un if x['no_date']),
                past_date=sum(1 for x in un if x['past_date']),
                long=[dict(id=r['id'], title=r.get('title'), bucket=r['bucket'], min=round(r['min'])) for r in long_rows],
                recurring=[dict(bucket=g['bucket'], word=g['word'], n=len(g['rows']), drive=g['drive'],
                                titles=[r.get('title') for r in g['rows']][:5]) for g in recurring],
                unfinished=un, unknown=unknown(rows, B))


def render(rep):
    L = [f"drive check {rep['today']}: {rep['drives']} active drives · {rep['no_goal']} with no goal · "
         f"{rep['no_date']} with no target date · {rep['past_date']} past their date · "
         f"{len(rep['long']) + len(rep['recurring'])} efforts with no drive"]
    if rep['long'] or rep['recurring']:
        L.append('\nno drive — effort on a rhythm alone:')
        for r in rep['long']:
            L.append(f"  · {r['min']} min · {r['bucket']} · {r['title']}")
        for g in rep['recurring']:
            home = f" → belongs on {g['drive']}?" if g['drive'] else ''
            L.append(f"  · {g['n']} rows on “{g['word']}” · {g['bucket']}{home} · " + ' | '.join(g['titles'][:3]))
    if rep['unfinished']:
        L.append('\ndrives to finish (goal · timeline):')
        for x in rep['unfinished']:
            miss = ' + '.join(m for m, on in (('goal', x['no_goal']), ('date', x['no_date']), ('date passed', x['past_date'])) if on)
            ev = f"{x['open']} open of {x['rows']}"
            if x['latest_open_target']:
                ev += f", latest open target {x['latest_open_target']}"
            if x['last_done']:
                ev += f", last done {x['last_done_on']}: {x['last_done'][:60]}"
            L.append(f"  · {x['code']} {x['drive']} — needs {miss} · {ev}")
    if rep['unknown']:
        L.append('\nnames nothing active: ' + ' · '.join(f'{n} ({k})' for n, k in rep['unknown']))
    L.append('\nNext: one short list to her — a goal and a timeline for each, from its rows, to accept or adjust. '
             'Write only what she says; open-ended only at her word.')
    return '\n'.join(L)


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the drive check: effort with no drive, drives with no goal or date')
    ap.add_argument('--rhythms', required=True, help='a complete read of the rhythms base')
    ap.add_argument('--stream', action='append', default=[], help='a complete read of a weekly base, live first')
    ap.add_argument('--today', help='YYYY-MM-DD, her local date (default: now)')
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local(required=False) or {}
    sf = L.get('stream_fields') or {}
    names = ('datetime', 'end', 'time_spent', 'target', 'status', 'title', 'practice', 'rhythm', 'key')
    fields = {k: sf.get(k, k) for k in names}
    fields['how'] = sf.get('how', 'how')
    now = dt.datetime.now(dt.timezone.utc)
    today = dt.date.fromisoformat(a.today) if a.today else (now + dt.timedelta(hours=offset_hours(L, now))).date()
    recs, _ = merge_live_first(a.stream) if a.stream else ([], [])
    rows = []
    for r in recs:
        c = cells(r)
        row = {k: sv(c.get(v, c.get(k))) for k, v in fields.items()}
        row['id'] = r['id']
        row['min'] = minutes(row, None)
        rows.append(row)
    skip = set()
    for n in list((L.get('people') or {}).values()) + list(((L.get('care') or {}).get('pet') or {}).get('names') or []):
        skip |= words(n)
    RF.update({k: v for k, v in (L.get('rhythms_fields') or {}).items() if k in RF})
    recs_rh = complete(a.rhythms, 'rhythms')
    if any(k.startswith('fld') for r in recs_rh[:1] for k in cells(r)) and not all(RF[k].startswith('fld') for k in RF):
        sys.exit('the rhythms read is keyed by field id: add goal, target, type, status, code and open_ended '
                 'to rhythms_fields in her settings (be•do system › settings › facts_local)')
    rep = run(recs_rh, rows, today, frozenset(skip), tuple(L.get('work_parents') or (L.get('calendar') or {}).get('work_parents') or ()))
    print(json.dumps(rep, ensure_ascii=False, indent=1) if a.json else render(rep))


if __name__ == '__main__':
    main()
