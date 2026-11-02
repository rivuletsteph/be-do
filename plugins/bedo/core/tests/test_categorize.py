# -*- coding: utf-8 -*-
"""The categorizing pass and the day-page audit (2 Nov 2026): one test for each thing she had to catch by
hand on Sunday 1 Nov's day page, then Sunday itself rebuilt from code alone.

Every row is invented, or Sunday's own times with every name and word replaced (fixture_sunday.py).

    python3 plugins/bedo/core/tests/test_categorize.py
"""
import datetime as dt, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.dirname(HERE)
WLB = os.path.join(CORE, '..', 'skills', 'bedo-week-look-behind')
sys.path[:0] = [HERE, CORE, os.path.join(WLB, 'scripts')]
import bedo_categorize as BC  # noqa: E402
import bedo_dayaudit as BD  # noqa: E402
import bedo_photos as PH  # noqa: E402
import bedo_remaining as RM  # noqa: E402
import bedo_entry as E  # noqa: E402
import bedo_fill as FL  # noqa: E402
from day_rings import day_rings  # noqa: E402
import fixture_sunday as FX  # noqa: E402

ME, PA, KID = '♋ Self', '♐Partner', '♑Kid'
L = dict(self_person=ME, people=dict(self=ME, partner=PA, kid=KID), household=['Partner', 'Kid'],
         utc_offset_hours=-6, time_zone='America/Chicago', system_rhythm='be•do',
         care=dict(pet=dict(names=['Pip'])), rhythm_wellness={'Tales': '💖 spirit', 'Outings': '🔥 fire'},
         quiet_topics=['quiet topic'])
DAY = dt.date(2026, 11, 3)            # a Tuesday, CST (UTC-6)
NOT_LIVED = {'▫️potential', '⬜ intention', '✖️ dropped', '⨂ skipped'}
n = 0


def z(h, m=0, day=DAY):
    return (dt.datetime.combine(day, dt.time(h, m)) + dt.timedelta(hours=6)).strftime('%Y-%m-%dT%H:%M:00.000Z')


def row(p, a, b=None, **kw):
    global n
    n += 1
    return dict(id=kw.pop('id', f'x{n}'), practice=p, title=kw.pop('title', p), datetime=z(*a), end=z(*b) if b else None,
                status=kw.pop('status', '◉ done'), **kw)


def calls(rows, rule=None, ctx=None, day=DAY, settings=L):
    out = BC.run(rows, day, settings, ctx or BC.Ctx())
    return [c for c in out if rule is None or c['rule'] == rule]


def rings(rows, day=DAY, settings=L, sleep=None):
    return day_rings([dict(r, when=r['datetime'], spent=r.get('time_spent')) for r in rows], day, settings,
                     frozenset(), NOT_LIVED, sleep)


# 1 · alone vs with family: at home she is with the household unless a row says alone; a minute nothing covers
#     is not alone; a row inside one that names its company takes it; the sleep row names her (2 Nov 2026)
R1 = [row('😴 sleep', (0, 0), (6, 0), person=f'{PA}, {KID}'),
      row('🍳 lunch prep', (12, 0), (12, 30)),
      row('📺 show', (20, 0), (21, 0), title='📺 a show, on my own'),
      row('📲 capture', (20, 10), (20, 30)),
      row('🚶‍♀️ walking', (17, 0), (17, 30), details='Pip and I are walking.'),
      row('📺 show', (21, 0), (21, 30), title='📺 a show, not alone this time')]
C1 = {c['title']: c['new'] for c in calls(R1) if c['field'] == 'person'}
assert C1['🍳 lunch prep'] == f'{PA}, {KID}', C1                       # at home: with them by default
assert C1['📺 a show, on my own'] == ME and C1['🚶‍♀️ walking'] == ME, C1   # her words, and just her and the dog
assert C1['📲 capture'] == ME, C1                                       # inside the show on her own
assert C1['📺 a show, not alone this time'] == f'{PA}, {KID}', C1            # 'not alone' is not alone
assert C1['😴 sleep'] == f'{ME}, {PA}, {KID}', C1                      # the night names her
W1 = rings(BC.apply(R1, calls(R1)))['who']
assert W1['alone'] == 60 + 30, W1                                       # the show and the walk; never an empty minute
assert W1['family'] > 600 and W1['social'] == 0, W1
print('ok 1 — with the family by default; alone only where a row says so; the night names her')

