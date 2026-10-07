"""Check every completed B MAT/CSV against the archived inputs and truth export."""
from pathlib import Path
import hashlib,json,os,sys,time
for key in ('OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','OMP_NUM_THREADS'):os.environ[key]='1'
ROOT=Path(__file__).resolve().parents[2];PHASE=ROOT/'phaseE'
sys.path.insert(0,str(PHASE/'_local_pydeps'))
import h5py
import numpy as np
import pandas as pd
from scipy.io import loadmat

OUT=PHASE/'E2_frontend_ext'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    jobs=pd.read_csv(OUT/'B_jobs.csv')
    original=pd.read_csv(ROOT/'phaseD/X2_frontend/X2_records.csv')
    archived=original.groupby(['scene','snr_db','record_id']).first()
    index=pd.read_csv(PHASE/'E1_trajexport/traj_export_X2_index.csv')
    truth_rows=index.groupby(['scene','snr_db','record_id']).truth_row.first()
    checks=[];maximum={};field_checks=0
    with h5py.File(PHASE/'E1_trajexport/traj_export_X2.h5','r') as truths:
        for job in jobs.itertuples(index=False):
            path=OUT/'records'/f'{job.tag}.csv'
            while not path.exists() or path.stat().st_size==0:
                state=json.loads((PHASE/'REMAINING_RUN_STATUS.json').read_text())
                if state.get('state')=='stopped':raise RuntimeError('Main run stopped before integrity verification completed.')
                print('Waiting for saved B input',len(checks)+1,'/1400',flush=True)
                time.sleep(30)
            data=pd.read_csv(path);saved=loadmat(path.with_suffix('.mat'),simplify_cells=True)['S']
            key=(job.scene,job.snr_db,job.record_id);reference=archived.loc[key]
            assert len(data)==3 and len(saved['rows'])==3 and len(saved['details'])==3
            assert list(data.frontend)==['SUV_GRID','DHMM','ORACLE']
            assert data.input_hash.eq(reference.input_hash).all() and saved['input_hash']==reference.input_hash
            assert data.seed.eq(reference.seed).all() and saved['seed']==reference.seed
            assert saved['scene']==job.scene and saved['snr_db']==job.snr_db and saved['record_id']==job.record_id
            truth=np.asarray(saved['truth_g']);assert len(truth)==6000
            assert np.array_equal(truth,truths['truth'][int(truth_rows.loc[key])]),f'Truth differs: {job.tag}'
            local_max=0.;fields=0
            for i,detail in enumerate(saved['details']):
                assert detail['frontend']==data.iloc[i].frontend
                for name in ('input_g','output_g'):
                    assert len(detail[name])==6000 and np.isfinite(detail[name]).all()
                for name,value in saved['rows'][i].items():
                    if name in data and isinstance(value,(int,float,bool,np.number)) and np.isreal(value):
                        actual=float(data.iloc[i][name]);expected=float(value)
                        assert np.isfinite([actual,expected]).all(),(job.tag,name)
                        delta=abs(actual-expected)
                        assert np.isclose(actual,expected,rtol=5e-14,atol=1e-12),(job.tag,name,delta)
                        local_max=max(local_max,delta);maximum[name]=max(maximum.get(name,0.),delta);fields+=1
            field_checks+=fields
            checks.append({'tag':job.tag,'scene':job.scene,'snr_db':job.snr_db,'record_id':job.record_id,
                'rows':3,'numeric_field_checks':fields,'numeric_max_abs_diff':local_max,
                'csv_sha256':sha(path),'mat_sha256':sha(path.with_suffix('.mat')),
                'input_hash_match':True,'seed_match':True,'truth_bitwise_equal_to_archive':True,'passed':True})
            if len(checks)%100==0:print('Integrity checked',len(checks),'/1400',flush=True)
    assert len(checks)==1400
    temp=OUT/'B_CHECKPOINT_INTEGRITY.pending.csv'
    pd.DataFrame(checks).to_csv(temp,index=False);temp.replace(OUT/'B_CHECKPOINT_INTEGRITY.csv')
    status={'passed':True,'input_records':1400,'method_rows':4200,'checked_numeric_fields':field_checks,
            'all_input_hashes_and_seeds_match_archive':True,'all_truth_trajectories_bitwise_equal_to_archive':True,
            'all_trajectories_finite':True,'max_csv_mat_abs_difference_by_numeric_field':maximum,
            'scope':'Full MAT/CSV/input/truth check. Independent eta recomputation is in FINAL_STATUS and export checks.'}
    temp=OUT/'B_CHECKPOINT_INTEGRITY.pending.json'
    temp.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8');temp.replace(OUT/'B_CHECKPOINT_INTEGRITY.json')
    print(json.dumps(status),flush=True)

if __name__=='__main__':main()
