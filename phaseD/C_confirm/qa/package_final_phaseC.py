"""Finalize the review archive after writing the completed continuation state."""
from pathlib import Path
import csv, hashlib, json, zipfile

ROOT=Path(r'D:\论文集\phaseD');OUT=ROOT/'C_confirm'
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
    return h.hexdigest()

def package():
    status=json.loads((OUT/'FINAL_STATUS.json').read_text(encoding='utf8'))
    assert status['status']=='stop2_complete_awaiting_user_audit' and not status['X_started']
    notes=OUT/'CONTINUATION_NOTES.md';old=notes.read_text(encoding='utf-8-sig')
    header=('# FINAL — Confirmation complete; STOP POINT 2\n\n'
        'All 2,800 phase-52 records / 14,000 method rows completed. C-A1: P1/P2/P3/S1 all PASS. Primary method ADA_local_c04_t30_A. DO NOT rerun the numerical batch and DO NOT start X1–X3 without later explicit user release of stop point 2. All former exec sessions have completed.\n\n'
        'Read CONFIRM_REPORT.md, CONFIRM_DECISION.json, FINAL_STATUS.json and audits. All inputs, old development outputs and protected sources unchanged. Native reconstruction max metric/track difference 0; CSV/MAT reconciliation max difference 4.97e-14; independent bootstrap decisions PASS; both Nature figures automatic and visual QA PASS.\n\n'
        'Numerical MATLAB process reported heap corruption AFTER all chunks, CSV and final config were saved. Separate read-only native processes exited normally; no optimizer retries. Incident fully disclosed and validated in ENVIRONMENT_EXIT_INCIDENT.json. S0 still has an eta cost relative to UNB; P2 passed on the preregistered pooled unit.\n\n'
        'Final archive: phaseD/PhaseD_停止点2_核对包_20261004.zip. Full MATLAB chunks stay local under C_confirm/chunks.\n\n'
        '---\n\nHistorical in-progress notes below are retained for traceability and are superseded by the final state above.\n\n')
    assert not old.startswith('# FINAL');notes.write_text(header+old,encoding='utf8')
    manifest=OUT/'DELIVERY_MANIFEST_sha256.csv'
    files=[p for p in OUT.rglob('*') if p.is_file() and 'chunks' not in p.relative_to(OUT).parts and p!=manifest]
    files+=[p for p in (ROOT/'codeC').iterdir() if p.is_file()]
    files+=[ROOT/'PREREGISTRATION_PhaseD_20261003.md',ROOT/'PREREGISTRATION_PhaseD_ADDENDUM_20261003.md',ROOT/'D_dev/FROZEN_METHOD.json',ROOT/'STOP1_audit_Claude_20261004/STOP1_AUDIT.md']
    rows=list(csv.DictReader((ROOT/'codeC/SOURCE_MANIFEST_C_sha256.csv').open(encoding='utf8')))
    files+=[Path(r['source_file']) for r in rows];files=sorted(set(files))
    entries=[]
    with manifest.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['relative_file','sha256']);w.writeheader()
        for p in files:
            row=dict(relative_file=p.relative_to(ROOT.parent).as_posix(),sha256=sha(p));entries.append(row);w.writerow(row)
    archive=ROOT/'PhaseD_停止点2_核对包_20261004.zip'
    staging=ROOT/'PhaseD_停止点2_核对包_20261004.final.partial.zip'
    backup=ROOT/'PhaseD_停止点2_核对包_20261004_initial.zip'
    for p in [archive,staging,backup]:assert p.resolve().parent==ROOT.resolve()
    assert not staging.exists() and not backup.exists()
    with zipfile.ZipFile(staging,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[manifest]:z.write(p,p.relative_to(ROOT.parent).as_posix())
    with zipfile.ZipFile(staging) as z:
        assert z.testzip() is None
        names=z.namelist();assert len(names)==len(set(names))==len(files)+1
        for row in entries:assert hashlib.sha256(z.read(row['relative_file'])).hexdigest()==row['sha256']
        assert z.read('phaseD/C_confirm/CONFIRM_REPORT.md')==(OUT/'CONFIRM_REPORT.md').read_bytes()
    archive.rename(backup);staging.rename(archive)
    digest=sha(archive)
    (ROOT/'PhaseD_停止点2_核对包_20261004.sha256').write_text(digest+'  '+archive.name+'\n',encoding='utf8')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,entries=len(names),all_entry_hashes='PASS',sha256=digest,branch=status['branch'],stop=2,X_started=False),ensure_ascii=False))

if __name__=='__main__':package()
