#!/usr/bin/env bash
# The Day Ahead in four commands. The Airtable rows never pass through the chat;
# the calendars do, as three small Calendar-connector calls the chat saves to disk.
#
#   bash run_day_ahead.sh prep  YYYY-MM-DD            # clone, fetch Airtable direct, print the calendar plan
#   bash run_day_ahead.sh cal   YYYY-MM-DD            # after the chat saved cal/*.json: check them, write cal.json
#   bash run_day_ahead.sh fetch YYYY-MM-DD            # Airtable only — re-read the live stream after the intention check
#   bash run_day_ahead.sh build YYYY-MM-DD <secure> [builder args…]
#        e.g. build 2026-09-28 secure --secure-words "…" --now 07:10 --intention "…" --intention "…" --intention "…"
#        (one build, the final; --draft still marks a hand-run page as "before your intentions")
#
# Needs, in the working folder: day_ahead_local.json (or LB_LOCAL pointing at it) and
# the Airtable token: bedo_secrets.json (there, in the folder above it, or at
# BEDO_SECRETS), AIRTABLE_PAT, or — in a Claude cloud session (CLAUDE_CODE_REMOTE=true)
# — none at all, because the environment's API credential is attached by the proxy
# after the request leaves the VM. Without any of those, prep still clones and prints
# the calendar plan, says the rows must come through the chat, and exits 3 — a plain
# claude.ai chat never has the token. The builder, the engine, the fetcher and the
# calendar reader come fresh from the version store on every prep.
#
# Runs anywhere. Three things differ by machine, and each is an override:
#   LB_DIR    the working folder          (default /home/claude/da)
#   LB_LOCAL  where day_ahead_local.json is copied from, if not already in place
#   LB_OUT    where the finished page is also copied (skipped if it can't be made)
# Settings live in day_ahead_local.json; nothing is merged at run time.
set -euo pipefail
MODE=${1:-}; DAY=${2:-}
W=${LB_DIR:-/home/claude/da}; mkdir -p "$W"; cd "$W"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8   # Windows python prints cp1252 by default and dies on an emoji

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
  [ -f day_ahead_local.json ] && return 0
  if [ -n "${LB_LOCAL:-}" ] && [ -f "$LB_LOCAL" ]; then cp "$LB_LOCAL" day_ahead_local.json; return 0; fi
  for c in /root/.claude/skills/synced/*/bedo-day-ahead/assets/day_ahead_local.json; do
    [ -f "$c" ] && { cp "$c" day_ahead_local.json; return 0; }
  done
  echo "day_ahead_local.json not found in $W — put it there or set LB_LOCAL"; exit 1
}

secrets_file() {
  for c in "${BEDO_SECRETS:-}" bedo_secrets.json ../bedo_secrets.json; do
    [ -n "$c" ] && [ -f "$c" ] && { echo "$c"; return 0; }
  done
  return 1
}

fetch_airtable() {
  need_local
  [ -f scripts/bedo_fetch.py ] || { echo "scripts/bedo_fetch.py missing — run prep first"; exit 1; }
  # no token is not a crash: a plain claude.ai chat never has one. Say so and let the caller carry on.
  # In a Claude cloud session there is no file either, and none is needed: the fetch sends no
  # Authorization header and the environment's API credential is attached by the proxy.
  SECARGS=()
  if SEC=$(secrets_file); then SECARGS=(--secrets "$SEC")
  elif [ -z "${AIRTABLE_PAT:-}" ] && [ "${CLAUDE_CODE_REMOTE:-}" != true ] && [ -z "${BEDO_PROXY_AUTH:-}" ]; then
    echo "NO TOKEN: bedo_secrets.json not found in $W or above it (set BEDO_SECRETS to point at one)" >&2; return 3
  fi
  rm -rf data
  "$PY" scripts/bedo_fetch.py --day "$DAY" --local day_ahead_local.json "${SECARGS[@]}" --out data
}

[ -n "$DAY" ] || { echo "usage: run_day_ahead.sh prep|cal|fetch|build YYYY-MM-DD [secure] [builder args…]"; exit 2; }

if [ "$MODE" = prep ]; then
  need_local
  rm -rf be-do-main
  git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main
  S=be-do-main/plugins/bedo/skills
  rm -rf scripts && cp -r $S/bedo-day-ahead/scripts . && cp $S/bedo-day-ahead/assets/day_ahead_engine.html .
  cp $S/bedo-look-behind/scripts/bedo_fetch.py scripts/     # the Airtable reader lives with the look behind
  cp be-do-main/plugins/bedo/core/*.py be-do-main/plugins/bedo/core/facts.json scripts/   # the one reader (I11 I15 I5)
  # an escape hatch: anything in overlay/ wins over the version store for this run
  if [ -d overlay ]; then cp overlay/*.py scripts/ 2>/dev/null || true
    cp overlay/day_ahead_engine.html . 2>/dev/null || true; fi
  RC=0; fetch_airtable || RC=$?
  [ "$RC" -eq 0 ] || [ "$RC" -eq 3 ] || exit "$RC"      # a short or failed read stops here (I11)
  rm -rf cal && mkdir cal
  "$PY" scripts/bedo_cal.py --plan --today "$DAY" --local day_ahead_local.json --dir cal
  if [ "$RC" -eq 3 ]; then
    # the builder, the engine and the calendar plan are all in place; only the rows are missing
    mkdir -p data
    echo "NO TOKEN HERE, so Airtable was not read. Read it through the chat instead (SKILL.md step 1,"
    echo "'Without the runner'): save the live week and the week before as data/w##.json and rhythms as"
    echo "data/rhythms.json in $W, then run cal and build as usual. This is the expensive path."
    exit 3
  fi
elif [ "$MODE" = cal ]; then
  need_local
  "$PY" scripts/bedo_cal.py --build --today "$DAY" --local day_ahead_local.json --dir cal --out cal.json
elif [ "$MODE" = fetch ]; then
  fetch_airtable
elif [ "$MODE" = build ]; then
  need_local
  SECURE=${3:-}; shift 3 2>/dev/null || shift $#
  [ -f cal.json ] || { echo "cal.json missing — run cal first"; exit 1; }
  ls data/w*.json >/dev/null 2>&1 || { echo "no data/w*.json — run prep (or fetch) first"; exit 1; }
  STREAMS=$(ls -r data/w*.json | sed 's/^/--stream /' | tr '\n' ' ')
  SEC_ARGS=(); [ -n "$SECURE" ] && SEC_ARGS=(--secure "$SECURE")
  "$PY" scripts/day_ahead.py --today "$DAY" --local day_ahead_local.json $STREAMS \
    --rhythms data/rhythms.json --calendar cal.json --template day_ahead_engine.html \
    --out "$DAY-day-ahead.html" "${SEC_ARGS[@]}" "$@"
  OUT=${LB_OUT:-/mnt/user-data/outputs}
  if mkdir -p "$OUT" 2>/dev/null; then cp "$DAY-day-ahead.html" "$OUT/"
    echo "also copied to $OUT/"; fi
else
  echo "usage: run_day_ahead.sh prep|cal|fetch|build YYYY-MM-DD [secure] [builder args…]"; exit 2
fi
