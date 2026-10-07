from pathlib import Path
import json,warnings
import numpy as np
import pandas as pd
R=Path('D:/论文集/phaseD');FM='ADA_local_c04_t30_A';SCENES=['S0','S2']
def write(obj,p):p.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=True),encoding='utf-8')
def interval(a):
 a=np.asarray(a);a=a[np.isfinite(a)]
 return [float(x) for x in np.quantile(a,[.025,.975])] if len(a) else [np.nan,np.nan]
def draws(seed):
 rng=np.random.default_rng(seed);return [rng.integers(0,100,(2000,100)) for _ in SCENES]
def pct(v,q):return float(np.nanquantile(v,q)) if np.isfinite(v).any() else np.nan
def analyze_x1():
 O=R/'X1_duration';d=pd.read_csv(O/'X1_records.csv');assert len(d)==9600
 ks=['scene','snr_db','record_id','duration_s'];p=d.pivot(index=ks,columns='method',values='peak_db');s=p['SMR']
 d['gain_peak_vs_SMR_db']=[p.loc[tuple(row[k] for k in ks),row['method']]-s.loc[tuple(row[k] for k in ks)] for _,row in d.iterrows()]
 cell=[];pooled=[];D=draws(20261053)
 metrics=['eta','peak_db','gain_eta_vs_SMR','gain_peak_vs_SMR_db','runtime_s','t_round0_s','t_expansion_s','triggered','harm_vs_SMR']
 for (scene,snr,T,m),g in d.groupby(['scene','snr_db','duration_s','method'],sort=True):
  for met in metrics:
   x=g.sort_values('record_id')[met].to_numpy(float);boot=x[D[SCENES.index(scene)]].mean(axis=1);lo,hi=interval(boot)
   cell.append(dict(scene=scene,snr_db=int(snr),duration_s=int(T),method=m,metric=met,n=len(x),mean=float(x.mean()),lo=lo,hi=hi,median=float(np.median(x)),p90=float(np.quantile(x,.9))))
 for (T,m),g in d.groupby(['duration_s','method'],sort=True):
  for met in metrics:
   vals=[];boots=[]
   for i,sc in enumerate(SCENES):
    a=g[g.scene.eq(sc)].pivot(index='record_id',columns='snr_db',values=met).sort_index().to_numpy(float);assert a.shape==(100,3)
    vals.append(a.mean());boots.append(a[D[i]].mean(axis=(1,2)))
   for scope,point,boot in [('pooled',np.mean(vals),np.mean(boots,axis=0)),*[(sc,vals[i],boots[i]) for i,sc in enumerate(SCENES)]]:
    lo,hi=interval(boot);sub=g if scope=='pooled' else g[g.scene.eq(scope)]
    pooled.append(dict(scope=scope,duration_s=int(T),method=m,metric=met,mean=float(point),lo=lo,hi=hi,median=float(sub[met].median()),p90=float(sub[met].quantile(.9))))
 pd.DataFrame(cell).to_csv(O/'X1_cell_stats.csv',index=False);pd.DataFrame(pooled).to_csv(O/'X1_summary.csv',index=False)
 d.to_csv(O/'X1_analysis_records.csv',index=False)
 write({'records':2400,'method_rows':9600,'bootstrap_seed':20261053,'bootstrap_replicates':2000,'unit':'Within-scene seed; all three SNRs and all four durations carried together; equal cell weights','hard_fail_rows':int(d.hard_fail.sum()),'budget_cap_rows':int(d.budget_cap.sum())},O/'X1_ANALYSIS.json')
