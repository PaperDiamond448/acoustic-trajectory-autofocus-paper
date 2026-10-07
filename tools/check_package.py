"""Check this curated snapshot without running or changing experiments."""
from pathlib import Path
from urllib.parse import unquote
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def main():
    rows=list(csv.DictReader((ROOT/'整理清单.csv').open(encoding='utf-8-sig',newline='')))
    errors=[]
    for r in rows:
        p=ROOT/r['repo_path']
        if not p.is_file() or sha(p)!=r['repo_sha256']:
            errors.append(r['repo_path'])
    images=re.findall(r'!\[[^\n]*?\]\(([^)]+)\)',(ROOT/'在线阅读_完整修订稿.md').read_text(encoding='utf-8'))
    for rel in images:
        if not (ROOT/unquote(rel)).is_file():errors.append('missing reading figure: '+rel)
    counts={}
    for sub,expected in [('C_confirm/C_records.csv',14000),('X1_duration/X1_records.csv',9600),('X2_frontend/X2_records.csv',5600)]:
        with (ROOT/'phaseD'/sub).open(encoding='utf-8-sig',newline='') as f:
            n=sum(1 for _ in csv.DictReader(f))
        counts[sub]=n
        if n!=expected:errors.append(f'{sub}: {n} != {expected}')
    with (ROOT/'phaseD/X3_real/X3_FROZEN_TESTSET.csv').open(encoding='utf-8-sig',newline='') as f:
        counts['X3_FROZEN_TESTSET.csv']=sum(1 for _ in csv.DictReader(f))
    if counts['X3_FROZEN_TESTSET.csv']!=105:errors.append('Wrong frozen real test-set count')
    core=['phaseD_ada.m','phaseD_dwell.m','phaseD_regularization.m','estimate_proposed_T.m','build_family_T.m']
    for n in core:
        if not (ROOT/'phaseD/code'/n).exists():errors.append('missing core: '+n)
    if len(images)!=16:errors.append(f'Expected 16 reading figures, found {len(images)}')
    report={'verified_files':len(rows),'reading_figures':len(images),'record_counts':counts,'errors':errors}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    if errors:raise SystemExit(1)

if __name__=='__main__':main()
