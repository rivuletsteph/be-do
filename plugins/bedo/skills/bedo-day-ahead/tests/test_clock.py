# -*- coding: utf-8 -*-
"""Drive the builder over a small fixture and check the clocks it writes.

The day ahead prints times in the user's own shorthand — 9:30a, 2p, ends 1am,
through Sun 27 Sep. Those used to be built with glibc's '%-I' and '%-d', which
drop a leading zero but are a GNU extension: on Windows strftime raises on them
outright, so the builder ran on one laptop and nowhere else. They are formatted
by hand now, and this pins the exact strings they have to produce.

It is also the only test that runs day_ahead.py end to end, so a fixture that
stops parsing or a template that stops filling fails here too.

Every name and sentence below is an obvious invention.

    python3 tests/test_clock.py
"""
import json, os, subprocess, sys, tempfile, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
BUILDER = os.path.join(SKILL, 'scripts', 'day_ahead.py')
ENGINE = os.path.join(SKILL, 'assets', 'day_ahead_engine.html')

TODAY = dt.date(2026, 9, 22)       # a Tuesday, so the weekday names are checkable

SF = dict(title='fldTitle', key='fldKey', details='fldDetails', when='fldWhen',
          end='fldEnd', target='fldTarget', status='fldStatus',
          practice='fldPractice', person='fldPerson', rhythm='fldRhythm',
          waiting='fldWaiting', queue='fldQueue', event='fldEvent')
RF = dict(name='fldRName', code='fldRCode', type='fldRType', status='fldRStatus',
          target='fldRTarget', parent='fldRParent', emoji='fldREmoji',
          dest='fldRDest', goal='fldRGoal')

LOCAL = {
    'self_person': 'Self', 'self_calendar': 'you', 'other_calendars': ['other'],
    'own_practices': ['look ahead'], 'weighing_phrases': [r'weigh(s|ing)? on me'],
    'week_word_title': r'^Weekly intention — (.+)$',
    'week_zero_sunday': '2026-09-13', 'week_zero_number': 38,
    'map_end': '2026-12-31', 'utc_offset_hours': 0,
    'rhythms_base': '', 'rhythms_table': '', 'artifact_url': '',
    'drive_name_example': 'D9 — Example drive', 'note_records': {},
    'child_calendar': 'other', 'calendar_people': {'other': 'Other'},
    'fields': {'stream': SF, 'rhythms': RF},
}


def stamp(day, h, m):
    return f'{day.isoformat()}T{h:02d}:{m:02d}:00.000Z'


STREAM = [{
    'id': 'rec00000001', 'createdTime': stamp(TODAY, 6, 0),
    'cellValuesByFieldId': {
        SF['title']: 'An example action', SF['key']: 'k001',
        SF['status']: '▶️ in motion', SF['practice']: '⚡ action',
        SF['rhythm']: 'D9 — Example drive',
        SF['target']: stamp(TODAY + dt.timedelta(days=1), 12, 0),
    },
}, {
    # the afternoon event's own row, found by its link and nothing else
    'id': 'rec00000002', 'createdTime': stamp(TODAY, 6, 5),
    'cellValuesByFieldId': {
        SF['title']: 'Something unrelated by name', SF['key']: 'k002',
        SF['status']: '⬜ intention', SF['practice']: '⚡ action',
        SF['rhythm']: 'D9 — Example drive',
        SF['event']: 'https://www.google.com/calendar/event?eid=QUZURVJOT09O',
    },
}]

RHYTHMS = [{
    'id': 'rhy00001', 'createdTime': stamp(TODAY, 0, 0),
    'cellValuesByFieldId': {
        RF['name']: 'D9 — Example drive', RF['type']: '♐ drive',
        RF['status']: 'active', RF['emoji']: '🚐',
        RF['dest']: [{'name': 'an example destination'}],
    },
}]

MIDNIGHT = dt.datetime.combine(TODAY, dt.time())


def ev(summary, a, b, allday=False, eid=None):
    """An event in the shape the calendar tool hands back."""
    key = 'date' if allday else 'dateTime'
    fmt = (lambda t: t.date().isoformat()) if allday else (lambda t: t.isoformat())
    e = {'summary': summary, 'start': {key: fmt(a)}, 'end': {key: fmt(b)}}
    if eid:
        e['htmlLink'] = f'https://www.google.com/calendar/event?eid={eid}'
    return e


