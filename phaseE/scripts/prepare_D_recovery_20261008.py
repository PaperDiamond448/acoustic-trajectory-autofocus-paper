"""Archive the stopped run and verify existing injection checkpoints before resuming."""
from pathlib import Path
import hashlib
import json
import shutil
import sys
import time

import numpy as np
import pandas as pd
from scipy.io import loadmat

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'phaseE'
OUT = PHASE / 'E5_inject'
RECOVERY = OUT / 'recovery_20261008_0341'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    assert not (RECOVERY / 'RECOVERY_PRECHECK.json').exists(), 'Precheck is already complete; do not overwrite it.'
    RECOVERY.mkdir(exist_ok=True)
    for source in [
        PHASE / 'REMAINING_RUN_STATUS.json', PHASE / 'REMAINING_RUN_PROCESS.json',
        PHASE / 'REMAINING_RUN_CONFIG.json', PHASE / 'remaining_20261007.out.log',
        PHASE / 'remaining_20261007.err.log', OUT / 'README_STOPPED.md',
        OUT / 'run_D_01251_01275.log', OUT / 'run_D_01276_01300.log',
        PHASE / '_completion_notification/status.json',
        PHASE / 'scripts/run_remaining_PhaseE.py',
    ]:
        if source.exists():
            target = RECOVERY / 'before' / source.relative_to(PHASE)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                shutil.copy2(source, target)

    config = json.loads((PHASE / 'REMAINING_RUN_CONFIG.json').read_text())
    for name, digest in config['new_implementation_sha256'].items():
        assert sha(PHASE / 'scripts' / name) == digest, f'Implementation changed: {name}'
    lock = json.loads((PHASE / 'PREREGISTRATION_PhaseE_20261007.sha256.json').read_text())
    assert sha(PHASE / lock['file']) == lock['sha256']
    protected = pd.read_csv(PHASE / 'E0_preflight/PROTECTED_FILES_before.csv')
    for row in protected.itertuples(index=False):
        assert sha(ROOT / row.path) == row.sha256, f'Protected source changed: {row.path}'

    jobs = pd.read_csv(OUT / 'D_jobs.csv').set_index('tag')
    snapshot = []
    max_eta_diff = 0.0
    complete = 0
    methods = {'VS', 'V0', 'MFT', 'SUV', 'SUV_GRID', 'DHMM'}
    for csv in sorted((OUT / 'records').glob('*.csv')):
        assert not csv.stem.endswith('.pending') and csv.stat().st_size > 0
        mat = csv.with_suffix('.mat')
        assert mat.exists(), f'Saved CSV without MAT: {csv}'
        table = pd.read_csv(csv)
        assert len(table) == 6 and set(table.frontend) == methods
        assert np.isfinite(table[['eta_in', 'eta_out']].to_numpy()).all()
        job = jobs.loc[csv.stem]
        data = loadmat(mat, simplify_cells=True)['S']
        for field in ('band_id', 'window_id', 'target_kind', 'snr_db', 'record_id', 'seed', 'duration_s'):
            assert (table[field] == job[field]).all(), (csv.name, field)
            assert data[field] == job[field], (mat.name, field)
        assert table.input_hash.nunique() == 1 and table.input_hash.iloc[0] == data['input_hash']
        assert len(data['rows']) == 6 and len(data['details']) == 6
        for record, detail in zip(data['rows'], data['details']):
            # Row frontend is a MATLAB string object; detail frontend is a char array.
            frontend = detail['frontend']
            saved = table[table.frontend == frontend].iloc[0]
            for field in ('eta_in', 'eta_out'):
                diff = abs(float(saved[field]) - float(record[field]))
                max_eta_diff = max(max_eta_diff, diff)
                assert diff < 1e-12, (csv.name, field, diff)
        for trajectory in [data['truth_g'], data['truth_phase']] + [
            detail[field] for detail in data['details'] for field in ('input_g', 'output_g')
        ]:
            assert np.size(trajectory) == 6000 and np.isfinite(trajectory).all()
        for path in (csv, mat):
            snapshot.append({'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)})
        complete += 1
        if complete % 100 == 0:
            print('CHECK', complete, flush=True)
    pd.DataFrame(snapshot).to_csv(RECOVERY / 'SAVED_CHECKPOINTS_before.csv', index=False)
    pending = [p.name for p in (OUT / 'records').glob('*.pending.*')]
    result = {
        'checked_local': time.strftime('%Y-%m-%d %H:%M:%S'),
        'saved_inputs_verified': complete, 'saved_method_rows_verified': complete * 6,
        'checkpoint_files_hashed': len(snapshot), 'max_csv_mat_eta_difference': max_eta_diff,
        'all_seed_and_job_metadata_match': True, 'all_trajectories_finite_and_6000_samples': True,
        'protected_files_unchanged': len(protected), 'new_numeric_implementation_unchanged': True,
        'preregistration_sha256': lock['sha256'], 'pending_files': pending,
        'eta_recomputation': 'Full independent recomputation remains part of the unchanged finalizer after all D inputs finish.',
    }
    (RECOVERY / 'RECOVERY_PRECHECK.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False), flush=True)


def verify_preserved():
    before = pd.read_csv(RECOVERY / 'SAVED_CHECKPOINTS_before.csv')
    for row in before.itertuples(index=False):
        path = ROOT / row.path
        assert path.stat().st_size == row.bytes and sha(path) == row.sha256, f'Checkpoint changed: {path}'
    protected = pd.read_csv(PHASE / 'E0_preflight/PROTECTED_FILES_before.csv')
    for row in protected.itertuples(index=False):
        assert sha(ROOT / row.path) == row.sha256, f'Protected source changed: {row.path}'
    original = json.loads((RECOVERY / 'before/REMAINING_RUN_CONFIG.json').read_text())
    for name, digest in original['new_implementation_sha256'].items():
        assert sha(PHASE / 'scripts' / name) == digest, f'Numeric implementation changed: {name}'
    result = {
        'checked_local': time.strftime('%Y-%m-%d %H:%M:%S'),
        'all_previously_saved_checkpoints_unchanged': True,
        'checkpoint_files_verified': len(before), 'saved_inputs_before_resume': len(before) // 2,
        'protected_files_unchanged': len(protected), 'numeric_implementation_unchanged': True,
        'runner_sha256_after_recovery': sha(PHASE / 'scripts/run_remaining_PhaseE.py'),
    }
    (RECOVERY / 'RECOVERY_CHECKS.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify-preserved']:
        verify_preserved()
    else:
        assert not sys.argv[1:]
        main()
