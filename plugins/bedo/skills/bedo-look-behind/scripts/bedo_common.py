# -*- coding: utf-8 -*-
"""Pieces the be•do builders share. Nothing personal lives here.

Three kinds of thing:
  · reading a saved Airtable dump, and refusing a partial one
  · naming a practice the same way everywhere, so the same practice is one
    practice however its glyph drifts
  · colour, derived rather than listed
"""
import colorsys, datetime as dt, json, re, sys

# Practice names drift — '⚡action' and '⚡ action' are one practice. Key on the
# word, never the glyph, or the drift splits the pool in two. One copy of this,
# imported everywhere, or two builders disagree about what a practice is called.
_LEAD = re.compile(r"^[^\w]+", re.UNICODE)


def norm(p):
    return re.sub(r"\s+", " ", _LEAD.sub("", (p or "").strip())).strip().lower()


def die(msg):
    sys.exit("ABORT: " + msg)


def read_dump(path):
    """A saved tool result in a claude.ai chat is wrapped: [{"text": "<json>"}].
    Accept that as-is, so the chat can pass the saved file straight in."""
    d = json.load(open(path, encoding="utf-8"))
    if isinstance(d, list) and d and isinstance(d[0], dict) and "text" in d[0]:
        d = json.loads(d[0]["text"])
    return d


def complete(path):
    """Records, and how many. A short read is not a read (I11)."""
    d = read_dump(path)
    recs = d.get("records")
    if recs is None:
        die(f"{path}: no records key — is this an Airtable read?")
    tot = (d.get("metadata") or {}).get("totalRecordCount")
    if tot is None or len(recs) != tot:
        die(f"{path}: {len(recs)} of {tot} records — a truncated read is not a read (I11)")
    return recs, len(recs), (d.get("metadata") or {})


def sv(v):
    """A select cell arrives as {"name": …}; everything else as itself."""
    return v.get("name") if isinstance(v, dict) else v


def weekno(day, zero_sunday, zero_number):
    """Weeks open on Sunday, anchored on one known week, so it holds forward
    and back. The anchor pair lives in the local settings file."""
    return zero_number + (day - dt.date.fromisoformat(zero_sunday)).days // 7


# ── colour, derived ───────────────────────────────────────────────────────
# One rule for the page: a mark's outline is its own colour, a couple of shades
# down. Listing both shades by hand is how they drift apart.
def darker(hex_c, drop=0.17):
    r, g, b = (int(hex_c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, max(0.0, l - drop), s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def lighter(hex_c, lift=0.07):
    r, g, b = (int(hex_c[i:i + 2], 16) / 255 for i in (1, 3, 5))
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    r, g, b = colorsys.hls_to_rgb(h, min(1.0, l + lift), s)
    return "#%02X%02X%02X" % (round(r * 255), round(g * 255), round(b * 255))


def shade(hex_c, facing_in):
    """be keeps the deep shade, do takes the pale one, one step lighter."""
    return hex_c if facing_in else lighter(hex_c)
