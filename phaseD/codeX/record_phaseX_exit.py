from pathlib import Path
import hashlib,json
R=Path('D:/论文集/phaseD');O=R/'Y_compute'
files=[]
for p in sorted((R/'X1_duration/chunks').glob('*.mat')):
 if p.name.endswith('.partial.mat'):continue
 original=p.name.startswith('T150_S0_') or p.name.startswith('T150_S2_-20dB_') or (p.name.startswith('T150_S2_-17dB_') and int(p.stem.rsplit('_',1)[1])<=4)
 if original:files.append(p)
assert len(files)==44
log=R/'Y_compute/X_numeric_batch.log';archive=O/'X_numeric_initial_heap_exit.log';archive.write_bytes(log.read_bytes())
d={'exit_code':'0xc0000374','message':'Heap corruption','completed_X1_records':440,'committed_chunks':len(files),'saved_chunks_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'recovery':'Same immutable driver reuses committed signature-checked chunks. Uncommitted jobs restart from preregistered seeds and original budgets; no candidate pooling or per-solve extra budget.','X2_or_real_module_started':False}
(O/'X_INITIAL_ENVIRONMENT_EXIT.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8');print(len(files),'committed chunks preserved')
