# Independent re-derivation of Phase D development decisions (Claude, 2026-10-04).
import pandas as pd, numpy as np
D='D:/论文集/phaseD/D_dev/'
def cellmean(t,col):
    # equal-weight mean of per-cell means within scene
    return t.groupby(['scene','snr_db'])[col].mean().groupby('scene').mean()
# ---------------- D1 ----------------
d1=pd.read_csv(D+'D1_records.csv')
assert d1.groupby(['Delta_s','arm','method']).size().eq(840).all()
assert (d1.seed==20260915+51_000_000+d1.scene.map({'S0':10000,'S2':30000})+d1.record_id).all()
# VIT eta identical across rows of same record?
v=d1.groupby(['scene','snr_db','record_id']).eta_VIT.nunique(); print('VIT eta unique per record:',v.max())
s=d1[d1.arm=='scaled'].copy(); s['g']=s.eta-s.eta_VIT
G=s.groupby(['scene','method','Delta_s']).apply(lambda q: q.groupby('snr_db').g.mean().mean()).rename('G').reset_index()
rows=[]
for (sc,m),q in G.groupby(['scene','method']):
    gmax=q.G.max(); thr=0.95*gmax if gmax>0 else gmax-0.005
    for r in q.itertuples(): rows.append((sc,m,r.Delta_s,r.G,gmax,thr,r.G>=thr))
R=pd.DataFrame(rows,columns=['scene','method','Delta','G','Gmax','thr','ok'])
F=[30,15,10,7.5,6]
ok=[d for d in F if R[R.Delta==d].ok.all()]
print('D1 eligible (freezable):',ok,'-> Delta* =',max(ok) if ok else None)
print(R.pivot_table(index='Delta',columns=['scene','method'],values='G').round(4))
# budget cap / hard fail in D1
print('D1 hard_fail:',int(d1.hard_fail.sum()),' budget_cap rate by Delta:'); print(d1.groupby('Delta_s').budget_cap.mean().round(4))
# unscaled control
c=d1[(d1.method=='F02')].copy(); c['g']=c.eta-c.eta_VIT
print('F02 scaled vs unscaled G by Delta (pooled):')
print(c.groupby(['arm','Delta_s']).apply(lambda q: q.groupby(['scene','snr_db']).g.mean().groupby('scene').mean().mean()).unstack(0).round(4))
# ---------------- D2 ----------------
d2=pd.read_csv(D+'D2_records.csv'); assert (d2.Delta_s==10).all()
assert d2.groupby('method').size().eq(840).all()
base=d2[d2.method=='F02'][['scene','snr_db','record_id','eta','peak_db']].rename(columns={'eta':'xF02','peak_db':'pF02'})
d2=d2.drop(columns=[c for c in d2.columns if c.endswith('_F02')]).merge(base,on=['scene','snr_db','record_id'],validate='many_to_one')
d2['eta_F02']=d2.xF02
d2['gF']=d2.eta-d2.eta_F02; d2['harm']=(d2.eta<d2.eta_F02-0.01).astype(float)
def GH(q):
    g=cellmean(q,'gF'); h=cellmean(q,'harm'); return g['S0'],g['S2'],(g['S0']+g['S2'])/2,h['S0'],h['S2'],(h['S0']+h['S2'])/2
tab=pd.DataFrame({m:GH(q) for m,q in d2.groupby('method')},index=['G_S0','G_S2','G','H_S0','H_S2','H']).T
print(tab.round(5))
A3=all(tab.loc[m,f'G_{s}']<0.005 for m in ['F04','F08','UNB'] for s in ['S0','S2']); print('A3 (no gain) all <0.005:',A3)
Gref=tab.loc[['F04','F08','UNB'],'G'].max(); print('Gref',Gref,'thr',0.9*Gref)
ada=tab[tab.index.str.startswith('ADA')].copy(); ada['ok']=ada.G>=0.9*Gref
adm=ada[ada.ok]; Hmin=adm.H.min(); near=adm[adm.H<=Hmin+0.005]
print('admissible',len(adm),'Hmin',Hmin); print('near-tie set:'); print(near[['G','H']])
def key(n):
    p=n.split('_'); return (0 if p[1]=='global' else 1, int(p[2][1:]), -int(p[3][1:]))
pick=sorted(near.index,key=key)[0]; print('selected ADA:',pick)
for rho in ['F04','F08']:
    okS=[tab.loc[rho,f'G_{s}']>=tab.loc[pick,f'G_{s}']-0.002 and tab.loc[rho,f'H_{s}']<=tab.loc[pick,f'H_{s}']+0.01 for s in ['S0','S2']]
    print(rho,'fixed-sufficient per scene',okS)
print('F* =', tab.loc[['F04','F08'],'G'].idxmax())
# ---------------- D2a A/B ----------------
A=pd.read_csv(D+'rerunA_records.csv'); B=pd.read_csv(D+'rerunB_records.csv')
k=['scene','snr_db','record_id']; M=A.merge(B,on=k,suffixes=('_A','_B'))
trA=M.triggered_A.astype(bool); trB=M.triggered_B.astype(bool); assert (trA==trB).all()
T=M[trA]; print('triggered',len(T))
print('mean|deta|',(T.eta_A-T.eta_B).abs().mean(),'mean|dpeak|',(T.peak_db_A-T.peak_db_B).abs().mean(),'median rt B/A',(T.runtime_s_B/T.runtime_s_A).median())
print('mean eta A-B on triggered',(T.eta_A-T.eta_B).mean(),' frac A>B',((T.eta_A-T.eta_B)>0).mean())
