#!/usr/bin/env python3
"""privacy check — nothing personal goes into this public repo.

This repo is the generic engine. Everything specific to a person — names,
places, projects, ids, links, their words — lives in their own settings files
and bases, never here. This check enforces that on every push and pull request.

Two kinds of hit:
  · private terms — never committed, and a hit is printed masked, so the check
    never writes a private word into a public log. Two sources:
      - LIVE from Airtable: the names in every table of the bases named in
        $BEDO_LIVE_BASES (default: connections, rhythms, places), read fresh once per
        run, so a person added to connections is covered from the next pull
        request. Each read costs Airtable calls, and the run says how many.
        In CI it uses $AIRTABLE_READ_TOKEN, a read-only token that can see only
        those bases; in a Claude cloud session the proxy supplies the credential.
        From places, each place's name and the parts of where it is (a street,
        a town), so a place she adds is covered without a list to keep
        (12 Nov 2026, her words: I'm not going to remember the list).
      - STATIC, optional: anything no base holds, from $BEDO_PRIVATE_TERMS (one
        per line; a repo secret in CI) or ~/.bedo/private_terms.txt.
  · patterns anyone's data has — Airtable ids, real email addresses, artifact,
    Drive and Docs links, calendar ids, and location: Google place ids and
    precise coordinates. A home address comes from the places base.
  · services — which apps, stores, banks and devices someone uses is a map to
    their logins (her words, 12 Nov 2026: that is private info, it would be
    easy for someone to try to pull together my logins). A service's name is a
    hit in anything NEW: an added line, a commit message, a pull request's
    title or description, a branch name. Existing files are not re-read for
    them, and an added line in a file whose path names the service (an
    integration's own folder) is let through. Two sources: SERVICES below, a
    generic list of common consumer services, and LIVE the app names in her
    settings rows (`apps` and `services` in any row of the settings table),
    read when that table is readable; a CI token that can't see it skips it.

    python3 tools/privacy_check.py              # every tracked file, as it is now
    python3 tools/privacy_check.py --diff BASE  # lines added and commit messages since BASE
    python3 tools/privacy_check.py --files --diff BASE   # both, with the names read once
    python3 tools/privacy_check.py --history    # every version of every file, every message,
                                                # every branch and tag name
    python3 tools/privacy_check.py --outgoing --title "TITLE" --text pr.md
        # before a push or a pull request: every file, the lines, messages and
        # author emails since origin/main, this branch's name, and the PR's own
        # title and description — the one run every chat makes (12 Nov 2026)

What the public sees is more than the files (her words, 12 Nov 2026: the privacy
check only scans repo files, so PR titles, descriptions and commit messages slip
through). `--title STRING`, `--text FILE` (`-` for stdin) and `--branch NAME`
each check one more thing, and each may be given more than once.

Exit 1 on any hit.
"""
import os, re, subprocess, sys

PATTERNS = [
    ('airtable id', re.compile(r'\b(?:app|tbl|fld|rec|viw|sel|usr|wsp)[A-Za-z0-9]{14}\b')),
    ('email', re.compile(r'\b[\w.+-]+@[\w-]+\.[\w.-]+\b')),
    ('artifact link', re.compile(r'claude\.ai/(?:code/)?artifact/[\w-]{8,}')),
    ('drive or docs link', re.compile(r'(?:drive|docs)\.google\.com/\S+')),
    ('calendar event link', re.compile(r'google\.com/calendar/event\?eid=\w+')),
    # where someone has been: a Google place id points at one exact spot, and a
    # precise lat,lng pair or a Timeline E7 coordinate is a spot by itself
    ('google place id', re.compile(r'\bChIJ[\w-]{20,}')),
    ('coordinates', re.compile(r'(?<![\d.])-?[1-9]\d?\.\d{4,}\s*,\s*-?\d{2,3}\.\d{4,}\b')),
    ('timeline coordinate', re.compile(r'\b(?:lat|lng|latitude|longitude)E7\"?\s*[:=]\s*-?\d{6,}')),
]
# placeholders the tests and examples use on purpose
ALLOW = re.compile(r'^(?:me|you|kid|fam|someone|user|name|example|test|noreply)@'
                   r'|@(?:example\.(?:com|org)|anthropic\.com|users\.noreply\.github\.com)$'
                   r'|@group(?:\.v)?\.calendar\.google\.com$|^\w@'
                   r'|^(?:fld|tbl|app|rec)X+$', re.I)