CAL = {'calendars': [{'who': 'you', 'events': [
    # no row yet, and its glyph names a drive: a row is written for it
    ev('⬜🚐Morning example', MIDNIGHT + dt.timedelta(hours=9, minutes=30),
       MIDNIGHT + dt.timedelta(hours=10, minutes=30), eid='TU9STklORw'),
    ev('Afternoon example', MIDNIGHT + dt.timedelta(hours=14),
       MIDNIGHT + dt.timedelta(hours=15), eid='QUZURVJOT09O'),
    # runs past midnight, so tomorrow names it by the hour it ends
    ev('Overnight example', MIDNIGHT + dt.timedelta(hours=22),
       MIDNIGHT + dt.timedelta(days=1, hours=1)),
    # a multi-day all-day stay, drawn as a band and named on its first day
    ev('Away example', MIDNIGHT + dt.timedelta(days=3),
       MIDNIGHT + dt.timedelta(days=6), allday=True),
]}, {'who': 'other', 'events': [
    # the child's event on top of hers: who has him?
    ev('Child example', MIDNIGHT + dt.timedelta(hours=14, minutes=30),
       MIDNIGHT + dt.timedelta(hours=15, minutes=30)),
]}], 'read': {'window': '14 days', 'you': '4/4', 'other': '1/1'}}


def dump(records):
    return {'records': records, 'metadata': {'totalRecordCount': len(records)}}


def main():
    tmp = tempfile.mkdtemp(prefix='dayahead-')

    def w(name, obj):
        path = os.path.join(tmp, name)
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(obj, fh, ensure_ascii=False)
        return path

    out = os.path.join(tmp, 'page.html')
    r = subprocess.run(
        [sys.executable, BUILDER, '--today', TODAY.isoformat(),
         '--local', w('day_ahead_local.json', LOCAL),
         '--stream', w('w39.json', dump(STREAM)),
         '--rhythms', w('rhythms.json', dump(RHYTHMS)),
         '--calendar', w('cal.json', CAL),
         '--template', ENGINE, '--out', out, '--now', '07:15',
         '--secure', 'secure', '--secure-words', 'an example secure base'],
        capture_output=True, text=True, encoding='utf-8',
        env=dict(os.environ, PYTHONIOENCODING='utf-8'))
    print(r.stdout or '', r.stderr or '')
    if r.returncode:
        sys.exit(f'the builder did not run on this platform (rc={r.returncode})')

    with open(out, encoding='utf-8') as fh:
        html = fh.read()
    D = json.loads(html.split('const DATA=', 1)[1].split(';</script>', 1)[0])

    fails = []

    def check(name, got, want):
        if got != want:
            fails.append(f'{name}\n     got  {got!r}\n     want {want!r}')
        else:
            print(f'  ok   {name}')

    def when_on(n, title):
        return next((e['when'] for e in D['days'][n]['events']
                     if e['title'] == title), None)

    # '%-d' built this
    check('the date drops its leading zero', D['dateLabel'], 'Tuesday 22 September')
    # '%-I:%M' plus the first letter of '%p' built these
    check('a half-hour start', when_on(0, 'Morning example'), '9:30a')
    check('an on-the-hour start', when_on(0, 'Afternoon example'), '2p')
    # '%-I%p' built this
    check('an event ending the next day', when_on(1, 'Overnight example'), 'ends 1am')
    # fmt_day, which was always portable — here so the pair stay consistent
    check('a multi-day stay names its last day',
          when_on(3, 'Away example'), 'through Sun 27 Sep')

    # the look-ahead plan, written beside the page
    P = json.load(open(os.path.join(tmp, 'page.plan.json'), encoding='utf-8'))
    check('one today row, for the event with no row',
          [r['event'] for r in P['today_rows']], ['Morning example'])
    row = P['today_rows'][0]['fields'] if P['today_rows'] else {}
    check('bucketed off the event glyph', row.get(SF['rhythm']), 'D9 — Example drive')
    check('keyed at the write, not the event', row.get(SF['key']), '260922_0715')
    check('targeted at the event', row.get(SF['target']), stamp(TODAY, 9, 30))
    check('carries the event link', row.get(SF['event']),
          'https://www.google.com/calendar/event?eid=TU9STklORw')
    check('the linked event is not rowed again',
          any(r['event'] == 'Afternoon example' for r in P['today_rows'] + P['today_asks']), False)
    check("the child's overlap is named", 'child' in [c['kind'] for c in P['conflicts']], True)

    # the engine declares its encoding, or every glyph above comes back mojibake
    check('engine declares utf-8', '<meta charset="utf-8">' in html, True)

    print()
    if fails:
        print(f'{len(fails)} clock(s) are wrong:')
        for f in fails:
            print('  FAIL ' + f)
        sys.exit(1)
    print(f'the builder runs here and every clock reads right. page: {out}')


if __name__ == '__main__':
    main()
