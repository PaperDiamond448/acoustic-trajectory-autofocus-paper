from realtools import *
strong=[49,64,79,94,112,130]; segs=[0,300,600,900,1200,1500,1800,2100,2400,2700]
rows=[]
for s in segs:
    T={f:load_tracks(f,s) for f in strong}
    for ft in strong:
        y,fref=load_y(ft,s)
        own,_=peak_rel_db(y,fref,T[ft]['VS_FM'].values)
        lps,_=peak_rel_db(y,fref,T[ft]['SMR'].values)
        for fg in strong:
            if fg==ft: continue
            g,nu=peak_rel_db(y,fref,ft*T[fg]['VS_FM'].values/fg)
            rows.append(dict(s=s,target=ft,guide=fg,own=own,lps=lps,guided=g,nu=nu,loss_vs_own=own-g))
d=pd.DataFrame(rows)
d.to_csv('strong_cross.csv',index=False)
print('median loss of guided vs own module (dB), by target:'); print(d.groupby('target').loss_vs_own.median().round(2))
print('median guided-minus-LPS (dB):', (d.guided-d.lps).median().round(2), ' fraction guided>=LPS:', ((d.guided-d.lps)>=0).mean().round(2))
print('by |ft-fg| bins:'); d['df']=abs(d.target-d.guide); print(d.groupby(pd.cut(d.df,[0,20,40,60,90])).loss_vs_own.median().round(2))
print('median |nu| of guided peak (Hz):', d.nu.abs().median().round(3))
