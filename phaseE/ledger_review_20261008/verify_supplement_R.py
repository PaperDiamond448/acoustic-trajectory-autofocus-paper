"""Archive and reproduce supplied R1/R2/R4 calculations without changing inputs."""
from pathlib import Path
import sys, os, json, hashlib, shutil, runpy, contextlib
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'supplement_R'
ORIGINAL=OUT/'originals'
RERUN=OUT/'rerun'
for p in [ORIGINAL,RERUN]:p.mkdir(parents=True,exist_ok=True)
DOWNLOAD=Path('C:/Users/Lenovo/Downloads')
FILES=['ledger_supplement_R.py','realtools.py','R1_noise_positions.csv',
       'R1_strong94.csv','R1_cross_guidance_nu.csv','R2_100Hz.csv','R4_interline.csv',
       '两份复核意见处理_Claude_20261008.md']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=[]
for name in FILES:
 src=DOWNLOAD/name;dst=ORIGINAL/name
 if dst.exists() and sha(src)!=sha(dst):raise RuntimeError(f'Archive differs: {name}')
 shutil.copy2(src,dst)
 assert sha(src)==sha(dst)
 manifest.append(dict(source=str(src),archive=str(dst),sha256=sha(dst),bytes=dst.stat().st_size))
(OUT/'SOURCE_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
BASE=ROOT/'phaseD/X3_real'
inputs=list((BASE/'tracks').glob('*_T300.csv'))+list((BASE/'screen_inputs').glob('*.mat'))
cross=ROOT/'当前主线精选_20261003/13_第一批补充分析_20261007/数据与脚本/strong_cross.csv'
inputs.append(cross)
before={str(p):sha(p) for p in inputs}
sys.path.insert(0,str(ROOT/'phaseE/_local_pydeps'))
sys.path.insert(0,str(ORIGINAL))
previous=Path.cwd();oldargv=sys.argv[:]
try:
 os.chdir(RERUN);sys.argv=[str(ORIGINAL/'ledger_supplement_R.py'),str(ROOT)]
 with (OUT/'supplied_script_stdout.txt').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log):
  runpy.run_path(str(ORIGINAL/'ledger_supplement_R.py'),run_name='__main__')
finally:
 os.chdir(previous);sys.argv=oldargv
comparisons={}
for name in FILES:
 if not name.endswith('.csv'):continue
 a=pd.read_csv(ORIGINAL/name);b=pd.read_csv(RERUN/name)
 assert a.columns.tolist()==b.columns.tolist() and a.shape==b.shape
 assert a.isna().equals(b.isna())
 delta=(a-b).abs().max().fillna(0)
 assert delta.max()<1e-8,(name,delta.to_dict())
 comparisons[name]=dict(rows=len(a),columns=len(a.columns),max_abs_difference=float(delta.max()),by_column=delta.to_dict())

# Independent reconstruction: do not import the supplied realtools helper here.
import h5py
STRONG=[49,64,79,94,112,130]
tracks={};signals={}
def tr(f,s):
 key=(int(f),int(s))
 if key not in tracks:tracks[key]=pd.read_csv(BASE/'tracks'/f'f{key[0]}_s{key[1]}_T300.csv')
 return tracks[key]
def signal(f,s):
 key=(int(f),int(s))
 if key not in signals:
  with h5py.File(BASE/'screen_inputs'/f'f{key[0]}_s{key[1]}.mat','r') as h:
   a=h['y'][0];signals[key]=(a['real']+1j*a['imag'],float(h['extract/fref'][0,0]))
 return signals[key]
def own_spectrum(f,s,g):
 y,ref=signal(f,s);e=g-ref
 phase=np.r_[0,np.cumsum((e[1:]+e[:-1])/2/20)]*2*np.pi
 nfft=1 << int(np.ceil(np.log2(8*len(y))))
 freq=np.fft.fftfreq(nfft,d=1/20);use=abs(freq)<=1.5
 raw=np.abs(np.fft.fft(y,nfft)[use])**2/len(y)
 power=np.abs(np.fft.fft(y*np.exp(-1j*phase),nfft)[use])**2/len(y)
 db=10*np.log10(power/raw.max());nu=freq[use]
 bg=np.median(db[(abs(nu)>.05)&(abs(nu)<.5)])
 return nu,db,bg
