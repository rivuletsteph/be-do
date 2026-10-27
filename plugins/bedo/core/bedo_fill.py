# -*- coding: utf-8 -*-
"""Device and wellness, deduced: rule 1 of the 9 Oct amendment, from the
fill_gaps rules tested on the 8 Oct build.

Her words, 9 Oct: *propose an amendment or some way of moving forward where I
don't have to do this … it seems like this should be codified.*

Every row is written with both filled. In order:

  wellness  an ⚡ action on a drive takes the drive's element; else the
            practice's catalog wellness; else its usual; else ASK
  device    a plan (▫️ ⬜) isn't done yet and carries none; a body or
            self-care practice is 🚫 none; a phone practice 📱 phone; a
            title that names the laptop 💻 laptop; a done row inside a
            walking, driving, cycling or 📍 location span 🚫 none; else its
            usual; else ASK

Last, a practice's history: what it carried most often in her other weeks.
Her words, 9 Oct: *use all of the clues at your disposal … but not dinging me
every time something isn't complete.* So her own past rows answer before she
is asked, labelled as her usual. A catch-all (⚡ action, 📝 log) has no usual.

    deduce(row, ctx) -> ({field: (value, source)}, [field asked])

`row` uses the logical names (practice, status, title, rhythm, wellness,
device, datetime, end). `ctx` is a Context built from the catalog, the drives,
the day's rows and, optionally, other weeks' rows.
"""
import collections, datetime as dt, re

from bedo_reader import FACTS

FILL = FACTS['fill']
PLANS = set(FACTS['status']['plans'])
ACTION = FACTS['practice']['action']
DOING = set(FACTS['wellness']['do'])
HEART = FACTS['wellness']['be'][0]
NOT_HAPPENED = PLANS | {FACTS['status']['actions'][4], FACTS['status']['logs'][2],
                        FACTS['weather_status']['status']}


def word(practice):
    """'🤸🏻‍♀️ morning movement' → 'morning movement'. A glyph drifts; the word doesn't."""
    return re.sub(r'\s+', ' ', re.sub(r'^[^\w]+', '', (practice or '').strip())).lower()


def _utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


class Context:
    """What the rules read. Every part is optional: a rule whose input is
    missing simply doesn't fire, and the field is asked instead."""

    def __init__(self, catalog=None, drives=None, day_rows=(), history=(), local=None, flows=None):
        local = local or {}
        self.local = local
        extra = local.get('fill') or {}
        self.none = {word(p) for p in FILL['device_none'] + (extra.get('device_none') or [])}
        self.phone = {word(p) for p in FILL['device_phone'] + (extra.get('device_phone') or [])}
        self.generic = {word(p) for p in FILL['generic_practices']}
        self.catalog = {word(k): v for k, v in (catalog or {}).items() if v}   # practice → wellness
        self.drives = {k.strip(): v for k, v in (drives or {}).items() if k and v}  # drive name → element
        span_pr = {word(p) for p in FILL['span_practices']}
        self.spans = [(_utc(r['datetime']), _utc(r['end'])) for r in day_rows
                      if word(r.get('practice')) in span_pr and r.get('datetime') and r.get('end')]
        F = FACTS['flows']
        either = [x for pr in F.get('either_or', []) for x in pr]          # one of a pair is a flow step
        self.flows = ({word(p) for p in list(flows) + either} if flows is not None else   # no catalog: facts' named steps
                      {word(p) for p in (F['core']['dawn'] + list(F['close'].values()) + [F['wake']]
                                         + F['after_sunrise'] + either)})
        self.day_rows = list(day_rows)
        self.hist = {'wellness': collections.defaultdict(collections.Counter),
                     'device': collections.defaultdict(collections.Counter),
                     'rhythm': collections.defaultdict(collections.Counter)}
        for r in history:
            p = word(r.get('practice'))
            for f in ('wellness', 'device', 'rhythm'):
                if r.get(f):
                    self.hist[f][p][r[f]] += 1

    def hint(self, field, practice):
        p = word(practice)
        if p in self.generic or not self.hist[field][p]:
            return None
        return self.hist[field][p].most_common(1)[0][0]


def _drive_element(row, ctx):
    for d in (row.get('rhythm') or '').split(','):
        if ctx.drives.get(d.strip()):
            return ctx.drives[d.strip()]
    return None


