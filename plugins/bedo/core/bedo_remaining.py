# -*- coding: utf-8 -*-
"""The remaining list: what is left of the open flow, read, never recalled.

Each line is a rule a chat used to have to remember, and skipped:

  A127  built from the CATALOG, filtered to active, for the open flow — 11 Sep
        dropped 🌬️ evening breaths for a whole evening because the list was typed
        from memory
  A166  remainders only, with a done count on top; done steps are left off
  A208  bare practice names: no cadence, no last-logged line, no reasons
  A200 · A227  📿 morning mantra prints as its name; the words come on request
  A228  a core in a code block, everything else on ONE line underneath; nothing
        leaves the catalog and every step counts toward done
  A126  the dawn list stops printing at noon; dusk opens after 7 PM

Predicted order is the catalog's own `order` field, low first; a step with no
order goes last. Nothing personal lives here: the flow's practices come from
the live catalog, the core from facts.json.

    python3 bedo_remaining.py --live                 # the open flow, now
    python3 bedo_remaining.py --live --flow dusk     # a named flow
    python3 bedo_remaining.py --catalog practices.json --day day.json --flow dawn
"""
import datetime as dt, re, sys

from bedo_reader import FACTS, as_rows, complete, load_local, offset_hours, on_day

FLOWS = FACTS['flows']
_MODS = re.compile('[️\U0001F3FB-\U0001F3FF]')


def norm(name):
    """A practice name compared without variation selectors or skin tones, so
    🤸🏻‍♀️ and 🤸‍♀️ are one step. The catalog's own spelling is what prints."""
    return ' '.join(_MODS.sub('', name or '').split()).casefold()


def catalog(src, fields=None):
    """Catalog rows from a complete read (I11), under logical names."""
    return as_rows(complete(src, 'practices catalog'), fields or FACTS['catalog_fields'])


def _hhmm(s):
    h, m = s.split(':')
    return dt.time(int(h), int(m))


def flow_steps(cat, flow):
    """The open flow's steps: active, in the flow's phase, a flow or optional
    step (or any step the catalog gave an order in that phase), in order."""
    phase = FLOWS['phase'][flow]
    steps = [r for r in cat if r.get('active') and r.get('phase') == phase and r.get('practice')
             and (r.get('group') in FLOWS['groups'] or r.get('order') is not None)]
    steps.sort(key=lambda r: (r.get('order') is None, r.get('order') or 0, r['practice']))
    return steps


def logged(day_rows):
    """Every practice the day already carries, in any status — a ⨂ skipped
    step is captured, not remaining."""
    return {norm(r.get('practice')) for r in day_rows if r.get('practice')}


def open_flow(now_local, day_rows):
    """dawn until its close is logged or noon passes (A126); dusk after 7 PM
    until its close is logged; otherwise none."""
    have = logged(day_rows)
    t = now_local.time()
    if t < _hhmm(FLOWS['backup_close']['dawn']) and norm(FLOWS['close']['dawn']) not in have:
        return 'dawn'
    if t >= _hhmm(FLOWS['dusk_opens_after']) and norm(FLOWS['close']['dusk']) not in have:
        return 'dusk'
    return None


def split(steps, day_rows, flow):
    """(done count, total, core remaining, other remaining) — each a list of
    catalog names in predicted order."""
    have = logged(day_rows)
    left = [s['practice'] for s in steps if norm(s['practice']) not in have]
    core = FLOWS['core'].get(flow)
    if core is None:
        return len(steps) - len(left), len(steps), left, []
    want = {norm(c) for c in core}
    return (len(steps) - len(left), len(steps),
            [p for p in left if norm(p) in want], [p for p in left if norm(p) not in want])


def holds_open(steps, day_rows, flow):
    """What still keeps the flow from closing itself: required steps only —
    never an optional one, never one collapsed off the core (A228), never the
    close itself."""
    have = logged(day_rows)
    core = FLOWS['core'].get(flow)
    want = {norm(c) for c in core} if core is not None else None
    close = norm(FLOWS['close'][flow])
    return [s['practice'] for s in steps
            if norm(s['practice']) not in have and norm(s['practice']) != close
            and s.get('group') not in FLOWS['never_held_open']
            and (want is None or norm(s['practice']) in want)]


def render(flow, steps, day_rows):
    """The text form: a code block with the count and the core, then one line."""
    done, total, core, rest = split(steps, day_rows, flow)
    head = f'{FLOWS["phase"][flow]} · {done} of {total} done'
    if not core and not rest:
        return '```\n' + FLOWS['phase'][flow] + f' · all {total} done\n```'
    out = '```\n' + '\n'.join([head] + core) + '\n```'
    if rest:
        out += '\nalso: ' + ' · '.join(rest)
    return out


def spoken(flow, steps, day_rows):
    """The one spoken line on voice — names only."""
    done, total, core, rest = split(steps, day_rows, flow)
    left = core + rest
    name = flow
    if not left:
        return f'{name}: all {total} done.'
    return f'{name}: {len(left)} left, next is {left[0]}.'


def _ref(text):
    """Every non-ASCII character as a numeric reference, so a glyph cannot
    drift in the markup (A237)."""
    return ''.join(c if ord(c) < 128 else f'&#x{ord(c):X};' for c in text)


def short(name):
    """(glyph, one or two words): '🔅 evening sun' → ('🔅', 'evening sun');
    '📧 clear gmail inbox' → ('📧', 'gmail inbox')."""
    glyph, _, words = (name or '').partition(' ')
    words = words.split()
    return glyph, ' '.join(words[-2:]) if len(words) > 2 else ' '.join(words)


