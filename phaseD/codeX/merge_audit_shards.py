from pathlib import Path
import csv,hashlib,json,sys
import pandas as pd
R=Path('D:/论文集/phaseD');stage=sys.argv[1];folder,total,chunks={'X1':('X1_duration',2400,240),'X2':('X2_frontend',1400,140)}[stage];O=R/folder;D=O/'qa_shards'
for row in csv.DictReader((R/'Y_compute/SHARDED_AUDIT_ADAPTER_MANIFEST.csv').open(encoding='utf-8')):
 assert hashlib.sha256(Path(row['source_file']).read_bytes()).hexdigest()==row['sha256']
proofs=[];rounds=[];dwells=[]
for start in range(1,chunks+1,10):
 tag=f'shard_{start:03d}_{min(start+9,chunks):03d}'
 q=json.loads((D/(tag+'_AUDIT.json')).read_text(encoding='utf-8'));assert q['status']=='PASS' and q['records']==100 and q['rows']==400;proofs.append(q)
 rounds.append(pd.read_csv(D/(tag+'_ADA_rounds.csv')))
 if stage=='X1':dwells.append(pd.read_csv(D/(tag+'_SMR_F02_dwell.csv')))
data=pd.read_csv(O/(stage+'_records.csv'));keys=['scene','snr_db','record_id']+(['duration_s','method'] if stage=='X1' else ['frontend']);assert len(data)==4*total and not data.duplicated(keys).any()
allrounds=pd.concat(rounds,ignore_index=True);rkeys=['scene','snr_db','record_id','duration_s','frontend','round'];assert not allrounds.duplicated(rkeys).any();assert len(allrounds.drop_duplicates(rkeys[:-1]))==total*(1 if stage=='X1' else 4)
allrounds.to_csv(O/(stage+'_ADA_rounds.csv'),index=False)
if stage=='X1':
 d=pd.concat(dwells,ignore_index=True);assert len(d)==total and not d.duplicated(['scene','snr_db','record_id','duration_s']).any();d.to_csv(O/'X1_SMR_F02_dwell.csv',index=False)
result=dict(status='PASS',records=sum(q['records'] for q in proofs),rows=sum(q['rows'] for q in proofs),all_metrics_and_CSV_max_abs_difference=max(q['all_metrics_and_CSV_max_abs_difference'] for q in proofs),ADA_solver_round_hard_fail=sum(q['ADA_solver_round_hard_fail'] for q in proofs),ADA_solver_round_budget_cap=sum(q['ADA_solver_round_budget_cap'] for q in proofs),shards=len(proofs),scope='All original per-record checks unchanged in 100-record read-only shards; exact chunk/record/CSV/round coverage and unique keys independently verified in merge; no optimization')
assert result['records']==total and result['rows']==4*total
(O/'SAVED_OUTPUTS_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result),flush=True)
