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

    # the log row is the channel from the dusk chat to the morning routine:
    # print the [be•do] block the row carries …
    python3 words.py --day D --file words-D.json --row-block
    # … and, the next morning, recover the words from that row in the stream dump
    python3 words.py --day D --file words-D.json --local look_behind_local.json \
        --from-stream data/w40.json [--from-stream data/w39.json]

The file: {"day": "YYYY-MM-DD", "lead": "…", "story": [[glyph, text], …],
"draft": ["lead", "story"], "by": "be•do"}. `draft` names the parts that are
still be•do's; an empty list means both are the user's. The builder refuses a
file whose day is not the day it is building.

The row block (SKILL.md step 8). The dusk chat and the morning routine share
no file; what they share is the stream. The look behind's log row carries the
words in its [be•do] block, one line each, and the first line names the day
and whether the page is still a draft:

    [be•do] look behind 2026-09-28 · draft
    draft lead: A Monday that did everything by loosening its grip
    draft story: ☕ Coffee on the back patio from before eight …
    draft story: 🐶 An evening walk with Buddy and Rosa …

The first line says which PAGE the row stands for — `· draft`, the dusk build
of a day not yet over, or `· final`, the morning build from the whole day's
rows (`--row-block --final`). The `draft ` prefix on a line says whose WORDS
they are: a part the user touched or accepted loses it — `lead: …`,
`story: …` — and a final page can still carry be•do's draft words, marked.
`--from-stream` finds the row by its first line (never by title or practice,
which a chat may write differently), the newest matching row wins, and the
prefixes say which parts are still be•do's. The routine then edits nothing:
it builds the final from these words as they stand.

Edits are applied in this order whatever order they are typed in: the lead,
then --set-line, then --drop-line (highest first), then --add-line. Line
numbers are the ones --show printed.
"""
import argparse, json, os, re, sys

PARTS = ('lead', 'story')
MARK = 'const DATA = '
# the first line of the log row's [be•do] block, and the words under it
ROW_HEAD = re.compile(r'^\[be\u2022do\] look behind (\d{4}-\d{2}-\d{2})(?:\s*\u00b7\s*(draft|final))?\s*$', re.M)
ROW_LEAD = re.compile(r'^(draft )?lead:\s*(.+?)\s*$', re.M)
ROW_LINE = re.compile(r'^(draft )?story:\s*(\S+)\s+(.+?)\s*$', re.M)


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


def row_block(W, page='draft'):
    """The [be•do] block for the look behind's log row, carrying these words.
    `page` is which build the row stands for: the dusk draft or the final."""
    out = [f"[be\u2022do] look behind {W['day']} \u00b7 {page}"]
    out.append(('draft ' if 'lead' in W['draft'] else '') + 'lead: ' + W['lead'])
    for g, t in W['story']:
        out.append(('draft ' if 'story' in W['draft'] else '') + f'story: {g} {t}')
    return '\n'.join(out)


def parse_block(text):
    """The words out of a details field, or None when it carries no block."""
    m = ROW_HEAD.search(text or '')
    if not m:
        return None
    body = text[m.end():]
    lead = ROW_LEAD.search(body)
    lines = ROW_LINE.findall(body)
    draft = []
    if lead and lead.group(1):
        draft.append('lead')
    if lines and any(d for d, _, _ in lines):
        draft.append('story')
    return dict(day=m.group(1), page=(m.group(2) or 'draft'), lead=(lead.group(2) if lead else ''),
                story=[[g, t] for _, g, t in lines], draft=draft, by='be\u2022do' if draft else None)


def from_stream(paths, day, local):
    """The words the dusk chat left in the day's log row. Every dump is read,
    live base first, and among the rows whose block names this day the newest
    wins (the row may have been written at dusk and updated since)."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from bedo_common import read_dump
    L = json.load(open(local, encoding='utf-8'))
    fs = (L.get('fields') or {}).get('stream') or {}
    if not fs.get('details'):
        die('local settings: fields.stream.details is needed to read the row')
    hits = []
    for p in paths:
        for r in (read_dump(p) or {}).get('records') or []:
            c = r.get('cellValuesByFieldId') or {}
            W = parse_block(c.get(fs['details']))
            if W and W['day'] == day:
                hits.append((r.get('createdTime') or '', r['id'], c.get(fs.get('key')), W))
    if not hits:
        return None, None
    hits.sort()
    created, rid, key, W = hits[-1]
    return W, dict(id=rid, key=key, created=created)


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
    ap.add_argument('--from-stream', action='append', default=[], metavar='DUMP',
                    help="recover the words from the day's look-behind log row in a stream dump (needs --local)")
    ap.add_argument('--local', help='the settings file, for the stream field ids')
    ap.add_argument('--row-block', action='store_true',
                    help="print the [be\u2022do] block for the log row, carrying these words")
    ap.add_argument('--final', action='store_true',
                    help='with --row-block: the row stands for the final page, not the dusk draft')
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
        if edits or a.from_page or a.from_stream:
            die('--new writes a fresh file; it does not combine with edits, --from-page or --from-stream')
        if not a.lead or not a.line:
            die('--new needs --lead and at least one --line')
        W = dict(day=a.day, lead=a.lead.strip(), story=[[g.strip(), t.strip()] for g, t in a.line],
                 draft=list(PARTS) if a.draft else [], by='be•do' if a.draft else None)
    elif a.from_stream:
        if not a.local:
            die('--from-stream needs --local, for the stream field ids')
        W, row = from_stream(a.from_stream, a.day, a.local)
        if not W:
            sys.exit(f'NO ROW: no look-behind log row for {a.day} carries a words block in '
                     + ', '.join(a.from_stream) + ' — the routine drafts the words itself, marked')
        print(f"recovered from row {row['id']}" + (f" ({row['key']})" if row.get('key') else '')
              + f" \u00b7 the row stands for the {W.pop('page')} page")
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
    if a.new or edits or a.from_page or a.from_stream or not os.path.exists(a.file):
        save(a.file, W)
    show(W, a.file)
    if a.row_block:
        print()
        print(row_block(W, 'final' if a.final else 'draft'))
    if a.to_page:
        if not (a.page and os.path.exists(a.page)):
            die(f'--to-page: no page at {a.page} — build it first')
        to_page(a.page, W)
        print(f'{a.page} now carries these words')
    elif edits and a.page and os.path.exists(a.page):
        print(f'{a.page} still carries the old words — add --to-page, then publish')


if __name__ == '__main__':
    main()
