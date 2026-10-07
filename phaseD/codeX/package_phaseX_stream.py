"""Same delivery contents as package_phaseX.py, bounded-memory hashing."""
from pathlib import Path
import hashlib, json, zipfile

R = Path('D:/论文集/phaseD')
manifest = R / 'Y_compute/FINAL_DELIVERY_MANIFEST.json'
zipout = R / 'PhaseD_X阶段完整核对包_20261004.zip'
def hash_stream(stream):
    h = hashlib.sha256()
    while block := stream.read(4 * 1024 * 1024):
        h.update(block)
    return h.hexdigest()
def sha(path):
    with path.open('rb') as stream:
        return hash_stream(stream)
files = []
for folder in ['codeX', 'X1_duration', 'X2_frontend', 'X3_real', 'Y_compute']:
    files.extend(p for p in (R / folder).rglob('*') if p.is_file()
                 and '__pycache__' not in p.parts and p != manifest
                 and not p.name.endswith('.partial.mat'))
files.extend(R / name for name in [
    'PHASE_D_REPORT.md', 'DEVIATIONS.md',
    'PREREGISTRATION_PhaseD_20261003.md',
    'PREREGISTRATION_PhaseD_ADDENDUM_20261003.md',
    'D_dev/FROZEN_METHOD.json', 'C_confirm/CONFIRM_REPORT.md',
    'C_confirm/CONFIRM_DECISION.json',
    'STOP2_audit_Claude_20261004/STOP2_AUDIT.md'])
files = sorted(set(files))
hashes = {p.relative_to(R).as_posix(): sha(p) for p in files}
manifest.write_text(json.dumps(dict(status='ALL_X_AND_Y_COMPLETE_STOPPED',
                                   files=hashes,
                                   report_sha256=hashes['PHASE_D_REPORT.md']),
                               ensure_ascii=False, indent=2), encoding='utf-8')
assert not zipout.exists(), 'Preserve existing delivery; select another filename if packaging again.'
with zipfile.ZipFile(zipout, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=3, allowZip64=True) as z:
    for i, p in enumerate([*files, manifest], 1):
        z.write(p, p.relative_to(R).as_posix())
        if i % 500 == 0:
            print(f'Packaged {i}/{len(files)+1} files', flush=True)
with zipfile.ZipFile(zipout) as z:
    assert z.testzip() is None
    for i, (name, digest) in enumerate(hashes.items(), 1):
        with z.open(name) as stream:
            assert hash_stream(stream) == digest, name
        if i % 500 == 0:
            print(f'Verified {i}/{len(files)} archive entry hashes', flush=True)
result = dict(status='PASS', file=str(zipout), entries=len(files)+1,
              bytes=zipout.stat().st_size, sha256=sha(zipout),
              all_entry_hashes_verified=True,
              storage_adapter='Same original delivery selection and SHA-256/CRC proofs; bounded-memory stream hashing.')
(R / 'Y_compute/PACKAGE_VERIFICATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
