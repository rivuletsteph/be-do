# -*- coding: utf-8 -*-
"""words.py — the lead and the story, kept so they can be drafted, read back,
changed, and put on a page.

The lead and the story are the two things on The Day Behind that are not
computed. In a chat with the user present they are written there. In a
scheduled run nobody is present, so be•do drafts them from the day's digest and
marks them as a draft (amendment [id], 28 Sep 2026: a scheduled
look behind may draft its own lead and story, as long as they stay editable).
This script is the "editable": every change is one command, the part that was
touched stops being a draft, and the change goes straight into the built page
without reading Airtable again.

    # a scheduled run writes its draft
    python3 words.py --day D --file words-D.json --new --draft \\
        --lead "one line naming the day" --line 🚗 "a stretch" --line 🌙 "another"

    # read it back, numbered
    python3 words.py --day D --file words-D.json --show

    # change it; what is touched is no longer a draft
    python3 words.py --day D --file words-D.json --set-lead "her line"
    python3 words.py --day D --file words-D.json --set-line 2 🌳 "her stretch" --drop-line 4
    python3 words.py --day D --file words-D.json --add-line 3 ☕ "a stretch that was missing"
    python3 words.py --day D --file words-D.json --accept all     # they are fine as they are

    # put the words on the page already built, no re-read
    python3 words.py --day D --file words-D.json --page D-day-behind.html --to-page

    # no words file on this machine: recover it from the page
    python3 words.py --day D --file words-D.json --page D-day-behind.html --from-page

The file: {"day": "YYYY-MM-DD", "lead": "…", "story": [[glyph, text], …],
"draft": ["lead", "story"], "by": "be•do"}. `draft` names the parts that are
still be•do's; an empty list means both are the user's. The builder refuses a
file whose day is not the day it is building.

Edits are applied in this order whatever order they are typed in: the lead,
then --set-line, then --drop-line (highest first), then --add-line. Line
numbers are the ones --show printed.
"""
import argparse, json, os, sys

PARTS = ('lead', 'story')
MARK = 'const DATA = '


def die(msg):
    sys.exit('ABORT: ' + msg)


def norm_draft(v):
    """true → both parts; a name or a list of names → those; anything empty → none.
    The page's own form, {"lead": bool, "story": bool}, is read too."""
    if v is True:
        return list(PARTS)
    if not v:
        return []
    if isinstance(v, dict):
        v = [k for k, on in v.items() if on]
    if isinstance(v, str):
        v = [v]
    bad = [x for x in v if x not in PARTS]
    if bad:
        die(f'draft names {bad}; it may only name lead and story')
    return [p for p in PARTS if p in v]


def check(W):
    if not (W['lead'] or '').strip():
        die('the lead is empty')
    if '\n' in W['lead'].strip():
        die('the lead is one line')
    if not W['story']:
        die('the story has no lines — a page with an empty story reads as a day that did not happen')
    for i, ln in enumerate(W['story'], 1):
        if len(ln) != 2 or not str(ln[0]).strip() or not str(ln[1]).strip():
            die(f'story line {i} needs a glyph and a text')


def load(path, day):
    W = json.load(open(path, encoding='utf-8'))
    if W.get('day') and W['day'] != day:
        die(f"{path} holds the words for {W['day']}, not {day}")
    return dict(day=day, lead=(W.get('lead') or '').strip(),
                story=[[str(g).strip(), str(t).strip()] for g, t in (W.get('story') or [])],
                draft=norm_draft(W.get('draft')), by=W.get('by'))


def save(path, W):
    out = dict(day=W['day'], lead=W['lead'], story=W['story'], draft=W['draft'])
    if W['draft']:
        out['by'] = W.get('by') or 'be•do'
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(out, fh, ensure_ascii=False, indent=1)
        fh.write('\n')


def page_data(path):
    html = open(path, encoding='utf-8').read()
    i = html.find(MARK)
    if i < 0:
        die(f'{path}: no page data in it — is this a built look behind?')
    j = i + len(MARK)
    try:
        D, end = json.JSONDecoder().raw_decode(html, j)
    except ValueError as ex:
        die(f'{path}: the page data does not parse ({ex})')
    if not isinstance(D, dict):
        die(f'{path}: this is the engine, not a built page')
    return html, D, j, end


def from_page(path, day):
    _, D, _, _ = page_data(path)
    if D.get('day') and D['day'] != day:
        die(f"{path} is the page for {D['day']}, not {day}")
    return dict(day=day, lead=(D.get('title') or '').strip(),
                story=[[str(g), str(t)] for g, t in (D.get('story') or [])],
                draft=norm_draft(D.get('draft')), by=None)


