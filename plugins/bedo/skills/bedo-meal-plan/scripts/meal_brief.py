# -*- coding: utf-8 -*-
"""The meal brief: everything a meal plan is drafted from, in one short read.

Her words, 5 Nov 2026: it would be good to have a meal planning skill that I can
access when I am wanting to do that effort. The first plan (26 Oct) cost a full
read of the shelf and two weekly streams, read by eye. This reads the same dumps
in code and prints what the plan needs and nothing else:

  ate      what was actually eaten, by day, over the last --days days: the meal
           rows (a plan is not a meal), and whether each was cooked, reheated,
           eaten out or someone else's cooking. A reheated dish is not a second
           cook.
  ahead    the next seven days: the week's typical shape (the settings'
           week_shape) and any open intention in the stream that day whose title
           reads as food (a potluck, a dinner out, a party)
  shelf    consumables by where they are kept: in date (with days left), past
           their shelf life (probably gone), running low, and the wants, by store
  recipes  the in-rotation and want-to-try recipes, each scored on its key
           ingredients against the in-date shelf: probably makeable, two or
           fewer missing, or further. House dishes with no ingredients on record
           are listed as such.

The shelf is a partial record, not an inventory: a row that says on hand was
put there by an order or her own words, and an absence proves nothing. The
brief says "the shelf shows", never "you have".

    python3 meal_brief.py --stream w45.json [--stream w44.json] \\
        --supplies supplies.json --recipes recipes.json --today YYYY-MM-DD \\
        [--days 10] [--local meal_plan_local.json] [--facts-local facts_local.json] [--json]

Nothing here writes. Every dump is a full read (I11): a truncated one stops it.
"""
import argparse, datetime as dt, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
for p in (HERE, os.path.join(HERE, '..', '..', '..', 'core')):
    if os.path.exists(os.path.join(p, 'bedo_reader.py')):
        sys.path.insert(0, os.path.abspath(p))
        break
from bedo_reader import FACTS, as_rows, complete, die, load_local, merge_live_first, offset_hours  # noqa: E402

M = FACTS['meals']
DIVIDER = FACTS['divider']
OPEN = set(FACTS['status']['open'])
PLANS_OR_DROPPED = set(FACTS['status']['plans']) | {'✖️ dropped'}   # a plan was not eaten
DAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

# words that say a dish was not cooked fresh that day
REHEAT_WORDS = ('leftover', 'leftovers', 'reheat', 'reheated', 'heated up', 'from the freezer', 'frozen')
# food words for an open intention in the days ahead, beyond the meal words
PLAN_WORDS = ('potluck', 'party', 'bash', 'cookout', 'bbq', 'picnic', 'restaurant',
              'cook', 'bake', 'grill', 'dinner', 'lunch', 'brunch', 'breakfast', 'eat')
# words dropped before a shelf item and a recipe's key ingredient are compared
STOP = {'fresh', 'frozen', 'organic', 'large', 'small', 'medium', 'whole', 'sliced', 'chopped',
        'grated', 'shredded', 'crumbles', 'crumbled', 'cooked', 'raw', 'baby', 'extra', 'virgin',
        'boneless', 'skinless', 'bone-in', 'skin-on', 'block', 'bag', 'of', 'and', 'or', 'the',
        'a', 'plain', 'unsalted', 'salted', 'low-fat', 'nonfat', 'pasture', 'raised', 'h-e-b'}


def word(practice):
    """The practice without its glyph: '🍽️ dinner' → 'dinner'."""
    return re.sub(r'^[^\w]+', '', (practice or '').strip()).lower()


def her_text(row):
    return ((row.get('title') or '') + ' ' + (row.get('details') or '').split(DIVIDER, 1)[0]).lower()


