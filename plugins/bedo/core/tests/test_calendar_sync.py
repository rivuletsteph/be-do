# -*- coding: utf-8 -*-
"""Drive calendar_sync.py over a small fixture and check the plan it prints.

Every name below is an obvious invention.

    python3 tests/test_calendar_sync.py
"""
import base64, datetime as dt, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SYNC = os.path.join(os.path.dirname(HERE), 'calendar_sync.py')

SF = dict(title='fldTitle', key='fldKey', when='fldWhen', end='fldEnd', target='fldTarget',
          status='fldStatus', event='fldEvent', spent='fldSpent')
LOCAL = {'utc_offset_hours': -5, 'fields': {'stream': SF},
         'calendar_summaries': {'you': 'mine', 'kid': 'kid'}, 'sync_calendars': ['you', 'kid'],
         'dropped_calendar': 'dropped'}
CALS = {'calendars': [{'id': 'me@gmail.com', 'summary': 'mine'},
                      {'id': 'fam@group.calendar.google.com', 'summary': 'kid'},
                      {'id': 'other@example.com', 'summary': 'someone else'},
                      {'id': 'gone@group.calendar.google.com', 'summary': 'dropped'}]}


def link(ev, cal_short):
    raw = base64.urlsafe_b64encode(f'{ev} {cal_short}'.encode()).decode().rstrip('=')
    return f'https://www.google.com/calendar/event?eid={raw}'


def row(i, key, status, when, event, end=None, target=None, spent=None):
    c = {SF['title']: f'row {i}', SF['key']: key, SF['status']: status,
         SF['when']: when, SF['event']: event}
    if end: c[SF['end']] = end
    if target: c[SF['target']] = target
    if spent: c[SF['spent']] = spent
    return {'id': f'rec{i:014d}', 'createdTime': when, 'cellValuesByFieldId': c}


def ev(cal, eid, summary, a, b, mine=True):
    return {'calendarId': cal, 'id': eid, 'summary': summary, 'organizer': {'self': mine},
            'start': {'dateTime': a, 'timeZone': 'America/Chicago'},
            'end': {'dateTime': b, 'timeZone': 'America/Chicago'}}


STREAM = [
    # its own row, done, ran 9:00–9:45 against a 9–10 booking: prefix and times move
    row(1, 'a', '✅ done', '2026-09-23T14:00:00.000Z', link('ev1', 'me@m'), end='2026-09-23T14:45:00.000Z'),
    # its own row, dropped: prefix only
    row(2, 'b', '✖️ dropped', '2026-09-23T16:00:00.000Z', link('ev2', 'me@m')),
    # a row ABOUT a later event (rescheduling it): the event is left alone
    row(3, 'c', '✅ done', '2026-09-23T18:00:00.000Z', link('ev3', 'fam@g'), target='2026-09-25T17:00:00.000Z'),
    # done with a time spent and already matching: nothing to do
    row(4, 'd', '✅ done', '2026-09-23T20:00:00.000Z', link('ev4', 'me@m'), spent=3600),
    # dropped, and the user already moved its event to the dropped calendar
    row(5, 'e', '✖️ dropped', '2026-09-23T22:00:00.000Z', link('ev5', 'me@m')),
]
EVENTS = [
    ev('me@gmail.com', 'ev1', '⬜🏭Example check-in', '2026-09-23T09:00:00-05:00', '2026-09-23T10:00:00-05:00'),
    ev('me@gmail.com', 'ev2', 'Example lunch', '2026-09-23T11:00:00-05:00', '2026-09-23T12:00:00-05:00'),
    ev('fam@group.calendar.google.com', 'ev3', 'Example appointment', '2026-09-30T14:00:00-05:00', '2026-09-30T15:00:00-05:00'),
    ev('me@gmail.com', 'ev4', '✔️ Example session', '2026-09-23T15:00:00-05:00', '2026-09-23T16:00:00-05:00'),
    ev('gone@group.calendar.google.com', 'ev5', '✖️Example outing', '2026-09-23T17:00:00-05:00', '2026-09-23T18:00:00-05:00'),
]


