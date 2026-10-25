import sys, json, re, datetime as dt
import os
D=os.environ.get('RINGS_DIR','.')   # a working folder: look_behind_local.json, scripts/, data/ (as the day behind's prep leaves it)
sys.path.insert(0, D+'/scripts')
import week_look_behind as W, bedo_reader
DAY=sys.argv[1] if len(sys.argv)>1 else '2026-10-23'
L=json.load(open(D+'/look_behind_local.json')); S=L['fields']['stream']; PF=L['fields']['practices']
off=dt.timedelta(hours=L['utc_offset_hours'])
loc=lambda ts: (dt.datetime.fromisoformat(ts.replace('Z','+00:00'))+off).replace(tzinfo=None) if ts else None
day=dt.date.fromisoformat(DAY); s0=dt.datetime.combine(day,dt.time()); e0=s0+dt.timedelta(days=1)
low=lambda p: re.sub(r'^[^\w]+','',p or '').strip().lower()
FLOW={low(W.sv(bedo_reader.cells(r).get(PF['name']))) for r in bedo_reader.complete(D+'/data/practices.json')
      if W.sv(bedo_reader.cells(r).get(PF['group'])) == 'flow'}
seen={}
import glob
for p in sorted(glob.glob(D+'/data/w*.json'),reverse=True):
    for r in bedo_reader.complete(p):
        if r['id'] in seen: continue
        c=bedo_reader.cells(r); g=lambda k: W.sv(c.get(S[k])) if S.get(k) else None
        seen[r['id']]=dict(t=g('title') or '',p=g('practice') or '',st=g('status') or '',a=loc(c.get(S['when'])),b=loc(c.get(S['end'])),
            dev=g('device') or '',who=c.get(S['person']),rh=((g('rhythm') or '').split(',')[0]).strip(),spent=c.get(S['spent']))
names=lambda v: [] if not v else ([W.sv(x) if isinstance(x,dict) else x for x in v] if isinstance(v,list) else [x.strip() for x in str(v).split(',')])
TICK=5
SLEEP={'sleep','nap'}; PREP={'dinner prep','meal prep','cooking','lunch prep','breakfast prep'}
EAT={'breakfast','lunch','dinner','snack','brunch','dessert','coffee','smoothie','evening tea','tea','morning water','water','other consumable','drink'}     # nutrition: food and drink (24 Oct 2026)
MOVE={'morning movement','walking','hip exercises','strength training','barre','cycling','rowing','yoga','squat','sun salutations','morning sun','evening sun','exercise','stretch'}
BOOK={'book','morning book','reading','audiobook'}
TV={'show','movie','video'}
SCREENISH={'action','log','text','ai chat','video call','phone','usage check','calendar event','look ahead','look behind','intention check','journal','insight'}
MOM={'highlight','glimmer','gratitude','insight','milestone','journal'}
RINGS=[('sleep','😴','Sleep',[('sleep','asleep, in bed')]),
       ('flow','🌗','Flows',[('flow','dawn and dusk')]),
       ('food','🍽️','Food',[('eat','making it and eating it')]),
       ('move','🚶‍♀️','Moving',[('move','movement and time outside')]),
       ('body','🌿','Body',[('eat','food: making it and eating it'),('move','moving: movement and time outside')]),
       ('work','💼','Working',[('work','professional work'),('system','be•do'),('care','caretaking')]),
       ('enjoy','🎈','Recreation',[('enjoy','reading, shows, play, time together, glimmers')]),
       ('screen','📱','On a screen',[('screen','on a screen')])]
A={k:[None]*1440 for k,*_ in RINGS}
A['drive']=[None]*1440
A['cook']=[None]*1440
A['other']=[None]*1440
ENJOY={'book','reading','audiobook','show','movie','video','game','glimmer','play','social','song','music','puzzle','outing','fresh air','video call'}   # being: what she enjoyed (24 Oct 2026); it may overlap caretaking
CARE_PR={'clean','laundry','laundry move','care task','dishes','tidy','errand',
         'shower','bath','evening hygiene','getting ready','skincare'}     # caring for herself is caretaking too (24 Oct 2026)
