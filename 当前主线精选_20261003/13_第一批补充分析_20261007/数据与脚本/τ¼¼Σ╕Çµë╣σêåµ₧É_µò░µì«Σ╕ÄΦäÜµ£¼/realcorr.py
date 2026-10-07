import numpy as np, pandas as pd
from theory import sigma2
from scipy.signal import welch
x=pd.read_csv('/home/claude/repo/phaseD/X3_real/X3_cases.csv')
cases=x[(x.method=='VS_FM')&(x.duration_s==300)][['tone_hz','segment_start_s','gain_peak_vs_SMR_db']]
grp=pd.read_csv('/home/claude/repo/phaseD/X3_real/X3_visibility.csv')[['tone_hz','segment_start_s','group']]
cases=cases.merge(grp,on=['tone_hz','segment_start_s'])
FS=20.0; t=np.arange(6000)/FS; idx=(t>=5)&(t<295)
rows=[]
for r in cases.itertuples():
    tr=pd.read_csv(f'/home/claude/repo/phaseD/X3_real/tracks/f{r.tone_hz}_s{r.segment_start_s}_T300.csv')
    dg=(tr.VS_FM-tr.SMR).values
    dgd=dg-dg[idx].mean()
    # spectral split: fraction of (demeaned) correction variance at periods > 60 s, and K-weighted (phase) fraction
    seg=dgd[idx]; F=np.fft.rfftfreq(len(seg),1/FS); P=np.abs(np.fft.rfft(seg))**2
    P[0]=0
    frac_slow=P[(F>0)&(F<1/60)].sum()/P.sum()
    K=np.where(F>0,1/np.maximum(F,1e-9)**2,0)  # high-f kernel ~1/f^2 (upper bound weighting for low f)
    s2=sigma2(dg,t,idx)
    rows.append(dict(tone=r.tone_hz,seg=r.segment_start_s,group=r.group,gain=r.gain_peak_vs_SMR_db,
                     rms_mHz=1e3*np.sqrt(np.mean(seg**2)),max_mHz=1e3*np.abs(dg[idx]).max(),frac_var_period_gt60=frac_slow,phase_change_s2=s2))
d=pd.DataFrame(rows)
print(d.groupby('group')[['rms_mHz','max_mHz','frac_var_period_gt60','phase_change_s2','gain']].median().round(3))
from scipy.stats import spearmanr
for g in ['weak','strong','shallow']:
    s=d[d.group==g]; print(g,'n',len(s),' spearman(phase_change, gain)=%.2f'%spearmanr(s.phase_change_s2,s.gain)[0])
print('all: spearman(phase_change, gain)=%.2f'%spearmanr(d.phase_change_s2,d.gain)[0])
w=d[(d.group=='weak')]
print(w.sort_values('gain')[['tone','seg','gain','rms_mHz','frac_var_period_gt60','phase_change_s2']].round(3).to_string(index=False))
d.to_csv('real_correction_spectra.csv',index=False)