def deduce(row, ctx):
    """({field: (value, source)}, [fields to ask]) for the empty ones only."""
    got, ask = {}, []
    p = word(row.get('practice'))
    if not row.get('wellness'):
        w = None
        if p in PASSIVE:          # passive rest is being (24 Oct 2026): heart with people, else hers to say
            w, src = (HEART, 'passive rest with people') if row.get('person') else (None, None)
            if not w:
                c = ctx.catalog.get(p) or ctx.hint('wellness', p)
                w, src = (c, "the practice's catalog wellness") if c and c not in DOING else (None, None)
        else:
            if (row.get('practice') or '').strip() == ACTION and row.get('rhythm'):
                w = _drive_element(row, ctx)
                src = "the drive's element"
            if not w and ctx.catalog.get(p):
                w, src = ctx.catalog[p], "the practice's catalog wellness"
            if not w and ctx.hint('wellness', p):
                w, src = ctx.hint('wellness', p), 'what this practice usually carries'
        if w:
            got['wellness'] = (w, src)
        else:
            ask.append('wellness')
    if not row.get('device') and row.get('status') not in PLANS:
        t = row.get('title') or ''
        s = _utc(row.get('datetime'))
        d = None
        if p in ctx.none:
            d, src = '🚫 none', 'a body or self-care practice'
        elif p in ctx.phone:
            d, src = '📱 phone', 'a phone practice'
        elif any(w in t.lower() or w in t for w in FILL['laptop_words']):
            d, src = '💻 laptop', 'the title names the laptop'
        elif s and any(a <= s <= b for a, b in ctx.spans):
            d, src = '🚫 none', 'inside a walking, driving, cycling or location span'
        elif ctx.hint('device', p):
            d, src = ctx.hint('device', p), 'what this practice usually carries'
        if d:
            got['device'] = (d, src)
        else:
            ask.append('device')
    return got, ask


PASSIVE = {word(p) for p in FACTS['being_doing']['passive_rest']}
BK = FACTS['buckets']
STORIES = {word(p) for p in BK['stories_practices']}
SYSTEM = {word(p) for p in BK['system_practices']}
WINDOWS = [w.lower() for w in FACTS['window_chats']]
OPEN = FACTS['open_actions']


def is_window(title):
    t = (title or '').lower()
    return any(w in t for w in WINDOWS)


def bucket(row, ctx):
    """Every row that happened sits in a flow, or under a rhythm or a drive
    (20 Oct 2026). None when the row needs nothing; else (value, source), with
    value None when nothing deduces it and she is asked in passing."""
    p = word(row.get('practice'))
    if not p or row.get('rhythm') or row.get('status') in NOT_HAPPENED or p in ctx.flows:
        return None
    sys_r, stories = ctx.local.get('system_rhythm'), ctx.local.get('stories_rhythm')
    if sys_r and (p in SYSTEM or (p == word(ACTION) and is_window(row.get('title')))):
        return sys_r, 'a window chat sits under the system drive'
    if stories and p in STORIES:
        return stories, 'a story, read or watched'
    h = ctx.hint('rhythm', p)
    return (h, 'what this practice usually carries') if h else (None, None)


def open_device(row, ctx):
    """An open ⚡ action (▫️ ⬜) is written with the device it will be done on
    (8 Oct 2026): (value, source), value None when nothing deduces it. None
    when the row needs nothing — ▶️ in motion is deduced like any lived row."""
    if (row.get('practice') or '').strip() != ACTION or row.get('status') not in PLANS or row.get('device'):
        return None
    t = row.get('title') or ''
    if any(w in t.lower() or w in t for w in FILL['laptop_words']):
        return '💻 laptop', 'the title names the laptop'
    if row.get('quickie'):
        return '📱 phone', 'a quickie is phone-doable'
    if any(re.search(r'\b' + re.escape(w) + r'\b', t.lower()) for w in OPEN['phone_words']):
        return '📱 phone', 'the title is a phone task'
    return None, None


def catalog_flows(recs, local):
    """The practices that belong to a flow: active, in the dawn or dusk phase,
    in a group that is not the log-type one."""
    from bedo_reader import cells, sv
    pf = local.get('practices_fields') or {}
    phases = set(FACTS['flows']['phase'].values())
    out = set()
    for r in recs:
        c = cells(r)
        name = sv(c.get(pf.get('practice', 'practice'), c.get('practice')))
        ph = sv(c.get(pf.get('phase', 'phase'), c.get('phase')))
        grp = sv(c.get(pf.get('group', 'group'), c.get('group')))
        if name and ph in phases and grp and grp not in BK['flow_groups_not']:
            out.add(name)
    return out


def ask_line(row, field, ctx):
    h = ctx.hint(field, row.get('practice'))
    t = row.get('title') or row.get('practice') or '?'
    return f'{field} for “{t[:60]}”?' + (f' (usually {h})' if h else '')


def catalog_wellness(recs, local):
    """practice → wellness, from a practices dump (by field id when facts_local
    names them, else by name)."""
    from bedo_reader import cells, sv
    pf = local.get('practices_fields') or {}
    out = {}
    for r in recs:
        c = cells(r)
        name = sv(c.get(pf.get('practice', 'practice'), c.get('practice')))
        well = sv(c.get(pf.get('wellness', 'wellness'), c.get('wellness')))
        if name:
            out[name] = well
    return out


def drive_elements(recs, local):
    """drive name → element, from a rhythms dump."""
    from bedo_reader import cells, sv
    rf = local.get('rhythms_fields') or {}
    out = {}
    for r in recs:
        c = cells(r)
        name = sv(c.get(rf.get('name', 'name'), c.get('name')))
        el = sv(c.get(rf.get('element', 'element'), c.get('element')))
        if name:
            out[name] = el
    return out
