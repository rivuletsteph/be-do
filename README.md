# be•do

Builders for the be•do pages. Each one is a self-contained skill folder under
`plugins/bedo/skills/` — the builder, the page engine and the settings travel
together, so a skill runs in any project or none.

| page | folder | settings |
|---|---|---|
| the day ahead | `bedo-day-ahead` | `day_ahead_local.json` |
| the day behind | `bedo-look-behind` | `look_behind_local.json` |

This repository is the version store: skill work happens here and nowhere else,
and the settings files in the table above are gitignored — they hold one
person's own ids and never ship.

## Local settings — `day_ahead_local.json`

Nothing personal lives in the builder or the engine. Names, calendar labels,
Airtable ids, the clock offset and the published page's link all come from
`day_ahead_local.json`, which is gitignored and never shared.

`plugins/bedo/skills/bedo-day-ahead/assets/day_ahead_local.example.json` is the
same file with every value blanked. Copy it to `day_ahead_local.json` and fill
it in. A missing field id or clock offset aborts the build on purpose: a blank
id reads every row as empty, and the page would look calm and be wrong.

Most keys say what they are. These four don't:

**`week_word_title`** — a regular expression, not a title. It finds the row that
carries the week's word and captures the word itself in group 1, so it needs
exactly one capture group. The newest matching row in the stream wins. Example:
`^Weekly intention — (.+)$` matches a row titled *Weekly intention — steady* and
captures *steady*.

**`week_zero_sunday`** — a `YYYY-MM-DD` date, and it must be a Sunday. This is
the anchor for week numbering, not the first week of anything. The builder
counts whole weeks from this date and adds `week_zero_number` to get the W## on
the page's chip, so the pair has to agree: if `week_zero_sunday` is the Sunday
that began W19, then `week_zero_number` is 19. Get either wrong and every week
number on every page is off by the same amount.

**`map_end`** — a `YYYY-MM-DD` date, the right-hand edge of the map that draws
each drive running out to what it serves. It bounds the drawing only; it doesn't
filter rows or affect the three. Usually the end of the current year. Move it
when the map starts to feel cramped or too sparse.

**`weighing_phrases`** — regular expressions for the way the user says something
is weighing on them, used to lift a sentence out of a row's details when the
page explains why a pick matters. Write them as patterns, not literal
sentences, so tense and person vary without needing a new entry: `weigh(s|ing)? on me` catches
*weighs on me* and *weighing on me* both. Matching is case-insensitive. An empty
list is valid — the page just won't quote the user back to themselves.


# The day behind — `plugins/bedo/skills/bedo-look-behind/`

The canon build settled 21 Sep 2026. `assets/look_behind_engine.html` is that
page byte for byte, with its `DATA` literal replaced by a `/*__DATA__*/null`
placeholder; `scripts/look_behind.py` fills it. Nothing about the layout is the
builder's business, and nothing personal is the engine's.

Two sections are not computed. **The lead and the story are the user's**,
written in the chat from the day's rows and passed in through `--words`. The
builder refuses to build without them rather than ship a page with a hole where the
day's own account of itself should be.

## Local settings — `look_behind_local.json`

Same rule as the day ahead, and the same abort on a missing field id.
`assets/look_behind_local.example.json` is the blank shape. Most keys say what
they are. These five don't:

**`effort_minute_divisor`** — the scale that puts minutes and effort bands in
the same units on the wheel. A row with a real span contributes its minutes over
this number; a row that holds no time contributes its practice's effort band.
**Six**, by the user's amendment: an hour of something weighs ten and a logged
moment weighs its band. It changes the wheel's proportions and the
BE/tending/growing bar, and nothing else — but it changes every one of them, so don't move it
without a reason.

**`zero_when_person_excludes_self`** — when true, a row that names people and
doesn't name `self_person` is somebody else's own row kept in the user's stream,
and is out of the wheel and the pie both. A child's sleep row is the case this
exists for. Rows with no person on them are always the user's.

**`zero_practices` / `zero_practice_groups`** — practices that happened but are
not effort, named one at a time or a whole catalogue group at once. Sleep is the
one that matters: it scores zero on the wheel and its minutes are still logged
on the pie, because the hours happened. This is not the same as a plan, which
never happened at all and is excluded everywhere by `noscore_statuses`.

**`growing_types`** — the rhythm types that count as growing on the doing side.
Everything else there is tending, **including a row carrying no bucket at all**,
because an unnamed doing hour was the floor being held up. Tending is the
default rather than something a row earns, and that is what makes the bar add
up: every doing row lands in one of the two, so the page is never left with a
remainder to draw as something else.

**`device_slice` / `device_off`** — the screen is a property of the row, not of
the practice, so the stream's device field decides the screen slice. `device_off`
lists the device values that mean no screen. A row the practice map already
placed keeps its slice: eating in front of the television is still eating.

**`pie`** — the five slices, in precedence order, with the practices that fall in
each. When two rows are open at once the earlier slice wins the minute. The last
entry carries `"rest": true` and is the remainder of the day; it lists no
practices. A slice may pin a fixed `w` phrase instead of letting the builder
name it from the day's row titles.

## Who was in your day

The circles are **not** a setting. They are read live from the connections
table as a fourth saved read, alongside the stream, the rhythms and the
practices. A person sits in several circles and the first one listed is the one
they are grouped by; `circle_order` in the settings decides which circle comes
first on the page, and people fall back to order of appearance inside a circle.
Matching is on the full name or the short one with any glyph stripped, because
the stream's person field carries whichever one the user typed.

## Estimates

`scripts/typical_time.py` reads the weekly CSV archives and writes
`typical_time.json`: the median measured duration per practice, kept only where
there were at least five observations and the spread was tight. A row with no
end gets that median; a practice with no median gets no estimate at all. The
engine draws estimates striped and states the total, and the builder reports how
many estimated minutes it had to trim to keep the day inside twenty-four hours.

## Tests

One per skill. Both are plain scripts: no test runner, no dependencies.

`python3 plugins/bedo/skills/bedo-look-behind/tests/test_canon.py` builds a
fixture backwards from the canon page and checks every computed section against
it. The numbers in that fixture are the canon's; every name and sentence is an
obvious invention. Run it after any change to the look behind builder.

`python3 plugins/bedo/skills/bedo-day-ahead/tests/test_clock.py` runs the day
ahead builder over a small fixture and checks the times it writes — 9:30a, 2p,
ends 1am, through Sun 27 Sep. Those were once built with `%-I` and `%-d`, which
are a GNU extension and raise on Windows, so run this first on any machine the
builder hasn't run on before.
