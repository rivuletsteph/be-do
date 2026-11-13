#!/usr/bin/env bash
# be•do's checks, run rather than remembered. The core comes fresh from the
# version store on every preflight; the other commands reuse that copy.
#
#   bash run_checks.sh judgment   # the judgment file, read in full at the first reply
#   bash run_checks.sh preflight [--kind week --week N] [--part B] [--handoff FILE]
#   bash run_checks.sh remaining [--flow dawn|dusk] [--voice]
#   bash run_checks.sh dusk      [--date YYYY-MM-DD] [--chats chats.json] [--photos folder.json [--links week.json]] [--write]
#   bash run_checks.sh meals     [--date YYYY-MM-DD] [--json]   # each meal's prep and eating, placed from context
#   bash run_checks.sh places    --stays stays.json [--json]   # the map check: her Timeline screenshot's stays as 📍 rows, new places to ask
#   bash run_checks.sh dayqa     YYYY-MM-DD [--calendar day.json …] [--photos folder.json] [--sleep oura.json] [--sessions chats.json] [--json]
#                                # be•do's calls on the day first (bedo_categorize), the day's records read, then one list to accept
#   bash run_checks.sh daygate   YYYY-MM-DD [--rows day.json]   # look_behind.day_ahead_first: the day ahead final and the
#                                # day QA'd, before any day behind (6 Nov 2026); exits 1 while the gate is closed
#   bash run_checks.sh entry     row.json [--base "w41 be•do"] [--chat MMDD] [--catalog practices.json] [--rhythms rhythms.json] [--day today.json]
#                                # MMDD: a my day chat's date, from its title; the catalog and rhythms let it deduce
#                                # wellness and know a flow step; the day's rows let it see two things at once
#   bash run_checks.sh stretches FILE        # stamps, a claude.ai chat read, or a transcript
#   bash run_checks.sh order [--json]        # her predicted order: typical times to write to the catalog
#   bash run_checks.sh cleanup [--drives 2] [--json]   # the weekly drive cleanup, after the split: the big
#                                # picture, this week's drives, and the evidence on each stale row (9 Nov 2026)
#   bash run_checks.sh drives --rhythms rhythms.json --stream live.json [--stream older.json] [--json]
#                                # the drive check (10 Nov 2026): effort with no drive, drives with no goal or date
#   bash run_checks.sh close --chat URL --title "TITLE" [--date YYYY-MM-DD]   # the chat close: QA, entry, title
#   bash run_checks.sh calendar event.json [--readback read.json --from CALENDAR_ID] [--rhythms rhythms.json]
#   bash run_checks.sh calsync YYYY-MM-DD [--events events.json --calendars calendars.json]
#                                # the dusk close: the calendar mirrors the stream (the done marks). First run lists
#                                # the linked events to fetch; with the two files it prints the plan to write
#                                # every calendar write: named, read back, work in purple
#   bash run_checks.sh inbox threads.json [--archive planned.json]   # before the inbox sweep archives anything
#   bash run_checks.sh chats --sessions mine.json [--sessions other.json] [--rows rows.json] [--json]
#                                # the chat sweep, at the dusk close and the weekly close: every open chat
#                                # against its objective and its row; what be•do does on its own, and her one list
#   bash run_checks.sh outgoing [--title "TITLE"] [--text pr.md] [--branch NAME]
#                                # before every push and every pull request opened or edited (12 Nov 2026): the
#                                # privacy check on the files, the new commits, the branch name and the PR's own text
#   bash run_checks.sh usage [days]          # the Airtable calls made from here, by day and by script
#   bash run_checks.sh how NAME              # a command's notes (commands/NAME.md): read before its first run in a chat
#
# With an Airtable token (AIRTABLE_PAT, a bedo_secrets.json, or a Claude cloud
# session's proxy) the checks read Airtable themselves. Without one, read through
# the Airtable connector, save the results as files, and pass them:
#   preflight --bases names.json --stream recent.json [--amendments amendments.json] [--look-behind log.json]
#   remaining --catalog practices.json --day today.json
#   dusk      --day today.json --catalog practices.json
#   meals     --day today.json
#   places    --stays stays.json --day today.json --places places.json
#   dayqa     --day today.json --catalog practices.json --rhythms rhythms.json --connections connections.json
#   daygate   --rows day.json   (the day's rows and the next morning's: its 👁️ look ahead row and its dusk close row)
# A command given no files and no token says so and exits 3.
#
# Overrides: BC_DIR (where the core is kept, default ~/bedo-checks),
# BEDO_FACTS_LOCAL (her settings file, used when the Airtable settings row can't be read),
# BC_LOCAL_FIRST (use BEDO_FACTS_LOCAL even when the row can be read — tests only),
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

