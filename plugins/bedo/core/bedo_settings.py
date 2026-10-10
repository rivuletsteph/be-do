# -*- coding: utf-8 -*-
"""Settings from one place: a row in Airtable, not a file inside each skill's
zip (10 Oct 2026).

Each builder's settings (look_behind_local, day_ahead_local, facts_local) used
to live only inside its skill, so changing one value meant repackaging and
uploading the skill. Now the live copy is a row in the `settings` table of the
`be•do system` base — one row per file, its JSON in the `json` field — and any
chat changes a setting by editing that row. The skill's own copy stays as the
fallback: when Airtable can't be read here (Cowork, a plain chat) or the row is
missing or broken, the runner uses the file it always used, and says so.

Base and table are found by NAME, so no id lives in this public repo.

    python3 bedo_settings.py look_behind_local --out look_behind_local.json

Exit 0: the file was written from Airtable. Exit 1: it was not, and the caller
falls back to its own copy. Nothing here ever stops a build.
"""
import argparse, json, os, re, sys

BASE_NAME = 'be•do system'
TABLE_NAME = 'settings'
NAME_FIELD, JSON_FIELD = 'name', 'json'


def parse(text):
    """The row's JSON as a dict, or None. A code fence around it is forgiven,
    because a chat pasting JSON into a long-text field often adds one."""
    t = (text or '').strip()
    t = re.sub(r'^```(?:json)?\s*|\s*```$', '', t)
    try:
        d = json.loads(t)
    except ValueError:
        return None
    return d if isinstance(d, dict) and d else None


def from_records(recs, name):
    """(settings, why-not) for the row called `name` among the table's records."""
    rows = [r for r in recs if ((r.get('fields') or {}).get(NAME_FIELD) or '').strip() == name]
    if not rows:
        return None, f'no row named {name}'
    if len(rows) > 1:
        return None, f'{len(rows)} rows named {name} — which one is meant?'
    d = parse((rows[0].get('fields') or {}).get(JSON_FIELD))
    return (d, None) if d else (None, f'the {name} row is not a JSON object')


def fetch(name):
    """(settings, why-not), read live. Never raises and never exits."""
    try:
        import bedo_air
        if not bedo_air.can_read():
            return None, 'Airtable cannot be read here'
        air = bedo_air.Air()
        base = air.bases().get(BASE_NAME)
        if not base:
            return None, f'no base named {BASE_NAME}'
        tables = air.get(f'meta/bases/{base}/tables')['tables']
        table = next((t['id'] for t in tables if t['name'] == TABLE_NAME), None)
        if not table:
            return None, f'no {TABLE_NAME} table in {BASE_NAME}'
        return from_records(air.records(base, table), name)
    except SystemExit as e:                      # bedo_air dies on an HTTP error
        return None, str(e)
    except Exception as e:                       # noqa: BLE001 — the fallback must always be reachable
        return None, f'{type(e).__name__}: {e}'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('name', help='the row: look_behind_local, day_ahead_local or facts_local')
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    d, why = fetch(a.name)
    if not d:
        print(f'settings: {a.name} not read from Airtable ({why}) — using the skill\'s own copy', file=sys.stderr)
        sys.exit(1)
    tmp = a.out + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(d, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, a.out)
    print(f'settings: {a.name} from Airtable ({BASE_NAME} › {TABLE_NAME})')


if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    main()