SKIP = ('tools/privacy_check.py',)

# Common consumer services, by any name a person would write. Generic and
# public: it says nothing about who uses which; her own list is read live.
SERVICES = [
    'Netflix', 'HBO Max', 'HBO', 'Hulu', 'Disney+', 'Disney Plus', 'Prime Video', 'Amazon Prime',
    'Peacock', 'Paramount+', 'Apple TV', 'YouTube TV', 'YouTube Premium', 'Sling', 'Fubo', 'Tubi',
    'Pluto TV', 'Plex', 'MGM+', 'Crunchyroll', 'Spotify', 'Pandora', 'SiriusXM', 'Apple Music',
    'Audible', 'Kindle', 'Libby', 'Hoopla', 'Scribd', 'Kobo', 'Goodreads',
    'Venmo', 'PayPal', 'Zelle', 'Cash App', 'Chase', 'Wells Fargo', 'Bank of America', 'Capital One',
    'Citibank', 'American Express', 'Amex', 'Discover card', 'Ally Bank', 'USAA', 'Navy Federal',
    'Schwab', 'Fidelity', 'Vanguard', 'Robinhood', 'Coinbase', 'Mint', 'Quicken', 'TurboTax',
    'Oura', 'Fitbit', 'Whoop', 'Garmin', 'Peloton', 'Strava', 'MyFitnessPal', 'Noom', 'Calm', 'Headspace',
    'H-E-B', 'HEB', 'Kroger', 'Walmart', 'Costco', 'Instacart', 'DoorDash', 'Uber Eats', 'Grubhub',
    'Ring doorbell', 'Nest', 'Alexa', 'Life360', 'Ancestry', '23andMe', 'MyChart',
]


# a first name that is also an everyday word, or a placeholder the tests use, is
# matched only as part of the full name it came with
COMMON = {'field', 'mark', 'will', 'alex', 'dana', 'blair', 'casey', 'may', 'june',
          'rose', 'grace', 'hope', 'joy', 'faith', 'river', 'sage', 'reed', 'bill',
          'pat', 'art', 'drew', 'chase', 'hunter', 'page', 'sky', 'dawn', 'summer',
          'the', 'and', 'team', 'group', 'family', 'friends', 'work', 'school', 'mom',
          'dad', 'granny', 'grandpa', 'grandma', 'doctor', 'church', 'new', 'old', 'big',
          'day', 'one', 'two', 'miss', 'mrs', 'mr', 'dr', 'ms', 'aunt', 'uncle', 'son', 'kid',
          # month and weekday abbreviations are code, whoever shares the name
          'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'sept', 'oct', 'nov', 'dec',
          'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'}
REPO_WORDS = {'be•do', 'be-do', 'bedo'}


CALLS = 0   # Airtable calls this run made; the plan counts every one


def _get(url, token):
    import json, urllib.request
    global CALLS
    CALLS += 1
    req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'} if token else {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def live_terms():
    """Every name in the live bases. Returns None when no source is configured."""
    import urllib.parse
    token = os.environ.get('AIRTABLE_READ_TOKEN')
    in_cloud = os.environ.get('CLAUDE_CODE_REMOTE') == 'true'
    if not token and not in_cloud:
        return None
    want = {b.strip().lower() for b in os.environ.get('BEDO_LIVE_BASES', 'connections,rhythms,places').split(',')
            if b.strip()}
    api, out = 'https://api.airtable.com/v0', set()
    bases, off = [], None
    while True:
        d = _get(f'{api}/meta/bases' + (f'?offset={off}' if off else ''), token)
        bases += [b for b in d.get('bases', []) if b['name'].strip().lower() in want]
        off = d.get('offset')
        if not off:
            break
    if not bases:
        raise RuntimeError('none of the live bases is readable: ' + ', '.join(sorted(want)))
    for b in bases:
        people = 'connection' in b['name'].lower()
        for t in _get(f"{api}/meta/bases/{b['id']}/tables", token)['tables']:
            extra = {f['id']: f['name'].lower() for f in t['fields'] if f['name'].lower() in ('short name', 'where')}
            fids = [t['primaryFieldId']] + list(extra)
            off = None
            while True:
                q = [('returnFieldsByFieldId', 'true'), ('pageSize', '100')] + [('fields[]', f) for f in fids]
                if off:
                    q.append(('offset', off))
                d = _get(f"{api}/{b['id']}/{t['id']}?{urllib.parse.urlencode(q)}", token)
                for r in d['records']:
                    for f in fids:
                        v = str(r['fields'].get(f) or '')
                        out.update(where_terms(v) if extra.get(f) == 'where' else names_in(v, people))
                off = d.get('offset')
                if not off:
                    break
    return out


