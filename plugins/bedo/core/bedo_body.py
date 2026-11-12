# -*- coding: utf-8 -*-
"""bedo_body: what her body says about a stretch she didn't log (12 Nov 2026).

Her words, the morning after Wednesday's QA filled 6:57–9:00a as be•do work:
*I don't know if I was working on be•do till 9:00, because I was also getting
myself ready and my son ready and making breakfast and doing all the things …
this is where the Oura heart rate check could come in handy*, and then: *the
Oura heart rate really should be built in, especially when I'm looking back
during the QA.*

Read by hand that morning, Oura split the stretch cleanly: 6:57–8:30 light
movement and sitting by turns (heart rate 73–86), then 8:30–8:56 steady
movement at 90–103 bpm, which Oura itself logged as housework. This module
does that read for the QA's gap step.

Two Oura records, both for the local day:
  activity   daily_activity's `class_5_min`: one digit per five minutes from
             its `timestamp` (0 not worn, 1 rest, 2 inactive, 3 low,
             4 medium, 5 high)
  heart      the heartrate samples, [{timestamp, bpm}] (day_heart.py's file)

`segments(a, b)` cuts a stretch where she goes from sitting to moving:
  moving   15+ minutes of medium or high activity (one low slot inside a run
           is allowed), or of heart rate over her calm line when there is no
           activity record
  still    the rest, when three in four of its slots are rest or inactive:
           sitting, at a desk, reading, resting
  mixed    the rest otherwise: on her feet and down again by turns, the way a
           morning of getting ready and breakfast reads
A piece under 15 minutes joins its neighbour. Each segment carries its median
heart rate and the slots it was read from, so the QA can say why.

    python3 bedo_body.py --day 2026-11-11 --local facts_local.json --out body-2026-11-11.json

reads Oura (the proxy attaches the key, as day_heart.py does) and writes
{"activity": {timestamp, class_5_min}, "heart": [...]}. Exit 3 when Oura
can't be read here: the QA runs without it.
"""
import datetime as dt, json, os, statistics, sys, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bedo_clock  # noqa: E402

SLOT = dt.timedelta(minutes=5)
MIN_RUN = dt.timedelta(minutes=15)
STILL, MIXED, MOVING = 'still', 'mixed', 'moving'
CALM_BPM = 80                      # her hr_calm_max default (the 8 Nov heart-rate amendment)
API = 'https://api.ouraring.com/v2/usercollection/'


def _utc(s):
    t = dt.datetime.fromisoformat(str(s).replace('Z', '+00:00'))
    return t.astimezone(dt.timezone.utc) if t.tzinfo else t.replace(tzinfo=dt.timezone.utc)


