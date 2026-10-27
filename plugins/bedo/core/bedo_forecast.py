# -*- coding: utf-8 -*-
"""🔭 forecasts (20 Oct 2026): a forecast is one stream row in her words — what
she thinks will happen — with the day it comes due as its target. Nothing
else is required: no score, no percentages. Every look behind (day, week,
month) lists the forecasts due in its window, and she says in her own words
how each turned out.

A forecast is a ● log, not an open action, so the weekly split would leave it
behind in the old base; carry() keeps one whose day hasn't come in the new
base, so the look behind of its day can find it.

`row` uses the logical names: practice, title, target, datetime.
"""
import datetime as dt

from bedo_reader import FACTS

FC = FACTS['forecast']


def _word(p):
    import bedo_fill
    return bedo_fill.word(p)


def is_forecast(row):
    t = (row.get('title') or '').strip().lower()
    return _word(row.get('practice')) in {_word(p) for p in FC['practices']} or t.startswith(FC['title_prefix'])


def _utc(s):
    return dt.datetime.fromisoformat(s.replace('Z', '+00:00')) if s else None


def due_in(rows, start, end):
    """The forecasts whose target falls in [start, end) — UTC instants."""
    out = []
    for r in rows:
        t = _utc(r.get('target'))
        if t and is_forecast(r) and start <= t < end:
            out.append(r)
    return sorted(out, key=lambda r: r['target'])


def ahead(row, first_new_day, offset_hours):
    """A forecast whose day has not come by the new week's first day: it rides
    the split into the new base."""
    t = _utc(row.get('target'))
    return bool(t and is_forecast(row) and (t + dt.timedelta(hours=offset_hours)).date() >= first_new_day)


def line(row):
    """The QA line for a forecast that has come due: hers to say how it went."""
    t = (row.get('title') or '').strip()
    return f'{t} — due now: ask her, in her own words, how it turned out'
