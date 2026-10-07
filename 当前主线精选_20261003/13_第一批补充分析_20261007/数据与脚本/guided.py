from realtools import *
weak=[(52,600),(52,900),(52,2400),(61,2100),(100,600),(100,900),(100,1200),(100,1500),(100,1800),(103,900),(103,1200),(118,1500),(121,0),(133,1200),(136,900)]
strong=[49,64,79,94,112,130]
rows=[]
for fw,s in weak:
    y,fref=load_y(fw,s); tr=load_tracks(fw,s)
    r={'case':f'{fw} Hz, {s}-{s+300} s','f':fw,'s':s}
    for m in ['SMR','VS_FM','SUV','SUV_FM']:
        r[m],r[m+'_nu']=peak_rel_db(y,fref,tr[m].values)
    D=[]
    for fs_ in strong:
        ts=load_tracks(fs_,s)
        Dk=ts['VS_FM'].values/fs_
        D.append(Dk)
        if fs_==94:
            r['G94'],r['G94_nu']=peak_rel_db(y,fref,fw*Dk)
            r['G94_SMR'],_=peak_rel_db(y,fref,fw*ts['SMR'].values/fs_)
    D=np.array(D)
    Dm=np.median(D,axis=0)
    r['Gmed'],r['Gmed_nu']=peak_rel_db(y,fref,fw*Dm)
    # spread of strong-line Doppler factors, converted to Hz at fw (demeaned per line)
    dev=(D-D.mean(axis=1,keepdims=True)); 
    r['strong_spread_mHz']=1e3*fw*np.median(np.std(dev,axis=0))
    rows.append(r)
d=pd.DataFrame(rows)
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(d[['case','SMR','VS_FM','SUV','G94','G94_SMR','Gmed','G94_nu','Gmed_nu','VS_FM_nu','strong_spread_mHz']].round(3))
d.to_csv('guided_results.csv',index=False)
