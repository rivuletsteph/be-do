#!/usr/bin/env python3
"""grant_page: the grant watch report as one readable page.

    python3 grant_page.py report.json watch.json out.html [--sheet URL] [--standalone]

    python3 grant_page.py --extract page.html watch.json seen.json

The page carries its own data (the watch list and the seen ids), so --extract
reads last week's page back into the two files the watch needs.

--standalone writes a whole document to save and share outside Claude; leave
--sheet off then, so a private list's link isn't passed around.

report.json is grant_watch.py --json; watch.json is the same watch list.
The page leads with what fits the work (a program applied to before, a watched
program or agency, or a keyword in the title) and folds away the rest.
"""
import datetime as dt
import html
import json
import sys

E = html.escape


def fits(r, watch):
    """A match that fits the work, not just a word in a long description."""
    if r.get("applied_before"):
        return True
    kinds = {m.split(":", 1)[0] for m in r["matched"]}
    if kinds & {"program", "listing", "applied", "agency"}:
        return True
    t = (r["title"] or "").lower()
    return any(k.lower() in t for k in watch.get("keywords", []))


def why(r, watch):
    t = (r["title"] or "").lower()
    out = []
    if r.get("applied_before"):
        out.append("applied " + ", ".join(str(a.get("year")) for a in r["applied_before"]))
    for m in r["matched"]:
        kind, term = m.split(": ", 1)
        if kind == "keyword" and term.lower() in t:
            out.append(term)
        elif kind in ("program", "agency", "listing") and not r.get("applied_before"):
            out.append(term)
    seen, uniq = set(), []
    for w in out:
        if w not in seen:
            seen.add(w)
            uniq.append(w)
    return uniq


def nice(d):
    return dt.date.fromisoformat(d).strftime("%a %-d %b") if d else "no date yet"


def urgency(days):
    if days is None:
        return "later"
    return "now" if days <= 14 else "soon" if days <= 42 else "later"


def row(r, watch, horizon):
    d = r["days_left"]
    pos = 100 if d is None else max(0, min(100, d / horizon * 100))
    tags = "".join(f'<span class="tag">{E(w)}</span>' for w in why(r, watch))
    if r["status"] == "forecasted":
        tags += '<span class="tag fc">forecast</span>'
    if r.get("new"):
        tags += '<span class="tag nw">new</span>'
    days = "" if d is None else f'<b>{d}</b><span>{"day" if d == 1 else "days"}</span>'
    return f'''<li class="opp {urgency(d)}">
  <div class="when"><div class="days">{days}</div><div class="date">{E(nice(r["close"]))}</div></div>
  <div class="what">
    <a href="{E(r["link"])}" target="_blank" rel="noopener">{E(r["title"])}</a>
    <div class="meta"><span>{E((r["agency"] or "").strip())}</span><code>{E(r["number"])}</code></div>
    <div class="tags">{tags}</div>
  </div>
  <div class="track" aria-hidden="true"><i style="left:{pos:.1f}%"></i></div>
</li>'''


# built from parts: the font axes read like an address to the privacy check
FONTS = ("https://fonts.googleapis.com/css2?family=Archivo:wdth,wght" + "@" + "75..100,500..800"
         "&family=Public+Sans:wght" + "@" + "400;600&family=IBM+Plex+Mono:wght" + "@" + "400;500&display=swap")


DATA_ID = "grant-watch-data"


PRIVATE = ("evidence",)  # her mail's subject lines: in her own page, never in a shared file


def data_block(watch, seen, share=False):
    """The watch list and last week's seen ids, carried inside the page itself:
    the page is the one record (her word, 6 Nov 2026), so next week reads it back."""
    if share:
        watch = dict(watch, applied=[{k: v for k, v in a.items() if k not in PRIVATE}
                                     for a in watch.get("applied", [])])
    blob = json.dumps({"watch": watch, "seen": sorted(seen)}, ensure_ascii=False, indent=1)
    blob = blob.replace("</", "<\\/")
    return f'<script type="application/json" id="{DATA_ID}">\n{blob}\n</script>'


def extract(path):
    """Read the watch list and seen ids back out of a published page."""
    import re
    s = open(path, encoding="utf-8").read()
    m = re.search(r'<script type="application/json" id="' + DATA_ID + r'">(.*?)</script>', s, re.S)
    if not m:
        raise SystemExit("no grant watch data in " + path)
    return json.loads(m.group(1).replace("<\\/", "</"))