def to_page(path, W):
    html, D, j, end = page_data(path)
    if D.get('day') and D['day'] != W['day']:
        die(f"{path} is the page for {D['day']}, not {W['day']}")
    D['title'], D['story'] = W['lead'], W['story']
    D['draft'] = {p: p in W['draft'] for p in PARTS}
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(html[:j] + json.dumps(D, ensure_ascii=False) + html[end:])


def show(W, path):
    tag = lambda p: '  [draft]' if p in W['draft'] else ''
    print(f"{W['day']} · {path}")
    print(f"lead{tag('lead')}")
    print(f"     {W['lead']}")
    print(f"story{tag('story')}")
    for i, (g, t) in enumerate(W['story'], 1):
        print(f'  {i:>2} {g}  {t}')
    if W['draft']:
        print(f"still be•do's draft: {', '.join(W['draft'])}")
    else:
        print('both are the user\'s')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--day', required=True)
    ap.add_argument('--file', required=True, help='the words file for this day')
    ap.add_argument('--page', help='the built page for this day')
    ap.add_argument('--new', action='store_true', help='write a fresh file from --lead and --line')
    ap.add_argument('--draft', action='store_true', help="with --new: these are be•do's, not the user's")
    ap.add_argument('--lead')
    ap.add_argument('--line', nargs=2, action='append', metavar=('GLYPH', 'TEXT'), default=[])
    ap.add_argument('--from-page', action='store_true', help='recover the words from --page')
    ap.add_argument('--show', action='store_true')
    ap.add_argument('--set-lead')
    ap.add_argument('--set-line', nargs=3, action='append', metavar=('N', 'GLYPH', 'TEXT'), default=[])
    ap.add_argument('--drop-line', type=int, action='append', default=[])
    ap.add_argument('--add-line', nargs=3, action='append', metavar=('N', 'GLYPH', 'TEXT'), default=[])
    ap.add_argument('--accept', choices=PARTS + ('all',), action='append', default=[])
    ap.add_argument('--to-page', action='store_true', help='write the words into --page, no re-read')
    a = ap.parse_args()

    edits = bool(a.set_lead or a.set_line or a.drop_line or a.add_line or a.accept)
    if a.new:
        if edits or a.from_page:
            die('--new writes a fresh file; it does not combine with edits or --from-page')
        if not a.lead or not a.line:
            die('--new needs --lead and at least one --line')
        W = dict(day=a.day, lead=a.lead.strip(), story=[[g.strip(), t.strip()] for g, t in a.line],
                 draft=list(PARTS) if a.draft else [], by='be•do' if a.draft else None)
    elif a.from_page or not os.path.exists(a.file):
        if not (a.page and os.path.exists(a.page)):
            die(f'{a.file} is not here and there is no page to recover it from'
                + (f' ({a.page})' if a.page else ' (pass --page)'))
        W = from_page(a.page, a.day)
        print(f'recovered from {a.page}')
    else:
        W = load(a.file, a.day)

    def n_of(s, top):
        try:
            n = int(s)
        except ValueError:
            die(f'{s!r} is not a line number')
        if not 1 <= n <= top:
            die(f'line {n} — the story has lines 1 to {top}' if top == len(W['story'])
                else f'line {n} — a new line goes at 1 to {top}')
        return n

    touched = set()
    if a.set_lead is not None:
        W['lead'] = a.set_lead.strip(); touched.add('lead')
    for n, g, t in a.set_line:
        W['story'][n_of(n, len(W['story'])) - 1] = [g.strip(), t.strip()]; touched.add('story')
    for n in sorted(a.drop_line, reverse=True):
        del W['story'][n_of(n, len(W['story'])) - 1]; touched.add('story')
    for n, g, t in a.add_line:
        W['story'].insert(n_of(n, len(W['story']) + 1) - 1, [g.strip(), t.strip()]); touched.add('story')
    for p in a.accept:
        touched.update(PARTS if p == 'all' else (p,))
    # what the user touched, or accepted as it stands, is theirs from here on
    W['draft'] = [p for p in W['draft'] if p not in touched]

    check(W)
    if a.new or edits or a.from_page or not os.path.exists(a.file):
        save(a.file, W)
    show(W, a.file)
    if a.to_page:
        if not (a.page and os.path.exists(a.page)):
            die(f'--to-page: no page at {a.page} — build it first')
        to_page(a.page, W)
        print(f'{a.page} now carries these words')
    elif edits and a.page and os.path.exists(a.page):
        print(f'{a.page} still carries the old words — add --to-page, then publish')


if __name__ == '__main__':
    main()
