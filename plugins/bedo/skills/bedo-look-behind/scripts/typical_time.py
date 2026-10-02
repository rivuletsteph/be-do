# -*- coding: utf-8 -*-
"""typical time — observed, never declared.

The practices table has no `typical time` field; only `effort band` was ever
built. This computes one from the user's own past rows: the median measured
per practice across the weekly archives, written to typical_time.json for the
look behind builder to read.

A practice needs FLOOR observations before it gets a median. Below that the
row keeps nothing and the builder falls back to nothing at all — the minutes
stay unestimated and the pie says so. A flagged estimate beats a clean guess;
no estimate beats an invented one.

    python3 typical_time.py <archive_dir> [out.json]

<archive_dir> holds one folder per weekly base, each with a stream CSV.
"""
import csv, glob, json, os, statistics, sys, datetime as dt

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bedo_common import norm  # noqa: E402  the one naming rule, shared

FLOOR    = 3        # fewer observations than this and the practice is left out
# The user's word, 2 Oct 2026: use the medians, all of them. A median shrugs off the odd
# row (hips 2, 6, 7, 10, 12 and one 60 still reads 8), so there is no spread gate;
# the spread is reported so a wide one can be seen, and the page draws every
# estimate striped.
# These never get a typical length: a row of one with no end is a check-in, a
# status change or a container, not a stretch of that length. Driving too, the
# user's word 2 Oct 2026: the commute and each standing route are their own length, and
# one number for every drive is wrong; drives carry real ends from Timeline.
EXCLUDE  = {"action", "calendar event", "location", "capture", "log", "sleep",
            "driving", "text"}
MAX_MIN  = 24 * 60  # a span longer than a day is a data error, not a duration
NOSCORE  = {"▫️potential", "⬜ intention", "✖️ dropped"}

# The CSV export writes datetimes as display text in the user's local zone
# ("September 7, 2026 9:55am"), not ISO. Only `created` is ISO UTC. Both
# ends of a row share a zone, so a duration is right either way.
_FMTS = ("%B %d, %Y %I:%M%p", "%B %d, %Y %I:%M %p", "%b %d, %Y %I:%M%p")


def parse_dt(s):
    s = (s or "").strip()
    if not s: return None
    try:
        return dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        pass
    t = s[:-2] + s[-2:].upper() if s[-2:].lower() in ("am", "pm") else s
    for f in _FMTS:
        try:
            return dt.datetime.strptime(t, f)
        except ValueError:
            continue
    return None


def parse_spent(s):
    s = (s or "").strip()
    if not s or ":" not in s: return None
    try:
        h, m = s.split(":")[:2]
        return int(h) * 60 + int(m)
    except ValueError:
        return None


def collect(archive_dir):
    obs, files, rows_read = {}, [], 0
    for path in sorted(glob.glob(os.path.join(archive_dir, "*", "stream*.csv"))):
        files.append(os.path.basename(os.path.dirname(path)))
        with open(path, encoding="utf-8-sig", newline="") as fh:
            for r in csv.DictReader(fh):
                rows_read += 1
                if (r.get("status") or "").strip() in NOSCORE:
                    continue                      # a plan is not a lived duration
                name = norm(r.get("practice text"))
                if not name:
                    continue
                a, b = parse_dt(r.get("datetime")), parse_dt(r.get("end datetime"))
                if a and b:
                    mins = round((b - a).total_seconds() / 60)
                else:
                    mins = parse_spent(r.get("time spent"))
                if mins is None or mins <= 0 or mins > MAX_MIN:
                    continue
                obs.setdefault(name, []).append(mins)
    return obs, files, rows_read


def main():
    archive_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    out_path    = sys.argv[2] if len(sys.argv) > 2 else "typical_time.json"
    obs, files, rows_read = collect(archive_dir)

    # A median is only worth having where the user's own history is consistent.
    # practices swing by two orders of magnitude depending on the day, and a
    # "typical" one of those is not a thing. Spread is the interquartile range
    # over the median: tight keeps the estimate, wide drops the practice and
    # the row stays a moment on the page.
    def spread(v):
        med = statistics.median(v)
        if not med: return 99.0
        q = statistics.quantiles(v, n=4)
        return (q[2] - q[0]) / med

    kept = {n: v for n, v in obs.items() if len(v) >= FLOOR and n not in EXCLUDE}
    doc = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "floor": FLOOR,
        "excluded": sorted(EXCLUDE),
        "window": files,
        "rows_read": rows_read,
        "practices_with_any_duration": len(obs),
        "practices": {
            n: {"median_min": int(statistics.median(v)), "n": len(v),
                "low": min(v), "high": max(v),
                "spread": round(spread(v), 2)}
            for n, v in sorted(kept.items())
        },
    }
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=1)
    print(f"read {rows_read} rows from {len(files)} archives")
    print(f"{len(obs)} practices carry at least one real duration")
    print(f"{len(kept)} have {FLOOR}+ observations and are kept")
    for n, d in sorted(doc["practices"].items(), key=lambda kv: -kv[1]["n"]):
        print(f"  {d['n']:4d}  {d['median_min']:5d} min  "
              f"spread {d['spread']:.2f}   {n}   ({d['low']}-{d['high']})")

if __name__ == "__main__":
    main()