# Each command's notes sit beside this script (commands/NAME.md), so the skill file
# every chat reads stays short. `how NAME` prints them; every other command says
# where its notes are as it runs, so reading them is never left to memory.
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
if [ "$CMD" = how ]; then
  N=${1:-}
  if [ -n "$N" ] && [ -f "$HERE/commands/$N.md" ]; then cat "$HERE/commands/$N.md"; exit 0; fi
  echo "usage: run_checks.sh how NAME — notes for: $(cd "$HERE/commands" 2>/dev/null && ls | sed 's/\.md$//' | tr '\n' ' ')"; exit 1
fi
case "$CMD" in
  judgment|preflight|remaining|usage|"") ;;   # their notes are in the skill file itself, or there are none
  *) if [ -f "$HERE/commands/$CMD.md" ]; then
       echo "first run of $CMD in this chat? read its notes: bash run_checks.sh how $CMD" >&2
     fi ;;
esac

fetch_core() {
  if [ -n "${BC_CORE_SRC:-}" ]; then rm -rf "$W/core"; cp -r "$BC_CORE_SRC" "$W/core"; return 0; fi   # a local copy, for testing a branch
  local T; T=$(mktemp -d)
  if curl -sSL -o "$T/b.tgz" https://codeload.github.com/rivuletsteph/be-do/tar.gz/refs/heads/main \
     && tar -xzf "$T/b.tgz" -C "$T" 2>/dev/null && [ -d "$T/be-do-main/plugins/bedo/core" ]; then :
  else   # in Cowork the tarball can come back as a JSON refusal; a clone works there
    rm -rf "$T/be-do-main"; git clone -q --depth 1 https://github.com/rivuletsteph/be-do "$T/be-do-main"
  fi
  rm -rf "$W/core"; cp -r "$T/be-do-main/plugins/bedo/core" "$W/core"
  # dayqa's painted check reads the day page's own rules (30 Oct 2026); they import only the core
  cp "$T/be-do-main/plugins/bedo/skills/bedo-week-look-behind/scripts/day_rings.py" "$W/core/" 2>/dev/null || true
  cp "$T/be-do-main/docs/v53-judgment.md" "$W/core/judgment.md" 2>/dev/null || true
  # what the version store holds, for `skills` (12 Nov 2026): each skill, and whether it has a loader
  "$PY" - "$T/be-do-main/plugins/bedo/skills" "$W/core/skills.json" <<'S' 2>/dev/null || true
import json, os, sys
d = sys.argv[1]
json.dump({n: {'loader': os.path.isfile(os.path.join(d, n, 'loader', 'SKILL.md'))}
           for n in sorted(os.listdir(d)) if os.path.isfile(os.path.join(d, n, 'SKILL.md'))}, open(sys.argv[2], 'w'))
S
  rm -rf "$T"
}