# 2 · riding vs driving: a family car trip is 🚗 travel (being); at the wheel only by her word (2 Nov 2026)
R2 = [row('🚗 driving', (9, 0), (10, 0), title='🚗 driving up to the lake'),
      row('🚗 driving', (15, 0), (16, 0), title='🚗 to the store', details='I drove us home.'),
      row('🚗 driving', (11, 0), (11, 30), person=KID, title='🚗 Kid to class')]
C2 = calls(R2, 'travel')
assert [c['title'] for c in C2] == ['🚗 driving up to the lake'] and C2[0]['new'] == '🚗 travel', C2
K2 = {b['k']: {k['k']: k['min'] for k in b['kinds']} for b in rings(BC.apply(R2, calls(R2)))['bands']}
assert K2['being']['travel'] == 60 and K2['doing']['drive'] == 60 + 30, K2
print('ok 2 — riding with the family is travel, being; at the wheel only when she says or it is just her and Kid')

# 3 · wellness follows the rhythm: her named rhythms always, a feed keeps its own, an empty one by the element
#     and its being pair (2 Nov 2026)
CTX3 = BC.Ctx(rhythms={'Tales': '🔥 fire', 'Outings': '🔥 fire', 'Body': '🌎 earth', 'be•do': '💨 air'},
              catalog={'🚶‍♀️ walking': dict(wellness='🤸‍♀️ body')})
R3 = [row('🎥 movie', (8, 0), (10, 0), rhythm='Tales', wellness='🩷 heart'),
      row('🚴‍♀️ cycling', (14, 0), (15, 0), rhythm='Outings', wellness='🤸‍♀️ body'),
      row('⭐ highlight', (14, 30), rhythm='Outings', wellness='🩷 heart'),
      row('📌 social', (7, 0), (7, 20), rhythm='Tales', wellness='🧠 mind'),
      row('🚶‍♀️ walking', (16, 0), (16, 30), rhythm='Body'),
      row('⚡ action', (18, 0), (18, 30), rhythm='be•do'),
      row('🎵 song', (19, 0), (19, 5), rhythm='Tales', wellness='🧠 mind',
          details='———\n[be•do] wellness mind is her word')]
C3 = {c['title']: c['new'] for c in calls(R3, 'wellness', CTX3)}
assert C3 == {'🎥 movie': '💖 spirit', '🚴‍♀️ cycling': '🔥 fire', '⭐ highlight': '🔥 fire',
              '🚶‍♀️ walking': '🤸‍♀️ body', '⚡ action': '💨 air'}, C3
assert FL.deduce(dict(practice='📺 show', rhythm='Tales', person=KID), FL.Context(local=L))[0]['wellness'][0] == '💖 spirit'
print('ok 3 — the rhythm decides: stories are spirit, adventures fire, a feed its own, her word over all')

# 4 · the day's intention and highlight show where she'd look: the balance, the story, the moments
R4 = [row('⚡ intention check', (8, 0), title='⚡ intention check — an adventure: the lake trail'),
      row('🚴‍♀️ cycling', (14, 0), (15, 0), title='🚴‍♀️ the lake trail by bike', rhythm='Outings', wellness='🤸‍♀️ body'),
      row('⭐ highlight', (14, 30), title='⭐ the dog pulling the bike', rhythm='Outings', wellness='🩷 heart')]
G4 = rings(R4)
A4 = BD.audit(R4, DAY, L, G4, dict(lead='a quiet day', story=[['🌙', 'a show']]))
assert {i['check'] for i in A4 if i['kind'] == 'fix'} == {'intention', 'highlight'}, A4
assert any('story' in i['line'] for i in A4 if i['check'] == 'intention'), A4
R4b = BC.apply(R4, calls(R4, 'wellness', CTX3))
A4b = BD.audit(R4b, DAY, L, rings(R4b), dict(lead='the lake trail', story=[['🚴', 'the lake trail, the dog pulling the bike']]))
assert not [i for i in A4b if i['kind'] == 'fix'], A4b
print('ok 4 — the intention and the highlight are checked on the balance, the story and the moments')

# 5 · a session row counts over her stretches only, never its envelope (day_rings, 2 Nov 2026)
R5 = [row('⚡ action', (11, 0), title='⚡ a chat touched twice', rhythm='be•do', wellness='💨 air', person=f'{PA}, {KID}',
          details='———\n[be•do] stretches: 11:00–11:10 · 8:00–8:10 = 20m')]
