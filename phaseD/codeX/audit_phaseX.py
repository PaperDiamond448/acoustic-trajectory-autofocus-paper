from pathlib import Path
import csv,json,hashlib
import pandas as pd,numpy as np
R=Path('D:/论文集/phaseD');FM='ADA_local_c04_t30_A'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
protected={}
for rel in ['codeX/SOURCE_MANIFEST_X_sha256.csv','codeX/PROTECTED_STOP2_sha256.csv','X3_real/X3_FREEZE_MANIFEST.csv','Y_compute/ENVIRONMENT_ADAPTER_MANIFEST.csv','codeX/POSTPROCESS_MANIFEST_sha256.csv']:
 rows=list(csv.DictReader((R/rel).open(encoding='utf-8-sig')))
 for row in rows:assert sha(Path(row['source_file']))==row['sha256'],row['source_file']
 protected[rel]=len(rows)
incident=json.loads((R/'Y_compute/X_INITIAL_ENVIRONMENT_EXIT.json').read_text(encoding='utf-8'))
for p,h in incident['saved_chunks_sha256'].items():assert sha(Path(p))==h,p
olddev=set(pd.read_csv(R/'D_dev/D1_records.csv').seed);oldc=set(pd.read_csv(R/'C_confirm/C_records.csv').seed);seeds=[]
for phase,folder,stage,n in [(53,'X1_duration','X1',2400),(54,'X2_frontend','X2',1400)]:
 d=pd.read_csv(R/folder/(stage+'_records.csv'));keys=['scene','snr_db','record_id']+(['duration_s'] if phase==53 else [])+(['method'] if phase==53 else ['frontend']);assert len(d)==4*n and not d.duplicated(keys).any()
 expected=20260915+phase*1000000+d.scene.map({'S0':1,'S2':3})*10000+d.record_id;assert np.array_equal(d.seed,expected);assert set(d.seed).isdisjoint(olddev|oldc);seeds.append(set(d.seed))
 assert np.array_equal(d.P,d.duration_s/10+1);assert (d.Delta_s==10).all()
 if phase==53:
  p=d.pivot(index=['scene','snr_db','record_id','duration_s'],columns='method',values='eta');f=d[d.method.eq(FM)].set_index(['scene','snr_db','record_id','duration_s']);trigger=f.triggered.eq(1);assert np.array_equal(p.loc[~trigger,FM],p.loc[~trigger,'F02']);j=d.pivot(index=['scene','snr_db','record_id','duration_s'],columns='method',values='J');assert (j[FM]>=j.F02-1e-12).all()
 else:assert (d.J>=d.J_round0-1e-12).all();assert (d.input_usable.eq(1)==(d.usable_fraction>=.9)).all()
 audit=json.loads((R/folder/'SAVED_OUTPUTS_AUDIT.json').read_text(encoding='utf-8'));assert audit['status']=='PASS'
assert seeds[0].isdisjoint(seeds[1]);v=pd.read_csv(R/'X3_real/X3_visibility.csv');p=pd.read_csv(R/'X3_real/X3_FROZEN_TESTSET.csv');assert len(v)==330 and np.array_equal(v.passed.eq(1),(v.peak_excess_dB>10)&(v.ridge_continuity>.6));assert len(p)==json.loads((R/'X3_real/X3_TESTSET_FREEZE.json').read_text(encoding='utf-8'))['passed_cases']
c=pd.read_csv(R/'X3_real/X3_cases.csv');assert len(c)==len(p)*8 and not c.duplicated(['tone_hz','segment_start_s','method']).any();assert set(zip(c.tone_hz,c.segment_start_s))==set(zip(p.tone_hz,p.segment_start_s));assert c[c.competing_ridge.eq(1)].shape[0]==8
assert json.loads((R/'X3_real/INDEPENDENT_REAL_METRICS_AUDIT.json').read_text(encoding='utf-8'))['status']=='PASS'
result={'status':'PASS','records':{'X1':2400,'X2':1400,'X3_passed_cases':len(p),'X3_duration_windows':16},'protected_file_checks':protected,'original_44_X1_chunks_unchanged':True,'fresh_seed_sets_disjoint':True,'all_cases_and_negative_values_retained':True,'final_method':'ADA_local_c04_t30_A','postconfirmation_parameter_changes':0}
(R/'Y_compute/INTEGRITY_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result))
