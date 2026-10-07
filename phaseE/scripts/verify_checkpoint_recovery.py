"""Verify CSV restoration without changing any saved scientific result."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd
from scipy.io import loadmat

ROOT=Path(__file__).resolve().parents[2];PHASE=ROOT/'phaseE'
OUT=PHASE/'E2_frontend_ext';RECOVERY=OUT/'recovery_20261007_1848'
def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):h.update(data)
    return h.hexdigest()
before=pd.read_csv(RECOVERY/'SAVED_CHECKPOINTS_BEFORE_sha256.csv')
for row in before.itertuples(index=False):assert sha(ROOT/row.path)==row.sha256,str(row.path)
path=OUT/'records/B_S2_snr-10_id7_T300.csv';csv=pd.read_csv(path)
saved=loadmat(path.with_suffix('.mat'),simplify_cells=True)['S']
assert len(csv)==3 and list(csv.frontend)==['SUV_GRID','DHMM','ORACLE']
assert csv.input_hash.eq(saved['input_hash']).all() and csv.seed.eq(saved['seed']).all()
differences={}
for field in ('eta_in','eta_out','gain_eta','J','J_start','J_round0','runtime_s'):
    expected=np.asarray([row[field] for row in saved['rows']],dtype=float)
    differences[field]=float(np.max(np.abs(csv[field].to_numpy()-expected)))
    assert differences[field]<1e-12,(field,differences[field])
old=json.loads((RECOVERY/'REMAINING_RUN_CONFIG.json').read_text(encoding='utf-8'))['new_implementation_sha256']
unchanged=('estimate_dhmm.m','phaseE_ext_one.m','phaseE_inject_one.m','finalize_extension.py')
for name in unchanged:assert sha(PHASE/'scripts'/name)==old[name],name
protected=pd.read_csv(PHASE/'E0_preflight/PROTECTED_FILES_before.csv')
for row in protected.itertuples(index=False):assert sha(ROOT/row.path)==row.sha256,str(row.path)
cfg={'complete_B_inputs':1207,'restored_input':'B_S2_snr-10_id7_T300',
     'all_previous_checkpoint_files_unchanged':len(before),'protected_original_files_unchanged':len(protected),
     'numeric_method_sources_unchanged':list(unchanged),'restoration_csv_mat_max_abs_diff':differences,
     'solver_calls':0,'simulation_calls':0,'passed':True,
     'csv_sha256':sha(path),'mat_sha256':sha(path.with_suffix('.mat')),
     'io_wrapper_sha256_after':{name:sha(PHASE/'scripts'/name) for name in ('phaseE_ext_batch.m','phaseE_inject_batch.m','run_remaining_PhaseE.py')}}
(RECOVERY/'RECOVERY_CHECKS.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
print(json.dumps(cfg),flush=True)