G5 = rings(R5)
assert G5['energy']['min']['air'] == 20, G5['energy']
assert G5['who']['people'][0]['min'] == 20, G5['who']['people']           # the family over her stretches, not 9 hours
print('ok 5 — a session row counts its stretches, on the balance and on the who card')

# 6 · every chat she worked in that day has its time: a session entry, or 📲 capture rows for a window chat
S6 = [dict(url='session_a', title='a drive chat', stretches=[[z(9), z(9, 40)]]),
      dict(url='session_b', title='✔️1103 my day', stretches=[[z(7), z(7, 30)]]),
      dict(url='session_c', title='another drive chat', stretches=[[z(13), z(13, 20)]])]
R6 = [row('📲 capture', (7, 0), (7, 10), chat='https://claude.ai/code/session_b'),
      row('⚡ action', (13, 0), title='⚡ the other chat', time_spent=1200, chat='https://claude.ai/code/session_c')]
A6 = [i['line'] for i in BD.check_chats(R6, S6, DAY, L)]
assert len(A6) == 2 and 'no session entry' in A6[0] and 'window chat' in A6[1], A6
print('ok 6 — a chat with her turns and no row is named; a window chat needs capture rows for its minutes')

# 7 · point rows with a usual length get it: the catalog, else her own weeks, else a first guess
H7 = [row('🧎‍♀️ hip exercises', (8, 0), (8, 20)), row('🧎‍♀️ hip exercises', (8, 0), (8, 20)),
      row('🧎‍♀️ hip exercises', (8, 0), (8, 30))]
R7 = [row('🤸🏻‍♀️ morning movement', (7, 10)), row('🧎‍♀️ hip exercises', (7, 30)), row('🌌 evening blessing', (22, 30)),
      row('⭐ highlight', (15, 0)), row('🌈 supplements', (12, 0))]
CTX7 = BC.Ctx(catalog={'🤸🏻‍♀️ morning movement': dict(typical=12), '🌈 supplements': dict(zero=True)}, history=H7)
C7 = {c['title']: c['new'][11:16] for c in calls(R7, 'length', CTX7)}
assert C7 == {'🤸🏻‍♀️ morning movement': z(7, 22)[11:16], '🧎‍♀️ hip exercises': z(7, 50)[11:16],
              '🌌 evening blessing': z(22, 34)[11:16]}, C7
print('ok 7 — movement, hips and the blessing cover their minutes; a highlight and a pill stay points')
# what she says wins, and it changes (2 Nov 2026): her words on the row, then the last length she gave, then the catalog
H7b = H7 + [row('🧎‍♀️ hip exercises', (8, 0), details='my hips took 12 minutes today')]
R7b = [row('🧎‍♀️ hip exercises', (7, 30)), row('🤸🏻‍♀️ morning movement', (7, 10), details='about 5 min of movement'),
       row('⚔️ quest', (20, 0), details='in bed about 9 hours')]                 # not a practice with a length
C7b = {c['title']: c['new'][11:16] for c in calls(R7b, 'length', BC.Ctx(catalog=CTX7.catalog, history=H7b))}
assert C7b == {'🧎‍♀️ hip exercises': z(7, 42)[11:16], '🤸🏻‍♀️ morning movement': z(7, 15)[11:16]}, C7b
print('ok 7b — the length she gave wins over her usual and the catalog')

# 8 · estimated 📝 filler gives way to rows from evidence
EST = '———\n[be•do] ESTIMATED FROM CONTEXT: between the rows.'
R8 = [row('📝 log', (5, 0), (8, 0), title='📝 the early morning (estimated)', details=EST),
      row('📲 capture', (5, 0), (5, 30)), row('📌 social', (6, 0), (8, 0)),
      row('📝 log', (13, 0), (13, 20), title='📝 packing (estimated)', details=EST), row('📲 capture', (13, 0), (13, 15)),
      row('📝 log', (18, 0), (18, 9), title='📝 a short stretch (estimated)', details=EST)]
C8 = [(c['title'].split()[1], c['field'], c['new']) for c in calls(R8, 'filler')]
assert C8 == [('the', 'datetime', z(5, 30)), ('the', 'end', z(6, 0)), ('packing', 'status', '✖️ dropped')], C8
print('ok 8 — a filler keeps only the gap the evidence leaves, and goes when none is left')

