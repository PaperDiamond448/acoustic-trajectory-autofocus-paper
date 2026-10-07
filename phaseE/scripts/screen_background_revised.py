"""Calibrate the revised screening threshold BEFORE reading real-window powers."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
import pandas as pd
from scipy.io import loadmat
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'phaseE/E5_inject'
CAL=OUT/'screen_revision_20261007'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def statistic(power):
    # power: [..., frequency=200, frame=291]. Equal frequency grids for both inputs.
    s=power.mean(axis=-1)
    local=np.lib.stride_tricks.sliding_window_view(s,11,axis=-1)
    baseline=np.median(local,axis=-1) # outputs correspond to original bins 5..194
    use=np.arange(75,126) # baseband -2.5 ... +2.5 Hz
    ratio=s[...,use]/baseline[...,use-5]
    return (10*np.log10(ratio)).max(axis=-1)
def main():
    CAL.mkdir(parents=True,exist_ok=True)
    lock=json.loads((ROOT/'phaseE/PREREGISTRATION_PhaseE_20261007.sha256.json').read_text())
    assert sha(ROOT/'phaseE'/lock['file'])==lock['sha256']
    cfg={'task':'D_revised_screen','null_windows':2000,'seed':2026100701,'generator':'NumPy PCG64',
      'numpy_version':np.__version__,'fs_hz':20,'duration_s':300,'window':'symmetric Hann, 200 samples',
      'hop_samples':20,'fft_points':200,'frequency_grid_hz':.1,'frames':291,
      'baseline_halfwidth_hz':.5,'baseline_points':11,'test_abs_frequency_hz_max':2.5,
      'null_percentile':.99,'quantile_method':'linear','round_threshold':'ceil to 0.1 dB',
      'retain_if':'D < threshold','preregistration_sha256':lock['sha256'],
      'no_injection_started':True,'script_sha256':sha(Path(__file__))}
    (CAL/'run_config.json').write_text(json.dumps(cfg,indent=2)+'\n',encoding='utf-8')
    frozen=CAL/'CALIBRATION_FREEZE.json';nullpath=CAL/'WHITE_NOISE_CALIBRATION.csv'
    if not frozen.exists():
        rng=np.random.default_rng(cfg['seed']);w=np.hanning(200);frame=np.arange(200)[None,:]+np.arange(291)[:,None]*20
        vals=[]
        for a in range(0,2000,16):
            n=min(16,2000-a);r=rng.standard_normal((n,6000,2));z=(r[:,:,0]+1j*r[:,:,1])/np.sqrt(2)
            framed=z[:,frame]*w
            power=abs(np.fft.fftshift(np.fft.fft(framed,200,axis=-1),axes=-1))**2/np.sum(w*w)
            vals.extend(statistic(np.swapaxes(power,-1,-2)).tolist())
            if (a+n)%400==0:print('CALIBRATION',a+n,'/2000',flush=True)
        d=pd.DataFrame({'null_window':np.arange(2000),'D_db':vals});d.to_csv(nullpath,index=False)
        q=float(np.quantile(vals,.99,method='linear'));th=float(np.ceil(q*10)/10)
        status={'null_windows':2000,'null_median_db':float(np.median(vals)),'null_q99_db':q,'threshold_db':th,
          'seed':cfg['seed'],'calibration_csv_sha256':sha(nullpath),'config_sha256':sha(CAL/'run_config.json'),
          'freeze_before_real_new_D':True,'no_injection_started':True}
        frozen.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8')
    status=json.loads(frozen.read_text());assert sha(nullpath)==status['calibration_csv_sha256']
    # First access to real powers for the NEW statistic occurs below this frozen threshold.
    old=pd.read_csv(OUT/'BACKGROUND_SCREEN.csv');rows=[]
    for r in old.itertuples(index=False):
        path=OUT/'background'/f'b{r.band_id}_w{r.window_id}.mat';q=loadmat(path,simplify_cells=True)
        assert q['power'].shape==(200,291) and np.allclose(q['freq'],np.arange(-100,100)/10,atol=1e-12)
        value=float(statistic(q['power']));row=r._asdict();row['old_retained']=row.pop('retained')
        row.update(D_db=value,threshold_db=status['threshold_db'],retained=value<status['threshold_db'],
            background_mat_sha256=sha(path),calibration_sha256=status['calibration_csv_sha256'])
        rows.append(row)
    d=pd.DataFrame(rows);d.to_csv(CAL/'BACKGROUND_SCREEN_REVISED.csv',index=False)
    final={'screened_windows':20,'retained_windows':int(d.retained.sum()),'threshold_db':status['threshold_db'],
      'calibration_csv_sha256':status['calibration_csv_sha256'],'screen_csv_sha256':sha(CAL/'BACKGROUND_SCREEN_REVISED.csv'),
      'screen_complete':True,'injection_started':False,'preregistration_sha256':lock['sha256']}
    (CAL/'BACKGROUND_SCREEN_REVISED_FREEZE.json').write_text(json.dumps(final,indent=2)+'\n',encoding='utf-8')
    print(status,flush=True);print(d[['band_id','window_id','screen_score_db','D_db','retained']].to_string(index=False),flush=True);print(final,flush=True)
if __name__=='__main__':main()
