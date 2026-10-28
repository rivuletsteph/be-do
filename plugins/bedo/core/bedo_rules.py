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
    'entry.bucket': 'bedo_entry + bedo_fill — every row that happened sits in a flow, a rhythm or a drive',
    'entry.open_device': 'bedo_entry + bedo_fill — an open action carries the device it will be done on',
    'entry.being_doing': "bedo_entry + bedo_fill — a drive's work takes its element; passive rest is being",
    'entry.appointment': 'bedo_entry — an appointment ahead carries its calendar event link',
    'entry.cloudy': 'bedo_entry — a cloudy morning is still due: never ⨂ skipped for the weather',
    'remaining.cloudy_light': 'bedo_remaining — on a cloudy morning the line names her bright light, by the sun-by time',
    'entry.synergy_now': 'bedo_entry — two things at once are asked about as she logs them',
    'preflight.chat_name': 'bedo_preflight — the chat-name line, lettered a, b, c',
    'preflight.base': 'bedo_preflight — the weekly base resolved by name, newest row within 36 h',
    'preflight.paper': 'bedo_preflight — an active amendment with no check is named',
    'remaining': 'bedo_remaining — the remaining list, emitted by code, one horizontal line, never a widget',
    'remaining.either_or': 'bedo_remaining — evening breaths or evening meditation: one closes both',
    'remaining.sun_by': 'bedo_remaining — morning sun names its sun-by time: an hour after sunrise or waking',
    'dusk': 'bedo_dusk_audit — the one-pass dusk list',
    'meals': "bedo_meals — each meal's prep and eating placed from context",
    'dayqa': 'bedo_dayqa — meals, gaps, movement, people, device in one list',
    'dayqa.synergy_count': 'bedo_dayqa — two things at once with no answer are counted, never asked the next day',
    'preflight.look_behind_date': "bedo_preflight — yesterday's look behind only when its log row says it was built",
    'look_behind.gate': 'look_behind — no build past 10% rows unfilled, a row over 12 h, or before dayqa was shown',
    'look_behind.people': 'look_behind — people only from rows that happened, matched on any alias',
    'look_behind.moving': 'look_behind — movement is Moving, and Moving wins the minute',
    'look_behind.play': 'look_behind — show, movie, video and game are Play, never a drive slice',
    'look_behind.doing': 'look_behind — a drive row with a span is Doing, device or not',
    'look_behind.no_sleep': 'look_behind — a morning with no sleep row is flagged',
    'look_behind.forecasts': 'look_behind + week_look_behind + bedo_split — forecasts due in the window are listed; one not yet due rides the split',
    'week_look_behind.qa_gate': "week_look_behind — no build until every day of the week has its dayqa",
    'week_look_behind.heart': 'week_look_behind — time with somebody counts toward heart too, both counted',
    'week_look_behind.coverage': 'week_look_behind — how much of each waking day the record covers',
    'week_look_behind.moved': 'week_look_behind — a row moved between bases names its original, read once',
    'dayqa.family_heart': 'bedo_dayqa — a stretch with family nothing else names is filled as heart',
    'day_ahead.chore': 'day_ahead — the look ahead plants one chore for her son',
    'calendar': 'bedo_calendar — every calendar write names its calendar and is read back',
    'calendar.purple': 'bedo_calendar — every work event is purple, colorId 3',
    'inbox.keeps': 'bedo_inbox — an automatic keep (her keep list) is never archived',
    'inbox.archive_unless': 'bedo_inbox — a sender archived by default stays only when it is about what she keeps it for',
    'inbox.nudge': 'bedo_inbox — before archiving, one line asks her to glance through the inbox',
    'dusk.photos': 'bedo_dusk_audit — photo import is a dusk-close step, named when it was not run',
    'preflight.schedule': 'bedo_preflight — the skills schedule: what is due, named at the first reply',
    'day_ahead.no_build_rows': 'day_ahead — be•do build rows stay off the day ahead',
    'stretches': "bedo_stretches — a session's time is the sum of its stretches",
    'order': 'bedo_order — the predicted flow order',
    'close': 'bedo_close — a chat closes with QA, then its session entry, then the rename to done',
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
