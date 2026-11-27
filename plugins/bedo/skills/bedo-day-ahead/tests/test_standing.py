"""The standing link: the build names it beside the day's own link. Every build
through the day publishes only to the standing page (her words, 20 Nov 2026: I
only want to check one page); the day's own link is published once, at the dusk
close's last rebuild."""
import datetime as dt, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts'))
import myday

TODAY = dt.date(2026, 3, 4)
local = lambda s: dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
ROW = dict(id='rec1', practice='👁️ look ahead', created='2026-03-04T13:00:00Z', when='2026-03-04T13:00:00Z',
           deliverable='https://example.invalid/the-day')


def main():
    p = myday.page_links([ROW], TODAY, local, 'https://example.invalid/standing')
    assert p == dict(url='https://example.invalid/the-day', row='rec1', standing='https://example.invalid/standing'), p
    # the standing link is never taken for the day's own
    p = myday.page_links([dict(ROW, deliverable='https://example.invalid/standing')], TODAY, local, 'https://example.invalid/standing')
    assert p['url'] is None and p['standing'] == 'https://example.invalid/standing', p
    # no standing link in the settings: nothing to publish there
    assert myday.page_links([], TODAY, local)['standing'] is None
    # the runner's instruction and the procedure say standing, never both
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sh = open(os.path.join(here, 'run_day_ahead.sh'), encoding='utf-8').read()
    line = [l for l in sh.splitlines() if 'echo "publish:' in l][0]
    assert 'page.standing' in line and 'to page.url above' not in line, line
    md = open(os.path.join(here, 'SKILL.md'), encoding='utf-8').read()
    assert 'publishes only to `page.standing`' in md
    assert 'go there too' not in md and 'Then publish the same file to `page.standing`' not in md
    print('ok')


if __name__ == '__main__':
    main()
