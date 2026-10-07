"""Read archived MAT-v7 trajectories; write the task-A H5 in one Python process."""
from pathlib import Path
import csv
import hashlib
import json
import os
import sys
import time

for name in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[name]='1'
LOCAL=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(LOCAL/'_local_pydeps'))
import h5py
import numpy as np
import pandas as pd
from scipy.io import loadmat

ROOT=LOCAL.parent
OUT=LOCAL/'E1_trajexport'
SOURCE=ROOT/'phaseD/X2_frontend'


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def run():
    complete=json.loads((OUT/'truth_X2_checked_status.json').read_text(encoding='utf-8'))
    assert complete['complete'] and complete['all_input_hashes_match'] and complete['records']==1400
    assert sha(OUT/'truth_X2_checked.h5')==complete['sha256']
    truth_index=pd.read_csv(OUT/'truth_X2_checked_index.csv')
    truth_map=truth_index.set_index(['scene','snr_db','record_id'])
    old=pd.read_csv(SOURCE/'X2_records.csv')
    old_map=old.set_index(['scene','snr_db','record_id','frontend'])
    assert old_map.index.is_unique and truth_map.index.is_unique
    files=sorted((SOURCE/'chunks').glob('T300_*.mat')); assert len(files)==140
    stem=OUT/'traj_export_X2'
    assert not stem.with_suffix('.h5').exists()
    signature=sha(ROOT/'phaseD/codeX/SOURCE_MANIFEST_X_sha256.csv')
    rows=[];sources=[];count=0;tic=time.monotonic()
    with h5py.File(OUT/'truth_X2_checked.h5','r') as truths,h5py.File(stem.with_suffix('.h5'),'w') as h:
        assert truths['truth'].shape==(1400,6000)
        h.create_dataset('truth',data=truths['truth'][:],dtype='float64',chunks=(1,6000),compression='gzip',compression_opts=4)
        ds_i=h.create_dataset('input',(5600,6000),dtype='float64',chunks=(1,6000),compression='gzip',compression_opts=4)
        ds_o=h.create_dataset('output',(5600,6000),dtype='float64',chunks=(1,6000),compression='gzip',compression_opts=4)
        h.attrs['fs_hz']=20.0;h.attrs['duration_s']=300.0;h.attrs['evaluation_interval_s']=[5.,295.]
        h.attrs['frequency_units']='Hz baseband';h.attrs['time_grid']='t=n/20, n=0,...,5999';h.attrs['index_origin']=0
        for j,path in enumerate(files,1):
            before=sha(path)
            data=loadmat(path,simplify_cells=True,variable_names=['results','signature','phase_id'])
            assert data['signature']==signature and int(data['phase_id'])==54
            results=data['results']; assert len(results)==10
            for record in results:
                scene=record['scene'];snr=int(record['snr_db']);rid=int(record['record_id'])
                truth=truth_map.loc[(scene,snr,rid)]
                assert record['input_hash']==truth.input_hash
                details=record['details']; assert len(details)==4
                for f,(name,detail) in enumerate(zip(['VS','MFT','SUV','V0'],details)):
                    assert detail['frontend']==name
                    expected=old_map.loc[(scene,snr,rid,name)]
                    assert expected.input_hash==record['input_hash'] and expected.seed==truth.seed
                    gi=np.asarray(detail['input_g'],dtype=np.float64).ravel()
                    go=np.asarray(detail['ada']['out']['g'],dtype=np.float64).ravel()
                    assert gi.shape==go.shape==(6000,) and np.isfinite(gi).all() and np.isfinite(go).all()
                    # MATLAB string fields use MCOS serialization in MAT-v7.
                    # The char frontend in details and the frozen four-row
                    # ordering identify the numeric row without decoding MCOS.
                    archived_row=record['rows'][f]
                    assert abs(archived_row['eta_in']-expected.eta_in)<1e-14
                    assert abs(archived_row['eta_out']-expected.eta_out)<1e-14
                    ds_i[count]=gi;ds_o[count]=go
                    rows.append({'row':count,'truth_row':int(truth.truth_row),'scene':scene,'snr_db':snr,
                                 'record_id':rid,'seed':int(truth.seed),'frontend':name,
                                 'eta_in':expected.eta_in,'eta_out':expected.eta_out,'input_usable':expected.input_usable,
                                 'input_hash':expected.input_hash,'duration_s':300,
                                 'eta_in_matlab_check':archived_row['eta_in'],'eta_out_matlab_check':archived_row['eta_out'],
                                 'eta_in_matlab_abs_diff':abs(archived_row['eta_in']-expected.eta_in),
                                 'eta_out_matlab_abs_diff':abs(archived_row['eta_out']-expected.eta_out)})
                    count+=1
            after=sha(path); assert before==after
            sources.append({'path':str(path),'bytes':path.stat().st_size,'sha256_before':before,'sha256_after':after,'unchanged':True})
            del data,results
            if j%10==0:print(f'X2 existing-trajectory export {j}/140 chunks; {count} rows; {time.monotonic()-tic:.1f}s',flush=True)
    assert count==5600 and len({r['truth_row'] for r in rows})==1400
    pd.DataFrame(rows).to_csv(str(stem)+'_index.csv',index=False)
    pd.DataFrame(sources).to_csv(str(stem)+'_source_chunks_sha256.csv',index=False)
    status={'export_complete':True,'trajectory_rows':count,'truth_records':1400,'all_input_hashes_match':True,
            'all_source_chunks_unchanged':True,'max_eta_in_matlab_abs_diff':max(r['eta_in_matlab_abs_diff'] for r in rows),
            'max_eta_out_matlab_abs_diff':max(r['eta_out_matlab_abs_diff'] for r in rows),'elapsed_seconds':time.monotonic()-tic,
            'h5_sha256':sha(stem.with_suffix('.h5')),'export_adapter':'Python reads existing MAT-v7; truth/hash recreation uses frozen MATLAB generator'}
    Path(str(stem)+'_export_status.json').write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    config={'task':'A','stage':'X2','duration_s':300,'phase_id':54,'truth_records':1400,'trajectory_rows':5600,
            'samples_per_row':6000,'fs_hz':20,'evaluation_interval_s':[5,295],'source_directory':str(SOURCE),
            'seed_rule':'master_seed+54e6+1e4*scene_code+record_id','frontends':['VS','MFT','SUV','V0'],
            'h5_local_path':str(stem.with_suffix('.h5')),'no_new_estimation':True,'chunk_count':140,
            'export_adapter':status['export_adapter']}
    Path(str(stem)+'_run_config.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(status),flush=True)


if __name__=='__main__':run()
