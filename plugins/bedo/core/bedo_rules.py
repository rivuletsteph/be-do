# -*- coding: utf-8 -*-
"""What the code enforces, by name, so preflight can say which active
amendments are still a rule on paper only (9 Oct 2026: *why on Earth did all
this get skipped before?*).

CHECKS names every check the core and the builders run. Which amendment each
one enforces is hers, keyed by the amendment's record id, so it lives in
facts_local.json, never here:

    "amendment_checks": {
      "rec…": ["entry.whole", "entry.one_day", "look_behind.gate"],
      "rec…": ["judgment"]
    }

`judgment` marks a rule that needs judgment, not code (docs/v53-judgment.md
holds it). An active amendment with no entry, or whose names include one the
code doesn't have, prints as `rule on paper only`.
"""
from bedo_reader import cells, sv

CHECKS = {
    'entry.choices': 'bedo_entry — every select value is a full choice (I4)',
    'entry.key': 'bedo_entry — only an ⚡ action row carries a key, and always does',
    'entry.utc': 'bedo_entry — datetimes stored UTC with a Z (I12)',
    'entry.divider': 'bedo_entry — her words, one divider, then the [be•do] block',
    'entry.base': "bedo_entry — a row goes in its own week's base",
    'entry.day_chat': 'bedo_entry — a my day chat holds one day',
    'entry.practice': 'bedo_entry — every row carries a practice',
    'entry.whole': 'bedo_entry + bedo_fill — device and wellness at write time, deduced or asked',
    'entry.one_day': 'bedo_entry — datetime and end on one day, at most 12 h',
    'entry.plan_people': 'bedo_entry — a plan names people in mentioned, not person',
    'entry.gratitude': 'bedo_entry — gratitude is one bullet per thing',
    'entry.milestone': 'bedo_entry — a milestone names its drive',
    'preflight.chat_name': 'bedo_preflight — the chat-name line, lettered a, b, c',
    'preflight.base': 'bedo_preflight — the weekly base resolved by name, newest row within 36 h',
    'preflight.paper': 'bedo_preflight — an active amendment with no check is named',
    'remaining': 'bedo_remaining — the remaining list, emitted by code, one line',
    'dusk': 'bedo_dusk_audit — the one-pass dusk list',
    'meals': "bedo_meals — each meal's prep and eating placed from context",
    'dayqa': 'bedo_dayqa — meals, gaps, movement, people, device in one list',
    'look_behind.gate': 'look_behind — no build past 10% rows unfilled, a row over 12 h, or before dayqa was shown',
    'look_behind.people': 'look_behind — people only from rows that happened, matched on any alias',
    'look_behind.moving': 'look_behind — movement is Moving, and Moving wins the minute',
    'look_behind.play': 'look_behind — show, movie, video and game are Play, never a drive slice',
    'look_behind.doing': 'look_behind — a drive row with a span is Doing, device or not',
    'look_behind.no_sleep': 'look_behind — a morning with no sleep row is flagged',
    'day_ahead.no_build_rows': 'day_ahead — be•do build rows stay off the day ahead',
    'stretches': "bedo_stretches — a session's time is the sum of its stretches",
    'order': 'bedo_order — the predicted flow order',
}
NOT_CODE = 'judgment'


def active(recs, local):
    """[(id, date, decision)] for the active amendments in a read."""
    af = local.get('amendments_fields') or {}
    out = []
    for r in recs:
        c = cells(r)
        st = sv(c.get(af.get('status', 'status'), c.get('status')))
        if st != 'active':
            continue
        out.append((r['id'], sv(c.get(af.get('date', 'date'), c.get('date'))) or '',
                    sv(c.get(af.get('decision', 'decision'), c.get('decision'))) or ''))
    return sorted(out, key=lambda x: x[1])


def on_paper(amendments, mapping):
    """The active amendments no check in code enforces: [(id, date, decision, why)]."""
    out = []
    for rid, date, decision in amendments:
        names = (mapping or {}).get(rid)
        if not names:
            out.append((rid, date, decision, 'no check named'))
            continue
        unknown = [n for n in names if n != NOT_CODE and n not in CHECKS]
        if unknown:
            out.append((rid, date, decision, 'names a check the code lacks: ' + ', '.join(unknown)))
    return out


def lines(amendments, mapping):
    paper = on_paper(amendments, mapping)
    out = [f'rule on paper only: {d[5:] or "?"} · {dec[:70]} ({why})' for _, d, dec, why in paper]
    if mapping is None and amendments:
        out.insert(0, 'amendment_checks is not in facts_local — every active amendment reads as on paper')
    return out
