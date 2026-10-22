---
name: "bedo-oura"
description: "Bring Oura into the be•do stream from the Oura API, morning and evening. Morning: the night as a 😴 sleep row with its real times, and readiness with what made it (recovery index, HRV balance, resting heart rate, temperature), the sleep score with its stages, and the activity score on the 🪐 morning oura row. Evening: activity, steps, Oura's workouts, stress, recovery, resilience, moments and naps on the 🪐 evening oura row. Use unasked at the 🪐 morning oura and 🪐 evening oura flow steps, when the user asks for Oura, sleep, readiness, recovery or activity to be pulled in, before the day behind builds, or at the weekly QA when nights are missing."
---

# Oura into the stream, morning and evening

The user's word, 20 Oct 2026: *I want to make sure Oura gets uploaded
automatically, and I really want it to access the API.* In W42, five of seven
nights had no sleep row until the QA rebuilt them by hand from screenshots. The
same day: *recovery, sleep and activity are big.*

`scripts/oura.py` reads the Oura API (v2) for a range of days and plans rows
against what the stream already holds. **It never writes.** The plan is rows and
patches in the stream's own field ids, and the chat applies them with the
Airtable connector in one call each.

## When

- **🪐 morning oura**, in the dawn flow: `run_oura.sh morning <today>`.
- **🪐 evening oura**, in the dusk flow: `run_oura.sh evening <today>`.
- **Catch-up**: a day whose flow step was missed, or was run from the phone,
  where the script can't run: `run_oura.sh both <day> [<last day>]`. The morning
  run before the day behind builds catches up yesterday's evening this way.

Nothing waits on a clock. A scheduled catch-up on the laptop is for the user to
choose.

## What it plans

**Morning**, per day
- **sleep**: the main sleep period ending that morning (Oura's `long_sleep`)
  becomes a 😴 sleep row, in bed to out of bed. A sleep row already there for
  that night is kept, and one with no end gets its end.
- **recovery**: readiness and each of its contributors (recovery index, HRV
  balance, resting HR, body temp, sleep balance, previous night, previous day,
  activity balance) and the temperature deviation.
- **the night**: the sleep score, time asleep of time in bed, efficiency, deep,
  REM, light and awake, time to fall asleep, HRV, resting HR, breathing rate,
  SpO2 and breathing disturbance.
- **activity**: the activity score, on a line of its own.

It goes on that day's 🪐 morning oura row, with her words kept. When there is no
row, a ◉ done row is made at wake-up. The week page reads `readiness NN`,
`sleep NN` and `activity NN` from this row, so those words stay as they are.

**Evening**, per day
- **activity**: the score, steps, active calories, time high, medium, low and
  sitting, inactivity alerts, and walking-equivalent distance.
- **workouts**: Oura's own workouts, written as `cycling 10:05a–10:40a`, the form
  the day QA turns into movement rows.
- **stress**: time stressed and restored, Oura's word for the day, and resilience.
- **moments**: breathing and meditation sessions.
- **heart**: cardio age and VO2 max, when Oura has them.
- **naps**: each nap of 15 minutes or more becomes its own 😴 sleep row, unless a rest or sleep row of hers already covers it, or her other rows fill that time (Oura read rest as sleep), which leaves a note instead.

It goes on that day's 🪐 evening oura row. When there is no row, a **● log** row
is made instead, never ◉ done, because the flow step stays hers to do.

Every block begins `[be•do] From the Oura API`. Run again, it **replaces its own
block** when Oura's numbers have moved, so an evening read at dusk is filled out
by the next morning's catch-up. It plans nothing when they haven't moved. When
the ring hasn't synced, the plan has a note and no row: *open the Oura app so
the ring syncs*.

## Run it

```
bash run_oura.sh morning|evening|both YYYY-MM-DD [YYYY-MM-DD]
```

It works in the day behind's folder (`OURA_DIR`, else `LB_DIR`). It takes the
scripts fresh from the version store, reads the stream with the day behind's
fetch, reads Oura, and writes `oura-plan.json`. Then apply `create` with
`create_records_for_table` and `patch` with `update_records_for_table`, both to
the weekly base that holds the row's date. Say what went in, in one line. `notes`
names anything it could not place or could not read.

By hand: `python3 scripts/oura.py --mode … --start … --end … --local
look_behind_local.json --stream data/w##.json [--stream …] --out oura-plan.json`.
It saves the raw fetch to `oura.json`, and `--oura oura.json` plans again from it
without reading Oura twice.

The cost is the stream read plus one Airtable call for the creates and one for
the patches. Airtable's free plan allows 1,000 calls a month.

## Setup: once, by the user, on the laptop

Oura ended personal access tokens at the end of 2025. The API now takes only an
app's sign-in, which the user approves once:

1. At **developer.ouraring.com/applications**, create an application. It's
   personal, and any name will do. Set the redirect URI to exactly
   `http://localhost:8765/callback`.
2. On the laptop, run `python scripts/oura_auth.py`. It asks for the app's
   Client ID and Client Secret and saves them in `~/.bedo/bedo_secrets.json`. It
   then opens Oura to approve be•do and saves the sign-in in
   `~/.bedo/oura_tokens.json`. Neither file ever ships.
3. `python scripts/oura_auth.py --check` says who is signed in and until when.

The sign-in lasts about 30 days and **renews by itself** on each run when under
two days are left. Each renewal hands back a new single-use refresh token, saved
before anything else happens. A 401 means the sign-in has ended: run
`oura_auth.py` again.

**Cloud and phone chats** can't keep a renewing sign-in. A token copied into a
cloud environment's credential for `api.ouraring.com` works until it expires,
about 30 days, and then needs copying again. So the laptop is where Oura is read
dependably, and phone flow steps are caught up by the next laptop run.

An unreachable host or a refusal on a core endpoint aborts. It never plans from a
partial read. A refusal on an extra (workouts, sessions, SpO2, resilience, cardio
age, VO2 max) is a note, and the rest still plans.

## Tests

`python3 tests/test_oura.py` runs two invented days, morning and evening. It
covers a new sleep row, a missing end filled, recovery and sleep joining her
words, an older Oura line replaced, the workout in the day QA's form, a nap as
its own row, an evening logged and not ticked, a dusk read refreshed next
morning, nothing planned twice, and the week page still reading its three scores.
