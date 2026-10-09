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


def word(practice):
    """'🤸🏻‍♀️ morning movement' → 'morning movement'. A glyph drifts; the word doesn't."""
    return re.sub(r'\s+', ' ', re.sub(r'^[^\w]+', '', (practice or '').strip())).lower()


def _utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


class Context:
    """What the rules read. Every part is optional: a rule whose input is
    missing simply doesn't fire, and the field is asked instead."""

    def __init__(self, catalog=None, drives=None, day_rows=(), history=(), local=None):
        local = local or {}
        extra = local.get('fill') or {}
        self.none = {word(p) for p in FILL['device_none'] + (extra.get('device_none') or [])}
        self.phone = {word(p) for p in FILL['device_phone'] + (extra.get('device_phone') or [])}
        self.generic = {word(p) for p in FILL['generic_practices']}
        self.catalog = {word(k): v for k, v in (catalog or {}).items() if v}   # practice → wellness
        self.drives = {k.strip(): v for k, v in (drives or {}).items() if k and v}  # drive name → element
        span_pr = {word(p) for p in FILL['span_practices']}
        self.spans = [(_utc(r['datetime']), _utc(r['end'])) for r in day_rows
                      if word(r.get('practice')) in span_pr and r.get('datetime') and r.get('end')]
        self.hist = {'wellness': collections.defaultdict(collections.Counter),
                     'device': collections.defaultdict(collections.Counter)}
        for r in history:
            p = word(r.get('practice'))
            for f in ('wellness', 'device'):
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