CARE=json.load(open(os.environ['RINGS_CARE'])) if os.environ.get('RINGS_CARE') else {}
CARE_RH=tuple(CARE.get('rhythms') or ())      # rhythms whose rows are caretaking
CARE_WHO=tuple(CARE.get('people') or ())      # the people whose care is caretaking
WIN={'dawn':[],'dusk':[]}; held={}
TT={}
def paint(ring,kind,a,b,title=None):
    i,j=max(0,int((a-s0).total_seconds()//60)),min(1440,int((b-s0).total_seconds()//60))
    PRI={'work':0,'care':1,'system':2}       # on the working ring: a be•do session running beside the school run is still the school run
    for m in range(i,j):
        if A[ring][m] is None or (ring=='work' and PRI.get(kind,9)<PRI.get(A[ring][m],9)): A[ring][m]=kind
        if title: TT.setdefault((ring,m),[]).append((kind,title))
    if title and j>i: held.setdefault(kind,[]).append(title) if title not in held.get(kind,[]) else None
moments=[]
for r in seen.values():
    if any(x in r['st'] for x in ('intention','potential','dropped','skipped')): continue
    a,b=r['a'],r['b']
    if not a: continue
    if not b and r['spent']: b=a+dt.timedelta(seconds=float(r['spent']))
    span = b is not None and b>a and b-a<=dt.timedelta(hours=14)
    if not span and not (s0<=a<e0): continue
    if span and (b<=s0 or a>=e0): continue
    pr=low(r['p']); t=re.sub(r'^[^\w]+','',r['t']).split(' — ')[0].strip()
    bb=b if span else a+dt.timedelta(minutes=TICK)
    if (pr in MOM or re.search(bedo_reader.FACTS['garden'].get('shared_pattern') or r'$^', pr)) and s0<=a<e0:
        moments.append(dict(m=int((a-s0).total_seconds()//60),g=r['p'].split()[0] if r['p'] else '·',t=t,p=pr,d=int((b-a).total_seconds()//60) if span else 0))
    if pr in SLEEP and span: paint('sleep','sleep',a,b)
    if pr in PREP: paint('cook','cook',a,bb,t)
    if pr in EAT: paint('food','eat',a,bb,t)
    if pr in MOVE: paint('move','move',a,bb,t)
    if pr in FLOW or pr in ('dawn flow close','dusk flow close'):
        k='dawn' if a.hour<15 else 'dusk'; paint('flow','flow',a,bb,t); WIN[k].append(a)
    if pr=='driving' and span: paint('drive','drive',a,b)
    care = pr in CARE_PR or any(x in r['rh'] for x in CARE_RH) or (span and pr in ('log','driving') and any(w in r['t'] or any(w in n for n in names(r['who'])) for w in CARE_WHO))
    if care and span: paint('work','care',a,b,t)
    elif r['rh'] and span and pr=='action' and (b-a)>=dt.timedelta(minutes=10):
        paint('work','system' if r['rh']=='be•do' else 'work',a,b,t)
    if span:
        i,j=max(0,int((a-s0).total_seconds()//60)),min(1440,int((b-s0).total_seconds()//60))
        for m in range(i,j):
            if A['other'][m] is None: A['other'][m]='pending'
            TT.setdefault(('other',m),[]).append(('other',t))
        if pr not in SLEEP|PREP|EAT|MOVE|FLOW and not (r['rh'] and pr=='action') and not care: held.setdefault('other',[]).append(t) if t not in held.get('other',[]) else None
    if pr in ENJOY and span: paint('enjoy','enjoy',a,b,t)
    d=r['dev'].lower()
    if 'laptop' in d or 'desktop' in d or 'tv' in d or pr in TV: paint('screen','screen',a,bb,t)
    if 'phone' in d: paint('screen','screen',a,bb if pr in SCREENISH else a+dt.timedelta(minutes=TICK),t)
    who=[]
    if who and span:
        for n in who: paint('people','people',a,b); held.setdefault('who',{}); held['who'][n]=held['who'].get(n,0)
        i,j=max(0,int((a-s0).total_seconds()//60)),min(1440,int((b-s0).total_seconds()//60))
        for n in who: held['who'][n]+=max(0,j-i)
for m in range(1440):
    if A['other'][m]=='pending' and any(A[k][m] for k in ('sleep','flow','food','move','work')): A['other'][m]=None
    elif A['other'][m]=='pending': A['other'][m]='other'
# sleep from Oura when it can be read: each night's real span, the minute the need was met
# (asleep minutes, counted through the night's five-minute phases), and Oura's best bedtime window
# for the night that starts this evening (24 Oct 2026: am I meeting my sleep need, or way over or under)
import urllib.request
def oura(ep, a, b):
    try:
        u=f'https://api.ouraring.com/v2/usercollection/{ep}?start_date={a}&end_date={b}'
        return json.load(urllib.request.urlopen(u, timeout=20)).get('data') or []
    except Exception as e:
        print('oura: no read —', e); return []
NEED=int(os.environ['RINGS_SLEEP_NEED']) if os.environ.get('RINGS_SLEEP_NEED') else None   # minutes; Oura's app shows it, the API doesn't
nights=[]; window=None
OS=oura('sleep', (day-dt.timedelta(days=1)).isoformat(), (day+dt.timedelta(days=2)).isoformat())
if OS:
    A['sleep']=[None]*1440
    for r in OS:
        if r.get('type') not in ('long_sleep','sleep'): continue
        bs=dt.datetime.fromisoformat(r['bedtime_start']).replace(tzinfo=None); be=dt.datetime.fromisoformat(r['bedtime_end']).replace(tzinfo=None)
        if be<=s0 or bs>=e0: continue
        for m in range(max(0,int((bs-s0).total_seconds()//60)), min(1440,int((be-s0).total_seconds()//60))): A['sleep'][m]='sleep'
        met=None
        if NEED and r.get('sleep_phase_5_min'):
            got=0
            for i,ch in enumerate(r['sleep_phase_5_min']):
                if ch in '123': got+=5
                if got>=NEED: met=bs+dt.timedelta(minutes=5*(i+1)); break
        nights.append(dict(start=bs.isoformat(), end=be.isoformat(), asleep=r['total_sleep_duration']//60, inbed=r['time_in_bed']//60,
                           need=NEED, met=int((met-s0).total_seconds()//60) if met and s0<=met<e0 else None, met_at=met.isoformat() if met else None,
                           a=max(0,int((bs-s0).total_seconds()//60)), b=min(1440,int((be-s0).total_seconds()//60))))
    ST=[x for x in oura('sleep_time', (day-dt.timedelta(days=14)).isoformat(), (day+dt.timedelta(days=1)).isoformat()) if x.get('optimal_bedtime')]
    if ST:
        x=ST[-1]['optimal_bedtime']; nxt=e0     # offsets are from the midnight that ends this day
        window=[int((nxt+dt.timedelta(seconds=x['start_offset'])-s0).total_seconds()//60), int((nxt+dt.timedelta(seconds=x['end_offset'])-s0).total_seconds()//60), ST[-1]['day']]
def runs(arr, ring=None):
    out=[];cur=None
    for m,x in enumerate(arr+[None]):
        if x!=cur:
            if cur is not None: out[-1][2]=m
            if x is not None: out.append([x,m,m+1,[]])
            cur=x
    for r in out:      # what the chunk was: the rows of its own kind inside it, in order
        for m in range(r[1],r[2]):
            for k,t in [x for rg in {'body':('food','move'),'being':('food','move','enjoy'),'doing':('work','cook')}.get(ring,(ring,)) for x in TT.get((rg,m),[])]:
                if k==r[0] and t not in r[3]: r[3].append(t)
        r[3]=r[3][:4]
    return out
# sitting to eat is not moving (24 Oct 2026): a meal's minutes come out of the moving ring; making food is food, not movement
for m in range(1440):
    if A['food'][m] is not None: A['move'][m]=None
# what she was doing, not what the system was doing (24 Oct 2026): a session row records when the
# laptop ran, so its minutes are her work only while she wasn't driving, eating, moving or asleep
for m in range(1440):
    if A['work'][m] in ('work','system') and (A['drive'][m] or A['food'][m] or A['move'][m] or A['sleep'][m]):
        A['work'][m]=None
for m in range(1440):
    A['body'][m]=A['food'][m] or A['move'][m]
asleep=lambda m: 0<=m<1440 and A['sleep'][m] is not None
for m in range(1440):
    if asleep(m): A['flow'][m]=None
win={}
for k,v in WIN.items():
    ms=[int((x-s0).total_seconds()//60) for x in v if 0<=int((x-s0).total_seconds()//60)<1440 and not asleep(int((x-s0).total_seconds()//60))]
    if ms:
        a,b=min(ms),min(1440,max(ms)+TICK)
        while b>a and asleep(b-1): b-=1
        win[k]=[a,b]
A['being']=[None]*1440; A['doing']=[None]*1440
for m in range(1440):
    A['being'][m]=A['food'][m] and 'eat' or A['move'][m] or A['enjoy'][m]
    A['doing'][m]=A['work'][m] or A['cook'][m]
RINGS=[x for x in RINGS if x[0] not in ('food','move','body','work','enjoy','other')]
RINGS.insert(2,('being','🌿','Being',[('eat','eating'),('move','moving'),('enjoy','recreation')]))
RINGS.insert(3,('doing','🔨','Doing',[('work','professional work'),('care','caretaking'),('cook','cooking'),('system','be•do')]))
A.pop('drive')
OUT=dict(day=f"{day:%A} {day.day} {day:%B}",rings=[dict(k=k,e=e,n=n,kinds=[dict(k=kk,n=nn,min=sum(1 for x in A[k] if x==kk),held=(held.get(kk) or [])[:6]) for kk,nn in kinds],
          runs=runs(A[k],k),total=sum(1 for x in A[k] if x)) for k,e,n,kinds in RINGS],
         win=win,nights=nights,window=window,moments=sorted(moments,key=lambda x:x['m']),who=sorted((held.get('who') or {}).items(),key=lambda x:-x[1]),
         awake=1440-sum(1 for x in A['sleep'] if x))
json.dump(OUT,open(f'rings-{DAY}.json','w'),ensure_ascii=False)
for r in OUT['rings']: print(r['n'],r['total'],[(x['n'],x['min']) for x in r['kinds']])
print('win',win,'moments',len(moments),'who',OUT['who'][:5])
