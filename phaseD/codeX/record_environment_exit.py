from pathlib import Path
import csv, hashlib, json, sys
R = Path('D:/论文集/phaseD')
stage, first, last, completed = sys.argv[1:]
first, last, completed = int(first), int(last), int(completed)
folder = {'X1': 'X1_duration', 'X2': 'X2_frontend'}[stage]
stamp = R / folder / f'short_batch_{first:03d}_{last:03d}.json'
content = json.loads(stamp.read_text(encoding='utf-8'))
assert content['stage'] == stage and content['first_job'] == first and content['last_job'] == last
p = R / 'Y_compute/ENVIRONMENT_EXIT_EVENTS.csv'
fields = ['stage', 'first_job', 'last_job', 'records_committed_at_exit', 'exit_code',
          'complete_stamp', 'complete_stamp_sha256', 'event']
rows = list(csv.DictReader(p.open(encoding='utf-8'))) if p.exists() else []
if not any(q['stage'] == stage and int(q['first_job']) == first for q in rows):
    rows.append(dict(stage=stage, first_job=first, last_job=last,
                     records_committed_at_exit=completed, exit_code=-1073740940,
                     complete_stamp=str(stamp),
                     complete_stamp_sha256=hashlib.sha256(stamp.read_bytes()).hexdigest(),
                     event='Observed launcher exit 0xc0000374 after complete stamp; next batch started; numerical results retained'))
    with p.open('w', encoding='utf-8', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
print(f'Recorded {stage} {first}-{last} exit after verified completed stamp.')