# 9 · the clock after the time change: a stamp an hour off Oura's own instant, on that day only
NOV1 = dt.date(2026, 11, 1)
SL9 = [dict(start='2026-10-31T23:02:17.000-05:00', end='2026-11-01T06:05:47.000-05:00')]   # 5:05 CST, in the old offset
R9 = [dict(id='s', practice='😴 sleep', title='😴 sleep', status='● log', datetime='2026-11-01T04:02:00.000Z',
           end='2026-11-01T12:05:00.000Z', person=ME),
      dict(id='w', practice='😶 wake', title='😶 wake', status='◉ done', datetime='2026-11-01T12:05:00.000Z')]
C9 = {(c['id'], c['field']): c['new'] for c in calls(R9, 'clock', BC.Ctx(sleep=SL9), NOV1)}
assert C9 == {('s', 'end'): '2026-11-01T11:05:00.000Z', ('w', 'datetime'): '2026-11-01T11:05:00.000Z'}, C9
assert not calls(R9, 'clock', BC.Ctx(sleep=SL9), DAY), 'only on the day the clocks change'
print('ok 9 — on the day the clocks fall back, sleep and wake take Oura\'s instant, not its old-offset clock')

# 10 · photos: at most six on the day page, the highlights, never near-duplicates (2 Nov 2026)
T10 = dt.datetime(2026, 11, 1, 9)
hl = dict(practice='⭐ highlight', person=KID)
P10 = [dict(t=T10 + dt.timedelta(minutes=10 * i, seconds=s), src=f'p{i}{s}', keeper=True,
            row=hl if i == 4 else dict(practice='📍 location') if i % 2 else dict(practice='🎥 movie', person=KID))
       for i in range(9) for s in (0, 20)]
chosen, left = PH.select(P10, ME)
assert len(chosen) == 6 and len(left) == 12, (len(chosen), len(left))
ts = sorted(p['t'] for p in chosen)
assert all((b - a).total_seconds() > 90 for a, b in zip(ts, ts[1:])), ts
assert any(p['row'] is hl for p in chosen) and sum(p['row'].get('practice') == '📍 location' for p in chosen) <= 1
assert [i['check'] for i in BD.check_photos([p['t'] for p in P10])] == ['photos', 'photos']
print('ok 10 — six photos, one per moment, the highlight and people first')

# 11 · colors: doing warm, being cool, sleep dark navy (the engine's tokens, light theme)
css = open(os.path.join(WLB, 'assets', 'week_look_behind_engine.html'), encoding='utf-8').read()
light_css = css[css.index(':root{--rb-flow:'):]
tok = dict(re.findall(r'--rb-([a-z-]+):(#[0-9A-Fa-f]{6})', light_css[:light_css.index('@media')]))


def hls(h):
    import colorsys
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))
    hh, ll, ss = colorsys.rgb_to_hls(r, g, b)
    return hh * 360, ll


for k in ('work', 'care', 'family', 'community', 'pet', 'home', 'cook', 'drive', 'system'):
    assert hls(tok[k])[0] < 60 or hls(tok[k])[0] > 330, (k, tok[k], hls(tok[k]))
for k in ('eat', 'move', 'recreation', 'travel', 'personal', 'social'):
    assert 70 < hls(tok[k])[0] < 290, (k, tok[k], hls(tok[k]))
h, light = hls(tok['sleep'])
assert 200 < h < 250 and light < .45 and hls(tok['sleep-deep'])[1] < .3, (tok['sleep'], tok['sleep-deep'])
print('ok 11 — doing is warm, being is cool, the night is dark navy')

# the folds: Wednesday is money day; a quiet topic is never raised; Sunday's turn to the week
R12 = [row('⚡ action', (9, 0), status='⬜ intention', title='⚡ Pay the water bill'),
       row('⚡ action', (9, 0), status='⬜ intention', title='⚡ Pay the card', target=z(12, 0, DAY + dt.timedelta(days=1))),
       row('⚡ action', (9, 0), status='▫️potential', title='⚡ a refund someday'),
       row('⚡ action', (9, 0), status='▶️ in motion', title='⚡ the refund', waiting_on='them'),
       row('⚡ action', (9, 0), status='⬜ intention', title='⚡ teach Kid card games')]
