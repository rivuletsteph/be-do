# -*- coding: utf-8 -*-
"""The weekend shapes (25 Oct 2026).

Her words: a Sunday look ahead is fundamentally different from Monday through
Friday; Saturday is also different. Sunday reads the week by day — the peak, the
open days, the clashes, the trips — the way the 6 Sep look ahead did ("Tuesday
is the peak, Thursday has a clash, Monday is open"), with the morning held for
reflection and what has to be ready for Monday. Saturday is fun first, with
tending when there's room. The weekday sections are not drawn on either.

Every name below is an obvious invention.

    python3 tests/test_shape.py
"""
import datetime as dt
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
sys.path.insert(0, HERE)
import day_ahead as da  # noqa: E402
import test_clock as tc  # noqa: E402  the end-to-end fixture

SUN = dt.date(2026, 3, 8)
L = dict(self_calendar='you', child_calendar='Kid', other_calendars=['Kid', 'Pat'],
         work_parents=['Work'], tending=['Home'])


def at(day, h, m=0):
    return dt.datetime.combine(SUN + dt.timedelta(days=day), dt.time(h, m))


def e(who, title, a, b, allday=False, summary=None):
    return dict(who=who, title=title, summary=summary or title, a=a, b=b, allday=allday, occasion=False,
                stay=(b - a) >= dt.timedelta(hours=12), multi=(b - a) >= dt.timedelta(days=2), location='')


def day_list(n=13):
    return [dict(date=(SUN + dt.timedelta(days=i)).isoformat(), label=da.fmt_day(SUN + dt.timedelta(days=i)),
                 events=[], due=[], bands=[]) for i in range(1, n + 1)]