def analyze_x2():
 O=R/'X2_frontend';d=pd.read_csv(O/'X2_records.csv');assert len(d)==5600;D=draws(20261054);cell=[];pool=[];bins=[]
 for (f,sc,snr),g in d.groupby(['frontend','scene','snr_db']):
  x=g.sort_values('record_id');boot=x.gain_eta.to_numpy()[D[SCENES.index(sc)]].mean(axis=1);lo,hi=interval(boot)
  cell.append(dict(frontend=f,scene=sc,snr_db=int(snr),n=len(x),usable_n=int(x.input_usable.sum()),eta_in=float(x.eta_in.mean()),eta_out=float(x.eta_out.mean()),gain_eta=float(x.gain_eta.mean()),lo=lo,hi=hi,gain_peak_db=float(x.gain_peak_db.mean()),positive_fraction=float(x.gain_positive.mean()),trigger_fraction=float(x.triggered.mean())))
 for f,g in d.groupby('frontend'):
  for group in ['all','input_usable']:
   boots=[];points=[];nonempty=[];emptyboot=0
   for i,sc in enumerate(SCENES):
    q=g[g.scene.eq(sc)];a=q.pivot(index='record_id',columns='snr_db',values='gain_eta').sort_index().to_numpy(float)
    if group=='input_usable':
     ok=q.pivot(index='record_id',columns='snr_db',values='input_usable').sort_index().to_numpy(bool);a=np.where(ok,a,np.nan)
    with warnings.catch_warnings():
     warnings.simplefilter('ignore',RuntimeWarning);cellmeans=np.nanmean(a,axis=0);bc=np.nanmean(a[D[i]],axis=1)
    nonempty.extend(np.isfinite(cellmeans));points.append(cellmeans.mean());boots.append(bc.mean(axis=1));emptyboot+=int((~np.isfinite(bc)).any(axis=1).sum())
   point=float(np.mean(points));boot=np.mean(boots,axis=0);lo,hi=interval(boot)
   # Never silently discard bootstrap replicates with empty input-usable cells.
   estimable=all(nonempty) and np.isfinite(boot).all()
   if not estimable:lo=hi=np.nan
   sub=g if group=='all' else g[g.input_usable.eq(1)]
   pool.append(dict(frontend=f,group=group,n=len(sub),equal_cell_mean=point,lo=lo,hi=hi,estimable=estimable,nonempty_cells=int(sum(nonempty)),total_cells=14,bootstrap_empty_cell_replicates=emptyboot,record_weighted_mean=float(sub.gain_eta.mean()),interpretation=('systematically_negative_usable' if f=='SUV' and group=='input_usable' and estimable and hi<0 else 'descriptive')))
  for j in range(10):
   q=g[(g.eta_in>=j/10)&(g.eta_in<((j+1)/10 if j<9 else 1.000000001))];r=q[q.eta_in<.95]
   bins.append(dict(frontend=f,bin_left=j/10,bin_right=(j+1)/10,bin_center=(j+.5)/10,n=len(q),gain_eta=float(q.gain_eta.mean()),recovery_n=len(r),recovery_fraction=float((r.gain_eta/(1-r.eta_in)).mean())))
 pd.DataFrame(cell).to_csv(O/'X2_summary.csv',index=False);pd.DataFrame(pool).to_csv(O/'X2_pooled.csv',index=False);pd.DataFrame(bins).to_csv(O/'X2_eta_bins.csv',index=False)
 write({'records':1400,'frontend_rows':5600,'bootstrap_seed':20261054,'bootstrap_replicates':2000,'unit':'Within-scene seed carried across all seven SNRs and all four frontends','hard_fail_rows':int(d.hard_fail.sum()),'budget_cap_rows':int(d.budget_cap.sum()),'usable_ci_policy':'Equal fourteen conditional cell means. Empty cell or empty-cell bootstrap replicate makes CI not estimable; no record deletion or reweighting.'},O/'X2_ANALYSIS.json')
