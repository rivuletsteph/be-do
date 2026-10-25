# -*- coding: utf-8 -*-
"""How the day went: the waking day as a rainbow of bands.

Settled with her on 24 Oct 2026, drawn on Fri 23 Oct; every decision and her
words for it are in docs/day-behind-cards.md. In short:

- The rainbow is the 16 waking hours from getting up; the gap at the bottom is
  the 8 hours of a night, filled for the hours in bed the night before.
- From the inside out: a thin band for the dawn and dusk flows; being (eating
  and drinking, moving, recreation); doing (professional work, caretaking of
  others and of herself, cooking, be•do); a thin line for time on a screen.
  Bands overlap freely: one stretch can be two things.
- Doing makes or moves something; being is when the moment itself is the point.
- Work is what she was doing, not what the laptop was doing: a session row's
  minutes are hers only while she wasn't driving, eating, moving or asleep.
- A meal is not moving. Food is all nutrition, drinks too.
- The moments that mattered sit outside the rainbow at their own times.

Nothing personal lives here. What counts as caretaking beyond the practices
below (her rhythms and the people she cares for) is `care` in the settings:
{"rhythms": [...], "people": [...]}; the system's own drive is `system_rhythm`;
the daily goals the bars under the rainbow mark are `day_goals`, minutes by part
({"inbed": 480, "move": 120}).
"""
import datetime as dt
import re

import bedo_reader

TICK = 5                    # a moment with no length is drawn as five minutes
IDEAL_BED = 480             # 16 waking hours and 8 in bed make the day
SPAN = 960

SLEEP = {'sleep', 'nap'}
COOK = {'dinner prep', 'meal prep', 'cooking', 'lunch prep', 'breakfast prep'}
EAT = {'breakfast', 'lunch', 'dinner', 'snack', 'brunch', 'dessert', 'coffee', 'smoothie', 'evening tea',
       'tea', 'morning water', 'water', 'other consumable', 'drink'}
MOVE = {'morning movement', 'walking', 'hip exercises', 'strength training', 'barre', 'cycling', 'rowing',
        'yoga', 'squat', 'sun salutations', 'morning sun', 'evening sun', 'exercise', 'stretch'}
RECREATION = {'book', 'reading', 'audiobook', 'show', 'movie', 'video', 'game', 'glimmer', 'play', 'social',
              'song', 'music', 'puzzle', 'outing', 'fresh air', 'video call'}
CARE = {'clean', 'laundry', 'laundry move', 'care task', 'dishes', 'tidy', 'errand',
        'shower', 'bath', 'evening hygiene', 'getting ready', 'skincare'}      # caring for herself is caretaking too
TV = {'show', 'movie', 'video'}
SCREENISH = {'action', 'log', 'text', 'ai chat', 'video call', 'phone', 'usage check', 'calendar event',
             'look ahead', 'look behind', 'intention check', 'journal', 'insight'}
MOMENTS = {'highlight', 'glimmer', 'gratitude', 'insight', 'milestone', 'journal'}
FLOW_CLOSES = {'dawn flow close', 'dusk flow close'}

BANDS = [('flow', 'Flows', [('flow', 'dawn and dusk')]),
         ('being', 'Being', [('eat', 'eating and drinking'), ('move', 'moving'), ('recreation', 'recreation')]),
         ('doing', 'Doing', [('work', 'professional work'), ('care', 'caretaking'), ('cook', 'cooking'),
                             ('system', 'be•do')]),
         ('screen', 'On a screen', [('screen', 'on a screen')])]


def low(p):
    """A practice without its glyph: '😴 sleep' → 'sleep'."""
    return re.sub(r'^[^\w]+', '', p or '').strip().lower()


def names(v):
    if not v:
        return []
    if isinstance(v, list):
        return [x.get('name') if isinstance(x, dict) else str(x) for x in v]
    return [x.strip() for x in str(v).split(',')]


def title(t):
    return re.sub(r'^[^\w]+', '', t or '').split(' — ')[0].strip()


