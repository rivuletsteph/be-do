"""The pieces the be•do pages share, and the one function that puts them in.

The my day page (bedo-day-ahead) and the my week page (bedo-week-ahead) are
different pages, but they are the same page furniture: one ground, one card,
one theme button, one set of wellness glyphs, one family of colours for the
kinds of time, one way to write a time. Those live here, in one copy, so the
two cannot drift apart — a change to a colour or a glyph lands on both pages
at the next build.

A page engine marks where each part goes with a comment placeholder, the way
it already marked the base flow's own css and js:

    /*THEMEJS*/  /*SHELLCSS*/  /*BLOCKSCSS*/  /*BASICSJS*/
    /*KINDSJS*/  /*WELLNESSJS*/  /*CLOCKJS*/  /*BFCSS*/  /*BFJS*/

`fill(page)` replaces every placeholder the page carries and leaves the rest
alone, so an engine takes only the parts it uses. The palette itself is not
here: it is read off the day ahead's own :root and injected as /*ROOT*/ and
/*NIGHT*/, because it is generated, not written.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BF = os.path.join(HERE, '..', 'base-flow')

PARTS = {
    '/*THEMEJS*/': os.path.join(HERE, 'theme.js'),
    '/*SHELLCSS*/': os.path.join(HERE, 'shell.css'),
    '/*BLOCKSCSS*/': os.path.join(HERE, 'blocks.css'),
    '/*BASICSJS*/': os.path.join(HERE, 'basics.js'),
    '/*KINDSJS*/': os.path.join(HERE, 'kinds.js'),
    '/*WELLNESSJS*/': os.path.join(HERE, 'wellness.js'),
    '/*CLOCKJS*/': os.path.join(HERE, 'clock.js'),
    '/*BFCSS*/': os.path.join(BF, 'base_flow.css'),
    '/*BFJS*/': os.path.join(BF, 'base_flow.js'),
    '/*BFCARDCSS*/': os.path.join(HERE, 'baseflow-card.css'),
    '/*BFCARDJS*/': os.path.join(HERE, 'baseflow-card.js'),
}


def read(mark):
    """one part, as it sits on disk"""
    return open(PARTS[mark], encoding='utf-8').read()


def fill(page):
    """every shared part this page asks for, put where it asked for it"""
    for mark, path in PARTS.items():
        if mark in page:
            page = page.replace(mark, open(path, encoding='utf-8').read())
    return page


def am_pm(hhmm):
    """a time ending in a lowercase a or p — her amendment the clock amendment of 9 Nov 2026,
    9 Nov 2026: 9:00a, 2:45p. No space, no m, no AM/PM. The javascript side of
    the same rule is clock.js, so a page and a reply agree."""
    h, m = (int(x) for x in str(hhmm).split(':')[:2])
    return f'{h % 12 or 12}:{m:02d}{"a" if h < 12 else "p"}'


def span(a, b):
    """a range of times, the letter on each end, dropped from the first only
    when both ends share it (2:00–3:30p)"""
    one, two = am_pm(a), am_pm(b)
    return (one[:-1] + '–' + two) if one[-1] == two[-1] else (one + '–' + two)
