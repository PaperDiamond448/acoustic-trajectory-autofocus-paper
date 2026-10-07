"""Preserve the failed checkpoint and validate its complete, saved MATLAB result."""
from pathlib import Path
import hashlib,json,shutil
import numpy as np
import pandas as pd
from scipy.io import loadmat

ROOT=Path(__file__).resolve().parents[2]
PHASE=ROOT/'phaseE';OUT=PHASE/'E2_frontend_ext'
RECOVERY=OUT/'recovery_20261007_1848'
RECOVERY.mkdir(exist_ok=True)
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
for name in ('REMAINING_RUN_CONFIG.json','REMAINING_RUN_STATUS.json','remaining_20261007.out.log','remaining_20261007.err.log'):
    source=PHASE/name;target=RECOVERY/name
    if source.exists() and not target.exists():shutil.copy2(source,target)
for name in ('phaseE_ext_batch.m','phaseE_inject_batch.m','run_remaining_PhaseE.py'):
    target=RECOVERY/('before_'+name)
    if not target.exists():shutil.copy2(PHASE/'scripts'/name,target)
saved=[];invalid=[]
for path in sorted((OUT/'records').glob('B_*.csv')):
    mat=path.with_suffix('.mat');assert mat.exists(),str(mat)
    if path.stat().st_size==0:
        invalid.append(path)
    else:
        data=pd.read_csv(path);expected=2 if path.name.startswith('B_reg') else 3
        assert len(data)==expected and data.frontend.nunique()==expected
        assert np.isfinite(data[['eta_in','eta_out']].to_numpy()).all()
        saved.append({'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)})
    saved.append({'path':mat.relative_to(ROOT).as_posix(),'sha256':sha(mat)})
assert len(invalid)==1 and invalid[0].name=='B_S2_snr-10_id7_T300.csv'
for mat in (OUT/'records').glob('B_*.mat'):
    assert mat.with_suffix('.csv').exists(),f'Orphan MAT requires separate inspection: {mat}'
bad=invalid[0];shutil.copy2(bad,RECOVERY/('original_empty_'+bad.name))
result=loadmat(bad.with_suffix('.mat'),simplify_cells=True)['S']
assert result['scene']=='S2' and result['snr_db']==-10 and result['record_id']==7 and result['duration_s']==300
assert len(result['rows'])==3 and len(result['details'])==3 and len(result['truth_g'])==6000
assert [row['frontend'] for row in result['details']]==['SUV_GRID','DHMM','ORACLE']
values=[]
for row in result['rows']:
    values.append({'eta_in':float(row['eta_in']),'eta_out':float(row['eta_out'])})
    assert np.isfinite([row['eta_in'],row['eta_out']]).all()
for detail in result['details']:
    assert len(detail['input_g'])==6000 and len(detail['output_g'])==6000
    assert np.isfinite(detail['input_g']).all() and np.isfinite(detail['output_g']).all()
old=pd.read_csv(ROOT/'phaseD/X2_frontend/X2_records.csv')
old=old[(old.scene=='S2')&(old.snr_db==-10)&(old.record_id==7)]
assert len(old)==4 and old.input_hash.eq(result['input_hash']).all()
assert old.seed.eq(result['seed']).all()
protected=pd.read_csv(PHASE/'E0_preflight/PROTECTED_FILES_before.csv')
for row in protected.itertuples(index=False):assert sha(ROOT/row.path)==row.sha256,str(row.path)
pd.DataFrame(saved).to_csv(RECOVERY/'SAVED_CHECKPOINTS_BEFORE_sha256.csv',index=False)
status={'complete_csv_records':1276,'complete_B_inputs':1206,'regression_inputs':70,
    'empty_csv':str(bad),'saved_mat_sha256':sha(bad.with_suffix('.mat')),
    'saved_mat_complete':True,'input_hash_matches_archive':True,'seed_matches_archive':True,
    'saved_eta':values,'protected_files_unchanged':len(protected),
    'recovery':'Restore CSV from saved S.rows using MATLAB; no solver or simulation call.'}
(RECOVERY/'RECOVERY_PRECHECK.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
print(json.dumps(status),flush=True)
