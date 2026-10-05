# -*- coding: utf-8 -*-
"""What the read filter keeps off the page (5 Oct 2026).

Build work on the system itself is not the next right thing to do, so a row on a
drive named in hide_drives never reaches the page — unless its title names one
of the user's own reviews (hide_keep), which stays. A ⏱️ quickie is offered when
the user has a few minutes, never on this page.

Every name below is an obvious invention.

    python3 tests/test_filter.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import day_ahead as da  # noqa: E402


def row(title, drive='', status='⬜ intention', **kw):
    r = dict(id=title, title=title, rhythm=drive, status=status, practice='⚡ action',
             queue=None, waiting=None)
    r.update(kw)
    return r


def main():
    da.HIDE.update(drives=('Build Drive',), keep=('weekly review', 'month ahead'))
    rows = [row('Wire the new reader', 'Build Drive'),
            row('Weekly review — Sunday', 'Build Drive'),
            row('The month ahead for November', 'Build Drive'),
            row('Call the plumber', 'Home'),
            row('Look up a recipe', 'Home', quickie=True),
            row('Done already', 'Build Drive', status='✅ done')]
    out, dropped = da.filtered_open({r['id']: r for r in rows})
    kept = sorted(r['title'] for r in out)
    want = ['Call the plumber', 'The month ahead for November', 'Weekly review — Sunday']
    assert kept == want, kept
    assert dropped['hidden'] == 1 and dropped['quickie'] == 1, dropped
    # nothing named to hide: nothing hidden
    da.HIDE.update(drives=(), keep=())
    out, dropped = da.filtered_open({r['id']: r for r in rows})
    assert dropped['hidden'] == 0 and len(out) == 4, (dropped, len(out))
    # a practice with a cadence: drawn on its day, done once a row that day carries it,
    # its drive read off the latest row that carried it
    import datetime as dt
    assert da.cadence_days('weekly · Monday') == [0]
    assert da.cadence_days('weekly · Tue, Fri') == [1, 4]
    assert da.cadence_days('monthly') == []
    practices = [dict(name='🌊 river check', cadence='weekly · Monday')]
    mon = dt.date(2026, 10, 5)
    logged = [dict(row('River check — all clear', 'River Drive', status='✅ done'),
                   practice='🌊 river check', when='2026-10-05T13:12:00.000Z', created='2026-10-05T13:12:00.000Z')]
    got = da.standing_steps(practices, logged, mon, 14)
    assert sorted(got) == [mon, dt.date(2026, 10, 12)], sorted(got)
    assert got[mon][0]['st'] == '✅' and got[dt.date(2026, 10, 12)][0]['st'] == '⬜', got
    assert got[mon][0]['every'] == 'Mon' and got[mon][0]['drive'] == 'River Drive', got
    print('ok — hidden drives, their own reviews kept, quickies off the page, cadence')


if __name__ == '__main__':
    main()
