# -*- coding: utf-8 -*-
"""How the day went: the waking day as a rainbow of bands.

Settled with her on 24 Oct 2026, drawn on Fri 23 Oct; every decision and her
words for it are in docs/day-behind-cards.md. In short:

- The dial is the calendar day, midnight to midnight, on a clock (26 Oct 2026):
  midnight at the bottom, noon at the top. In bed is the misty blue across every
  ring, asleep the deeper blue, placed by Oura's five-minute timeline
  (day_sleep.py) where there is one. `wake` and `span` stay in the data for the
  words and the bars; the drawing no longer starts at getting up.
- From the inside out: a thin band for the dawn and dusk flows; being (eating
  and drinking, moving, personal care, recreation); doing (professional work,
  family care, pet care, home care, making, be•do); a thin line for time on a
  screen (28 Oct: the care is named for what is cared for, and making is
  cooking she creates, building, gardening, music: what a care task can become).
  Bands overlap freely: one stretch can be two things.
- Doing makes or moves something; being is when the moment itself is the point.
- Work is what she was doing, not what the laptop was doing. A session row that
  names her stretches (`stretches: …` in its `[be•do]` block, from her own
  messages) is drawn over those stretches only; any session row's minutes are
  hers only while she wasn't driving, eating, moving or asleep.
- A meal is not moving. Food is all nutrition, drinks too.
- The moments that mattered sit outside the rainbow at their own times.

Nothing personal lives here. What counts as care beyond the practices below is
`care` in the settings: {"family": {"rhythms", "people", "together"},
"pet": {"rhythms", "names"}, "home": {"rhythms"}, "personal": {"rhythms"}}
("together" is her own words for them as a group, "calendars" their own calendars,
whose events are their day and drawn on their strip, not her rainbow; the older shape
{"rhythms", "people"} reads as family); the system's own drive is `system_rhythm`;
the daily goals the bars under the rainbow mark are `day_goals`, minutes by part
({"inbed": 480, "move": 120}). Recreation beyond the practices below is
`recreation` in the settings, {"rhythms": [...]}: a lived row with a span on
one of those rhythms is recreation too, whatever else it was (Urban Air with
her son, 24 Oct: "it was recreation and caretaking").
"""
import base64
import datetime as dt
import re

import bedo_reader
from bedo_entry import synergy_from
import bedo_stretches as stretches

TICK = 5                    # a moment with no length is drawn as five minutes
IDEAL_BED = 480             # 16 waking hours and 8 in bed make the day
SPAN = 960

SLEEP = {'sleep', 'nap'}
COOK = {'dinner prep', 'meal prep', 'cooking', 'lunch prep', 'breakfast prep', 'baking'}
MAKE = {'cooking', 'baking', 'woodworking', 'building', 'gardening', 'crafting', 'sewing', 'making',
        'making music', 'guitar', 'piano', 'jam'}                                    # making, always (28 Oct)
# making is cooking she creates, by her words, never by its length (31 Oct 2026, replacing the 28 Oct 30-minute rule:
# "there wasn't anything particularly creative about the dinner I made yesterday, so I would just call that family care")
MADE = ('i baked', 'we baked', 'baked bread', 'baked a ', 'baked some', 'recipe', 'from scratch', 'tried a new',
        'experiment')   # her words: she made something (not 'baked potato', a side dish, 31 Oct)
EAT = {'breakfast', 'lunch', 'dinner', 'snack', 'brunch', 'dessert', 'coffee', 'smoothie', 'evening tea',
       'tea', 'morning water', 'water', 'other consumable', 'drink'}
MOVE = {'morning movement', 'walking', 'hip exercises', 'strength training', 'barre', 'cycling', 'rowing',
        'yoga', 'squat', 'sun salutations', 'morning sun', 'evening sun', 'exercise', 'stretch'}
RECREATION = {'book', 'reading', 'audiobook', 'podcast', 'show', 'movie', 'video', 'game', 'glimmer', 'play', 'social',
              'song', 'music', 'puzzle', 'outing', 'fresh air', 'video call'}
CARE_KINDS = {'family', 'community', 'pet', 'home'}
# the required tasks of taking care of the family: the meal, setting the table, the kitchen after (31 Oct 2026)
FAMILY_CHORES = ('after dinner', 'after supper', 'kitchen', 'set the table', 'setting the table', 'family dinner')
# community care: caring for people beyond the family she's responsible for (31 Oct 2026, her words: hosting a
# party is more community care); her own words or the row's title say so, and the settings can add her own
# (`care.community.words`, such as the group of children she helps with)
# voting is community care too, even when it is also fun (31 Oct 2026, her words: it was fun but it was also community)
COMMUNITY = ('hosting', 'we hosted', 'hosted the', 'potluck at our house', 'party at our house', 'community care',
             'voted', 'ballot', 'to vote')   # the act itself: 'home from voting' is not
