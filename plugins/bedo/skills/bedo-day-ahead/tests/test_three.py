# -*- coding: utf-8 -*-
"""be•do's three — the Pareto three (J9, 9 Oct 2026).

From uncalendared work, deduped by subject, in the order of pull: someone
waiting · target passed · in motion · named as weighing. A row that is a
calendar event's own is never picked, and two asks from the same person read
as one thing, so one person fills one slot.

Every name below is an obvious invention.

    python3 tests/test_three.py
"""
import datetime as dt
import os, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import day_ahead as da  # noqa: E402

TODAY = dt.date(2026, 3, 11)
L = dict(self_person='Me', weighing_phrases=['on my mind'], task_horizon_days=7)


def row(rid, title, target=None, person='', status='⬜ intention', drive='Home', details=''):
    return dict(id=rid, key=rid, title=title, rhythm=drive, status=status, person=person,
                target=f'{target}T17:00:00.000Z' if target else None, details=details)


def main():
    rows = [
        row('a', 'Mend the gate latch for Pat', '2026-03-11', person='Pat'),
        row('b', 'Lend Pat the ladder', '2026-03-12', person='Pat'),          # same person: next in line
        row('c', 'Text Sam about the boat', '2026-03-11', person='Sam'),      # a calendar event's own
        row('d', 'Post the quarterly form', '2026-03-09', drive='Paperwork'), # target passed
        row('e', 'Paint the shed door', '2026-03-13', status='▶️ in motion', drive='Garden'),
    ]
    chains = defaultdict(list, {r['key']: [dict(details=r['details'], created='2026-03-10')] for r in rows})
    rhythms = {'Home': dict(name='Home'), 'Paperwork': dict(name='Paperwork'), 'Garden': dict(name='Garden')}
    picks, nxt, more = da.pareto(rows, chains, rhythms, TODAY, L, calendared={'c'})
    got = [(p['kind'], p['row']['id']) for p in picks]
    assert got == [('someone waiting', 'a'), ('target passed', 'd'), ('in motion', 'e')], got
    assert all(p['row']['id'] != 'c' for p in picks), 'a calendar event never needs recommending'
    assert {'kind': 'someone waiting', 'title': 'Lend Pat the ladder'} in nxt, nxt
    assert 'd' not in [m['id'] for m in more], 'a row past its date has its own section'
    assert 'c' not in [m['id'] for m in more], more
    # with only one kind on offer, its slots still fill to three (one per person waiting,
    # at most two from one drive)
    only = [row('p', 'Call Ann back', '2026-03-11', person='Ann'),
            row('q', 'Send Bo the photos', '2026-03-12', person='Bo', drive='Garden'),
            row('r', 'Return Cy the drill', '2026-03-13', person='Cy', drive='Paperwork')]
    ch = defaultdict(list, {r['key']: [] for r in only})
    picks, _, _ = da.pareto(only, ch, rhythms, TODAY, L)
    assert len(picks) == 3, picks
    print('ok — four kinds in the order of pull, calendar events left out, one slot per person waiting')


if __name__ == '__main__':
    main()