def guide(f,s):return f*np.median([tr(k,s).VS_FM.to_numpy()/k for k in STRONG if k!=f],axis=0)
independent=[]
noise=pd.read_csv(RERUN/'R1_noise_positions.csv')
strong94=pd.read_csv(RERUN/'R1_strong94.csv')
weak=pd.read_csv(RERUN/'R2_100Hz.csv')
for s in [600,900,1200,1500,1800]:
 nu,db,bg=own_spectrum(100,s,guide(100,s))
 for row in noise[noise.start_s==s].itertuples():
  v=db[abs(nu-row.position_hz)<=row.window_hz].max()-bg
  independent.append(abs(v-row.excess_db))
 row=weak[(weak.tone_hz==100)&(weak.start_s==s)].iloc[0]
 independent.append(abs(db[abs(nu)<=.01].max()-bg-row.excess_at_predicted_db))
 independent.append(abs(db[abs(nu-row.ridge_offset_hz)<=.01].max()-bg-row.excess_at_ridge_db))
 nu,db,bg=own_spectrum(94,s,guide(94,s))
 expected=strong94.loc[strong94.start_s==s,'excess_at_predicted_db'].iloc[0]
 independent.append(abs(db[abs(nu)<=.01].max()-bg-expected))

# The supplied script copies cross-guidance peak locations from the old CSV.
# Recompute all 300 peaks from saved signals as an independent source check.
cross_rows=pd.read_csv(cross);peak_differences=[];nu_differences=[]
for row in cross_rows.itertuples():
 g=row.target*tr(row.guide,row.s).VS_FM.to_numpy()/row.guide
 nu,db,bg=own_spectrum(row.target,row.s,g);j=np.argmax(db)
 nu_differences.append(abs(nu[j]-row.nu))
 peak_differences.append(abs(db[j]-row.guided))

def stats(q):return dict(n=len(q),median=float(q.excess_db.median()),p90=float(q.excess_db.quantile(.9)),maximum=float(q.excess_db.max()))
summary=dict(all_positions=stats(noise),negative_positions=stats(noise[noise.position_hz<0]),
 positive_positions=stats(noise[noise.position_hz>0]))
threshold=summary['negative_positions']['p90']
summary['predicted_positions_above_negative_p90']=weak[(weak.tone_hz==100)&(weak.excess_at_predicted_db>threshold)][['start_s','excess_at_predicted_db']].to_dict('records')
summary['strong_cross_peak_abs_nu_quantiles_hz']={str(p):float(np.percentile(abs(cross_rows.nu),p)) for p in [50,90,99,100]}
summary['strong94_excess_db']=strong94.excess_at_predicted_db.tolist()
r4=pd.read_csv(RERUN/'R4_interline.csv')
summary['R4_per_tone_medians']=r4.groupby('tone_hz').median().drop(columns='start_s').reset_index().to_dict('records')
summary['positive_reference_nearest_distance_hz_range']=[float((.15-weak[weak.tone_hz==100].ridge_offset_hz).min()),float((.15-weak[weak.tone_hz==100].ridge_offset_hz).max())]
summary['positive_reference_farthest_distance_hz_range']=[float((.45-weak[weak.tone_hz==100].ridge_offset_hz).min()),float((.45-weak[weak.tone_hz==100].ridge_offset_hz).max())]
assert max(independent)<1e-8
assert max(nu_differences)<1e-10 and max(peak_differences)<1e-8
changed=[p for p,h in before.items() if sha(Path(p))!=h]
assert not changed,changed
result=dict(csv_comparisons=comparisons,independent_spectrum_checks=dict(n=len(independent),max_abs_db_difference=max(independent),
 cross_pairs=len(cross_rows),max_abs_cross_nu_difference=max(nu_differences),max_abs_cross_peak_db_difference=max(peak_differences)),
 summary=summary,protected_input_files_verified=len(before))
(OUT/'VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'INPUT_SHA256.json').write_text(json.dumps(before,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