PERSONAL = {'shower', 'bath', 'evening hygiene', 'hygiene', 'getting ready', 'skincare'}  # personal care: her own body
# (🫧 hygiene too: "personal care and my evening routine" drew as professional work, 1 Nov 2026)
TRAVEL = {'riding', 'ride', 'flight', 'flying', 'travel', 'train', 'bus'}   # carried, not at the wheel (30 Oct)
HOME = {'clean', 'laundry', 'laundry move', 'care task', 'dishes', 'tidy', 'errand'}       # home care: care tasks
HOME_WORDS = ('tidy', 'tidied', 'clean the', 'cleaned the', 'vacuum', 'laundry', 'dishes', 'bathrooms')  # an action that was house care (31 Oct)
TV = {'show', 'movie', 'video'}
SCREENISH = {'action', 'log', 'text', 'ai chat', 'video call', 'phone', 'usage check', 'calendar event',
             'look ahead', 'look behind', 'intention check', 'journal', 'insight'}
TOGETHER = ('with {w}', '{w} and i ', '{w} and me', 'for {w}', 'me and {w}')   # her words: it was with or for them
NOW = re.compile(r"\b(?:i'm|i am|right now|it's|this is)\b")       # a moment speaking of now, not telling the day
SHARED_SHOW = ('for {w}', "{w}'s show", "{w}'s pick")                          # a show or game: caretaking only when it was theirs
MOMENTS = {'highlight', 'glimmer', 'gratitude', 'insight', 'milestone', 'journal'}
CONTACT = {'text', 'phone', 'video call'}
# balance, the original card (1 Nov 2026, her pick: the original design, in plain minutes): each row's wellness kind
# takes its minutes, being on one side and doing on the other, doing split into tending and growing
BEING4, DOING4 = ('heart', 'mind', 'body', 'spirit'), ('water', 'air', 'earth', 'fire')
WELL_ALIAS = {'wind': 'air'}   # reaching someone at a distance: named on the who card, not timed
FLOW_CLOSES = {'dawn flow close', 'dusk flow close'}
AT_THE_MOMENT = {'highlight'}  # a flow step whose row sits at the moment's own time, not when the step was done

BANDS = [('flow', 'Flows', [('flow', 'dawn and dusk')]),
         ('being', 'Being', [('eat', 'eating and drinking'), ('move', 'moving'), ('personal', 'personal care'),
                             ('recreation', 'recreation'), ('social', 'social recreation'), ('travel', 'travel')]),
         ('doing', 'Doing', [('work', 'professional work'), ('family', 'family care'), ('community', 'community care'),
                             ('pet', 'pet care'),
                             ('home', 'home care'), ('cook', 'making'), ('drive', 'driving'), ('system', 'be•do')]),
         ('screen', 'On a screen', [('screen', 'on a screen')])]


def event_calendar(link):
    """The calendar an event link belongs to, without its domain: Google's eid is base64 of
    '<event id> <calendar id>', the calendar's domain shortened ('…@g')."""
    m = re.search(r'eid=([A-Za-z0-9_-]+)', link or '')
    if not m:
        return None
    try:
        raw = base64.urlsafe_b64decode(m.group(1) + '=' * (-len(m.group(1)) % 4)).decode('utf-8', 'replace')
    except ValueError:
        return None
    parts = raw.split(' ')
    return parts[1].split('@')[0] if len(parts) > 1 else None


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


ASLEEP = re.compile(r'(?:(\d+)\s*h\s*)?(\d+)\s*min\s+asleep|(\d+)\s*h\s+asleep')


def asleep_min(details):
    """Minutes asleep, from the Oura line in a sleep row ('7 h 18 min asleep'); None when it isn't there.
    In bed is the row's span; asleep is the part of it drawn in the deeper blue (26 Oct 2026)."""
    m = ASLEEP.search(details or '')
    if not m:
        return None
    return int(m.group(3)) * 60 if m.group(3) else int(m.group(1) or 0) * 60 + int(m.group(2))


