from pathlib import Path
import json, hashlib, sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
W=Path(__file__).resolve().parents[2]; O=Path(__file__).parent; rows=[];sources={}
def read(rel):
 p=W/rel;sources[rel]=hashlib.sha256(p.read_bytes()).hexdigest();return pd.read_csv(p)
def add(key,value,expected=None,tol=.00051,source=''):
 value=float(value);ok=None if expected is None else abs(value-expected)<=tol
 rows.append(dict(key=key,value=value,expected=expected,tolerance=tol,passed=ok,source=source))
name='ADA_local_c04_t30_A'; keys=['scene','snr_db','record_id']
c=read('phaseD/C_confirm/C_records.csv');cp=c.pivot(index=keys,columns='method',values=['eta','peak_db'])
ada=c[c.method==name];lps=c[c.method=='SMR'];delta=cp.eta[name]-cp.eta.SMR
add('C_eta_LPS',lps.eta.mean(),.466);add('C_eta_ADA',ada.eta.mean(),.660);add('C_gain',delta.mean(),.194)
add('C_peak_gain',(cp.peak_db[name]-cp.peak_db.SMR).mean(),2.26,.0051)
for scene in ['S0','S2']:
 s=delta.xs(scene);add('C_harm_vs_LPS_'+scene,(s<-.01).mean(),.001 if scene=='S0' else .019,.00051)
 for snr,v in s.groupby(level='snr_db'):
  add(f'C_gain_{scene}_{snr}',v.mean(),{('S0',-20):.049,('S0',-18):.330,('S0',-17):.328,('S0',-14):.096}.get((scene,snr)))
 s=ada[ada.scene==scene];add('C_trigger_'+scene,s.triggered.mean(),.194 if scene=='S0' else .279)
 add('C_expansion_gain_'+scene,(cp.eta[name]-cp.eta.F02).xs(scene).mean(),.005 if scene=='S0' else .014)
add('C_RMSE_lt005_S0_minus20',((lps.scene=='S0')&(lps.snr_db==-20)&(lps.track_rmse_hz<.05)).sum(),26,0)
add('C_eta_LPS_S0_minus14',lps[(lps.scene=='S0')&(lps.snr_db==-14)].eta.mean(),.865)
add('C_trigger_all',ada.triggered.mean(),.23607,.0000051)
add('C_F02_gain',(cp.eta.F02-cp.eta.SMR).mean(),.184)
add('C_extra_ADA',(cp.eta[name]-cp.eta.F02).mean(),.009,.00051)
for m,e in [('F04',.336),('UNB',.359),(name,.020)]:
 add('C_S2_harm_vs_F02_'+m,((cp.eta[m]-cp.eta.F02).xs('S2')<-.01).mean(),e)
s2=cp.xs('S2');bad=(s2.eta.UNB-s2.eta.F02)<-.01
add('C_UNB_harmed_n',bad.sum(),503,0);add('C_UNB_harmed_peak_up_vs_F02_n',(s2.peak_db.UNB[bad]>s2.peak_db.F02[bad]).sum(),484,0)
add('C_UNB_harmed_peak_up_vs_LPS_n',(s2.peak_db.UNB[bad]>s2.peak_db.SMR[bad]).sum(),503,0)
add('C_S0_UNB_minus_ADA',(cp.eta.UNB-cp.eta[name]).xs('S0').mean(),.006)
add('C_UNB_peak_gain',(cp.peak_db.UNB-cp.peak_db.SMR).mean(),2.61,.0051)
x=read('phaseD/X2_frontend/X2_records.csv');e=read('phaseE/E2_frontend_ext/E2_records.csv')
x=pd.concat([x,e[e.frontend.isin(['DHMM','SUV_GRID'])]],ignore_index=True)
assert len(x)==8400 and not x.duplicated(keys+['frontend']).any()
tab=x.groupby('frontend')[['eta_in','eta_out','gain_eta']].mean();tab.to_csv(O/'table3_sim_recomputed.csv')
for f in tab.index:
 for m in tab.columns:add('X2_mean_'+f+'_'+m,tab.loc[f,m])
for f in ['VS','DHMM','MFT','SUV']:
 for (scene,snr),z in x[x.frontend==f].groupby(['scene','snr_db']):
  for m in ['eta_in','eta_out','gain_eta']:add(f'X2_{scene}_{snr}_{f}_{m}',z[m].mean())
t=read('phaseE/E1_trajexport/traj_export_X2_theory_metrics.csv');v=t[t.frontend=='VS']
for label,mask,nn in [('lt05',v.in_sigma2<.5,463),('05to5',(v.in_sigma2>=.5)&(v.in_sigma2<5),115),('ge5',v.in_sigma2>=5,822)]:
 z=v[mask];add('X2_VS_sigma_'+label+'_n',len(z),nn,0)
 for m in ['eta_in','eta_out']:add('X2_VS_sigma_'+label+'_'+m,z[m].mean())
