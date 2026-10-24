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
EAT={'breakfast','lunch','dinner','snack','brunch','dessert'}     # food only, no drinks (24 Oct 2026)
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
       ('other','🧺','Other',[('other','everything else you did')]),
       ('screen','📱','On a screen',[('screen','on a screen')])]
A={k:[None]*1440 for k,*_ in RINGS}
A['drive']=[None]*1440
CARE_PR={'clean','laundry','laundry move','care task','dishes','tidy','errand'}
CARE=json.load(open(os.environ['RINGS_CARE'])) if os.environ.get('RINGS_CARE') else {}
CARE_RH=tuple(CARE.get('rhythms') or ())      # rhythms whose rows are caretaking
CARE_WHO=tuple(CARE.get('people') or ())      # the people whose care is caretaking
WIN={'dawn':[],'dusk':[]}; held={}
def paint(ring,kind,a,b,title=None):
    i,j=max(0,int((a-s0).total_seconds()//60)),min(1440,int((b-s0).total_seconds()//60))
    PRI={'work':0,'care':1,'system':2}       # on the working ring: a be•do session running beside the school run is still the school run
    for m in range(i,j):
        if A[ring][m] is None or (ring=='work' and PRI.get(kind,9)<PRI.get(A[ring][m],9)): A[ring][m]=kind
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
    if pr in MOM and s0<=a<e0: moments.append(dict(m=int((a-s0).total_seconds()//60),g=r['p'].split()[0] if r['p'] else '·',t=t))
    if pr in SLEEP and span: paint('sleep','sleep',a,b)
    if pr in PREP: paint('food','eat',a,bb,t)
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
        if pr not in SLEEP|PREP|EAT|MOVE|FLOW and not (r['rh'] and pr=='action') and not care: held.setdefault('other',[]).append(t) if t not in held.get('other',[]) else None
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
def runs(arr):
    out=[];cur=None
    for m,x in enumerate(arr+[None]):
        if x!=cur:
            if cur is not None: out[-1][2]=m
            if x is not None: out.append([x,m,m+1])
            cur=x
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
RINGS=[x for x in RINGS if x[0] not in ('food','move')]
A.pop('drive')
OUT=dict(day=f"{day:%A} {day.day} {day:%B}",rings=[dict(k=k,e=e,n=n,kinds=[dict(k=kk,n=nn,min=sum(1 for x in A[k] if x==kk),held=(held.get(kk) or [])[:6]) for kk,nn in kinds],
          runs=runs(A[k]),total=sum(1 for x in A[k] if x)) for k,e,n,kinds in RINGS],
         win=win,moments=sorted(moments,key=lambda x:x['m']),who=sorted((held.get('who') or {}).items(),key=lambda x:-x[1]),
         awake=1440-sum(1 for x in A['sleep'] if x))
json.dump(OUT,open(f'rings-{DAY}.json','w'),ensure_ascii=False)
for r in OUT['rings']: print(r['n'],r['total'],[(x['n'],x['min']) for x in r['kinds']])
print('win',win,'moments',len(moments),'who',OUT['who'][:5])
