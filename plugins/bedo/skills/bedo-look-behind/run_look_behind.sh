#!/usr/bin/env bash
# The Day Behind in two commands. Nothing about the rows passes through the chat
# except the digest the lead and story are written from.
#
#   bash run_look_behind.sh prep  YYYY-MM-DD           # fetch + print the day's digest
#   bash run_look_behind.sh qa    YYYY-MM-DD           # the QA list to clear before building (no page)
#   bash run_look_behind.sh build YYYY-MM-DD           # after the words are written: the day page (rainbow, moments, stream)
#   bash run_look_behind.sh canon YYYY-MM-DD <secure>  # the old canon page (21 Sep 2026), kept for comparison
#   bash run_look_behind.sh words YYYY-MM-DD [edits…]  # read the lead and story back, or change them
#
# The words live in words-YYYY-MM-DD.json, written with scripts/words.py (a scheduled
# run adds --draft). `words` with no edits prints them numbered; with --set-lead,
# --set-line, --drop-line, --add-line or --accept it changes them, and --to-page puts
# them on the page already built, with no second read. words.json still works.
#
# Needs, in the working folder: look_behind_local.json (or LB_LOCAL pointing at it, or
# the installed skill's copy). The builder, engine, fetcher and digest come fresh from
# the version store every prep. The Airtable token is bedo_secrets.json in the working
# folder or the folder above it, or AIRTABLE_PAT — or, in a Claude cloud session, none
# at all: the environment's API credential is attached by the proxy after the request
# leaves the VM, and the fetch sends no Authorization header (CLAUDE_CODE_REMOTE=true).
#
# Runs anywhere. Three things differ by machine, and each is an override:
#   LB_DIR    the working folder          (default /home/claude/lb)
#   LB_LOCAL  where look_behind_local.json is copied from, if not already in place
#   LB_OUT    where the finished page is also copied (skipped if it can't be made)
# python3 is used when present, otherwise python.
set -euo pipefail
MODE=${1:-}; DAY=${2:-}; SECURE=${3:-}
W=${LB_DIR:-/home/claude/lb}; mkdir -p "$W"; cd "$W"
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
  [ -f look_behind_local.json ] && return 0
  if [ -n "${LB_LOCAL:-}" ] && [ -f "$LB_LOCAL" ]; then cp "$LB_LOCAL" look_behind_local.json; return 0; fi
  for c in /root/.claude/skills/synced/*/bedo-look-behind/assets/look_behind_local.json; do
    [ -f "$c" ] && { cp "$c" look_behind_local.json; return 0; }
  done
  echo "look_behind_local.json not found in $W — put it there or set LB_LOCAL"; exit 1
}

if [ "$MODE" = prep ]; then
  rm -rf be-do-main
  git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main
  S=be-do-main/plugins/bedo/skills/bedo-look-behind
  rm -rf scripts && cp -r $S/scripts . && cp $S/assets/look_behind_engine.html .
  cp be-do-main/plugins/bedo/skills/bedo-day-ahead/scripts/day_digest.py scripts/   # the digest lives with the day ahead
  # the day page is the week builder's --day mode since 25 Oct 2026 (docs/day-behind-cards.md)
  cp be-do-main/plugins/bedo/skills/bedo-week-look-behind/scripts/*.py scripts/
  cp be-do-main/plugins/bedo/skills/bedo-week-look-behind/assets/week_look_behind_engine.html .
  cp be-do-main/plugins/bedo/core/*.py be-do-main/plugins/bedo/core/facts.json scripts/   # the one reader (I11 I15 I5)
  # an escape hatch: anything in overlay/ wins over the version store for this run
  if [ -d overlay ]; then cp overlay/*.py scripts/ 2>/dev/null || true
    cp overlay/look_behind_engine.html overlay/week_look_behind_engine.html . 2>/dev/null || true; fi
  # the live settings are a row in Airtable (be•do system › settings); without it, the copy below
  [ -n "${LB_LOCAL:-}" ] || "$PY" scripts/bedo_settings.py look_behind_local --out look_behind_local.json || true
  need_local
  rm -rf data
  SECARGS=()
  for c in "${BEDO_SECRETS:-}" bedo_secrets.json ../bedo_secrets.json; do
    [ -n "$c" ] && [ -f "$c" ] && { SECARGS=(--secrets "$c"); break; }
  done
  # the fetch and the digest run from scripts/, fresh from the version store (or the overlay);
  # a root copy left in the working folder by an older prep is not used
  "$PY" scripts/bedo_fetch.py --day "$DAY" --local look_behind_local.json "${SECARGS[@]}" --out data
  STREAMS=$(ls -r data/w*.json | sed 's/^/--stream /' | tr '\n' ' ')
  "$PY" scripts/day_digest.py --day "$DAY" --local look_behind_local.json $STREAMS --width 130
elif [ "$MODE" = qa ]; then
  # the checks live in the canon builder; run it for its QA block alone, nothing to publish
  need_local
  STREAMS=$(ls -r data/w*.json | sed 's/^/--stream /' | tr '\n' ' ')
  "$PY" scripts/look_behind.py --day "$DAY" --local look_behind_local.json $STREAMS \
    --rhythms data/rhythms.json --practices data/practices.json --connections data/connections.json \
    --template look_behind_engine.html --out "qa-$DAY.html" --secure secure --allow-unwritten \
    | "$PY" -c 'import json,sys; d=json.load(sys.stdin); print(json.dumps({k: d[k] for k in ("qa", "not_yet_whole", "estimates_trimmed_min", "containers_set_aside", "circles_read") if k in d}, ensure_ascii=False, indent=1))'
  rm -f "qa-$DAY.html"
elif [ "$MODE" = build ] || [ "$MODE" = canon ]; then
  need_local
  STREAMS=$(ls -r data/w*.json | sed 's/^/--stream /' | tr '\n' ' ')
  # the day's own words file, unless a words.json written since is newer (the older habit)
  WORDS=words.json
  if [ -f "words-$DAY.json" ] && { [ ! -f words.json ] || [ "words-$DAY.json" -nt words.json ]; }; then
    WORDS="words-$DAY.json"; fi
  [ -f "$WORDS" ] || { echo "no words for $DAY — write words-$DAY.json with scripts/words.py --new (SKILL.md)"; exit 1; }
  echo "words: $WORDS"
  if [ "$MODE" = build ]; then
    # photos from the week's Drive folder when the key is here; without it the page builds without them
    PHOTOS=
    if [ -n "${BEDO_DRIVE_SA:-}${BEDO_DRIVE_SA_FILE:-}" ]; then
      "$PY" scripts/day_photos.py --day "$DAY" --local look_behind_local.json --out "photos-$DAY" || true
      if [ -n "$(ls -A "photos-$DAY" 2>/dev/null)" ]; then PHOTOS="--photos photos-$DAY"; fi
    fi
    # the places catalog, for the map card's data (day_places.py; not drawn yet, D6.68)
    PLACES=; [ -f data/places.json ] && PLACES="--places data/places.json"
    "$PY" scripts/week_look_behind.py --day "$DAY" --words "$WORDS" --local look_behind_local.json $STREAMS \
      --rhythms data/rhythms.json --practices data/practices.json \
      --template week_look_behind_engine.html $PHOTOS $PLACES --out "$DAY-day-behind.html"
  else
  # typical lengths, the median of the user's own timed rows (scripts/typical_time.py)
  TYPICAL=; [ -f typical_time.json ] && TYPICAL="--typical typical_time.json"
  # the day's photos from the week's W## photos folder, when a Drive key is here (BEDO_DRIVE_SA
  # or BEDO_DRIVE_SA_FILE); without one the strip stays hidden and the page builds as before
  PHOTOS=
  if [ -f scripts/day_photos.py ]; then rm -rf "photos-$DAY"
    if "$PY" scripts/day_photos.py --day "$DAY" --local look_behind_local.json --out "photos-$DAY"; then
      PHOTOS="--photos photos-$DAY"; else echo "photos: none read — the page builds without them"; fi; fi
  "$PY" scripts/look_behind.py --day "$DAY" --local look_behind_local.json $STREAMS \
    --rhythms data/rhythms.json --practices data/practices.json --connections data/connections.json \
    --words "$WORDS" --template look_behind_engine.html $TYPICAL $PHOTOS \
    --out "$DAY-day-behind.html" --secure "$SECURE"
  fi
  OUT=${LB_OUT:-/mnt/user-data/outputs}
  if mkdir -p "$OUT" 2>/dev/null; then cp "$DAY-day-behind.html" "$OUT/"
    echo "also copied to $OUT/"; fi
elif [ "$MODE" = words ]; then
  [ -f scripts/words.py ] || { echo "scripts/words.py missing — run prep first"; exit 1; }
  shift 2
  "$PY" scripts/words.py --day "$DAY" --file "words-$DAY.json" --page "$DAY-day-behind.html" "$@"
  case " $* " in *" --to-page "*)
    OUT=${LB_OUT:-/mnt/user-data/outputs}
    if mkdir -p "$OUT" 2>/dev/null; then cp "$DAY-day-behind.html" "$OUT/"
      echo "also copied to $OUT/"; fi;; esac
else
  echo "usage: run_look_behind.sh prep|qa|build|canon|words YYYY-MM-DD [secure (canon) | edits… (words)]"; exit 2
fi
