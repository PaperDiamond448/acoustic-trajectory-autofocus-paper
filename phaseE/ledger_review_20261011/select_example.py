from pathlib import Path
import hashlib, json
import numpy as np, pandas as pd
from scipy.io import loadmat
from scipy.integrate import cumulative_trapezoid
O=Path(__file__).parent;records=loadmat(O/'confirm_candidates.mat',simplify_cells=True)['samples']
rows=[];cache={}
def sigma(e,t):
 phase=2*np.pi*cumulative_trapezoid(e,t,initial=0);A=np.c_[np.ones(len(t)),t-t.mean()];r=phase-A@np.linalg.lstsq(A,phase,rcond=None)[0];return np.mean(r*r)
def dwell(e):
 signs=np.sign(e);edges=np.r_[0,np.where(np.diff(signs)!=0)[0]+1,len(e)];return np.diff(edges).max()/20
for r in records:
 t=r['t'];idx=(t>=5)&(t<295);ei=r['truth']-r['input_g'];eo=r['truth']-r['output_g'];si=sigma(ei[idx],t[idx]);so=sigma(eo[idx],t[idx])
 nfft=65536;f=np.fft.fftfreq(nfft,1/20);spec={}
 for label,g in [('LPS',r['input_g']),('CDTR',r['output_g']),('ideal',r['truth'])]:
  phi=2*np.pi*cumulative_trapezoid(g,t,initial=0);spec[label]=np.abs(np.fft.fft(r['target'][idx]*np.exp(-1j*phi[idx]),nfft))**2
 den=np.abs(r['target'][idx]).sum()**2;eta={k:s[np.abs(f)<=2].max()/den for k,s in spec.items()}
 assert abs(eta['LPS']-r['eta_in_saved'])<1e-12 and abs(eta['CDTR']-r['eta_out_saved'])<1e-12
 row=dict(record_id=int(r['record_id']),seed=int(r['seed']),sigma2_in=float(si),sigma2_out=float(so),eta_in=eta['LPS'],eta_out=eta['CDTR'],gain=eta['CDTR']-eta['LPS'],max_error_full_mHz=np.abs(ei).max()*1000,max_error_eval_mHz=np.abs(ei[idx]).max()*1000,longest_same_sign_s=dwell(ei[idx]),qualifies=bool(.5<=si<5 and np.abs(ei).max()<.02 and eta['CDTR']>.85))
 rows.append(row);cache[row['record_id']]=(r,idx,f,spec)
df=pd.DataFrame(rows);q=df[df.qualifies].copy();assert len(q)>0
median=float(q.gain.median());q['distance_to_median']=np.abs(q.gain-median);best=q.sort_values(['distance_to_median','record_id']).iloc[0];rid=int(best.record_id);r,idx,f,spec=cache[rid]
df['selected']=df.record_id==rid;df.to_csv(O/'FIG3_example_candidates.csv',index=False)
result=best.to_dict();result.update({'median_candidate_gain':median,'candidate_count':len(q),'exported_count':len(df),'criterion':'all stated conditions, full-trajectory max error below .02 Hz; closest to median gain, record_id tie break','evaluation_interval_s':[5,295],'source_file':r['source_file'],'source_sha256':hashlib.sha256(Path(r['source_file']).read_bytes()).hexdigest(),'input_hash':r['input_hash'],'no_new_optimization':True,'spectral_reference':'maximum ideal-compensation target-only power over ±2 Hz on the same 290 s support'})
(O/'FIG3_example_selected.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
pd.DataFrame({'time_s':r['t'],'true_g_Hz':r['truth'],'LPS_g_Hz':r['input_g'],'CDTR_g_Hz':r['output_g'],'LPS_error_mHz':1000*(r['input_g']-r['truth']),'CDTR_error_mHz':1000*(r['output_g']-r['truth'])}).to_csv(O/'FIG3_example_trajectories.csv',index=False)
sel=np.abs(f)<=.15;order=np.argsort(f[sel]);ref=spec['ideal'][np.abs(f)<=2].max()
pd.DataFrame({'residual_frequency_Hz':f[sel][order],**{k+'_power_dB':10*np.log10(np.maximum(s[sel][order]/ref,1e-15)) for k,s in spec.items()}}).to_csv(O/'FIG3_example_spectra.csv',index=False)
print(json.dumps(result,ensure_ascii=False,indent=2))
