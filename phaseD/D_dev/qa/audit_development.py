"""Read-only, independent consistency audit of the completed development."""
from pathlib import Path
import hashlib, json, math
import numpy as np
import pandas as pd

ROOT=Path(r'D:\论文集\phaseD'); OUT=ROOT/'D_dev'
checks=[]
def check(condition, text):
    assert bool(condition),text
    checks.append(text)
def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def load(name):return json.loads((OUT/name).read_text(encoding='utf-8-sig'))
rng=np.random.default_rng(20261051)
draws={scene:rng.integers(0,60,size=(2000,60)) for scene in ['S0','S2']}
def ci(q,column,scene):
    parts=[]
    for sc in (['S0','S2'] if scene=='pooled' else [scene]):
        seeds=q[q.scene==sc].groupby('record_id')[column].mean().reindex(range(1,61)).to_numpy()
        check(np.isfinite(seeds).all(),'Complete seed clusters for CI '+column+' '+sc)
        parts.append(seeds[draws[sc]].mean(axis=1))
    return np.percentile(np.mean(parts,axis=0),[2.5,97.5])

for name,want in [('PREREGISTRATION_PhaseD_20261003.md','af3ab68bbdfd8ecefbd042e9faaac001a16c28a8f73a2fc071b3e315a6090df5'),('PREREGISTRATION_PhaseD_ADDENDUM_20261003.md','fa6ccd779cb2ecfdff250778571963cdc77a170c187a95f85978a15638400344')]:
    check(sha(ROOT/name)==want,'Unmodified plan: '+name)
for name in ['BASELINE_MANIFEST_sha256.csv','code/SOURCE_MANIFEST_sha256.csv']:
    manifest=pd.read_csv(ROOT/name)
    for r in manifest.itertuples(index=False):
        check(sha(r[0])==r[1],'Unmodified manifest entry: '+str(r[0]))

check(load('../G_gates/gates.json')['all_pass'],'All G1-G8 gates passed')
check(not any((ROOT/'C_confirm').glob('**/*.mat')) if (ROOT/'C_confirm').exists() else True,'Confirmation MAT outputs absent')
f=load('FROZEN_METHOD.json');check(f['confirmation_started'] is False,'Frozen confirmation flag false')
key=['scene','snr_db','record_id','seed','input_hash']
tables={}
expected={'D1':20,'fixed':5,'rerunA':1,'rerunB':1,'grid':20}
for stage,n in expected.items():
    path=OUT/(stage+'_records.csv')
    if not path.exists():continue
    t=pd.read_csv(path);tables[stage]=t
    check(len(t)==840*n,stage+' row count')
    check(not t.duplicated(key+['Delta_s','arm','method']).any(),stage+' unique configurations')
    check(t.seed.eq(20260915+51000000+t.scene.map({'S0':10000,'S2':30000})+t.record_id).all(),stage+' phase-51 seeds')
    check(np.isfinite(t.eta).all() and t.eta.between(0,1).all(),stage+' finite eta in [0,1]')
    check((t.groupby(['scene','snr_db','record_id']).input_hash.nunique()==1).all(),stage+' paired input hashes')
    check(t.groupby(['scene','snr_db','record_id']).size().eq(n).all(),stage+' every record has all variants')
    for (delta,arm,method),q in t.groupby(['Delta_s','arm','method']):
        check(q.groupby(['scene','snr_db']).size().eq(60).all(),stage+' complete SNR cells '+str((delta,arm,method)))
    for column in ['gain_eta_vs_SMR','gain_eta_vs_VIT']:
        baseline='eta_'+column.split('_')[-1]
        check(np.allclose(t[column],t.eta-t[baseline],atol=5e-15,rtol=0),stage+' '+column+' consistency')
    check((t.harm_vs_SMR.astype(bool)==(t.eta<t.eta_SMR-.01)).all(),stage+' harm threshold strict')

