# -*- coding: utf-8 -*-
"""A finished day's my day page (14 Nov 2026).

- Its top list is what she did: the actions closed ✅ that day and her ⭐ highlight, in time order, never be•do's
  recommendations (her words: no reason to do this; the thing I accomplished was teaching and starting the trip).
- A highlight logged during the day keeps its own card at its own time; only one told at night is matched to the
  earlier card it names (her words: these need to be integrated into the stream with the correct times and pictures).
- The day in six is retired: the stream holds the moments.
- Sleep on the time-went line is the night she slept, from her ring, never two nights in bed added by the clock.

Every name below is an obvious invention.

    python3 tests/test_finished_day.py
"""
import datetime as dt
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'scripts'))
import flow  # noqa: E402

F = dict(status='s', practice='p', when='w', title='t', details='d', rhythm='r')


class Off:
    """A fixed UTC−6, enough for a test."""
    def __radd__(self, other):
        return other - dt.timedelta(hours=6)


def rec(rid, when, practice, title, status='◉ done', details='', rhythm=''):
    return dict(id=rid, cellValuesByFieldId=dict(w=when, p=practice, t=title, s=status, d=details, r=rhythm))


def test_did_of():
    rows = [
        rec('a', '2026-03-13T16:00:00.000Z', '⚡ action', '⚡ Lead the pond walk', '✅ done', 'We found frogs.\n———\n[be•do] …', 'Home'),
        rec('b', '2026-03-13T17:13:00.000Z', '⭐ highlight', '⭐ the kids on the hay bales', '◉ done', 'It was beautiful.'),
        rec('c', '2026-03-13T18:00:00.000Z', '⚡ action', '⚡ Paint the shed door', '▶️ in motion'),      # not closed
        rec('d', '2026-03-12T18:00:00.000Z', '⚡ action', '⚡ Post the form', '✅ done'),                 # another day
        rec('e', '2026-03-13T19:00:00.000Z', '☕ coffee', '☕ coffee'),                                   # a flow step
    ]
    did = flow.did_of(rows, F, Off(), dt.date(2026, 3, 13))
    assert [x['t'] for x in did] == ['Lead the pond walk', 'the kids on the hay bales'], did
    assert did[0]['why'] == 'We found frogs.' and did[0]['drive'] == 'Home'
    assert did[1]['g'] == '⭐' and all(x['st'] == '✅' for x in did)


def test_night_of():
    rows = [
        rec('n1', '2026-03-13T05:02:00.000Z', '😴 sleep', '😴 sleep, night before Fri', details='———\n[be•do] From the ring: in bed 11:02 PM to 7:08 AM, 8 h 06; 7 h 26 asleep, efficiency 92%.'),
        rec('n2', '2026-03-14T03:12:00.000Z', '😴 sleep', '😴 sleep, night before Sat', details='7 h 50 asleep'),   # tonight
    ]
    rows[0]['cellValuesByFieldId']['e'] = '2026-03-13T13:08:00.000Z'
    rows[1]['cellValuesByFieldId']['e'] = '2026-03-14T12:48:00.000Z'
    G = dict(F, end='e')
    n = flow.night_of(rows, G, Off(), dt.date(2026, 3, 13))
    assert n['asleep'] == 7 * 60 + 26 and n['label'] == 'Thu night', n


def card(t, a, b, k='lived', **kw):
    return dict(k=k, t=t, a=a, b=b, **kw)


def test_highlight_keeps_its_time():
    items = [
        card('🚗 to the park with the kids', '09:33', '10:00'),
        card('🌳 the park', '10:00', '14:28', k='event', summary='the park'),
        card('🌟 Kit: hide and seek at the park', '11:13', '11:23'),     # logged during the day: stays
        card('🌟 Kit: the park was the best', '21:00', '21:10'),          # told at night: matched to its card
    ]
    out = flow.star_the_highlight(items)
    day = next(x for x in out if 'hide and seek' in x['t'])
    assert (day['a'], day['b']) == ('11:13', '11:23'), day
    night = next(x for x in out if 'the best' in x['t'])
    assert night['a'] != '21:00' and night.get('told') == '21:00', night


def test_engine():
    page = open(os.path.join(os.path.dirname(HERE), 'assets', 'flow_engine.html'), encoding='utf-8').read()
    assert 'what you did' in page and "over3&&!D.picked?(D.did||[])" in page
    assert ".three li.did:before" in page and "class=\"${over3?'did'" in page   # checked, fully bright
    assert "asleep · ${esc(NG.label)}" in page   # the night she slept, never two nights in bed
    assert 'const SIX=[];' in page     # the day in six is retired
    assert "const ids=over?['three','today'" in page   # a finished day leads with what she did


def main():
    test_did_of()
    test_highlight_keeps_its_time()
    test_night_of()
    test_engine()
    print('ok — a finished day: what she did, moments in the stream at their own time')


if __name__ == '__main__':
    main()