def night_runs(nights, sleep, s0, off):
    """The day's sleep, midnight to midnight (26 Oct 2026, her word: "it needs to split at midnight").
    In bed is the sleep rows' spans; asleep is where Oura's five-minute timeline says 1, 2 or 3 inside
    them, or, for a row no Oura period covers, its own Oura line's minutes with the awake time split
    between falling asleep and getting up. Minutes asleep outside every row are in bed too.
    Returns runs [state, a, b] over the day's minutes, with the day's totals."""
    bed, zz = [False] * 1440, [False] * 1440
    covered, source = set(), 'none'
    for p in sleep or []:
        a = dt.datetime.fromisoformat(p['start']).astimezone(dt.timezone.utc).replace(tzinfo=None) + off
        pa, pb = int((a - s0).total_seconds() // 60), None
        for i, ph in enumerate(p.get('phases') or ''):
            if ph in '123':
                for m in range(pa + 5 * i, pa + 5 * i + 5):
                    if 0 <= m < 1440:
                        zz[m] = True
        b = dt.datetime.fromisoformat(p['end']).astimezone(dt.timezone.utc).replace(tzinfo=None) + off
        pb = int((b - s0).total_seconds() // 60)
        for i, n in enumerate(nights):
            if p.get('phases') and pa < n['rb'] and pb > n['ra']:
                covered.add(i)
                source = 'oura'
    for i, n in enumerate(nights):
        for m in range(n['a'], n['b']):
            bed[m] = True
        if i not in covered and n.get('asleep'):               # no timeline: centre the minutes asleep in the span
            z = min(n['asleep'], n['rb'] - n['ra'])
            a = n['ra'] + (n['rb'] - n['ra'] - z) // 2
            for m in range(max(0, a), min(1440, a + z)):
                zz[m] = True
            source = source if source == 'oura' else 'row'
    runs, cur = [], None
    for m in range(1441):
        x = None if m == 1440 else ('asleep' if zz[m] else 'bed' if bed[m] else None)
        if x != cur:
            if cur is not None:
                runs[-1][2] = m
            if x is not None:
                runs.append([x, m, m + 1])
            cur = x
    return dict(runs=runs, inbed=sum(1 for m in range(1440) if bed[m] or zz[m]), asleep=sum(zz), source=source, zz=zz, covered=covered)


def day_rings(rows, day, L, flows=frozenset(), not_lived=frozenset(), sleep=None):
    """The rainbow's data for one day, from rows already deduped (live base first).
    Each row carries 'when', 'end' (ISO, UTC), 'spent' (seconds), 'practice', 'title',
    'status', 'rhythm', 'person', 'device', 'details'. `flows` holds the flow practices, normalised.
    `sleep` is Oura's periods around the day (day_sleep.py), each with its five-minute timeline."""
    off = dt.timedelta(hours=L['utc_offset_hours'])
    s0 = dt.datetime.combine(day, dt.time())
    e0 = s0 + dt.timedelta(days=1)
    care = L.get('care') or {}
    fam = care.get('family') or care                       # the older shape, {"rhythms", "people"}, is family care
    care_rh, care_who = tuple(fam.get('rhythms') or ()), tuple(fam.get('people') or ())
    care_together = tuple(x.lower() for x in fam.get('together') or ())   # her own words for them together ('the boys')
    pet_rh = tuple((care.get('pet') or {}).get('rhythms') or ())
    pet_rx = re.compile(r'\b(?:%s)\b' % '|'.join(map(re.escape, (care.get('pet') or {}).get('names') or ()))) \
        if (care.get('pet') or {}).get('names') else None   # a name as she writes it: Buddy the dog, not 'my buddy'
    home_rh = tuple((care.get('home') or {}).get('rhythms') or ())
    community_words = tuple(w.lower() for w in (care.get('community') or {}).get('words') or ())
    personal_rh = tuple((care.get('personal') or {}).get('rhythms') or ())
    # shared care: rows on these rhythms are two kinds of care at once, half and half (1 Nov 2026, her words:
    # the prep and the party were both family and community care, so they should be half and half)
    shared_rh = tuple((care.get('shared') or {}).get('rhythms') or ())
    shared_kinds = tuple((care.get('shared') or {}).get('kinds') or ('family', 'community'))
    their_cals = tuple(c.split('@')[0] for c in fam.get('calendars') or ())   # their own calendars: their day, not hers
    theirs = []
    rec_rh = tuple((L.get('recreation') or {}).get('rhythms') or ())
    # who was there is a mark on the stretch, not a kind of time (1 Nov 2026, her pick: how I spent my time is what I
    # did; who I was with goes on the stretch). `household` names the family; anyone else on a lived row is "with others"
    household = tuple(L.get('household') or ())
    system = L.get('system_rhythm') or 'be•do'
    shared = (bedo_reader.FACTS.get('garden') or {}).get('shared_pattern')

    def local(ts):
        return (dt.datetime.fromisoformat(ts.replace('Z', '+00:00')) + off).replace(tzinfo=None) if ts else None

    def mins(t):
        return int((t - s0).total_seconds() // 60)

    A = {k: [None] * 1440 for k in ('flow', 'eat', 'move', 'personal', 'recreation', 'work', 'cook', 'screen', 'drive', 'travel')}
    seen_titles = {}                          # (array, minute) → [(kind, title)]: what a tap names
    WIN = {'dawn': [], 'dusk': []}
    nights, moments = [], []
    PRI = {'work': 0, 'family': 1, 'community': 1.5, 'pet': 2, 'home': 3, 'system': 4}   # a be•do session beside the school run is still the school run

    OWN = [False] * 1440   # a care minute held by her own row (what she did), not a scheduled action
    HERS = [False] * 1440  # a work minute from her own row (a voice journal on a drive), not a session running beside her
    WK = [set() for _ in range(1440)]   # every kind of doing at each minute: two things at once both count (9 Oct)
    SHARED = [False] * 1440             # a minute of shared care: its kinds count half each, not whole each
    WITH = [set() for _ in range(1440)]  # who outside the family was there, minute by minute
    SEEN = {}                            # each name's place as she wrote it on the row, for the order she reads them in
    FAMW = [set() for _ in range(1440)]  # who in the family was there, minute by minute
    contacts = []                        # texts and calls: who she reached, at a distance
    ENERGY = {k: set() for k in BEING4 + DOING4}   # the minutes each kind held: a minute counts once per kind
    GROW = {k: set() for k in DOING4}               # the doing minutes on a drive: growing; the rest is tending
    growing_rh = set(L.get('_growing') or ())
    ENERGY_ROWS = {k: {} for k in BEING4 + DOING4}
    zero_pr = {low(x) for x in (L.get('zero_practices') or ())}
    mentioned = []                       # people named in the day's rows, whether or not they were there
    lived = []                          # (a, b, row) for the synergy read

    def paint(arr, kind, a, b, t=None, own=False):
        i, j = max(0, mins(a)), min(1440, mins(b))
        for m in range(i, j):
            cur = A[arr][m]
            if arr == 'work' and cur in CARE_KINDS and kind in CARE_KINDS and own != OWN[m]:
                win = own       # her walk with the dogs during his class was pet care, all of it (28 Oct)
            else:
                win = cur is None or (arr == 'work' and PRI.get(kind, 9) < PRI.get(cur, 9))
            if win:
                A[arr][m] = kind
                if arr == 'work':
                    OWN[m] = own
            if arr == 'work':
                WK[m].add(kind)
            if t:
                seen_titles.setdefault((arr, m), []).append((kind, t))

    for r in rows:
        if r.get('status') in not_lived:
            continue
        a, b = local(r.get('when')), local(r.get('end'))
        if not a:
            continue
        parts = stretches.from_details(r.get('details'), a)    # her stretches, when the row names them
        if parts:
            b = max(b or a, parts[-1][1])
        if not b and r.get('spent'):
            b = a + dt.timedelta(seconds=float(r['spent']))
        pieces = parts or [(a, b)]
        span = b is not None and b > a and b - a <= dt.timedelta(hours=14)
        if (span and (b <= s0 or a >= e0)) or (not span and not s0 <= a < e0):
            continue
        pr, t = low(r.get('practice')), title(r.get('title'))
        lived.append((a, b if span else None, r))
        # their day is theirs (28 Oct): an event from their own calendar, or their own play, is drawn on their
        # strip, never on her rainbow; what she did meanwhile is her own rows
        whose = next((w for w in care_who if (event_calendar(r.get('event')) in their_cals and their_cals)
                      or ((pr in RECREATION or pr in TV) and t.lower().startswith(w.lower() + ' '))
                      or (pr in EAT and t.lower().startswith((w.lower() + ' ', w.lower() + "'s ")))), None)   # his dinner
        if whose:
            if span:
                theirs.append(dict(who=whose, a=max(0, mins(a)), b=min(1440, mins(b)), t=t))
            continue
        bb = b if span else a + dt.timedelta(minutes=TICK)
        if s0 <= a < e0 and (pr in MOMENTS or (shared and re.search(shared, pr))):
            moments.append(dict(m=mins(a), g=(r.get('practice') or '·').split()[0], t=t, p=pr,
                                d=int((b - a).total_seconds() // 60) if span else 0))
        # the wheel: the row's wellness kind, its minutes (a moment counts five), never sleep or his own rows
        wl = (r.get('wellness') or {}).get('name') if isinstance(r.get('wellness'), dict) else r.get('wellness')
        wk = WELL_ALIAS.get(str(wl or '').split()[-1].lower(), str(wl or '').split()[-1].lower()) if wl else ''
        if wk in ENERGY and pr not in SLEEP and pr not in zero_pr and not pr.startswith(tuple(w.lower() + "'s" for w in care_who)) \
                and not any(t == w or t.startswith(w + ' ') for w in care_who):      # 'his name — his reading' is his own row
            if span:
                ms = range(max(mins(a), 0), min(mins(b), 1440))
            else:
                ms = range(mins(a), min(mins(a) + TICK, 1440)) if s0 <= a < e0 else range(0)
            if len(ms):
                ENERGY[wk].update(ms)
                if wk in GROW and (r.get('rhythm') or '') in growing_rh:
                    GROW[wk].update(ms)
                ENERGY_ROWS[wk][t] = ENERGY_ROWS[wk].get(t, 0) + len(ms)
        if pr in CONTACT and s0 <= a < e0:
            contacts.append(dict(m=mins(a), t=t, who=names(r.get('person'))))
        if s0 <= a < e0:
            for n in names(r.get('mentioned')):
                if n not in mentioned:
                    mentioned.append(n)
        if pr in SLEEP and span:
            nights.append(dict(a=max(0, mins(a)), b=min(1440, mins(b)), inbed=int((b - a).total_seconds() // 60),
                               asleep=asleep_min(r.get('details')), ra=mins(a), rb=mins(b)))
        said = ((r.get('title') or '') + ' ' + (r.get('details') or '').split('———')[0]).lower()
        # making is cooking she creates, and any making (28 Oct); quick food is care for whoever it fed
        quick = pr in COOK and pr not in MAKE and not any(w in said for w in MADE)
        if (pr in COOK or pr in MAKE) and not quick:
            paint('cook', 'cook', a, bb, t)
        if pr in EAT:
            paint('eat', 'eat', a, bb, t)
        if pr in MOVE:
            paint('move', 'move', a, bb, t)
        rh, who = (r.get('rhythm') or ''), names(r.get('person'))
        on_rec = any(x in rh for x in rec_rh)       # an action on a recreation rhythm too: it was lived, not worked (27 Oct)
        if span and (pr in RECREATION or on_rec):
            if household:                     # who was there is a mark (1 Nov 2026), so time with others is recreation
                paint('recreation', 'recreation', a, b, t)
            else:
                # social recreation: time with other people for its own sake, like a party someone else threw (31 Oct
                # 2026) beyond the family she cares for: time with her son is family time, a party with friends is
                # social (and a playmate's visit is his play, with her caring for him); a party is social either way
                others = [n for n in who if not any(w in n for w in care_who)]
                social = pr == 'social' or 'party' in said or (bool(others) and len(others) == len(who))
                paint('recreation', 'social' if social else 'recreation', a, b, t)
        if span and household and pr not in SLEEP:
            outside = [n for n in who if not any(w in n for w in household)]
            for n in outside:
                SEEN.setdefault(n, len(SEEN))
            inside = [n for n in who if n not in outside]
            for m in range(max(0, mins(a)), min(1440, mins(b))):
                FAMW[m].update(inside)
            for m in range(max(0, mins(a)), min(1440, mins(b))):
                WITH[m].update(outside)
        if (pr in flows and pr not in AT_THE_MOMENT) or pr in FLOW_CLOSES:
            paint('flow', 'flow', a, bb, t)
            WIN['dawn' if a.hour < 15 else 'dusk'].append(a)
        # travel (30 Oct, her words: driving is more active and traveling more passive): at the wheel is
        # doing, carried in a car or on a plane is being
        if pr == 'driving' and span:
            paint('drive', 'drive', a, b, t)
        if pr in TRAVEL and span:
            paint('travel', 'travel', a, b, t)
        # caretaking is when her focus is on them (28 Oct): an action she did with a care person, driving them,
        # or her words saying it was together or for them. Being nearby while she does her own thing is not.
        with_care = [w for w in care_who if any(w in n for n in who)]
        cues = SHARED_SHOW if pr in TV or pr == 'game' else TOGETHER   # a show together is the show, unless it was for them
        together = any(c.format(w=w.lower()) in said for w in with_care for c in cues) or (
            with_care and cues is TOGETHER and any(c in said for c in care_together))
        # cooking a meal for the family is care, never professional work (31 Oct 2026, her words: dinner
        # prep is not professional work, that is a care task)
        cook_care = quick and span and (bool(who) or 'dinner' in pr or 'dinner' in t.lower() or 'family' in said)
        chore_care = pr in HOME and span and any(w in said for w in FAMILY_CHORES)   # the kitchen after a family meal
        # a be•do session that talks about care is still be•do work: its notes never make it care (1 Nov 2026:
        # a session settling the care kinds drew as two hours of community care, from "voting is community care"
        # in its notes, then as pet care, from "Rosa and Buddy the whole time at Greenhouse")
        by_words = rh != system
        is_community = span and by_words and any(w in said for w in COMMUNITY + community_words)
        is_family = cook_care or chore_care or any(x in rh for x in care_rh) or (span and (
            (with_care and (pr in ('action', 'driving') or together)) or (pr == 'driving' and any(w in t for w in care_who))))
        is_pet = any(x in rh for x in pet_rh) or bool(span and by_words and pet_rx and pet_rx.search(
            (r.get('title') or '') + ' ' + (r.get('details') or '').split('———')[0] + ' ' + ' '.join(who)))
        care_kind = ('community' if is_community else       # her words for it win over the rhythm it was filed under
                     'family' if is_family or (quick and (with_care or together)) else 'pet' if is_pet else
                     'home' if pr in HOME or any(x in rh for x in home_rh) or (pr == 'action' and any(w in t.lower() for w in HOME_WORDS))
                     else None)
        if span and shared_rh and any(x in rh for x in shared_rh) and pr not in PERSONAL:
            for pa, pb in pieces:                                 # both kinds, two lanes, half each in the totals
                for k in shared_kinds:
                    paint('work', k, pa, pb, t, own=pr != 'action')
                for m in range(max(0, mins(pa)), min(1440, mins(pb))):
                    SHARED[m] = True
        elif span and (pr in PERSONAL or (quick and not care_kind) or (not care_kind and pr == 'action'
                                                                       and any(x in rh for x in personal_rh))):
            paint('personal', 'personal', a, b, t)                # personal care: her own body, her own quick food
        elif care_kind and span:
            for pa, pb in pieces:
                paint('work', care_kind, pa, pb, t, own=pr != 'action')
        elif rh and span and (pr == 'action' or pr not in flows) and not on_rec and pr not in COOK and \
                (parts or b - a >= dt.timedelta(minutes=10)):     # a work practice with its time counts too (28 Oct)
            for pa, pb in pieces:
                paint('work', 'system' if rh == system else 'work', pa, pb, t)
                if pr != 'action':
                    for m in range(max(0, mins(pa)), min(1440, mins(pb))):
                        HERS[m] = True
        d = (r.get('device') or '').lower()
        if 'laptop' in d or 'desktop' in d or 'tv' in d or pr in TV:
            for pa, pb in (parts or [(a, bb)]):
                paint('screen', 'screen', pa, pb, t)
        if 'phone' in d:
            for pa, pb in (parts or [(a, bb if pr in SCREENISH else a + dt.timedelta(minutes=TICK))]):
                paint('screen', 'screen', pa, pb, t)

    # asleep is where the night says so (Oura's timeline, or a row's own line); with neither, all the hours in bed.
    # A bedtime flow step done in bed before sleep stays a flow (26 Oct 2026).
    night = night_runs(nights, sleep, s0, off)
    asleep = [False] * 1440
    for i, n in enumerate(nights):
        for m in range(n['a'], n['b']):
            asleep[m] = asleep[m] or not (i in night['covered'] or n.get('asleep'))
    for m in range(1440):
        asleep[m] = asleep[m] or night['zz'][m]
    for m in range(1440):
        if A['eat'][m]:
            A['move'][m] = None                                   # sitting to eat is not moving
        if (A['drive'][m] and not HERS[m]) or A['eat'][m] or A['move'][m] or asleep[m]:
            # a session running while she drove is the system's; her own journal on the drive is hers (30 Oct)
            if A['work'][m] in ('work', 'system'):
                A['work'][m] = None                               # her doing, not the system's
            WK[m] -= {'work', 'system'}
        if A['work'][m] is None and WK[m] - {'work', 'system'} == set() and WK[m]:
            WK[m] = set()
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

    # care, grouped (1 Nov 2026, her words: splitting up all these different kinds of care is too many decisions;
    # group all of the care tasks and name them): with `care.grouped`, family, community, pet and home care draw
    # and count as one kind, 'care', each minute once, and the kinds that happened are named under it
    grouped = bool(care.get('grouped'))

    def group(kinds):
        out = []
        for kk, nn in kinds:
            if kk not in CARE_KINDS:
                out.append((kk, nn))
            elif ('care', 'care') not in out:
                out.append(('care', 'care'))
        return out
    bands_def = [(k, n, group(kinds) if grouped and k == 'doing' else
                  [x for x in kinds if not (household and x[0] == 'social')]) for k, n, kinds in BANDS]   # who: a mark

    # each band holds every kind at each minute, in the band's own order; two at once draw as two lanes (28 Oct)
    order = {k: [kk for kk, _ in kinds] for k, _, kinds in bands_def}
    sets = {'flow': [{A['flow'][m]} - {None} for m in range(1440)],
            'being': [{A['eat'][m], A['move'][m], A['personal'][m], A['recreation'][m], A['travel'][m]} - {None}
                      for m in range(1440)],
            'doing': [WK[m] | ({A['cook'][m], A['drive'][m]} - {None}) for m in range(1440)],
            'screen': [{A['screen'][m]} - {None} for m in range(1440)]}
    care_of = []                              # the kinds of care that happened, most minutes first, for the name line
    if grouped:
        care_of = sorted(([kk, sum(1 for s in sets['doing'] if kk in s)] for kk, _ in BANDS[2][2] if kk in CARE_KINDS),
                         key=lambda x: -x[1])
        care_of = [x for x in care_of if x[1]]
        sets['doing'] = [(s - CARE_KINDS) | ({'care'} if s & CARE_KINDS else set()) for s in sets['doing']]
    sources = {'flow': ('flow',), 'being': ('eat', 'move', 'personal', 'recreation', 'travel'), 'doing': ('work', 'cook', 'drive'), 'screen': ('screen',)}

    def runs(band):
        key = [tuple(k for k in order[band] if k in s) for s in sets[band]] + [()]
        out, start = [], 0
        for m in range(1, 1441):
            if key[m] != key[m - 1]:
                for i, k in enumerate(key[m - 1]):         # one run per kind, with its lane and the lanes beside it
                    out.append([k, start, m, [], i, len(key[m - 1])])
                start = m
        for run in out:                       # what the chunk was: its own kind's rows, in order
            for m in range(run[1], run[2]):
                for k, t in (y for s in sources[band] for y in seen_titles.get((s, m), [])):
                    if (k == run[0] or (run[0] == 'care' and k in CARE_KINDS)) and t not in run[3]:
                        run[3].append(t)
            run[3] = run[3][:4]
        return out

    morning = next((n for n in nights if n['a'] == 0 and n['b'] < 720), None)
    evening = next((n for n in nights if n['a'] >= 900), None)
    wake = morning['b'] if morning else (min(m for m, s in enumerate(asleep) if not s) if not all(asleep) else 420)
    bands = []
    for k, n, kinds in bands_def:
        ss = sets[k]
        def weight(m, kk, s):                 # a shared-care minute holding all its kinds: half to each (1 Nov)
            if k == 'doing' and SHARED[m] and kk in shared_kinds and set(shared_kinds) <= s:
                return 1 / len(shared_kinds)
            return 1
        bands.append(dict(k=k, n=n, total=sum(1 for s in ss if s), runs=runs(k),
                          kinds=[dict(k=kk, n=nn, min=round(sum(weight(m, kk, s) for m, s in enumerate(ss) if kk in s)),
                                      **({'of': care_of} if kk == 'care' else {}))
                                 for kk, nn in kinds]))
    # synergy, as her words say it: a stretch where two things at once helped each other, or got in each
    # other's way (28 Oct: "it would be neat to show that on the graphic")
    synergy, at_once = [], [sum(len(sets[k][m]) for k in ('being', 'doing')) for m in range(1440)]
    for a, b, r in lived:
        if (r.get('rhythm') or '') == system or (b is not None and b - a > dt.timedelta(hours=4)):
            continue                          # a be•do session talks about synergy; an envelope is not two things at once
        hers = (r.get('details') or '').split('———')[0].strip()
        ans, cue = synergy_from(title(r.get('title')) + ' ' + hers)
        if ans not in ('synergizing', 'competing', 'both'):
            continue
        SYW = bedo_reader.FACTS.get('synergy') or {}
        words = [w for kind in ('her_words', 'cues') for x, ws in (SYW.get(kind) or {}).items()
                 if ans in (x, 'both') for w in ws]
        lines = [s for s in re.split(r'(?<=[.!?])\s+|\n+', hers) if any(w in s.lower() for w in words)]
        own = [s for s in lines if not s.lower().startswith('overlap')]   # her sentence before the QA's note line
        line = (own or lines or [hers or title(r.get('title'))])[0]
        if b is None and not NOW.search(line.lower()):
            continue                          # a journal telling the day after it: not this moment's synergy
        need = 2                              # two things at once, at least
        if b is None:                         # a moment: the shortest stretch it sat inside, and the moment is one of the two
            need = 1
            cover = [(x, y) for x, y, o in lived if y and o is not r and x <= a < y and y - x <= dt.timedelta(hours=4)
                     and low(o.get('practice')) not in SLEEP]
            if not cover:
                continue
            a, b = min(cover, key=lambda c: c[1] - c[0])
        i, j = max(0, mins(a)), min(1440, mins(b))
        if j - i < 2 or max(at_once[i:j]) < need:
            continue                          # one thing alone: nothing to synergize
        same = next((s for s in synergy if s['ans'] == ans and s['a'] < j and i < s['b']), None)
        if same:                              # two rows saying it of the same stretch: one stretch, in her own words
            same['a'], same['b'] = min(same['a'], i), max(same['b'], j)
            if own and same['said'].lower().startswith('overlap'):
                same.update(t=title(r.get('title')), said=line.strip()[:220])
            continue
        synergy.append(dict(a=i, b=j, ans=ans, t=title(r.get('title')), cue=cue, said=line.strip()[:220]))
    goals = dict(L.get('day_goals') or {})        # minutes a day she aims for, by part: {"inbed": 480, "move": 120}
    # with others: each stretch of a quarter hour or more with someone outside the family, and who (1 Nov 2026)
    with_others, m = [], 0
    while m < 1440:
        if WITH[m] and not asleep[m]:
            i, who_all = m, set()
            while m < 1440 and WITH[m] and not asleep[m]:
                who_all |= WITH[m]
                m += 1
            if m - i >= 15:
                firsts = []
                for n in sorted(who_all, key=lambda n: (min(k for k in range(i, m) if n in WITH[k]), SEEN.get(n, 0))):
                    f = re.sub(r'^[^\w]+', '', n).split()[0] if re.sub(r'^[^\w]+', '', n) else n
                    if f not in firsts:
                        firsts.append(f)
                with_others.append(dict(a=i, b=m, who=firsts))
        else:
            m += 1
    # who I was with (1 Nov 2026, her pick): every waking minute is alone (the dogs count as alone), family, or social
    # (anyone outside the family there, family or not), and the people by name and circle, with their minutes
    who_card = None
    if household:
        bed_m = evening['a'] if evening else 1440
        awake = [m for m in range(wake, bed_m) if not asleep[m]]
        circles = L.get('_circles') or {}
        def clean_name(n):
            return re.sub(r'^[^\w]+', '', n).strip()
        # social splits by who: work when everyone outside the family there is from her Work circle (1 Nov 2026)
        def social_kind(ws):
            cs = [circles.get(clean_name(n)) or circles.get(n) for n in ws]
            return 'work' if cs and all(c == 'Work' for c in cs) else 'social'
        kind = {m: social_kind(WITH[m]) if WITH[m] else 'family' if FAMW[m] else 'alone' for m in awake}
        strip, prev = [], None
        for m in awake:
            if strip and prev == m - 1 and strip[-1][0] == kind[m]:
                strip[-1][2] = m + 1
            else:
                strip.append([kind[m], m, m + 1])
            prev = m
        mins_of = {}
        for m in awake:
            for n in WITH[m] | FAMW[m]:
                mins_of[n] = mins_of.get(n, 0) + 1
        people = [dict(n=clean_name(n), min=v,
                       circle=circles.get(clean_name(n)) or circles.get(n) or ('Family' if any(h in n for h in household) else ''))
                  for n, v in sorted(mins_of.items(), key=lambda x: (-x[1], SEEN.get(x[0], 0)))]
        # a text or a call names its person on the row, or in its title by a name from connections
        known = sorted((k for k in circles if ' ' in k), key=len, reverse=True)
        reach = []
        for c in sorted(contacts, key=lambda x: x['m']):
            ws = [clean_name(n) for n in c['who']] or [k for k in known if k.lower() in c['t'].lower()][:1]
            reach.append(dict(m=c['m'], t=c['t'], who=ws, circle=next((circles.get(w) for w in ws if circles.get(w)), '')))
        # mentioned but not there: one quiet line, never a chip on everyone (1 Nov 2026)
        there = {clean_name(n).split()[0].lower() for n in mins_of} | {w.lower() for c in reach for w in c['who']}
        named = [clean_name(n) for n in mentioned]
        named = [n for i, n in enumerate(named) if n and n not in named[:i] and n.split()[0].lower() not in there
                 and n.lower() not in there]
        who_card = dict(alone=sum(1 for m in awake if kind[m] == 'alone'),
                        family=sum(1 for m in awake if kind[m] == 'family'),
                        social=sum(1 for m in awake if kind[m] == 'social'),
                        work=sum(1 for m in awake if kind[m] == 'work'), strip=strip, people=people,
                        contacts=reach, mentioned=named, circle_order=list(L.get('circle_order') or []))
    be_min, do_min = sum(len(ENERGY[k]) for k in BEING4), sum(len(ENERGY[k]) for k in DOING4)
    grow_min = sum(len(GROW[k]) for k in DOING4)
    energy = dict(min={k: len(v) for k, v in ENERGY.items()}, be=be_min, tending=do_min - grow_min, growing=grow_min,
                  rows={k: [x for x, _ in sorted(v.items(), key=lambda kv: -kv[1])[:3]]
                                    for k, v in ENERGY_ROWS.items()})
    return dict(wake=wake, bed=evening['a'] if evening else None, inbed=morning['inbed'] if morning else None,
                asleep=morning['asleep'] if morning else None, night=night['runs'],
                inbed_day=night['inbed'], asleep_day=night['asleep'], asleep_from=night['source'],
                ideal_bed=goals.get('inbed') or IDEAL_BED, span=SPAN, bands=bands, win=win, goals=goals,
                moments=sorted(moments, key=lambda x: x['m']), theirs=sorted(theirs, key=lambda x: x['a']),
                synergy=synergy, with_others=with_others, who=who_card, energy=energy)