for (scene,snr),z in v[v.in_sigma2>=5].groupby(['scene','snr_db']):add(f'X2_VS_sigma_ge5_{scene}_{snr}_n',len(z))
a=read('phaseE/E1_trajexport/traj_export_X2_diagA2.csv')
for f,z in a.groupby('frontend'):
 add('A2_rho_'+f,spearmanr(z.eta_clean_m1-z.eta_in,z.eta_out-z.eta_in).statistic,{'VS':.934,'V0':.929,'MFT':.937,'SUV':.224}[f])
 add('A2_recoverable_'+f,(z.eta_clean_m1-z.eta_in).mean(),.056 if f=='SUV' else None)
# Paired subsets, joined on record identifiers, never independently filtered averages.
th2=read('phaseE/E2_frontend_ext/traj_export_E2_theory_metrics.csv');allth=pd.concat([t,th2[th2.frontend=='DHMM']])
xx=x.pivot(index=keys,columns='frontend',values=['eta_out','eta_in','input_usable'])
tt=allth.pivot(index=keys,columns='frontend',values='in_sigma2')
for f,nn,dd in [('VS',546,.011),('DHMM',541,.020)]:
 m=(tt[f]<5)&(tt.SUV<5)&(tt.index.get_level_values('scene')=='S0');diff=xx.eta_out[f]-xx.eta_in.SUV
 add('paired_S0_small_'+f+'_n',m.sum(),nn,0);add('paired_S0_small_'+f+'_difference',diff[m].mean(),dd)
for f,nn,dd in [('VS',565,-.01968),('DHMM',555,-.10399)]:
 m=(xx.input_usable[f]==1)&(xx.input_usable.SUV==1)&(xx.index.get_level_values('scene')=='S2');diff=xx.eta_out[f]-xx.eta_in.SUV
 add('paired_S2_usable_'+f+'_n',m.sum(),nn,0);add('paired_S2_usable_'+f+'_difference',diff[m].mean(),dd,.0000051)
y=read('phaseD/X1_duration/X1_records.csv');y=y[y.method==name]
for (T,scene),z in y.groupby(['duration_s','scene']):
 for m in ['eta','eta_SMR','gain_eta_vs_SMR']:add(f'X1_{T}_{scene}_{m}',z[m].mean())
 add(f'X1_{T}_{scene}_harm',(z.gain_eta_vs_SMR<-.01).mean(),{(150,'S0'):.097,(150,'S2'):.340}.get((T,scene)))
for T,z in y.groupby('duration_s'):
 add(f'X1_{T}_runtime_median',z.runtime_s.median(),{150:.71897,600:16.55891}.get(T),.00001)
 P=int(T//10)+1;add(f'X1_{T}_max_iterations',np.floor(240*max(1,P/21)+.5));add(f'X1_{T}_max_fevals',np.floor(1000*max(1,P/21)+.5))
 aa=read(f'phaseE/E1_trajexport/traj_export_X1_T{T}_diagA2.csv');aa=aa[aa.frontend=='VS'];add(f'X1_{T}_A2_recoverable',(aa.eta_clean_m1-aa.eta_in).mean(),{150:.1243,300:.2404}.get(T),.00011)
eo=read('phaseA/tables/E0_phase_corrected_perrecord.csv')
eo.groupby(['dataset','estimator'])[['eta_full','eta_after_slow_correction','eta_after_fast_correction']].mean().to_csv(O/'E0_means_recomputed.csv')
# The injection columns are re-read as means; their frozen intervals remain in ledger v2.
p=W/'phaseE/E5_inject/E5_records.csv'
if p.exists():
 d=read('phaseE/E5_inject/E5_records.csv');d=d[d.frontend.isin(tab.index)]
 d.groupby('frontend')[['eta_in','eta_out','gain_eta']].mean().to_csv(O/'table3_inject_recomputed.csv')
df=pd.DataFrame(rows);df.to_csv(O/'CHAPTER4_NUMERIC_CHECK.csv',index=False)
bad=df[df.passed==False]
(O/'CHAPTER4_NUMERIC_CHECK.json').write_text(json.dumps({'entries':len(rows),'checked_expectations':int(df.expected.notna().sum()),'failed':bad.fillna('').to_dict('records'),'sources_sha256':sources},ensure_ascii=False,indent=2),encoding='utf-8')
print('entries',len(rows),'failed',bad.to_dict('records'));print(tab);print(pd.read_csv(O/'E0_means_recomputed.csv'))
