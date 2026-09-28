#!/usr/bin/env bash
# The Day Behind in two commands. Nothing about the rows passes through the chat
# except the digest the lead and story are written from.
#
#   bash run_look_behind.sh prep  YYYY-MM-DD           # fetch + print the day's digest
#   bash run_look_behind.sh build YYYY-MM-DD <secure>  # after words.json is written
#
# Needs, in the working folder: bedo_fetch.py, day_digest.py, bedo_secrets.json,
# look_behind_local.json. The builder and engine come fresh from the version store
# every run.
#
# Runs anywhere. Three things differ by machine, and each is an override:
#   LB_DIR    the working folder          (default /home/claude/lb)
#   LB_LOCAL  where look_behind_local.json is copied from, if not already in place
#   LB_OUT    where the finished page is also copied (skipped if it can't be made)
# python3 is used when present, otherwise python.
set -euo pipefail
MODE=${1:-}; DAY=${2:-}; SECURE=${3:-}
W=${LB_DIR:-/home/claude/lb}; cd "$W"

# Windows ships a python3.exe stub that exists but refuses to run, so prove the
# interpreter works rather than trusting that it is on the path.
PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 || continue
  "$c" -c 'import sys' >/dev/null 2>&1 || continue
  PY=$c; break
done
[ -n "$PY" ] || { echo "no working python found (tried python3, python, py)"; exit 1; }

need_local() {
  # the settings file carries every key the builder needs; nothing is merged at run time
  [ -f look_behind_local.json ] && return 0
  if [ -n "${LB_LOCAL:-}" ] && [ -f "$LB_LOCAL" ]; then cp "$LB_LOCAL" look_behind_local.json; return 0; fi
  for c in /root/.claude/skills/synced/*/bedo-look-behind/assets/look_behind_local.json; do
    [ -f "$c" ] && { cp "$c" look_behind_local.json; return 0; }
  done
  echo "look_behind_local.json not found in $W — put it there or set LB_LOCAL"; exit 1
}

if [ "$MODE" = prep ]; then
  need_local
  rm -rf be-do-main
  git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main
  S=be-do-main/plugins/bedo/skills/bedo-look-behind
  rm -rf scripts && cp -r $S/scripts . && cp $S/assets/look_behind_engine.html .
  # an escape hatch: anything in overlay/ wins over the version store for this run
  if [ -d overlay ]; then cp overlay/look_behind.py scripts/ 2>/dev/null || true
    cp overlay/look_behind_engine.html . 2>/dev/null || true; fi
  rm -rf data
  "$PY" bedo_fetch.py --day "$DAY" --local look_behind_local.json --secrets bedo_secrets.json --out data
  STREAMS=$(ls -r data/w*.json | sed 's/^/--stream /' | tr '\n' ' ')
  "$PY" day_digest.py --day "$DAY" --local look_behind_local.json $STREAMS --width 130
elif [ "$MODE" = build ]; then
  need_local
  STREAMS=$(ls -r data/w*.json | sed 's/^/--stream /' | tr '\n' ' ')
  "$PY" scripts/look_behind.py --day "$DAY" --local look_behind_local.json $STREAMS \
    --rhythms data/rhythms.json --practices data/practices.json --connections data/connections.json \
    --words words.json --template look_behind_engine.html \
    --out "$DAY-day-behind.html" --secure "$SECURE"
  OUT=${LB_OUT:-/mnt/user-data/outputs}
  if mkdir -p "$OUT" 2>/dev/null; then cp "$DAY-day-behind.html" "$OUT/"
    echo "also copied to $OUT/"; fi
else
  echo "usage: run_look_behind.sh prep|build YYYY-MM-DD [secure]"; exit 2
fi
