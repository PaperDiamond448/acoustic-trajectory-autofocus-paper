"""Read-only independent checks of Claude's 2026-10-08 claims ledger.

Writes only this review directory. Does not launch any experimental solver.
"""
from pathlib import Path
import hashlib, json, importlib.util
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CUR = ROOT / '当前主线精选_20261003'
FIRST = CUR / '13_第一批补充分析_20261007/数据与脚本'
sources = {}
checks = {}

def register(p):
    p = Path(p)
    sources[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    return p

def read(p):
    p = Path(p)
    if not p.is_absolute(): p = ROOT / p
    return pd.read_csv(register(p))

def rho(x,y):
    return float(spearmanr(x,y).statistic)

def means(g):
    return dict(n=len(g), eta_in=g.eta_in.mean(), eta_out=g.eta_out.mean(),
                gain=(g.eta_out-g.eta_in).mean())

spec=importlib.util.spec_from_file_location('supplied_theory', register(FIRST/'theory.py'))
th=importlib.util.module_from_spec(spec);spec.loader.exec_module(th)
t,idx=th.eval_idx(300)
k=th.kernel([1/290,1/14.5])
phase_checks=[]
for phase in [0,np.pi/2]:
    e=np.sqrt(2)*.003*np.cos(2*np.pi*(t-5)/290+phase)
    phase_checks.append(dict(phase=phase, rms=np.sqrt(np.mean(e[idx]**2)),
                             sigma2=th.sigma2(e,t,idx), eta=th.eta_actual(e,t,idx)))
checks['T1']=dict(kernel=k.tolist(), ratio=k[0]/k[1],
                  phase_average_eta_approx=np.exp(-k*.003**2).tolist(),
                  same_frequency_same_rms_different_phase=phase_checks)
mc=read(FIRST/'mc_results.csv')
checks['T2_MC']={name:dict(n=len(g),mae=np.mean(np.abs(g.pred-g.eta)),bias=np.mean(g.pred-g.eta))
 for name,g in [('small',mc[mc.s2<.5]),('medium',mc[(mc.s2>=.5)&(mc.s2<1)]),('large',mc[mc.s2>=1])]}
checks['T4_MC']=dict(rho_eta_sigma2=rho(mc.eta,mc.s2),rho_eta_rmse=rho(mc.eta,mc.rms),
 spacing_at_amp4={str(s):dict(n=len(g),rms_mean=g.rms.mean(),rms_min=g.rms.min(),rms_max=g.rms.max(),eta_mean=g.eta.mean())
 for s,g in mc[mc.amp==4].groupby('spacing')})
ex=read(CUR/'05_图表素材/正文图_20261004/source_data/expA_curves.csv')
checks['T3']={}
for label in ['A','B']:
 e=np.interp(t,ex.t_s,ex['e_'+label+'_hz']);s=th.sigma2(e,t,idx)
 checks['T3'][label]=dict(sigma2=s,pred=np.exp(-s),eta=th.eta_actual(e,t,idx))
e0=read('phaseA/tables/E0_phase_corrected_perrecord.csv')
checks['T5']=e0.groupby(['scene','estimator'])[['eta_full','eta_after_slow_correction','eta_after_fast_correction']].mean().reset_index().to_dict('records')
x2=read('phaseE/E1_trajexport/traj_export_X2_theory_metrics.csv')
b=read('phaseE/E2_frontend_ext/traj_export_E2_theory_metrics.csv')
d=read('phaseE/E5_inject/traj_export_E5_theory_metrics.csv')
assert set(d.target_kind)=={1,2}
d['target_kind']=d.target_kind.map({1:'GEO',2:'GPS'})
checks['T2_empirical']={};checks['P2_P3']={}
for name,frame in [('X2',x2),('D',d)]:
 checks['T2_empirical'][name]={};checks['P2_P3'][name]={}
 for front,g in frame.groupby('frontend'):
  small=g[g.in_sigma2<.5]
  checks['T2_empirical'][name][front]=dict(n=len(small),mae=np.mean(abs(small.in_eta_pred-small.eta_in)))
  checks['P2_P3'][name][front]=dict(all=rho(g.pred_recoverable,g.eta_out-g.eta_in),
   below5=rho(g.loc[g.in_sigma2<5,'pred_recoverable'],(g.eta_out-g.eta_in)[g.in_sigma2<5]))
  if name=='D':
   checks['P2_P3'][name][front]['by_target_below5']={str(k):dict(n=len(q),rho=rho(q.pred_recoverable,q.eta_out-q.eta_in)) for k,q in g[g.in_sigma2<5].groupby('target_kind')}
checks['T6']={}
for f in ['VS','SUV']:
 g=x2[(x2.frontend==f)&(x2.scene=='S0')&(x2.in_sigma2<.5)]
 checks['T6'][f]=dict(n=len(g),rms_demeaned_median_mHz=g.in_rmse_demeaned_hz.median()*1000,
  eta_mean=g.eta_in.mean(),slow_phase_median=g.in_p_gt60s.median())
checks['M3']={name:dict(**means(g),scenes=g.scene.value_counts().to_dict()) for name,g in [
 ('small',x2[(x2.frontend=='VS')&(x2.in_sigma2<.5)]),
 ('medium',x2[(x2.frontend=='VS')&(x2.in_sigma2>=.5)&(x2.in_sigma2<5)]),
 ('large',x2[(x2.frontend=='VS')&(x2.in_sigma2>=5)])]}
checks['P1']={}
for tag in ['X2','X1_T150','X1_T300','X1_T450','X1_T600']:
 a=read(f'phaseE/E1_trajexport/traj_export_{tag}_diagA2.csv')
 checks['P1'][tag]={str(f):dict(n=len(g),rho=rho(g.ceiling_gain_m1,g.gain)) for f,g in a.groupby('frontend')}
 if tag=='X2':
  q=a[(a.frontend=='SUV')&(a.scene=='S0')].merge(x2[['row','in_sigma2']],on='row',validate='one_to_one')
  checks['cycle_diagnostic']={str(k):dict(n=len(g),eta_in=g.eta_in.mean()) for k,g in q.groupby(q.n_slip_runs>0)}

c=read('phaseD/C_confirm/C_records.csv')
keys=['scene','snr_db','record_id']
base=c[c.method=='SMR'].set_index(keys)
ada=c[c.method=='ADA_local_c04_t30_A'].set_index(keys).loc[base.index]
g=ada.eta-base.eta
sel=g>.01;usable=base.track_rmse_hz<.05
checks['M1_T4_confirmation']=dict(n=len(ada),eta_in=base.eta.mean(),eta_out=ada.eta.mean(),
 eta_VIT=ada.eta_VIT.mean(),gain=g.mean(),peak_gain=(ada.peak_db-base.peak_db).mean(),runtime_median=ada.runtime_s.median(),
 improved_n=int(sel.sum()),rmse_increase_fraction=((ada.track_rmse_hz>base.track_rmse_hz)[sel]).mean(),
 rmse_below05=dict(n=int(usable.sum()),eta_in=base.eta[usable].mean(),eta_out=ada.eta[usable].mean(),
  rmse_in_median_mHz=base.track_rmse_hz[usable].median()*1000,rmse_out_median_mHz=ada.track_rmse_hz[usable].median()*1000))
f02=c[c.method=='F02'].set_index(keys).loc[base.index]
checks['M5']=dict(f02_gain=(f02.eta-base.eta).mean(),ada_addition=(ada.eta-f02.eta).mean(),
 addition_by_scene=(ada.eta-f02.eta).groupby(level='scene').mean().to_dict(),harms_vs_f02={})
for m in ['F04','UNB','ADA_local_c04_t30_A']:
 q=c[c.method==m].set_index(keys).loc[base.index]
 delta=q.eta-f02.eta
 checks['M5']['harms_vs_f02'][m]=(delta<-.01).groupby(level='scene').mean().to_dict()
xx=read('phaseD/X1_duration/X1_records.csv')
checks['M4']=xx[xx.method=='ADA_local_c04_t30_A'].groupby(['duration_s','scene']).gain_eta_vs_SMR.mean().reset_index().to_dict('records')
bb=read('phaseE/E2_frontend_ext/E2_records.csv')
cc=read('phaseE/E3_duration_ext/E3_records.csv')
checks['M2_M6_M7']={str(f):dict(**means(q),harm_fraction=((q.eta_out-q.eta_in)<-.01).mean()) for f,q in pd.concat([x2,bb]).groupby('frontend')}
checks['M7_duration']=cc[cc.frontend=='ORACLE'].groupby('duration_s').eta_out.mean().to_dict()

def compare(frame,front,scene=None):
 q=frame if scene is None else frame[frame.scene==scene]
 keys=['scene','snr_db','record_id','duration_s']
 for key in ['band_id','window_id','target_kind']:
  if key in q:keys.append(key)
 left=q[q.frontend==front];right=q[q.frontend=='SUV']
 pair=left.merge(right,on=keys,suffixes=('_front','_pc'),validate='one_to_one')
 assert (pair.input_hash_front==pair.input_hash_pc).all()
 pair['delta']=pair.eta_out_front-pair.eta_in_pc
 return pair

def cluster_ci(q):
 # Scene-specific bootstrap, all SNRs of each selected record_id kept together.
 u=q.groupby('record_id').delta.agg(['sum','count'])
 rng=np.random.default_rng(20261008)
 indices=rng.integers(0,len(u),size=(2000,len(u)))
 v=u['sum'].to_numpy()[indices].sum(1)/u['count'].to_numpy()[indices].sum(1)
 return dict(n=len(q),mean=q.delta.mean(),ci=np.quantile(v,[.025,.975]).tolist(),clusters=len(u))

checks['comparisons_simulation']={}
ab=pd.concat([x2,b],ignore_index=True)
for front in ['VS','DHMM']:
 checks['comparisons_simulation'][front]={}
 for scene in ['S0','S2']:
  q=compare(ab,front,scene)
  small=q[(q.in_sigma2_front<5)&(q.in_sigma2_pc<5)]
  bothusable=q[q.input_usable_front.astype(bool)&q.input_usable_pc.astype(bool)]
  checks['comparisons_simulation'][front][scene]=dict(
   both_small=cluster_ci(small) if len(small) else dict(n=0),both_usable=cluster_ci(bothusable),
   front_ge5=int((q.in_sigma2_front>=5).sum()))
checks['comparisons_duration']={}
for T in [150,300,450,600]:
 xf=read(f'phaseE/E1_trajexport/traj_export_X1_T{T}_theory_metrics.csv')
 cf=read(f'phaseE/E3_duration_ext/traj_export_E3_T{T}_theory_metrics.csv')
 q=compare(pd.concat([xf,cf]),'VS','S0')
 checks['comparisons_duration'][str(T)]=dict(
  both_small=cluster_ci(q[(q.in_sigma2_front<5)&(q.in_sigma2_pc<5)]),
  both_usable=cluster_ci(q[q.input_usable_front.astype(bool)&q.input_usable_pc.astype(bool)]))
checks['comparison_partitions']={}
for tag,frame,front in [('X2_S0',ab[ab.scene=='S0'],'VS'),('D_GEO',d[d.target_kind=='GEO'],'VS'),
 ('D_GPS',d[d.target_kind=='GPS'],'VS'),('D_GPS_DHMM',d[d.target_kind=='GPS'],'DHMM')]:
 q=compare(frame,front);a=q.in_sigma2_front<5;bsmall=q.in_sigma2_pc<5
 checks['comparison_partitions'][tag]=dict(total=q.delta.mean(),groups={
  label:dict(n=int(mask.sum()),mean=q.delta[mask].mean()) for label,mask in [
  ('both_small',a&bsmall),('only_pc_small',~a&bsmall),('only_front_small',a&~bsmall),('both_large',~a&~bsmall)]})
dr=read('phaseE/E5_inject/E5_records.csv')
assert set(dr.target_kind)=={1,2}
dr['target_kind']=dr.target_kind.map({1:'GEO',2:'GPS'})
checks['D1_D2']={str(f):dict(**means(q),by_target={str(k):means(v) for k,v in q.groupby('target_kind')}) for f,q in dr.groupby('frontend')}
checks['D3']={str(k):means(q) for k,q in d[(d.frontend=='VS')&(d.in_sigma2>=.5)&(d.in_sigma2<5)].groupby('target_kind')}
checks['D4_D5']={}
for target,q in dr[dr.frontend=='VS'].groupby('target_kind'):
 harm=q.gain_eta<-.01
 checks['D4_D5'][target]=dict(trigger_all=q.triggered.mean(),trigger_harmed=q.loc[harm,'triggered'].mean(),harm_n=int(harm.sum()),
  by_snr={str(s):dict(n=len(g),harm=(g.gain_eta<-.01).mean(),eta_in=g.eta_in.mean(),gain=g.gain_eta.mean(),
  harm_gain=g.loc[g.gain_eta<-.01,'gain_eta'].mean(),usable=g.input_usable.mean()) for s,g in q.groupby('snr_db')})

rc=read(FIRST/'real_correction_spectra.csv')
checks['R3']={str(k):dict(n=len(q),medians=q.select_dtypes(include='number').median().to_dict(),
 max_mHz=q.max_mHz.max(),rho_phase_gain=rho(q.phase_change_s2,q.gain)) for k,q in rc.groupby('group')}
checks['R3']['all_rho']=rho(rc.phase_change_s2,rc.gain)
sc=read(FIRST/'strong_cross.csv')
checks['R4']=dict(n=len(sc),guided_below_lps=(sc.guided<sc.lps).mean(),nu_abs_median=sc.nu.abs().median(),
 loss_by_target=sc.groupby('target').loss_vs_own.median().to_dict())
strong=[49,64,79,94,112,130]
traces={}
residuals=[]
for start in range(0,3000,300):
 for f in strong:
  traces[f,start]=read(f'phaseD/X3_real/tracks/f{f}_s{start}_T300.csv')
 for f in strong:
  own=traces[f,start].VS_FM.to_numpy()
  guide=f*np.median(np.array([traces[ff,start].VS_FM.to_numpy()/ff for ff in strong if ff!=f]),axis=0)
  err=(own-guide)[idx]
  residuals.append(dict(tone=f,start=start,rms_demeaned_mHz=1000*np.std(err),rms_mHz=1000*np.sqrt(np.mean(err**2))))
checks['R4_track_residuals_definition_check']=pd.DataFrame(residuals).groupby('tone')[['rms_demeaned_mHz','rms_mHz']].median().to_dict()
checks['R2_track_comparison']=[]
for start in [600,900,1200,1500,1800]:
 tr=read(f'phaseD/X3_real/tracks/f100_s{start}_T300.csv')
 guide=100*np.median(np.array([traces[f,start].VS_FM.to_numpy()/f for f in strong]),axis=0)
 checks['R2_track_comparison'].append(dict(start=start,
  VS_offset_median=np.median(tr.VS_FM.to_numpy()-guide),
  PC_offset_median=np.median(tr.SUV.to_numpy()-guide),
  VS_PC_rms_demeaned_mHz=1000*np.std((tr.VS_FM-tr.SUV).to_numpy()[idx])))
gp=read(FIRST/'guided_position_check.csv')
checks['R2_positions']=gp.to_dict('records')
xc=read('phaseD/X3_real/X3_cases.csv')
checks['R2_GPS']=xc[(xc.tone_hz==100)&(xc.method=='VS_FM')&(xc.duration_s==300)][['segment_start_s','gps_mean_offset_hz']].to_dict('records')
er=read('phaseE/E4_guided_real/E4_records.csv')
checks['R5']=er[(er.tone_hz==133)&(er.segment_start_s==1200)][['method','peak_relative_periodogram_db']].to_dict('records')
checks['R5_original']=xc[(xc.tone_hz==133)&(xc.segment_start_s==1200)&(xc.duration_s==300)][['method','peak_relative_periodogram_db']].to_dict('records')
eg=er[er.method=='G_ADA']
checks['E_guided']=dict(n=len(eg),median_gain=eg.gain_peak_vs_VS_FM_db.median(),positive=int((eg.gain_peak_vs_VS_FM_db>0).sum()))

def clean(x):
 if isinstance(x,dict):return {str(k):clean(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,(np.integer,)):return int(x)
 if isinstance(x,(float,np.floating)):return float(x) if np.isfinite(x) else None
 return x

(OUT/'ledger_numeric_checks.json').write_text(json.dumps(clean(checks),ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'READ_SOURCES_SHA256.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(clean(checks),ensure_ascii=False,indent=2))
