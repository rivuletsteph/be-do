# -*- coding: utf-8 -*-
"""One view for how things flow and how the drives moved (261111_d7, her notes of 11 Nov 2026).

Flow steps go to the wheel by their wellness; each rhythm lands on its own element; the day's
artifacts sit up top; the drives' moves live on the flow, not in a section of their own.

Every name below is an obvious invention.

    python3 tests/test_merged_flow.py
"""
import os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'scripts'))
import flow  # noqa: E402

RF = dict(name='fN')


def rec(name, **cells):
    return dict(id='rec' + name, cellValuesByFieldId=dict(fN=name, **cells))


def main():
    # the element field found from the read itself: the one whose values read as an element
    read = [rec('Rhythm One', fE='🌎 earth', fX='notes'), rec('Rhythm Two', fE={'name': '🌊 water'}),
            rec('Drive A', fE='💨 air'), rec('Rhythm Three'), rec('Odd One', fE='lava')]
    assert flow.rhythm_elements(read, RF) == {'Rhythm One': 'earth', 'Rhythm Two': 'water', 'Drive A': 'air'}
    # named in her settings, that field wins
    read2 = [rec('Rhythm One', fE='🌎 earth', fF='🔥 fire')]
    assert flow.rhythm_elements(read2, dict(RF, element='fF')) == {'Rhythm One': 'fire'}
    # nothing that reads as an element: an empty map, never a guess
    assert flow.rhythm_elements([rec('Rhythm One', fX='hello')], RF) == {}
    assert flow.rhythm_elements(None, RF) == {}

    eng = open(os.path.join(HERE, '..', 'assets', 'flow_engine.html'), encoding='utf-8').read()
    # the day's artifacts, up top, placed first by the page's order
    assert '<section class="arts" id="arts"></section>' in eng and 'function arts()' in eng
    assert re.search(r"function draw\(\)\{[^}]*\barts\(\)", eng)
    assert "['arts','today'" in eng, 'the artifacts lead the page in the workday and on a day gone'
    # the drives' moves are on the flow; no section of their own any more
    assert 'id="moved"' not in eng and 'function moved()' not in eng and 'moved();' not in eng
    assert 'function driveMove(d)' in eng
    # the wheel's eight elements, and the flow practices straight to theirs
    assert 'function flowSteps()' in eng and "to:'w'" in eng and 'rhythmEl(' in eng
    print('ok · the merged flow')


if __name__ == '__main__':
    main()
