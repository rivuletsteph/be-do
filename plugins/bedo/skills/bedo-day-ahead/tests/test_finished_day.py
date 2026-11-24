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
    assert [x['t'] for x in did] == ['the kids on the hay bales', 'Lead the pond walk'], did   # her highlight leads
    assert did[1]['why'] == 'We found frogs.' and did[1]['drive'] == 'Home'
    assert did[0]['g'] == '⭐' and all(x['st'] == '✅' for x in did)


def test_meaning_leads():
    """The list is ranked by what was meaningful (23 Nov 2026, her words: the memorable things are, where was I with
    my family): her highlights, then time with her people, then her work, then the system's line."""
    FP = dict(F, person='who', emotion='e', photo='ph')
    def row(rid, when, practice, title, status='● log', rhythm='', who='', e='', ph='', details=''):
        return dict(id=rid, cellValuesByFieldId=dict(w=when, p=practice, t=title, s=status, d=details, r=rhythm, who=who, e=e, ph=ph))
    rows = [
        row('a', '2026-03-13T14:00:00.000Z', '⚡ action', '⚡ Rebuilt the page', '✅ done', 'Sysdrive'),
        row('b', '2026-03-13T15:00:00.000Z', '⚡ action', '⚡ Post the form', '✅ done', 'Home'),
        row('c', '2026-03-13T16:00:00.000Z', '🌿 fresh air', 'Trampoline with Pip', who='♑Pip Plum, Me', details='[be•do] From 2 photos.'),
        row('d', '2026-03-13T17:00:00.000Z', '📝 log', '📝 sitting, unlogged (estimated)', who='Pip Plum'),      # a filler
        row('e', '2026-03-13T18:00:00.000Z', '☕ coffee', 'Coffee with Pip', '◉ done', who='Pip Plum'),          # a flow step
        row('f', '2026-03-13T19:00:00.000Z', '🍽️ dinner', 'Soup', who='Pip Plum'),                               # names no one
        row('g', '2026-03-13T20:00:00.000Z', '⭐ highlight', '⭐ soup night', '◉ done'),
        row('h', '2026-03-13T20:02:00.000Z', '🍽️ dinner', 'Family dinner', who='Pip Plum'),                      # the highlight's own
        row('i', '2026-03-13T21:00:00.000Z', '🎥 movie', 'A quiet film', who='Me', ph='keeper'),                 # kept a photo
    ]
    did = flow.did_of(rows, FP, Off(), dt.date(2026, 3, 13), hidden={'Sysdrive'}, me='Me', flows=frozenset({'coffee'}))
    assert [x['kind'] for x in did] == ['highlight', 'heart', 'heart', 'action', 'system'], did
    assert [x['t'] for x in did][:4] == ['soup night', 'Trampoline with Pip', 'A quiet film', 'Post the form'], did
    assert did[1]['why'] == '' and did[-1]['why'] == '1 piece of upkeep', did
    many = rows + [row(f'm{i}', f'2026-03-13T2{i % 3}:1{i}:00.000Z', '🌿 fresh air', f'Outside with Pip {i}', who='Pip Plum') for i in range(9)]
    many += [row(f'k{i}', f'2026-03-13T13:0{i}:00.000Z', '⚡ action', f'⚡ Errand {i}', '✅ done', 'Home') for i in range(6)]
    did = flow.did_of(many, FP, Off(), dt.date(2026, 3, 13), hidden={'Sysdrive'}, me='Me', flows=frozenset({'coffee'}))
    kinds = [x['kind'] for x in did]
    assert kinds.count('highlight') + kinds.count('heart') == flow.DID_HEART_CAP and len(did) == flow.DID_CAP + 1, kinds


def test_a_moment_marked_meaningful_leads():
    """A moment be•do marked as meaningful, from her own words, leads with her highlights, whatever its kind; a kind
    alone never does, and she never has to say so (23 Nov 2026, her words: I didn't want to actually have to say a moment
    was meaningful, I want the system to figure that out)."""
    said = 'I got it wrong, and we talked it through.\n\nWhat I took home.\n———\n[be•do] Said the next morning.\n[be•do] meaningful: her take-home, what I took home'
    rows = [
        rec('a', '2026-03-13T15:00:00.000Z', '⭐ highlight', '⭐ soup night', '◉ done'),
        rec('b', '2026-03-13T16:00:00.000Z', '⚡ action', '⚡ Post the form', '✅ done', '', 'Home'),
        rec('c', '2026-03-13T17:00:00.000Z', '💡 insight', '💡 insight · a quiet thought', '● log', 'Just a thought.\n———\n[be•do] logged.'),
        rec('d', '2026-03-13T23:00:00.000Z', '💡 insight', '💡 insight · a miss to learn from', '● log', said),
        rec('e', '2026-03-13T23:30:00.000Z', '📒 journal', 'What mattered', '● log', 'meaningful: my own word, not the mark'),   # her words, no block
        rec('f', '2026-03-13T23:40:00.000Z', '⚡ action', '⚡ Call the school', '⬜ intention', '———\nmeaningful: named'),       # never happened
    ]
    did = flow.did_of(rows, F, Off(), dt.date(2026, 3, 13))
    assert [(x['kind'], x['t']) for x in did] == [('highlight', 'soup night'), ('meaningful', '💡 insight · a miss to learn from'),
                                                  ('action', 'Post the form')], did
    assert did[1]['g'] == '' and did[1]['why'] == 'I got it wrong, and we talked it through.', did[1]   # its own glyph, her words
    c = lambda i: rows[i]['cellValuesByFieldId']
    assert flow.marked_meaningful(c(3), F) and not flow.marked_meaningful(c(2), F) and not flow.marked_meaningful(c(4), F)
    # it is never crowded out: marked moments sit above the cap, like her highlights
    FP = dict(F, person='who')
    many = [dict(id=f'm{i}', cellValuesByFieldId=dict(w=f'2026-03-13T1{i}:10:00.000Z', p='🌿 fresh air', t=f'Outside with Pip {i}',
                                                      s='● log', d='', r='', who='Pip Plum')) for i in range(9)]
    did = flow.did_of(many + rows, FP, Off(), dt.date(2026, 3, 13))
    assert [x['kind'] for x in did][:2] == ['highlight', 'meaningful'], did
    assert sum(x['kind'] in ('highlight', 'meaningful', 'heart') for x in did) == flow.DID_HEART_CAP, did
    # on the timeline it is gold, and the engine scores it with her highlights
    eng = open(os.path.join(os.path.dirname(HERE), 'assets', 'flow_engine.html'), encoding='utf-8').read()
    assert 'x.star||x.meant' in eng