C12 = calls(R12, 'money')
assert [(c['title'], c['new']) for c in C12] == [('⚡ Pay the water bill', z(12, 0, DAY + dt.timedelta(days=1)))], C12
assert dt.date.fromisoformat(C12[0]['new'][:10]).weekday() == 2
A13 = BD.audit([row('⭐ highlight', (9, 0), title='⭐ a quiet topic eased')], DAY, L, None,
               dict(lead='x', story=[['·', 'nothing']]))
assert A13 == [], A13
SUN = dt.date(2026, 11, 8)
close = dict(practice='🌅 dawn flow close', datetime='2026-11-08T15:00:00.000Z')
assert RM.week_turn(SUN, [close]).startswith('next: ready for the transition')
assert RM.week_turn(SUN, [close, dict(practice='📲 capture', title='📲 my week — the close',
                                      datetime='2026-11-08T16:00:00.000Z')]) is None
assert RM.week_turn(SUN - dt.timedelta(days=1), [close]) is None and RM.week_turn(SUN, []) is None
print('ok — money to Wednesday, a quiet topic never raised, Sunday asks about the week once the dawn flow is through')

# the entry check carries the calls on one row as it is written
ent = E.problems(dict(practice='🚗 driving', title='🚗 up to the lake', status='◉ done', datetime=z(9), end=z(10),
                      person=f'{PA}, {KID}', device='🚫 none', wellness='🩷 heart', rhythm='Outings'),
                 fill=FL.Context(local=L))
assert any(p.startswith('practice: 🚗 driving → 🚗 travel') for p in ent), ent
assert any(p.startswith('wellness: 🩷 heart → 🔥 fire') for p in ent), ent
print('ok — the entry check names the calls on a row as it is written')

# Sunday 1 Nov, rebuilt from code alone: the rows as the chats first wrote them, the pass, the page's rings
S = FX.SUNDAY
SL, SD = S['settings'], dt.date.fromisoformat(S['day'])
ctx = BC.Ctx(rhythms=S['rhythms'], catalog=S['catalog'], sleep=S['sleep'])
first = rings(S['rows'], SD, SL, S['sleep'])
C = BC.run(S['rows'], SD, SL, ctx)
rows = BC.apply(S['rows'], C)
got = rings(rows, SD, SL, S['sleep'])
acc = S['accepted']
assert first['energy']['min']['fire'] < acc['fire'] * .6 and first['energy']['min']['spirit'] < acc['spirit'] / 4, first['energy']
E1 = got['energy']['min']
assert abs(E1['fire'] - acc['fire']) <= 15, E1                         # the adventure, about 4 h
assert abs(E1['spirit'] - acc['spirit']) <= 25, E1                     # spirit, about 6 h
assert got['wake'] == 305 and got['inbed_day'] > 350, (got['wake'], got['inbed_day'])   # the night, an hour corrected
assert {c['rule'] for c in C} >= {'clock', 'length', 'filler', 'sleep', 'company', 'travel', 'wellness'}, {c['rule'] for c in C}
# alone: by her rule, only the walk with the dog and the show on her own; the my week hour is the one question
A = BD.audit(rows, SD, SL, got, S['words'], None, None, C)
assert not [i for i in A if i['kind'] == 'fix'], A
asks = [i for i in A if i['kind'] == 'ask']
assert len(asks) == 1 and asks[0]['check'] == 'company' and '11:01' in asks[0]['line'], asks
assert 100 <= got['who']['alone'] <= 130, got['who']['alone']
pid = {x['id'] for x in asks[0]['if_alone_patch']}
on_my_own = [dict(r, person=SL['self_person']) if r['id'] in pid else r for r in rows] + [
    dict(id='her', details='On my own on the couch.', **asks[0]['if_alone'])]
alone = rings(on_my_own, SD, SL, S['sleep'])['who']['alone']
assert abs(alone - acc['alone']) <= 30, alone                           # her answer: about 3.5 h, as she accepted
print(f'ok — Sunday from code alone: fire {E1["fire"]} (accepted {acc["fire"]}), spirit {E1["spirit"]} '
      f'({acc["spirit"]}), alone {got["who"]["alone"]} by her rule, {alone} once she says the my week hour was hers '
      f'({acc["alone"]})')