def widget(flow, steps, day_rows):
    """The remaining list as her pill strip (A237, A248): the flow's glyph and a
    marigold bar, no words and no count; one row of uniform pills, glyphs shown,
    scrolling left to right; a tap opens a note box and sends nothing until she
    says. Order is the catalog's for now — the predicted order (minutes since
    wake) is backlog 261002_0620. Returns an HTML fragment for a widget surface."""
    done, total, core, rest = split(steps, day_rows, flow)
    left = core + rest
    bar = FLOWS['widget']['bar'][flow]
    head = _ref(FLOWS['phase'][flow].split(' ')[0])
    pct = round(100 * done / total) if total else 100
    pills = ''.join(
        f'<button class="p" data-n="{_ref(n)}"><span class="g">{_ref(g)}</span>{_ref(w)}</button>'
        for n, (g, w) in ((n, short(n)) for n in left))
    return f"""<div class="bedo-rl">
<style>
.bedo-rl{{font:15px/1.2 system-ui,sans-serif;color:inherit}}
.bedo-rl .h{{display:flex;align-items:center;gap:10px;margin:0 0 10px}}
.bedo-rl .h .f{{font-size:22px}}
.bedo-rl .t{{flex:1;height:8px;border-radius:4px;background:rgba(127,127,127,.18);overflow:hidden}}
.bedo-rl .t i{{display:block;height:100%;width:{pct}%;background:{bar};border-radius:4px}}
.bedo-rl .s{{display:flex;gap:8px;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:6px}}
.bedo-rl .p{{flex:0 0 auto;scroll-snap-align:start;height:40px;padding:0 16px;border-radius:20px;border:1px solid rgba(127,127,127,.4);background:rgba(127,127,127,.1);color:inherit;font:inherit;cursor:pointer;white-space:nowrap}}
.bedo-rl .g{{margin-right:8px}}
.bedo-rl .n{{display:none;margin-top:10px;gap:8px;flex-direction:column}}
.bedo-rl .n.on{{display:flex}}
.bedo-rl textarea{{font:inherit;color:inherit;background:rgba(127,127,127,.08);border:1px solid rgba(127,127,127,.4);border-radius:10px;padding:8px;min-height:56px}}
.bedo-rl .b{{display:flex;gap:8px}}
.bedo-rl .b button{{height:36px;padding:0 16px;border-radius:18px;border:1px solid rgba(127,127,127,.4);background:transparent;color:inherit;font:inherit;cursor:pointer}}
.bedo-rl .b .go{{background:{bar};border-color:{bar};color:#14121c}}
</style>
<div class="h"><span class="f">{head}</span><div class="t"><i></i></div></div>
<div class="s">{pills}</div>
<div class="n"><div class="w"></div><textarea placeholder="a note, if you want one"></textarea>
<div class="b"><button class="go">log it</button><button class="x">cancel</button></div></div>
<script>
(function(){{var a=document.querySelectorAll('.bedo-rl'),r=a[a.length-1],n=r.querySelector('.n'),w=n.querySelector('.w'),
ta=n.querySelector('textarea'),cur=null;
r.querySelectorAll('.p').forEach(function(b){{b.onclick=function(){{cur=b.getAttribute('data-n');w.textContent=cur;ta.value='';n.classList.add('on');ta.focus();}};}});
n.querySelector('.x').onclick=function(){{n.classList.remove('on');cur=null;}};
n.querySelector('.go').onclick=function(){{if(!cur)return;var t='log '+cur+(ta.value.trim()?' — '+ta.value.trim():'');
if(typeof sendPrompt==='function')sendPrompt(t);n.classList.remove('on');}};}})();
</script>
</div>"""


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(description='the remaining list for the open flow')
    ap.add_argument('--live', action='store_true', help='read the catalog and today from Airtable')
    ap.add_argument('--catalog'); ap.add_argument('--day', help='a complete read of the day\'s rows')
    ap.add_argument('--flow', choices=['dawn', 'dusk'])
    ap.add_argument('--date', help='YYYY-MM-DD, default today')
    ap.add_argument('--voice', action='store_true')
    ap.add_argument('--widget', action='store_true', help='the pill strip, as HTML for a widget surface')
    a = ap.parse_args(argv)
    L = load_local()
    now = dt.datetime.now(dt.timezone.utc)
    now_local = now + dt.timedelta(hours=offset_hours(L, now))
    day = dt.date.fromisoformat(a.date) if a.date else now_local.date()
    fields = {**{k: k for k in ('practice', 'status', 'datetime')}, **L.get('stream_fields', {})}
    if a.live:
        from bedo_air import Air, read_day, read_catalog
        air = Air()
        cat_src, (day_src, _) = read_catalog(air, L), read_day(air, L, day)
    else:
        if not (a.catalog and a.day):
            sys.exit('give --live, or both --catalog and --day')
        cat_src, day_src = a.catalog, a.day
    cat = catalog(cat_src, L.get('practices_fields'))
    rows = on_day(as_rows(complete(day_src, 'day'), fields), day, L)
    flow = a.flow or open_flow(now_local, rows)
    if not flow:
        print('no flow open')
        return
    steps = flow_steps(cat, flow)
    print(spoken(flow, steps, rows) if a.voice else widget(flow, steps, rows) if a.widget
          else render(flow, steps, rows))


if __name__ == '__main__':
    main()
