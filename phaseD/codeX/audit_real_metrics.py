from pathlib import Path
import numpy as np,pandas as pd,json
R=Path('D:/论文集/phaseD');O=R/'X3_real';refs=pd.read_csv(R.parent/'phaseA/tables/A4_groundtruth.csv')
maxima={k:0. for k in ['peak_relative_periodogram_db','peak_frequency_hz','prominence_db','width_3db_hz','gps_mean_offset_hz','gps_demeaned_rms_hz']};checked=0
for suffix,table in [('',pd.read_csv(O/'X3_cases.csv')),('_duration',pd.read_csv(O/'X3_duration.csv'))]:
 for (tone,start,T),group in table.groupby(['tone_hz','segment_start_s','duration_s']):
  tag=f'f{tone}_s{start}_T{T}{suffix}';raw=np.loadtxt(O/'audit_raw'/f'{tag}.csv',delimiter=',');t=raw[:,0];y=raw[:,1]+1j*raw[:,2];tracks=pd.read_csv(O/'tracks'/f'{tag}.csv');N=len(y);nfft=2**int(np.ceil(np.log2(8*N)));f=tone+np.fft.fftshift(np.fft.fftfreq(nfft,.05));mask=np.abs(f-tone)<=1.5;fu=f[mask]
  p0=abs(np.fft.fftshift(np.fft.fft(y,nfft)))**2/N;pk0=p0[mask].max();gps=tone*np.interp(start+t,refs.t_s,refs.f_gps_100)/100;idx=(t>=5)&(t<T-5)
  for _,r in group.iterrows():
   g=tracks[r.method].to_numpy()-tone;phi=np.concatenate(([0],np.cumsum((g[:-1]+g[1:])/2*np.diff(t))))*2*np.pi;p=abs(np.fft.fftshift(np.fft.fft(y*np.exp(-1j*phi),nfft)))**2/N;pu=p[mask];im=np.argmax(pu);pk=pu[im];db=10*np.log10(np.maximum(pu,np.finfo(float).tiny));noise=pu[(abs(fu-fu[im])>=.5)&(abs(fu-fu[im])<=1.5)]
   left=np.where(db[:im+1]<=db[im]-3)[0];right=np.where(db[im:]<=db[im]-3)[0]
   if len(left) and len(right):
    il=left[-1];ir=im+right[0];fl=np.interp(db[im]-3,db[[il,il+1]],fu[[il,il+1]]);fr=np.interp(db[im]-3,db[[ir,ir-1]],fu[[ir,ir-1]]);width=fr-fl
   else:width=np.nan
   e=(tone+g-gps)[idx];v=dict(peak_relative_periodogram_db=10*np.log10(pk/pk0),peak_frequency_hz=fu[im],prominence_db=10*np.log10(pk/max(np.median(noise),np.finfo(float).tiny)),width_3db_hz=width,gps_mean_offset_hz=e.mean(),gps_demeaned_rms_hz=np.sqrt(np.mean((e-e.mean())**2)))
   for k,a in v.items():
    b=r[k];assert np.isnan(a)==np.isnan(b),(tag,r.method,k,a,b)
    if np.isfinite(a):delta=abs(a-b);assert delta<=1e-7,(tag,r.method,k,delta);maxima[k]=max(maxima[k],delta)
   checked+=1
 # Independently compare shared 300-s duration reruns to the complete real cases.
d=pd.read_csv(O/'X3_duration.csv');c=pd.read_csv(O/'X3_cases.csv');q=d[d.duration_s==300].merge(c,on=['tone_hz','segment_start_s','duration_s','method'],suffixes=('_duration','_case'),validate='one_to_one')
assert len(q)==12
for k in ['input_hash','peak_relative_periodogram_db','prominence_db','width_3db_hz','J','J_start','J_round0']:
 a=q[k+'_duration'];b=q[k+'_case']
 if k=='input_hash':assert (a==b).all()
 else:assert np.allclose(a,b,atol=1e-12,rtol=0,equal_nan=True),k
result={'status':'PASS','rows':checked,'independent_implementation':'NumPy FFT, trapezoidal phase integration, spectrum/GPS formulas written separately from MATLAB','tolerance':1e-7,'metric_max_absolute_differences':maxima,'shared_300_s_rerun_rows':len(q),'raw_export_note':'CSV decimal precision; original MATLAB inputs and frozen numerical results unchanged'}
(O/'INDEPENDENT_REAL_METRICS_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result))
