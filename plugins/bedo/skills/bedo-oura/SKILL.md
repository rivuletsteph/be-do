---
name: "bedo-oura"
description: "Bring Oura into the be•do stream from the Oura API: each night's sleep as a 😴 sleep row with its real times, and each morning's readiness, sleep and activity scores on the 🪐 morning oura row. Use when the user asks for Oura, sleep or readiness to be pulled in, at the morning routine before the day behind builds, or at the weekly QA when nights are missing."
---

# Oura into the stream

The user's word, 20 Oct 2026: *I want to make sure Oura gets uploaded
automatically, and I really want it to access the API.* In W42, five of seven
nights had no sleep row until the QA rebuilt them by hand from screenshots.

One script, `scripts/oura.py`, reads the Oura API (v2) for a range of days and
plans rows against what the stream already holds. **It never writes.** The plan
is rows and patches in the stream's own field ids, and the chat applies them
with the Airtable connector in one call each.

## What it plans, per day

- **sleep** — the main sleep period ending that morning (Oura's `long_sleep`)
  becomes a 😴 sleep row, in bed to out of bed. A sleep row already there for
  that night is kept; one with no end gets its end. Naps are left out.
- **morning** — readiness, sleep and activity scores, HRV, resting heart rate,
  time asleep of time in bed, efficiency, temperature and steps, as one line.
  It is appended to that day's 🪐 morning oura row with her words kept, or a new
  row is made at wake-up when there is none.
- **stress** — daytime stress and recovery, appended to the evening oura row
  when one exists.

Everything it writes says *From the Oura API* in its `[be•do]` block. Run twice,
it plans nothing new for what it already wrote.

## Run it

```
python3 scripts/oura.py --start YYYY-MM-DD --end YYYY-MM-DD \
  --local look_behind_local.json --stream data/w##.json [--stream data/w##-prev.json] --out oura-plan.json
```

The streams are the day behind's own reads (`run_look_behind.sh prep` saves
them in `data/`), live base first. It saves the raw fetch to `oura.json`;
`--oura oura.json` plans again from it without reading Oura twice. Then apply
`create` with `create_records_for_table` and `patch` with
`update_records_for_table`, both to the weekly base that holds the row's date,
and say what went in, in one line. `notes` names anything it could not place.

## Setup — once, by the user

1. **Network:** the cloud environment's settings, Network access, Allowed
   domains: add `api.ouraring.com` (package managers left ticked).
2. **The token:** create a personal access token in the Oura account, and add
   it to the environment's network secrets for `api.ouraring.com`, so the proxy
   attaches it and the session never holds it (as the Airtable token works).
   On a laptop, `OURA_PAT` or `oura_pat` in `bedo_secrets.json` instead.
3. Both reach **new** sessions only. A session opened before the change stays
   blocked; the script says *Oura unreachable* and stops.

A 401 or 403 aborts with *token missing, revoked or rotated?*. An unreachable
host aborts too. It never plans from a partial read.

## Automatic

The aim is the 03:00 morning routine running this for yesterday before the day
behind builds, so the morning page already has the night. The routine can read
Oura and plan; it writes the rows only when created from the claude.ai routines
page with the Airtable connector attached (`bedo-look-behind/MORNING.md`).

## Tests

`python3 tests/test_oura.py` — two invented mornings: a new sleep row, a missing
end filled, the scores joining her words, a nap left out, nothing planned twice.
