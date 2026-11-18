"""The standing link: the build names it beside the day's own link, so every
publish of the day's page also reaches the page her browser opens at start."""
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
    print('ok')


if __name__ == '__main__':
    main()
