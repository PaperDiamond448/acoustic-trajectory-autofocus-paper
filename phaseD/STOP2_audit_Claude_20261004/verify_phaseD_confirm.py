# Independent recomputation of confirmation endpoints (Claude, 2026-10-04); own RNG.
import pandas as pd, numpy as np
t=pd.read_csv('D:/论文集/phaseD/C_confirm/C_records.csv')
FM='ADA_local_c04_t30_A'
assert t.groupby('method').size().eq(2800).all() and set(t.method)=={'SMR','F02','F04','UNB',FM}
assert (t.seed==20260915+52_000_000+t.scene.map({'S0':10000,'S2':30000})+t.record_id).all()
dev=set(pd.read_csv('D:/论文集/phaseD/D_dev/D2_records.csv',usecols=['seed']).seed); e4a=set(pd.read_csv('D:/论文集/phaseC/E4a_formal_paired_20260925/E4a_all_records.csv',usecols=['seed']).seed)
print('seed overlap dev/E4a:',len(set(t.seed)&dev),len(set(t.seed)&e4a))
k=['scene','snr_db','record_id']
W=t.pivot_table(index=k,columns='method',values='eta').reset_index()
J=t.pivot_table(index=k,columns='method',values='J').reset_index()
trig=t[t.method==FM].set_index(k).triggered.astype(bool)
Wi=W.set_index(k)
print('triggered',trig.sum(),'; untriggered max|FM-F02|',(Wi.loc[~trig,FM]-Wi.loc[~trig,'F02']).abs().max(),'; J_FM>=J_F02 all',(J.set_index(k)[FM]>=J.set_index(k)['F02']-1e-12).all())
W['d1']=W[FM]-W['F02']; W['d2']=W[FM]-W['UNB']
W['h']=(W[FM]<W['F02']-0.01).astype(float)-(W['UNB']<W['F02']-0.01).astype(float)
rng=np.random.default_rng(777)
def pooled(col,B=4000):
    est=[];boots=[]
    for sc in ['S0','S2']:
        M=W[W.scene==sc].pivot(index='record_id',columns='snr_db',values=col).to_numpy()  # 200 x 7
        est.append(M.mean(0).mean())
        idx=rng.integers(0,M.shape[0],(B,M.shape[0]))
        boots.append(M[idx].mean(1).mean(1))
    e=np.mean(est); b=np.mean(boots,0); return e,np.percentile(b,[2.5,97.5]),est
for col,name in [('d1','P1 FM-F02'),('d2','P2 FM-UNB'),('h','P3 H_FM-H_UNB')]:
    e,ci,per=pooled(col); print(f'{name}: {e:.6f} CI [{ci[0]:.6f},{ci[1]:.6f}]  per-scene S0 {per[0]:.6f} S2 {per[1]:.6f}')
bad=0
for (sc,snr),q in W.groupby(['scene','snr_db']):
    a=q.d1.to_numpy(); b=a[rng.integers(0,len(a),(4000,len(a)))].mean(1); hi=np.percentile(b,97.5)
    if hi<-0.005: bad+=1
print('S1 degraded cells:',bad,'/14')
# FM vs SMR per cell, CI positive count
pos=0
for (sc,snr),q in W.groupby(['scene','snr_db']):
    a=(q[FM]-q['SMR']).to_numpy(); b=a[rng.integers(0,len(a),(4000,len(a)))].mean(1); pos+=np.percentile(b,2.5)>0
print('FM-SMR cells with CI>0:',pos,'/14; pooled mean FM-SMR', W.groupby(['scene','snr_db']).apply(lambda q:(q[FM]-q.SMR).mean(),include_groups=False).mean().round(4))
P=t.pivot_table(index=k,columns='method',values='peak_db')
print('peak gain FM-SMR pooled dB',(P[FM]-P['SMR']).groupby(level=[0,1]).mean().mean().round(3),' FM-F02 dB',(P[FM]-P['F02']).groupby(level=[0,1]).mean().mean().round(3))
print('harm rates (vs F02) by scene:'); 
for m in ['F04','UNB',FM]:
    h=(W[m]<W['F02']-0.01).groupby(W.scene).mean(); print(' ',m,h.round(4).to_dict())