def stamp(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00'))


def local_day(s, local):
    t = stamp(s)
    return (t + dt.timedelta(hours=offset_hours(local, t))).date()


def clean_title(t):
    return re.sub(r'^[^\w]+', '', (t or '').strip())


# ── ate ──────────────────────────────────────────────────────────────────────

def how_made(row, kind, preps):
    """cooked · reheated · out · theirs · eaten. `preps` are the prep rows in the
    window before it (facts' prep_window_minutes). A family possessive (Mom's
    chili) is theirs; a restaurant word, or a meal "at" a named place, is out; a
    leftover word is reheated; a prep row before a meal is cooked. A snack is
    eaten, whatever came before it."""
    text = her_text(row)
    if any(re.search(r'\b' + re.escape(w) + r"'?s\b", text) for w in M['family_words']):
        return 'theirs'
    if any(w in text for w in M['out_words']) or re.search(r'\bat (?:the )?(?!home\b)[A-Z]', row.get('title') or ''):
        return 'out'
    if any(w in text for w in REHEAT_WORDS):
        return 'reheated'
    if preps and kind != 'snack':
        return 'cooked'
    return 'eaten'


def ate(rows, today, days, local):
    start = today - dt.timedelta(days=days)
    meals, preps = [], []
    for r in rows:
        if not r.get('datetime') or r.get('status') in PLANS_OR_DROPPED:
            continue
        d = local_day(r['datetime'], local)
        if not (start <= d <= today):
            continue
        w = word(r.get('practice'))
        if w in M['prep_words']:
            preps.append(r)
        elif w in M['meal_words']:
            meals.append((d, w, r))
    out = {}
    for d, kind, r in sorted(meals, key=lambda x: x[2]['datetime']):
        t = stamp(r['datetime'])
        before = [p for p in preps
                  if dt.timedelta(0) <= t - stamp(p['datetime']) <= dt.timedelta(minutes=M['prep_window_minutes'])]
        out.setdefault(d.isoformat(), []).append(
            {'kind': kind, 'what': clean_title(r.get('title')), 'made': how_made(r, kind, before)})
    return out


# ── ahead ────────────────────────────────────────────────────────────────────

def ahead(rows, today, shape, local):
    out = []
    for i in range(7):
        d = today + dt.timedelta(days=i)
        food = []
        for r in rows:
            if r.get('status') not in OPEN or not r.get('target'):
                continue
            if local_day(r['target'], local) != d:
                continue
            title = (r.get('title') or '').lower()          # the title only: details mention lunch in passing
            if any(re.search(r'\b' + w + r'\b', title) for w in PLAN_WORDS):
                food.append(clean_title(r.get('title')))
        out.append({'date': d.isoformat(), 'day': DAYS[d.weekday()],
                    'theme': (shape or {}).get(DAYS[d.weekday()], ''), 'on the stream': food})
    return out


# ── shelf ────────────────────────────────────────────────────────────────────

def days_left(row, today):
    try:
        added = dt.date.fromisoformat((row.get('added') or '')[:10])
        return (added + dt.timedelta(days=int(row['shelf_life'])) - today).days
    except (TypeError, ValueError, KeyError):
        return None


def shelf(rows, today):
    s = {'in date': {}, 'probably gone': [], 'running low': [], 'want': {}}
    for r in rows:
        if r.get('kind') != 'consumable':
            continue
        st, item, where = r.get('status'), r.get('item') or '', r.get('where') or 'unplaced'
        if st == 'want':
            stores = r.get('buy_where') or []
            stores = [x.get('name', x) if isinstance(x, dict) else x for x in stores] or ['store not named']
            for x in stores:
                s['want'].setdefault(x, []).append(item)
            continue
        if st == 'running low':
            s['running low'].append(item)
        if st not in ('on hand', 'running low'):
            continue
        left = days_left(r, today)
        if left is not None and left < 0:
            s['probably gone'].append(item)
        else:
            s['in date'].setdefault(where, []).append([item, left])
    for v in s['in date'].values():
        v.sort(key=lambda x: (x[1] is None, x[1] if x[1] is not None else 0, x[0]))
    for v in s['want'].values():
        v.sort()
    s['probably gone'].sort()
    return s


# ── recipes ──────────────────────────────────────────────────────────────────

def tokens(name):
    name = (name or '').lower().split(' — ')[0]
    out = []
    for t in re.findall(r"[a-z][a-z'&-]*", name):
        if t in STOP:
            continue
        if len(t) > 3 and t.endswith('es') and t[:-2].endswith(('ch', 'sh', 'o', 'x')):
            t = t[:-2]
        elif len(t) > 3 and t.endswith('s') and not t.endswith('ss'):
            t = t[:-1]
        out.append(t)
    return out


def matches(ingredient, item):
    """A key ingredient is on the shelf when one name's words sit inside the
    other's and the shelf item's last word (its noun) is among the ingredient's:
    'chicken thighs' ↔ 'bone-in skin-on chicken thighs', 'parmesan cheese' ↔
    'grated parmesan', but not 'pasta' ↔ 'marinara pasta sauce'."""
    a, b = tokens(ingredient), tokens(item)
    if not a or not b:
        return False
    A, B = set(a), set(b)
    return (A <= B or B <= A) and b[-1] in A


def score(recipes, in_date):
    items = [i for v in in_date.values() for i, _ in v]
    out = []
    for r in recipes:
        if r.get('standing') not in ('in rotation', 'want to try'):
            continue
        keys = [k.strip() for k in (r.get('key_ingredients') or '').splitlines() if k.strip()]
        entry = {'title': r.get('title'), 'standing': r.get('standing'), 'course': r.get('course'),
                 'theme': r.get('theme') or ''}
        if not keys:
            entry.update(fit='no ingredients on record', have=[], missing=[])
        else:
            have = [k for k in keys if any(matches(k, i) for i in items)]
            missing = [k for k in keys if k not in have]
            entry.update(have=have, missing=missing,
                         fit='probably makeable' if not missing else
                             f'{len(missing)} away' if len(missing) <= 2 else 'further')
        out.append(entry)
    order = {'probably makeable': 0, '1 away': 1, '2 away': 2, 'further': 3, 'no ingredients on record': 4}
    out.sort(key=lambda e: (order.get(e['fit'], 5), e['standing'] != 'in rotation', e['title'] or ''))
    return out


# ── the brief ────────────────────────────────────────────────────────────────

def brief(stream, supplies, recipes, today, local, shape, days=10):
    sh = shelf(supplies, today)
    return {'today': today.isoformat(), 'ate': ate(stream, today, days, local),
            'ahead': ahead(stream, today, shape, local), 'shelf': sh,
            'recipes': score(recipes, sh['in date'])}


def as_text(b):
    L = [f"meal brief · {b['today']} · the shelf is a partial record: \"the shelf shows\", never \"you have\"", '',
         'ate']
    for d, meals in sorted(b['ate'].items()):
        L.append(f'  {d}  ' + ' · '.join(f"{m['kind']}: {m['what']} ({m['made']})" for m in meals))
    L += ['', 'ahead']
    for a in b['ahead']:
        extra = ('  — ' + '; '.join(a['on the stream'])) if a['on the stream'] else ''
        L.append(f"  {a['day']} {a['date']}  {a['theme'] or '—'}{extra}")
    s = b['shelf']
    L += ['', 'shelf, in date']
    for where, items in sorted(s['in date'].items()):
        L.append(f'  {where}: ' + ', '.join(f'{i} ({n}d)' if n is not None else i for i, n in items))
    L.append('  probably gone (past shelf life): ' + (', '.join(s['probably gone']) or '—'))
    L.append('  running low: ' + (', '.join(s['running low']) or '—'))
    L += ['', 'wants']
    for store, items in sorted(s['want'].items()):
        L.append(f'  {store}: ' + ', '.join(items))
    L += ['', 'recipes']
    for r in b['recipes']:
        miss = f" · missing {', '.join(r['missing'])}" if r['missing'] else ''
        theme = f" [{r['theme']}]" if r['theme'] else ''
        L.append(f"  {r['fit']:<26} {r['title']}{theme} ({r['standing']}){miss}")
    return '\n'.join(L)


STREAM_FIELDS = ('datetime', 'target', 'status', 'title', 'details', 'practice')


def settings(path, row, how):
    """A settings file when there is one, else its row in the settings table
    (bedo_settings), else stop: a plan from blank ids would read an empty shelf."""
    if path and os.path.exists(path):
        with open(path, encoding='utf-8') as fh:
            return json.load(fh)
    try:
        import bedo_settings
        d, why = bedo_settings.fetch(row)
    except Exception as e:                       # noqa: BLE001
        d, why = None, f'{type(e).__name__}: {e}'
    if not d:
        die(f'no {row} settings ({why}) — {how}')
    return d


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--stream', action='append', required=True, help='a weekly stream dump; live base first')
    ap.add_argument('--supplies', required=True)
    ap.add_argument('--recipes', required=True)
    ap.add_argument('--today', required=True)
    ap.add_argument('--days', type=int, default=None)
    ap.add_argument('--local', default=os.path.join(HERE, '..', 'assets', 'meal_plan_local.json'))
    ap.add_argument('--facts-local', default=None)
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args()
    mine = settings(a.local, 'meal_plan_local', 'copy assets/meal_plan_local.example.json and fill it in')
    facts_local = load_local(a.facts_local, required=False) or settings(None, 'facts_local', 'see the core\'s facts_local.example.json')
    stream_fields = {k: (facts_local.get('stream_fields') or {}).get(k) for k in STREAM_FIELDS}
    for name, fields in (('supplies_fields', mine.get('supplies_fields')), ('recipes_fields', mine.get('recipes_fields')),
                         ('stream_fields', stream_fields)):
        if not fields or any(not v or '…' in v for v in fields.values()):
            die(f'{name} has a blank id — a blank id reads every row as empty')
    recs, _ = merge_live_first(a.stream)
    stream = as_rows(recs, stream_fields)
    supplies = as_rows(complete(a.supplies), mine['supplies_fields'])
    recipes = as_rows(complete(a.recipes), mine['recipes_fields'])
    b = brief(stream, supplies, recipes, dt.date.fromisoformat(a.today), facts_local,
              mine.get('week_shape'), a.days or mine.get('days_back', 10))
    print(json.dumps(b, ensure_ascii=False, indent=1) if a.json else as_text(b))


if __name__ == '__main__':
    main()