find_local() {
  # the live settings are a row in Airtable (be•do system › settings), and the
  # row wins: the loader's copy is only the fallback, so a change is one edit
  # to the row, never a skill upload (25 Oct 2026). BC_LOCAL_FIRST=1 keeps a
  # given file first, for tests.
  if [ -z "${BC_LOCAL_FIRST:-}" ] && (cd "$W/core" && "$PY" bedo_settings.py facts_local --out "$W/facts_local.json"); then
    export BEDO_FACTS_LOCAL="$W/facts_local.json"; return 0; fi
  [ -n "${BEDO_FACTS_LOCAL:-}" ] && [ -f "$BEDO_FACTS_LOCAL" ] && return 0
  for c in ./facts_local.json "$W/facts_local.json" /root/.claude/skills/synced/*/bedo-checks/assets/facts_local.json \
           "$HOME/.bedo/facts_local.json"; do
    [ -f "$c" ] && { export BEDO_FACTS_LOCAL=$(cd "$(dirname "$c")" && pwd)/$(basename "$c"); return 0; }
  done
  echo "facts_local.json not found — copy the skill's assets/facts_local.json into the working folder"; exit 1
}

has_files() { for a in "$@"; do case "$a" in --bases|--stream|--catalog|--day|--rows) return 0;; esac; done; return 1; }

live_or_files() {   # $1 = what to say is needed; rest = the args
  local need=$1; shift
  if has_files "$@"; then return 1; fi
  if (cd "$W/core" && "$PY" -c 'import bedo_air, sys; sys.exit(0 if bedo_air.can_read() else 1)'); then return 0; fi
  echo "NO TOKEN HERE: expected in Cowork or a plain chat, not a failure. Don't run the checks by hand."
  echo "Read through the Airtable connector, save each result as a file, and run this again with $need (how: bash run_checks.sh how no-token)"; exit 3
}

case "$CMD" in
  judgment)   # the project's instructions, fresh from the version store: nothing to paste
    fetch_core
    [ -f "$W/core/judgment.md" ] || { echo "judgment file missing from the download"; exit 1; }
    cat "$W/core/judgment.md" ;;
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
  meals)
    [ -d "$W/core" ] || fetch_core; find_local
    if live_or_files "--day today.json" "$@"; then set -- --live "$@"; fi
    "$PY" "$W/core/bedo_meals.py" "$@" ;;
  places)     # 5 Nov 2026: one 📍 row per stay, coordinates only in the places base
    [ -d "$W/core" ] || fetch_core; find_local
    if live_or_files "--day today.json --places places.json" "$@"; then set -- --live "$@"; fi
    "$PY" "$W/core/bedo_places.py" "$@" ;;
  dayqa)
    [ -d "$W/core" ] || fetch_core; find_local
    D=${1:?usage: run_checks.sh dayqa YYYY-MM-DD [--json] [files]}; shift
    if live_or_files "--day today.json --catalog practices.json --rhythms rhythms.json --connections connections.json" "$@"; then set -- --live "$@"; fi
    "$PY" "$W/core/bedo_dayqa.py" --date "$D" "$@" ;;
  daygate)    # 6 Nov 2026, her words: finish the day ahead, make sure you QA it, then do the day behind
    [ -d "$W/core" ] || fetch_core; find_local
    D=${1:?usage: run_checks.sh daygate YYYY-MM-DD [--rows day.json]}; shift
    if live_or_files "--rows day.json" "$@"; then set -- --live "$@"; fi
    "$PY" "$W/core/bedo_daygate.py" check --date "$D" "$@" ;;
  order)
    [ -d "$W/core" ] || fetch_core; find_local
    if has_files "$@"; then :; elif (cd "$W/core" && "$PY" -c 'import bedo_air, sys; sys.exit(0 if bedo_air.can_read() else 1)'); then set -- --live "$@"
    else echo "NO TOKEN HERE: expected in Cowork or a plain chat, not a failure. Don't run the checks by hand."
         echo "Read through the Airtable connector and run this again with --stream (each weekly base, live first) and --catalog files"; exit 3; fi
    "$PY" "$W/core/bedo_order.py" "$@" ;;
  cleanup)   # 9 Nov 2026, her words: over 300 lines got carried to the new week … it needs to happen on a weekly basis
    [ -d "$W/core" ] || fetch_core; find_local
    if has_files "$@"; then :; elif (cd "$W/core" && "$PY" -c 'import bedo_air, sys; sys.exit(0 if bedo_air.can_read() else 1)'); then set -- --live "$@"
    else echo "NO TOKEN HERE: expected in Cowork or a plain chat, not a failure. Don't run the checks by hand."
         echo "Read the live weekly base's stream (and last week's) through the connector and run this again with --stream FILE --stream FILE"; exit 3; fi
    "$PY" "$W/core/bedo_cleanup.py" "$@" ;;
  drives)   # 10 Nov 2026, her words: everything I'm putting significant effort into has a drive … what the goal is and what the timeline is
    [ -d "$W/core" ] || fetch_core; find_local
    "$PY" "$W/core/bedo_drive_check.py" "$@" ;;
  close)   # her rule, 25 Oct 2026: QA, then the session entry, then the rename to done
    [ -d "$W/core" ] || fetch_core; find_local
    if has_files "$@"; then :
    elif (cd "$W/core" && "$PY" -c 'import bedo_air, sys; sys.exit(0 if bedo_air.can_read() else 1)'); then set -- --live "$@"
    else echo "NO TOKEN HERE: expected in Cowork or a plain chat, not a failure. Don't run the checks by hand."
         echo "Read the chat's ⚡ entry (and, for a my day chat, the day's rows) through the connector and run this again with --rows FILE"; exit 3; fi
    "$PY" "$W/core/bedo_close.py" "$@" ;;
  stretches)
    [ -d "$W/core" ] || fetch_core; find_local
    "$PY" "$W/core/bedo_stretches.py" "$@" ;;
  calsync)    # her yes, 11 Nov 2026: keep the calendar's done marks; the step left the retired day behind
    [ -d "$W/core" ] || fetch_core; find_local
    D=${1:?usage: run_checks.sh calsync YYYY-MM-DD [--events events.json --calendars calendars.json] [--local look_behind_local.json --stream week.json]}; shift
    MODE=--list; FILES=""
    for a in "$@"; do case "$a" in --events) MODE=--plan;; --stream) FILES=1;; esac; done
    if [ -n "$FILES" ]; then :
    elif (cd "$W/core" && "$PY" -c 'import bedo_air, sys; sys.exit(0 if bedo_air.can_read() else 1)'); then set -- --live "$@"
    else echo "NO TOKEN HERE: expected in Cowork or a plain chat, not a failure. Don't run the checks by hand."
         echo "Read the week's stream through the connector and run this again with --local look_behind_local.json --stream week.json"; exit 3; fi
    "$PY" "$W/core/calendar_sync.py" $MODE --day "$D" "$@" ;;
  calendar)   # 6 and 9 Oct 2026: the calendar named, the write read back, work in purple
    [ -d "$W/core" ] || fetch_core; find_local
    "$PY" "$W/core/bedo_calendar.py" "$@" ;;
  inbox)      # 22, 25 and 26 Oct 2026: automatic keeps, archive by rule, the nudge before archiving
    [ -d "$W/core" ] || fetch_core; find_local
    "$PY" "$W/core/bedo_inbox.py" "$@" ;;
  chats)      # 2 and 5 Nov 2026: the chat sweep — every open chat against its objective and its row
    [ -d "$W/core" ] || fetch_core; find_local
    if has_files "$@"; then :
    elif (cd "$W/core" && "$PY" -c 'import bedo_air, sys; sys.exit(0 if bedo_air.can_read() else 1)'); then set -- --live "$@"
    else echo "NO TOKEN HERE: expected in Cowork or a plain chat, not a failure. Don't run the checks by hand."
         echo "Read the ⚡ rows with a chat link (this week's base and the one before) through the connector and run this again with --rows FILE"; exit 3; fi
    "$PY" "$W/core/bedo_chats.py" "$@" ;;
  entry)
    [ -d "$W/core" ] || fetch_core; find_local
    ROW=${1:?usage: run_checks.sh entry row.json [--base NAME] [--chat MMDD] [--catalog FILE] [--rhythms FILE] [--day FILE] [--keys FILE]}; shift
    BASE=""; CHAT=""; CAT=""; RHY=""; DAY=""; KEYS=""
    while [ $# -gt 0 ]; do case "$1" in --base) BASE=${2:-}; shift 2;; --chat) CHAT=${2:-}; shift 2;;
      --catalog) CAT=${2:-}; shift 2;; --rhythms) RHY=${2:-}; shift 2;; --day) DAY=${2:-}; shift 2;;
      --keys) KEYS=${2:-}; shift 2;; *) shift;; esac; done
    "$PY" - "$W/core" "$ROW" "$BASE" "$CHAT" "$CAT" "$RHY" "$DAY" "$KEYS" <<'E'
import datetime as dt, json, sys
sys.path.insert(0, sys.argv[1])
from bedo_entry import notes, problems, utc
import bedo_clock
from bedo_reader import as_rows, complete, load_local
import bedo_fill as FL
L = load_local()
rows = json.load(open(sys.argv[2], encoding='utf-8'))
rows = rows if isinstance(rows, list) else [rows]
chat = None
if sys.argv[4]:   # the chat's MMDD, from its title; the year is the row's (a January chat in December is not a case)
    y = utc(rows[0]['datetime']).year if rows and (rows[0].get('datetime') or '').endswith('Z') else dt.date.today().year
    chat = dt.date(y, int(sys.argv[4][:2]), int(sys.argv[4][2:4]))
# device and wellness are deduced, never left empty (9 Oct 2026): the catalog
# gives wellness, the drives their element; spans come from the rows written together
cat = complete(sys.argv[5], 'catalog') if sys.argv[5] else None
day = as_rows(complete(sys.argv[7], 'day'), {**{k: k for k in ('datetime', 'end', 'status', 'practice', 'title', 'key')},
                                              **(L.get('stream_fields') or {})}) if sys.argv[7] else []
ids = {r.get('id') for r in rows if r.get('id')}
fill = FL.Context(catalog=FL.catalog_wellness(cat, L) if cat else None,
                  drives=FL.drive_elements(complete(sys.argv[6], 'rhythms'), L) if sys.argv[6] else None,
                  day_rows=rows + [r for r in day if r.get('id') not in ids], local=L,
                  flows=FL.catalog_flows(cat, L) if cat else None)
# one row per key (12 Nov 2026): what the live base already holds on these keys. Read here when Airtable
# answers (one call), from --keys FILE where it doesn't, else from the day's rows, and said when it's only those
NAMES = {**{k: k for k in ('datetime', 'end', 'status', 'practice', 'title', 'key')}, **(L.get('stream_fields') or {})}
keys = sorted({(r.get('key') or '').strip() for r in rows} - {''})
existing = [r for r in day if (r.get('key') or '').strip() in keys]
if keys:
    import bedo_air
    from bedo_entry import week_number
    if sys.argv[8]:
        existing = as_rows(complete(sys.argv[8], 'keys'), NAMES)
    elif NAMES['key'] != 'key' and bedo_air.can_read():
        air = bedo_air.Air()
        want = sys.argv[3] or L.get('weekly_name', 'w{n} be•do').format(n=week_number(bedo_clock.now_local(L).date()))
        base = air.bases().get(want)
        if base:
            f = 'OR(' + ', '.join("{%s}='%s'" % (NAMES['key'], k.replace("'", '')) for k in keys) + ')'
            existing = as_rows(air.records(base, L['stream_table'], formula=f, by_id=True), NAMES)
        else:
            print(f'key: no base named {want}, so the keys were checked against the day\'s rows only')
    else:
        print('key: not checked against the base here — read the rows on ' + ', '.join(keys) +
              ' through the connector and pass them as --keys FILE')
# the clock is the zone, read for each row's own instant; the hand-kept number is only for a machine with no zone (f6)
CLOCK = L if (bedo_clock.zone(L) is not None or L.get('utc_offset_hours') is not None) else None
if bedo_clock.zone(L) is None:
    print('clock: the time zone could not be read here, so times use the fixed number '
          f'({L.get("utc_offset_hours")}) — check it against a real clock before writing')
bad = 0
for r in rows:
    p = problems(r, sys.argv[3] or None, CLOCK, L.get('weekly_name', 'w{n} be•do'), chat, fill,
                 (L.get('people') or {}).get('self'), existing=existing)
    print(('ok    ' if not p else 'FIX   ') + (r.get('title') or r.get('practice') or '?'))
    for x in p:
        print('      · ' + x)
    for x in notes(r, fill):          # never blocks the write
        print('      note: ' + x)
    bad += bool(p)
sys.exit(1 if bad else 0)
E
    ;;
  outgoing)   # 12 Nov 2026, her words: the privacy check only scans repo files, so PR titles, descriptions and commit messages slip through
    R=${BEDO_REPO:-$(git rev-parse --show-toplevel 2>/dev/null || true)}
    [ -n "$R" ] && [ -f "$R/tools/privacy_check.py" ] || { echo "outgoing: run this inside the be-do clone, or set BEDO_REPO to it"; exit 2; }
    (cd "$R" && "$PY" tools/privacy_check.py --outgoing "$@") ;;
  skills)     # 12 Nov 2026: installed skills in step with the version store
    fetch_core
    REPO_SKILLS="$W/core/skills.json"
    [ -n "${BC_CORE_SRC:-}" ] && [ -d "$BC_CORE_SRC/../skills" ] && REPO_SKILLS="$BC_CORE_SRC/../skills"   # testing a branch
    [ -e "$REPO_SKILLS" ] || { echo "skills: the list of repo skills is missing from the download"; exit 1; }
    set -- --repo "$REPO_SKILLS" "$@"
    case " $* " in *" --installed "*) ;; *)
      for c in "$HOME/.claude/skills" /root/.claude/skills /mnt/skills/user; do [ -d "$c" ] && set -- "$@" --installed "$c"; done ;; esac
    "$PY" "$W/core/bedo_skills.py" "$@" ;;
  usage)      # 4 Nov 2026: what the checks spend, so the plan can be sized from real numbers
    [ -d "$W/core" ] || fetch_core
    "$PY" "$W/core/bedo_air.py" usage "$@" ;;
  *) echo "usage: run_checks.sh judgment|preflight|remaining|dusk|meals|dayqa|daygate|entry|stretches|order|cleanup|drives|close|calendar|calsync|inbox|chats|outgoing|skills|usage|how [args]"; exit 2 ;;
esac
