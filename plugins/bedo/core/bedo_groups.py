# -*- coding: utf-8 -*-
"""The groups check: her open actions, read together, and what could go in one go.

Her words, 24 Nov 2026: I need you to keep track of these open intentions and
potential actions and proactively scan how these things can be grouped. On that
day the live base held some 440 open rows and nothing read them side by side,
and an ask that came by work email (a post someone wanted) never reached
the stream at all.

Every open row (▫️ potential, ⬜ intention, ▶️ in motion) is read once and put
under four lenses. A group needs two rows or more; one row is not a grouping.

  sitting   the same kind of doing, done in one sitting whatever the drive:
            calls and texts, email and posts, orders, bookings, forms and bills,
            look-ups. Read from the title's own words
  person    the same person on the person or mentioned field, other than the
            household (her, her son, her partner: `people` in her settings), who
            is with her by default and would make every row one group
  place     the same place: a town or a spot named in the title (`in Riverton`,
            `at the clinic`), and any of her `group_places` words
  drive     the drive's own ⬜ steps, when two or more wait on it

What it never does: write a row, close one, move a date, or choose for her. The
groups are offers; the day ahead draws them, and she picks.

The mail half reads the Gmail connector's threads (the same read the 📧 clear
gmail inbox step makes) and names each thread that reads as an ask of her and
that no row mentions: by its subject's words, or by the sender's name. Work mail
is seen only where it reaches Gmail (forwarded, or a chat or calendar notice).
A flagged ask goes on her short list to say yes to; it is never written unasked
(J3: an intention is hers).

    python3 bedo_groups.py --live [--json]
    python3 bedo_groups.py --rows rows.json [--mail threads.json] [--json]
"""
import argparse, json, re, sys

from bedo_reader import FACTS, as_rows, load_local, read_dump

OPEN = tuple(FACTS['status']['open'])
INTENT, MOVING, MAYBE = '⬜ intention', '▶️ in motion', '▫️potential'
FIELDS = ('title', 'status', 'details', 'datetime', 'rhythm', 'person', 'mentioned', 'key', 'practice', 'quickie',
          'device', 'target')
ASK = re.compile(r'(?im)^\W*(?:\[be•do\]\W*)?for code:')

