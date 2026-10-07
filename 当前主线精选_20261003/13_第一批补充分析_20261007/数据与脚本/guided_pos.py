from realtools import *
d=pd.read_csv('guided_results.csv')
strong=[49,64,79,94,112,130]
rows=[]
for r in d.itertuples():
    y,fref=load_y(r.f,r.s)
    D=np.median([load_tracks(fk,r.s)['VS_FM'].values/fk for fk in strong],axis=0)
    g=r.f*D
    nu0,S0=spectrum(y); z=y*np.exp(-1j*comp_phase(g,fref)); nu,S=spectrum(z)
    Sdb=10*np.log10(S/S0.max())
    core=np.abs(nu)<=0.01; bg=(np.abs(nu)>0.05)&(np.abs(nu)<0.5)
    pk=Sdb[core].max(); excess=pk-np.median(Sdb[bg])
    # also: offset between VS_FM track (module) and guided track
    tr=load_tracks(r.f,r.s); off=np.median(tr.VS_FM.values-g)
    rows.append(dict(case=r.case,guided_zero_peak_db=pk,zero_excess_db=excess,guided_maxpeak_nu=r.Gmed_nu,module_track_minus_guided_hz=off))
o=pd.DataFrame(rows); print(o.round(3).to_string(index=False)); o.to_csv('guided_position_check.csv',index=False)
