#!/usr/bin/env python3
"""grant_watch: the weekly grant-deadline watch, from grants.gov's public API.

Reads a watch file (what to look for and what was already applied for) and
prints the week's report: deadlines in the window, new matches since last week,
and programs applied to before that are open again. Nothing personal lives here;
the watch file comes from her Sheet in Drive.

    python3 grant_watch.py watch.json [--seen seen.json] [--weeks 12]
                           [--today YYYY-MM-DD] [--json] [--offline hits.json]
"""
import argparse
import datetime as dt
import html
import json
import sys
import urllib.request

API = "https://api.grants.gov/v1/api/search2"
STATUSES = "forecasted|posted"
VIEW = "https://www.grants.gov/search-results-detail/{id}"


def search(body, rows=100):
    """All hits for one search, paged. POST only: the API refuses a GET."""
    hits, start = [], 0
    while True:
        req = dict(body, oppStatuses=STATUSES, rows=rows, startRecordNum=start)
        r = urllib.request.Request(API, data=json.dumps(req).encode(),
                                   headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(r, timeout=30) as f:
            data = json.load(f).get("data") or {}
        page = data.get("oppHits") or []
        hits += page
        start += len(page)
        if not page or start >= int(data.get("hitCount") or 0):
            return hits


def parse_date(s):
    try:
        return dt.datetime.strptime(s, "%m/%d/%Y").date()
    except (TypeError, ValueError):
        return None


def prefix(number):
    """USDA-NIFA-NLGCA-011938 → USDA-NIFA-NLGCA: a program across its cycles."""
    parts = (number or "").split("-")
    return "-".join(parts[:-1]) if len(parts) > 1 and parts[-1].isdigit() else number or ""


def queries(watch):
    """One search per keyword, agency, program prefix and assistance listing."""
    out = []
    for k in watch.get("keywords", []):
        # quoted, so a phrase is a phrase: unquoted, "water quality" matched
        # any of its words and brought back 537 opportunities instead of 27
        out.append(("keyword", k, {"keyword": f'"{k}"' if " " in k else k}))
    for a in watch.get("agencies", []):
        out.append(("agency", a, {"agencies": a}))
    for p in watch.get("programs", []):
        out.append(("program", p, {"keyword": p}))
    for c in watch.get("assistance_listings", []):
        out.append(("listing", c, {"cfda": c}))
    for a in watch.get("applied", []):
        p = prefix(a.get("number", ""))
        if p and p not in watch.get("programs", []):
            out.append(("applied", p, {"keyword": p}))
    return out


def collect(watch, fetch=search):
    found = {}
    for kind, term, body in queries(watch):
        for h in fetch(body):
            h = dict(h, title=html.unescape(h.get("title") or ""))
            hit = found.setdefault(h["id"], dict(h, matched=[]))
            hit["matched"].append(f"{kind}: {term}")
    return found


def report(watch, found, seen, today, weeks):
    horizon = today + dt.timedelta(weeks=weeks)
    applied = {}
    for a in watch.get("applied", []):
        if a.get("number"):
            applied.setdefault(prefix(a["number"]), []).append(a)
    skip = set(watch.get("ignore", []))
    skip_agency = set(watch.get("ignore_agencies", []))
    rows = []
    for h in found.values():
        if h["number"] in skip or prefix(h["number"]) in skip:
            continue
        if h.get("agencyCode") in skip_agency:
            continue
        close = parse_date(h.get("closeDate"))
        if close and close < today:
            continue
        past = applied.get(prefix(h["number"]))
        rows.append({
            "id": h["id"], "number": h["number"], "title": h["title"],
            "agency": h.get("agency") or h.get("agencyCode"),
            "status": h.get("oppStatus"), "open": h.get("openDate"),
            "close": close.isoformat() if close else None,
            "days_left": (close - today).days if close else None,
            "soon": bool(close and close <= horizon),
            "new": h["id"] not in seen,
            "applied_before": ([{k: a.get(k) for k in ("year", "status", "role")}
                                for a in sorted(past, key=lambda a: str(a.get("year")))]
                               if past else None),
            "matched": sorted(set(h["matched"])),
            "link": VIEW.format(id=h["id"]),
        })
    rows.sort(key=lambda r: (r["close"] is None, r["close"] or ""))
    return {
        "today": today.isoformat(), "weeks": weeks,
        "soon": [r for r in rows if r["soon"]],
        "new": [r for r in rows if r["new"] and not r["soon"]],
        "reopened": [r for r in rows if r["applied_before"] and not r["soon"]],
        "seen": sorted(found),
    }


def line(r):
    when = f"closes {r['close']} ({r['days_left']} days)" if r["close"] else "no close date yet"
    tags = []
    if r["status"] == "forecasted":
        tags.append("forecast")
    if r["new"]:
        tags.append("new")
    if r["applied_before"]:
        tags.append("applied " + "; ".join(f"{a.get('year') or '?'} {a.get('status') or '?'}"
                                           for a in r["applied_before"]))
    tag = f" [{', '.join(tags)}]" if tags else ""
    return f"- {r['title']} · {r['agency']} · {r['number']} · {when}{tag}\n  {r['link']}"


def text(rep):
    out = [f"grant watch · {rep['today']} · next {rep['weeks']} weeks"]
    for key, head in (("soon", "Deadlines coming up"), ("new", "New since last week"),
                      ("reopened", "Applied before, open again")):
        out.append(f"\n{head} ({len(rep[key])})")
        out += [line(r) for r in rep[key]] or ["- none"]
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("watch")
    ap.add_argument("--seen", help="last week's seen ids (a JSON list); rewritten with this week's")
    ap.add_argument("--weeks", type=int, default=None)
    ap.add_argument("--today")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--offline", help="saved hits keyed by search term, for tests")
    a = ap.parse_args(argv)
    watch = json.load(open(a.watch))
    weeks = a.weeks or watch.get("weeks", 12)
    today = dt.date.fromisoformat(a.today) if a.today else dt.date.today()
    seen = set()
    if a.seen:
        try:
            seen = set(json.load(open(a.seen)))
        except FileNotFoundError:
            pass
    if a.offline:
        saved = json.load(open(a.offline))
        fetch = lambda body: saved.get(json.dumps(body, sort_keys=True), [])
    else:
        fetch = search
    try:
        found = collect(watch, fetch)
    except OSError as e:
        print(f"grants.gov could not be reached: {e}", file=sys.stderr)
        return 2
    rep = report(watch, found, seen, today, weeks)
    if a.seen and not seen and not a.offline:
        # first run: nothing is "new" yet; say so instead of listing everything
        for r in rep["new"]:
            r["new"] = False
        rep["new"] = []
    if a.seen:
        json.dump(rep["seen"], open(a.seen, "w"))
    print(json.dumps(rep, indent=1) if a.json else text(rep))
    return 0


if __name__ == "__main__":
    sys.exit(main())
