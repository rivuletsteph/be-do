#!/usr/bin/env bash
# be•do's checks, run rather than remembered. The core comes fresh from the
# version store on every preflight; the other commands reuse that copy.
#
#   bash run_checks.sh preflight [--kind week --week N] [--part B] [--handoff FILE]
#   bash run_checks.sh remaining [--flow dawn|dusk] [--voice]
#   bash run_checks.sh dusk      [--date YYYY-MM-DD] [--chats chats.json] [--write]
#   bash run_checks.sh entry     row.json [--base "w41 be•do"]
#   bash run_checks.sh stretches FILE        # stamps, a claude.ai chat read, or a transcript
#
# With an Airtable token (AIRTABLE_PAT, a bedo_secrets.json, or a Claude cloud
# session's proxy) the checks read Airtable themselves. Without one, read through
# the Airtable connector, save the results as files, and pass them:
#   preflight --bases names.json --stream recent.json
#   remaining --catalog practices.json --day today.json
#   dusk      --day today.json --catalog practices.json
# A command given no files and no token says so and exits 3.
#
# Overrides: BC_DIR (where the core is kept, default ~/bedo-checks),
# BEDO_FACTS_LOCAL (her settings file, if it isn't found by itself),
# BC_CORE_SRC (a local core folder to use instead of the version store — tests only).
set -euo pipefail
CMD=${1:-}; shift || true
W=${BC_DIR:-$HOME/bedo-checks}; mkdir -p "$W"
export PYTHONUTF8=1 PYTHONIOENCODING=utf-8

# Windows ships a python3.exe stub that exists but refuses to run
PY=""
for c in python3 python py; do
  command -v "$c" >/dev/null 2>&1 || continue
  "$c" -c 'import sys' >/dev/null 2>&1 || continue
  PY=$c; break
done
[ -n "$PY" ] || { echo "no working python found (tried python3, python, py)"; exit 1; }

fetch_core() {
  if [ -n "${BC_CORE_SRC:-}" ]; then rm -rf "$W/core"; cp -r "$BC_CORE_SRC" "$W/core"; return 0; fi   # a local copy, for testing a branch
  local T; T=$(mktemp -d)
  if curl -sSL -o "$T/b.tgz" https://codeload.github.com/rivuletsteph/be-do/tar.gz/refs/heads/main \
     && tar -xzf "$T/b.tgz" -C "$T" 2>/dev/null && [ -d "$T/be-do-main/plugins/bedo/core" ]; then :
  else   # in Cowork the tarball can come back as a JSON refusal; a clone works there
    rm -rf "$T/be-do-main"; git clone -q --depth 1 https://github.com/rivuletsteph/be-do "$T/be-do-main"
  fi
  rm -rf "$W/core"; cp -r "$T/be-do-main/plugins/bedo/core" "$W/core"; rm -rf "$T"
}

find_local() {
  [ -n "${BEDO_FACTS_LOCAL:-}" ] && [ -f "$BEDO_FACTS_LOCAL" ] && return 0
  for c in ./facts_local.json "$W/facts_local.json" /root/.claude/skills/synced/*/bedo-checks/assets/facts_local.json \
           "$HOME/.bedo/facts_local.json"; do
    [ -f "$c" ] && { export BEDO_FACTS_LOCAL=$(cd "$(dirname "$c")" && pwd)/$(basename "$c"); return 0; }
  done
  echo "facts_local.json not found — copy the skill's assets/facts_local.json into the working folder"; exit 1
}

has_files() { for a in "$@"; do case "$a" in --bases|--stream|--catalog|--day) return 0;; esac; done; return 1; }

live_or_files() {   # $1 = what to say is needed; rest = the args
  local need=$1; shift
  if has_files "$@"; then return 1; fi
  if (cd "$W/core" && "$PY" -c 'import bedo_air, sys; sys.exit(0 if bedo_air.can_read() else 1)'); then return 0; fi
  echo "NO TOKEN HERE: read through the Airtable connector and pass $need (see SKILL.md)"; exit 3
}

case "$CMD" in
  preflight)
    fetch_core; find_local
    if live_or_files "--bases names.json --stream recent.json" "$@"; then set -- --live "$@"; fi
    "$PY" "$W/core/bedo_preflight.py" "$@" ;;
  remaining)
    [ -d "$W/core" ] || fetch_core; find_local
    if live_or_files "--catalog practices.json --day today.json" "$@"; then set -- --live "$@"; fi
    "$PY" "$W/core/bedo_remaining.py" "$@" ;;
  dusk)
    [ -d "$W/core" ] || fetch_core; find_local
    if live_or_files "--day today.json --catalog practices.json" "$@"; then set -- --live "$@"; fi
    "$PY" "$W/core/bedo_dusk_audit.py" "$@" ;;
  stretches)
    [ -d "$W/core" ] || fetch_core; find_local
    "$PY" "$W/core/bedo_stretches.py" "$@" ;;
  entry)
    [ -d "$W/core" ] || fetch_core; find_local
    ROW=${1:?usage: run_checks.sh entry row.json [--base NAME]}; shift
    BASE=""; [ "${1:-}" = --base ] && BASE=${2:-}
    "$PY" - "$W/core" "$ROW" "$BASE" <<'E'
import json, sys
sys.path.insert(0, sys.argv[1])
from bedo_entry import problems
from bedo_reader import load_local
L = load_local()
rows = json.load(open(sys.argv[2], encoding='utf-8'))
bad = 0
for r in rows if isinstance(rows, list) else [rows]:
    p = problems(r, sys.argv[3] or None, L.get('utc_offset_hours'), L.get('weekly_name', 'w{n} be•do'))
    print(('ok    ' if not p else 'FIX   ') + (r.get('title') or r.get('practice') or '?'))
    for x in p:
        print('      · ' + x)
    bad += bool(p)
sys.exit(1 if bad else 0)
E
    ;;
  *) echo "usage: run_checks.sh preflight|remaining|dusk|entry|stretches [args]"; exit 2 ;;
esac
