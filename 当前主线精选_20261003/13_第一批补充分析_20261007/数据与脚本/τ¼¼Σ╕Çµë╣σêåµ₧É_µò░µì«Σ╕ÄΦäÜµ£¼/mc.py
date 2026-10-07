import numpy as np, pandas as pd
from theory import *
rng=np.random.default_rng(1)
T=300; t,idx=eval_idx(T)
rows=[]
for spacing in [5,10,20,40,80,150]:
    nodes=np.arange(0,T+spacing,spacing)
    for amp in [1,2,4,8,16]:   # mHz rms of node values
        for k in range(40):
            v=rng.standard_normal(len(nodes))*amp*1e-3
            e=np.interp(t,nodes,v)
            s2=sigma2(e,t,idx); ea=eta_actual(e,t,idx)
            rows.append(dict(spacing=spacing,amp=amp,rms=np.sqrt(np.mean(e[idx]**2)),s2=s2,eta=ea,pred=np.exp(-s2)))
d=pd.DataFrame(rows)
d['err']=d.pred-d.eta
bins=pd.cut(d.s2,[0,0.1,0.3,0.5,1,2,100])
print(d.groupby(bins,observed=True).agg(n=('err','size'),mean_err=('err','mean'),mae=('err',lambda x: np.abs(x).mean())).round(3))
from scipy.stats import spearmanr
print('Spearman(eta, -sigma2)=%.3f   Spearman(eta,-rms)=%.3f'%(spearmanr(d.eta,-d.s2)[0],spearmanr(d.eta,-d.rms)[0]))
sub=d[d.s2<0.5]; print('sigma2<0.5: n=%d, MAE=%.3f'%(len(sub),np.abs(sub.err).mean()))
# same rms, different spacing -> eta
print(d[d.amp==4].groupby('spacing')[['rms','eta']].mean().round(3))
d.to_csv('mc_results.csv',index=False)
