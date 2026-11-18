# -*- coding: utf-8 -*-
"""A journal on the my day page (18 Nov 2026): its highlights, her whole words, and the moment it is the download of.

Her words: I just really want to have a list of highlights from the journal entry, and then click on it and have the
whole entry pop up and be readable; it'd be nice if it was clearly linked to the coffee, because it's kind of the
download of that. Every name below is an obvious invention.

    python3 tests/test_journal.py
"""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import flow  # noqa: E402

F = dict(details='d', emotion='em', person='p', practice='pr', device='dv')
IDA, IDJ, IDK, IDZ = ('rec' + c * 14 for c in 'AJKZ')   # invented, built so no id sits in the source
LONG = ('That was a really good talk with Wren. ' * 40).strip()
J = ('She gets me.\nThe follow-through is my struggle. And more.\n' + LONG +
     '\n———\n[be•do] From her voice note.\nmoment: ' + IDA + '\n· She gets me.\n· The follow-through is my struggle.')


def main():
    o = flow.opens_to({'d': J, 'pr': '📒 journal'}, F)
    assert o['her'].endswith(LONG), 'her words are whole, never cut at 700'
    assert len(o['her']) > 700
    assert o['pts'] == ['She gets me.', 'The follow-through is my struggle.'], o['pts']
    assert o['moment'] == IDA and o['jr']

    # an older journal with no key-points block: the first sentence of each paragraph stands in
    old = flow.opens_to({'d': 'The cup broke this morning. I can try the warranty.\nA worry about the dog. I let it go.',
                         'pr': '📒 journal'}, F)
    assert old['pts'] == ['The cup broke this morning.', 'A worry about the dog.'], old['pts']
    assert old['moment'] is None

    # bullets on a row that is not a journal are its notes, not highlights
    assert flow.opens_to({'d': 'met up\n———\n[be•do] notes\n· a point', 'pr': '🗣️ face-to-face'}, F)['pts'] is None

    # the two cards point at each other, also when the moment folded into its calendar event
    ev = dict(k='event', t='☕ coffee with Wren', rids=[IDA])
    jr = dict(k='lived', t='📒 journal', rid=IDJ, moment=IDA)
    flow.link_moments([ev, jr])
    assert ev['journals'] == [IDJ] and jr['moment'] == IDA

    # a moment not on today's page leaves the journal as it was
    lone = dict(k='lived', t='📒 journal', rid=IDK, moment=IDZ)
    flow.link_moments([lone])
    assert 'moment' not in lone

    # the engine draws the list, the whole entry and the link, and the old fold under a small link is gone
    E = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()
    for need in ('ul class="pts"', 'the whole entry', 'data-jump', "'after'", 'window.__all=all'):
        assert need in E, need
    assert '<summary>her words</summary>' not in E
    print('ok: journal highlights, whole words, and the moment link')


if __name__ == '__main__':
    main()