def names_in(v, people):
    """The private names in one value from a live base."""
    out = set()
    v = re.sub(r'^[\W_]+', '', v, flags=re.UNICODE)
    # in brackets: a capitalised nickname is a name, a lowercase note is not
    nick = [n.strip() for n in re.findall(r'[(\[]([^)\]]*)[)\]]', v) if n.strip()[:1].isupper()]
    v = re.sub(r'\s*[(\[][^)\]]*[)\]]', '', v).strip()
    out.update(n for n in nick if len(n) >= 3 and n.lower() not in COMMON)
    words = v.split()
    # from connections, every name; from the other bases (drives, places, values)
    # only the specific ones — two words or more with a capital after the first,
    # like a place or a person — never 'Love', 'cooking' or 'Home'
    specific = len(words) >= 2 and any(w[:1].isupper() for w in words[1:])
    if len(v) >= 3 and v.lower() not in REPO_WORDS and (people or specific):
        out.add(v)
    if people:   # a person's first and last names are each theirs
        for tok in re.split(r'[\s,/&()]+', v):
            if len(tok) >= 3 and tok[:1].isupper() and tok.lower() not in COMMON:
                out.add(tok)
    return out


def where_terms(v):
    """The private parts of a place's address: the whole of it, a street (it starts
    with a number), and any specific part like a town of two words. A one-word town
    or a state is left out: it is everyday text, and alone it points at no one."""
    v = v.strip()
    out = {v} if len(v) >= 8 else set()
    for part in (p.strip() for p in v.split(',')):
        if re.match(r'\d+\s+\S', part) and len(part) >= 6:
            out.add(part)
        elif part:
            out |= names_in(part, False)
    return out


def terms():
    raw = os.environ.get('BEDO_PRIVATE_TERMS')
    if raw is None:
        p = os.path.expanduser('~/.bedo/private_terms.txt')
        raw = open(p, encoding='utf-8').read() if os.path.exists(p) else ''
    ts = {t.strip() for t in raw.replace(',', '\n').splitlines() if len(t.strip()) >= 3}
    try:
        live = live_terms()
    except Exception as e:   # configured but unreadable is a failure, never a silent pass
        print(f'privacy check: could not read the live names — {type(e).__name__}', file=sys.stderr)
        sys.exit(2)
    if live is None:
        print('privacy check: no live names source — checking the static list and patterns', file=sys.stderr)
    else:
        print(f'privacy check: {len(live)} live names read in {CALLS} Airtable calls', file=sys.stderr)
        ts |= live
    ts = sorted({t for t in ts if t.lower() not in COMMON}, key=len, reverse=True)
    if not ts:
        print('privacy check: no private terms list — checking patterns only', file=sys.stderr)
    return [(t, re.compile(r'(?<![\w])' + re.escape(t) + r'(?![\w])', re.I)) for t in ts]


def live_services():
    """The services her settings name: `apps[].app` and `services` in any row of
    the settings table. An empty set when that table can't be read here."""
    import json, urllib.parse
    token = os.environ.get('AIRTABLE_READ_TOKEN')
    if not token and os.environ.get('CLAUDE_CODE_REMOTE') != 'true':
        return set()
    api, out = 'https://api.airtable.com/v0', set()
    try:
        bases = _get(f'{api}/meta/bases', token).get('bases', [])
        base = next((b['id'] for b in bases if b['name'].strip().lower() == 'be•do system'), None)
        if not base:
            return out
        table = next((x['id'] for x in _get(f'{api}/meta/bases/{base}/tables', token)['tables']
                      if x['name'].lower() == 'settings'), None)
        if not table:
            return out
        for r in _get(f'{api}/{base}/{table}?pageSize=100', token).get('records', []):
            try:
                d = json.loads(r['fields'].get('json') or '{}')
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            out |= {a.get('app', '') for a in d.get('apps', []) if isinstance(a, dict)}
            out |= {s for s in d.get('services', []) if isinstance(s, str)}
    except Exception:   # noqa: BLE001 — the generic list still stands
        return out
    return {s.strip() for s in out if len(s.strip()) >= 3 and s.strip().lower() not in ('paper books', 'elsewhere')}


