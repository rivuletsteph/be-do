---
name: "bedo-week-ahead"
description: "Build The My Week page — the my day page applied to a whole week. Use at the Monday plan, when the user asks for my week, the week page or the week ahead, or when a my week chat opens."
---

# The my week page

Her word, 10 Nov 2026: *build a my week page for W46 by applying my day page to
the week. Same look, same parts, made for a whole week.* The old week look
ahead (`4ZBkuSUHEGRBeWEpRL1NBZ`) is retired with it.

**This page is the my day page, over seven days.** It has no look of its own.
Everything it draws it draws with the my day page's own code:

| what | whose |
|---|---|
| the three calendars, read into day pages | `day_ahead.calendar()` |
| each day tagged the peak, open, a clash, away | `day_ahead.week_shape()` |
| the week in one line | `day_ahead.week_lead()` |
| the rows with pull — here the **possible paths** | `day_ahead.pareto()` |
| the big things coming, and what prepares them | `day_ahead.horizon()` |
| a day's cards: events, what she lived, steps at a time | `flow.schedule_of()` |
| a day's wellness wheel, and how evenly it was shared | `flow.wheel_of()`, `flow.evenness()` |
| the space between her and what's due | `flow.buffer_on()` |
| which kind of time a row was | `flow.kind_of()` |
| the shell, the card, the glyphs, the colours, the clock, the base-flow river | `plugins/bedo/assets/flow-parts` |

**Never borrow the my day page's stylesheet** (her words). What both pages share
lives in `flow-parts`, in one copy; the week's own css is only what a week needs
and a day does not — seven columns instead of one set of hours. A change to a
colour or a glyph there lands on both pages at the next build.

The palette is read off a built day-ahead page's own `:root`, so the two pages
are literally the same colours.

## The order on the page

The Monday rules in `bedo-weekly-close`, then the day page's own parts:

1. **This week's word**, first and in its own slot. Filled when she has given
   it; **empty, with candidates under it — carry-over first — when she hasn't**.
   The word is hers (J14); the page never picks one.
2. **This week's focus practice**, hers, with the days of the week a row already
   carries it. A count, never a score.
3. **What I could push this week** — the leverage list, *never a queue*, and
   **drive by drive**, because the week's unit is the drive: a day asks which
   row to do next, a week asks which stretches of trail it can move. It opens
   as a **board** — the few drives down the side, the week across the top, each
   action on the day it is due — because a week of prose is a week she will not
   read. The words come under it, one card a drive.

   Her words on the first W46 page, 9 Nov 2026: *that algorithm or whatever
   that's trying to pick the top three needs some work*. It had picked a meeting
   that was last week, a credit-card chore and a conditional chiropractor visit,
   and the four things she actually named were nowhere. So `week_push()` holds
   four rules, each one of those three complaints:

   - **a row that IS a calendar event is not an action.** A meeting that did not
     happen is still a meeting; it belongs in past its date.
   - **a row hanging straight off a rhythm is not drive work.** Her own test: a
     rhythm is the country, ongoing; a drive is a stretch of trail with a start
     and an end. Only an active `♐ drive` can lead a week.
   - **a potential row is a maybe, not an action.**
   - **a drive with no date anywhere does not lead.** The four things she named
     each had a hard date bearing down and people it affected. An undated ask
     from a colleague is a nag, not a deadline.

   A date is the entry fee, people raise it, in motion raises it, and each extra
   row adds less than the one before, so one urgent thing beats three vague ones.
   The section says in words what it left out and why, because a picker that got
   it wrong once has to show its working.

   **Her own pins come first.** `--push "<drive or code>::<why>"` puts a drive at
   the top in her words, dated or not — the rule reads the rows, it cannot read
   what she decided this morning. A drive with no date at all reaches the page
   only by her hand.

   One thing to know when a row does not surface: **a plan names its people in
   `mentioned`, never in `person`**. The day page's own `pareto()` reads
   `person` only, which is why a plan due tomorrow with two colleagues named
   on it scored nothing. `week_push()` reads both.
4. **The week on the calendar** — seven days, hers, her son's and her husband's.
   A day ahead keeps its Google colour; a day lived wears the be•do colour of
   the kind of time it was. **A day already lived folds** to what mattered —
   anything on the calendar, anything that ran 45 minutes or more, the
   highlight, anything still open — with the rest one tap under it, because
   seven days of every logged row is a wall.
