# -*- coding: utf-8 -*-
"""Drive bedo_cal.py --build over saved connector results and check what it
writes — and, just as much, what it refuses. The reader's failures would be
silent otherwise: a cal.json that parses but names the wrong calendar or
misses a page gives a page that looks calm and is wrong.

Every name below is an obvious invention.

    python3 tests/test_cal.py
"""
import base64, json, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
READER = os.path.join(os.path.dirname(HERE), 'scripts', 'bedo_cal.py')
TODAY = '2026-09-22'
LOCAL = {'self_calendar': 'you', 'other_calendars': ['Kid'], 'utc_offset_hours': -5,
         'time_zone': 'America/Chicago',
         'calendar_summaries': {'you': 'my calendar', 'Kid': 'Kid'}}
CALS = {'calendars': [{'id': 'me@example.com', 'summary': 'my calendar'},
                      {'id': 'kid@group.calendar.google.com', 'summary': 'Kid'}]}


def link(event_id, cal='kid@g'):
    # a real link's eid is base64 of '<event id> <calendar>'
    return 'https://www.google.com/calendar/event?eid=' + base64.urlsafe_b64encode(
        f'{event_id} {cal}'.encode()).decode().rstrip('=') + '&ctz=America/Chicago'


def ev(summary, start, end, **kw):
    eid = kw.pop('id', summary.lower())
    e = dict(id=eid, summary=summary, start=start, end=end, status='confirmed', htmlLink=link(eid))
    e.update(kw)
    return e


def timed(summary, day, h1, h2, **kw):
    return ev(summary, {'dateTime': f'2026-09-{day:02d}T{h1:02d}:00:00-05:00'},
              {'dateTime': f'2026-09-{day:02d}T{h2:02d}:00:00-05:00'}, **kw)


YOU = {'summary': 'my calendar', 'events': [
    timed('Standup', 22, 9, 10, recurringEventId='abc'),
    timed('Dentist', 24, 14, 15, location='Main St'),
    ev('Away', {'date': '2026-09-27T00:00:00Z'}, {'date': '2026-09-30T00:00:00Z'}, transparency='transparent'),
]}
KID = {'summary': 'Kid', 'events': [timed('Practice', 23, 16, 17)]}

FAILED = []


def run(tmp):
    r = subprocess.run([sys.executable, READER, '--build', '--today', TODAY, '--local',
                        os.path.join(tmp, 'local.json'), '--dir', os.path.join(tmp, 'cal'),
                        '--out', os.path.join(tmp, 'cal.json')],
                       capture_output=True, text=True, encoding='utf-8')
    return r.returncode, r.stdout + r.stderr


def setup(you=YOU, kid=KID, cals=CALS, local=LOCAL):
    tmp = tempfile.mkdtemp()
    os.mkdir(os.path.join(tmp, 'cal'))
    for name, d in (('local.json', local), ('cal/calendars.json', cals), ('cal/you.json', you), ('cal/Kid.json', kid)):
        if d is not None:
            json.dump(d, open(os.path.join(tmp, name), 'w', encoding='utf-8'), ensure_ascii=False)
    return tmp


def check(name, cond, detail=''):
    if not cond:
        FAILED.append(f'{name}: {detail}')
    print(('ok   ' if cond else 'FAIL ') + name)


# ── a good read builds, in the shape the builder reads ──
tmp = setup()
code, out = run(tmp)
check('good read builds', code == 0, out)
cal = json.load(open(os.path.join(tmp, 'cal.json'), encoding='utf-8'))
check('who labels are the settings labels', [c['who'] for c in cal['calendars']] == ['you', 'Kid'])
you = {e['summary']: e for e in cal['calendars'][0]['events']}
check('recurring marked', you['Standup']['recurring'] is True and you['Dentist']['recurring'] is False)
check('transparent marked', you['Away'].get('transparent') is True and 'transparent' not in you['Dentist'])
check('htmlLink kept', all(e.get('htmlLink') for c in cal['calendars'] for e in c['events']))
check('read counts', cal['read'] == {'window': 'Tue 22 Sep – Mon 5 Oct', 'you': '3/3', 'Kid': '1/1'}, str(cal['read']))
check('one line per event printed', out.count('you:') == 3 and out.count('Kid:') == 1, out)
shutil.rmtree(tmp)

# ── a list of pages is one read ──
p1 = dict(summary='my calendar', events=YOU['events'][:2], nextPageToken='t')
p2 = dict(summary='my calendar', events=YOU['events'][2:])
tmp = setup(you=[p1, p2]); code, out = run(tmp)
check('paged read builds', code == 0 and '3/3' in out, out); shutil.rmtree(tmp)

# ── the refusals ──
tmp = setup(you=[p1]); code, out = run(tmp)
check('refuses a last page with nextPageToken', code != 0 and 'nextPageToken' in out, out); shutil.rmtree(tmp)

tmp = setup(you=dict(YOU, summary='Holidays')); code, out = run(tmp)
check('refuses a read of the wrong calendar', code != 0 and 'wrong calendar id' in out, out); shutil.rmtree(tmp)

tmp = setup(kid=dict(KID, events=[timed('Late', 30, 9, 10)]))  # 30 Sep is past the 14-day window's end of 6 Oct? no — inside
code, out = run(tmp)
check('an event inside the window is fine', code == 0, out); shutil.rmtree(tmp)
tmp = setup(kid=dict(KID, events=[timed('Old', 20, 9, 10)])); code, out = run(tmp)
check('refuses an event before the window', code != 0 and 'outside' in out, out); shutil.rmtree(tmp)

bad = dict(KID, events=[dict(timed('NoLink', 23, 9, 10), htmlLink='')])
tmp = setup(kid=bad); code, out = run(tmp)
check('refuses an event with no htmlLink', code != 0 and 'htmlLink' in out, out); shutil.rmtree(tmp)

tmp = setup(cals=None); code, out = run(tmp)
check('refuses without calendars.json', code != 0 and 'calendars.json' in out, out); shutil.rmtree(tmp)

tmp = setup(cals={'calendars': CALS['calendars'][:1]}); code, out = run(tmp)
check('refuses a calendar missing from the list', code != 0 and 'not in' in out, out); shutil.rmtree(tmp)

tmp = setup(local={k: v for k, v in LOCAL.items() if k != 'calendar_summaries'}); code, out = run(tmp)
check('refuses settings without calendar_summaries', code != 0 and 'calendar_summaries' in out, out); shutil.rmtree(tmp)

tmp = setup(kid=dict(KID, events=KID['events'] + [dict(timed('Gone', 23, 9, 10), status='cancelled')]))
code, out = run(tmp)
check('a cancelled event is dropped', code == 0 and 'Kid 1/1' in out, out); shutil.rmtree(tmp)

drift = dict(KID, events=[dict(timed('Drift', 23, 9, 10), id='someone-else')])
tmp = setup(kid=drift); code, out = run(tmp)
check('refuses a link that names another event', code != 0 and 'own id' in out, out); shutil.rmtree(tmp)
good = dict(KID, events=[timed('Same', 23, 9, 10, id='evt1')])
tmp = setup(kid=good); code, out = run(tmp)
check('a link that names its own event passes', code == 0, out); shutil.rmtree(tmp)

if FAILED:
    print('\n' + '\n'.join(FAILED)); sys.exit(1)
print(f'\nall {out.count("") and 15} checks passed' if False else '\nall checks passed')