# services that are also everyday words count only as written, capitalised
CASED = {'Nest', 'Calm', 'Mint', 'Chase', 'Peacock', 'Sling', 'Fidelity', 'Discover', 'Ring', 'Target'}


def service_terms():
    names = set(SERVICES) | live_services()
    return [(s, re.compile(r'(?<![\w])' + re.escape(s) + r'(?![\w+])', 0 if s in CASED else re.I))
            for s in sorted(names, key=len, reverse=True)]


def check_services(text, where, S, hits, path=''):
    """A service named in new text. A line in a file whose path names the service
    (an integration's own folder) is let through."""
    p = re.sub(r'[^a-z0-9]+', '', path.lower())
    for n, line in enumerate(text.splitlines(), 1):
        if 'privacy: ok' in line:
            continue
        for s, rx in S:
            if rx.search(line) and not (p and re.sub(r'[^a-z0-9]+', '', s.lower()) in p):
                hits.append(f'{where}:{n}: a service someone uses {mask(s)}')
                break


def mask(s):
    return s[0] + '·' * (len(s) - 1)


def check(text, where, T, hits):
    for n, line in enumerate(text.splitlines(), 1):
        if 'privacy: ok' in line:   # a made-up value in a test, marked by hand and reviewed
            continue
        for t, rx in T:
            if rx.search(line):
                hits.append(f'{where}:{n}: private term {mask(t)}')
        for name, rx in PATTERNS:
            for m in rx.finditer(line):
                if not ALLOW.search(m.group(0)):
                    hits.append(f'{where}:{n}: {name} {mask(m.group(0))}')


def git(*a):
    return subprocess.run(['git', *a], capture_output=True, text=True, check=True).stdout


class Run:
    """What one run checks. `files`, `base` and `history` as before; `texts` are
    (where, text) pairs: a PR's title and description, a comment; `branches`
    are branch names, read as words (`a_b/c` is checked as `a b c`)."""
    def __init__(self):
        self.files, self.base, self.history, self.texts, self.branches = False, None, False, [], []

    def as_tuple(self):
        return self.files, self.base, self.history


def read_text(path):
    if path == '-':
        return sys.stdin.read()
    with open(path, encoding='utf-8') as f:
        return f.read()


def current_branch():
    try:
        b = git('rev-parse', '--abbrev-ref', 'HEAD').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return None if b in ('', 'HEAD') else b


def parse(a):
    """What to check. With nothing to check named, every tracked file. --files and
    --diff BASE may be given together, so one run reads the names once and checks
    both. --outgoing is the run before anything leaves: the files, the change since
    origin/main (unless --diff names another base) and the current branch's name."""
    r, outgoing, i = Run(), False, 0
    one = {'--diff', '--title', '--text', '--branch'}
    while i < len(a):
        if a[i] in one and i + 1 < len(a):
            k, v, i = a[i], a[i + 1], i + 2
            if k == '--diff':
                r.base = v
            elif k == '--title':
                r.texts.append(('title', v))
            elif k == '--text':
                r.texts.append((f'text {v}', read_text(v)))
            else:
                r.branches.append(v)
        elif a[i] == '--files':
            r.files, i = True, i + 1
        elif a[i] == '--history':
            r.history, i = True, i + 1
        elif a[i] == '--outgoing':
            outgoing, i = True, i + 1
        else:
            print(f'privacy check: unknown argument {a[i]}', file=sys.stderr)
            sys.exit(2)
    if outgoing:
        r.files, r.base = True, r.base or 'origin/main'
        b = current_branch()
        if b and b not in r.branches:
            r.branches.append(b)
    if not (r.base or r.history or r.texts or r.branches):
        r.files = True
    return r


def modes(a):
    return parse(a).as_tuple()


