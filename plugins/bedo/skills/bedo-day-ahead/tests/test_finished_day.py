# -*- coding: utf-8 -*-
"""A finished day's my day page (14 Nov 2026).

- Its top list is what she did: the actions closed ✅ that day and her ⭐ highlight, in time order, never be•do's
  recommendations (her words: no reason to do this; the thing I accomplished was teaching and starting the trip).
- A highlight logged during the day keeps its own card at its own time; only one told at night is matched to the
  earlier card it names (her words: these need to be integrated into the stream with the correct times and pictures).
- The day in six is retired: the stream holds the moments.

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


def test_picks_are_not_done():
    """A recommended pick never counts as done on its own (18 Nov 2026, her words: number two and three did not happen on
    the what you did, so there needs to be a better check there). The picks passed to a finished day's build are be•do's
    three; what you did is only what the record shows closed that day."""
    rows = [
        rec('a', '2026-03-13T16:00:00.000Z', '⚡ action', '⚡ Lead the pond walk', '✅ done'),
        rec('p', '2026-03-01T16:00:00.000Z', '⚡ action', '⚡ Ask the clinic about the form', '⬜ intention'),   # a pick, still open
        rec('q', '2026-03-13T15:00:00.000Z', '⚡ action', '⚡ Send the grant list', '⬜ intention'),             # a pick, today, open
    ]
    did = flow.did_of(rows, F, Off(), dt.date(2026, 3, 13))
    assert [x['t'] for x in did] == ['Lead the pond walk'], did


def test_system_work_is_one_line():
    """The system's own work folds into one line (18 Nov 2026, her words: I did the weekly close, Claude handled the details)."""
    rows = [
        rec('a', '2026-03-13T14:00:00.000Z', '⚡ action', '⚡ Chat sweep: two branches archived', '✅ done', '', 'Sysdrive'),
        rec('b', '2026-03-13T15:00:00.000Z', '⚡ action', '⚡ Swept 40 chats; w11 cloned', '✅ done', '', 'Sysdrive'),
        rec('c', '2026-03-13T16:00:00.000Z', '⚡ action', '⚡ Lead the pond walk', '✅ done', '', 'Home'),
    ]
    did = flow.did_of(rows, F, Off(), dt.date(2026, 3, 13), hidden={'Sysdrive'})
    assert [x['t'] for x in did] == ['the weekly close, Claude handled the details', 'Lead the pond walk'], did
    assert 'Swept 40 chats' in did[0]['why'], did[0]
    assert len(flow.did_of(rows, F, Off(), dt.date(2026, 3, 13))) == 3   # no hidden drives, nothing folds


def test_the_day_links_its_own_quest():
    """Each day's quest page is its own, linked from that day's page (18 Nov 2026)."""
    G = dict(F, deliverable='v')
    rows = [dict(id='q', cellValuesByFieldId=dict(w='2026-03-14T03:30:00.000Z', p='⚔️ the quest', t='⚔️ the quest — 5 of 10',
                                               s='◉ done', v='https://example.org/quest/day-13')),
            dict(id='o', cellValuesByFieldId=dict(w='2026-03-15T03:30:00.000Z', p='⚔️ the quest', t='⚔️ the quest — 7 of 10',
                                               s='◉ done', v='https://example.org/quest/day-14'))]
    own = flow.day_quest_url(rows, G, Off(), dt.date(2026, 3, 13))
    assert own == 'https://example.org/quest/day-13', own
    sched = [dict(k='lived', t='⚔️ the quest — 5 of 10')]
    assert flow.quest_link({'quest_url': 'https://example.org/quest/shared'}, sched, own)['u'] == own
    assert flow.quest_link({'quest_url': 'https://example.org/quest/shared'}, sched)['u'].endswith('shared')
    assert flow.day_quest_url(rows, F, Off(), dt.date(2026, 3, 13)) is None   # no deliverable field, no link


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
    assert 'what you did' in page and "const T=over3?(D.did||[]):(D.three||[]);" in page
    assert 'D.picked' not in page      # a finished day's list never takes be•do's picks as done (18 Nov 2026)
    assert ".three li.did:before" in page and "class=\"${over3?'did'" in page   # checked, fully bright
    assert 'const SIX=[];' in page     # the day in six is retired
    assert "const ids=over?['three','today'" in page   # a finished day leads with what she did


def main():
    test_did_of()
    test_picks_are_not_done()
    test_system_work_is_one_line()
    test_the_day_links_its_own_quest()
    test_highlight_keeps_its_time()
    test_engine()
    print('ok — a finished day: what she did, moments in the stream at their own time')


if __name__ == '__main__':
    main()