def test_system_work_is_one_line():
    """The system's own work folds into one line (18 Nov 2026, her words: I did the weekly close, Claude handled the details)."""
    rows = [
        rec('a', '2026-03-13T14:00:00.000Z', '⚡ action', '⚡ Chat sweep: two branches archived', '✅ done', '', 'Sysdrive'),
        rec('b', '2026-03-13T15:00:00.000Z', '⚡ action', '⚡ Swept 40 chats; w11 cloned', '✅ done', '', 'Sysdrive'),
        rec('c', '2026-03-13T16:00:00.000Z', '⚡ action', '⚡ Lead the pond walk', '✅ done', '', 'Home'),
    ]
    did = flow.did_of(rows, F, Off(), dt.date(2026, 3, 13), hidden={'Sysdrive'})
    # last, and a count: its little things are not the day (23 Nov 2026)
    assert [x['t'] for x in did] == ['Lead the pond walk', 'the weekly close, Claude handled the details'], did
    assert did[1]['why'] == '2 pieces of upkeep' and 'Swept 40 chats; w11 cloned' in did[1]['covers'], did[1]
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


def test_summary_line():
    """A finished day's top is one line (24 Nov 2026, her words through Duet: one line summarizing the day's important,
    meaningful things): her highlights in her words, then who she was with, then her work as a count, upkeep never."""
    did = [dict(t='soup night', kind='highlight', who=['Pip']), dict(t='Trampoline with Pip', kind='heart', who=['Pip']),
           dict(t='A quiet film', kind='heart', who=['Ada']), dict(t='Post the form', kind='action'),
           dict(t='be•do work, Claude handled the details', kind='system')]
    # her highlight in her words, then who she was with by name, then her work as a count; a moment is never "done"
    assert flow.summary_of(did) == 'Soup night · time with Pip and Ada · 1 thing done', flow.summary_of(did)
    # no highlight: two moments with her people stand in for it
    few = [dict(t='the pond walk', kind='heart'), dict(t='a call home.', kind='heart', who=['Ada']),
           dict(t='lunch out', kind='heart'), dict(t='Post the form', kind='action'), dict(t='Paint the door', kind='action')]
    assert flow.summary_of(few) == 'The pond walk and a call home · time with Ada · 2 things done', flow.summary_of(few)
    # only work: named when it is a thing or two
    work = [dict(t='Post the form', kind='action'), dict(t='Paint the door.', kind='action')]
    assert flow.summary_of(work) == 'Post the form and Paint the door', flow.summary_of(work)
    many = [dict(t=f'moment {i}', kind='heart', who=['Pip']) for i in range(6)]
    assert flow.summary_of(many) == 'Moment 0 and moment 1 · time with Pip', flow.summary_of(many)
    assert flow.summary_of([dict(t='be•do work', kind='system')]) == ''
    assert flow.summary_of([]) == ''


def test_engine():
    page = open(os.path.join(os.path.dirname(HERE), 'assets', 'flow_engine.html'), encoding='utf-8').read()
    # a finished day opens on one line, never a list (24 Nov 2026)
    assert "if(over3&&!D.picked){ el.innerHTML=D.summary?" in page and 'class="sumline"' in page
    # its meaningful moments are drawn on the timeline, larger, with her words and photos, never folded (24 Nov 2026)
    assert "const MOM=window.__mom=new Set(gone?[...sixOf(pastAll)" in page
    assert "const big=x=>(window.__mom&&window.__mom.has(x))||" in page
    assert "need=x=>MOM.has(x)?((x.photos||[]).length?170:92)" in page
    # every photo, named feeling, glimmer or highlight is a moment too, not only what the ranking keeps (Mon 23 Nov's lunch)
    assert "&&(x.star||x.meant||x.mom||x.felt||x.keeper||(x.photos||[]).length||" in page
    assert "[...sixOf(pastAll),...pastAll.filter(momOwn)]" in page
    # a moment inside a combined card keeps its whole title and her words
    assert "mom:MOM.has(o),her:o.her" in page and "class=\"ln${m.mom?' mln':''}\"" in page
    assert page.count('${momBody(x)}') == 2 and '.cal .ev.meantc .mph img' in page
    assert 'const SIX=[];' in page     # the day in six is retired
    assert "const ids=over?['three','today'" in page   # a finished day leads with what she did


def main():
    test_did_of()
    test_a_moment_marked_meaningful_leads()
    test_meaning_leads()
    test_system_work_is_one_line()
    test_the_day_links_its_own_quest()
    test_highlight_keeps_its_time()
    test_summary_line()
    test_engine()
    print('ok — a finished day: one summary line, moments in the stream at their own time')


if __name__ == '__main__':
    main()