# the kinds of doing that go in one sitting, first match wins; the words are hers in the titles of Nov 2026
KINDS = (
    ('calls', '📞', 'calls and texts', r'\b(?:call|text|reach out|talk to|talk with|check in with|ask|invite|'
                                      r'follow up with|message)\b'),
    ('email', '✉️', 'email and posts', r'\b(?:e-?mail|reply|respond|send|post on|post to|forward|share)\b'),
    ('book', '🗓️', 'bookings and sign-ups', r'\b(?:book|schedule|appointment|reserve|register|sign up|sign-up|'
                                           r'enroll|rsvp)\b'),
    ('forms', '🧾', 'forms and bills', r'\b(?:pay|renew|sign|form|file|claim|cancel|submit|request|apply)\b'),
    ('buy', '🛒', 'orders and errands', r'\b(?:order|buy|purchase|shop|shopping|return|pick up|drop off)\b'),
    ('look', '🔎', 'look-ups', r'\b(?:look into|look at|look up|research|find|explore|compare|read up)\b'),
)
_KIND = [(k, g, n, re.compile(p, re.I)) for k, g, n, p in KINDS]
# a place named in the title: "in Riverton", "at Oak Hall", "to Lake City"
_PLACE = re.compile(r"\b(?:in|at|to|near|from)\s+((?:the\s+)?[A-Z][\w'’&-]+(?:\s+[A-Z][\w'’&-]+){0,2})")
_NOT_PLACE = {'the', 'my', 'a', 'an', 'his', 'her', 'our', 'this', 'next', 'january', 'february', 'march', 'april',
              'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december', 'monday', 'tuesday',
              'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'be•do'}
_SPLIT = re.compile(r'\s*[,·;]\s*')
_LEAD = re.compile(r'^[^\w]+')
SHOW = 6           # rows shown under one group; the rest are counted
TOP = 4            # groups shown under one lens


def clean(t):
    return re.sub(r'^\W+', '', (t or '').strip()).strip()


def _people(v):
    if not v:
        return []
    if isinstance(v, (list, tuple)):
        v = ', '.join(str(x) for x in v)
    return [n for n in (_LEAD.sub('', x).strip() for x in _SPLIT.split(str(v))) if n]


def open_rows(rows, hidden=()):
    """The open action rows, one per key (the live base first), with Duet's asks
    for Code and hidden drives left out."""
    out, seen = [], set()
    for r in rows:
        if (r.get('status') or '') not in OPEN:
            continue
        p = r.get('practice') or ''
        if p and '⚡' not in p:
            continue
        if ASK.search(r.get('details') or '') or (r.get('rhythm') or '') in hidden:
            continue
        k = r.get('key') or r.get('id')
        if k in seen:
            continue
        seen.add(k)
        out.append(r)
    return out


def kind_of(title):
    for k, g, n, rx in _KIND:
        if rx.search(title or ''):
            return k
    return None


def places_of(title, extra=()):
    t = clean(title)
    got = []
    for m in _PLACE.finditer(t):
        p = re.sub(r'^the\s+', '', m.group(1)).strip(" '’")
        if p.split()[0].lower() not in _NOT_PLACE and not re.search(r"['’]s$", p.split()[0]) and p not in got:
            got.append(p)
    low = t.lower()
    for w in extra:
        if w and re.search(r'\b' + re.escape(w.lower()) + r'\b', low) and w not in got:
            got.append(w)
    return got


def _item(r):
    return dict(id=r.get('id'), title=clean(r.get('title')), status=r.get('status'), drive=r.get('rhythm') or None,
                target=r.get('target') or None)


def _order(rs):
    rank = {INTENT: 0, MOVING: 1, MAYBE: 2}       # what she meant first; a ▶️ title is often a progress note
    return sorted(rs, key=lambda r: (rank.get(r.get('status'), 3), r.get('target') or '9', r.get('datetime') or ''))


def _group(lens, name, glyph, rs, why):
    rs = _order(rs)
    return dict(lens=lens, name=name, glyph=glyph, n=len(rs), intent=sum(r.get('status') != MAYBE for r in rs),
                drives=len({r.get('rhythm') for r in rs if r.get('rhythm')}), why=why,
                rows=[_item(r) for r in rs[:SHOW]], more=max(0, len(rs) - SHOW))


def _top(gs, n=TOP):
    return sorted(gs, key=lambda g: (-g['intent'], -g['n'], g['name']))[:n]


def groups(rows, self_names=(), places=(), hidden=()):
    """The groupings among `rows`: {lens: [group, …]} and the count read.
    `self_names`: the household, left out of the person lens and the places."""
    rs = open_rows(rows, hidden)
    me = {_LEAD.sub('', s).strip().lower() for s in self_names if s}
    places_out = me | {n.split()[0] for n in me}
    by = dict(sitting={}, person={}, place={}, drive={})
    for r in rs:
        k = kind_of(r.get('title'))
        if k:
            by['sitting'].setdefault(k, []).append(r)
        who = []
        for n in _people(r.get('person')) + _people(r.get('mentioned')):
            if n.lower() not in me and n not in who:
                who.append(n)
        for n in who:
            by['person'].setdefault(n, []).append(r)
        for p in [p for p in places_of(r.get('title'), places) if p.lower() not in places_out]:
            by['place'].setdefault(p, []).append(r)
        if r.get('rhythm') and r.get('status') == INTENT:
            by['drive'].setdefault(r['rhythm'], []).append(r)
    kinds = {k: (g, n) for k, g, n, _ in KINDS}
    out = dict(
        sitting=_top([_group('sitting', kinds[k][1], kinds[k][0], v, 'one sitting, whatever the drive')
                      for k, v in by['sitting'].items() if len(v) > 1], len(KINDS)),
        # someone on a tenth of everything is company by default, like the household, and not a grouping
        person=_top([_group('person', n, '👤', v, f'everything open with {n}') for n, v in by['person'].items()
                     if 1 < len(v) <= max(12, len(rs) // 10)]),
        place=_top([_group('place', p, '📍', v, f'in one go at {p}') for p, v in by['place'].items() if len(v) > 1]),
        drive=_top([_group('drive', d, '🚣', v, 'its waiting steps, in one push') for d, v in by['drive'].items()
                    if len(v) > 1]))
    return dict(read=len(rs), lenses=out)


# --- the mail half: asks that came by email and never reached the stream -------------------------------------

_ASKING = re.compile(r'\?|\b(?:can you|could you|would you|will you|please|let me know|are you able|do you have time|'
                     r'when can|need you to|asked you|ask you)\b', re.I)
_BULK = re.compile(r'no-?reply|noreply|notifications?@|newsletter|mailer|news@|info@|updates?@|marketing|digest',
                   re.I)
_STOP = set('a an and are as at be by can could do for from have i in is it me my of on or our please re fw fwd '
            'that the this to we will with would you your about just need want get time'.split())


def _words(t):
    return {w for w in re.findall(r"[a-z][a-z'’]{2,}", (t or '').lower()) if w not in _STOP}


def _name_of(sender):
    s = (sender or '').strip()
    m = re.match(r'\s*"?([^"<]+?)"?\s*<', s)
    if m:
        return m.group(1).strip()
    local = s.split('@')[0]
    return re.sub(r'[._]+', ' ', local).strip()


def unlanded(threads, rows, me=(), work=()):
    """Threads that read as an ask of her, from a person, that no row mentions.
    `me`: her own addresses, never a sender to flag. `work`: addresses or
    domains whose mail is work mail; a thread to or from one is marked work."""
    text = ' \n'.join(f'{r.get("title") or ""} {r.get("details") or ""}' for r in rows).lower()
    have = _words(text)
    mine = {m.lower() for m in me if m}
    out = []
    for t in threads:
        msgs = t.get('messages') or [t]
        last = msgs[-1]
        sender = (last.get('sender') or last.get('from') or '')
        subj = next((m.get('subject') for m in msgs if m.get('subject')), '') or ''
        body = ' '.join(f'{m.get("subject") or ""} {m.get("snippet") or ""}' for m in msgs)
        if not sender or sender.lower() in mine or _BULK.search(sender) or not _ASKING.search(body):
            continue
        name = _name_of(sender)
        first = name.split()[0].lower() if name else ''
        sw = _words(re.sub(r'^\s*(?:re|fw|fwd)\s*:\s*', '', subj, flags=re.I))
        hit = len(sw & have) >= max(2, (len(sw) + 1) // 2) if sw else False
        if hit or (first and len(first) > 2 and re.search(r'\b' + re.escape(first) + r'\b', text)
                   and sw & have):
            continue
        addrs = ' '.join([sender] + [a for m in msgs for a in (m.get('toRecipients') or []) + (m.get('ccRecipients') or [])])
        out.append(dict(thread=t.get('id'), subject=subj.strip() or '(no subject)', sender=name or sender,
                        url=t.get('viewUrl') or last.get('viewUrl'),
                        work=any(w.lower() in addrs.lower() for w in work if w)))
    return out


# --- the report ---------------------------------------------------------------------------------------------

LENS = (('sitting', 'one sitting'), ('person', 'one person'), ('place', 'one place'), ('drive', 'one drive'))


def report(g, mail=None):
    out = [f'groups {g["read"]} open actions read · offers only, nothing written']
    for lens, label in LENS:
        gs = g['lenses'][lens]
        if not gs:
            continue
        out.append(f'  {label}:')
        for x in gs:
            out.append(f'    {x["glyph"]} {x["name"]} · {x["n"]} ({x["intent"]} meant, {x["n"] - x["intent"]} maybe)'
                       + (f' across {x["drives"]} drives' if x['drives'] > 1 else ''))
            out.append('        ' + ' · '.join(r['title'][:60] for r in x['rows'][:3])
                       + (f' · +{x["n"] - 3}' if x['n'] > 3 else ''))
    if mail is not None:
        if not mail:
            out.append('  mail: every ask in the threads read is on the stream')
        else:
            out.append(f'  mail: {len(mail)} ask(s) by email with no row. Put them on her list; write one only on her yes:')
            for m in mail:
                out.append(f'    ✉️ {m["subject"][:70]} · {m["sender"]}' + (' · work' if m['work'] else '')
                           + (f' · {m["url"]}' if m.get('url') else ''))
    return out


def read_live(L, every=False):
    """This week's base and last week's while it is still there, the live one
    first: the open rows, or with `every` all of them (the mail half looks for
    an ask among the closed rows too)."""
    from bedo_air import Air
    import datetime as dt
    from bedo_entry import week_number
    from bedo_reader import offset_hours
    air = Air()
    names = air.bases()
    now = dt.datetime.now(dt.timezone.utc)
    today = (now + dt.timedelta(hours=offset_hours(L, now))).date()
    name = L.get('weekly_name', 'w{n} be•do')
    want = []
    for d in (today, today - dt.timedelta(days=7)):          # the live base first
        n = name.format(n=week_number(d))
        if n in names and n not in want:
            want.append(n)
    sf = L.get('stream_fields') or {}
    fields = {k: sf.get(k, k) for k in FIELDS}
    st = fields['status']
    formula = f"OR({', '.join(f'{{{st}}} = ' + repr(s).replace(chr(92), '') for s in OPEN)})"
    rows = []
    for n in want:
        kw = {} if every else dict(formula=formula)
        src = air.dump(names[n], L['stream_table'], by_id=True, **kw)
        rows += [dict(r, _base=n) for r in as_rows(src['records'], fields)]
    return rows


def settings(L):
    people = L.get('people') or {}
    me = [v for v in people.values() if isinstance(v, str) and v]       # the household: self, kid, partner
    if L.get('self_person'):
        me.append(L['self_person'])
    G = L.get('groups') or {}
    return dict(self_names=me, places=G.get('places') or [], hidden=set(L.get('hide_drives') or []),
                my_mail=G.get('my_mail') or [], work_mail=G.get('work_mail') or [])


def main(argv=None):
    ap = argparse.ArgumentParser(description='the groups check: open actions read together, offers only')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--rows', help="a read of the stream's rows (Airtable records)")
    ap.add_argument('--mail', help="the Gmail connector's search_threads result, for asks that never landed")
    ap.add_argument('--json', action='store_true')
    a = ap.parse_args(argv)
    L = load_local()
    S = settings(L)
    if a.live:
        rows = read_live(L, every=bool(a.mail))
    elif a.rows:
        sf = L.get('stream_fields') or {}
        rows = as_rows(read_dump(a.rows)['records'], {k: sf.get(k, k) for k in FIELDS})
    else:
        sys.exit('give --live or --rows FILE')
    g = groups(rows, S['self_names'], S['places'], S['hidden'])
    mail = None
    if a.mail:
        from bedo_inbox import threads_of
        mail = unlanded(threads_of(read_dump(a.mail)), rows, S['my_mail'], S['work_mail'])
    if a.json:
        print(json.dumps(dict(g, mail=mail), ensure_ascii=False, indent=1))
    else:
        print('\n'.join(report(g, mail)))


if __name__ == '__main__':
    main()