def day_rings(rows, day, L, flows=frozenset(), not_lived=frozenset()):
    """The rainbow's data for one day, from rows already deduped (live base first).
    Each row carries 'when', 'end' (ISO, UTC), 'spent' (seconds), 'practice', 'title',
    'status', 'rhythm', 'person', 'device'. `flows` holds the flow practices, normalised."""
    off = dt.timedelta(hours=L['utc_offset_hours'])
    s0 = dt.datetime.combine(day, dt.time())
    e0 = s0 + dt.timedelta(days=1)
    care = L.get('care') or {}
    care_rh, care_who = tuple(care.get('rhythms') or ()), tuple(care.get('people') or ())
    system = L.get('system_rhythm') or 'be•do'
    shared = (bedo_reader.FACTS.get('garden') or {}).get('shared_pattern')

    def local(ts):
        return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).replace(tzinfo=None) if ts else None

    def mins(t):
        return int((t - s0).total_seconds() // 60)

    A = {k: [None] * 1440 for k in ('flow', 'eat', 'move', 'recreation', 'work', 'cook', 'screen', 'drive')}
    seen_titles = {}                          # (array, minute) → [(kind, title)]: what a tap names
    WIN = {'dawn': [], 'dusk': []}
    nights, moments = [], []
    PRI = {'work': 0, 'care': 1, 'system': 2}   # a be•do session beside the school run is still the school run

    def paint(arr, kind, a, b, t=None):
        i, j = max(0, mins(a)), min(1440, mins(b))
        for m in range(i, j):
            cur = A[arr][m]
            if cur is None or (arr == 'work' and PRI.get(kind, 9) < PRI.get(cur, 9)):
                A[arr][m] = kind
            if t:
                seen_titles.setdefault((arr, m), []).append((kind, t))

    for r in rows:
        if r.get('status') in not_lived:
            continue
        a, b = local(r.get('when')), local(r.get('end'))
        if not a:
            continue
        if not b and r.get('spent'):
            b = a + dt.timedelta(seconds=float(r['spent']))
        span = b is not None and b > a and b - a <= dt.timedelta(hours=14)
        if (span and (b <= s0 or a >= e0)) or (not span and not s0 <= a < e0):
            continue
        pr, t = low(r.get('practice')), title(r.get('title'))
        bb = b if span else a + dt.timedelta(minutes=TICK)
        if s0 <= a < e0 and (pr in MOMENTS or (shared and re.search(shared, pr))):
            moments.append(dict(m=mins(a), g=(r.get('practice') or '·').split()[0], t=t, p=pr,
                                d=int((b - a).total_seconds() // 60) if span else 0))
        if pr in SLEEP and span:
            nights.append(dict(a=max(0, mins(a)), b=min(1440, mins(b)), inbed=int((b - a).total_seconds() // 60)))
        if pr in COOK:
            paint('cook', 'cook', a, bb, t)
        if pr in EAT:
            paint('eat', 'eat', a, bb, t)
        if pr in MOVE:
            paint('move', 'move', a, bb, t)
        if pr in RECREATION and span:
            paint('recreation', 'recreation', a, b, t)
        if pr in flows or pr in FLOW_CLOSES:
            paint('flow', 'flow', a, bb, t)
            WIN['dawn' if a.hour < 15 else 'dusk'].append(a)
        if pr == 'driving' and span:
            paint('drive', 'drive', a, b)
        rh, who = (r.get('rhythm') or ''), names(r.get('person'))
        is_care = pr in CARE or any(x in rh for x in care_rh) or (
            span and pr in ('log', 'driving') and any(w in t or any(w in n for n in who) for w in care_who))
        if is_care and span:
            paint('work', 'care', a, b, t)
        elif rh and span and pr == 'action' and b - a >= dt.timedelta(minutes=10):
            paint('work', 'system' if rh == system else 'work', a, b, t)
        d = (r.get('device') or '').lower()
        if 'laptop' in d or 'desktop' in d or 'tv' in d or pr in TV:
            paint('screen', 'screen', a, bb, t)
        if 'phone' in d:
            paint('screen', 'screen', a, bb if pr in SCREENISH else a + dt.timedelta(minutes=TICK), t)

    asleep = [False] * 1440
    for n in nights:
        for m in range(n['a'], n['b']):
            asleep[m] = True
    for m in range(1440):
        if A['eat'][m]:
            A['move'][m] = None                                   # sitting to eat is not moving
        if A['work'][m] in ('work', 'system') and (A['drive'][m] or A['eat'][m] or A['move'][m] or asleep[m]):
            A['work'][m] = None                                   # her doing, not the system's
        if asleep[m]:
            A['flow'][m] = None                                   # a flow step logged asleep is not a flow
    win = {}
    for k, v in WIN.items():
        ms = [mins(x) for x in v if 0 <= mins(x) < 1440 and not asleep[mins(x)]]
        if ms:
            a, b = min(ms), min(1440, max(ms) + TICK)
            while b > a and asleep[b - 1]:
                b -= 1
            win[k] = [a, b]

    being = [A['eat'][m] or A['move'][m] or A['recreation'][m] for m in range(1440)]
    doing = [A['work'][m] or A['cook'][m] for m in range(1440)]
    sources = {'flow': ('flow',), 'being': ('eat', 'move', 'recreation'), 'doing': ('work', 'cook'), 'screen': ('screen',)}
    arrays = {'flow': A['flow'], 'being': being, 'doing': doing, 'screen': A['screen']}

    def runs(band):
        out, cur = [], None
        for m, x in enumerate(arrays[band] + [None]):
            if x != cur:
                if cur is not None:
                    out[-1][2] = m
                if x is not None:
                    out.append([x, m, m + 1, []])
                cur = x
        for run in out:                       # what the chunk was: its own kind's rows, in order
            for m in range(run[1], run[2]):
                for k, t in (y for s in sources[band] for y in seen_titles.get((s, m), [])):
                    if k == run[0] and t not in run[3]:
                        run[3].append(t)
            run[3] = run[3][:4]
        return out

    morning = next((n for n in nights if n['a'] == 0 and n['b'] < 720), None)
    evening = next((n for n in nights if n['a'] >= 900), None)
    wake = morning['b'] if morning else (min(m for m, s in enumerate(asleep) if not s) if not all(asleep) else 420)
    bands = []
    for k, n, kinds in BANDS:
        arr = arrays[k]
        bands.append(dict(k=k, n=n, total=sum(1 for x in arr if x), runs=runs(k),
                          kinds=[dict(k=kk, n=nn, min=sum(1 for x in arr if x == kk)) for kk, nn in kinds]))
    goals = dict(L.get('day_goals') or {})        # minutes a day she aims for, by part: {"inbed": 480, "move": 120}
    return dict(wake=wake, bed=evening['a'] if evening else None, inbed=morning['inbed'] if morning else None,
                ideal_bed=goals.get('inbed') or IDEAL_BED, span=SPAN, bands=bands, win=win, goals=goals,
                moments=sorted(moments, key=lambda x: x['m']))
