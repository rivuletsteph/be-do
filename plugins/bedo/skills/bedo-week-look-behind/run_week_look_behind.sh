#!/usr/bin/env bash
# The Week Behind in one command, the way the day behind runs.
#
#   bash run_week_look_behind.sh [YYYY-MM-DD]   # any day of the week; default: the week just closed
#
# Fetches the builder fresh from the version store, the settings from Airtable
# (be•do system › settings, the look_behind_local row — the day behind's), the
# live week and the asked week's bases, and builds the page. Nothing to upload.
#
# Overrides: LB_DIR (working folder, default /home/claude/wlb), LB_LOCAL (a
# settings file to use instead of the Airtable row), LB_OUT (where the page is
# also copied). A cloud session needs no token; elsewhere AIRTABLE_PAT or a
# bedo_secrets.json in the working folder or above it.
set -euo pipefail
DAY=${1:-}
W=${LB_DIR:-/home/claude/wlb}; mkdir -p "$W"; cd "$W"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 || continue
  "$c" -c 'import sys' >/dev/null 2>&1 || continue
  PY=$c; break
done
[ -n "$PY" ] || { echo "no working python found (tried python3, python, py)"; exit 1; }

# the week: Sunday to Saturday; with no day given, the last full week
TODAY=$("$PY" -c 'import datetime as d; print(d.date.today())')
[ -n "$DAY" ] || DAY=$("$PY" -c 'import datetime as d; t=d.date.today(); print(t - d.timedelta(days=(t.weekday()+2) % 7 or 7))')
SAT=$("$PY" -c "import datetime as d; x=d.date.fromisoformat('$DAY'); print(x + d.timedelta(days=(5 - x.weekday()) % 7))")

rm -rf be-do-main
git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main
S=be-do-main/plugins/bedo/skills
rm -rf scripts && mkdir scripts
cp $S/bedo-week-look-behind/scripts/*.py $S/bedo-look-behind/scripts/bedo_fetch.py scripts/
cp be-do-main/plugins/bedo/core/*.py be-do-main/plugins/bedo/core/facts.json scripts/
cp $S/bedo-week-look-behind/assets/week_look_behind_engine.html .
if [ -d overlay ]; then cp overlay/*.py scripts/ 2>/dev/null || true
  cp overlay/week_look_behind_engine.html . 2>/dev/null || true; fi

# settings: LB_LOCAL if given, else the Airtable row, else the installed day behind's copy
if [ -n "${LB_LOCAL:-}" ] && [ -f "$LB_LOCAL" ]; then cp "$LB_LOCAL" look_behind_local.json
elif ! "$PY" scripts/bedo_settings.py look_behind_local --out look_behind_local.json; then
  for c in /root/.claude/skills/synced/*/bedo-look-behind/assets/look_behind_local.json; do
    [ -f "$c" ] && { cp "$c" look_behind_local.json; break; }
  done
fi
[ -f look_behind_local.json ] || { echo "no settings: the Airtable row and the installed copy are both out of reach"; exit 1; }

SECARGS=()
for c in "${BEDO_SECRETS:-}" bedo_secrets.json ../bedo_secrets.json; do
  [ -n "$c" ] && [ -f "$c" ] && { SECARGS=(--secrets "$c"); break; }
done
# the live week first (I15), then the asked week's own bases when they are older
rm -rf data && mkdir -p data/live data/week
"$PY" scripts/bedo_fetch.py --day "$TODAY" --local look_behind_local.json "${SECARGS[@]}" --out data/live
"$PY" scripts/bedo_fetch.py --day "$SAT" --local look_behind_local.json "${SECARGS[@]}" --out data/week
for f in data/week/w*.json; do if [ -f "data/live/$(basename "$f")" ]; then rm "$f"; fi; done   # a base read twice is read once
STREAMS=$( { ls -r data/live/w*.json; ls -r data/week/w*.json 2>/dev/null || true; } | sed 's/^/--stream /' | tr '\n' ' ')

OUTF="$SAT-week-behind.html"
"$PY" scripts/week_look_behind.py --week "$DAY" --local look_behind_local.json $STREAMS \
  --rhythms data/live/rhythms.json --template week_look_behind_engine.html --out "$OUTF"
OUT=${LB_OUT:-/mnt/user-data/outputs}
if mkdir -p "$OUT" 2>/dev/null; then cp "$OUTF" "$OUT/"; echo "also copied to $OUT/"; fi