def main():
    tmp = tempfile.mkdtemp(prefix='calsync-')

    def w(name, obj):
        p = os.path.join(tmp, name)
        json.dump(obj, open(p, 'w', encoding='utf-8'), ensure_ascii=False)
        return p

    args = ['--day', '2026-09-23', '--local', w('local.json', LOCAL),
            '--stream', w('w.json', {'records': STREAM, 'metadata': {'totalRecordCount': len(STREAM)}})]
    env = dict(os.environ, PYTHONIOENCODING='utf-8')
    lst = subprocess.run([sys.executable, SYNC, '--list'] + args, capture_output=True, text=True, encoding='utf-8', env=env)
    plan = subprocess.run([sys.executable, SYNC, '--plan'] + args + ['--events', w('e.json', EVENTS),
                          '--calendars', w('c.json', CALS)], capture_output=True, text=True, encoding='utf-8', env=env)
    if lst.returncode or plan.returncode:
        sys.exit(lst.stderr + plan.stderr)
    L, P = json.loads(lst.stdout), json.loads(plan.stdout)
    fails = []

    def check(name, got, want):
        (fails.append(f'{name}\n     got  {got!r}\n     want {want!r}') if got != want else print(f'  ok   {name}'))

    check('the link decodes to event and calendar',
          [(f['event_id'], f['calendar_id']) for f in L['fetch']][:3],
          [('ev1', 'me@gmail.com'), ('ev2', 'me@gmail.com'), ('ev3', 'fam@group.calendar.google.com')])
    ch = {c['key']: c['update'] for c in P['changes']}
    check('done takes ✔️, the plain check, in place of ⬜ (4 Nov 2026)', ch.get('a', {}).get('summary'), '✔️🏭Example check-in')
    check('its real times follow the row', (ch.get('a', {}).get('startTime'), ch.get('a', {}).get('endTime')),
          ('2026-09-23T09:00', '2026-09-23T09:45'))
    check('notifications are off', ch.get('a', {}).get('notificationLevel'), 'NONE')
    check('dropped takes ✖️ and keeps its times', (ch.get('b', {}).get('summary'), 'startTime' in ch.get('b', {})),
          ('✖️Example lunch', False))
    check('a row about an event does not move it', 'c' in ch, False)
    check('a matching event is left alone', 'd' in ch, False)
    check('a dropped event still on a synced calendar is listed to move', [m['key'] for m in P.get('to_move', [])], ['b'])
    check('one already on the dropped calendar is recognised, not called deleted',
          [u['why'] for u in P['unchanged'] if u['row'] == 'row 5'], ['already on dropped'])
    # the live read (11 Nov 2026): the checks' own settings name the fields, and the rows arrive
    # already in hand, in the API's shape (`fields`), as two reads: the day, and the week's linked rows
    sys.path.insert(0, os.path.dirname(HERE))
    import calendar_sync as CS
    import bedo_clock
    facts = {'stream_fields': dict(title='fldTitle', key='fldKey', datetime='fldWhen', end='fldEnd', target='fldTarget',
                                   status='fldStatus', calendar_event='fldEvent', time_spent='fldSpent')}
    check("the checks' settings map onto this file's field names", CS.fields_from_facts(facts), SF)
    try:
        CS.fields_from_facts({'stream_fields': {'title': 'fldTitle'}})
        check('a settings file with no event field stops the run', 'ran', 'stopped')
    except SystemExit as e:
        check('a settings file with no event field stops the run', 'calendar_event' in str(e), True)
    api = [dict(id=r['id'], createdTime=r['createdTime'], fields=r['cellValuesByFieldId']) for r in STREAM]
    day_read = {'records': api[:1], 'metadata': {'totalRecordCount': 1}}
    linked_read = {'records': api, 'metadata': {'totalRecordCount': len(api)}}     # the day's row comes twice
    off = bedo_clock.Offset({'utc_offset_hours': -5})
    live = CS.linked_for_day(CS.load([day_read, linked_read], SF, off), dt.date(2026, 9, 23), off)
    files = CS.linked_for_day(CS.load([w('again.json', {'records': STREAM,
                                                        'metadata': {'totalRecordCount': len(STREAM)}})], SF, off),
                              dt.date(2026, 9, 23), off)
    check('rows in hand, in the API shape, plan the same day as the file read',
          sorted(r['key'] for r in live), sorted(r['key'] for r in files))
    check('and a row read twice is one row', len(live), len({r['id'] for r in live}))
    print()
    if fails:
        print(f'{len(fails)} failed:'); [print('  FAIL ' + f) for f in fails]; sys.exit(1)
    print('the sync plans what it should, and nothing else.')


if __name__ == '__main__':
    main()
