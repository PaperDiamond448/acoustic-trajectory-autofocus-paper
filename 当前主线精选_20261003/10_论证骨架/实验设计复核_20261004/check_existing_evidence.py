"""Post-review forensic calculations; reads frozen inputs, never fits a method."""
from pathlib import Path
import json,hashlib
import numpy as np
import pandas as pd
from scipy.integrate import cumulative_trapezoid
O=Path(__file__).resolve().parent;R=O.parents[1];P=R.parent/'phaseD'
FM='ADA_local_c04_t30_A';res={};inputs={}
def read(p,**kw):
 p=Path(p);inputs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest();return pd.read_csv(p,**kw)
c=read(P/'C_confirm/C_summary.csv')
def cm(m,metric,scope='ALL'):return float(c[(c.method==m)&(c.metric==metric)&(c.scope==scope)]['mean'].iloc[0])
res['C']={k:cm(m,met,scope) for k,m,met,scope in [('ADA_minus_SMR',FM,'gain_eta_vs_SMR','ALL'),('F02_minus_SMR','F02','gain_eta_vs_SMR','ALL'),('ADA_minus_F02',FM,'gain_eta_vs_F02','ALL'),('ADA_minus_UNB_S0',FM,'gain_eta_vs_UNB','S0')]}
assert abs(res['C']['ADA_minus_SMR']-res['C']['F02_minus_SMR']-res['C']['ADA_minus_F02'])<1e-12
d=read(P/'D_dev/D2_summary.csv');g=d.groupby('method').gain_eta_vs_F02.mean()
res['D2']={'reference_method':g[['F04','F08','UNB']].idxmax(),'retained_ratio':float(g[FM]/g[['F04','F08','UNB']].max())}
x=read(P/'X1_duration/X1_summary.csv')
res['X1_S2_SMR_eta']=x[(x.scope=='S2')&(x.method=='SMR')&(x.metric=='eta')].sort_values('duration_s')['mean'].tolist()
inc=read(P/'X3_real/X3_increments.csv');vis=read(P/'X3_real/X3_visibility.csv');cases=read(P/'X3_real/X3_cases.csv')
weak=inc[(inc.group=='weak')&(inc.pair=='VS_FM-SMR')].sort_values(['tone_hz','segment_start_s'])
rows=[];fftmax=[]
for r in weak.itertuples():
 tone=int(r.tone_hz);start=int(r.segment_start_s);tag=f'f{tone}_s{start}_T300'
 s=read(P/f'X3_real/spectra/{tag}.csv');tr=read(P/f'X3_real/tracks/{tag}.csv');raw=read(P/f'X3_real/audit_raw/{tag}.csv',header=None).to_numpy()
 t=raw[:,0];y=raw[:,1]+1j*raw[:,2];nfft=2**int(np.ceil(np.log2(8*len(t))));f=np.fft.fftshift(np.fft.fftfreq(nfft,.05));mask=abs(f)<=1.5
 assert np.max(abs((s.frequency_Hz-tone).to_numpy()-f[mask]))<1e-10
 er={}
 for m in ['SMR','F02','VS_FM']:
  z=y*np.exp(-2j*np.pi*cumulative_trapezoid(tr[m].to_numpy()-tone,t,initial=0))
  pp=abs(np.fft.fftshift(np.fft.fft(z,nfft)))**2/len(t)
  er[m]=float(np.max(abs(pp[mask]-s[m].to_numpy())))
 fftmax.append(max(er.values()));assert max(er.values())<1e-6
 band=s[abs(s.frequency_Hz-tone)<=.5];raw_peak=float(band.loc[band.Periodogram.idxmax(),'frequency_Hz'])
 adar=cases[(cases.tone_hz==tone)&(cases.segment_start_s==start)&(cases.method=='VS_FM')].iloc[0]
 pos={m:float(s.loc[s[m].idxmax(),'frequency_Hz']-tone) for m in ['SMR','F02','VS_FM']}
 gain=float(10*np.log10(s.VS_FM.max()/s.SMR.max()));assert abs(gain-r.gain_peak_db)<1e-9
 rows.append({'tone_hz':tone,'start_s':start,'source_set':int(r.set_number),'source_level_inferred':r.source_level_inferred,'gain_ADA_minus_SMR_db':gain,'gain_ADA_minus_F02_db':float(10*np.log10(s.VS_FM.max()/s.F02.max())),'triggered':int(adar.triggered),'uncompensated_peak_within_nominal_half_hz':raw_peak,'SMR_track_mean_hz':float(tr.SMR.mean()),'ADA_track_mean_hz':float(tr.VS_FM.mean()),'SMR_track_fraction_outside_nominal_half_hz':float((abs(tr.SMR-tone)>.5).mean()),'SMR_max_residual_hz':pos['SMR'],'ADA_max_residual_hz':pos['VS_FM'],'max_residual_shift_hz':pos['VS_FM']-pos['SMR'],'saved_FFT_max_abs_error':max(er.values())})
diag=pd.DataFrame(rows);diag.to_csv(O/'weak15_peak_correspondence.csv',index=False)
gain=diag.gain_ADA_minus_F02_db
res['X3']={'groups':inc[inc.pair=='VS_FM-SMR'].group.value_counts().to_dict(),'weak_median_gain_db':float(weak.gain_peak_db.median()),'weak_all_positive':bool((weak.gain_peak_db>0).all()),'weak_ADA_minus_F02':{'positive':int((gain>1e-9).sum()),'negative':int((gain< -1e-9).sum()),'unchanged':int((abs(gain)<=1e-9).sum())},'triggered':int(diag.triggered.sum()),'FFT_max_abs_error':max(fftmax),'SMR_mean_outside_nominal_half_hz':int((abs(diag.SMR_track_mean_hz-diag.tone_hz)>.5).sum()),'diagnostic_only_not_new_exclusion':True}
dur=read(P/'X3_real/X3_duration.csv');res['real_duration']={'tones':sorted(dur.tone_hz.unique().tolist()),'starts':dur[['tone_hz','segment_start_s']].drop_duplicates().to_dict('records')}
p60=read(R/'03_实验证据/C_原稿批次P60_表/T0_primary_endpoint.csv').iloc[0]
assert abs(p60.Pd_assoc_P60-p60.Pd_assoc_B2-p60.dPd_assoc_mean)<1e-12
res['P60']={k:float(p60[k]) for k in ['dPd_assoc_mean','ci_lo_with_calibration','ci_hi_with_calibration','threshold_P60','threshold_B2']}
expected={'PREREGISTRATION_PhaseD_20261003.md':'af3ab68bbdfd8ecefbd042e9faaac001a16c28a8f73a2fc071b3e315a6090df5','PREREGISTRATION_PhaseD_ADDENDUM_20261003.md':'fa6ccd779cb2ecfdff250778571963cdc77a170c187a95f85978a15638400344','D_dev/FROZEN_METHOD.json':'ff63f32c38fc17e99620faa074025c337df247bf823be4fa4b40e74860c0a89f'}
res['frozen_hashes']={k:hashlib.sha256((P/k).read_bytes()).hexdigest() for k in expected};assert res['frozen_hashes']==expected
(O/'FORENSIC_CALCULATIONS.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
(O/'AUDIT_INPUT_HASHES.json').write_text(json.dumps(inputs,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(res,ensure_ascii=False,indent=2))