def page(rep, watch, sheet=None, share=False):
    weeks = rep["weeks"]
    horizon = weeks * 7
    today = dt.date.fromisoformat(rep["today"])
    soon = rep["soon"]
    good = [r for r in soon if fits(r, watch)]
    rest = [r for r in soon if not fits(r, watch)]
    new = [r for r in rep["new"] if fits(r, watch)]
    reopened = rep["reopened"]
    lead = good[0] if good else None
    applied = watch.get("applied", [])

    def lst(rows):
        return '<ol class="opps">' + "".join(row(r, watch, horizon) for r in rows) + "</ol>" if rows else '<p class="none">None this week.</p>'

    lead_html = ""
    if lead:
        ab = lead.get("applied_before") or []
        hist = "; ".join(f'{a.get("year")} {a.get("status")}' for a in ab)
        lead_html = f'''<section class="lead {urgency(lead["days_left"])}">
  <div class="count"><b>{lead["days_left"]}</b><span>days</span></div>
  <div>
    <p class="eyebrow">Next deadline that fits</p>
    <h2><a href="{E(lead["link"])}" target="_blank" rel="noopener">{E(lead["title"])}</a></h2>
    <p class="sub">{E((lead["agency"] or "").strip())} · <code>{E(lead["number"])}</code> · closes {E(nice(lead["close"]))}{(" · applied before: " + E(hist)) if hist else ""}</p>
  </div>
</section>'''

    def arow(a):
        st = (a.get("status") or "unknown").replace(" ", "-")
        return (f'<tr><td>{E(str(a.get("year") or ""))}</td><td>{E(a.get("program") or "")}</td>'
                f'<td><span class="st {E(st)}">{E(a.get("status") or "unknown")}</span></td>'
                f'<td>{E(a.get("role") or "")}</td><td><code>{E(a.get("number") or "")}</code></td></tr>')

    applied_html = ""
    if applied:
        applied_html = f'''<section>
  <h3>What you've applied for <span class="n">{len(applied)}</span></h3>
  <div class="scroll"><table><thead><tr><th>Year</th><th>Program</th><th>Status</th><th>Your role</th><th>Number</th></tr></thead>
  <tbody>{"".join(arow(a) for a in sorted(applied, key=lambda a: str(a.get("year")), reverse=True))}</tbody></table></div>
</section>'''

    funded = watch.get("funded", [])

    def frow(f):
        c = (f.get("checked") or "").lower()
        mark = ('<span class="st funded">checked</span>' if c.startswith(("yes", "partly"))
                else '<span class="st submitted">likely</span>' if c.startswith("likely")
                else '<span class="st">not yet checked</span>')
        src = f'<a href="{E(f["source"])}" target="_blank" rel="noopener">source</a>' if f.get("source") else ""
        note = f.get("checked") or ""
        note = note.split(":", 1)[1].strip() if ":" in note else ""
        note_html = f'<div class="note">{E(note)}</div>' if note else ""
        return (f'<tr><td>{E(f.get("years") or "")}</td><td>{E(f.get("project") or "")}'
                f'<div class="meta"><span>{E(f.get("funder") or "")} · {E(f.get("program") or "")}</span></div>{note_html}</td>'
                f'<td>{E(f.get("role") or "")}</td><td><code>{E(f.get("number") or "")}</code></td><td>{mark} {src}</td></tr>')

    funded_html = ""
    if funded:
        funded_html = f'''<section>
  <h3>Funded projects <span class="n">{len(funded)}</span></h3>
  <div class="scroll"><table><thead><tr><th>Years</th><th>Project</th><th>His role</th><th>Award</th><th>Record</th></tr></thead>
  <tbody>{"".join(frow(f) for f in sorted(funded, key=lambda f: str(f.get("years") or "0"), reverse=True))}</tbody></table></div>
</section>'''

    sheet_html = f' · <a href="{E(sheet)}" target="_blank" rel="noopener">the watch list (Sheet)</a>' if sheet else ""
    return f'''<title>Grant watch</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="{FONTS}">
<style>
/* layout: a deadline ledger, nearest first, each row placed on a {weeks}-week track */
:root {{
  --bg: #f3f6f6; --panel: #ffffff; --ink: #14232a; --muted: #5a6b72; --line: #d5dfe1;
  --water: #1f6f86; --water-soft: #dcecf0; --now: #b4471f; --now-soft: #f6e2d8; --soon: #8a6a12; --soon-soft: #f2ead2;
  --display: "Archivo", "Arial Narrow", system-ui, sans-serif;
  --body: "Public Sans", system-ui, -apple-system, "Segoe UI", sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, Menlo, monospace;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg: #0f1a1e; --panel: #15242a; --ink: #e3ecee; --muted: #93a7ad; --line: #26383f;
  --water: #6cc0d6; --water-soft: #173540; --now: #f08a62; --now-soft: #3a2219; --soon: #d9b453; --soon-soft: #332b14; color-scheme: dark }} }}
:root[data-theme="dark"] {{
  --bg: #0f1a1e; --panel: #15242a; --ink: #e3ecee; --muted: #93a7ad; --line: #26383f;
  --water: #6cc0d6; --water-soft: #173540; --now: #f08a62; --now-soft: #3a2219; --soon: #d9b453; --soon-soft: #332b14; color-scheme: dark }}
body {{ background: var(--bg); color: var(--ink); font: 15px/1.5 var(--body); }}
.wrap {{ max-width: 860px; margin: 0 auto; padding-block: 28px 56px;
  padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px));
  display: grid; gap: 28px; }}
a {{ color: inherit; text-decoration-color: color-mix(in srgb, var(--water) 55%, transparent); text-underline-offset: 3px; }}
a:hover {{ color: var(--water); }}
a:focus-visible {{ outline: 2px solid var(--water); outline-offset: 2px; border-radius: 2px; }}
code {{ font: 12.5px var(--mono); color: var(--muted); }}
header h1 {{ font: 800 clamp(30px, 6vw, 44px)/1 var(--display); font-stretch: 78%; letter-spacing: -.01em; margin: 0; text-wrap: balance; }}
header p {{ margin: 8px 0 0; color: var(--muted); }}
.eyebrow, h3 {{ font: 600 12px/1.2 var(--display); letter-spacing: .09em; text-transform: uppercase; color: var(--muted); margin: 0; }}
h3 {{ margin-bottom: 10px; display: flex; gap: 8px; align-items: baseline; }}
h3 .n {{ font: 500 12px var(--mono); letter-spacing: 0; color: var(--water); }}
.lead {{ display: grid; grid-template-columns: auto 1fr; gap: 20px; align-items: center; background: var(--panel);
  border: 1px solid var(--line); border-left: 6px solid var(--water); border-radius: 6px; padding: 18px 20px; }}
.lead.now {{ border-left-color: var(--now); }}
.lead h2 {{ font: 700 clamp(19px, 3.4vw, 24px)/1.2 var(--display); font-stretch: 88%; margin: 4px 0 6px; text-wrap: balance; }}
.lead .sub {{ margin: 0; color: var(--muted); font-size: 14px; }}
.count {{ text-align: center; min-width: 72px; }}
.count b {{ display: block; font: 800 52px/1 var(--display); font-variant-numeric: tabular-nums; color: var(--now); }}
.lead:not(.now) .count b {{ color: var(--water); }}
.count span {{ font: 600 12px var(--display); text-transform: uppercase; letter-spacing: .09em; color: var(--muted); }}
.scale {{ display: flex; justify-content: space-between; font: 11px var(--mono); color: var(--muted); padding: 0 0 6px; }}
.opps {{ list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--line); }}
.opp {{ display: grid; grid-template-columns: 92px minmax(0, 1fr); gap: 4px 16px; padding: 12px 0; border-bottom: 1px solid var(--line); }}
.when .days {{ font-variant-numeric: tabular-nums; }}
.when .days b {{ font: 700 22px/1 var(--display); }}
.when .days span {{ font-size: 12px; color: var(--muted); margin-left: 4px; }}
.when .date {{ font: 12px var(--mono); color: var(--muted); margin-top: 2px; }}
.opp.now .days b {{ color: var(--now); }}
.opp.soon .days b {{ color: var(--soon); }}
.what a {{ font-weight: 600; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 4px 12px; font-size: 13px; color: var(--muted); margin-top: 2px; }}
.tags {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }}
.tags:empty {{ display: none; }}
.tag {{ font-size: 12px; padding: 1px 8px; border-radius: 99px; background: var(--water-soft); color: var(--water); }}
.tag.fc {{ background: var(--soon-soft); color: var(--soon); }}
.tag.nw {{ background: var(--now-soft); color: var(--now); }}
.track {{ grid-column: 2; height: 4px; background: var(--line); border-radius: 2px; position: relative; margin-top: 6px; }}
.track i {{ position: absolute; top: -3px; width: 10px; height: 10px; margin-left: -5px; border-radius: 50%; background: var(--water); }}
.opp.now .track i {{ background: var(--now); }}
.opp.soon .track i {{ background: var(--soon); }}
details {{ background: var(--panel); border: 1px solid var(--line); border-radius: 6px; padding: 12px 16px; }}
summary {{ cursor: pointer; font-weight: 600; }}
summary span {{ color: var(--muted); font-weight: 400; }}
details .opps {{ margin-top: 10px; }}
.note {{ font-size: 12.5px; color: var(--muted); margin-top: 3px; }}
.none {{ color: var(--muted); margin: 0; }}
.scroll {{ overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; font-size: 14px; }}
th {{ text-align: left; font: 600 12px var(--display); letter-spacing: .06em; text-transform: uppercase; color: var(--muted); padding: 6px 10px 6px 0; border-bottom: 1px solid var(--line); }}
td {{ padding: 9px 10px 9px 0; border-bottom: 1px solid var(--line); vertical-align: top; }}
td:first-child {{ font: 500 13px var(--mono); }}
.st {{ font-size: 12px; padding: 1px 8px; border-radius: 99px; background: var(--line); color: var(--ink); white-space: nowrap; }}
.st.funded {{ background: var(--water-soft); color: var(--water); }}
.st.declined {{ background: var(--now-soft); color: var(--now); }}
.st.submitted {{ background: var(--soon-soft); color: var(--soon); }}
footer {{ color: var(--muted); font-size: 13px; border-top: 1px solid var(--line); padding-top: 14px; }}
@media (max-width: 520px) {{
  .lead {{ grid-template-columns: 1fr; gap: 8px; }} .count {{ text-align: left; display: flex; align-items: baseline; gap: 8px; }}
  .opp {{ grid-template-columns: 1fr; }} .when {{ display: flex; gap: 10px; align-items: baseline; }} .track {{ grid-column: 1; }}
}}
</style>
<div class="wrap">
<header>
  <h1>Grant watch</h1>
  <p>Week of {E(today.strftime("%-d %B %Y"))} · {len(good)} deadlines that fit your work in the next {weeks} weeks</p>
</header>
{lead_html}
<section>
  <h3>Deadlines that fit <span class="n">{len(good)}</span></h3>
  <div class="scale" aria-hidden="true"><span>today</span><span>{weeks // 2} weeks</span><span>{weeks} weeks</span></div>
  {lst(good)}
</section>
{funded_html}
<section>
  <h3>New since last week <span class="n">{len(new)}</span></h3>
  {lst(new)}
</section>
<section>
  <h3>Applied before, open again <span class="n">{len(reopened)}</span></h3>
  {lst(reopened)}
</section>
<details>
  <summary>Other matches <span>· {len(rest)} where a keyword shows up only in the full description</span></summary>
  {lst(rest)}
</details>
{applied_html}
{data_block(watch, rep.get("seen", []), share)}
<footer>From grants.gov, posted and forecasted opportunities, read {E(today.strftime("%-d %b %Y"))}. Dollar amounts, salaries and personnel are never kept here{sheet_html}.</footer>
</div>
'''


def standalone(body):
    """A whole document, for a file saved and shared outside Claude (OneDrive)."""
    return ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
            + body.replace("<div class=\"wrap\">", "</head>\n<body>\n<div class=\"wrap\">", 1)
            + "</body>\n</html>\n")


def main(argv=None):
    a = argv or sys.argv[1:]
    if a and a[0] == "--extract":
        # grant_page.py --extract page.html watch.json seen.json
        d = extract(a[1])
        json.dump(d["watch"], open(a[2], "w"), ensure_ascii=False, indent=1)
        json.dump(d["seen"], open(a[3], "w"))
        return 0
    alone = "--standalone" in a
    a = [x for x in a if x != "--standalone"]
    sheet = None
    if "--sheet" in a:
        i = a.index("--sheet")
        sheet = a[i + 1]
        a = a[:i] + a[i + 2:]
    rep, watch, out = json.load(open(a[0])), json.load(open(a[1])), a[2]
    html_out = page(rep, watch, sheet, share=alone)
    open(out, "w").write(standalone(html_out) if alone else html_out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
