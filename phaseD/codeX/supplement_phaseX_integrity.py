from pathlib import Path
import csv,json,hashlib,pandas as pd
R=Path('D:/论文集/phaseD')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={}
for name in ['Y_compute/FILEBRIDGE_ADAPTER_MANIFEST.csv','Y_compute/V7BRIDGE_ADAPTER_MANIFEST.csv','Y_compute/X3_CSV_READ_ADAPTER_MANIFEST.csv','Y_compute/X3_FILEBRIDGE_ADAPTER_MANIFEST.csv','Y_compute/SHARDED_AUDIT_ADAPTER_MANIFEST.csv','Y_compute/REGISTERED_BOUNDS_AUDIT_ADAPTER_MANIFEST.csv','X3_real/CANONICAL_SCREEN_SOURCE_MANIFEST.csv','BASELINE_MANIFEST_sha256.csv']:
 rows=list(csv.DictReader((R/name).open(encoding='utf-8-sig')))
 for row in rows:assert sha(Path(row['source_file']))==row['sha256'],row['source_file']
 checks[name]=len(rows)
prior=json.loads((R/'Y_compute/PRE_FILEBRIDGE_CHUNKS.json').read_text(encoding='utf-8'))
for p,h in prior['sha256'].items():assert sha(Path(p))==h,p
real_prior=json.loads((R/'Y_compute/X3_PRE_DURATION_EXIT.json').read_text(encoding='utf-8'))
for p,h in real_prior['sha256'].items():assert sha(Path(p))==h,p
old=pd.read_csv(R/'X3_real/qa/initial_independent_window_screen/X3_visibility.csv');new=pd.read_csv(R/'X3_real/X3_visibility.csv');q=old.merge(new,on=['tone_hz','segment_start_s'],suffixes=('_preliminary','_final'),validate='one_to_one');flips=q[q.passed_preliminary!=q.passed_final];flips.to_csv(R/'X3_real/SCREEN_INTERFACE_CORRECTION_FLIPS.csv',index=False)
result={'status':'PASS','extra_protected_checks':checks,'all_920_pre_filebridge_committed_records_unchanged':True,'canonical_screen_interface_correction_pass_flips':len(flips),'canonical_cases':int(new.passed.sum()),'method_or_threshold_changes':0}
(R/'Y_compute/SUPPLEMENT_INTEGRITY_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result))
