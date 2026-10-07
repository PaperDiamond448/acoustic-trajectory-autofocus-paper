"""Five-minute read-only experiment monitoring, including silent process exits."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import argparse
import csv
import hashlib
import json
import os
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'phaseE'
OUT = PHASE / '_health_monitor'
PS = r'C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
FOLDERS = {'B_reg': 'E2_frontend_ext', 'B': 'E2_frontend_ext', 'C': 'E3_duration_ext', 'D': 'E5_inject'}
COUNTS = {'B': (1400, 4200), 'C': (2400, 4800), 'D': (5040, 30240)}
TZ = timezone(timedelta(hours=8))
INTERVAL = 300
STALE_SECONDS = 900


def now():
    return datetime.now(TZ).isoformat()


def read_json(path):
    for attempt in range(4):
        try:
            return json.loads(path.read_text(encoding='utf-8-sig'))
        except json.JSONDecodeError:
            if attempt == 3:
                raise
            time.sleep(.2)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + '.pending')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(path)


def controller_alive(pid):
    pid = int(pid)
    assert pid > 0
    command = (f'$p = Get-CimInstance Win32_Process -Filter "ProcessId = {pid}"\n'
               'if ($null -eq $p) { Write-Output "null" } else {\n'
               '  $p | Select-Object ProcessId,CommandLine | ConvertTo-Json -Compress\n}')
    result = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-Command', command],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30,
                            creationflags=subprocess.CREATE_NO_WINDOW)
    if result.returncode:
        raise RuntimeError('Cannot query the experiment controller process.')
    proc = json.loads(result.stdout.decode('utf-8-sig', errors='replace').strip())
    return bool(proc and 'run_remaining_PhaseE.py' in (proc.get('CommandLine') or ''))


def inspect_progress():
    state = read_json(PHASE / 'REMAINING_RUN_STATUS.json')
    process = read_json(PHASE / 'REMAINING_RUN_PROCESS.json')
    stage = state.get('stage')
    alive = controller_alive(process['pid'])
    saved = expected = None
    latest = 0.0
    missing = []
    if stage in FOLDERS:
        folder = PHASE / FOLDERS[stage]
        with (folder / f'{stage}_jobs.csv').open(encoding='utf-8-sig', newline='') as handle:
            tags = {row['tag'] for row in csv.DictReader(handle)}
        saved, expected = 0, len(tags)
        for tag in tags:
            path = folder / 'records' / (tag + '.csv')
            if path.exists() and path.stat().st_size:
                saved += 1
                latest = max(latest, path.stat().st_mtime)
                if not path.with_suffix('.mat').exists():
                    missing.append(tag)
        # Export, finalization, retries and upload also count as activity.
        for path in folder.iterdir():
            if path.is_file():
                latest = max(latest, path.stat().st_mtime)
    for name in ('remaining_20261007.out.log', 'remaining_20261007.err.log', 'REMAINING_RUN_STATUS.json'):
        path = PHASE / name
        if path.exists():
            latest = max(latest, path.stat().st_mtime)
    age = max(0.0, time.time() - latest) if latest else None
    if state.get('state') == 'stopped':
        health, reason = 'stopped', state.get('reason', 'Controller reported a stop.')
    elif stage == 'B/C/D' and state.get('state') == 'complete' and state.get('uploaded'):
        health, reason = 'complete', None
    elif missing:
        health, reason = 'saved_pair_missing', f'{len(missing)} nonempty CSV files lack matching MAT files.'
    elif not alive:
        health, reason = 'controller_missing', 'Experiment controller has exited before completion.'
    elif age is not None and age >= STALE_SECONDS:
        health, reason = 'no_recent_activity', 'No saved results or controller/finalizer activity for 15 minutes.'
    else:
        health, reason = 'running', None
    return {'checked_local': now(), 'health': health, 'reason': reason, 'stage': stage,
            'saved_inputs': saved, 'planned_inputs': expected, 'controller_pid': process['pid'],
            'controller_alive': alive, 'seconds_since_last_activity': age, 'missing_mat_tags': missing,
            'run_state': state, 'poll_seconds': INTERVAL,
            'next_check_local': (datetime.now(TZ) + timedelta(seconds=INTERVAL)).isoformat()}


def uploaded_tasks(snapshot):
    # The controller advances stages only after upload and remote-ref verification.
    stage = snapshot['stage']
    tasks = ['B'] if stage == 'C' else ['B', 'C'] if stage == 'D' else []
    if snapshot['health'] == 'complete':
        tasks = ['B', 'C', 'D']
    for task in tasks:
        result = read_json(PHASE / FOLDERS[task] / 'FINAL_STATUS.json')
        assert result['complete'] and result['eta_recomputation_passed']
        assert result['protected_files_unchanged'] == 154
        assert (result['input_records'], result['method_rows']) == COUNTS[task]
    return tasks


def notify(title, body):
    message = OUT / 'message.json'
    write_json(message, {'title': title, 'body': body})
    result = subprocess.run([PS, '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                             '-File', str(PHASE / 'scripts/submit_completion_notification.ps1'),
                             '-MessagePath', str(message)], stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, timeout=30,
                             creationflags=subprocess.CREATE_NO_WINDOW)
    (OUT / 'delivery.stdout.log').write_bytes(result.stdout)
    (OUT / 'delivery.stderr.log').write_bytes(result.stderr)
    with (OUT / 'alerts.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps({'local_time': now(), 'title': title, 'body': body,
                                 'submitted': result.returncode == 0,
                                 'exit_code': result.returncode}, ensure_ascii=False) + '\n')
    return result.returncode == 0


def already_notified(snapshot):
    if snapshot['health'] != 'stopped':
        return False
    try:
        previous = read_json(PHASE / '_completion_notification/status.json')
        return (previous.get('notification_submitted') and previous.get('state') == 'run_stopped'
                and previous.get('run_state') == snapshot['run_state'])
    except (OSError, ValueError):
        return False


def check_once(no_notify=False):
    OUT.mkdir(exist_ok=True)
    previous_path = OUT / 'alert_state.json'
    previous = read_json(previous_path) if previous_path.exists() else {'completed_notified': ['B'], 'issue': None}
    try:
        snapshot = inspect_progress()
        completed = uploaded_tasks(snapshot)
    except Exception as error:
        snapshot = {'checked_local': now(), 'health': 'monitor_check_error', 'reason': str(error),
                    'stage': None, 'poll_seconds': INTERVAL,
                    'next_check_local': (datetime.now(TZ) + timedelta(seconds=INTERVAL)).isoformat()}
        completed = []
    if snapshot['health'] not in ('running', 'complete'):
        issue = (snapshot['health'], snapshot.get('stage'), snapshot.get('reason'))
        key = hashlib.sha256(json.dumps(issue).encode()).hexdigest()
        if previous.get('issue') != key and not no_notify:
            labels = {'stopped': '实验已停止', 'controller_missing': '实验进程已退出',
                      'no_recent_activity': '实验进度需要检查', 'saved_pair_missing': '实验保存文件需要检查',
                      'monitor_check_error': '实验监控检查失败'}
            body = f'任务 {snapshot.get("stage") or "C/D"}。请查看 phaseE/_health_monitor/STATUS.json；已保存结果保持原样。'
            if already_notified(snapshot) or notify(labels[snapshot['health']], body):
                previous['issue'] = key
    elif previous.get('issue') is not None:
        if not no_notify and notify('实验已恢复进展', f'任务 {snapshot.get("stage")} 当前运行正常，五分钟监控继续。'):
            previous['issue'] = None
    for task in completed:
        if task == 'C' and task not in previous['completed_notified'] and not no_notify:
            if notify('积累时长扩展已完成', 'C 已通过核验并上传 GitHub，D 真实背景注入已开始。'):
                previous['completed_notified'].append(task)
    snapshot['completed_and_uploaded'] = completed
    write_json(OUT / 'STATUS.json', snapshot)
    if not no_notify:
        write_json(previous_path, previous)
    with (OUT / 'checks.jsonl').open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(snapshot, ensure_ascii=False) + '\n')
    print(json.dumps(snapshot, ensure_ascii=False), flush=True)
    return snapshot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--once', action='store_true')
    parser.add_argument('--no-notify', action='store_true')
    args = parser.parse_args()
    write_json(OUT / 'PROCESS.json', {'pid': os.getpid(), 'started_local': now(),
               'script': str(Path(__file__).resolve()), 'poll_seconds': INTERVAL})
    while True:
        started = time.monotonic()
        snapshot = check_once(args.no_notify)
        if args.once or snapshot['health'] == 'complete':
            break
        time.sleep(max(0, INTERVAL - (time.monotonic() - started)))


if __name__ == '__main__':
    main()
