# How the day went — the rings prototype

Built with her on 24 Oct 2026 (see `docs/day-behind-cards.md`), on Friday 23 Oct.
Not yet part of the builder; it is folded in once the card is settled.

    RINGS_DIR=<the day behind's working folder> RINGS_CARE=care.json RINGS_SLEEP_NEED=<minutes> python3 rings.py YYYY-MM-DD
    python3 rings_page.py YYYY-MM-DD        # writes how-friday-went.html

`RINGS_DIR` is a folder the day behind's prep left behind: `look_behind_local.json`,
`scripts/` (the builder and core) and `data/w*.json`, `data/practices.json`.
`care.json` names what counts as caretaking, and stays local:
`{"rhythms": ["<a rhythm name part>", ...], "people": ["<a name>", ...]}`.
Sleep is read from Oura when the session can reach `api.ouraring.com` (the cloud
environment's key): each night's real span, the minute the night's asleep time
reached the need (from `sleep_phase_5_min`), and Oura's best bedtime window
(`sleep_time`, the latest record). The need itself is not in Oura's API; it is
`RINGS_SLEEP_NEED`, from the app's Sleep Health page.