d1=load('D1_DECISION.json'); rules=d1['rules']; eligible=[d for d in [30,15,10,7.5,6] if all(r['qualifies'] for r in rules if r['Delta_s']==d)]
check(eligible==d1['eligible_intersection'],'D1 eligible intersection')
for r in rules:
    q=tables['D1'];q=q[(q.scene==r['scene'])&(q.method==r['method'])&(q.arm=='scaled')&(q.Delta_s==r['Delta_s'])]
    check(math.isclose(float((q.eta-q.eta_VIT).mean()),r['G'],rel_tol=1e-12,abs_tol=1e-14),'D1 raw-record rule input '+str((r['scene'],r['method'],r['Delta_s'])))
    check(np.allclose(ci(q,'gain_eta_vs_VIT',r['scene']),[r['G_lo'],r['G_hi']],atol=1e-13,rtol=1e-12),'D1 reported gain interval '+str((r['scene'],r['method'],r['Delta_s'])))
for scene in ['S0','S2']:
    for method in ['F02','UNB']:
        rows=[r for r in rules if r['scene']==scene and r['method']==method]
        gm=max(r['G'] for r in rows);threshold=.95*gm if gm>0 else gm-.005
        check(all(r['Gmax_all_seven']==gm and r['threshold']==threshold and r['qualifies']==(r['G']>=threshold) for r in rows),'D1 threshold '+scene+' '+method)
if eligible:chosen=max(eligible)
else:
    gaps={d:max(r['Gmax_all_seven']-r['G'] for r in rules if r['Delta_s']==d) for d in [30,15,10,7.5,6]}
    best=min(gaps.values());chosen=max(d for d,gap in gaps.items() if gap<=best+1e-4)
check(chosen==d1['Delta_s']==f['Delta_s'],'D1 independently reproduced selection')

a=tables['D1'];a=a[(a.Delta_s==chosen)&(a.arm=='scaled')&a.method.isin(['F02','UNB'])]
b=tables['fixed'];b=b[b.method.isin(['F02','UNB'])]
pair=a.merge(b,on=key+['method'],suffixes=('_D1','_D2'),validate='one_to_one')
check(len(pair)==1680,'Exact D1/D2 reuse pairing')
for column in ['eta','peak_db','J','runtime_s','max_coeff','iterations','fevals','selected']:
    check(pair[column+'_D1'].eq(pair[column+'_D2']).all(),'D1/D2 reused '+column)
fixed=load('D2_FIXED_DECISION.json')
base=tables['fixed'];base=base[base.method=='F02'][key+['eta']].rename(columns={'eta':'eta_base'})
all2=pd.read_csv(OUT/'D2_records.csv').merge(base,on=key,validate='many_to_one')
all2['raw_G']=all2.eta-all2.eta_base;all2['raw_H']=(all2.eta<all2.eta_base-.01).astype(float)
for r in fixed['A3_inputs']:
    q=all2[(all2.scene==r['scene'])&(all2.method==r['method'])]
    check(math.isclose(float(q.raw_G.mean()),r['gain_eta_vs_F02'],rel_tol=1e-12,abs_tol=1e-14),'A3 raw-record gain '+r['scene']+' '+r['method'])
    check(np.allclose(ci(q,'raw_G',r['scene']),[r['gain_eta_vs_F02_lo'],r['gain_eta_vs_F02_hi']],atol=1e-13,rtol=1e-12),'A3 reported gain interval '+r['scene']+' '+r['method'])
ref=max(float(all2[all2.method==m].raw_G.mean()) for m in ['F04','F08','UNB'])
check(math.isclose(ref,fixed['Gref'],rel_tol=1e-12,abs_tol=1e-14),'Gref from raw paired records')
best=min(['F04','F08'],key=lambda m:(-float(all2[all2.method==m].raw_G.mean()),m))
check(best==fixed['F_star'],'F_star pooled paired gain')
check(fixed['C0']==all(r['gain_eta_vs_F02']<.005 for r in fixed['A3_inputs']),'A3 six simultaneous strict conditions')
if fixed['C0']:
    check(f['branch']=='C0' and f['method']=='F02' and 'grid' not in tables,'C0 short circuit')
