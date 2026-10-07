"""Exercise silent exit, stalled progress and alert deduplication without alerts."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import os
import time
import monitor_PhaseE_health as monitor


def main():
    with TemporaryDirectory(dir=monitor.PHASE / '_health_monitor') as work:
        phase = Path(work)
        folder = phase / 'E3_duration_ext'
        records = folder / 'records'
        records.mkdir(parents=True)
        (folder / 'C_jobs.csv').write_text('tag\none\n', encoding='utf-8')
        csv = records / 'one.csv'
        mat = records / 'one.mat'
        csv.write_text('eta_in,eta_out\n0.5,0.7\n', encoding='utf-8')
        mat.write_bytes(b'saved-fixture')
        state = phase / 'REMAINING_RUN_STATUS.json'
        state.write_text(json.dumps({'stage':'C','state':'running'}), encoding='utf-8')
        (phase / 'REMAINING_RUN_PROCESS.json').write_text(json.dumps({'pid':123}), encoding='utf-8')
        previous_folder = phase / 'E2_frontend_ext'
        previous_folder.mkdir()
        (previous_folder / 'FINAL_STATUS.json').write_text(json.dumps({
            'complete':True,'eta_recomputation_passed':True,'protected_files_unchanged':154,
            'input_records':1400,'method_rows':4200}), encoding='utf-8')
        with patch.object(monitor, 'PHASE', phase), patch.object(monitor, 'OUT', phase / 'monitor'), \
                patch.object(monitor, 'controller_alive', return_value=True) as alive:
            assert monitor.inspect_progress()['health'] == 'running'
            alive.return_value = False
            assert monitor.inspect_progress()['health'] == 'controller_missing'
            alive.return_value = True
            mat.unlink()
            assert monitor.inspect_progress()['health'] == 'saved_pair_missing'
            mat.write_bytes(b'saved-fixture')
            for path in phase.rglob('*'):
                if path.is_file(): os.utime(path,(time.time()-1000,time.time()-1000))
            assert monitor.inspect_progress()['health'] == 'no_recent_activity'
            state.write_text(json.dumps({'stage':'C','state':'stopped','reason':'fixture error'}), encoding='utf-8')
            assert monitor.inspect_progress()['health'] == 'stopped'
            snap = monitor.inspect_progress()
            with patch.object(monitor, 'inspect_progress', return_value=snap), \
                    patch.object(monitor, 'uploaded_tasks', return_value=[]), \
                    patch.object(monitor, 'notify', return_value=True) as notify:
                monitor.check_once()
                monitor.check_once()
                assert notify.call_count == 1, 'Unchanged issue must not repeatedly notify.'
            # A completed final report is not an upload confirmation while still
            # in the same stage: a C -> D transition is required for C delivery.
            assert monitor.uploaded_tasks({'stage':'C','health':'running'}) == ['B']
    print('Monitor checks passed: running, silent exit, missing MAT, stalled activity, reported stop, deduplicated alerts.')


if __name__ == '__main__':
    main()
