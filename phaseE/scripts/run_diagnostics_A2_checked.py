"""Run the supplied diagnostic unchanged, then validate against archived rows."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'phaseE/E1_trajexport'
SCRIPT = Path(__file__).with_name('diagnostics_A2.py')
STEMS = ['traj_export_X2'] + [f'traj_export_X1_T{t}' for t in (150,300,450,600)]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def main():
    env=os.environ.copy()
    env['PYTHONPATH']=str(ROOT/'phaseE/_local_pydeps')+os.pathsep+env.get('PYTHONPATH','')
    for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS','NUMEXPR_NUM_THREADS'):
        env[key]='1'
    import pandas as pd
    import numpy as np
    config={'task':'A2','datasets':STEMS,'workers':6,'script_sha256':sha(SCRIPT),
            'script_unchanged':True,'eta_tolerance':1e-6,'new_simulations':0,
            'inputs':[{ 'dataset':s,'h5_sha256':sha(OUT/(s+'.h5')),
                        'index_sha256':sha(OUT/(s+'_index.csv'))} for s in STEMS],
            'interpretation':'Numerically found penalized-objective solutions, not certified global maxima; clean-out difference also includes solver and constraint differences.'}
    cp=OUT/'run_config_A2.json'
    if cp.exists():
        assert json.loads(cp.read_text(encoding='utf-8'))==config
    else: cp.write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    checks=[]
    for item in config['inputs']:
        stem=item['dataset']; name=OUT/stem
        status=OUT/(stem+'_diagA2_check.json')
        if not status.exists():
            print('START',stem,flush=True)
            started=time.time()
            log=OUT/(stem+'_diagA2.log')
            with log.open('w',encoding='utf-8') as f:
                p=subprocess.run([sys.executable,'-X','utf8',str(SCRIPT),str(name),'6'],env=env,stdout=f,stderr=subprocess.STDOUT)
            if p.returncode:
                raise RuntimeError(f'{stem}: exit {p.returncode}; see {log}')
            ix=pd.read_csv(str(name)+'_index.csv'); d=pd.read_csv(str(name)+'_diagA2.csv')
            assert len(d)==len(ix) and d.row.is_unique and set(d.row)==set(ix.row)
            for col in ix.columns:
                a=ix.sort_values('row')[col].reset_index(drop=True)
                b=d.sort_values('row')[col].reset_index(drop=True)
                pd.testing.assert_series_equal(a,b,check_names=False)
            vals=d[['eta_clean_m1','eta_clean_m2','eta_in_recomputed']].to_numpy()
            assert np.isfinite(vals).all() and (vals>=-1e-12).all() and (vals<=1+1e-10).all()
            err=float((d.eta_in_recomputed-d.eta_in).abs().max()); assert err<1e-6
            assert sha(name.with_suffix('.h5'))==item['h5_sha256']
            check={'task':'A2','dataset':stem,'rows':len(d),'passed':True,'eta_in_max_abs_diff':err,
                   'eta_tolerance':1e-6,'input_h5_unchanged':True,'script_sha256':sha(SCRIPT),
                   'elapsed_s':time.time()-started,
                   'm1_below_input_rows':int((d.eta_clean_m1<d.eta_in-1e-6).sum()),
                   'm2_below_m1_rows':int((d.eta_clean_m2<d.eta_clean_m1-1e-6).sum()),
                   'm1_below_saved_output_rows':int((d.eta_clean_m1<d.eta_out-1e-6).sum())}
            status.write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')
        else:
            check=json.loads(status.read_text(encoding='utf-8')); assert check['passed']
        checks.append(check)
        print('DONE',json.dumps(check),flush=True)
    pd.DataFrame(checks).to_csv(OUT/'DIAGNOSTICS_A2_CHECKS.csv',index=False)
    protected=pd.read_csv(ROOT/'phaseE/E0_preflight/PROTECTED_FILES_before.csv')
    for r in protected.itertuples(index=False):
        assert sha(ROOT/r.path)==r.sha256, f'Frozen file changed: {r.path}'
    print('COMPLETE',sum(c['rows'] for c in checks),'rows;',len(protected),'protected files unchanged',flush=True)

if __name__=='__main__': main()
