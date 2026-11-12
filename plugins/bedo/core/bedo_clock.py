# -*- coding: utf-8 -*-
"""The one clock. Every script that turns a UTC instant into her local time,
or a local day into UTC, does it here, from the settings' `time_zone`.

`utc_offset_hours` was kept by hand and went stale twice a year (1 Nov 2026,
and again on 10 Nov when the day ahead's copy still said -5). The offset is
now worked out from the zone for the instant or the day in hand, so a night
that straddles a change reads each end on its own clock. The fixed number is
only a fallback for a machine with no zone database, or settings with no
`time_zone`.

Nothing personal lives here, and nothing here imports the rest of the core,
so any script can carry it.
"""
import datetime as dt

UTC = dt.timezone.utc


def zone(local):
    """The settings' time zone as a tzinfo, or None when it can't be read."""
    tz = (local or {}).get('time_zone')
    if not tz:
        return None
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(tz)
    except Exception:
        return None


def fallback_hours(local):
    return float((local or {}).get('utc_offset_hours') or 0)


def _aware(t):
    return t.replace(tzinfo=UTC) if t.tzinfo is None else t


def offset_hours(local, when_utc):
    """The local UTC offset, in hours, at a UTC instant (aware, or naive UTC).
    `local` may also be a plain number — an offset already worked out — which
    is returned as it is, and an Offset is read through, so code that takes
    any of them keeps one path."""
    if isinstance(local, Offset):
        local = local.local
    if isinstance(local, dt.timedelta):
        return local.total_seconds() / 3600
    if isinstance(local, (int, float)):
        return float(local)
    z = zone(local)
    if z is not None:
        return _aware(when_utc).astimezone(z).utcoffset().total_seconds() / 3600
    return fallback_hours(local)


def offset(local, when_utc):
    """offset_hours as a timedelta."""
    return dt.timedelta(hours=offset_hours(local, when_utc))


def parse(ts):
    """An ISO time ('...Z' or with an offset) as an aware UTC datetime; None for blank."""
    if not ts:
        return None
    if isinstance(ts, dt.datetime):
        return _aware(ts).astimezone(UTC)
    return _aware(dt.datetime.fromisoformat(str(ts).replace('Z', '+00:00'))).astimezone(UTC)


def to_local(local, when_utc):
    """A UTC instant (aware, naive UTC, or an ISO string) as a naive local
    datetime, on the clock that held at that instant."""
    t = parse(when_utc)
    if t is None:
        return None
    return (t + offset(local, t)).replace(tzinfo=None)


def to_utc(local, naive_local):
    """A naive local wall time as an aware UTC datetime, on the clock that held
    then. In the repeated hour of a fall-back the first (daylight) reading is
    taken; in the skipped hour of a spring-forward, the standard one."""
    if isinstance(local, Offset):
        local = local.local
    if isinstance(local, dt.timedelta):
        local = local.total_seconds() / 3600
    if isinstance(local, (int, float)):
        return (naive_local - dt.timedelta(hours=local)).replace(tzinfo=UTC)
    z = zone(local)
    if z is not None:
        return naive_local.replace(tzinfo=z).astimezone(UTC)
    return (naive_local - dt.timedelta(hours=fallback_hours(local))).replace(tzinfo=UTC)


def day_start_utc(local, day):
    """Local midnight at the start of `day`, as an aware UTC datetime."""
    return to_utc(local, dt.datetime.combine(day, dt.time()))


def day_bounds_utc(local, day):
    """[start, end) of the local day in UTC — 23 or 25 hours on a change day."""
    return day_start_utc(local, day), day_start_utc(local, day + dt.timedelta(days=1))


def offset_on(local, day):
    """The offset that holds at local noon on `day` — the day's own clock, for
    a figure that is one per day (a page's header, a week's columns)."""
    return offset_hours(local, to_utc(local, dt.datetime.combine(day, dt.time(12))))


def now_local(local, now_utc=None):
    """The local wall clock now (or at now_utc), naive, to the minute."""
    t = now_utc or dt.datetime.now(UTC)
    return to_local(local, t).replace(second=0, microsecond=0)


def iso_offset(hours):
    """-6 → '-06:00'."""
    sign = '-' if hours < 0 else '+'
    h = abs(hours)
    return f'{sign}{int(h):02d}:{int(round((h % 1) * 60)):02d}'


class Offset:
    """Stands where a fixed `dt.timedelta(hours=utc_offset_hours)` used to, and
    works out the offset from the instant it meets:

        utc_instant + off   → that instant on the local clock (tzinfo kept as given)
        local_wall  - off   → that wall time back in UTC     (tzinfo kept as given)

    A naive or UTC-stamped datetime on the left is read as UTC for `+` and as
    a local wall time for `-`, which is what the old timedelta arithmetic
    meant. So a night across the 1 Nov change reads its start at -5 and its
    end at -6, where the fixed number read both on one clock."""

    def __init__(self, local):
        self.local = local

    def __radd__(self, t):
        if not isinstance(t, dt.datetime):
            return NotImplemented
        return t + offset(self.local, t)

    def __rsub__(self, t):
        if not isinstance(t, dt.datetime):
            return NotImplemented
        u = to_utc(self.local, t.replace(tzinfo=None))
        return u if t.tzinfo is not None else u.replace(tzinfo=None)

    def hours(self, when_utc):
        return offset_hours(self.local, when_utc)

    def __repr__(self):
        return f'Offset({(self.local or {}).get("time_zone") if isinstance(self.local, dict) else self.local!r})'


def tzinfo(local):
    """A tzinfo for `.astimezone(...)`: the zone itself when it can be read, so
    every instant takes its own offset; else the fixed fallback offset. A plain
    number is taken as a fixed offset."""
    if isinstance(local, Offset):
        local = local.local
    if isinstance(local, dt.timedelta):
        return dt.timezone(local)
    if isinstance(local, (int, float)):
        return dt.timezone(dt.timedelta(hours=local))
    return zone(local) or dt.timezone(dt.timedelta(hours=fallback_hours(local)))


def problem(local):
    """Why no clock can be had from these settings, or None. A readable
    time_zone is enough; without one, the fixed utc_offset_hours is the
    fallback, and with neither every time would be read as UTC."""
    if zone(local) is not None:
        return None
    if (local or {}).get('utc_offset_hours') is not None:
        return None
    tz = (local or {}).get('time_zone')
    return (f"time_zone {tz!r} can't be read here and there is no utc_offset_hours to fall back on"
            if tz else 'time_zone is missing (America/Chicago, say)')
