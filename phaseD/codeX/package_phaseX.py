from pathlib import Path
import zipfile,hashlib,json,sys,csv
R=Path('D:/论文集/phaseD');manifest=R/'Y_compute/FINAL_DELIVERY_MANIFEST.json';zipout=R/'PhaseD_X阶段完整核对包_20261004.zip'
files=[]
for folder in ['codeX','X1_duration','X2_frontend','X3_real','Y_compute']:
 files.extend(p for p in (R/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest and not p.name.endswith('.partial.mat'))
files.extend([R/'PHASE_D_REPORT.md',R/'DEVIATIONS.md',R/'PREREGISTRATION_PhaseD_20261003.md',R/'PREREGISTRATION_PhaseD_ADDENDUM_20261003.md',R/'D_dev/FROZEN_METHOD.json',R/'C_confirm/CONFIRM_REPORT.md',R/'C_confirm/CONFIRM_DECISION.json',R/'STOP2_audit_Claude_20261004/STOP2_AUDIT.md'])
files=sorted(set(files));hashes={str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
manifest.write_text(json.dumps({'status':'ALL_X_AND_Y_COMPLETE_STOPPED','files':hashes,'report_sha256':hashes['PHASE_D_REPORT.md']},ensure_ascii=False,indent=2),encoding='utf-8')
assert not zipout.exists(),'Preserve existing delivery; choose a new filename if packaging again.'
with zipfile.ZipFile(zipout,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=3) as z:
 for p in [*files,manifest]:z.write(p,str(p.relative_to(R)))
with zipfile.ZipFile(zipout) as z:
 assert z.testzip() is None
 for name,h in hashes.items():assert hashlib.sha256(z.read(name)).hexdigest()==h,name
result={'status':'PASS','file':str(zipout),'entries':len(files)+1,'bytes':zipout.stat().st_size,'sha256':hashlib.sha256(zipout.read_bytes()).hexdigest(),'all_entry_hashes_verified':True}
(R/'Y_compute/PACKAGE_VERIFICATION.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))
