# -*- coding: utf-8 -*-
"""Drive words.py end to end: a draft is written, read back, changed and put on
a page, and what was touched stops being a draft.

The lead and the story are the two things on the page that are not computed,
so nothing downstream can notice when they are wrong. This pins the three ways
they could go wrong quietly: a draft shown as the user's words, an edit that
never reaches the page, and one day's words landing on another day's page.

Every name and sentence below is an obvious invention.

    python3 tests/test_words.py
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORDS = os.path.join(os.path.dirname(HERE), 'scripts', 'words.py')
DAY = '2026-09-22'
WALK = '\U0001F6B6\U0001F3FB‍♀️‍➡️'   # a glyph made of seven codepoints
FAILED = []


def check(name, cond, detail=''):
    if not cond:
        FAILED.append(f'{name}: {detail}')
    print(('  ok   ' if cond else '  FAIL ') + name)


def main():
    tmp = tempfile.mkdtemp(prefix='words-')
    f = os.path.join(tmp, f'words-{DAY}.json')
    page = os.path.join(tmp, f'{DAY}-day-behind.html')

    def run(*args, day=DAY, file=f, page_=page):
        r = subprocess.run([sys.executable, WORDS, '--day', day, '--file', file, '--page', page_, *args],
                           capture_output=True, text=True, encoding='utf-8',
                           env=dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1'))
        return r.returncode, (r.stdout or '') + (r.stderr or '')

    read = lambda: json.load(open(f, encoding='utf-8'))

    # ── a scheduled run writes its draft ──
    code, out = run('--new', '--draft', '--lead', 'An invented day', '--line', WALK, 'A walk that never happened',
                    '--line', '☕', 'Coffee, invented', '--line', '\U0001F319', 'An early night')
    check('a draft is written', code == 0, out)
    W = read()
    check('both parts are marked draft', W['draft'] == ['lead', 'story'] and W['by'] == 'be•do', str(W))
    check('the day is on the file', W['day'] == DAY)
    check('a seven-codepoint glyph survives the command line', W['story'][0][0] == WALK, repr(W['story'][0][0]))
    check('show says what is still a draft', '[draft]' in out and "still be•do's draft: lead, story" in out, out)

    # ── the refusals ──
    code, out = run('--new', '--lead', 'No story', file=os.path.join(tmp, 'x.json'))
    check('refuses a draft with no story', code != 0 and 'at least one --line' in out, out)
    code, out = run('--show', day='2026-09-23')
    check('refuses the words of another day', code != 0 and 'holds the words for' in out, out)
    code, out = run('--set-line', '9', '☕', 'nowhere')
    check('refuses a line that is not there', code != 0 and 'lines 1 to 3' in out, out)
    check('a refused edit leaves the file alone', read() == W)

    # ── a page to carry them: only the words may change ──
    DATA = {'chip': 'c', 'day': DAY, 'title': 'old lead', 'story': [['x', 'old']], 'draft': {'lead': True, 'story': True},
            'who': [{'name': 'Invented Person'}], 'read': 'w39 · 3/3'}
    tail = ';\nconst esc = s => String(s);\n</script>'
    open(page, 'w', encoding='utf-8').write('<script>\nconst DATA = ' + json.dumps(DATA, ensure_ascii=False) + tail)

    def page_data():
        h = open(page, encoding='utf-8').read()
        return json.loads(h.split('const DATA = ', 1)[1].split(';\nconst esc', 1)[0]), h

    # ── editing the lead makes the lead hers, and leaves the story a draft ──
    code, out = run('--set-lead', 'Her own line', '--to-page')
    check('the lead is edited', code == 0 and read()['lead'] == 'Her own line', out)
    check('only the lead stops being a draft', read()['draft'] == ['story'], str(read()['draft']))
    D, h = page_data()
    check('the page carries the new lead', D['title'] == 'Her own line')
    check('the page carries the draft story', D['story'][0] == [WALK, 'A walk that never happened'])
    check('the page marks only the story', D['draft'] == {'lead': False, 'story': True}, str(D['draft']))
    check('nothing else on the page moved', D['who'] == DATA['who'] and D['read'] == DATA['read'] and h.endswith(tail))

    # ── story edits: set, drop, add, in one go ──
    code, out = run('--set-line', '2', '\U0001F375', 'Tea, in fact', '--drop-line', '3',
                    '--add-line', '1', '\U0001F305', 'Up before the light')
    S = read()['story']
    check('set, drop and add land where they were aimed',
          [t for _, t in S] == ['Up before the light', 'A walk that never happened', 'Tea, in fact'], str(S))
    check('an edited story is no longer a draft', read()['draft'] == [] and 'by' not in read(), str(read()))
    check('an edit without --to-page says the page is behind', 'still carries the old words' in out, out)
    check('and it is', page_data()[0]['story'][1] == ['☕', 'Coffee, invented'])

    # ── accepting a draft as it stands ──
    run('--new', '--draft', '--lead', 'A second invented day', '--line', '\U0001F319', 'A night')
    code, out = run('--accept', 'all', '--to-page')
    check('accepting clears the draft without changing a word',
          read()['draft'] == [] and read()['lead'] == 'A second invented day', str(read()))
    check('the page stops saying draft', page_data()[0]['draft'] == {'lead': False, 'story': False})

    # ── another machine: no words file, only the page ──
    os.remove(f)
    code, out = run('--show')
    check('the words are recovered from the page', code == 0 and 'recovered from' in out
          and read()['lead'] == 'A second invented day', out)

    # ── a page for another day, and the bare engine ──
    D, _ = page_data(); D['day'] = '2026-09-21'
    open(page, 'w', encoding='utf-8').write('<script>\nconst DATA = ' + json.dumps(D) + tail)
    code, out = run('--to-page')
    check("refuses another day's page", code != 0 and 'is the page for 2026-09-21' in out, out)
    open(page, 'w', encoding='utf-8').write('<script>\nconst DATA = /*__DATA__*/null' + tail)
    code, out = run('--to-page')
    check('refuses the bare engine', code != 0, out)

    print()
    # ── the log row is the channel from dusk to morning ──
    code, out = run('--new', '--draft', '--lead', 'A rebuilt day', '--line', '☕', 'Coffee again',
                    '--line', WALK, 'The walk, invented', '--row-block', file=os.path.join(tmp, 'row.json'))
    check('the row block is printed', code == 0 and f'[be\u2022do] look behind {DAY} \u00b7 draft' in out
          and 'draft lead: A rebuilt day' in out and f'draft story: {WALK} The walk, invented' in out, out)
    block = out[out.index('[be\u2022do] look behind'):].strip()
    # the dusk chat writes the block into the row; the morning routine reads it back from the dump
    local = os.path.join(tmp, 'local.json')
    json.dump({'fields': {'stream': {'details': 'fldDETAILS', 'key': 'fldKEY'}}}, open(local, 'w'))
    dump = os.path.join(tmp, 'w99.json')
    older = block.replace('draft lead: A rebuilt day', 'draft lead: An older draft')
    edited = block.replace('draft lead: A rebuilt day', 'lead: Her own line')   # she touched the lead at dusk
    json.dump({'records': [
        {'id': 'rec1', 'createdTime': '2026-09-22T23:00:00.000Z',
         'cellValuesByFieldId': {'fldKEY': '260922_2300', 'fldDETAILS': 'her words\n\u2014\u2014\u2014\n' + older}},
        {'id': 'rec2', 'createdTime': '2026-09-23T04:00:00.000Z',
         'cellValuesByFieldId': {'fldKEY': '260922_2300', 'fldDETAILS': 'her words\n\u2014\u2014\u2014\n' + edited}},
        {'id': 'rec3', 'createdTime': '2026-09-23T05:00:00.000Z',
         'cellValuesByFieldId': {'fldKEY': '260921_2300', 'fldDETAILS': block.replace(DAY, '2026-09-21')}},
    ], 'metadata': {'totalRecordCount': 3}}, open(dump, 'w', encoding='utf-8'), ensure_ascii=False)
    f2 = os.path.join(tmp, 'from-row.json')
    code, out = run('--from-stream', dump, '--local', local, file=f2)
    W2 = json.load(open(f2, encoding='utf-8'))
    check('the words come back from the newest row for the day', code == 0 and 'recovered from row rec2' in out, out)
    check('a lead she touched is hers, the story still a draft',
          W2['lead'] == 'Her own line' and W2['draft'] == ['story'] and W2['story'][1][0] == WALK, str(W2))
    check("another day's row is not taken", W2['day'] == DAY)
    code, out = run('--from-stream', dump, '--local', local, day='2026-09-25', file=os.path.join(tmp, 'none.json'))
    check('no row for the day says NO ROW', code != 0 and 'NO ROW' in out, out)
    code, out = run('--row-block', '--final', file=f2)
    check('--final marks the row as the final page, the words still be•do\'s',
          f'\u00b7 final' in out and 'draft story:' in out and '\nlead: Her own line' in out, out)

    # ── which days still need a final ──
    LOG = os.path.join(os.path.dirname(HERE), 'scripts', 'look_behind_log.py')
    json.dump({'fields': {'stream': {'details': 'fldDETAILS', 'key': 'fldKEY'}},
               'week_zero_sunday': '2026-05-03', 'week_zero_number': 19}, open(local, 'w'))
    # a final page can still carry be•do's words, marked: the first line says which build, the prefixes whose words
    final = block.replace(DAY, '2026-09-20').replace('\u00b7 draft', '\u00b7 final')
    json.dump({'records': [
        {'id': 'r1', 'createdTime': '2026-09-21T09:00:00.000Z', 'cellValuesByFieldId': {'fldDETAILS': final}},
        {'id': 'r2', 'createdTime': '2026-09-23T04:00:00.000Z', 'cellValuesByFieldId': {'fldDETAILS': edited}},
    ], 'metadata': {'totalRecordCount': 2}}, open(os.path.join(tmp, 'w39.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    r = subprocess.run([sys.executable, LOG, '--today', '2026-09-24', '--local', local,
                        '--stream', os.path.join(tmp, 'w39.json'), '--cap', '4'],
                       capture_output=True, text=True, encoding='utf-8')
    L = json.loads(r.stdout)
    states = {d['day']: d['state'] for d in L['days']}
    check('a final day, a draft day, a missing day and yesterday are told apart',
          states == {'2026-09-20': 'final', '2026-09-21': 'none', '2026-09-22': 'draft', '2026-09-23': 'none'}, str(states))
    check('to_build is oldest first and leaves the final out',
          L['to_build'] == ['2026-09-21', '2026-09-22', '2026-09-23'], str(L['to_build']))
    r = subprocess.run([sys.executable, LOG, '--today', '2026-09-30', '--local', local,
                        '--stream', os.path.join(tmp, 'w39.json'), '--cap', '3'],
                       capture_output=True, text=True, encoding='utf-8')
    L = json.loads(r.stdout)
    check('a day whose week was not fetched is unreachable, never built',
          all(d['state'] == 'unreachable' for d in L['days']) and L['to_build'] == [], r.stdout)

    if FAILED:
        print('\n'.join('  FAIL ' + x for x in FAILED)); sys.exit(1)
    print('the words can be drafted, changed and carried to the page.')


if __name__ == '__main__':
    main()