class Body:
    """One day of Oura: the five-minute activity classes and the heart rate samples."""

    def __init__(self, activity=None, heart=None, calm=CALM_BPM):
        self.slots = []            # [(start_utc, class)], class 0 dropped
        a = activity or {}
        if a.get('class_5_min') and a.get('timestamp'):
            t0 = _utc(a['timestamp'])
            for i, c in enumerate(str(a['class_5_min'])):
                if c.isdigit() and c != '0':
                    self.slots.append((t0 + i * SLOT, int(c)))
        self.heart = sorted((_utc(h['timestamp']), h['bpm']) for h in heart or [] if h.get('bpm'))
        self.calm = calm or CALM_BPM

    @classmethod
    def load(cls, path, calm=None):
        d = json.load(open(path, encoding='utf-8'))
        return cls(d.get('activity'), d.get('heart'), calm)

    def __bool__(self):
        return bool(self.slots or self.heart)

    def bpm(self, a, b):
        v = [x for t, x in self.heart if a <= t < b]
        return int(statistics.median(v)) if v else None

    def _classes(self, a, b):
        """[(start, end, class)] for the five-minute slots that fall in [a, b), clipped to it.
        Without an activity record, heart rate stands in: over her calm line reads as medium."""
        if self.slots:
            return [(max(t, a), min(t + SLOT, b), c) for t, c in self.slots if t < b and t + SLOT > a]
        out, t = [], a
        while t < b:
            x = self.bpm(t, min(t + SLOT, b))
            if x is not None:
                out.append((t, min(t + SLOT, b), 4 if x > self.calm else 2))
            t += SLOT
        return out

    def segments(self, a, b):
        """The stretch [a, b) cut at sitting and moving, or [] when Oura saw nothing of it."""
        cl = self._classes(a, b)
        if not cl:
            return []
        active = [c >= 4 for _, _, c in cl]
        for i in range(1, len(cl) - 1):          # one low slot inside a run of movement stays in it
            if not active[i] and cl[i][2] == 3 and active[i - 1] and active[i + 1]:
                active[i] = True
        parts, i = [], 0
        while i < len(cl):
            j = i
            while j < len(cl) and active[j] == active[i]:
                j += 1
            s, e = cl[i][0], cl[j - 1][1]
            if active[i] and e - s >= MIN_RUN:
                parts.append([s, e, MOVING, cl[i:j]])
            else:
                parts.append([s, e, None, cl[i:j]])
            i = j
        # join the pieces that aren't a run of movement, then name them still or mixed
        merged = []
        for p in parts:
            if merged and merged[-1][2] != MOVING and p[2] != MOVING:
                merged[-1][1], merged[-1][3] = p[1], merged[-1][3] + p[3]
            else:
                merged.append(p)
        for p in merged:
            if p[2] is None:
                calm = sum(c <= 2 for _, _, c in p[3])
                p[2] = STILL if calm >= 0.75 * len(p[3]) else MIXED
        # a piece under 15 minutes joins the neighbour it is longest beside
        changed = True
        while changed and len(merged) > 1:
            changed = False
            for k, p in enumerate(merged):
                if p[1] - p[0] < MIN_RUN:
                    n = k - 1 if k > 0 else k + 1
                    if k + 1 < len(merged) and k > 0 and merged[k + 1][1] - merged[k + 1][0] > merged[k - 1][1] - merged[k - 1][0]:
                        n = k + 1
                    q = merged[n]
                    q[0], q[1], q[3] = min(q[0], p[0]), max(q[1], p[1]), sorted(q[3] + p[3])
                    del merged[k]
                    changed = True
                    break
            # two neighbours of one kind become one
            k = 1
            while k < len(merged):
                if merged[k][2] == merged[k - 1][2]:
                    merged[k - 1][1], merged[k - 1][3] = merged[k][1], merged[k - 1][3] + merged[k][3]
                    del merged[k]
                else:
                    k += 1
        if merged:
            merged[0][0], merged[-1][1] = a, b    # the stretch's own edges, not the slots'
        return [{'start': s, 'end': e, 'kind': kind, 'bpm': self.bpm(s, e),
                 'classes': ''.join(str(c) for _, _, c in cl_)} for s, e, kind, cl_ in merged]


# ── reading Oura ───────────────────────────────────────────────────────────
def _get(path, q):
    out, tok = [], None
    while True:
        url = API + path + '?' + urllib.parse.urlencode(dict(q, **({'next_token': tok} if tok else {})))
        with urllib.request.urlopen(urllib.request.Request(url), timeout=30) as r:
            d = json.load(r)
        out += d.get('data') or []
        tok = d.get('next_token')
        if not tok:
            return out


def fetch(local, day):
    """{activity, heart} for her local day, read from the Oura API. Raises when Oura can't be read."""
    start, end = bedo_clock.day_bounds_utc(local, day)
    heart = [dict(timestamp=x['timestamp'], bpm=x['bpm']) for x in _get('heartrate', {
        'start_datetime': start.strftime('%Y-%m-%dT%H:%M:%SZ'), 'end_datetime': end.strftime('%Y-%m-%dT%H:%M:%SZ')})]
    acts = [x for x in _get('daily_activity', {'start_date': day.isoformat(),
                                               'end_date': (day + dt.timedelta(days=1)).isoformat()})
            if x.get('day') == day.isoformat()]
    act = {k: acts[0].get(k) for k in ('timestamp', 'class_5_min')} if acts else None
    return {'activity': act, 'heart': heart}


def main():
    import argparse
    ap = argparse.ArgumentParser(description="the day's Oura activity and heart rate, for the QA's gaps")
    ap.add_argument('--day', required=True)
    ap.add_argument('--local', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    L = json.load(open(a.local, encoding='utf-8'))
    try:
        d = fetch(L, dt.date.fromisoformat(a.day))
    except Exception as e:                       # noqa: BLE001 — no Oura here is not an error for the QA
        print(f'body: not read ({type(e).__name__}) — the QA runs without it')
        sys.exit(3)
    json.dump(d, open(a.out, 'w'))
    print(json.dumps({'day': a.day, 'heart': len(d['heart']), 'activity': bool(d['activity']), 'out': a.out}))


if __name__ == '__main__':
    main()
