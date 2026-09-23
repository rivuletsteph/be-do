# -*- coding: utf-8 -*-
"""The day pie — twenty-four hours, every minute in exactly one slice.

Carried over from the standalone pie with two changes the canon asks for:

  · five slices, not seven. The categories come from the local settings file,
    so the practice-to-slice map is the user's and never appears here.
  · striped means ESTIMATED, not doubled. A row with a real span paints its
    minutes and those minutes are logged. A row with no end gets its typical
    time instead, which is counted, stated, and drawn striped by the engine —
    never presented as logged.

Twenty-four hours is the cap. When two rows are open at once the earlier slice
in the category order wins the minute, so nothing is split in half and nothing
is counted twice. What no row covers is the rest slice, which the engine fills
out to the remainder of the day.
"""

DAY_MINUTES = 1440


def containers(rows, span_min=240, inside_min=3):
    """A container HOLDS other rows — four hours or more with at least three
    moments inside it. A trip, a field day, a dawn-to-dusk session: an envelope,
    not an activity. It scores nothing, on the pie or on the wheel.

    rows: dicts carrying 's' and 'e' in minutes from midnight ('e' may be None).
    Returns (kept, held)."""
    starts = sorted(r["s"] for r in rows if r.get("s") is not None)
    kept, held = [], []
    for r in rows:
        s, e = r.get("s"), r.get("e")
        if s is None or e is None:
            kept.append(r)
            continue
        inside = sum(1 for t in starts if s < t < e)
        (held if (e - s >= span_min and inside >= inside_min) else kept).append(r)
    return kept, held


def paint(rows, order):
    """One minute, one slice. Lowest precedence first, so the higher one
    overwrites it — `order` is the category keys, most specific first.

    rows: dicts with 'cat', 's', 'e' (minutes from midnight; 'e' None = no span).
    Returns a list of 1440 category keys or None."""
    slice_of = [None] * DAY_MINUTES
    for cat in reversed(order):
        for r in rows:
            if r.get("cat") != cat or r.get("s") is None or not r.get("e"):
                continue
            for m in range(max(0, r["s"]), min(DAY_MINUTES, r["e"])):
                slice_of[m] = cat
    return slice_of


def build(rows, cats, max_titles=4):
    """The DATA.pie list, in the shape the engine reads.

    cats: ordered list of {'k','e','n','c'} with the rest slice last, carrying
    'rest': True. Precedence runs down the list.
    rows: dicts with 'cat', 's', 'e', 'est' (estimated minutes for a row with
    no span) and 'title'.

    Returns (pie, trimmed) — trimmed is the estimated minutes dropped to keep
    the day inside twenty-four hours, and is reported rather than hidden."""
    order = [c["k"] for c in cats if not c.get("rest")]
    slice_of = paint(rows, order)

    logged = {k: 0 for k in order}
    for k in slice_of:
        if k:
            logged[k] += 1

    est = {k: 0 for k in order}
    for r in rows:
        if r.get("cat") in est and not r.get("e") and r.get("est"):
            est[r["cat"]] += r["est"]

    # Twenty-four hours is the cap, and an estimate is the part that gives.
    # A logged minute is measured; an estimated one is inferred, so when the
    # two together overrun the day the estimates are trimmed, proportionally,
    # and the builder says how many minutes went.
    room = DAY_MINUTES - sum(logged.values())
    want = sum(est.values())
    trimmed = 0
    if want > room:
        keep = max(0, room)
        scale = (keep / want) if want else 0
        scaled = {k: int(v * scale) for k, v in est.items()}
        trimmed = want - sum(scaled.values())
        est = scaled

    titles = {k: [] for k in order + [c["k"] for c in cats if c.get("rest")]}
    for r in rows:
        k, t = r.get("cat"), (r.get("title") or "").strip()
        if k in titles and t and t not in titles[k]:
            titles[k].append(t)

    pie = []
    for c in cats:
        k = c["k"]
        d = {"k": k, "e": c.get("e", ""), "n": c.get("n", k), "c": c.get("c", "#B9B5C4"),
             "logged": 0 if c.get("rest") else logged.get(k, 0),
             "est": 0 if c.get("rest") else est.get(k, 0),
             "w": c.get("w") or ", ".join(titles.get(k, [])[:max_titles])}
        if c.get("rest"):
            d["rest"] = True          # the engine fills its minutes out to the day
        pie.append(d)
    return pie, trimmed
