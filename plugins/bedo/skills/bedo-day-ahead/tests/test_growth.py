"""Growth on base flow (261111_f16) and made-up times (261112_f20): a target be•do supplied is not late."""
import datetime as dt, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'scripts'))
import flow

assert flow.made_up("———\n[be•do] Target 4p is be•do's placeholder.")
assert flow.made_up("———\n[be•do] drive cleanup: into today's money block, her yes (target Wed 11 Nov, 11 AM).")
assert not flow.made_up("Due Fri.\n———\n[be•do] Target is the expense deadline from the mail.")
assert not flow.made_up("")

F = dict(status='s', practice='p', rhythm='r', end='e', when='w')
loc = lambda ts: dt.date.fromisoformat(ts[:10])
row = lambda st, pr, rh, w: {'cellValuesByFieldId': {'s': st, 'p': pr, 'r': rh, 'w': w}}
rows = [row('✅ done', '⚡ action', 'Drive A', '2026-11-10T15:00:00Z'),
        row('✅ done', '⚡ action', 'Drive B', '2026-11-09T15:00:00Z'),
        row('✅ done', '⚡ action', 'Drive A', '2026-11-01T15:00:00Z'),   # older than a week
        row('✅ done', '⚡ action', 'Home', '2026-11-10T15:00:00Z'),      # a rhythm, tending
        row('⬜ intention', '⚡ action', 'Drive A', '2026-11-10T15:00:00Z')]
g = flow.grew_on(dt.date(2026, 11, 12), rows, F, {'Home'}, set(), loc)
assert g == dict(steps=2, drives=2), g
print('ok — growth counts the steps closed on her drives in the last week; a placeholder target is not a deadline')
