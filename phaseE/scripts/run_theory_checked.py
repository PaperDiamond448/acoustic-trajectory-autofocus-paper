"""Run the supplied, unmodified theory_metrics.py and enforce task A checks."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import sys

for name in ('OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'OMP_NUM_THREADS'):
    os.environ[name] = '1'
LOCAL = Path(__file__).resolve().parents[1]
if (LOCAL / '_local_pydeps').exists():
    sys.path.insert(0, str(LOCAL / '_local_pydeps'))

import h5py
import numpy as np
import pandas as pd
import scipy
import theory_metrics


def run(stem):
    path = Path(stem)
    index = pd.read_csv(str(path)+'_index.csv')
    saved = json.loads(Path(str(path)+'_export_status.json').read_text(encoding='utf-8'))
    assert saved['export_complete'] and saved['all_input_hashes_match']
    with h5py.File(str(path)+'.h5', 'r') as h:
        shapes = {key: h[key].shape for key in ('truth', 'input', 'output')}
        assert shapes['input'] == shapes['output']
        assert shapes['input'][0] == len(index)
        assert shapes['truth'][0] == index.truth_row.nunique()
        assert index.row.tolist() == list(range(len(index)))
        assert np.asarray(h.attrs['fs_hz']).item() == 20
        for key in shapes:
            assert h[key].dtype == np.dtype('float64')
    theory_metrics.main(str(path))
    data = pd.read_csv(str(path)+'_theory_metrics.csv')
    di, do = float(data.check_dev_in.max()), float(data.check_dev_out.max())
    status = {'passed': di < 1e-6 and do < 1e-6, 'checked_rows': len(data),
              'max_eta_in_abs_diff': di, 'max_eta_out_abs_diff': do, 'eta_tolerance': 1e-6,
              'h5_shapes': shapes, 'supplied_script_sha256': hashlib.sha256(Path(theory_metrics.__file__).read_bytes()).hexdigest(),
              'dependencies': {'numpy': np.__version__, 'pandas': pd.__version__,
                               'scipy': scipy.__version__, 'h5py': h5py.__version__}}
    Path(str(path)+'_python_check.json').write_text(json.dumps(status, indent=2)+'\n', encoding='utf-8')
    assert status['passed'], 'Task A eta mismatch: stop, record disagreement in README, and do not proceed.'

    # Same-record paired means; equally weight scene/SNR cells. Resample seed
    # clusters within each scene, carrying all SNRs and frontends together.
    scenes = sorted(data.scene.unique())
    snrs = sorted(data.snr_db.unique())
    fronts = sorted(data.frontend.unique())
    seeds = sorted(data.record_id.unique())
    full = pd.MultiIndex.from_product([scenes, seeds, snrs, fronts],
                                     names=['scene', 'record_id', 'snr_db', 'frontend'])
    keyed = data.set_index(['scene', 'record_id', 'snr_db', 'frontend']).reindex(full)
    assert not keyed[['eta_in', 'eta_out']].isna().any().any()
    matrix = keyed[['eta_in', 'eta_out']].to_numpy().reshape(len(scenes),len(seeds),len(snrs),len(fronts),2)
    cluster_means = matrix.mean(axis=2)
    rng = np.random.default_rng(20261007)
    draws = np.stack([rng.integers(0,len(seeds),size=(2000,len(seeds))) for _ in scenes])
    values=[]
    for b in range(2000):
        value=np.stack([cluster_means[s,draws[s,b]].mean(axis=0) for s in range(len(scenes))]).mean(axis=0)
        values.append(value)
    boots=np.stack(values)
    point=cluster_means.mean(axis=(0,1))
    result=[]
    for f, front in enumerate(fronts):
        x=data[data.frontend==front]
        for name, p, vals in [('eta_in',point[f,0],boots[:,f,0]),
                              ('eta_out',point[f,1],boots[:,f,1]),
                              ('gain',point[f,1]-point[f,0],boots[:,f,1]-boots[:,f,0])]:
            lo, hi=np.quantile(vals,[.025,.975])
            result.append({'frontend':front,'metric':name,'n':len(x),'estimate':p,
                           'ci_lo':lo,'ci_hi':hi,'bootstrap_replicates':2000,'bootstrap_seed':20261007,
                           'cell_weight':'equal_scene_snr','cluster':'record_id_within_scene'})
    pd.DataFrame(result).to_csv(str(path)+'_paired_summary.csv', index=False)
    np.savez_compressed(str(path)+'_bootstrap_draws.npz',draws=draws,scenes=scenes,record_ids=seeds,
                        bootstrap_seed=20261007)
    print(json.dumps(status),flush=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stem')
    run(parser.parse_args().stem)
