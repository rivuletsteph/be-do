# -*- coding: utf-8 -*-
"""The dawn page (27 Nov 2026): the dawn flow as four lanes in the wellness
wheel colors, the next three steps to tap, and the steps done in the order
done, each with its time and a line from its row.

The order comes from the same code as the remaining line (bedo_remaining's
flow_steps), worked out here and written into the page. The page itself only
decides what is done, from the day's rows, which it reads through her own
Airtable connector when she opens it or comes back to it — never on a timer.
A tap writes one row and fills its own dot, with no second read (her words,
27 Nov 2026: that is a lot of Airtable calls). So the page needs a rebuild only
when the order changes, never for a step logged.

    python3 bedo_dawn_page.py --live --out dawn.html          # build from the live catalog and today
    python3 bedo_dawn_page.py --catalog p.json --day d.json --base-id app… --out dawn.html

Prints `page.title`, `page.file`, `page.standing` (the settings row's
`dawn_url`; empty the first time, when the page is published new and its link
goes on the row) and `page.capabilities`, the declaration to publish with.
"""
import argparse, datetime as dt, json, os, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, on_day
import bedo_remaining as R

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'dawn_page.html')
P = FACTS['dawn_page']
FLOWS = FACTS['flows']
TITLE = 'Dawn flow'
TOOLS = ['list_records_for_table', 'create_records_for_table', 'delete_records_for_table', 'search_bases']
CAPABILITIES = {'mcp': {'servers': [{'server': 'Airtable', 'tools': TOOLS}]}}


def steps(cat):
    """[{p, lane, code, quiet, sun}] — the dawn steps the page draws, in her
    predicted order: the flow's steps, less what the page leaves off (her wake
    and the readouts Code writes for itself) and the close."""
    all_ = R.flow_steps(cat, 'dawn')
    off = set()
    for name in P['leave_off']:
        i = (next((j for j, r in enumerate(all_) if R.norm(r['practice']) == R.norm(name)), None)
             if ' ' in name.strip() else R.lead_at(all_, name))
        if i is not None:
            off.add(R.norm(all_[i]['practice']))
    close = R.norm(FLOWS['close']['dawn'])
    code = R.code_steps('dawn', all_)
    quiet = {R.norm(p) for p in FLOWS.get('ask_if_missing', {}).get('dawn', [])}
    sun = {R.norm(p) for p in FLOWS['after_sunrise']}
    out = []
    for r in all_:
        n = R.norm(r['practice'])
        if n in off or n == close:
            continue
        out.append({'p': r['practice'], 'lane': lane(r.get('wellness')), 'code': n in code,
                    'quiet': n in quiet, 'sun': n in sun})
    return out


def lane(wellness):
    """The lane a catalog wellness falls in: each of the four takes its pair
    on the wheel (heart and water, body and earth, mind and air, spirit and fire)."""
    w = R.norm(wellness)
    return next((v for k, v in P['lane_of'].items() if R.norm(k) == w), 'spirit')


def snapshot(day_rows):
    """The day's rows as the page reads them live, so it opens right with no
    read: the step, its time and status, its title and the start of its details
    (the line the page shows is worked out there, for every row alike)."""
    return [{'id': r.get('id'), 'p': r['practice'], 't': r['datetime'], 's': r.get('status') or '',
             'title': r.get('title') or '', 'd': (r.get('details') or '')[:600]}
            for r in day_rows if r.get('practice') and r.get('datetime')]


def sunrises(day, local):
    """{date: local minutes} of sunrise for the coming days at her home, from
    the settings row; empty without one. The place itself never goes on the page."""
    h = (local or {}).get('home') or {}
    if h.get('lat') is None or h.get('lon') is None:
        return {}
    return {str(day + dt.timedelta(days=i)): R.sunrise_at(day + dt.timedelta(days=i), h['lat'], h['lon'], local)
            for i in range(P['sunrise_days'])}


def plan(cat, day_rows, local, day, base_id, base_name):
    f = local['stream_fields']
    return {
        'day': str(day), 'tz': local.get('time_zone') or 'UTC',
        'base': {'id': base_id, 'name': base_name},
        'weekly_name': local.get('weekly_name', 'w{n} be•do'), 'week': FACTS['week'],
        'table': local['stream_table'],
        'fields': {k: f[k] for k in ('title', 'practice', 'status', 'datetime', 'details')},
        'steps': steps(cat), 'lanes': P['lanes'],
        'close': FLOWS['close']['dawn'], 'wake': FLOWS['wake'], 'noon': FLOWS['backup_close']['dawn'],
        'same_kind': FLOWS.get('same_kind', {}).get('dawn', {}), 'covers': FLOWS.get('covers', {}),
        'either_or': FLOWS.get('either_or', []),
        'sun_by_minutes': FLOWS['sun_by_minutes'], 'sunrise': sunrises(day, local),
        'next': P['next'], 'tap_status': P['tap_status'],
        'tap_details': f"{FACTS['divider']}\n{P['tap_line']}",
        'undo_seconds': P['undo_seconds'], 'reread_after_seconds': P['reread_after_seconds'],
        'open_status': list(R.OPEN), 'divider': FACTS['divider'], 'be_do': FACTS['be_do_block'],
        'rows': snapshot(day_rows),
    }


def render(data, template=TEMPLATE):
    """The page, with its data written in as JSON (every < escaped)."""
    html = open(template, encoding='utf-8').read()
    blob = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    assert '/*DATA*/null' in html
    return html.replace('/*DATA*/null', blob, 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description='build the dawn page')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--catalog'); ap.add_argument('--day')
    ap.add_argument('--base-id'); ap.add_argument('--base-name')
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--out', default='dawn.html')
    a = ap.parse_args(argv)
    L = load_local()
    now = dt.datetime.now(dt.timezone.utc)
    day = dt.date.fromisoformat(a.date) if a.date else (now + dt.timedelta(hours=offset_hours(L, now))).date()
    fields = {**{k: k for k in ('practice', 'status', 'datetime', 'details', 'title')}, **L.get('stream_fields', {})}
    if a.live:
        from bedo_air import Air, read_day, read_catalog
        air = Air()
        names = air.bases()
        cat_src = read_catalog(air, L)
        day_src, base_name = read_day(air, L, day, names)
        base_id = names[base_name]
    else:
        if not (a.catalog and a.day and a.base_id):
            sys.exit('give --live, or --catalog, --day and --base-id')
        cat_src, day_src, base_id = a.catalog, a.day, a.base_id
        from bedo_entry import week_number
        base_name = a.base_name or L.get('weekly_name', 'w{n} be•do').format(n=week_number(day))
    cat = R.catalog(cat_src, L.get('practices_fields'))
    rows = on_day(as_rows(complete(day_src, 'day'), fields), day, L)
    open(a.out, 'w', encoding='utf-8').write(render(plan(cat, rows, L, day, base_id, base_name)))
    print(f'page.title      {TITLE}')
    print(f'page.file       {os.path.abspath(a.out)}')
    print(f'page.standing   {L.get("dawn_url") or ""}')
    print(f'page.capabilities {json.dumps(CAPABILITIES)}')


if __name__ == '__main__':
    main()
