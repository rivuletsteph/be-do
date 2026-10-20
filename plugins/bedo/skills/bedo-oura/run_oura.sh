#!/usr/bin/env bash
# Oura into the stream in one command: the stream's own read, Oura's read, and the plan.
# Nothing is written here; the chat applies oura-plan.json with the Airtable connector.
#
#   bash run_oura.sh morning YYYY-MM-DD              # at 🪐 morning oura
#   bash run_oura.sh evening YYYY-MM-DD              # at 🪐 evening oura
#   bash run_oura.sh both    YYYY-MM-DD [YYYY-MM-DD] # catch up a day, or a range ending on the second date
#
# The working folder is the day behind's (OURA_DIR, else LB_DIR, else /home/claude/lb),
# so look_behind_local.json and bedo_secrets.json are already there. The Oura sign-in
# is kept by scripts/oura_auth.py in ~/.bedo; SKILL.md, Setup.
set -euo pipefail
MODE=${1:-}; START=${2:-}; END=${3:-$START}
case "$MODE" in morning|evening|both) ;; *) echo "usage: run_oura.sh morning|evening|both YYYY-MM-DD [YYYY-MM-DD]"; exit 2;; esac
[ -n "$START" ] || { echo "a day is needed: YYYY-MM-DD"; exit 2; }
W=${OURA_DIR:-${LB_DIR:-/home/claude/lb}}; mkdir -p "$W"; cd "$W"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 || continue
  "$c" -c 'import sys' >/dev/null 2>&1 || continue
  PY=$c; break
done
[ -n "$PY" ] || { echo "no working python found (tried python3, python, py)"; exit 1; }

rm -rf be-do-main
git clone -q --depth 1 https://github.com/rivuletsteph/be-do be-do-main
mkdir -p oura-scripts
cp be-do-main/plugins/bedo/skills/bedo-oura/scripts/*.py oura-scripts/
cp be-do-main/plugins/bedo/skills/bedo-look-behind/scripts/bedo_fetch.py be-do-main/plugins/bedo/core/*.py \
   be-do-main/plugins/bedo/core/facts.json oura-scripts/
[ -f look_behind_local.json ] || { [ -n "${LB_LOCAL:-}" ] && [ -f "$LB_LOCAL" ] && cp "$LB_LOCAL" look_behind_local.json; } || true
[ -f look_behind_local.json ] || { echo "look_behind_local.json not found in $W — put it there or set LB_LOCAL"; exit 1; }

SECARGS=()
for c in "${BEDO_SECRETS:-}" bedo_secrets.json ../bedo_secrets.json; do
  [ -n "$c" ] && [ -f "$c" ] && { SECARGS=(--secrets "$c"); break; }
done
rm -rf oura-data
"$PY" oura-scripts/bedo_fetch.py --day "$END" --local look_behind_local.json "${SECARGS[@]}" --out oura-data
STREAMS=$(ls -r oura-data/w*.json | sed 's/^/--stream /' | tr '\n' ' ')
"$PY" oura-scripts/oura.py --mode "$MODE" --start "$START" --end "$END" --local look_behind_local.json $STREAMS --out oura-plan.json