else:
    trig=load('D2_TRIGGER_DECISION.json'); rr=load('D2_RERUN_DECISION.json')
    check(trig['triggered_records']==int(tables['rerunA'].triggered.sum()),'A5 actual trigger count')
    check(trig['run_B']==(trig['triggered_records']>=30),'A5 comparison threshold')
    if trig['run_B']:
        p=tables['rerunA'].merge(tables['rerunB'],on=key,suffixes=('_A','_B'),validate='one_to_one');p=p[p.triggered_A.astype(bool)]
        vals=[float(abs(p.eta_B-p.eta_A).mean()),float(abs(p.peak_db_B-p.peak_db_A).mean()),float(np.median(p.runtime_s_B/p.runtime_s_A))]
        check(np.allclose(vals,[rr['mean_abs_eta_difference'],rr['mean_abs_peak_difference_db'],rr['median_runtime_B_over_A']],atol=1e-14,rtol=1e-13),'A/B decision inputs reproduced')
        check(rr['selected']==('B' if all(x<y for x,y in zip(vals,[.005,.1,.6])) else 'A'),'A/B strict three-condition rule')
    else:check(rr['selected']=='A' and 'rerunB' not in tables,'A5 sparse selects A without B')
    sel=f['decisions']['ADA_selection']; rows=sel['all_20_inputs'];qualified=[r for r in rows if r['gain_eta_vs_F02']>=.9*fixed['Gref']]
    for r in rows:
        q=all2[all2.method==r['method']]
        check(math.isclose(float(q.raw_G.mean()),r['gain_eta_vs_F02'],rel_tol=1e-12,abs_tol=1e-14),'ADA raw-record gain '+r['method'])
        check(math.isclose(float(q.raw_H.mean()),r['harm_vs_F02'],rel_tol=1e-12,abs_tol=1e-14),'ADA raw-record harm '+r['method'])
        check(np.allclose(ci(q,'raw_G','pooled'),[r['gain_eta_vs_F02_lo'],r['gain_eta_vs_F02_hi']],atol=1e-13,rtol=1e-12),'ADA paired gain interval '+r['method'])
        check(np.allclose(ci(q,'raw_H','pooled'),[r['harm_vs_F02_lo'],r['harm_vs_F02_hi']],atol=1e-13,rtol=1e-12),'ADA paired harm interval '+r['method'])
    check(all(r['qualifies']==(r['gain_eta_vs_F02']>=.9*fixed['Gref']) for r in rows),'ADA 90% gain qualification')
    if qualified:
        hmin=min(r['harm_vs_F02'] for r in qualified); options=[r['method'] for r in qualified if r['harm_vs_F02']<=hmin+.005]
    else:
        gm=max(r['gain_eta_vs_F02'] for r in rows);options=[r['method'] for r in rows if r['gain_eta_vs_F02']==gm]
    def priority(name):
        parts=name.split('_');return (parts[1]!='global',int(parts[2][1:]),-int(parts[3][1:]))
    check(min(options,key=priority)==sel['selected_ADA'],'ADA gain/harm/tie selection independently reproduced')
    tests=f['decisions']['fixed_radius_tests']; sufficient=[]
    for method in ['F04','F08']:
        q=[r for r in tests if r['method']==method]
        check(len(q)==2,'Fixed sufficiency both scenes '+method)
        for r in q:
            fix=all2[(all2.scene==r['scene'])&(all2.method==method)]
            ada=all2[(all2.scene==r['scene'])&(all2.method==sel['selected_ADA'])]
            check(np.allclose([fix.raw_G.mean(),ada.raw_G.mean(),fix.raw_H.mean(),ada.raw_H.mean()],[r['G_fixed'],r['G_ADA'],r['H_fixed'],r['H_ADA']],atol=1e-14,rtol=1e-12),'Fixed sufficiency raw inputs '+r['scene']+' '+method)
        check(all(r['passes']==(r['G_fixed']>=r['G_ADA']-.002 and r['H_fixed']<=r['H_ADA']+.01) for r in q),'Fixed gain/harm thresholds '+method)
        if all(r['passes'] for r in q):sufficient.append(method)
    check(f['method']==(sufficient[0] if sufficient else sel['selected_ADA']),'Final fixed/ADA choice independently reproduced')
    check(f['branch']==('C-F' if sufficient else 'C-A'),'Final branch reproduced')

result={'status':'PASS','check_count':len(checks),'checks':checks,'frozen_method_sha256':sha(OUT/'FROZEN_METHOD.json'),'scope':'Saved tables, original-file checksums, and independent rule arithmetic. No reruns or new budgets.'}
(OUT/'qa/development_audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'status':'PASS','checks':len(checks)}))
