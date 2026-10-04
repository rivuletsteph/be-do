#!/usr/bin/env python3
"""Build the monthly ahead-review swipe deck.

Inputs (none of them ship; they are the user's data):
  --stream   JSON dump of the live weekly stream table: {"records":[...]} as the
             Airtable list call returns it (cellValuesByFieldId).
  --recs     JSON {key: [rec, reason]} written by the chat's judgment pass.
             rec is one of done | drop | someday | keep | date | ask.
  --today    YYYY-MM-DD (the review date)
  --out      where to write the page
  --local    the user's settings (default: assets/ahead_review_local.json) —
             the stream's field ids live there, never here.

Scope (the monthly ahead-review rule): open action chains whose latest row per
key is an intention or in motion and whose key is older than 14 days, excluding
any chain carrying the queue box, a head with `waiting on`, and media practices.
Potentials belong to the season review, not the monthly one — except a potential
whose details say to ask again in this month ("ask me again at the beginning of
November"), which is carded in that month.
"""
import argparse, calendar, collections, datetime as D, json, re, pathlib, sys

# The one reader (I11, I15, I5) lives in plugins/bedo/core. The runner copies it
# beside this file; in the repo it is three folders up. Beside wins.
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_os.path.join(_HERE, '..', '..', '..', 'core'), _HERE):
    sys.path.insert(0, _os.path.normpath(_p))
import bedo_reader  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent.parent
FIELDS = ('title', 'key', 'details', 'target', 'status', 'practice', 'rhythm', 'waiting_on', 'queue')
POTENTIAL = '▫️potential'
OPEN = {'⬜ intention', '▶️ in motion'}
MEDIA = {'🎥 movie', '📗 book', '📺 show', '🎧 podcast', '🎧 audiobook', '📰 news'}
MONTHS = list(calendar.month_name)[1:]
ASK_AGAIN = re.compile(r'ask (?:me )?again\b[^.\n]*?\b(' + '|'.join(MONTHS) + r')\b', re.I)


def load_fields(path):
    s = json.load(open(path, encoding='utf-8'))
    f = s.get('fields', {}).get('stream', {})
    missing = [k for k in FIELDS if not f.get(k)]
    if missing:
        raise SystemExit(f'{path}: fields.stream is missing {", ".join(missing)} — '
                         'a blank id reads every row as empty, so the build stops here')
    return f


def asks_again_this_month(details, today):
    m = ASK_AGAIN.search(details or '')
    return bool(m) and m.group(1).lower() == MONTHS[today.month - 1].lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stream', action='append', required=True,
                    help='each weekly base the chains passed through, live first'); ap.add_argument('--recs', required=True)
    ap.add_argument('--today', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--days', type=int, default=14)
    ap.add_argument('--local', default=str(HERE / 'assets' / 'ahead_review_local.json'))
    a = ap.parse_args()
    F = load_fields(a.local)

    def g(r, k):
        v = r['cellValuesByFieldId'].get(F[k])
        return v['name'] if isinstance(v, dict) else v

    R, _ = bedo_reader.merge_live_first(a.stream)  # I11 and I15: every base, live first
    recs = json.load(open(a.recs, encoding='utf-8'))
    today = D.date.fromisoformat(a.today); cut = today - D.timedelta(days=a.days)
    chains = collections.defaultdict(list)
    for r in R:  # I5: a log that shares an action's minute is not its chain
        k = g(r, 'key')
        if k and bedo_reader.chain_key(k, g(r, 'status'), r['id']) == k: chains[k].append(r)
    items = []
    for k, rs in chains.items():
        rs.sort(key=lambda r: r['createdTime']); h = rs[-1]
        st = g(h, 'status'); det = g(h, 'details') or ''
        carded = st in OPEN or (st == POTENTIAL and asks_again_this_month(det, today))
        if not carded or any(g(r, 'queue') for r in rs) or g(h, 'waiting_on') or (g(h, 'practice') or '') in MEDIA:
            continue
        try: kd = D.datetime.strptime(k[:6], '%y%m%d').date()
        except ValueError: continue
        if kd > cut: continue
        her = re.split(r'———|\n---\n', det)[0].strip().replace('\n', ' ')
        if her.startswith('[be•do]'): her = ''
        rec, why = recs.get(k, ['ask', ''])
        t = re.sub(r'^(🖼️ )?⚡ ?(action — )?', '', g(h, 'title') or '').strip()
        tg = (g(h, 'target') or '')[:10]
        b = '🟨' if not tg else ('🟥' if tg < a.today else '🟦')
        items.append(dict(k=k, t=t, d=g(h, 'rhythm') or 'no drive', b=b, s=st, tg=tg,
                          age=(today - kd).days, r=rec, w=why, h=her[:160]))
    size = collections.Counter(i['d'] for i in items)
    items.sort(key=lambda i: (-size[i['d']], i['d'], i['k']))
    eng = (HERE / 'assets' / 'ahead_review_engine.html').read_text(encoding='utf-8')
    pathlib.Path(a.out).write_text(eng.replace('__ITEMS__', json.dumps(items, ensure_ascii=False)), encoding='utf-8')
    print(f'{len(items)} items across {len(size)} drives -> {a.out}')

if __name__ == '__main__':
    main()
