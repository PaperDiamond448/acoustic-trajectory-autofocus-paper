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
    files=[p for p in OUT.rglob('*') if p.is_file() and 'chunks' not in p.relative_to(OUT).parts]
    files+=[p for p in (ROOT/'codeC').iterdir() if p.is_file()]
    files+=[ROOT/'PREREGISTRATION_PhaseD_20261003.md',ROOT/'PREREGISTRATION_PhaseD_ADDENDUM_20261003.md',ROOT/'D_dev/FROZEN_METHOD.json',ROOT/'STOP1_audit_Claude_20261004/STOP1_AUDIT.md']
    # Include the exact scientific dependencies, with their directory structure intact.
    rows=list(csv.DictReader((ROOT/'codeC/SOURCE_MANIFEST_C_sha256.csv').open(encoding='utf8')))
    files+=[Path(r['source_file']) for r in rows]
    files=sorted(set(files))
    manifest=OUT/'DELIVERY_MANIFEST_sha256.csv'
    with manifest.open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['relative_file','sha256']);w.writeheader()
        for p in files:w.writerow(dict(relative_file=str(p.relative_to(ROOT.parent)),sha256=sha(p)))
    archive=ROOT/'PhaseD_停止点2_核对包_20261004.zip'
    assert not archive.exists(),'Avoid overwriting a prior delivered review archive.'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in files+[manifest]:z.write(p,p.relative_to(ROOT.parent).as_posix())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        entries=len(z.infolist())
    digest=sha(archive)
    (ROOT/'PhaseD_停止点2_核对包_20261004.sha256').write_text(digest+'  '+archive.name+'\n',encoding='utf8')
    print(json.dumps(dict(archive=str(archive),bytes=archive.stat().st_size,entries=entries,sha256=digest,full_mat_chunks='Remain local under C_confirm/chunks; not duplicated in review ZIP'),ensure_ascii=False))

if __name__=='__main__':package()