5. **How the time is going** — the week so far by kind of time, as a ring, as
   bars, and as one bar a day. A day is scaled back to the hours it had: two
   things at once are two rows, so a day of rows adds up to more than it lasted,
   and no day may read 28 hours.
6. **This week's wheel, so far** — every lived row under its element, be to the
   left, do to the right. It grows as the week does.
7. **The two weeks after** — what is already on the calendar, and the horizon.
8. **The rhythms, with their drives** — what is open this week under what it
   serves, tending first, then growing.
9. **Past its date** — open and past its target, oldest first, never folded away.
10. **Base flow** — the week's own mornings, in the my day page's river. It
    stops at today: a morning that has not happened is not one.
11. **The Pareto question, last.** be•do names the one it would reach for; the
    answer is hers.

Tapping a kind of time, or an element on the wheel, lights it up through the
page — the calendar, the bars and the wheel together (her 7 Nov 2026 decision
on the day page).

## Steps

1. **Read live, complete or abort.** One command, no rows through the chat:
   ```
   LB_DIR=<working folder> bash run_week_ahead.sh prep [WEEK]
   ```
   `prep` clones the version store, reads the live weekly base and the one
   before it with the read-only token, and prints the **calendar plan**: the
   21-day window (the week's Sunday and the two weeks after) and, for each
   calendar the settings name, the exact `list_events` arguments and the file to
   save the result to. The working folder is the my day page's: the my week page
   reads `day_ahead_local.json`, the same settings, so there is one copy.
2. **The calendars, through the connector** — the one read that passes through
   the chat. `list_calendars`, then `list_events` for **every** calendar the
   settings name, saved where the plan says. Then:
   ```
   bash run_week_ahead.sh cal [WEEK]
   ```
   writes `calweek.json` and prints one line per event. **Read those lines
   against the calendar before building.** A one-calendar read is how an
   appointment kept only on the child's calendar went unseen.
3. **Build.**
   ```
   bash run_week_ahead.sh build [WEEK] --word "…" --focus "…" \
     [--push "<drive or code>::<why>"] [--pick "<key>::<why>"]
   ```
   `--word`, `--focus` and `--push` are hers, passed when the chat has them and
   the rows do not; without them the builder reads her own rows and, failing that,
   leaves the slot empty with candidates. `--pareto` rewords the question in her
   words. Everything after the week goes to `scripts/week.py` unchanged.
4. **Publish** to the week's own page, favicon 📅, and put the link on the
   week's planning row as its deliverable — the way the day page keeps its link
   on the 👁️ look ahead row. A rebuild later in the week republishes to the same
   link.
5. **Say in the chat** what the page can't: the lead line, the paths worth her
   minute, and anything the calendar flagged as a clash. Then **one numbered
   list** of everything that is hers. The page holds the rest.

## The files

- `run_week_ahead.sh` — the runner: `prep` · `cal` · `fetch` · `build`
- `scripts/week.py` — the reader and builder; imports the day page's own scripts
- `assets/week_engine.html` — the page; nothing personal in it
- `tests/test_week.py` — drives the builder over a small fixture and checks the
  week it writes: the seven days, the word's slot, the paths, the two weeks
  after, base flow stopping at today, and the a-or-p clock

There is no `week_local.json`. The my week page reads the my day page's
settings, so a setting is changed in one place.

## What is hers

The week's word · her one focus practice · **which drives she pins** · which
path she takes · the answer to the Pareto question. The page proposes; it never
decides. (J14.)

## On night sight

Her palette (6 Nov 2026) holds the eight kinds of time at one lightness, which
reads on either ground — except sleep, a night indigo on purpose, and a thin bar
of night indigo on a dark ground is nothing at all (her words on the first W46
page: *I can't see the colors very well because I've got it kind of on night
sight*). So on night, and only in how this page draws them, a colour that does
not clear the ground is lifted towards white until it does — one measured rule,
no hand-picked exceptions. **Her palette itself is untouched**, and light mode is
unchanged. The my day page draws sleep the same dark way and has not been
changed; that is hers to call.

## Build from the stable release

Changes to the layout are a be•do work chat that ends with a push to
`github.com/rivuletsteph/be-do`. After any change to a shared part, run
`plugins/bedo/assets/flow-parts/tests/test_parts.py`: it fills both engines and
hands every script block to `node --check`, because a brace that moves between
files is invisible to a diff and fatal to a page.
