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

`--flow dusk` builds its twin, the dusk page (27 Nov 2026): the same page for
the dusk flow, where Code's steps fill when a run writes them, a step that needs
her words opens a box for them, and 💊 evening pills is one button for both rows.

Prints `page.title`, `page.file`, `page.standing` (the settings row's
`dawn_url` or `dusk_url`; empty the first time, when the page is published new
and its link goes on the row) and `page.capabilities`, the declaration to publish with.
"""
import argparse, datetime as dt, json, os, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, on_day
import bedo_remaining as R

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, 'dawn_page.html')
P = FACTS['dawn_page']
FLOWS = FACTS['flows']
TOOLS = ['list_records_for_table', 'create_records_for_table', 'delete_records_for_table', 'search_bases']
CAPABILITIES = {'mcp': {'servers': [{'server': 'Airtable', 'tools': TOOLS}]}}


def capabilities(flow):
    """What the page is published with: her connector, and for a page with
    batch toggles, its own store to keep them in, one document an evening."""
    return {**CAPABILITIES, 'db': {}} if (cfg(flow).get('batch') or {}).get('items') else CAPABILITIES


def cfg(flow):
    """The page's settings for a flow: dusk_page over dawn_page."""
    return {**P, **(FACTS.get(f'{flow}_page') or {})} if flow != 'dawn' else P


def names(all_, wanted):
    """The catalog names a list of names or bare glyphs points at."""
    out = set()
    for name in wanted:
        i = (next((j for j, r in enumerate(all_) if R.norm(r['practice']) == R.norm(name)), None)
             if ' ' in name.strip() else R.lead_at(all_, name))
        if i is not None:
            out.add(R.norm(all_[i]['practice']))
    return out


def steps(cat, flow='dawn'):
    """[{p, lane, code, quiet, sun, words, pattern, members}] — the steps the
    page draws, in her predicted order: the flow's steps, less what the page
    leaves off and the close. Steps taken together (💊 evening pills) are one
    step carrying its members."""
    C = cfg(flow)
    all_ = R.flow_steps(cat, flow)
    off = names(all_, C['leave_off'])
    close = R.norm(FLOWS['close'][flow])
    code = R.code_steps(flow, all_) | names(all_, C['code'])
    words = names(all_, C['words'])
    batch = names(all_, (C.get('batch') or {}).get('steps', []))
    quiet = {R.norm(p) for p in FLOWS.get('ask_if_missing', {}).get(flow, [])}
    sun = {R.norm(p) for p in FLOWS['after_sunrise']} if flow == 'dawn' else set()
    pattern = R.from_pattern(flow)
    groups = {g: [m for m in ms if R.norm(m) in {R.norm(r['practice']) for r in all_}]
              for g, ms in R.together(flow).items()}
    out, seen = [], set()
    for r in all_:
        n = R.norm(r['practice'])
        if n in off or n == close:
            continue
        g = next((g for g, ms in groups.items() if n in {R.norm(m) for m in ms}), None)
        if g in seen:
            continue
        s = {'p': g or r['practice'], 'lane': lane(r.get('wellness')), 'code': n in code,
             'quiet': n in quiet, 'sun': n in sun, 'words': n in words, 'pattern': n in pattern, 'batch': n in batch}
        if g:
            seen.add(g)
            s['members'] = groups[g]
        out.append(s)
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


def member_lines(flow, local):
    """{member: the be•do line its tapped row carries} — for 💊 evening pills,
    the default her settings row names (`evening_pills`), so the row says what
    was taken."""
    C, out = cfg(flow), {}
    default = ((local or {}).get('evening_pills') or {}).get('default') or {}
    for ms in R.together(flow).values():
        for m in ms:
            took = ', '.join(default.get(m) or [])
            out[m] = f"{FACTS['divider']}\n{C['tap_line'][:-1]}, with the default{': ' + took if took else ''}."
    return out


def plan(cat, day_rows, local, day, base_id, base_name, flow='dawn'):
    f, C = local['stream_fields'], cfg(flow)
    return {
        'flow': flow, 'label': C['label'], 'title': C['title'], 'day_starts': R._hhmm(C['day_starts']).hour * 60
        + R._hhmm(C['day_starts']).minute, 'all_in': C['all_in'], 'status_of': C['status_of'],
        'member_lines': member_lines(flow, local),
        'batch': {k: v for k, v in C['batch'].items() if k in ('name', 'label', 'note', 'items')} if C.get('batch') else None,
        'day': str(day), 'tz': local.get('time_zone') or 'UTC',
        'base': {'id': base_id, 'name': base_name},
        'weekly_name': local.get('weekly_name', 'w{n} be•do'), 'week': FACTS['week'],
        'table': local['stream_table'],
        'fields': {k: f[k] for k in ('title', 'practice', 'status', 'datetime', 'details')},
        'steps': steps(cat, flow), 'lanes': P['lanes'],
        'close': FLOWS['close'][flow], 'wake': FLOWS['wake'],
        'noon': FLOWS['backup_close']['dawn'] if flow == 'dawn' else None,
        'same_kind': FLOWS.get('same_kind', {}).get(flow, {}), 'covers': FLOWS.get('covers', {}),
        'either_or': FLOWS.get('either_or', []),
        'sun_by_minutes': FLOWS['sun_by_minutes'], 'sunrise': sunrises(day, local) if flow == 'dawn' else {},
        'next': P['next'], 'tap_status': P['tap_status'],
        'tap_details': f"{FACTS['divider']}\n{C['tap_line']}",
        'undo_seconds': P['undo_seconds'], 'reread_after_seconds': P['reread_after_seconds'],
        'open_status': list(R.OPEN), 'divider': FACTS['divider'], 'be_do': FACTS['be_do_block'],
        'rows': snapshot(day_rows),
    }


def render(data, template=TEMPLATE):
    """The page, with its data written in as JSON (every < escaped)."""
    html = open(template, encoding='utf-8').read()
    blob = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    assert '/*DATA*/null' in html and '<title>Dawn flow</title>' in html
    html = html.replace('<title>Dawn flow</title>', f"<title>{data.get('title') or 'Dawn flow'}</title>", 1)
    return html.replace('/*DATA*/null', blob, 1)


def main(argv=None):
    ap = argparse.ArgumentParser(description='build the dawn or dusk page')
    ap.add_argument('--flow', choices=['dawn', 'dusk'], default='dawn')
    ap.add_argument('--live', action='store_true')
    ap.add_argument('--catalog'); ap.add_argument('--day')
    ap.add_argument('--base-id'); ap.add_argument('--base-name')
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    L = load_local()
    now = dt.datetime.now(dt.timezone.utc)
    C = cfg(a.flow)
    out = a.out or f'{a.flow}.html'
    starts = R._hhmm(C['day_starts'])          # a dusk past midnight is still the evening before
    local_now = now + dt.timedelta(hours=offset_hours(L, now)) - dt.timedelta(hours=starts.hour, minutes=starts.minute)
    day = dt.date.fromisoformat(a.date) if a.date else local_now.date()
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
    open(out, 'w', encoding='utf-8').write(render(plan(cat, rows, L, day, base_id, base_name, a.flow)))
    print(f'page.title      {C["title"]}')
    print(f'page.file       {os.path.abspath(out)}')
    print(f'page.standing   {L.get(C["url_key"]) or ""}')
    print(f'page.icon       {C["icon"]}')
    print(f'page.capabilities {json.dumps(capabilities(a.flow))}')


if __name__ == '__main__':
    main()