def branch_words(name):
    """A branch name as the words in it: `/`, `_` and `.` separate words there."""
    return re.sub(r'[/_.]+', ' ', name.removeprefix('refs/heads/'))


def check_texts(texts, T, hits, S=()):
    for where, text in texts:
        check(text, where, T, hits)
        check_services(text, where, S, hits)


def check_branches(names, T, hits, S=()):
    for b in names:
        check(branch_words(b), f'branch name {mask(b)}', T, hits)
        check_services(branch_words(b), f'branch name {mask(b)}', S, hits)


def check_files(T, hits):
    for path in git('ls-files').splitlines():
        if path in SKIP:
            continue
        try:
            check(open(path, encoding='utf-8').read(), path, T, hits)
        except (UnicodeDecodeError, FileNotFoundError):
            continue


def check_diff(base, T, hits, S=()):
    try:
        git('merge-base', base, 'HEAD')
    except subprocess.CalledProcessError:
        # a fresh start shares no history with the old base: every file is
        # checked whole (--files), so only the new commits' messages remain
        print(f'privacy check: no history shared with {base} — checking the files and the new commit messages', file=sys.stderr)
        for sha in git('rev-list', 'HEAD', '--not', base).split():
            msg = git('log', '-1', '--format=%B', sha)
            check(msg, f'commit {sha[:7]}', T, hits)
            check_services(msg, f'commit {sha[:7]}', S, hits)
            check_people(sha, hits)
        return
    path = ''
    for line_no, line in enumerate(git('diff', '-U0', f'{base}...HEAD', '--', '.', *[f':!{s}' for s in SKIP]).splitlines()):
        if line.startswith('+++ '):
            path = line[4:].removeprefix('b/')
        elif line.startswith('+'):
            check(line[1:], f'diff+{line_no}', T, hits)
            check_services(line[1:], f'diff+{line_no} {path}', S, hits, path)
    for sha in git('rev-list', f'{base}..HEAD').split():
        msg = git('log', '-1', '--format=%B', sha)
        check(msg, f'commit {sha[:7]}', T, hits)
        check_services(msg, f'commit {sha[:7]}', S, hits)
        check_people(sha, hits)


def check_people(sha, hits):
    """A commit's author and committer emails are public too: a personal address
    reached main that way once (3 Nov 2026). Only the patterns are checked here: the
    names on a commit are the GitHub account's own display name."""
    for name, rx in PATTERNS:
        if name != 'email':
            continue
        for m in rx.finditer(git('log', '-1', '--format=%ae %ce', sha)):
            if not ALLOW.search(m.group(0)):
                hits.append(f'commit {sha[:7]} author: {name} {mask(m.group(0))}')


def check_history(T, hits):
    seen = set()
    for row in git('rev-list', '--all', '--objects').splitlines():
        sha, _, path = row.partition(' ')
        if not path or path in SKIP or sha in seen:
            continue
        seen.add(sha)
        if git('cat-file', '-t', sha).strip() != 'blob':
            continue
        try:
            check(git('cat-file', 'blob', sha), f'{path}@{sha[:7]}', T, hits)
        except (subprocess.CalledProcessError, UnicodeDecodeError):
            continue
    for sha in git('rev-list', '--all').split():
        check(git('log', '-1', '--format=%B', sha), f'commit {sha[:7]}', T, hits)
        check_people(sha, hits)
    refs = git('for-each-ref', '--format=%(refname:lstrip=2)', 'refs/heads', 'refs/remotes', 'refs/tags').split()
    check_branches([r.split('/', 1)[1] if r.startswith('origin/') else r for r in refs if r not in ('origin', 'origin/HEAD')],
                   T, hits)


def main(a=None):
    r = parse(sys.argv[1:] if a is None else a)
    T, hits = terms(), []
    S = service_terms() if (r.base or r.texts or r.branches) else []
    if r.files:
        check_files(T, hits)
    if r.base:
        check_diff(r.base, T, hits, S)
    if r.history:
        check_history(T, hits)
    check_texts(r.texts, T, hits, S)
    check_branches(r.branches, T, hits, S)
    for h in hits:
        print(h)
    print(f'privacy check: {len(hits)} hit(s)', file=sys.stderr)
    sys.exit(1 if hits else 0)


if __name__ == '__main__':
    main()