def main():
    assert da.shape_of(SUN) == 'sunday' and da.shape_of(SUN - dt.timedelta(days=1)) == 'saturday'
    assert da.shape_of(SUN + dt.timedelta(days=2)) == 'weekday'
    assert da.shape_of(SUN, 'weekday') == 'weekday', 'the chat can ask for another shape'

    evs = [
        e('you', 'Board meeting', at(2, 9), at(2, 12)),                 # Tue: the peak, 3 h
        e('you', 'Dentist', at(4, 10), at(4, 11)),                       # Thu
        e('Kid', 'Swim lesson', at(4, 10, 30), at(4, 11, 30)),           # Thu: who has Kid?
        e('Kid', 'Park day — Pat drives', at(2, 9), at(2, 13)),          # Tue: Pat has Kid, no clash
        e('you', 'Lake cabin', at(5, 0), at(8, 0), allday=True, summary='❔Lake cabin'),       # Fri: away
        e('you', 'Mail the forms', at(1, 0), at(6, 0), allday=True, summary='⬜📮 Mail the forms'),  # a window
    ]
    conflicts = da.find_conflicts(evs, SUN, 14, L)
    assert [c['date'] for c in conflicts if c['kind'] == 'child'] == [(SUN + dt.timedelta(days=4)).isoformat()], \
        'a child event that names who drives is covered; the other is a question'
    week = da.week_shape(day_list(), evs, conflicts, L)
    tags = {w['day']: w['tags'] for w in week}
    assert tags['Tuesday'] == ['peak'], tags
    assert tags['Monday'] == ['open'] and tags['Wednesday'] == ['open'], 'a weekday with nothing of hers is open'
    assert tags['Thursday'] == ['clash'], tags
    assert tags['Friday'] == ['away'] and tags['Saturday'] == ['away'], 'a stretch away, every day of it'
    assert 'Mail the forms' not in [s for w in week for s in w['starts']], 'a ⬜ window is not a trip'
    assert da.week_lead(week) == 'Monday is open, Tuesday is the peak, Thursday has a clash, Lake cabin starts Friday.', \
        da.week_lead(week)
    assert da.week_lead(da.week_shape(day_list()[5:6], [], [], L)) == 'A quiet week ahead.'

    # what has to be ready as the week opens: due Mon–Tue, never a calendar event's own row
    def row(rid, title, day, key=None, drive='Home', status='⬜ intention'):
        t = (at(day, 17) - da.UTC_OFFSET).strftime('%Y-%m-%dT%H:%M:00.000Z') if day is not None else None
        return dict(id=rid, key=key or rid, title=title, target=t, rhythm=drive, status=status)
    rows = [row('a', 'Pack the swim bag', 1), row('b', 'Print the agenda', 2, key='k-board'),
            row('c', 'Order the cake', 3), row('d', 'Return the library books', 1)]
    got = [r['id'] for r in da.ready_rows(rows, SUN, {'d', 'k-board'})]
    assert got == ['a'], 'matched by record id or by key; Wednesday is past the horizon'

    # Saturday's tending: under a tending rhythm, never under work; late, then this week, then moving
    da.DRIVES.clear()
    da.DRIVES.update({'Home': dict(name='Home'), 'Garden': dict(name='Garden', parent='Home'),
                      'Work': dict(name='Work'), 'Fun': dict(name='Fun')})
    sat = SUN - dt.timedelta(days=1)
    rows = [row('t1', 'Fix the gate', 3, drive='Garden'), row('t2', 'Clean the gutters', -3),
            row('t3', 'File the expense report', -3, drive='Work'), row('t4', 'Paint the shed', None, status='▶️ in motion'),
            row('t5', 'Someday: a greenhouse', None, drive='Garden'), row('t6', 'Kayak day', 1, drive='Fun')]
    assert [r['id'] for r in da.tending_rows(rows, sat, L)] == ['t2', 't1', 't4'], \
        [r['id'] for r in da.tending_rows(rows, sat, L)]
    assert da.tending_rows(rows, sat, dict(L, tending=[])) == [], 'no tending named, no section'

    # the morning: reflection until noon, and anything that would cut into it
    m = da.sunday_morning([e('you', 'Brunch', at(0, 10), at(0, 11))], {SUN: [dict(title='reflection')]}, SUN, {})
    assert m['what'] == 'reflection' and m['until'] == '12:00pm', m
    assert [x['title'] for x in m['early']] == ['Brunch'] and m['steps'] == [dict(title='reflection')]

    # end to end: the same fixture as the clock test, built in each shape
    tmp = tempfile.mkdtemp(prefix='dayahead-shape-')

    def w(name, obj):
        path = os.path.join(tmp, name)
        with open(path, 'w', encoding='utf-8') as fh:
            json.dump(obj, fh, ensure_ascii=False)
        return path
    args = ['--today', tc.TODAY.isoformat(), '--local', w('local.json', tc.LOCAL),
            '--stream', w('w39.json', tc.dump(tc.STREAM)), '--rhythms', w('rhythms.json', tc.dump(tc.RHYTHMS)),
            '--calendar', w('cal.json', tc.CAL), '--template', tc.ENGINE, '--now', '07:15']
    for shape in ('sunday', 'saturday', 'weekday'):
        out = os.path.join(tmp, f'{shape}.html')
        r = subprocess.run([sys.executable, tc.BUILDER, *args, '--out', out, '--shape', shape],
                           capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        assert r.returncode == 0, r.stderr
        html = open(out, encoding='utf-8').read()
        D = json.loads(html.split('const DATA=', 1)[1].split(';</script>', 1)[0])
        assert D['shape'] == shape, D['shape']
        assert D['chore'] and D['chore']['text'], D.get('chore')     # one chore for her son, every shape (11 Oct)
        assert (D['week'] is not None) == (shape == 'sunday') and (D['morning'] is not None) == (shape == 'sunday')
        assert (D['tending'] is not None) == (shape == 'saturday')
        if shape == 'sunday':
            assert len(D['week']) == 6 and D['lead'] == da.week_lead(D['week']), (len(D['week']), D['lead'])
        if shape == 'saturday':
            assert D['lead'] == 'Fun first; the calendar comes after.', D['lead']
    print('ok — Sunday reads the week by day, the morning is held, ready-for-Monday, Saturday tends, weekdays unchanged')


if __name__ == '__main__':
    main()
