from pathlib import Path
import csv,hashlib,json
R=Path('D:/论文集/phaseD')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
for d in ['X1_duration','X2_frontend','X3_real','Y_compute']:(R/d).mkdir(exist_ok=True)
sources={}
for rel in ['code/SOURCE_MANIFEST_sha256.csv','codeC/SOURCE_MANIFEST_C_sha256.csv']:
    for row in csv.DictReader((R/rel).open(encoding='utf-8-sig')):
        p=Path(row['source_file']);assert sha(p)==row['sha256'],str(p);sources[p]=row['sha256']
for p in [R/'D_dev/FROZEN_METHOD.json',R/'STOP2_audit_Claude_20261004/STOP2_AUDIT.md',R.parent/'phaseA/exp/A_visibility/run_A3.m',R.parent/'phaseA/exp/B_realtone/run_B1_realtone.m',*list((R/'codeX').glob('*.m')),*list((R/'codeX').glob('*.md'))]:sources[p]=sha(p)
with (R/'codeX/SOURCE_MANIFEST_X_sha256.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(p),h) for p,h in sorted(sources.items()))
protected=[]
for d in ['G_gates','D_dev','C_confirm','STOP1_audit_Claude_20261004','STOP2_audit_Claude_20261004']:
    protected.extend(p for p in (R/d).rglob('*') if p.is_file())
with (R/'codeX/PROTECTED_STOP2_sha256.csv').open('w',encoding='utf-8',newline='') as f:
    w=csv.writer(f);w.writerow(['source_file','sha256']);w.writerows((str(p),sha(p)) for p in sorted(protected))
print(json.dumps({'immutable_sources_verified':len(sources),'protected_files':len(protected),'X_manifest_sha256':sha(R/'codeX/SOURCE_MANIFEST_X_sha256.csv')}))
