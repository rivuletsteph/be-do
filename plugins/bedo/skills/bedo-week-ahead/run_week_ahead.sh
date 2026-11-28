#!/usr/bin/env bash
# The my week page's runner: prep · cal · fetch · build.
#
# It is the day page's runner with a week's window. prep clones the version store and reads the
# live weekly base and the one before it, straight from Airtable with the read-only token, so no
# row passes through the chat; cal turns the three calendars into one file the builder reads;
# build writes the page.
#
#   LB_DIR=<working folder> bash run_week_ahead.sh prep [WEEK]
#   bash run_week_ahead.sh cal  [WEEK]
#   bash run_week_ahead.sh fetch [WEEK]
#   bash run_week_ahead.sh build [WEEK] [--word "…"] [--focus "…"] [--pick "<key>::<why>"] …
#
# WEEK defaults to the week today falls in. Everything after the week on `build` goes to
# scripts/week.py unchanged.
set -euo pipefail

CMD="${1:-}"; shift || true
DIR="${LB_DIR:-$PWD}"
cd "$DIR"

WEEK=""
if [[ "${1:-}" =~ ^[0-9]+$ ]]; then WEEK="$1"; shift; fi

LOCAL="$DIR/day_ahead_local.json"   # the my week page reads the my day page's settings: one copy

# a python that runs: on Windows `python3` can be a stub that only points at the Store (the day
# page's runner does the same)
PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 || continue
  "$c" -c 'import sys' >/dev/null 2>&1 || continue
  PY=$c; break
done
[ -n "$PY" ] || { echo "no working python found (tried python3, python, py)" >&2; exit 1; }
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

secrets_file() {
  for p in "$DIR/bedo_secrets.json" "$DIR/../bedo_secrets.json" "$HOME/.bedo/bedo_secrets.json" \
           "${BEDO_SECRETS:-}"; do
    [ -n "$p" ] && [ -f "$p" ] && { echo "$p"; return 0; }
  done
  return 1
}

# the live weekly base and the one before it, read straight from Airtable: no row through the chat
fetch_airtable() {
  [ -f scripts/day/bedo_fetch.py ] || { echo "scripts/day/bedo_fetch.py missing — run prep first" >&2; exit 1; }
  SECARGS=()
  if SEC=$(secrets_file); then SECARGS=(--secrets "$SEC")
  elif [ -z "${AIRTABLE_PAT:-}" ] && [ "${CLAUDE_CODE_REMOTE:-}" != true ] && [ -z "${BEDO_PROXY_AUTH:-}" ]; then
    echo "NO TOKEN: no bedo_secrets.json found (set BEDO_SECRETS to point at one)" >&2; return 3
  fi
  rm -rf data
  "$PY" scripts/day/bedo_fetch.py --day "$1" --local "$LOCAL" "${SECARGS[@]}" --out data
}

store() {
  rm -rf be-do-main
  git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main
  S=be-do-main/plugins/bedo/skills
  rm -rf scripts && mkdir -p scripts
  cp -r $S/bedo-week-ahead/scripts/* scripts/
  mkdir -p scripts/day && cp $S/bedo-day-ahead/scripts/*.py scripts/day/   # the day page's own readers
  cp $S/bedo-look-behind/scripts/bedo_fetch.py scripts/day/                # the Airtable reader
  cp $S/bedo-week-look-behind/scripts/day_rings.py scripts/day/          # how the day page sorts a row into its kind of time
  cp be-do-main/plugins/bedo/core/*.py be-do-main/plugins/bedo/core/facts.json scripts/day/
  rm -rf assets && mkdir -p assets
  cp $S/bedo-week-ahead/assets/week_engine.html assets/
  cp $S/bedo-day-ahead/assets/flow_engine.html assets/     # read for the day's highlights rule, never built
  cp -r be-do-main/plugins/bedo/assets/base-flow assets/
  cp -r be-do-main/plugins/bedo/assets/flow-parts assets/   # the parts both pages are made of
  if [ -d overlay ]; then cp overlay/*.py scripts/ 2>/dev/null || true
    cp overlay/week_engine.html assets/ 2>/dev/null || true; fi
}

if [ "$CMD" = prep ]; then
  store
  # her settings row in Airtable always wins (her rule on the my day page, 11 Nov 2026): the file
  # already here is only the fallback when the row can't be read. A week built off a stale copy
  # ran without her time goals and with the old field and colour settings.
  "$PY" scripts/day/bedo_settings.py day_ahead_local --out "$LOCAL" || true
fi
[ -f "$LOCAL" ] || { echo "no day_ahead_local.json in $DIR — the my week page reads the my day page's settings" >&2; exit 2; }

week_now() {
  "$PY" - "$LOCAL" <<'PY'
import datetime as dt, json, sys
L = json.load(open(sys.argv[1], encoding='utf-8'))
t = dt.date.today()
sun = t - dt.timedelta(days=(t.weekday() + 1) % 7)
print(L['week_zero_number'] + (sun - dt.date.fromisoformat(L['week_zero_sunday'])).days // 7)
PY
}
[ -n "$WEEK" ] || WEEK="$(week_now)"

# the Sunday that opens that week — the fetch and the calendar read both start there
SUNDAY="$("$PY" - "$LOCAL" "$WEEK" <<'PY'
import datetime as dt, json, sys
L, n = json.load(open(sys.argv[1], encoding='utf-8')), int(sys.argv[2])
print((dt.date.fromisoformat(L['week_zero_sunday']) + dt.timedelta(weeks=n - L['week_zero_number'])).isoformat())
PY
)"

case "$CMD" in
  prep)
    fetch_airtable "$SUNDAY"
    echo
    # the calendar plan: the week's Sunday and the two weeks after it — 21 days, three calendars
    mkdir -p calweek
    "$PY" scripts/day/bedo_cal.py --plan --today "$SUNDAY" --days 21 \
      --local "$LOCAL" --dir calweek --out calweek.json
    ;;
  cal)
    "$PY" scripts/day/bedo_cal.py --build --today "$SUNDAY" --days 21 \
      --local "$LOCAL" --dir calweek --out calweek.json
    ;;
  fetch)
    fetch_airtable "$SUNDAY"
    ;;
  build)
    YEAR="${SUNDAY%%-*}"
    OUT="$DIR/${YEAR}-W${WEEK}-myweek.html"
    # the palette comes off a built day-ahead page: here, or in the my day page's own folder
    DAY_AHEAD="$(ls -1t "$DIR"/*-day-ahead.html "${BEDO_DAY_DIR:-$DIR/../da}"/*-day-ahead.html 2>/dev/null | head -1 || true)"
    [ -n "$DAY_AHEAD" ] || { echo "no built day-ahead page here or in ${BEDO_DAY_DIR:-$DIR/../da} to take the palette from" >&2; exit 2; }
    STREAMS=()
    for f in data/w*.json; do STREAMS+=(--stream "$f"); done
    "$PY" scripts/week.py --week "$WEEK" \
      --local "$LOCAL" "${STREAMS[@]}" --rhythms data/rhythms.json \
      --calendar calweek.json \
      $([ -f data/practices.json ] && echo --practices data/practices.json) \
      --template assets/week_engine.html --day-ahead "$DAY_AHEAD" \
      $([ -d behind ] && echo --behind behind) \
      --out "$OUT" "$@"
    ;;
  *)
    echo "usage: run_week_ahead.sh prep|cal|fetch|build [WEEK] [...]" >&2
    exit 2
    ;;
esac