def analyze_x3():
 O=R/'X3_real';d=pd.read_csv(O/'X3_cases.csv');vis=pd.read_csv(O/'X3_FROZEN_TESTSET.csv');assert len(d)==len(vis)*8
 d=d.merge(vis[['tone_hz','segment_start_s','group','set_number','source_level_db','source_level_inferred','peak_excess_dB','ridge_continuity']],on=['tone_hz','segment_start_s'],validate='many_to_one')
 pairs=[('VS_FM','SMR'),('VS_FM','MFT'),('MFT_FM','MFT'),('SUV_FM','SUV'),('VS_FM','F02'),('VS_FM','UNB')];rows=[]
 for key,g in d.groupby(['tone_hz','segment_start_s']):
  p=g.set_index('method')
  for out,entry in pairs:
   a,b=p.loc[out],p.loc[entry];rows.append(dict(tone_hz=int(key[0]),segment_start_s=int(key[1]),group=a.group,set_number=int(a.set_number),source_level_inferred=bool(a.source_level_inferred),pair=f'{out}-{entry}',gain_peak_db=float(a.peak_relative_periodogram_db-b.peak_relative_periodogram_db),gain_prominence_db=float(a.prominence_db-b.prominence_db),width_ratio=float(b.width_3db_hz/a.width_3db_hz),module_runtime_s=float(a.runtime_s)))
 inc=pd.DataFrame(rows);summary=[]
 for (group,pair),g in inc.groupby(['group','pair']):
  for met in ['gain_peak_db','gain_prominence_db','width_ratio']:
   x=g[met].to_numpy();finite=np.isfinite(x);summary.append(dict(group=group,pair=pair,metric=met,cases=len(x),finite_n=int(finite.sum()),median=pct(x,.5),q25=pct(x,.25),q75=pct(x,.75),positive_n=int(np.sum(x[finite]>(1 if met=='width_ratio' else 0)))))
 d.to_csv(O/'X3_analysis_cases.csv',index=False);inc.to_csv(O/'X3_increments.csv',index=False);pd.DataFrame(summary).to_csv(O/'X3_summary.csv',index=False)
 duration=pd.read_csv(O/'X3_duration.csv');assert len(duration)==16*3
 write({'cases':len(vis),'method_rows':len(d),'duration_windows':16,'duration_rows':len(duration),'hard_fail_rows':int(d.hard_fail.sum()),'budget_cap_rows':int(d.budget_cap.sum()),'groups':vis.groupby('group').size().to_dict(),'A3_flips':int(pd.read_csv(O/'X3_A3_comparison.csv').pass_flipped.sum()),'no_significance_tests':True,'source_level_note':'Set 5 120 dB inferred from 4-dB step; shallow level unpublished'},O/'X3_ANALYSIS.json')
def analyze_y():
 O=R/'Y_compute';rows=[]
 C=pd.read_csv(R/'C_confirm/C_records.csv');keys=['scene','snr_db','record_id'];base=C[C.method.eq('F02')].set_index(keys).runtime_s
 fm=C[C.method.eq(FM)].copy();fm['round0']=base.reindex(pd.MultiIndex.from_frame(fm[keys])).to_numpy();fm['expansion']=fm.runtime_s-fm.round0
 for name,a in [('frontend',fm.t_frontend_s),('VIT',fm.t_vit_s),('family',fm.t_family_s),('SMR',fm.t_smr_s),('BTA_round0',fm.round0),('BTA_expansion_given_trigger',fm.loc[fm.triggered.eq(1),'expansion']),('BTA_total',fm.runtime_s),('BTA_extra_over_SMR_fraction_T',fm.runtime_s/300)]:rows.append(dict(stage='C',component=name,n=len(a),median=float(a.median()),p90=float(a.quantile(.9))))
 for stage,folder in [('X1','X1_duration'),('X2','X2_frontend')]:
  d=pd.read_csv(R/folder/(stage+'_records.csv'));d=d[d.method.eq(FM)]
  groups=d.groupby('duration_s') if stage=='X1' else d.groupby('frontend')
  for key,g in groups:
   for met in ['runtime_s','t_round0_s','t_expansion_s']:
    rows.append(dict(stage=stage,component=f'{key}:{met}',n=len(g),median=float(g[met].median()),p90=float(g[met].quantile(.9))))
 pd.DataFrame(rows).to_csv(O/'Y_summary.csv',index=False)
 d1=pd.read_csv(R/'D_dev/D1_records.csv');d1[d1.arm.eq('scaled')].groupby(['P','method']).runtime_s.agg(['median',lambda x:x.quantile(.9)]).reset_index().rename(columns={'<lambda_0>':'p90'}).to_csv(O/'D1_time_vs_P.csv',index=False)
 write({'timing':'Per-call loaded wall times on six Processes workers; no concurrent X numerical stages. Not isolated serial benchmarks. Batch wall time reported separately.','C_trigger_fraction':float(fm.triggered.mean()),'C_records':2800},O/'Y_TIMING.json')
if __name__=='__main__':
 import sys
 for stage in sys.argv[1:] or ['X1','X2','X3','Y']:{'X1':analyze_x1,'X2':analyze_x2,'X3':analyze_x3,'Y':analyze_y}[stage]();print(stage+' analysis complete')
